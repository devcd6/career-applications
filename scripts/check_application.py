#!/usr/bin/env python3
"""Check an application folder against the knowledge base.

Usage:
    python scripts/check_application.py applications/<slug>
    python scripts/check_application.py applications/<slug> --claims kb/_views/claims.md

Errors (exit 1):
  provenance   a number in resume.md or cover-letter.md not in any claim's metrics; for resume bullets, not in the metrics of the claim(s) the bullet maps to
  titles       role title not one of the KB title variants (NCMW must be "Project Coordinator")
  dates        role dates differ from the KB role header
  counts       bullets per role outside the owner's ranges
  verbs        a role repeats a starting verb
  dashes       em dash in narrative text
  spacing      blank line between bullets or skill lines, or two blank lines in a row
  summary      summary does not end with a "Committed to" / "Dedicated to" sentence
  claims-used  a resume bullet missing from claims-used.md, or mapped to an unknown claim ID
  verbs-bracket a bullet's starting verb is not one of the claim's leading bracketed alternatives
  duplicates   two bullets in different roles are near-identical (word overlap >= 0.85)
  forced       a "Forced" keyword (keywords.txt line "Forced | phrase") is missing from resume.md
  hard-filters match.md has no "Hard filters" section
Warnings: starting verb not among the claim's canonical wording; use of allowed_numbers.txt;
  near-duplicate bullets (0.70 to 0.85); summary/skills terms not found in the KB;
  keywords missing from resume.md.
Reports (never gate): keyword coverage by category (keywords.txt, optional "Category | phrase"
  lines; --baseline FILE compares against another resume), Hard filters checklist from match.md,
  claims whose canonical wording has a number their metrics lack (--metrics-debt lists all).

Provenance borrows the idea (not the code) of career-ops. Numbers are compared as
literal tokens ("6,000+" must appear as "6,000+" in a claim's metrics), except that a count
written as a word in metrics ("four", two through twelve) also allows its digit ("4"). Years and
dates are checked by the dates check instead. "4+" (years of experience) is an
owner ruling in kb/_user_decisions.md and is always allowed. A reviewed list of extra
numbers may go in <slug>/allowed_numbers.txt (one per line); the check reports its use.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANGES = {  # role id (claims view '## <id>') -> (min, max); owner preferences
    "ncmw-project-coordinator": (9, 14),
    "ucsb-research-assistant": (5, 8),
    "sanctuary-centers-housing-coordinator": (8, 11),
    "asei-marketing-specialist": (4, 7),
    "casa-serena-program-assistant": (4, 6),
}
RULING_NUMBERS = {"4+"}
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
MON = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
DATE_RE = re.compile(rf"({MON})\s+(\d{{4}})\s*[-–—]+\s*(?:({MON})\s+(\d{{4}})|(Present|present|Current))")
NUM_RE = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?[+%]?")
WORDNUM = "two three four five six seven eight nine ten eleven twelve fifteen twenty thirty forty fifty hundred thousand dozen".split()
# A count written as a word in a claim's metrics also allows its digit form in a bullet (owner approved 2026-10-09).
# Limited to two through twelve; "one" is left out because it is also a pronoun.
WORD_DIGITS = dict(zip("two three four five six seven eight nine ten eleven twelve".split(), map(str, range(2, 13))))
IDENT_RE = re.compile(
    r"\bCFR\s*Part\s*\d+|\b\d+\s*CFR\b(?:\s*Part\s*\d+)?|\bPart\s*\d+|\bSection\s*\d+[\w/]*|\bWCAG\s*\d+(?:\.\d+)*"
    r"|\bM-\d+-\d+|\bSF-\d+\w*|\bRMF\s*\d+(?:\.\d+)*|\bISO\s*\d+|\bNCT\d+|\bRise\s*\d+|\bOffice\s*365|\b[A-Z]{2,}-\d+\w*")
SKIP_SECTIONS = ("education", "certification", "skill", "header", "publication")


def numbers_in(text):
    """Numeric tokens in text, ignoring dates, years and regulation/product identifiers."""
    text = IDENT_RE.sub(" ", DATE_RE.sub(" ", text))
    return [t for t in NUM_RE.findall(text) if not re.fullmatch(r"(19|20)\d\d", t)]


def metric_tokens(claim):
    m = claim.get("metrics", "")
    words = {w for w in re.findall(r"[a-z]+", m.lower()) if w in WORDNUM}
    return set(NUM_RE.findall(m)) | words | {WORD_DIGITS[w] for w in words if w in WORD_DIGITS}


def norm(s):
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip().lower()


def load_claims(path):
    roles, claims, cur = {}, {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            cur = None
            continue
        if line.startswith("## "):
            cur = {"id": line[3:].strip()}
            roles[cur["id"]] = cur
        elif cur is not None and re.match(r"(employer|title|dates|location): ", line):
            k, _, v = line.partition(": ")
            cur[k] = v.strip()
        m = re.match(r"### (A-\S+) \| (\S+)", line)
        if m:
            claims[m.group(1)] = {"tier": m.group(2), "role": cur["id"] if cur else ""}
        elif claims and line.startswith("canonical: "):
            claims[list(claims)[-1]]["canonical"] = line[11:]
        elif claims and line.startswith("metrics: "):
            claims[list(claims)[-1]]["metrics"] = line[9:]
    return roles, claims


def ym(mon, year):
    return f"{int(year):04d}-{MONTHS.index(mon[:3].lower()) + 1:02d}"


def parse_resume(text):
    """Split into sections {name: [lines]} and role blocks."""
    sections, order, name = {"header": []}, ["header"], "header"
    for line in text.splitlines():
        m = re.match(r"#{1,3}\s*\**(.+?)\**\s*$", line)
        if m and not line.startswith("# "):
            name = m.group(1).strip()
            sections[name] = []
            order.append(name)
        else:
            sections[name].append(line)
    return sections, order


def role_for(name, roles):
    n = norm(name)
    for rid, r in roles.items():
        emp = r.get("employer", "")
        acro = re.search(r"\(([^)]+)\)", emp)
        full = norm(re.sub(r"\s*\([^)]*\)", "", emp))
        if full and full in n or (acro and norm(acro.group(1)) == n):
            return rid
    return None


def bullets_of(lines):
    return [re.sub(r"^\s*[-*•]\s+", "", l).strip() for l in lines if re.match(r"\s*[-*•]\s+", l)]


CATEGORIES = ["title keyword", "hard skill", "action keyword", "business context", "domain keyword", "hard filter", "forced"]


def read_keywords(path):
    """keywords.txt lines: 'phrase' or 'Category | phrase'. Returns [(category, phrase)]."""
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cat, _, rest = line.partition("|")
        if rest and cat.strip().lower() in CATEGORIES:
            out.append((cat.strip().title(), rest.strip()))
        else:
            out.append(("Uncategorized", line))
    return out


def has_phrase(text, phrase):
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I) is not None


def coverage(kws, text):
    by = {}
    for cat, ph in kws:
        hit, tot = by.setdefault(cat, [[], []])
        (hit if has_phrase(text, ph) else tot).append(ph)
    return by


def kb_corpus():
    parts = []
    for rel in ("kb/skills.md", "kb/education.md", "kb/summaries.md"):
        f = ROOT / rel
        if f.exists():
            parts.append(f.read_text(encoding="utf-8"))
    d = ROOT / "kb" / "roles"
    if d.exists():
        parts += [f.read_text(encoding="utf-8") for f in sorted(d.glob("*.md"))]
    return norm(" ".join(parts))


def split_items(text):
    items, depth, cur = [], 0, ""
    for ch in text:
        depth += ch == "(" 
        depth -= ch == ")" and depth > 0
        if ch in ",;" and depth == 0:
            items.append(cur)
            cur = ""
        else:
            cur += ch
    items.append(cur)
    return [re.sub(r"^and\s+", "", i.strip(" .")) for i in items if i.strip(" .")]


def skill_terms(lines):
    terms = []
    for l in lines:
        m = re.match(r"\s*\**[^:*]+:\**\s*(.+)", l)
        if m:
            terms += split_items(m.group(1))
    return terms


def wordset(b):
    return set(re.findall(r"[a-z0-9']+", b.lower()))


def md_section(text, key):
    m = re.search(rf"^#+\s*\**[^\n]*{key}[^\n]*\n(.*?)(?=^#+\s|\Z)", text, re.I | re.S | re.M)
    return m.group(1).strip() if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--claims", help="application-facts packet (default: <folder>/application-facts.md)")
    ap.add_argument("--baseline", help="another resume to compare keyword coverage against")
    ap.add_argument("--metrics-debt", action="store_true", help="list every claim whose wording has a number its metrics lack")
    a = ap.parse_args()
    folder = Path(a.folder)
    claims_path = Path(a.claims) if a.claims else folder / "application-facts.md"
    if not claims_path.exists() and (folder / "claims-packet.md").exists():
        claims_path = folder / "claims-packet.md"
    if not claims_path.exists() and (ROOT / "kb" / "_views" / "claims.md").exists():
        claims_path = ROOT / "kb" / "_views" / "claims.md"
    if not claims_path.exists():
        print(f"no application-facts packet found: {claims_path}")
        return 2
    errors, warns, reports = [], [], []
    err = lambda k, m: errors.append(f"[{k}] {m}")
    roles, claims = load_claims(claims_path)
    if not claims:
        print("no claims loaded; run scripts/build_claims_view.py")
        return 2
    base = set(RULING_NUMBERS)
    allowed = set(base)
    for c in claims.values():
        allowed |= metric_tokens(c)
    extra = folder / "allowed_numbers.txt"
    if extra.exists():
        ex = {l.strip() for l in extra.read_text(encoding="utf-8").splitlines() if l.strip()}
        allowed |= ex
        base |= ex
        warns.append(f"allowed_numbers.txt in use ({', '.join(sorted(ex)) or 'empty'}); owner must review")

    docs = {n: (folder / n) for n in ("resume.md", "cover-letter.md")}
    for n, p in docs.items():
        if not p.exists():
            warns.append(f"{n} not found; skipped")
    texts = {n: p.read_text(encoding="utf-8") for n, p in docs.items() if p.exists()}

    # dashes
    for n, t in texts.items():
        for i, l in enumerate(t.splitlines(), 1):
            if "—" in l:
                err("dashes", f"{n}:{i} em dash")

    resume = texts.get("resume.md")
    all_bullets = []
    if resume:
        sections, order = parse_resume(resume)
        # provenance (resume)
        for sname in order:
            if any(s in sname.lower() for s in SKIP_SECTIONS):
                continue
            body = "\n".join(l for l in sections[sname]
                             if "@" not in l and not re.match(r"\s*[-*\u2022]\s", l))
            for tok in sorted(set(numbers_in(body))):
                if tok in allowed:
                    continue
                err("provenance", f"resume.md [{sname}] number {tok!r} not in any claim's metrics")
        # roles
        for sname in order:
            rid = role_for(sname, roles)
            if not rid:
                continue
            lines = sections[sname]
            block = "\n".join(lines)
            bl = bullets_of(lines)
            all_bullets += [(rid, b) for b in bl]
            lo, hi = RANGES.get(rid, (0, 999))
            if not lo <= len(bl) <= hi:
                err("counts", f"{rid}: {len(bl)} bullets, range {lo}-{hi}")
            verbs = [re.match(r"[\w'-]+", b).group(0).lower() for b in bl if re.match(r"[\w'-]+", b)]
            for v in sorted({v for v in verbs if verbs.count(v) > 1}):
                err("verbs", f"{rid}: starting verb {v!r} used {verbs.count(v)} times")
            head = block.split("\n- ")[0]
            variants = [v.strip() for v in roles[rid].get("title", "").split("|")]
            if rid.startswith("ncmw"):
                variants = ["Project Coordinator"]
                if re.search(r"junior", head, re.I):
                    err("titles", f"{rid}: title must be 'Project Coordinator' (found 'Junior')")
            if not any(norm(v) in norm(head) for v in variants):
                err("titles", f"{rid}: none of {variants} found in role heading")
            kb_dates = roles[rid].get("dates", "")
            m = DATE_RE.search(head)
            if not m:
                err("dates", f"{rid}: no date range found in role heading")
            else:
                start = ym(m.group(1), m.group(2))
                end = ym(m.group(3), m.group(4)) if m.group(3) else "present"
                if f"{start} to {end}" != kb_dates:
                    err("dates", f"{rid}: resume {start} to {end}, KB {kb_dates}")
            # spacing
            for i in range(1, len(lines) - 1):
                if not lines[i].strip() and re.match(r"\s*[-*•]\s", lines[i - 1]) and re.match(r"\s*[-*•]\s", lines[i + 1]):
                    err("spacing", f"{rid}: blank line between bullets")
                    break
        for sname in order:
            if "skill" in sname.lower():
                ls = sections[sname]
                for i in range(1, len(ls) - 1):
                    if not ls[i].strip() and ls[i - 1].strip() and ls[i + 1].strip():
                        err("spacing", f"[{sname}] blank line between skill lines")
                        break
        if re.search(r"\n[ \t]*\n[ \t]*\n", resume):
            err("spacing", "resume.md has two blank lines in a row")
        # summary
        key = next((s for s in order if "summary" in s.lower()), None)
        if not key:
            err("summary", "no SUMMARY section")
        else:
            text = " ".join(l.strip() for l in sections[key] if l.strip())
            sents = re.split(r"(?<=[.!?])\s+", text)
            if not sents or not re.match(r"(Committed|Dedicated) to\b", sents[-1]):
                err("summary", "summary must end with a 'Committed to...' or 'Dedicated to...' sentence")

    cover = texts.get("cover-letter.md")
    if cover:
        body = "\n".join(l for l in cover.splitlines() if "@" not in l)
        for tok in sorted(set(numbers_in(body))):
            if tok not in allowed:
                err("provenance", f"cover-letter.md number {tok!r} not in any claim's metrics")

    # claims-used
    cu = folder / "claims-used.md"
    if resume and not cu.exists():
        err("claims-used", "claims-used.md missing")
    elif resume:
        lines = cu.read_text(encoding="utf-8").splitlines()
        nlines = [norm(l) for l in lines]
        for l in lines:
            for cid in re.findall(r"A-[\w-]+", l):
                if cid not in claims:
                    err("claims-used", f"unknown claim ID {cid}")
        for rid, b in all_bullets:
            nb = norm(b)
            hit = next((l for l, n in zip(lines, nlines) if nb in n), None)
            ids = re.findall(r"A-[\w-]+", hit or "")
            if not hit:
                err("claims-used", f"bullet not in claims-used.md: {b[:70]}...")
            elif not any(i in claims for i in ids):
                err("claims-used", f"no valid claim ID for bullet: {b[:70]}...")
            else:
                ok = set().union(*(metric_tokens(claims[i]) for i in ids if i in claims)) | base
                for tok in sorted(set(numbers_in(b))):
                    if tok not in ok:
                        err("provenance", f"bullet number {tok!r} not in metrics of {', '.join(ids)}: {b[:60]}...")
                verb = re.match(r"[\w'-]+", b).group(0).lower()
                canon = " ".join(claims[next(i for i in ids if i in claims)].get("canonical", "").split()[:14]).lower()
                if verb not in re.findall(r"[\w'-]+", canon):
                    warns.append(f"verb {verb!r} not in claim wording start: {b[:60]}...")

    # verbs vs leading bracket group of the mapped claim
    if resume:
        _lines = cu.read_text(encoding="utf-8").splitlines() if cu.exists() else []
        for rid, b in all_bullets:
            nb = norm(b)
            hit = next((l for l in _lines if nb in norm(l)), None)
            ids = [i for i in re.findall(r"A-[\w-]+", hit or "") if i in claims]
            if not ids:
                continue
            g = re.match(r"\[([^\]]+)\]", claims[ids[0]].get("canonical", ""))
            if g and "|" in g.group(1):
                opts = {o.strip().split()[0].lower() for o in g.group(1).split("|") if o.strip()}
                verb = re.match(r"[\w'-]+", b).group(0).lower()
                if verb not in opts:
                    err("verbs-bracket", f"{rid}: {verb!r} not among {sorted(opts)} for {ids[0]}")

        # near-duplicate bullets across roles
        for i, (r1, b1) in enumerate(all_bullets):
            for r2, b2 in all_bullets[i + 1:]:
                if r1 == r2:
                    continue
                w1, w2 = wordset(b1), wordset(b2)
                j = len(w1 & w2) / max(1, len(w1 | w2))
                if j >= 0.85:
                    err("duplicates", f"{r1} / {r2} near-identical ({j:.2f}): {b1[:60]}...")
                elif j >= 0.70:
                    warns.append(f"{r1} / {r2} similar bullets ({j:.2f}): {b1[:60]}...")

        # summary and skills terms not in the KB
        corpus = kb_corpus()
        if corpus:
            skey = next((n for n in order if "skill" in n.lower()), None)
            terms = skill_terms(sections[skey]) if skey else []
            sumkey = next((n for n in order if "summary" in n.lower()), None)
            if sumkey:
                stext = " ".join(sections[sumkey])
                terms += [t for t in re.findall(r"(?<![.!?] )(?<!^)\b[A-Z][A-Za-z0-9&/+-]*(?: [A-Z][A-Za-z0-9&/+-]*)*", stext)
                          if len(t) > 3]
            seen, miss = set(), []
            for t in terms:
                core = norm(re.sub(r"\s*\([^)]*\)", "", t))
                if core and core not in seen:
                    seen.add(core)
                    if core not in corpus:
                        miss.append(t)
            if miss:
                warns.append(f"{len(miss)} summary/skills term(s) not found in kb/skills.md, education.md, summaries.md or kb/roles/: "
                             + "; ".join(miss[:25]) + (" ..." if len(miss) > 25 else "") + " (owner review)")

        # keyword coverage
        kws = read_keywords(folder / "keywords.txt")
        if kws:
            cov = coverage(kws, resume)
            base_cov = None
            if a.baseline and Path(a.baseline).exists():
                base_cov = coverage(kws, Path(a.baseline).read_text(encoding="utf-8"))
            reports.append("Keyword coverage (exact phrase, not a fit score):")
            for cat, (hit, miss) in cov.items():
                line = f"  {cat}: {len(hit)}/{len(hit) + len(miss)}"
                if base_cov:
                    line += f" (baseline {len(base_cov[cat][0])})"
                reports.append(line)
                if miss:
                    reports.append(f"    missing: {'; '.join(miss)}")
                if cat == "Forced" and miss:
                    for ph in miss:
                        err("forced", f"forced keyword missing from resume.md: {ph!r}")
            n_miss = sum(len(m) for c, (h, m) in cov.items() if c not in ("Forced", "Hard Filter"))
            if n_miss:
                warns.append(f"{n_miss} keyword phrase(s) not in resume.md (see coverage report)")

    # hard filters checklist from match.md
    mm = folder / "match.md"
    if resume:
        if not mm.exists():
            warns.append("match.md not found; hard filters not checked")
        else:
            hf = md_section(mm.read_text(encoding="utf-8"), "Hard filter")
            if not hf:
                err("hard-filters", 'match.md has no "Hard filters" section')
            else:
                reports.append("Hard filters (from match.md, confirm each before submitting):")
                reports += ["  " + l for l in hf.splitlines() if l.strip()]

    # metrics debt
    debt = [cid for cid, c in claims.items()
            if c.get("canonical") and set(numbers_in(re.sub(r"\[[^\]]*\]", " ", c["canonical"]))) - metric_tokens(c) - RULING_NUMBERS]
    if a.metrics_debt:
        reports.append(f"Metrics debt: {len(debt)} claim(s) have a number in their wording that metrics lacks: " + ", ".join(debt))
    else:
        reports.append(f"Metrics debt: {len(debt)} claim(s) (run with --metrics-debt to list)")

    for r in reports:
        print(r)

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

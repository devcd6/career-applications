#!/usr/bin/env python3
"""Check a research.md against the company-research layout and the knowledge base.

Usage:
    python scripts/check_research.py applications/<slug>

Errors (exit 1):
  parts     a "## Part N" heading (1 to 6) is missing, or lacks "### Findings" or "### Interview notes"
  tags      a bullet under "### Findings" without exactly one tag:
            [src: <url>] | [unverified: <url>] | [JD] | [inferred] | [not found]
  ids       a claim ID (A-...) not in the claims view, or a story ID (S###) not in kb/stories.md
  notes     an "Interview notes" bullet with no claim ID, story ID, "[none in KB]", or question mark
  numbers   a number in Interview notes not found in any claim's metrics
  sections  no "Source ledger" or "Red flags" or "Questions to ask" heading
  dashes    em dash in the text
Warnings: a [src:] URL not listed in the source ledger.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TAG_RE = re.compile(r"\[(src: *[^\]]+|unverified: *[^\]]+|JD|inferred|not found)\]")
PART_RE = re.compile(r"^## Part (\d)\b.*$", re.M)
BASIC_SECTIONS = ("Company snapshot", "Role context", "Language to mirror")


def sections(text, rx):
    ms = list(rx.finditer(text))
    out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out[m.group(1)] = text[m.end():end]
    return out


def sub(body, name):
    m = re.search(rf"^### {name}\b.*$", body, re.M)
    if not m:
        return None
    n = re.search(r"^###? ", body[m.end():], re.M)
    return body[m.end():m.end() + n.start()] if n else body[m.end():]


def bullets(block):
    return [ln.strip() for ln in block.splitlines() if re.match(r"\s*[-*] ", ln)]


def section(text, name):
    match = re.search(rf"^## {re.escape(name)}\s*$", text, re.M)
    if not match:
        return None
    next_heading = re.search(r"^## ", text[match.end():], re.M)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end():end]


def check_basic_research(text):
    errors, warnings = [], []
    if "—" in text:
        errors.append("[dashes] em dash found")
    for heading in (*BASIC_SECTIONS, "Source ledger", "Questions and unknowns"):
        if section(text, heading) is None:
            errors.append(f"[sections] no '{heading}' heading")

    ledger = section(text, "Source ledger") or ""
    for heading in BASIC_SECTIONS:
        body = section(text, heading)
        if body is None:
            continue
        for bullet in bullets(body):
            tags = TAG_RE.findall(bullet)
            if len(tags) != 1:
                errors.append(f"[tags] {heading}: {len(tags)} tags in: {bullet[:70]}")
            for tag in tags:
                if tag.startswith("src"):
                    url = re.sub(r"^src: *", "", tag).strip()
                    if url not in ledger:
                        warnings.append(f"{heading}: {url} not in source ledger")

    for warning in warnings:
        print("WARN", warning)
    for error in errors:
        print("ERROR", error)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--claims", default=str(ROOT / "kb" / "_views" / "claims.md"))
    ap.add_argument("--stories", default=str(ROOT / "kb" / "stories.md"))
    args = ap.parse_args()
    f = Path(args.folder) / "research.md"
    if not f.exists():
        print(f"error: {f} not found")
        return 1
    text = f.read_text(encoding="utf-8")
    if section(text, "Company snapshot") is not None:
        return check_basic_research(text)
    if not (ROOT / "kb" / "_views" / "claims.md").exists() or not (ROOT / "kb" / "stories.md").exists():
        print("error: legacy research layout requires KB sources; use the basic company brief format")
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_application as ca  # noqa: E402
    import check_interview_prep as cip  # noqa: E402

    _, claims = ca.load_claims(Path(args.claims))
    sids = cip.story_ids(Path(args.stories))
    allowed = set(ca.RULING_NUMBERS)
    for c in claims.values():
        allowed |= ca.metric_tokens(c)
    errs, warns = [], []

    if "—" in text:
        errs.append("[dashes] em dash found")
    for key in ("Source ledger", "Red flags", "Questions to ask"):
        if not re.search(rf"^#+ .*{key}", text, re.M | re.I):
            errs.append(f"[sections] no '{key}' heading")

    ledger = text.split("Source ledger", 1)[1].split("\n## ", 1)[0] if "Source ledger" in text else ""
    parts = sections(text, PART_RE)
    for n in "123456":
        body = parts.get(n)
        if body is None:
            errs.append(f"[parts] Part {n} missing")
            continue
        fnd, notes = sub(body, "Findings"), sub(body, "Interview notes")
        if fnd is None or notes is None:
            errs.append(f"[parts] Part {n} needs '### Findings' and '### Interview notes'")
            continue
        for b in bullets(fnd):
            tags = TAG_RE.findall(b)
            if len(tags) != 1:
                errs.append(f"[tags] Part {n}: {len(tags)} tags in: {b[:70]}")
            for t in tags:
                if t.startswith("src"):
                    url = re.sub(r"^src: *", "", t).strip()
                    if url not in ledger:
                        warns.append(f"Part {n}: {url} not in source ledger")
        for b in bullets(notes):
            has_id = bool(cip.CLAIM_ID_RE.search(b) or cip.STORY_ID_RE.search(b))
            if not (has_id or "[none in KB]" in b or "?" in b):
                errs.append(f"[notes] Part {n}: no claim/story ID, [none in KB] or question: {b[:70]}")
            for nums in ca.numbers_in(cip.strip_non_numeric(b)):
                if nums not in allowed:
                    errs.append(f"[numbers] Part {n}: '{nums}' not in any claim metrics: {b[:60]}")

    for cid in sorted(set(cip.CLAIM_ID_RE.findall(text))):
        if cid not in claims:
            errs.append(f"[ids] unknown claim {cid}")
    for sid in sorted(set(cip.STORY_ID_RE.findall(text))):
        if sid not in sids:
            errs.append(f"[ids] unknown story {sid}")

    for w in warns:
        print("WARN", w)
    for e in errs:
        print("ERROR", e)
    print(f"{len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check that every phrase in keywords.txt appears in the JD in the JD's exact wording.

Usage:
    python scripts/check_keywords.py applications/<slug>
    python scripts/check_keywords.py --jd jd.md --keywords keywords.txt

Uses the phrase matcher's own parsing and matching (case-insensitive, whole word,
curly apostrophes and en dashes normalized), so a phrase that passes here is counted by
the matcher. Every unmatched phrase is reported with its likely cause: hyphen versus space,
punctuation (an apostrophe or parentheses), or an inflected form in the JD.

Also checks the category caps (Business Context 10, Domain Keyword 5) and warns when a
Forced or Hard Filter phrase appears in a JD line that calls it preferred, a plus or nice to have.

Exit 0 when every phrase is found and no cap is exceeded, 1 when any is not, 2 on a missing or empty input.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCHER = ROOT / ".claude" / "skills" / "resume-tailor" / "scripts" / "exact_phrase_matcher.py"


def load_matcher():
    spec = importlib.util.spec_from_file_location("exact_phrase_matcher", MATCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


INFLECTION = r"(?:s|es|d|ed|ing|er|ers|ly)"


def squash(text):
    """Lowercase text with apostrophes dropped and every other non-word run turned into a space."""
    return " ".join(re.sub(r"[^\w]+", " ", re.sub(r"['\u2019]", "", text.lower())).split())


def compact(text):
    return re.sub(r"[\W_]+", "", text.lower())


def flexible(word):
    """Regex for one word that tolerates curly apostrophes and en dashes."""
    out = []
    for ch in word:
        if ch in "'\u2019":
            out.append("['\u2019]")
        elif ch in "-\u2013":
            out.append("[-\u2013]")
        else:
            out.append(re.escape(ch))
    return "".join(out)


def raw_find(jd_raw, words, tail=""):
    """The JD's own wording (original case and punctuation) for the given words, or None."""
    pat = r"\s+".join(flexible(w) for w in words) + tail
    m = re.search(r"(?<![\w])" + pat + r"(?![\w])", jd_raw, re.IGNORECASE)
    return m.group(0) if m else None


def excerpt(jd_raw, phrase):
    """The JD's own wording around a phrase whose punctuation differs, or None."""
    words = [r"['\u2019]?".join(re.escape(c) for c in w) for w in squash(phrase).split()]
    if not words:
        return None
    pat = r"[\W_]*".join(words)
    m = re.search(r"(?<![\w])" + pat + r"(?![\w])", jd_raw, re.IGNORECASE)
    if not m:
        return None
    start, end = m.start(), m.end()
    while start > 0 and not jd_raw[start - 1].isspace():
        start -= 1
    while end < len(jd_raw) and not jd_raw[end].isspace():
        end += 1
    return jd_raw[start:end].strip(".,;:")


def diagnose(m, jd_raw, phrase):
    jd_norm = m.norm(jd_raw)
    phrase_norm = m.norm(phrase)
    if ("-" in jd_norm or "-" in phrase_norm) and m.count(phrase_norm.replace("-", " "), jd_norm.replace("-", " ")):
        return "hyphen versus space; the JD wording differs from the keyword"
    found = excerpt(jd_raw, phrase)
    if found and squash(found) == squash(phrase):
        return f"punctuation differs (apostrophe, parentheses or similar); the JD says \"{found}\""
    words = phrase_norm.split()
    if words and len(words[-1]) >= 4:
        last = words[-1]
        stems = [last] + [last[:-n] for n in (1, 2) if last.endswith("s" if n == 1 else "es") and len(last) - n >= 3]
        for stem in stems:
            hit = raw_find(jd_raw, words[:-1] + [stem], tail=INFLECTION + "?")
            if hit:
                return f"JD uses a different form; the JD says \"{hit}\""
    if len(compact(phrase)) >= 6 and compact(phrase) in compact(jd_raw):
        return "hyphen or spacing differs; the JD writes the words differently"
    return "not found in the JD"


def read_phrases(m, kw_path):
    """Phrases as the matcher reads them, in order, without repeats. Also returns truncated lines."""
    phrases, truncated = [], []
    for line in kw_path.read_text(encoding="utf-8").splitlines():
        phrase = m.parse_line(line)[1]
        if phrase and phrase not in phrases:
            phrases.append(phrase)
        body = line.split("|", 1)[-1] if "|" in line else line
        # '#' glued to the preceding text (C#) is a phrase the matcher would cut short;
        # '#' after whitespace is an ordinary comment
        if not line.lstrip().startswith("#") and re.search(r"\S#", body):
            truncated.append(body.strip())
    return phrases, truncated


CAPS = {"Business Context": 10, "Domain Keyword": 5}
PREFERRED_RE = re.compile(r"\b(?:strongly\s+)?preferred\b|\bnice[- ]to[- ]have\b|\ba plus\b|\bdesired\b|\bbonus\b", re.I)


def category_counts(m, kw_path):
    counts = {}
    for line in kw_path.read_text(encoding="utf-8").splitlines():
        cat, phrase = m.parse_line(line)
        if phrase:
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def preferred_conflicts(m, jd_raw, kw_path):
    """Forced or Hard Filter phrases whose JD line (or its section heading) says preferred."""
    lines = jd_raw.splitlines()
    out = []
    for line in kw_path.read_text(encoding="utf-8").splitlines():
        cat, phrase = m.parse_line(line)
        if not phrase or cat not in ("Forced", "Hard Filter"):
            continue
        for i, text in enumerate(lines):
            if m.count(phrase, m.norm(text)):
                heading = next((l for l in reversed(lines[:i]) if re.match(r"\s*(?:#+|\*\*|[A-Z][A-Za-z ]+:\s*$)", l)), "")
                if PREFERRED_RE.search(text) or PREFERRED_RE.search(heading):
                    out.append((cat, phrase, text.strip()[:90]))
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", help="application folder holding jd.md and keywords.txt")
    ap.add_argument("--jd")
    ap.add_argument("--keywords")
    a = ap.parse_args()

    if a.folder:
        jd_path, kw_path = Path(a.folder) / "jd.md", Path(a.folder) / "keywords.txt"
    elif a.jd and a.keywords:
        jd_path, kw_path = Path(a.jd), Path(a.keywords)
    else:
        ap.error("give an application folder, or both --jd and --keywords")
    for path in (jd_path, kw_path):
        if not path.is_file():
            print(f"ERROR cannot read {path}")
            return 2

    try:
        m = load_matcher()
        jd_raw = jd_path.read_text(encoding="utf-8")
        phrases, truncated = read_phrases(m, kw_path)
    except (OSError, UnicodeDecodeError, ImportError, AttributeError) as exc:
        print(f"ERROR cannot read inputs: {exc}")
        return 2
    if not phrases:
        print(f"ERROR no phrases in {kw_path}")
        return 2

    jd = m.norm(jd_raw)
    bad = [p for p in phrases if m.count(p, jd) == 0]
    for p in bad:
        print(f"NOT FOUND  {p}  ({diagnose(m, jd_raw, p)})")
    for t in truncated:
        print(f"NOT FOUND  {t}  ('#' starts a comment in keyword files, so this phrase is cut short)")
    counts = category_counts(m, kw_path)
    capped = [(c, n, CAPS[c]) for c, n in counts.items() if c in CAPS and n > CAPS[c]]
    for c, n, cap in capped:
        print(f"OVER CAP  {c}: {n} phrases, maximum {cap}")
    for cat, phrase, text in preferred_conflicts(m, jd_raw, kw_path):
        print(f"WARN  {cat} phrase '{phrase}' sits in a preferred line: \"{text}\"")
    failures = len(bad) + len(truncated) + len(capped)
    if failures:
        print(f"{failures} problem(s) in {len(phrases)} phrases (not found in the JD's exact wording, or over a category cap)")
        return 1
    print(f"ok: all {len(phrases)} phrases found in the JD")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check that every phrase in keywords.txt appears in the JD in the JD's exact wording.

Usage:
    python scripts/check_keywords.py applications/<slug>
    python scripts/check_keywords.py --jd jd.md --keywords keywords.txt

Uses the phrase matcher's own parsing and matching (case-insensitive, whole word,
curly apostrophes and en dashes normalized), so a phrase that passes here is counted by
the matcher. Every unmatched phrase is reported with its likely cause: hyphen versus space,
punctuation (an apostrophe or parentheses), or an inflected form in the JD.

Exit 0 when every phrase is found, 1 when any is not, 2 on a missing or empty input.
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


def squash(text):
    """Lowercase text with apostrophes dropped and every other non-word run turned into a space."""
    return " ".join(re.sub(r"[^\w]+", " ", re.sub(r"['\u2019]", "", text.lower())).split())


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
    spaced_jd = jd_norm.replace("-", " ")
    spaced_phrase = phrase.replace("-", " ")
    if "-" in jd_norm + phrase and m.count(spaced_phrase, spaced_jd):
        return "hyphen versus space; the JD wording differs from the keyword"
    found = excerpt(jd_raw, phrase)
    if found and squash(found) == squash(phrase):
        return f"punctuation differs (apostrophe, parentheses or similar); the JD says \"{found}\""
    words = phrase.split()
    if words:
        head = r"\s+".join(re.escape(m.norm(w)) for w in words[:-1])
        last = re.escape(m.norm(words[-1]).rstrip("s")) if len(words[-1]) > 3 else re.escape(m.norm(words[-1]))
        pat = (head + r"\s+" if head else "") + last + r"\w*"
        hit = re.search(r"(?<![\w])" + pat + r"(?![\w])", jd_norm)
        if hit:
            raw = re.search(re.escape(hit.group(0)).replace(r"\ ", r"\s+"), jd_raw, re.IGNORECASE)
            return f"JD uses a different form; the JD says \"{raw.group(0) if raw else hit.group(0)}\""
    return "not found in the JD"


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

    m = load_matcher()
    jd_raw = jd_path.read_text(encoding="utf-8")
    jd = m.norm(jd_raw)
    phrases = [m.parse_line(line)[1] for line in kw_path.read_text(encoding="utf-8").splitlines()]
    phrases = [p for p in phrases if p]
    if not phrases:
        print(f"ERROR no phrases in {kw_path}")
        return 2

    bad = [p for p in phrases if m.count(p, jd) == 0]
    for p in bad:
        print(f"NOT FOUND  {p}  ({diagnose(m, jd_raw, p)})")
    if bad:
        print(f"{len(bad)} of {len(phrases)} phrases not found in the JD's exact wording")
        return 1
    print(f"ok: all {len(phrases)} phrases found in the JD")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check handoff.md files for personal data before they are committed.

Usage: python scripts/check_handoff.py [path ...]    (default: applications/*/handoff.md in the repo, from any directory)

Errors (exit 1): email address, phone number, the owner's name, a personal pronoun (write "the owner"),
em dash, URL with a query string or credential-looking token. A regex cannot catch quoted resume
text or pasted job-description paragraphs, so the author still has to keep those out. Handoffs refer to the owner as "the owner" and to repo
files by path.
"""
import glob
import os
import re
import sys

RULES = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("phone", re.compile(r"\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")),
    ("owner name", re.compile(r"\b(devika|dixit)\b", re.I)),
    ("pronoun", re.compile(r"\b(?:she|her|hers|herself|he|him|his|himself)\b", re.I)),
    ("em dash", re.compile("—")),
    ("token", re.compile(r"\b(?:sk-|ghp_|gho_|xox[bap]-|AKIA)[A-Za-z0-9_-]{8,}")),
    ("url with query", re.compile(r"https?://\S+\?\S+")),
]


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(root, "applications", "*", "handoff.md")))
    errors = 0
    for p in paths:
        try:
            with open(p, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError as e:
            print(f"ERROR cannot read {p}: {e}")
            errors += 1
            continue
        for i, line in enumerate(lines, 1):
            for name, rx in RULES:
                if rx.search(line):
                    print(f"ERROR {p}:{i} [{name}] {line[:80]}")
                    errors += 1
    print(f"handoff check: {'FAILED' if errors else 'ok'} ({len(paths)} file(s), {errors} error(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

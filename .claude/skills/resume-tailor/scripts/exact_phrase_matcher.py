#!/usr/bin/env python3
"""Exact-phrase JD matcher.

Checks a list of JD phrases against a resume and the JD itself. A phrase
matches only as an exact, case-insensitive, whole-word occurrence. There is no
stemming, no synonyms and no overlap score.

Usage:
    python exact_phrase_matcher.py --jd jd.txt --resume resume.md --phrases keywords.txt
    python exact_phrase_matcher.py --jd jd.txt --suggest 30

keywords.txt: one phrase per line ('#' starts a comment). A line may carry a
category: 'Hard Skill | data entry' (categories: Title Keyword, Hard Skill, Action
Keyword, Business Context, Domain Keyword, Hard Filter, Forced; others are treated
as part of the phrase). Plain lines are 'Uncategorized'. --suggest lists
frequent exact 1-3 word phrases from the JD to help choose phrases; it does
not judge fit.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

STOP = {
    "a", "an", "and", "or", "but", "of", "in", "on", "at", "by", "for", "to", "with",
    "as", "is", "are", "be", "will", "the", "this", "that", "it", "its", "our", "your",
    "we", "you", "who", "from", "have", "has", "can", "may", "all", "any", "not",
}


CATEGORIES = {"title keyword", "hard skill", "action keyword", "business context",
              "domain keyword", "hard filter", "forced"}


def parse_line(line):
    """'Category | phrase' or 'phrase' -> (category, phrase); '#' starts a comment."""
    line = line.split("#", 1)[0].strip()
    cat, sep, rest = line.partition("|")
    if sep and cat.strip().lower() in CATEGORIES:
        return cat.strip().title(), rest.strip()
    return "Uncategorized", line


def norm(text):
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("–", "-").lower())


def count(phrase, text):
    pat = r"(?<![\w])" + re.escape(norm(phrase)).replace(r"\ ", r"\s+") + r"(?![\w])"
    return len(re.findall(pat, text))


def suggest(jd, n):
    words = re.findall(r"[a-z0-9][a-z0-9'/+&-]*", norm(jd))
    c = Counter()
    for size in (1, 2, 3):
        for i in range(len(words) - size + 1):
            g = words[i:i + size]
            if g[0] in STOP or g[-1] in STOP:
                continue
            c[" ".join(g)] += 1
    return [(p, k) for p, k in c.most_common() if k > 1 and (" " in p or len(p) > 3)][:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jd", required=True)
    ap.add_argument("--resume")
    ap.add_argument("--phrases")
    ap.add_argument("--suggest", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    jd = norm(Path(a.jd).read_text(encoding="utf-8"))
    if a.suggest:
        for p, k in suggest(jd, a.suggest):
            print(f"{k:3d}  {p}")
        return 0
    if not (a.resume and a.phrases):
        ap.error("--resume and --phrases are required unless --suggest is used")
    resume = norm(Path(a.resume).read_text(encoding="utf-8"))
    rows = []
    for line in Path(a.phrases).read_text(encoding="utf-8").splitlines():
        cat, ph = parse_line(line)
        if ph:
            rows.append({"category": cat, "phrase": ph, "in_jd": count(ph, jd), "in_resume": count(ph, resume)})
    if a.json:
        print(json.dumps(rows, indent=2))
        return 0
    for r in rows:
        if r["in_jd"] == 0:
            print(f"NOT IN JD  {r['phrase']}")
    print(f"{'category':18} {'phrase':40} jd  resume")
    for r in rows:
        flag = "" if r["in_resume"] else "  <- missing from resume"
        print(f"{r['category']:18} {r['phrase']:40} {r['in_jd']:<3} {r['in_resume']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

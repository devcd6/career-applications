#!/usr/bin/env python3
"""Check a research.md against the basic company brief layout.

Usage:
    python scripts/check_research.py applications/<slug>

Exit 1 on errors, 2 for the retired six-part layout (older applications keep their original file).
See check_basic_research for the individual checks (required sections, tagged findings, source ledger,
no em dashes).
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
    args = ap.parse_args()
    f = Path(args.folder) / "research.md"
    if not f.exists():
        print(f"error: {f} not found")
        return 1
    text = f.read_text(encoding="utf-8")
    if section(text, "Company snapshot") is not None:
        return check_basic_research(text)
    print("error: research.md uses the retired six-part layout; this repository checks the basic company brief "
          "(Company snapshot, Role context, Language to mirror). Earlier applications keep their original file.")
    return 2


if __name__ == "__main__":
    sys.exit(main())

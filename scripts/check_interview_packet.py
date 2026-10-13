#!/usr/bin/env python3
"""Validate an interview handoff packet.

Usage: python scripts/check_interview_packet.py <packet.md>

Errors (exit 1): missing front matter keys, a missing, empty or unknown `##` section, no claim IDs
under "Claims used", no URL under "Role research" (or the line "No external sources."), or a
duplicate claim ID. The same contract is checked by career-pkm on import.
"""
import re
import sys
from pathlib import Path

SECTIONS = ["Job description", "Submitted resume", "Claims used", "Role research", "Known gaps"]
KEYS = ["slug", "created"]
CLAIM_ID_RE = re.compile(r"^- (A-[a-z0-9]+(?:-[a-z0-9]+)*-\d+)\s*$")
URL_RE = re.compile(r"https?://\S+")


def parse(text):
    """Return (front matter dict, {section: body}, [section order])."""
    meta, sections, order, cur = {}, {}, [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            order.append(cur)
            sections[cur] = []
        elif cur is None:
            m = re.match(r"(\w+): (.*)$", line)
            if m:
                meta[m.group(1)] = m.group(2).strip()
        else:
            sections[cur].append(line)
    return meta, {k: "\n".join(v).strip() for k, v in sections.items()}, order


def claim_ids(body):
    return [m.group(1) for m in (CLAIM_ID_RE.match(l) for l in body.splitlines()) if m]


def validate(text):
    errs = []
    meta, sections, order = parse(text)
    for k in KEYS:
        if not meta.get(k):
            errs.append(f"missing front matter key: {k}")
    for name in order:
        if name not in SECTIONS:
            errs.append(f"unknown section: {name}")
    for name in SECTIONS:
        if name not in sections:
            errs.append(f"missing section: {name}")
        elif not sections[name]:
            errs.append(f"empty section: {name}")
    if order != [s for s in SECTIONS if s in order] and not any(e.startswith("unknown") for e in errs):
        errs.append("sections out of order")
    if "Claims used" in sections:
        ids = claim_ids(sections["Claims used"])
        if not ids:
            errs.append("Claims used has no claim IDs (lines like '- A-...')")
        if len(ids) != len(set(ids)):
            errs.append("duplicate claim ID in Claims used")
    research = sections.get("Role research", "")
    if research and not URL_RE.search(research) and "No external sources." not in research:
        errs.append("Role research needs a source URL or the line 'No external sources.'")
    return errs


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"error: {path} not found")
        return 1
    errs = validate(path.read_text(encoding="utf-8"))
    for e in errs:
        print(f"error: {e}")
    print(f"{len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""Build an interview handoff packet from one application folder.

Usage: python scripts/build_interview_packet.py applications/<slug> [--out FILE]

Reads only jd.md, resume.md (or submitted-resume.md), claims-used.md, research.md and the
"Real gaps" section of match.md. Nothing else in the folder is copied. Headings inside copied files become level-4 headings;
the text is otherwise unchanged. Nothing is written unless
every input exists and the finished packet passes check_interview_packet.py. Default output is
<folder>/interview-packet.md; the owner carries it into career-pkm.
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_interview_packet as chk  # noqa: E402

CLAIM_RE = re.compile(r"\bA-[a-z0-9]+(?:-[a-z0-9]+)*-\d+\b")


def demote(text):
    """Turn embedded headings into level-4 headings so they cannot collide with packet sections."""
    return re.sub(r"^#{1,6}[ 	]+", "#### ", text, flags=re.M)


def read(folder, *names, raw=False):
    for n in names:
        p = folder / n
        if p.exists() and p.read_text(encoding="utf-8").strip():
            text = p.read_text(encoding="utf-8").strip()
            return text if raw else demote(text)
    raise SystemExit(f"error: missing or empty {' or '.join(names)} in {folder}")


def real_gaps(text):
    m = re.search(r"^## Real gaps[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m or not m.group(1).strip():
        raise SystemExit("error: match.md has no non-empty '## Real gaps' section")
    return demote(m.group(1).strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out")
    args = ap.parse_args()
    folder = Path(args.folder)
    out = Path(args.out) if args.out else folder / "interview-packet.md"

    ids = list(dict.fromkeys(CLAIM_RE.findall(read(folder, "claims-used.md"))))
    parts = [
        f"# Interview packet: {folder.name}",
        "",
        f"slug: {folder.name}",
        f"created: {date.today().isoformat()}",
        "",
        "## Job description", read(folder, "jd.md"), "",
        "## Submitted resume", read(folder, "resume.md", "submitted-resume.md"), "",
        "## Claims used", "\n".join(f"- {i}" for i in ids), "",
        "## Role research", read(folder, "research.md"), "",
        "## Known gaps", real_gaps(read(folder, "match.md", raw=True)), "",
    ]
    text = "\n".join(parts)
    errs = chk.validate(text)
    if errs:
        for e in errs:
            print(f"error: {e}")
        return 1
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} ({len(ids)} claims)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Report the state of one application folder and name the next /apply step.

Usage:
    python scripts/preflight.py applications/<slug> [--session-id ID] [--branch NAME]

Looks only at which files exist and are non-empty; it never reads their contents, so no
career facts reach the output. A missing folder counts as empty. Exits 0 in every state; the
apply skill acts on the "next:" line.

next: values, in workflow order:
  add-jd, research, keywords, packet, analyze, plan, plan-approval, build, cover-letter,
  check, done

At "packet" the output also carries a Packet request: slug, folder, the two public files the
career-pkm session reads, the command to run there, this session's ID and the branch to push to.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ARTIFACTS = [
    "jd.md", "research.md", "keywords.txt", "application-facts.md", "keywords.md", "match.md",
    "plan.md", "spec.json", "resume.md", "claims-used.md", "cover-letter.md", "handoff.md",
]

NEXT_TEXT = {
    "add-jd": "save the job description as jd.md (step 1 input)",
    "research": "write research.md (step 1, /research)",
    "keywords": "write keywords.txt from the JD wording and run scripts/check_keywords.py (step 2, /analyze-jd)",
    "packet": "stop: the Packet is missing; the owner runs the Packet request below in career-pkm",
    "analyze": "write keywords.md and match.md using application-facts.md (step 2, /analyze-jd)",
    "plan": "write plan.md and stop for the owner's approval (step 3, /tailor)",
    "plan-approval": "plan.md is waiting for the owner's approval; write spec.json only after it",
    "build": "build the resume from spec.json and write resume.md and claims-used.md (step 3)",
    "cover-letter": "write cover-letter.md (step 4, /cover-letter)",
    "check": "run the checks and write the redacted handoff.md (step 5, /check)",
    "done": "all artifacts exist; the owner reviews before submitting",
}


def present(folder, name):
    p = folder / name
    return p.is_file() and p.stat().st_size > 0


def next_step(have):
    order = [
        ("add-jd", "jd.md"), ("research", "research.md"), ("keywords", "keywords.txt"),
        ("packet", "application-facts.md"), ("analyze", None), ("plan", "plan.md"),
        ("plan-approval", "spec.json"), ("build", None), ("cover-letter", "cover-letter.md"),
        ("check", "handoff.md"),
    ]
    for step, needs in order:
        if step == "analyze":
            if not (have["keywords.md"] and have["match.md"]):
                return step
        elif step == "build":
            if not (have["resume.md"] and have["claims-used.md"]):
                return step
        elif not have[needs]:
            return step
    return "done"


def same_employer(folder):
    parts = folder.name.split("_")
    if len(parts) < 3 or not folder.parent.is_dir():
        return []
    return sorted(p.name for p in folder.parent.iterdir()
                  if p.is_dir() and p.name != folder.name and p.name.split("_")[1:2] == [parts[1]])


def current_branch(folder):
    try:
        cwd = folder if folder.is_dir() else folder.parent
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd,
                             capture_output=True, text=True)
        return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else "unknown"
    except OSError:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--session-id")
    ap.add_argument("--branch")
    a = ap.parse_args()

    folder = Path(a.folder)
    slug = folder.name
    have = {name: present(folder, name) for name in ARTIFACTS}
    step = next_step(have)

    print(f"application: {slug}")
    if not folder.is_dir():
        print("folder: missing (counts as empty)")
    for other in same_employer(folder):
        print(f"same employer: {other} (tell the owner before starting a second version)")
    for name in ARTIFACTS:
        print(f"{name:22} {'present' if have[name] else 'missing'}")
    print(f"next: {step}  {NEXT_TEXT[step]}")

    if step == "packet":
        session = a.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID") or "unknown"
        branch = a.branch or current_branch(folder)
        print()
        print("Packet request")
        print(f"  slug: {slug}")
        print(f"  folder: {folder.as_posix()}")
        print("  read: jd.md, keywords.txt (public JD text only)")
        print(f"  command: /build-packet {slug}")
        print(f"  session: {session}")
        print(f"  deliver-to: branch {branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

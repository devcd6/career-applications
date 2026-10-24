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

At "packet" the output also carries a Packet request: slug, folder, repository, the two public
files the career-pkm session reads, the command to run there, this session's ID, the file to
write and the branch to push it to. Branch and repository read "unknown" when git cannot say
(no remote, detached HEAD).
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# (step, files that must exist before the workflow moves past it), in workflow order
STEPS = [
    ("add-jd", ["jd.md"]),
    ("research", ["research.md"]),
    ("keywords", ["keywords.txt"]),
    ("packet", ["application-facts.md"]),
    ("analyze", ["keywords.md", "match.md"]),
    ("plan", ["plan.md"]),
    ("plan-approval", ["spec.json"]),
    ("build", ["resume.md", "claims-used.md"]),
    ("cover-letter", ["cover-letter.md"]),
    ("check", ["handoff.md"]),
]
SLUG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_[^_]+_.+")
ARTIFACTS = [name for _, files in STEPS for name in files]

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
    if not p.is_file():
        return False
    try:
        return bool(p.read_text(encoding="utf-8", errors="replace").strip())
    except OSError:
        return False


def next_step(have):
    for step, files in STEPS:
        if not all(have[f] for f in files):
            return step
    return "done"


def same_employer(folder):
    folder = folder.resolve()
    parts = folder.name.split("_")
    if len(parts) < 3 or not folder.parent.is_dir():
        return []
    return sorted(p.name for p in folder.parent.iterdir()
                  if p.is_dir() and p.name != folder.name and p.name.split("_")[1:2] == [parts[1]])


def git_out(folder, *args):
    cwd = folder if folder.is_dir() else folder.parent
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def current_branch(folder):
    branch = git_out(folder, "rev-parse", "--abbrev-ref", "HEAD")
    return branch if branch and branch != "HEAD" else "unknown"


def repository(folder):
    url = git_out(folder, "config", "--get", "remote.origin.url")
    m = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--session-id")
    ap.add_argument("--branch")
    a = ap.parse_args()

    folder = Path(a.folder)
    slug = folder.resolve().name
    have = {name: present(folder, name) for name in ARTIFACTS}
    step = next_step(have)

    print(f"application: {slug}")
    if not SLUG_RE.match(slug):
        print("warning: folder name is not YYYY-MM-DD_org_role")
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
        print(f"  repo: {repository(folder)}")
        print("  read: jd.md, keywords.txt (public JD text only)")
        print(f"  command: /build-packet {slug}")
        print(f"  session: {session}")
        print(f"  write-to: applications/{slug}/application-facts.md")
        print(f"  deliver-to: branch {branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

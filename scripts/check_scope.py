#!/usr/bin/env python3
"""Check that a branch changed only what its kind of work may change.

Usage: python scripts/check_scope.py [base]    (default base: origin/main)

Two kinds of change, never mixed in one branch:
  application  every changed path is under applications/<slug>/ for one slug.
  tooling      every changed path is under .claude/, .github/, docs/, scripts/, tests/ or is
               one of README.md, CLAUDE.md, CONTEXT.md; applications/ is untouched.
Always an error: applications/preferences.md, applications/profile-insights.md and writing/
(owner-maintained sources), career-pkm material (kb/, _raw/, resumes/, INDEX.md), and any other
root path.
"""
import subprocess
import sys

TOOLING_DIRS = (".claude/", ".github/", "docs/", "scripts/", "tests/")
TOOLING_FILES = {"README.md", "CLAUDE.md", "CONTEXT.md"}
OWNER_FILES = {"applications/preferences.md", "applications/profile-insights.md"}
FORBIDDEN_DIRS = ("writing/", "kb/", "_raw/", "resumes/")


def classify(paths):
    """Return (kind, errors) for a list of changed paths."""
    errors, slugs, tooling = [], set(), []
    for path in paths:
        if path in OWNER_FILES or path.startswith(FORBIDDEN_DIRS) or path == "INDEX.md":
            errors.append(f"owner-maintained or career-pkm path: {path}")
        elif path.startswith("applications/"):
            parts = path.split("/")
            if len(parts) < 3:
                errors.append(f"file directly under applications/: {path}")
            else:
                slugs.add(parts[1])
        elif path.startswith(TOOLING_DIRS) or path in TOOLING_FILES:
            tooling.append(path)
        else:
            errors.append(f"path outside allowed scope: {path}")
    if slugs and tooling:
        errors.append("application and tooling changes in one branch: " + ", ".join(tooling[:3]))
    if len(slugs) > 1:
        errors.append("more than one application folder changed: " + ", ".join(sorted(slugs)))
    kind = "tooling" if tooling and not slugs else "application" if slugs else "empty"
    return kind, errors


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    if subprocess.run(["git", "rev-parse", "--verify", "-q", base], capture_output=True).returncode:
        remote, _, branch = base.partition("/")
        subprocess.run(["git", "fetch", remote, branch], capture_output=True)
        if subprocess.run(["git", "rev-parse", "--verify", "-q", base], capture_output=True).returncode:
            print(f"ERROR cannot resolve base {base}")
            return 2
    paths = [line for line in git("diff", "--name-only", f"{base}...HEAD").splitlines() if line]
    kind, errors = classify(paths)
    for error in errors:
        print("ERROR", error)
    print("scope check:", "FAILED" if errors else "ok", f"({len(paths)} files, {kind})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

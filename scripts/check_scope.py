#!/usr/bin/env python3
"""Check that an application branch changed only what it may.

Usage: python scripts/check_scope.py [base]    (default base: origin/main)

Allowed without approval: applications/**.
Root paths (kb/, writing/samples/, INDEX.md) are allowed only as additions and only when
kb/_user_decisions.md gained lines in the same diff (the user's approval entry).
Always an error: any change under _raw/, any other root path, and deleted or edited lines
in kb/ or writing/ (existing claims are never edited). Generated files are exempt from the
deletion rule: INDEX.md, kb/_views/claims.md.
"""
import subprocess
import sys

GENERATED = {"INDEX.md", "kb/_views/claims.md"}
ROOT_OK = ("kb/", "writing/samples/")


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    if subprocess.run(["git", "rev-parse", "--verify", "-q", base], capture_output=True).returncode:
        remote, _, branch = base.partition("/")
        subprocess.run(["git", "fetch", remote, branch], capture_output=True)
        if subprocess.run(["git", "rev-parse", "--verify", "-q", base], capture_output=True).returncode:
            print(f"ERROR cannot resolve base {base}")
            return 2
    rows = [l.split("\t") for l in git("diff", "--numstat", f"{base}...HEAD").splitlines()]
    errors, root = [], []
    for add, dele, path in rows:
        if path.startswith("applications/"):
            continue
        if path.startswith("_raw/"):
            errors.append(f"_raw is read-only: {path}")
        elif path in GENERATED or path.startswith(ROOT_OK):
            root.append(path)
            if path not in GENERATED and dele not in ("0", "-"):
                errors.append(f"existing lines edited or deleted ({dele}): {path}")
        else:
            errors.append(f"path outside allowed scope: {path}")
    if root:
        approved = any(p == "kb/_user_decisions.md" and a not in ("0", "-") for a, _, p in rows)
        if not approved:
            errors.append("root additions without an approval entry added to kb/_user_decisions.md: " + ", ".join(root))
    for e in errors:
        print("ERROR", e)
    print("scope check:", "FAILED" if errors else "ok", f"({len(rows)} files, {len(root)} root)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/bin/bash
# Test scripts/session_start_handoff.sh against a throwaway repo, including the post-merge state
# (an application branch whose diff against main is empty). Exit 1 if any case fails.
# Usage: bash scripts/test_session_start_handoff.sh
set -uo pipefail

HOOK="$(cd "$(dirname "$0")" && pwd)/session_start_handoff.sh"
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
fail=0

git init -q --bare "$W/origin.git"
git init -q "$W/repo" && cd "$W/repo" || exit 1
git config user.email t@example.com && git config user.name t
mkdir -p applications/2026-10-12_acme_widget-coordinator applications/2026-10-01_other_analyst
echo "# Acme handoff" > applications/2026-10-12_acme_widget-coordinator/handoff.md
echo "# Other handoff" > applications/2026-10-01_other_analyst/handoff.md
git add -A && git commit -q -m base && git branch -M main
git remote add origin "$W/origin.git" && git push -q origin main 2>/dev/null
git fetch -q origin

run() { CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR="$W/repo" bash "$HOOK"; }
expect() {  # name, branch, pattern that must appear, pattern that must not
  git checkout -q -B "$2"
  out=$(run)
  if ! grep -q -- "$3" <<<"$out" || { [ -n "${4:-}" ] && grep -q -- "$4" <<<"$out"; }; then
    echo "FAIL $1 (branch $2)"; echo "$out" | head -5; fail=1
  else
    echo "ok   $1"
  fi
}

# post-merge: branch name matches the folder, diff against main is empty, typo in the employer word
expect "merged app branch, name match" "2026-10-12_acmee_widget-coordinator" "Acme handoff" "Other handoff"
expect "unrelated app branch lists only" "apply/2027-01-01_zzz_unrelated" "No handoff matches this branch" "BEGIN HANDOFF"
expect "main lists" "main" "Application handoffs available" "BEGIN HANDOFF"
expect "tooling lists" "tooling/x" "Application handoffs available" "BEGIN HANDOFF"
expect "data markers present" "2026-10-12_acme_widget-coordinator" "BEGIN HANDOFF" ""

git checkout -q -B 2026-10-12_acme_widget-coordinator
if [ -n "$(env -u CLAUDE_CODE_REMOTE CLAUDE_PROJECT_DIR="$W/repo" bash "$HOOK")" ]; then
  echo "FAIL silent when not remote"; fail=1
else
  echo "ok   silent when not remote"
fi

# a changed handoff on the branch wins over name matching
git checkout -q -B apply/2027-02-02_new_thing
echo "# Changed" >> applications/2026-10-01_other_analyst/handoff.md
git add -A && git commit -q -m change
out=$(run)
if grep -q "changed on this branch" <<<"$out" && grep -q "Other handoff" <<<"$out"; then echo "ok   changed handoff wins"; else echo "FAIL changed handoff wins"; fail=1; fi

[ "$fail" -eq 0 ] && echo "all passed" || echo "FAILED"
exit "$fail"

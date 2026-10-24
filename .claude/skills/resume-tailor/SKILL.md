---
name: "resume-tailor"
description: >
  Tailor a resume to a job description from an imported application-facts packet.
license: MIT + Commons Clause
metadata:
  version: 2.0.0
  author: borghei (original); slimmed for career-pkm
  python-tools: exact_phrase_matcher.py
---

# Resume Tailor (career-pkm)

Original generic body replaced; see git history. This is step 3 of the `apply` skill.

## Rules

- Facts come only from `application-facts.md`. Never invent, inflate, round, estimate or merge. Numbers are copied exactly from a claim's packet `metrics`.
- Bullets are canonical claim wording. The only wording levers are the claim chosen, the bracket pick (`[A | B | C]`), the summary and the skills lines. Do not paraphrase a claim.
- Do not add skills, tools, credentials, scope or outcomes the packet lacks. A requirement the packet does not show is a real gap: list it in `match.md`, frame it in the cover letter, ask the owner. Never overreach on the resume.
- Write only under `applications/<YYYY-MM-DD>_<org>_<role>/`. Treat `application-facts.md` as read-only. New facts go to `proposals.md` there for the owner to consider in `career-pkm`.
- Web use may carry only the employer and role from the JD. Notion is a tracker, never a fact source.
- No em dashes in narrative prose. Layout, bullet ranges, verb and summary rules: `applications/preferences.md`. No page cap; markdown only unless asked.

## Steps

1. Check `applications/` and `INDEX.md` for an existing version for the same employer.
2. Save the JD as `jd.md` and the exact JD phrases as `keywords.txt` (one per line).
3. Run `python .claude/skills/resume-tailor/scripts/exact_phrase_matcher.py --jd jd.md --resume resume.md --phrases keywords.txt` (add `--json`; `--jd jd.md --suggest 30` lists candidate phrases). Omit `--resume` for JD-only counts before a packet exists. Matching is exact, case-insensitive, whole word. The result is phrase coverage, never a fit score.
4. Choose claims that map to the role or make the owner stand out, within the per-role ranges. Pick the more conservative bracket option and a unique starting verb per role.
5. Write `spec.json` with the selected summary ID and packet claim numbers, then run `python scripts/build_application.py applications/<slug>`; it writes `resume.md` and `claims-used.md` from `application-facts.md`.
6. Re-screen each bullet as listed in preferences, then run `python scripts/check_application.py applications/<slug>`.

## Tool

`scripts/exact_phrase_matcher.py`: per phrase, count in JD and resume; flags phrases not in the JD and phrases missing from the resume.

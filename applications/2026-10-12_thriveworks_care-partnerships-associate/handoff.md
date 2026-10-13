# Handoff: Thriveworks Care Partnerships Associate application

Date: 2026-10-13. Repo: the owner's career-pkm repo. Work is committed and pushed to branch `2026-10-12_thriveworkds_care-partnerships-association` and fast-forwarded to `main` (d8cebb7) on the owner's explicit instruction. No pull request exists.

## State
The full apply workflow (research, analyze-jd, tailor, cover letter, check) is finished for this role. Everything is in `applications/2026-10-12_thriveworks_care-partnerships-associate/`:
- `jd.md`, `research.md`, `keywords.md`, `keywords.txt`, `match.md`, `rank.md`
- `plan.md` (approved; has a build log at the bottom), `spec.json`, `resume.md`, `claims-used.md`
- `cover-letter.md` (revised once to mirror the JD and employer more closely), `proposals.md` (items 1 to 12)

Checks last run clean: `check_application.py` (0 errors, 1 warning that 26 keyword phrases are not on the resume, by design), `detect_ai_writing.js` on the letter (0 issues), `check_research.py` (0), `check_scope.py` (ok, no root changes). The owner declined interview prep.

## Decisions worth knowing (not obvious from the files)
- Folder slug uses `thriveworks` and `associate`; the assigned branch name has a typo ("thriveworkds") and says "association". Branch left unchanged.
- Web fetches failed (DNS), so employer facts beyond the JD are search-summary level and tagged unverified in `research.md`. The letter uses only JD wording and no JD numbers.
- Owner rulings applied this session: A-asei-marketing-specialist-28 is used (the claims view labels it single-source, but the owner's Gate 3 "confirm all" ruling in `kb/_user_decisions.md` treats it as verified; tier label was not edited). The owner checked NCMW: members were providers and practitioners, so provider-organization engagement is claimed (A-ncmw-project-coordinator-41, -97, -24) but not referral-source outreach to physician offices. No claim exists for re-engaging inactive partners; the letter does not claim it.
- Patient Referral Dashboard was moved from Forced to Business Context in `keywords.txt` (it is the employer's tool, not experience). The checker was not weakened.
- A-ncmw-project-coordinator-11 (Growth team) was dropped from the resume because `scripts/build_application.py` leaves a stray space before the final period on its trailing bracket, and editing scripts is out of scope on an application branch. It is used in the cover letter. A fix to the script would be a separate change.
- The point-of-contact bullet uses A-ncmw-project-coordinator-24 (metrics carry 3,200+) rather than -101 (empty metrics).

## Open items for the owner
- Confirm or edit the reflection sentences in the letter and the four candor statements (`proposals.md` items 7 and 8).
- Optional: any sales, referral-source, account-management or re-engagement example, and how the owner used Salesforce, in the owner's own words. These would go to `proposals.md` first.
- Optional: verify employer details on the live Thriveworks site before quoting beyond the JD.
- Whether to keep or vary the owner's refrain line in the letter (kept once).

## Rules to remember
`CLAUDE.md` governs: `_raw/` read-only, facts only from `kb/` claims with exact metrics, no em dashes in prose, nothing from resumes or the KB leaves the repo, pushes to main only with the owner's approval, end sessions by confirming `git diff --stat origin/main...HEAD` shows only the application folder plus approved root paths. Use absolute paths because the shell directory drifts.

## Suggested skills for the next agent
- `apply` for any further change to this application, or a new role.
- `check` to re-run the provenance and style checks after edits.
- `cover-letter` if the owner wants another letter revision (read `writing/style-guide.md` first).
- `interview-prep` only if the owner later asks for it.
- `avoid-ai-writing` in detect mode on the letter only; never rewrite `resume.md`.

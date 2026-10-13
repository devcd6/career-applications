---
name: apply
description: Run the five-step application workflow using the job description and an imported, owner-selected application-facts packet.
---

# apply

Orchestrates one application. Read `CLAUDE.md`, `applications/preferences.md`, and `writing/style-guide.md`; use only the application's `application-facts.md` for career facts. This repository has no full career KB. The owner imports the packet produced in `career-pkm`.

Slug: `applications/<YYYY-MM-DD>_<org>_<role>/` (lowercase, hyphens). Before starting, look in `applications/` and `INDEX.md` for an existing version for the same employer and tell the owner. Every step saves its file and also prints to chat. Stop between steps when the owner wants to review, and ask rather than assume.

1. **/research** (`research.md`). Use `company-research` for a concise company snapshot, role context, language to mirror, source ledger, and unknowns. Web queries contain only employer, role, and relevant program names from the JD. Do not include career facts or interview notes. Tag every finding. Run `python scripts/check_research.py applications/<slug>`.
2. **/analyze-jd** (`keywords.md`, `match.md`). Use `job-description-analyzer` with the exact-phrase rules in preferences. Save phrases to `keywords.txt`; report hard filters, real gaps, and open questions. Compare requirements only with the imported application-facts packet. Do not run claim ranking here; career-fact selection belongs in `career-pkm` before packet export.
3. **/tailor** (`plan.md`, then `resume.md`, `claims-used.md`). Write `plan.md` with selected packet claim IDs, tier, bracket/verb choices, real gaps, and items for `proposals.md`. **Stop for owner approval before writing `spec.json` or running `build_application.py`.** Use the resume skills. Every bullet maps to a packet claim ID; role headings, dates, selected summary, education, credentials, publications, and skills come from the packet. The builder reads `application-facts.md` in the application folder. Print the resume in a Markdown code block.
4. **/cover-letter** (`cover-letter.md`). Use `cover-letter-generator` with `writing/style-guide.md` and the two closest samples in `writing/samples/`. Frame gaps honestly here. Numbers only from claim metrics.
5. **/check**. Run `check_application.py`, `check_research.py`, the cover-letter detectors, and `check_scope.py`. Application changes stay under `applications/<slug>/`; this repository never writes to the career KB. Report failures without weakening checks. Write a redacted session handoff in the application folder and run `check_handoff.py`.

After submission, generate an interview handoff packet. Interview research and prep run in `career-pkm` only after the owner imports that packet.

Rules that never bend: use only packet-backed career facts and exact metrics; never invent, inflate, round, or merge. Put new facts in this application's `proposals.md`; do not write them to another repository. The owner decides whether to transfer and verify them in `career-pkm`. Never offer to edit Notion.

## Working notes from earlier applications

- **Build, don't retype.** For step 3, write `spec.json` with packet claim numbers, selected summary ID, bracket picks, verbs, and skills lines; then run `build_application.py`. It copies canonical wording and selected education, credentials, and publications from the local packet and writes full claim IDs to `claims-used.md`.
- **Numbers.** Copy literal values from packet metrics. If a selected claim lacks a needed metric, choose another packet claim or record the gap in `proposals.md`; never fill it by inference.
- **Cover letters.** Before finalizing, search earlier `applications/*/cover-letter.md` for sentences you reused. The owner's refrains (see `writing/style-guide.md`) may repeat; any other sentence should not.
- **Research.** Names found in third-party directories are unverified; keep them out of the letter and say so in `research.md`. Program names that search cannot confirm are JD wording only.
- **Builder defects.** If `build_application.py` or another script mishandles a claim (for example a stray space before the final period after a trailing bracket), do not edit the script on the application branch: `check_scope.py` forbids it. Pick another claim or work around it inside `applications/<slug>/`, record the defect in `proposals.md`, and fix the script on a separate `tooling/` branch.
- **Employer product names.** Names of the employer's own tools or programs go under Business Context in `keywords.txt`, not Forced; the checker would otherwise demand them on the resume as experience. Do not weaken the checker; reclassify and say why in `keywords.md`.
- **Title and filters.** The role title may appear only in the posting URL; note that in `keywords.md`. Put degree-field and eligibility questions in `match.md` for the owner.
- **Superpowers plugin.** If it is enabled, do not invoke its brainstorming, plan, worktree or finishing skills during `/apply`. This skill's steps and the `plan.md` approval gate replace them (CLAUDE.md "Superpowers plugin").
- **Paths.** The shell's working directory drifts between calls. Use absolute paths and re-run the checks from the repo root.
- **Application questions.** Save employer form responses to `applications/<slug>/application-answers.md`. Build them from the JD, basic company research, exact keyword analysis, the approved application plan, and the imported `application-facts.md`. Use the competitive-cartographer skill for positioning and values fit; cite claim IDs for personal facts and do not invent unsupported details. Keep each answer to about 120 to 150 words, lead with the answer, name a gap once, then pivot. Use past tense for ended roles based on packet dates. Treat reflections from earlier letters as lessons, not career facts. Delivery notes in `applications/profile-insights.md` are self-report guidance, never a fact source; do not put its labels in employer-facing content. Run the detector on the answer file.
- **Step 5 cost.** The vendored avoid-ai-writing detect pass needs its `references/patterns.md` read in full (about 745 lines). Run the script checks first and the skill pass once, on the final letter.

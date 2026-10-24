> **SUPERSEDED (2026-10-24).** This describes the original single-repo, KB-based workflow. It refers to files and sections that no longer exist here (an "Application mode" section in CLAUDE.md, `build_claims_view.py`, `.claude/agents`, `applications/_tools/`, mattpocock skills). The current flow is in `.claude/skills/apply/SKILL.md` and `docs/adr/0001-packet-delivery-by-push.md`.

# HANDOFF: Build the application workflow in career-pkm

Status (2026-10-10): scaffold built and merged to main. This file stays as the design record; current rules are in CLAUDE.md "Application mode".

Owner: Devika C. Dixit. Repo: devcd6/career-pkm (private). Written 2026-10-08.
Task for this session: read this file, then build the scaffold below on a new branch (no pushes to main). Stop at the checkpoints marked CHECKPOINT and wait for the owner.

## Goal
Run the job-application workflows from the "[AUGUST] Job Search" claude.ai chats inside Claude Code on the web, grounded in this repo's knowledge base (KB) instead of Notion, without ever modifying the KB.

## Source of truth
- Facts come from kb/ (kb/roles/*, skills.md, education.md, summaries.md, stories.md). Follow CLAUDE.md "Using this project as knowledge" rules. All 64 conflicts are resolved and tiers are set, so use canonical wording and cite the claim ID.
- Style comes from writing/style-guide.md (approved) and writing/samples/*. Do NOT use the pasted "cover letter insight" analyses from old chats; the style guide documents their errors.
- Owner rulings in kb/_user_decisions.md win. Key ones: NatCon26 18+ sessions and 6,000+ attendees; newsletter 8,000+; involuntary commitment scan "50 states and DC (51 jurisdictions)"; degree year 2025; NCMW title always "Project Coordinator"; no full-time/part-time labels; do not add Recovery Ready publication status; 4+ years experience.
- Notion is now only the application tracker. Do not use it as a fact source. Never offer to edit Notion; the owner edits Notion manually.
- The role files total about 884 KB, too big to read. Generate kb/_views/claims.md (id, canonical, tier, metrics for all 252 claims, about 20k tokens) and load that whole. Open a role file only to see variants for one claim ID.

## Hard rules (keep from CLAUDE.md)
1. _raw/ is read-only. kb/, resumes/ and writing/ are read-only for application sessions except for additive, user-approved root additions (see CLAUDE.md "Application mode").
2. Never invent, inflate, round or merge facts. Numbers come only from a claim's metrics, copied exactly.
3. New facts a session surfaces go to applications/<slug>/proposals.md first. Only the owner can verify them; with the owner's in-session approval they may be added to root on the application branch (CLAUDE.md "Application mode").
4. Application sessions write under applications/. Root changes are allowed only as approved additions, in a separate `kb:` commit. Every session ends by confirming the diff against main shows only applications/<slug>/ plus approved root paths.
5. Update CLAUDE.md rule 8 (it forbids pushing, which no longer fits cloud sessions on a private repo). Ask the owner to approve the new wording.

## Cloud-session mechanics (verified in docs)
- Plugins in enabledPlugins do not load in cloud sessions. Commit skills to .claude/skills/ instead.
- CLAUDE.md, .claude/skills, agents, commands and rules load from the clone. Hooks and permission rules in .claude/settings.json load only in single-repo sessions.
- Put deny rules for kb/, resumes/, writing/, _raw/ in .claude/settings.json (verify the syntax). A Bash command may bypass an Edit deny, so the end-of-session diff check is the backstop.
- Network access: confirm WebSearch/WebFetch work at the environment's level. If not, use Custom with a minimal allowlist, not Full.

## Skills
Commit patched copies into .claude/skills/:
- Keep in the default flow: job-description-analyzer, resume-tailor, resume-bullet-writer, resume-ats-optimizer, resume-section-builder, cover-letter-generator, avoid-ai-writing (copy its inner skills/avoid-ai-writing folder).
- Available on request only: cv-creator (docx/pdf export), competitive-cartographer, career-biographer.
- Dropped: interview-coach. Do not add it.
- Patches:
  - resume-bullet-writer: remove "every bullet needs a number" and "find related metrics." Numbers only from claim metrics.
  - Web-capable skills: search only the employer and role named in the JD, never resume text.
  - career-biographer: output to proposals.md only.
  - resume-tailor: replace scripts/resume_matcher.py (loose keyword overlap) with an exact-phrase JD matcher.
- Add one orchestrator skill, "apply", with the five steps below. Slash commands: /research, /analyze-jd, /tailor, /cover-letter, /check.

## Owner preferences (from her chats; write to writing/preferences.md)
Resume tailoring:
- No bullet cap for page length. Include every bullet that maps to the role or makes her stand out.
- Bullet ranges per role: NCMW 9-12, UCSB 5-8, Sanctuary Centers 8-11, ASEI 4-7, Casa Serena 4-6. (The NCMW label was missing in one old paste and assumed; she should confirm.)
- Output in a chat markdown code block, not docx. Single-space everything, including between bullets and skill groups. Also save the same text to applications/<slug>/resume.md. Docx or PDF only on request.
- Before output, re-screen every bullet: maps to role or stands out; keywords integrated; follows bullet best practice; high-impact starting verb unique within each role. Choose verbs from the claim's bracketed alternatives.
- Summary ends with one short mission-tie sentence ("Committed to...", "Dedicated to...") that matches the employer's mission without copying it. Samples are in her old chats; copy them into preferences.md.
- Check applications/ and INDEX.md for an existing version for the same employer before starting.

Keyword analysis:
- Exact JD wording only, no synonyms. Six categories: Title Keyword, Hard Skill, Action Keyword, Business Context (max 10), Domain Keyword (max 5), Hard Filter. Top 15 rank. Do not turn preferred qualifications into requirements. If she pastes a Notion AI keyword table, assess it independently; do not trust it.

Gaps:
- State real gaps; frame them in the cover letter, not with resume overreach. Ask rather than assume.

Writing:
- No em dashes in narrative prose. Cover letters follow writing/style-guide.md. Run avoid-ai-writing in detect mode first and protect her signature refrains unless she says to vary them.

## Per-application flow
Each step saves to applications/<YYYY-MM-DD>_<org>_<role>/ and also prints to chat.
1. /research: deep company and team research (mission, language, hiring patterns, team members, reviews). Save research.md. Only company and role text leaves the repo.
2. /analyze-jd: keywords.md and match.md (score, gaps, open questions).
3. /tailor: resume.md plus claims-used.md (every bullet mapped to a claim ID and the verb chosen).
4. /cover-letter: cover-letter.md from the style guide and the two closest samples.
5. /check: runs the scripts below, plus avoid-ai-writing detect.

## Scripts to write
- scripts/build_claims_view.py: generates kb/_views/claims.md.
- scripts/check_application.py: verifies numbers, titles and dates against the KB; bullet counts within ranges; unique verbs per role; no em dashes; single spacing; summary closer present; every bullet in claims-used.md.
- Provenance check: block output containing any number not found in the claim metrics (borrowed from career-ops; its implementation was not confirmed, so write it fresh).

## Existing tools reviewed (none adopted wholesale)
- varunr89/resume-tailoring-skill: borrow confidence-scored matching, checkpoints, stated gaps. It writes back to its library, so do not use it as-is.
- career-ops: borrow provenance check, labeled estimates, draft-only actions.
- Wasif0410/job-application-skills: borrow "forced keyword" flagging.
- Skip: proficientlyjobs (no truthfulness safeguards, auto-apply); Paramchoudhary resume-quantifier (fabrication risk, unread).

## Build order
1. Branch. Add the claims view script and generate the view.
2. Add settings.json deny rules and the CLAUDE.md application-mode section. CHECKPOINT: show the owner the proposed rule 8 wording.
3. Copy and patch the skills; add the "apply" skill and preferences.md.
4. Write check_application.py.
5. Dry run on one real JD the owner supplies. CHECKPOINT: owner reviews the output and the diff before merging. Status (2026-10-09): two dry runs were done. The owner deleted the MAVEN test application; the AAMC application (`applications/2026-10-09_aamc_*`, including `application-answers.md`) is the remaining worked example and awaits owner review.

## Integrating outside skills and agents (GitHub or web)
Goal: keep finding tools that improve the workflow without letting any of them touch the facts. Do this only when the owner asks, or at the end of a dry run to propose candidates. Never install from a search result silently.

Vet before adopting (all must pass; write the verdict to `applications/_tools/<name>.md`):
1. Source and license: public repo, license that permits copying (MIT, Apache-2.0). Record URL, commit hash and date. Prefer maintained repos with recent commits.
2. Read the whole SKILL.md, agent file and every script. Reject or strip anything that fabricates or "quantifies" metrics, auto-applies to jobs, sends data to external services, writes back to a library or the KB, runs network or shell commands, or tells the model to ignore other instructions.
3. Fit: it fills a gap in the five-step flow (research, JD analysis, tailoring, cover letter, check) or strengthens a check. Skip anything that duplicates a skill already here.
4. Patch, do not wrap: copy the files into `.claude/skills/<name>/` (or `.claude/agents/`), add the same "Project override" block used in the other skills (claims-only facts and numbers, writes only under `applications/`, web use limited to employer and role, Notion is a tracker only, no em dashes), and add a `VENDORED.md` with source, commit and review date. Plugins in `enabledPlugins` do not load in cloud sessions, so vendor the files.
5. Test on one existing application folder and run `python scripts/check_application.py` plus the end-of-session `git status` check before committing. Commit each tool on its own so it can be reverted. Never push to main.

Where to look (search with generic terms only, never resume or KB text): GitHub topics and searches for "claude code skills" with job search, resume tailoring, ATS, cover letter, job description analysis, company research, and writing-quality or AI-pattern detection; the Anthropic skills repositories; claudemarketplaces.com and agentskill.work listings (pointers only, always read the source repo). Prefer the tools already reviewed in this file.

Standing candidates and decisions:
- Adopted: conorbronsdon/avoid-ai-writing (MIT), vendored in `.claude/skills/avoid-ai-writing/`. Detect mode on cover letters only. Never edit or rewrite mode on resume.md.
- Adopted: mattpocock/skills, `skills/productivity` (MIT, commit 49dd158): grill-me, grilling, handoff, teach, to-questionnaire, wait-what, writing-for-agents, vendored in `.claude/skills/` at the owner's request on 2026-10-09. Deviations from the procedure above: only `teach` and `handoff` (the two that write files) carry a "Project override" block, the other five are unmodified; the vetting verdict is in `.claude/skills/VENDORED-mattpocock.md` instead of `applications/_tools/`; and all seven went in one commit. Cautions there: run `teach` outside the repo; `handoff` text can hold personal data.
- Borrow ideas only: varunr89/resume-tailoring-skill (confidence-scored matching, checkpoints, stated gaps; it writes back to its library); career-ops (provenance check, labeled estimates, draft-only actions); Wasif0410/job-application-skills (forced-keyword flagging); Faizee-Asad/job-seeker-claude-skills (job tracker CSV and application-packet layout; unreviewed).
- Skip: proficientlyjobs/proficiently-claude-skills (auto-apply, no truthfulness safeguards); Paramchoudhary resume-quantifier (fabrication risk).
- Agents worth building locally rather than importing: a read-only `kb-auditor` agent that re-checks resume.md against claims-used.md and the claims view in a fresh context, and a `company-researcher` agent restricted to WebSearch and WebFetch with employer and role only. Define them in `.claude/agents/` with tool lists that exclude Write outside applications/.

## Open items for the owner
- Confirm NCMW bullet range 9-12.
- Update the claude.ai project instructions to say the repo is the fact source and Notion is only the tracker. They still carry old numbers (17 vs 18 sessions, 5,000+ vs 6,000+, "all 50 states"). She pastes this in herself.
- Keep or vary refrain lines in cover letters.
- Approve any new outside tool before it is vendored (see "Integrating outside skills and agents").
- Done (owner approved 2026-10-09): `scripts/check_application.py` now treats a count written as a word in a claim's `metrics` (two through twelve) as also allowing its digit in a bullet. Tested on the AAMC folder: A-ncmw-project-coordinator-119 ("4 departments and 15+ external partners", empty `metrics`) passes only when mapped together with A-ncmw-project-coordinator-19, whose `metrics` say "four internal departments, 15+ external partner organizations". Claim 119 alone still fails until its `metrics` are filled.
- Update `writing/style-guide.md` (owner only; `writing/` is read-only here): it still says the Insights Discovery profile was not imported. The owner supplied it on 2026-10-09; a summary for application use is in `applications/profile-insights.md`.
- Decide whether `applications/profile-insights.md` and `applications/preferences.md` stay under `applications/` or move to `writing/`, and whether the AAMC `spec.json` stays.
- Fill the empty `metrics` on verified claims that carry numbers in their canonical wording (list in each application's `proposals.md`). `kb/` is read-only for application sessions.

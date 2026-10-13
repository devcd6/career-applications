---
name: resume-ats-optimizer
description: Check a career-pkm resume for ATS-safe structure and exact-phrase keyword coverage
---

# Resume ATS Optimizer (career-pkm)

Original generic body replaced; see git history.

## Checks (advisory, report only)

- Structure: single column, no tables or graphics, plain bullets, standard headings (Summary, Experience, Education, Skills, Certifications), consistent `YYYY-MM` or month-year dates, contact line in the body.
- Keywords: run `resume-tailor/scripts/exact_phrase_matcher.py`. Report JD phrases missing from the resume. Do not recommend adding a keyword the KB cannot support; list it as a gap in `match.md`. Spell out terms with the JD's own wording and acronym where the KB claim already contains both.
- No density targets, no "estimated new match score" unless produced by the matcher, and no fit percentage.
- Output stays markdown. DOCX or PDF only when the owner asks.

## Rules

Facts only from the imported `application-facts.md`; never edit claim wording or add a keyword the packet cannot support. Write under `applications/<slug>/` only. No em dashes.

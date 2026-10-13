---
name: job-description-analyzer
description: Analyze a job posting for exact keywords, hard filters, and gaps against an imported application-facts packet.
---

# Job Description Analyzer (career-applications)

Original generic body replaced; see git history. This is step 2 of the `apply` skill.

## Output: `keywords.md` and `match.md` in the application folder

**Keywords.** Exact JD wording only, no synonyms. Six categories: Title Keyword, Hard Skill, Action Keyword, Business Context (max 10), Domain Keyword (max 5), Hard Filter. Rank the top 15 with JD and application-facts packet counts from `exact_phrase_matcher.py` (`--resume application-facts.md`). Flag forced keywords (short phrases the JD requires verbatim). A forced keyword must be supported by the packet. An employer's own product, tool or program name (for example its referral dashboard) is Business Context, never Forced, unless the packet shows it was used. Never turn preferred qualifications into requirements. If the owner pastes a Notion AI keyword table, assess it independently.

**Match.** Sections: Score (phrase coverage, not a fit percentage), Hard filters (each with met, unmet or ask), Strong matches (JD requirement to application-facts packet IDs), Real gaps, Open questions for the owner. Do not use LinkedIn or contacts.

## Rules

Facts only from `application-facts.md`. Report gaps; never fill them. Web use is limited to the employer and role from the JD. Write under `applications/<slug>/` only. No em dashes.

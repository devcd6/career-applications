---
name: resume-section-builder
description: Build the summary and skills sections of an application resume from the Packet, tailored to a target role
---

# Resume Section Builder (career-applications)

Original generic body replaced; see git history.

## Sections

- **Summary:** compose from the selected summary in `application-facts.md` and selected claims. Keep career facts supported by those packet entries. End with one short mission-tie sentence ("Committed to...", "Dedicated to...") that matches the employer's mission without copying it; patterns are in `applications/preferences.md`.
- **Skills:** group only the exact skill wording selected into `application-facts.md`. Mirror JD wording only where the packet supports it.
- **Education, credentials, and publications:** use only selected entries in `application-facts.md`; `scripts/build_application.py` renders them.
- Experience bullets belong to `resume-bullet-writer`; titles, dates and employers come from the packet's role header.

## Rules

No invented, inflated, rounded or merged facts. Numbers only from packet metrics. Section order and layout follow `applications/preferences.md`. Write under `applications/<slug>/` only. No em dashes.

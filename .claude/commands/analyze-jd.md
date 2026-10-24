---
description: Step 2: keyword analysis and match for a job description
---
Use the `apply` skill, step 2 (/analyze-jd), for: $ARGUMENTS. Run `python scripts/preflight.py applications/<slug>` first. Write keywords.txt and validate it with `python scripts/check_keywords.py applications/<slug>`. If preflight says the Packet is missing, stop and print the Packet request; do not write keywords.md or match.md. Once application-facts.md exists, rank with packet counts, save keywords.md and match.md in the application folder, and print them.

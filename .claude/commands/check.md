---
description: Step 5: run provenance and style checks on an application
---
Use the `apply` skill, step 5 (/check), for: $ARGUMENTS (an application folder). Run `python scripts/preflight.py` on it first. Run scripts/check_application.py, scripts/check_research.py, the cover-letter detectors, check_scope.py and check_handoff.py, and report every failure. Run the avoid-ai-writing detect pass once on the final letter. Write `handoff.md` only after every check passes, then run check_handoff.py. A failed check stops the run; never weaken it or work around it.

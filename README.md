# career-applications

Private workspace for job applications and resume tailoring. The complete career source of truth, reusable research, and interview preparation live in `career-pkm`.

## Contents

- `applications/`: historical and current opening-specific records.
- `applications/preferences.md` and `applications/profile-insights.md`: application-writing preferences and delivery guidance.
- `writing/`: approved style guide and cover-letter samples.
- `.claude/`: application workflow commands and skills.
- `scripts/`: resume generation, application checks, source-tagged research validation, handoff checks, `check_scope.py` (application and tooling changes stay in separate branches) and `preflight.py`.
- `tests/`: `python -m unittest discover -s tests` and `bash scripts/test_session_start_handoff.sh`; the same run in `.github/workflows/test.yml`.
- `docs/`: `adr/` (decisions, ADR 0001 accepted) and `history/` (superseded handoffs). `CONTEXT.md` defines the vocabulary (Opening, Packet, Gate).

Each new application folder receives an `application-facts.md` packet, pushed by `/build-packet` in `career-pkm` after the owner approves the selection (ADR 0001) or copied by hand. It contains only selected, source-traceable career facts needed for that opening. Do not add the full career KB, source resumes, or raw files here.

After submission, generate an interview handoff packet. The owner imports it into `career-pkm`, where deep company/industry research, interview preparation, and career-development queries are maintained.

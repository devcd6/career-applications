# Career applications

Private repository that owns job-application records and tailoring. Career facts live in `career-pkm`; this repository sees only the selected Packet for each Opening.

## Language

**Opening**:
One specific job posting the owner is applying to, identified by employer and role.
_Avoid_: job, listing, position

**Application folder**:
The single folder that holds every artifact for one Opening, named by date, employer and role.
_Avoid_: project, workspace, case

**Packet**:
The owner-selected set of career claims, summary, skills and credentials, with source IDs, that is the only source of personal career facts for one Opening. It is stored as `application-facts.md` in the Application folder.
_Avoid_: KB export, profile

**Packet request**:
A fact-free message that tells the owner how to get a Packet for an Opening: which Opening, which public files to read, which command to run, and where to deliver the result.
_Avoid_: handoff, ticket, ask

**Selection proposal**:
A ranked, advisory list of claims proposed for one Opening, grouped by role and listing JD phrases no claim covers, which the owner approves or edits before a Packet is built.
_Avoid_: shortlist, recommendation, ranking

**Gate**:
A point where the workflow stops until the owner decides. There are two: approval of the Selection proposal and approval of the plan.
_Avoid_: checkpoint, review step, pause

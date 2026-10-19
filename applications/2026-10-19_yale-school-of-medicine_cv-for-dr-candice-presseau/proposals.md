# Proposals (new or missing facts, owner decides)

1. (superseded by item 9) Sanctuary Centers, Veterans work. Owner said (2026-10-19) to include that she "worked with VA and other veterans services on behalf of veteran clients". The packet only supports A-sanctuary-centers-housing-coordinator-08 ("Served Veterans through HUD-VASH and related programs") and -07 (HUD-VASH among subsidy programs). The resume uses claim -08 as written. The VA and other veterans services coordination wording is not in the packet. To use it, the owner can confirm it and add it in career-pkm as a claim (additive, own commit), then regenerate the packet.
2. CAPM: the packet notes the 05/2026 expected completion has passed. The resume says "in progress" with no date. Owner to confirm current status.
3. No contact details in the packet. Header holds placeholders.
4. Title: UCSB heading uses "Research Project Coordinator", one of the KB title variants for that role (owner request).
5. Skills lines: the packet has no selected skills, so the skills block is drawn from wording in the selected claims and summary S-03. Owner to confirm, or add skills to the packet via career-pkm.
6. Header contact line is the one hardcoded in `scripts/build_application.py`. Role order is reverse chronological by end date.
7. Summary is adapted from S-03 for a research audience. The closing sentence is S-03's own. It does not claim trauma-specific or Veteran-specific research experience.
8. Bullets rebuilt 2026-10-19 to broader, multi-project claims; single-topic bullets (involuntary commitment scan, ibogaine scan, NatCon26 logistics, e-learning course) were dropped.
9. Owner-stated facts (2026-10-19, in session) used on the resume but not in the packet. Each needs promotion to `career-pkm` (additive claim, tier single-source, or verified if the owner says accurate) before `check_application.py` can pass. Wording is the owner's, lightly verbed:
   - NCMW: "collaboration with veteran-led ibogaine advocacy groups, such as Americans for Ibogaine" (OWNER-2026-10-19-N1).
   - Sanctuary: Veteran client base; navigation of VA benefits and eligibility for services (S1); collaboration with the VA and other veterans services on behalf of Veteran clients (S2); collaboration on sharing of VA client information with general SUD and social services programs (S3). HUD-VASH itself is already packet-backed (A-sanctuary-centers-housing-coordinator-07, -08).
   - The summary line "including Veterans served through HUD-VASH and VA benefits navigation" and two skills entries (VA benefits and eligibility navigation; HUD-VASH) rest on the same facts.
   - Note: `_raw/notion/master-career-profile.md` names Americans for Ibogaine people as NatCon26 session speakers and the group as a surveyed advocacy organization. It does not describe veteran-led collaboration, and no KB claim does.

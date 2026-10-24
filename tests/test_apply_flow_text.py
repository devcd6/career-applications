import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / ".claude" / "skills" / "apply" / "SKILL.md").read_text(encoding="utf-8")
COMMANDS = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / ".claude" / "commands").glob("*.md")}


def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    assert m, f"missing section: {heading}"
    return m.group(1)


class ApplySkillFlow(unittest.TestCase):
    def test_preflight_runs_first_and_resumes(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertLess(flow.index("scripts/preflight.py"), flow.index("scripts/check_keywords.py"))
        self.assertIn("first missing", flow)

    def test_stops_at_packet_request_without_jd_only_outputs(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertIn("Packet request", flow)
        self.assertRegex(flow, r"(?i)do not write `keywords\.md` or `match\.md`")

    def test_validator_then_packet_count_ranking(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertLess(flow.index("check_keywords.py"), flow.index("--resume application-facts.md"))

    def test_plan_is_only_gate_before_building(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertIn("Gate 2", flow)
        self.assertRegex(flow, r"(?i)only gate")

    def test_one_pass_after_approval_with_explicit_stops(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertRegex(flow, r"(?i)one pass")
        self.assertRegex(flow, r"(?i)failed check stops")
        self.assertRegex(flow, r"(?i)eligibility")
        self.assertRegex(flow, r"(?i)degree-field")
        self.assertIn("proposals.md", flow)

    def test_privacy_rules_kept(self):
        for phrase in ("Web queries contain only employer, role, and relevant program names",
                       "Never offer to edit Notion",
                       "never invent, inflate, round, or merge"):
            self.assertIn(phrase, SKILL)

    def test_commands_call_preflight_and_validator(self):
        for name in ("research", "analyze-jd", "tailor", "cover-letter", "check"):
            self.assertIn("scripts/preflight.py", COMMANDS[name], name)
        self.assertIn("scripts/check_keywords.py", COMMANDS["analyze-jd"])
        self.assertIn("check_scope.py", COMMANDS["check"])

    def test_tailor_command_has_no_rank_md_and_stops_for_plan(self):
        self.assertNotIn("rank.md", COMMANDS["tailor"])
        self.assertIn("plan.md", COMMANDS["tailor"])


if __name__ == "__main__":
    unittest.main()

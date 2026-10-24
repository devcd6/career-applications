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

    def test_manual_copy_fallback_until_adr_accepted(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertRegex(flow, r"(?i)copies? .*application-facts\.md")
        self.assertIn("ADR 0001", flow)

    def test_step_two_does_not_contradict_phrase_ranking(self):
        self.assertNotIn("Do not run claim ranking", SKILL)
        self.assertIn("Do not rank claims", SKILL)

    def test_handoff_written_only_after_checks_pass(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertRegex(flow, r"(?i)handoff\.md`? only after every check passes")

    def test_each_step_commits_and_pushes_to_designated_branch(self):
        git = section(SKILL, "Commits and PR")
        self.assertRegex(git, r"(?i)one commit per (completed )?step")
        self.assertRegex(git, r"(?i)push(es)? .*designated branch")
        self.assertIn("applications/<slug>/", git)
        self.assertRegex(git, r"(?i)never force-push")
        self.assertRegex(git, r"(?i)non-fast-forward.*pull --no-rebase")

    def test_single_pr_found_by_head_branch(self):
        git = section(SKILL, "Commits and PR")
        self.assertRegex(git, r"(?i)list_pull_requests")
        self.assertRegex(git, r"(?i)head branch")
        self.assertRegex(git, r"(?i)open (it )?only if (none|no)")
        self.assertRegex(git, r"(?i)ready for review")
        self.assertRegex(git, r"(?i)later steps? reuse")

    def test_subscribes_once_per_pr(self):
        git = section(SKILL, "Commits and PR")
        self.assertIn("subscribe_pr_activity", git)
        self.assertRegex(git, r"(?i)once")
        self.assertRegex(git, r"(?i)re-run.*(does not|never).*(second|another|duplicate)")

    def test_commit_and_pr_text_carry_no_career_facts(self):
        git = section(SKILL, "Commits and PR")
        self.assertRegex(git, r"(?i)claim IDs and paths only")
        self.assertRegex(git, r"(?i)never .*(resume|packet|KB) text")
        self.assertIn("Commit message", git)
        self.assertIn("PR body", git)

    def test_two_gate_flow_points_to_commit_section(self):
        flow = section(SKILL, "Two-gate flow")
        self.assertIn("Commits and PR", flow)

    def test_research_command_is_research_only(self):
        self.assertNotIn("keywords.txt", COMMANDS["research"])
        self.assertNotIn("Packet request", COMMANDS["research"])

    def test_tailor_command_has_no_rank_md_and_stops_for_plan(self):
        self.assertNotIn("rank.md", COMMANDS["tailor"])
        self.assertIn("plan.md", COMMANDS["tailor"])


if __name__ == "__main__":
    unittest.main()

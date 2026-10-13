import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_application.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_application.py"
RESEARCH_SCRIPT = ROOT / "scripts" / "check_research.py"
SKILL = "Project Tracking (Time Management, Deliverables)"


def facts_packet():
    return (
        "# Application facts packet\n\n"
        "## demo-role\n"
        "employer: Example Organization\n"
        "title: Program Coordinator\n"
        "dates: 2024-01 to 2024-12\n"
        "location: Remote, TX\n\n"
        "### A-demo-role-01 | verified\n"
        "canonical: Coordinated a pilot program\n"
        "metrics: 999+\n\n"
        "# Selected summaries\n"
        "### S-01\n"
        "summary: Program coordinator with community experience.\n"
        "source: kb/summaries.md#S-01\n\n"
        "# Selected education and credentials\n"
        "### EDU-01 Bachelor of Arts in Communications\n"
        "degree: Bachelor of Arts in Communications\n"
        "institution: Example University\n"
        "location: Austin, TX\n"
        "end: 2025\n"
        "tier: consistent\n"
        "source: kb/education.md#EDU-01\n"
        "### CERT-03 Community Program Certificate\n"
        "tier: consistent\n"
        "source: kb/education.md#CERT-03\n"
        "### PUB-01 Community Practice Article\n"
        "authors: A. Example\n"
        "date: 2024-01-01\n"
        "title: Community Practice Article\n"
        "publisher: Example Journal\n"
        "url: https://example.org/article\n"
        "tier: consistent\n"
        "source: kb/education.md#PUB-01\n\n"
        "# Selected skills\n"
        f"- {SKILL} | source: kb/skills.md\n"
    )


class ApplicationPacketTests(unittest.TestCase):
    def test_resume_builder_uses_selected_facts_from_local_packet(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "application"
            folder.mkdir()
            packet = folder / "application-facts.md"
            packet.write_text(facts_packet(), encoding="utf-8")
            spec = {
                "title": "Resume",
                "summary_source": "S-01",
                "summary": "Program coordinator. Committed to useful programs.",
                "skills": [f"**Program Management:** {SKILL}"],
                "roles": {
                    "demo-role": [
                        {"claims": [1], "verb": "Coordinated"},
                    ],
                },
            }
            (folder / "spec.json").write_text(json.dumps(spec), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(BUILD_SCRIPT), str(folder)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            resume = (folder / "resume.md").read_text(encoding="utf-8")
            claims_used = (folder / "claims-used.md").read_text(encoding="utf-8")
            self.assertIn("EXAMPLE ORGANIZATION", resume)
            self.assertIn("Program Coordinator", resume)
            self.assertIn("Remote, TX  Jan 2024 - Dec 2024", resume)
            self.assertIn("Coordinated a pilot program", resume)
            self.assertIn("A-demo-role-01", claims_used)
            self.assertIn("Example University", resume)
            self.assertIn("Community Program Certificate", resume)
            self.assertIn("Community Practice Article", resume)
            self.assertIn(SKILL, resume)
            self.assertNotIn("Google Project Management Certificate", resume)

    def test_application_checker_uses_folder_facts_packet_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "application"
            folder.mkdir()
            (folder / "application-facts.md").write_text(facts_packet(), encoding="utf-8")
            (folder / "resume.md").write_text(
                "## SUMMARY\n\nCoordinated 999+ pilot events. Committed to responsive operations.\n",
                encoding="utf-8",
            )
            (folder / "claims-used.md").write_text(
                "- Coordinated 999+ pilot events | A-demo-role-01 | verified | Coordinated\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), str(folder)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertIn("0 error(s)", result.stdout)

    def test_application_checker_fails_without_facts_packet(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "application"
            folder.mkdir()
            (folder / "resume.md").write_text("## SUMMARY\n\nText.\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), str(folder)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("no application-facts packet found", result.stdout)

    def test_basic_company_research_needs_no_career_kb_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "application"
            folder.mkdir()
            report = folder / "research.md"
            report.write_text(
                "# Company brief\n\n"
                "## Company snapshot\n"
                "- The organization describes its mission on its website. [src: https://example.org/about]\n\n"
                "## Role context\n"
                "- The posting emphasizes program coordination. [JD]\n\n"
                "## Language to mirror\n"
                "- Use the employer's stated phrase. [src: https://example.org/about]\n\n"
                "## Source ledger\n"
                "| URL | Owner | Date seen | Used in |\n"
                "|-----|-------|-----------|---------|\n"
                "| https://example.org/about | employer | 2026-10-13 | Company snapshot; Language |\n\n"
                "## Questions and unknowns\n"
                "- Confirm which program this role will support.\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(RESEARCH_SCRIPT), str(folder)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_basic_company_research_rejects_untagged_findings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "application"
            folder.mkdir()
            report = folder / "research.md"
            report.write_text(
                "# Company brief\n\n"
                "## Company snapshot\n- Unattributed finding.\n"
                "## Role context\n- Requirement from the JD. [JD]\n"
                "## Language to mirror\n- Employer language. [not found]\n"
                "## Source ledger\n| URL | Owner | Date seen | Used in |\n"
                "## Questions and unknowns\n- Ask which team this role supports.\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(RESEARCH_SCRIPT), str(folder)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("[tags]", result.stdout)


if __name__ == "__main__":
    unittest.main()

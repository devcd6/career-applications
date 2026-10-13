import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_interview_packet.py"
CHECK = ROOT / "scripts" / "check_interview_packet.py"

FILES = {
    "jd.md": "# Coordinator\nSupport programs.\n",
    "resume.md": "# Devika C. Dixit\n- Managed member communications.\n",
    "claims-used.md": "- Managed comms | A-ncmw-project-coordinator-24 | consistent | Managed\n"
    "- Other | A-ncmw-project-coordinator-19, A-ncmw-project-coordinator-24 | verified | Organized\n",
    "research.md": "# Research\nSource: https://example.org/about (seen 2026-10-13)\n",
    "match.md": "# Match\n\n## Strong matches\nx\n\n## Real gaps\n- No grant writing.\n\n## Open questions\nq\n",
}


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)


def make_folder(tmp, drop=(), rename_resume=False):
    folder = Path(tmp) / "2026-10-13_org_role"
    folder.mkdir()
    for name, text in FILES.items():
        if name in drop:
            continue
        if name == "resume.md" and rename_resume:
            name = "submitted-resume.md"
        (folder / name).write_text(text, encoding="utf-8")
    (folder / "cover-letter.md").write_text("UNRELATED LETTER TEXT", encoding="utf-8")
    return folder


class InterviewPacketTests(unittest.TestCase):
    def build(self, folder):
        out = folder / "interview-packet.md"
        return run(BUILD, folder, "--out", out), out

    def test_complete_packet_builds_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp)
            r, out = self.build(folder)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = out.read_text(encoding="utf-8")
            for h in ("## Job description", "## Submitted resume", "## Claims used", "## Role research", "## Known gaps"):
                self.assertIn(h, text)
            self.assertIn("slug: 2026-10-13_org_role", text)
            self.assertEqual(text.count("- A-ncmw-project-coordinator-24"), 1)
            self.assertIn("- A-ncmw-project-coordinator-19", text)
            self.assertIn("No grant writing.", text)
            self.assertIn("#### Requirements", text)
            self.assertNotIn("UNRELATED LETTER TEXT", text)
            self.assertEqual(run(CHECK, out).returncode, 0)

    def test_submitted_resume_name_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp, rename_resume=True)
            r, _ = self.build(folder)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_inputs_rejected_and_nothing_written(self):
        for drop in ("jd.md", "resume.md", "claims-used.md", "research.md"):
            with self.subTest(drop=drop), tempfile.TemporaryDirectory() as tmp:
                folder = make_folder(tmp, drop=(drop,))
                r, out = self.build(folder)
                self.assertNotEqual(r.returncode, 0)
                self.assertFalse(out.exists())

    def test_missing_gaps_section_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp)
            (folder / "match.md").write_text("# Match\n\n## Strong matches\nx\n", encoding="utf-8")
            r, out = self.build(folder)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(out.exists())

    def test_checker_rejects_incomplete_or_extra_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make_folder(tmp)
            _, out = self.build(folder)
            good = out.read_text(encoding="utf-8")
            cases = {
                "no resume": good.replace("## Submitted resume", "## Resume"),
                "no claims": good.replace("- A-ncmw-project-coordinator-19", "- none").replace("- A-ncmw-project-coordinator-24", "- none"),
                "extra": good + "\n## Cover letter\ntext\n",
                "no url": good.replace("https://example.org/about", "example"),
            }
            for name, text in cases.items():
                with self.subTest(name):
                    bad = Path(tmp) / "bad.md"
                    bad.write_text(text, encoding="utf-8")
                    self.assertNotEqual(run(CHECK, bad).returncode, 0)


if __name__ == "__main__":
    unittest.main()

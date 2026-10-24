import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATCHER = ROOT / ".claude" / "skills" / "resume-tailor" / "scripts" / "exact_phrase_matcher.py"

JD = "Coordinate training events. Prepare reports for training events and customer service.\n"
PHRASES = "Hard Skill | training events\nHard Skill | customer service\nHard Skill | Salesforce\n"
RESUME = "Coordinated training events for attendees.\n"


def run(*args, files):
    with tempfile.TemporaryDirectory() as tmp:
        paths = {}
        for name, text in files.items():
            paths[name] = Path(tmp) / name
            paths[name].write_text(text, encoding="utf-8")
        argv = [sys.executable, str(MATCHER)]
        for arg in args:
            argv.append(str(paths[arg]) if arg in paths else arg)
        return subprocess.run(argv, capture_output=True, text=True)


class JdOnlyMode(unittest.TestCase):
    def test_runs_without_resume_and_prints_jd_counts(self):
        r = run("--jd", "jd.md", "--phrases", "kw.txt", files={"jd.md": JD, "kw.txt": PHRASES})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"training events\s+2\b")
        self.assertRegex(r.stdout, r"customer service\s+1\b")

    def test_jd_only_has_no_resume_column(self):
        r = run("--jd", "jd.md", "--phrases", "kw.txt", files={"jd.md": JD, "kw.txt": PHRASES})
        self.assertNotIn("resume", r.stdout)

    def test_jd_only_still_flags_phrases_not_in_jd(self):
        r = run("--jd", "jd.md", "--phrases", "kw.txt", files={"jd.md": JD, "kw.txt": PHRASES})
        self.assertIn("NOT IN JD  Salesforce", r.stdout)

    def test_jd_only_json_omits_resume_counts(self):
        r = run("--jd", "jd.md", "--phrases", "kw.txt", "--json", files={"jd.md": JD, "kw.txt": PHRASES})
        rows = json.loads(r.stdout)
        self.assertEqual(rows[0]["in_jd"], 2)
        self.assertNotIn("in_resume", rows[0])

    def test_resume_without_phrases_is_an_error(self):
        r = run("--jd", "jd.md", "--resume", "resume.md", files={"jd.md": JD, "resume.md": RESUME})
        self.assertNotEqual(r.returncode, 0)

    def test_no_phrases_and_no_suggest_is_an_error(self):
        r = run("--jd", "jd.md", files={"jd.md": JD})
        self.assertNotEqual(r.returncode, 0)


class TwoInputModeUnchanged(unittest.TestCase):
    def test_two_input_output_keeps_resume_column_and_missing_flag(self):
        r = run("--jd", "jd.md", "--resume", "resume.md", "--phrases", "kw.txt",
                files={"jd.md": JD, "resume.md": RESUME, "kw.txt": PHRASES})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("jd  resume", r.stdout)
        self.assertRegex(r.stdout, r"training events\s+2\s+1\b")
        self.assertRegex(r.stdout, r"customer service\s+1\s+0\s+<- missing from resume")
        self.assertIn("NOT IN JD  Salesforce", r.stdout)

    def test_two_input_json_keeps_resume_counts(self):
        r = run("--jd", "jd.md", "--resume", "resume.md", "--phrases", "kw.txt", "--json",
                files={"jd.md": JD, "resume.md": RESUME, "kw.txt": PHRASES})
        rows = json.loads(r.stdout)
        self.assertEqual(rows[0]["in_resume"], 1)

    def test_suggest_still_works_alone(self):
        r = run("--jd", "jd.md", "--suggest", "5", files={"jd.md": JD})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("training events", r.stdout)


if __name__ == "__main__":
    unittest.main()

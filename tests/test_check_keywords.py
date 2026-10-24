import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_keywords.py"

JD = (
    "Education Coordinator I. Associate’s Degree required. Prepare continuing education (CE) credits "
    "records and trouble-shoot technical issues. Responding to correspondence and preparing reports.\n"
)


def run(keywords, jd=JD, folder_mode=False):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "jd.md").write_text(jd, encoding="utf-8")
        (base / "keywords.txt").write_text(keywords, encoding="utf-8")
        if folder_mode:
            argv = [sys.executable, str(SCRIPT), str(base)]
        else:
            argv = [sys.executable, str(SCRIPT), "--jd", str(base / "jd.md"), "--keywords", str(base / "keywords.txt")]
        return subprocess.run(argv, capture_output=True, text=True)


class Validator(unittest.TestCase):
    def test_all_phrases_found_exits_zero(self):
        r = run("Hard Skill | correspondence\nHard Skill | reports\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ok", r.stdout.lower())

    def test_missing_phrase_exits_nonzero_and_names_it(self):
        r = run("Hard Skill | Salesforce\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Salesforce", r.stdout)

    def test_phrase_with_missing_parentheses_explains_punctuation(self):
        r = run("Hard Skill | CE credits\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("CE credits", r.stdout)
        self.assertIn("punctuation", r.stdout)
        self.assertIn("(CE)", r.stdout)

    def test_missing_apostrophe_explains_punctuation(self):
        r = run("Hard Filter | Associates Degree\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("punctuation", r.stdout)

    def test_curly_apostrophe_in_jd_matches_straight_in_keywords(self):
        r = run("Hard Filter | Associate's Degree\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_hyphen_versus_space_is_explained(self):
        r = run("Hard Skill | trouble shoot\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hyphen", r.stdout)

    def test_inflection_names_the_jd_form(self):
        r = run("Action Keyword | respond\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Responding", r.stdout)

    def test_plural_names_the_jd_form(self):
        r = run("Hard Skill | report\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("reports", r.stdout)

    def test_every_unmatched_phrase_is_reported(self):
        r = run("Hard Skill | Salesforce\nHard Skill | Zoom\nHard Skill | reports\n")
        self.assertIn("Salesforce", r.stdout)
        self.assertIn("Zoom", r.stdout)
        flagged = [l for l in r.stdout.splitlines() if l.startswith("NOT FOUND")]
        self.assertEqual(len(flagged), 2)

    def test_comments_and_blank_lines_are_ignored(self):
        r = run("# note\n\nHard Skill | reports\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unknown_category_prefix_is_part_of_the_phrase(self):
        r = run("Other | reports\n")
        self.assertNotEqual(r.returncode, 0)

    def test_folder_argument_reads_jd_and_keywords(self):
        r = run("Hard Skill | reports\n", folder_mode=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_file_is_an_error(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent-folder"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_empty_keyword_file_is_an_error(self):
        r = run("# nothing\n")
        self.assertEqual(r.returncode, 2)


class ReviewFixes(unittest.TestCase):
    def test_hash_in_a_phrase_is_reported_not_truncated(self):
        r = run("Hard Skill | C#\n", jd="We use C and C++ daily.\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("C#", r.stdout)
        self.assertIn("comment", r.stdout)

    def test_unreadable_encoding_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "jd.md").write_bytes(b"caf\xe9 and reports\n")
            (base / "keywords.txt").write_text("Hard Skill | reports\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(base)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_short_last_word_is_not_called_an_inflection(self):
        r = run("Hard Skill | HR\n", jd="Track hrs and items weekly.\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found in the JD", r.stdout)
        self.assertNotIn("hrs", r.stdout)

    def test_unrelated_longer_word_is_not_called_an_inflection(self):
        r = run("Hard Skill | data\n", jd="Maintain the database daily.\n")
        self.assertIn("not found in the JD", r.stdout)

    def test_inflection_quotes_the_jd_with_its_original_case(self):
        r = run("Action Keyword | respond\n", jd="Responding to donors.\n")
        self.assertIn('"Responding"', r.stdout)

    def test_en_dash_in_keyword_still_gets_hyphen_diagnosis(self):
        r = run("Hard Skill | trouble\u2013shoot\n", jd="Trouble shoot issues.\n")
        self.assertIn("hyphen", r.stdout)

    def test_closed_compound_is_diagnosed_as_spacing(self):
        r = run("Hard Skill | troubleshoot\n", jd="Trouble-shoot issues.\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hyphen or spacing", r.stdout)

    def test_duplicate_phrases_are_counted_once(self):
        r = run("Hard Skill | Salesforce\nDomain Keyword | Salesforce\nHard Skill | reports\n")
        flagged = [l for l in r.stdout.splitlines() if l.startswith("NOT FOUND")]
        self.assertEqual(len(flagged), 1)
        self.assertIn("1 of 2 phrases", r.stdout)


if __name__ == "__main__":
    unittest.main()

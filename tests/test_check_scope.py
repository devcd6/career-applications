import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_scope import classify  # noqa: E402


class ScopeTests(unittest.TestCase):
    def test_application_only(self):
        kind, errors = classify(["applications/2026-10-24_hjf_x/keywords.txt", "applications/2026-10-24_hjf_x/plan.md"])
        self.assertEqual(("application", []), (kind, errors))

    def test_tooling_only(self):
        kind, errors = classify(["docs/adr/0001-packet-delivery-by-push.md", "scripts/check_scope.py", "CLAUDE.md"])
        self.assertEqual(("tooling", []), (kind, errors))

    def test_mixed_branch_is_rejected(self):
        _, errors = classify(["applications/a_b_c/plan.md", "scripts/check_scope.py"])
        self.assertTrue(any("one branch" in e for e in errors))

    def test_two_application_folders_rejected(self):
        _, errors = classify(["applications/a_b_c/plan.md", "applications/d_e_f/plan.md"])
        self.assertTrue(any("more than one" in e for e in errors))

    def test_owner_files_and_career_pkm_paths_rejected(self):
        for path in ("applications/preferences.md", "writing/style-guide.md", "kb/roles/x.md", "INDEX.md", "notes.txt"):
            _, errors = classify([path])
            self.assertTrue(errors, path)


if __name__ == "__main__":
    unittest.main()

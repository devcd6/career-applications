import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "preflight.py"
SLUG = "2026-10-24_example-org_education-coordinator"
PERSONAL = "Jane Q. Example led 18 sessions at 99% satisfaction"


def build(tmp, files, slug=SLUG):
    folder = Path(tmp) / "applications" / slug
    folder.mkdir(parents=True)
    for name in files:
        (folder / name).write_text(PERSONAL + "\n", encoding="utf-8")
    return folder


def run(folder, *extra, env=None):
    full_env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
    full_env.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPT), str(folder), *extra],
                          capture_output=True, text=True, env=full_env)


def next_step(out):
    for line in out.splitlines():
        if line.startswith("next:"):
            return line.split(":", 1)[1].split()[0]
    return None


class States(unittest.TestCase):
    def test_empty_folder_asks_for_the_jd(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, []))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(next_step(r.stdout), "add-jd")

    def test_missing_folder_counts_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(Path(tmp) / "applications" / SLUG)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(next_step(r.stdout), "add-jd")

    def test_jd_only_asks_for_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md"]))
            self.assertEqual(next_step(r.stdout), "research")

    def test_research_without_keywords_asks_for_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md"]))
            self.assertEqual(next_step(r.stdout), "keywords")

    def test_research_and_keywords_without_packet_stops_at_packet_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt"]),
                    "--session-id", "session_abc", "--branch", "claude/example-branch")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(next_step(r.stdout), "packet")
            for needle in (SLUG, f"applications/{SLUG}", "jd.md", "keywords.txt",
                           f"/build-packet {SLUG}", "session_abc", "claude/example-branch"):
                self.assertIn(needle, r.stdout)

    def test_packet_request_is_absent_in_other_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md"]))
            self.assertNotIn("Packet request", r.stdout)

    def test_packet_present_resumes_at_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md"]))
            self.assertEqual(next_step(r.stdout), "analyze")
            self.assertNotIn("Packet request", r.stdout)

    def test_analysis_done_asks_for_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md",
                                "keywords.md", "match.md"]))
            self.assertEqual(next_step(r.stdout), "plan")

    def test_plan_without_spec_waits_for_owner_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md",
                                "keywords.md", "match.md", "plan.md"]))
            self.assertEqual(next_step(r.stdout), "plan-approval")

    def test_spec_without_resume_asks_for_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md",
                                "keywords.md", "match.md", "plan.md", "spec.json"]))
            self.assertEqual(next_step(r.stdout), "build")

    def test_resume_without_letter_asks_for_cover_letter(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md",
                                "keywords.md", "match.md", "plan.md", "spec.json",
                                "resume.md", "claims-used.md"]))
            self.assertEqual(next_step(r.stdout), "cover-letter")

    def test_letter_without_handoff_asks_for_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md",
                                "keywords.md", "match.md", "plan.md", "spec.json",
                                "resume.md", "claims-used.md", "cover-letter.md"]))
            self.assertEqual(next_step(r.stdout), "check")

    def test_complete_folder_is_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md",
                                "keywords.md", "match.md", "plan.md", "spec.json", "resume.md",
                                "claims-used.md", "cover-letter.md", "handoff.md"]))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(next_step(r.stdout), "done")

    def test_empty_file_counts_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = build(tmp, ["jd.md"])
            (folder / "research.md").write_text("", encoding="utf-8")
            self.assertEqual(next_step(run(folder).stdout), "research")


class Details(unittest.TestCase):
    def test_session_id_defaults_to_the_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt"]),
                    env={"CLAUDE_CODE_SESSION_ID": "session_from_env"})
            self.assertIn("session_from_env", r.stdout)

    def test_unknown_session_is_stated_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt"]))
            self.assertIn("session: unknown", r.stdout)

    def test_file_contents_never_reach_the_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt", "application-facts.md"]))
            self.assertNotIn("Jane", r.stdout)
            self.assertNotIn("99%", r.stdout)

    def test_every_artifact_is_listed_present_or_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md"]))
            self.assertRegex(r.stdout, r"jd\.md\s+present")
            self.assertRegex(r.stdout, r"research\.md\s+missing")

    def test_existing_folder_for_same_opening_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, ["jd.md"], slug="2026-09-01_example-org_education-coordinator")
            r = run(Path(tmp) / "applications" / SLUG)
            self.assertIn("same opening: 2026-09-01_example-org_education-coordinator", r.stdout)
            self.assertIn("tell the owner", r.stdout)

    def test_other_role_at_same_employer_is_information_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, ["jd.md"], slug="2026-09-01_example-org_older-role")
            r = run(Path(tmp) / "applications" / SLUG)
            self.assertIn("2026-09-01_example-org_older-role", r.stdout)
            self.assertNotIn("tell the owner", r.stdout)
            self.assertNotIn("same opening", r.stdout)

    def test_other_employers_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, ["jd.md"], slug="2026-09-01_different-org_role")
            r = run(Path(tmp) / "applications" / SLUG)
            self.assertNotIn("different-org", r.stdout)


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"})


class ReviewFixes(unittest.TestCase):
    def packet_state(self, tmp):
        return build(tmp, ["jd.md", "research.md", "keywords.txt"])

    def test_packet_request_names_the_destination_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self.packet_state(tmp), "--branch", "b")
            self.assertIn(f"write-to: applications/{SLUG}/application-facts.md", r.stdout)

    def test_packet_request_names_the_repository_from_the_git_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q", "-b", "main")
            git(tmp, "remote", "add", "origin", "https://github.com/example-owner/example-repo.git")
            r = run(self.packet_state(tmp), "--branch", "b")
            self.assertIn("repo: example-owner/example-repo", r.stdout)

    def test_repository_is_unknown_without_a_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self.packet_state(tmp), "--branch", "b")
            self.assertIn("repo: unknown", r.stdout)

    def test_branch_defaults_to_the_checked_out_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q", "-b", "claude/example-branch")
            git(tmp, "commit", "-q", "--allow-empty", "-m", "x")
            r = run(self.packet_state(tmp))
            self.assertIn("deliver-to: branch claude/example-branch", r.stdout)

    def test_detached_head_is_reported_as_unknown_not_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q", "-b", "main")
            git(tmp, "commit", "-q", "--allow-empty", "-m", "x")
            git(tmp, "checkout", "-q", "--detach")
            r = run(self.packet_state(tmp))
            self.assertIn("deliver-to: branch unknown", r.stdout)

    def test_whitespace_only_file_counts_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = build(tmp, [])
            (folder / "jd.md").write_text("\n  \n", encoding="utf-8")
            self.assertEqual(next_step(run(folder).stdout), "add-jd")

    def test_dot_argument_uses_the_real_folder_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = build(tmp, ["jd.md"])
            r = subprocess.run([sys.executable, str(SCRIPT), "."], cwd=folder, capture_output=True, text=True)
            self.assertIn(f"application: {SLUG}", r.stdout)

    def test_slug_that_does_not_match_the_pattern_gets_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md"], slug="hjf-education-coordinator"))
            self.assertIn("warning: folder name is not YYYY-MM-DD_org_role", r.stdout)

    def test_well_formed_slug_has_no_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md"]))
            self.assertNotIn("warning", r.stdout)


FULL = ["jd.md", "research.md", "keywords.txt", "application-facts.md", "keywords.md", "match.md",
        "plan.md", "spec.json", "resume.md", "claims-used.md", "cover-letter.md", "handoff.md"]


def age(folder, name, seconds):
    p = folder / name
    t = p.stat().st_mtime - seconds
    os.utime(p, (t, t))


class Staleness(unittest.TestCase):
    def test_spec_older_than_plan_needs_reapproval(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = build(tmp, FULL)
            age(folder, "spec.json", 60)
            r = run(folder)
            self.assertEqual(next_step(r.stdout), "plan-approval")
            self.assertIn("stale", r.stdout)

    def test_handoff_older_than_resume_or_letter_needs_check(self):
        for newer in ("resume.md", "cover-letter.md"):
            with tempfile.TemporaryDirectory() as tmp:
                folder = build(tmp, FULL)
                age(folder, "handoff.md", 60)
                age(folder, "resume.md" if newer != "resume.md" else "cover-letter.md", 120)
                r = run(folder)
                self.assertEqual(next_step(r.stdout), "check", newer)

    def test_files_written_together_are_not_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(next_step(run(build(tmp, FULL)).stdout), "done")


class UnresolvedDestination(unittest.TestCase):
    def test_unknown_repo_or_branch_is_flagged_in_the_packet_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt"]))
            self.assertIn("warning: repo or branch unknown", r.stdout)

    def test_known_destination_has_no_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q", "-b", "claude/x")
            git(tmp, "remote", "add", "origin", "https://github.com/example-owner/example-repo.git")
            git(tmp, "commit", "-q", "--allow-empty", "-m", "x")
            r = run(build(tmp, ["jd.md", "research.md", "keywords.txt"]))
            self.assertNotIn("warning", r.stdout)


if __name__ == "__main__":
    unittest.main()

"""Behavioral checks for setup, evidence freshness, routing, and publication gates."""
import argparse
import copy
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import repo_cli as cli

ROOT = Path(__file__).resolve().parents[1]


class RepoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for key, value in (("user.name", "test"), ("user.email", "test@example.invalid")):
            subprocess.run(["git", "-C", str(self.root), "config", key, value], check=True)
        (self.root / ".gitignore").write_text(".repo/\nupstream/\n__pycache__/\n")
        (self.root / "toolchain.json").write_bytes((ROOT / "toolchain.json").read_bytes())
        (self.root / "upstream.json").write_text(json.dumps({"commit": "0" * 40}))
        (self.root / "tests").mkdir()
        (self.root / "tests/test_admission_api.py").write_text("import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): self.assertEqual(1+1,2)\n")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "fixture"], check=True)

    def verify(self):
        return cli.verify(self.root, argparse.Namespace(scope="schema", target=None, budget=10))

    def test_scope_produces_fresh_evidence_then_detects_change(self):
        result = self.verify()
        self.assertEqual(result["state"], "PASS")
        self.assertEqual(cli.latest(self.root)["state"], "PASS")
        (self.root / "tests/test_admission_api.py").write_text("# changed\n")
        self.assertEqual(cli.latest(self.root)["state"], "STALE")

    def test_log_tampering_invalidates_evidence(self):
        result = self.verify()
        (self.root / result["steps"][0]["log"]).write_text("PASS")
        self.assertEqual(cli.latest(self.root)["state"], "STALE")

    def test_missing_step_cannot_look_complete(self):
        result = self.verify()
        record = cli.read(self.root / result["run"])
        record["steps"] = []
        cli.atomic(self.root / result["run"], record)
        self.assertEqual(cli.latest(self.root)["state"], "STALE")

    def test_skipped_suite_fails_verification(self):
        (self.root / "tests/test_admission_api.py").write_text("import unittest\n@unittest.skip('missing dependency')\nclass Test(unittest.TestCase):\n def test_ok(self): pass\n")
        self.assertEqual(self.verify()["state"], "FAIL")

    def test_empty_suite_fails_verification(self):
        (self.root / "tests/test_admission_api.py").write_text("# no tests\n")
        self.assertEqual(self.verify()["state"], "FAIL")

    def test_budget_is_enforced(self):
        for budget in (-1, 0, 601):
            with self.assertRaises(cli.Problem):
                cli.verify(self.root, argparse.Namespace(scope="schema", target=None, budget=budget))

    def test_symlink_identity_is_bound_even_when_contents_match(self):
        (self.root / "left").write_text("equal")
        (self.root / "right").write_text("equal")
        (self.root / "link").symlink_to("left")
        before = cli.source_snapshot(self.root)
        tree_before = cli.content_tree(self.root)
        (self.root / "link").unlink()
        (self.root / "link").symlink_to("right")
        self.assertNotEqual(cli.source_snapshot(self.root), before)
        self.assertNotEqual(cli.content_tree(self.root), tree_before)

    def test_remote_branch_content_is_checked(self):
        remote = self.root / ".repo/remote.git"
        remote.parent.mkdir()
        subprocess.run(["git", "clone", "--bare", "-q", str(self.root), str(remote)], check=True)
        cli.command(["git", "remote", "add", "origin", str(remote)], self.root)
        head = cli.command(["git", "rev-parse", "HEAD"], self.root)
        cli.command(["git", "--git-dir=" + str(remote), "update-ref", "refs/heads/proposed", head], self.root)
        self.assertEqual(cli.remote_head(self.root, "proposed", cli.content_tree(self.root)), head)
        (self.root / "new.txt").write_text("different")
        cli.command(["git", "add", "new.txt"], self.root)
        cli.command(["git", "commit", "-qm", "local only"], self.root)
        with self.assertRaises(cli.Problem) as result:
            cli.remote_head(self.root, "proposed", cli.content_tree(self.root))
        self.assertEqual(result.exception.code, "TREE_MISMATCH")

    def test_capture_accepts_name_before_flags_and_retains_failure(self):
        with redirect_stdout(io.StringIO()) as output:
            code = cli.main(["--root", str(self.root), "capture", "regression", "--law", "upstream.json",
                             "--expected-exit", "1", "--contains", "expected failure", "--",
                             sys.executable, "-c", "print('expected failure'); raise SystemExit(1)"])
        self.assertEqual(code, 0, output.getvalue())
        record = cli.read(self.root / "counterexamples/regression.json")
        self.assertEqual(record["observation"]["exit_code"], 1)

    def test_watch_passes_remaining_budget_to_transport(self):
        timeouts = []
        def completed(root, arguments, timeout):
            timeouts.append(timeout)
            return {"statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}]}
        with patch.object(cli, "github", side_effect=completed), redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["--root", str(self.root), "watch", "3", "--budget", "1"]), 0)
        self.assertGreater(timeouts[0], 0)
        self.assertLessEqual(timeouts[0], 1)

    def test_temporary_index_does_not_stage_user_changes(self):
        before = cli.command(["git", "write-tree"], self.root)
        (self.root / "new.txt").write_text("new")
        candidate = cli.content_tree(self.root)
        self.assertNotEqual(candidate, before)
        self.assertEqual(cli.command(["git", "write-tree"], self.root), before)
        self.assertIn("new.txt", cli.command(["git", "ls-tree", "--name-only", candidate], self.root))

    def test_publication_requires_full_fresh_evidence(self):
        with self.assertRaises(cli.Problem):
            cli.publish_packet(self.root)
        self.verify()
        with self.assertRaises(cli.Problem):
            cli.publish_packet(self.root)

    def test_missing_capability_is_explicit(self):
        with patch.object(cli.shutil, "which", return_value=None):
            with self.assertRaises(cli.Problem) as result:
                cli.github(self.root, ["api", "user"])
        self.assertEqual(result.exception.code, "CAPABILITY_MISSING")

    def test_snapshot_excludes_local_run_outputs(self):
        before = cli.source_snapshot(self.root)
        cli.atomic(self.root / ".repo/example.json", {"new": 1})
        self.assertEqual(cli.source_snapshot(self.root), before)

    def test_catalog_and_generated_status(self):
        self.assertGreaterEqual(cli.catalog(ROOT, True)["items"], 60)
        self.assertEqual((ROOT / "docs/capabilities.md").read_text(), cli.rendered_status(ROOT))

    def test_routes_are_existing_small_working_sets(self):
        for name in ("GATE", "VERIFY", "RELEASE", "PROGRAM", "PROVE"):
            output = subprocess.check_output([str(ROOT / "repo"), "route", name], text=True)
            result = json.loads(output)
            self.assertTrue(result["ok"])
            self.assertLess(len(result["result"]["text"]), 6000)

    def test_setup_refuses_unknown_modified_target(self):
        target = self.root / "target"
        subprocess.run(["git", "clone", "-q", str(self.root), str(target)], check=True)
        pin = cli.command(["git", "-C", str(target), "rev-parse", "HEAD"], self.root)
        (self.root / "upstream.json").write_text(json.dumps({"commit": pin}))
        (target / "user.txt").write_text("preserve me")
        original = cli.command
        with patch.object(cli, "bun_for", return_value=sys.executable), patch.object(cli, "command", wraps=cli.command) as run:
            # Avoid installing a runtime: this test is about preserving dirty state.
            def cmd(argv, root=ROOT, timeout=15):
                if argv == [sys.executable, "--version"]:
                    return cli.read(self.root / "toolchain.json")["bun"]
                return original(argv, root, timeout)
            run.side_effect = cmd
            with self.assertRaises(cli.Problem) as result:
                cli.setup(self.root, argparse.Namespace(target=target, bun=None))
            self.assertEqual(result.exception.code, "DIRTY_TARGET")
        self.assertEqual((target / "user.txt").read_text(), "preserve me")

    def test_setup_preserves_ignored_destination(self):
        target = self.root / "target"
        subprocess.run(["git", "clone", "-q", str(self.root), str(target)], check=True)
        pin = cli.command(["git", "-C", str(target), "rev-parse", "HEAD"], self.root)
        (self.root / "upstream.json").write_text(json.dumps({"commit": pin}))
        (self.root / "CLAUDE.md").write_text("overlay")
        (target / ".git/info/exclude").write_text("CLAUDE.md\n")
        (target / "CLAUDE.md").write_text("user work")
        original = cli.command
        def cmd(argv, root=ROOT, timeout=15):
            if argv == [sys.executable, "--version"]:
                return cli.read(self.root / "toolchain.json")["bun"]
            return original(argv, root, timeout)
        with patch.object(cli, "bun_for", return_value=sys.executable), patch.object(cli, "command", side_effect=cmd):
            with self.assertRaises(cli.Problem) as result:
                cli.setup(self.root, argparse.Namespace(target=target, bun=None))
        self.assertEqual(result.exception.code, "DIRTY_TARGET")
        self.assertEqual((target / "CLAUDE.md").read_text(), "user work")


if __name__ == "__main__":
    unittest.main()

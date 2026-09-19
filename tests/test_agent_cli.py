import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_agent_contracts import plan, task
from tools.agent_system.cli import main
from tools.agent_system.state import GENESIS


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "system").mkdir()
        (self.root / "system/roadmap.json").write_text(json.dumps(plan(task())))
        (self.root / "source.txt").write_text("source")

    def call(self, *args):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = main(["--root", str(self.root), *args])
        return code, json.loads(stream.getvalue())

    def test_read_commands_do_not_create_files(self):
        before = sorted(str(p) for p in self.root.rglob("*"))
        for command in (("status",), ("next",), ("explain", "A"), ("check",), ("todo",)):
            code, response = self.call(*command)
            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))

    def test_unknown_task_returns_stable_error(self):
        code, value = self.call("explain", "missing")
        self.assertEqual(code, 2)
        self.assertEqual(value["error"]["code"], "UNKNOWN_TASK")

    def test_invalid_command_returns_json(self):
        code, response = self.call("not-a-command")
        self.assertEqual(code, 2)
        self.assertEqual(response["error"]["code"], "INVALID_ARGUMENTS")

    def test_changes_cursor_is_bounded_and_rejects_unknown_head(self):
        self.call("transition", "A", "RUNNING", "--request", "start", "--head", GENESIS, "--reason", "begin")
        code, response = self.call("changes", "--since", GENESIS, "--limit", "1")
        self.assertEqual(code, 0)
        self.assertEqual(len(response["result"]["events"]), 1)
        cursor = response["result"]["cursor"]
        self.assertEqual(self.call("changes", "--since", cursor)[1]["result"]["events"], [])
        self.assertEqual(self.call("changes", "--since", "bad")[1]["error"]["code"], "UNKNOWN_HEAD")

    def test_end_to_end_transition_verification_and_completion(self):
        code, started = self.call("transition", "A", "RUNNING", "--request", "start", "--head", GENESIS, "--reason", "begin")
        self.assertEqual(code, 0)
        code, evidence = self.call("verify", "A", "--run-id", "run")
        self.assertEqual(code, 0)
        code, completed = self.call("transition", "A", "SOLVED", "--request", "done", "--head", started["result"]["sha256"],
                                    "--reason", "verification passed", "--evidence", evidence["result"]["path"])
        self.assertEqual(code, 0)
        code, status = self.call("status")
        self.assertEqual(status["result"]["counts"], {"SOLVED": 1})
        (self.root / "source.txt").write_text("changed")
        code, checked = self.call("check")
        self.assertEqual(code, 2)
        self.assertEqual(checked["error"]["code"], "STALE_EVIDENCE")

    def test_state_path_escape_rejected(self):
        code, response = self.call("--state", "../escape", "status")
        self.assertEqual(code, 2)
        self.assertEqual(response["error"]["code"], "INVALID_PATH")

    def test_failing_verification_is_structured(self):
        (self.root / "source.txt").unlink()
        code, response = self.call("verify", "A", "--run-id", "failed")
        self.assertEqual(code, 2)
        self.assertEqual(response["error"]["code"], "MISSING_SOURCE")

    def test_json_array_is_not_an_evidence_object(self):
        (self.root / "bad.json").write_text("[]")
        code, response = self.call("transition", "A", "SOLVED", "--request", "bad", "--head", GENESIS,
                                   "--reason", "bad evidence", "--evidence", "bad.json")
        self.assertEqual(code, 2)
        self.assertEqual(response["error"]["code"], "INVALID_EVIDENCE")


if __name__ == "__main__":
    unittest.main()

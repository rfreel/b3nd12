from pathlib import Path
import tempfile
import unittest

from test_agent_contracts import task
from tools.agent_system.contracts import Problem
from tools.agent_system.evidence import execute, fresh, verify


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source.txt").write_text("original")
        self.task = task()

    def test_success_is_bound_to_source_and_artifact(self):
        ref = verify(self.root, self.task, "ok")
        self.assertTrue(fresh(self.root, self.task, ref))
        (self.root / "source.txt").write_text("changed")
        self.assertFalse(fresh(self.root, self.task, ref))
        (self.root / "source.txt").write_text("original")
        (self.root / ref["path"]).write_text("{}")
        self.assertFalse(fresh(self.root, self.task, ref))

    def test_failure_cannot_supply_completion(self):
        self.task["checks"] = [["python3", "-c", "raise SystemExit(3)"]]
        ref = verify(self.root, self.task, "failed")
        self.assertFalse(ref["passed"])
        self.assertFalse(fresh(self.root, self.task, ref))

    def test_timeout_is_retained(self):
        result = execute(["python3", "-c", "import time; time.sleep(10)"], self.root, 0.05)
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["passed"])
        self.assertLess(result["seconds"], 2)

    def test_duplicate_run_and_escape_rejected(self):
        verify(self.root, self.task, "one")
        for identity in ("one", "../escape"):
            with self.assertRaises(Problem):
                verify(self.root, self.task, identity)

    def test_source_drift_during_verification_fails(self):
        self.task["checks"] = [["python3", "-c", "from pathlib import Path; Path('source.txt').write_text('changed')"]]
        self.assertFalse(verify(self.root, self.task, "drift")["passed"])

    def test_unfinished_evidence_is_not_published(self):
        self.task["checks"] = [["python3", "-c", "from pathlib import Path; assert not Path('evidence/agent-system/runs/published.json').exists()"]]
        result = verify(self.root, self.task, "published")
        self.assertTrue(result["passed"])
        self.assertTrue((self.root / result["path"]).is_file())

    def test_zero_tests_is_not_evidence(self):
        result = execute(["python3", "-m", "unittest", "discover", "-s", "."], self.root, 2)
        self.assertFalse(result["passed"])

    def test_output_overflow_is_not_success(self):
        result = execute(["python3", "-c", "print('x'*200000)"], self.root, 2)
        self.assertTrue(result["truncated"])
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()

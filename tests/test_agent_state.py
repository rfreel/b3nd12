import concurrent.futures
from pathlib import Path
import tempfile
import unittest

from test_agent_contracts import plan, task
from tools.agent_system.contracts import Problem, canonical, digest
from tools.agent_system.evidence import verify
from tools.agent_system.state import GENESIS, append, project, read_events


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source.txt").write_text("original")
        self.plan = plan(task(), task("B", ["A"]))
        self.path = self.root / "events.jsonl"

    def payload(self, status, identity="A", evidence=None):
        return dict(task=identity, status=status, reason="test observation", reopen="source changes", evidence=evidence)

    def head(self):
        events = read_events(self.path, self.plan)
        return events[-1]["sha256"] if events else GENESIS

    def move(self, status, identity="A", evidence=None):
        return append(self.root, self.plan, self.path, self.payload(status, identity, evidence),
                      f"{identity}-{status}-{self.head()[:8]}", self.head())

    def test_idempotent_retry_and_conflicting_retry(self):
        value = self.payload("RUNNING")
        first = append(self.root, self.plan, self.path, value, "retry", GENESIS)
        self.assertEqual(first, append(self.root, self.plan, self.path, value, "retry", GENESIS))
        self.assertEqual(len(read_events(self.path, self.plan)), 1)
        with self.assertRaises(Problem):
            append(self.root, self.plan, self.path, self.payload("BLOCKED"), "retry", first["sha256"])

    def test_stale_head_does_not_write(self):
        self.move("RUNNING")
        before = self.path.read_bytes()
        with self.assertRaises(Problem):
            append(self.root, self.plan, self.path, self.payload("OPEN"), "stale", GENESIS)
        self.assertEqual(before, self.path.read_bytes())

    def test_two_writers_have_one_winner(self):
        def write(request):
            try:
                return append(self.root, self.plan, self.path, self.payload("RUNNING"), request, GENESIS)["seq"]
            except Problem as error:
                return error.code
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(write, ["first", "second"]))
        self.assertCountEqual(results, [1, "STALE_HEAD"])
        self.assertEqual(len(read_events(self.path, self.plan)), 1)

    def test_torn_tail_and_tampering_rejected(self):
        self.move("RUNNING")
        original = self.path.read_text()
        for broken in (original.rstrip(), original.replace("test observation", "fake observation")):
            self.path.write_text(broken)
            with self.assertRaises(Problem):
                read_events(self.path, self.plan)

    def test_rehashed_impossible_transition_rejected(self):
        event = self.move("RUNNING")
        event["payload"]["status"] = "SOLVED"
        event["sha256"] = digest({k: v for k, v in event.items() if k != "sha256"})
        self.path.write_text(canonical(event) + "\n")
        with self.assertRaises(Problem):
            read_events(self.path, self.plan)

    def test_plan_drift_rejected(self):
        self.move("RUNNING")
        self.plan["tasks"][0]["title"] = "Changed contract"
        with self.assertRaises(Problem):
            read_events(self.path, self.plan)

    def test_completion_needs_real_evidence(self):
        self.move("RUNNING")
        with self.assertRaises(Problem):
            self.move("SOLVED")
        ref = verify(self.root, self.plan["tasks"][0], "proof")
        self.move("SOLVED", evidence=ref)
        self.assertEqual(project(self.root, self.plan, read_events(self.path, self.plan))["next"]["task"], "B")

    def test_dependency_reopening_invalidates_dependent(self):
        for identity, item in zip(("A", "B"), self.plan["tasks"]):
            self.move("RUNNING", identity)
            self.move("SOLVED", identity, verify(self.root, item, identity))
        self.move("OPEN")
        states = project(self.root, self.plan, read_events(self.path, self.plan))["tasks"]
        self.assertEqual([t["status"] for t in states], ["OPEN", "STALE"])

    def test_changed_source_makes_solved_stale(self):
        self.move("RUNNING")
        self.move("SOLVED", evidence=verify(self.root, self.plan["tasks"][0], "proof"))
        (self.root / "source.txt").write_text("changed")
        current = project(self.root, self.plan, read_events(self.path, self.plan))
        self.assertEqual(current["tasks"][0]["status"], "STALE")
        self.assertEqual(current["next"]["action"], "reopen")

    def test_open_dependency_blocks_start(self):
        with self.assertRaises(Problem):
            self.move("RUNNING", "B")

    def test_unresolved_requires_reopen_condition(self):
        value = self.payload("UNRESOLVED")
        value["reopen"] = ""
        with self.assertRaises(Problem):
            append(self.root, self.plan, self.path, value, "bad", GENESIS)

    def test_read_does_not_initialize_history(self):
        self.assertEqual(read_events(self.path, self.plan), [])
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()

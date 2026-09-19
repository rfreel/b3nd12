import copy
from pathlib import Path
import json
import shutil
import tempfile
import unittest

from test_agent_contracts import plan, task
from tools.agent_system.benchmarks import benchmark, percentile, synthetic_history, validate_metrics
from tools.agent_system.contracts import Problem, parse
from tools.agent_system.state import decode_history

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_workload_replays_exactly_and_is_deterministic(self):
        contract = plan(task())
        first = synthetic_history(contract)
        self.assertEqual(first, synthetic_history(contract))
        events = decode_history(first, contract)
        self.assertEqual(len(events), 1000)
        self.assertEqual(events[-1]["payload"]["status"], "OPEN")

    def test_registry_has_diverse_scopes_and_explicit_targets(self):
        metrics = validate_metrics(parse((ROOT / "system/metrics.json").read_text()))["metrics"]
        self.assertGreaterEqual(len(metrics), 20)
        identities = {metric["id"] for metric in metrics}
        self.assertTrue({"agent_task_success", "cross_family_transfer_gain", "dollars_per_replicated_gain",
                         "false_admission_rate", "status_bytes"}.issubset(identities))
        self.assertTrue(all(metric["collection"] and metric["scope"] for metric in metrics))

    def test_duplicate_metrics_rejected(self):
        registry = parse((ROOT / "system/metrics.json").read_text())
        registry["metrics"].append(copy.deepcopy(registry["metrics"][0]))
        with self.assertRaises(Problem):
            validate_metrics(registry)

    def test_p95_keeps_slow_tail(self):
        self.assertEqual(percentile([1, 2, 3, 100]), 100)

    def test_valid_json_with_wrong_shape_is_rejected(self):
        for value in ([], None, {"schema_version": True, "metrics": []},
                      {"schema_version": 1, "metrics": [None]}):
            with self.subTest(value=value), self.assertRaises(Problem):
                validate_metrics(value)

    def test_cold_benchmark_uses_selected_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "system").mkdir()
            (root / "state").mkdir()
            (root / "state/events.jsonl").write_text("corrupt default journal")
            contract = plan(task())
            (root / "system/roadmap.json").write_text(json.dumps(contract))
            shutil.copyfile(ROOT / "system/metrics.json", root / "system/metrics.json")
            shutil.copyfile(ROOT / "control.py", root / "control.py")
            shutil.copytree(ROOT / "tools/agent_system", root / "tools/agent_system")
            result = benchmark(root, contract, [], "state/alternate.jsonl")
            self.assertEqual(result["state_path"], "state/alternate.jsonl")
            self.assertEqual(result["state_head"], "0" * 64)
            self.assertEqual(result["raw"]["tamper_rejected"], 10)


if __name__ == "__main__":
    unittest.main()

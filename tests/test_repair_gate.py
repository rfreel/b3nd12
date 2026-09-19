"""Synthetic fixtures test admission logic, not empirical repair performance."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repair_gate", ROOT / "tools/repair_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def report_fixture():
    context = {key: "a" * 64 for key in ("suite_sha256", "config_sha256", "environment_sha256")}
    before = {"context": context, "cases": [
        {"id": "target", "status": "FAIL", "evidence_sha256": "b" * 64},
        {"id": "regression", "status": "PASS", "evidence_sha256": "c" * 64},
    ]}
    after = copy.deepcopy(before)
    after["cases"][0].update(status="PASS", evidence_sha256="d" * 64)
    return {"schema_version": 1, "target_case": "target", "before": before, "after": after}


class RepairGateTests(unittest.TestCase):
    def test_valid_repair_accepted_without_mutation(self):
        report = report_fixture()
        original = copy.deepcopy(report)
        result = gate.evaluate(report)
        self.assertEqual(result["verdict"], "ACCEPTED")
        self.assertEqual(report, original)
        self.assertEqual(result, gate.evaluate(report))

    def test_failed_target_rejected(self):
        report = report_fixture()
        report["after"]["cases"][0]["status"] = "FAIL"
        self.assertEqual(gate.evaluate(report)["verdict"], "REJECTED")

    def test_already_passing_target_rejected(self):
        report = report_fixture()
        report["before"]["cases"][0]["status"] = "PASS"
        self.assertEqual(gate.evaluate(report)["verdict"], "REJECTED")

    def test_regression_rejected(self):
        report = report_fixture()
        report["after"]["cases"][1]["status"] = "FAIL"
        self.assertIn("baseline pass not preserved: regression", gate.evaluate(report)["reasons"])

    def test_missing_evidence_rejected(self):
        for index in (0, 1):
            with self.subTest(index=index):
                report = report_fixture()
                report["after"]["cases"].pop(index)
                self.assertEqual(gate.evaluate(report)["verdict"], "REJECTED")

    def test_context_drift_rejected(self):
        for key in ("suite_sha256", "config_sha256", "environment_sha256"):
            with self.subTest(key=key):
                report = report_fixture()
                report["after"]["context"][key] = "e" * 64
                self.assertEqual(gate.evaluate(report)["verdict"], "REJECTED")

    def test_unresolved_is_preserved(self):
        for side in ("before", "after"):
            for index in (0, 1):
                with self.subTest(side=side, index=index):
                    report = report_fixture()
                    report[side]["cases"][index]["status"] = "UNRESOLVED"
                    self.assertEqual(gate.evaluate(report)["verdict"], "UNRESOLVED")

    def test_schema_rejects_invalid_and_extra_values(self):
        mutations = [
            lambda r: r.update(schema_version=True),
            lambda r: r.update(extra="unrecognized"),
            lambda r: r.update(target_case=""),
            lambda r: r["before"].update(cases=[]),
            lambda r: r["before"]["cases"].append(r["before"]["cases"][0]),
            lambda r: r["before"]["cases"][0].update(status="UNKNOWN"),
            lambda r: r["before"]["cases"][0].update(evidence_sha256="missing"),
            lambda r: r["before"]["cases"][0].pop("evidence_sha256"),
            lambda r: r["before"]["context"].update(extra="a" * 64),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                report = report_fixture()
                mutate(report)
                with self.assertRaises(gate.InvalidReport):
                    gate.evaluate(report)

    def run_cli(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(content, encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "tools/repair_gate.py"), str(path)], capture_output=True, text=True)
            self.assertEqual(path.read_text(encoding="utf-8"), content)
            return result.returncode, json.loads(result.stdout)

    def test_cli_exit_codes(self):
        report = report_fixture()
        self.assertEqual(self.run_cli(json.dumps(report))[0], 0)
        report["after"]["cases"][0]["status"] = "FAIL"
        self.assertEqual(self.run_cli(json.dumps(report))[0], 1)
        report["after"]["cases"][0]["status"] = "UNRESOLVED"
        code, result = self.run_cli(json.dumps(report))
        self.assertEqual((code, result["verdict"]), (1, "UNRESOLVED"))
        for malformed in ('{"schema_version":1,"schema_version":1}', '{"a":NaN}', '{'):
            self.assertEqual(self.run_cli(malformed)[0], 2)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("autoresearch", ROOT / "experiments/autoresearch/run.py")
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


class AutoresearchTests(unittest.TestCase):
    def test_stderr_error_overrides_stdout_success(self):
        result = {"exit_code": 0,
                  "stdout": json.dumps({"id": "BND000", "unsafe": 0}),
                  "stderr": json.dumps({"severity": "error", "id": "BND110"})}
        self.assertFalse(campaign.checked(result))

    def test_missing_or_unsafe_attestation_rejected(self):
        for output in ("", "not json", json.dumps({"id": "BND000", "unsafe": 1})):
            self.assertFalse(campaign.checked({"exit_code": 0, "stdout": output, "stderr": ""}))

    def test_proof_surface_cannot_be_deleted_or_extended(self):
        baseline = (campaign.HERE / "baseline.bend").read_text()
        self.assertFalse(campaign.admissible(baseline.replace("import ./LAWS.bend as Laws", ""), baseline))
        self.assertFalse(campaign.admissible(baseline + "\nimport ./escape.bend\n", baseline))
        self.assertFalse(campaign.admissible(baseline + "\n@unsafe\n", baseline))
        self.assertFalse(campaign.admissible(baseline[:baseline.index("def Laws.unresolved_preserved")], baseline))

    def test_timeout_cannot_pass(self):
        self.assertFalse(campaign.checked({"exit_code": None, "stdout": "", "stderr": "timeout"}))


if __name__ == "__main__":
    unittest.main()

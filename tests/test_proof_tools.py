"""Proof generation drift and actual cross-runtime comparison checks."""
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load('generate-admission-proof')
correspondence = load('check-admission-correspondence')


class ProofToolsTests(unittest.TestCase):
    def test_generated_proof_matches_and_inventory_complete(self):
        self.assertEqual((ROOT / 'pilot/admission/PROOF.bend').read_text(), generator.render())
        self.assertEqual(generator.check_inventory(), 9)

    def test_removed_law_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'pilot/admission'
            shutil.copytree(ROOT / 'pilot/admission', destination)
            path = destination / 'LAWS.bend'
            path.write_text(path.read_text().replace('law eligible_accepted:', 'law renamed:'))
            with self.assertRaises(ValueError):
                generator.check_inventory(Path(tmp))

    def test_duplicate_or_missing_proof_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'pilot/admission'
            shutil.copytree(ROOT / 'pilot/admission', destination)
            path = destination / 'PROOF.bend'
            path.write_text(path.read_text() + '\ndef Laws.eligible_accepted():\n  {==}\n')
            with self.assertRaises(ValueError):
                generator.check_inventory(Path(tmp))

    def test_comparison_rejects_wrong_decision_and_incomplete_output(self):
        expected = [correspondence.python_decision(*v) for v in correspondence.vectors()]
        changed = expected.copy()
        changed[0] = 'ACCEPTED'
        with self.assertRaisesRegex(ValueError, 'Correspondence failure'):
            correspondence.compare(changed, expected)
        with self.assertRaisesRegex(ValueError, 'exactly 54'):
            correspondence.compare(expected[:-1], expected)

    def test_python_fixture_exercises_accept_reject_and_pending(self):
        self.assertEqual(correspondence.python_decision(True, 'PASS', 'PASS', 'PASS'), 'ACCEPTED')
        self.assertEqual(correspondence.python_decision(False, 'PASS', 'PASS', 'PASS'), 'REJECTED')
        self.assertEqual(correspondence.python_decision(True, 'PASS', 'PASS', 'PENDING'), 'PENDING')

    @unittest.skipUnless(os.environ.get('BEND_UPSTREAM'), 'BEND_UPSTREAM required for actual Bend runtime')
    def test_actual_bend_runtime(self):
        result = correspondence.run(os.environ.get('BUN', 'bun'), os.environ['BEND_UPSTREAM'])
        self.assertEqual(result['matching'], 54)
        self.assertTrue(result['runtime_executed'])
        self.assertEqual(result['unsafe'], 0)

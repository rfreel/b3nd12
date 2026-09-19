"""Public values, authenticated command evidence, and real Git demo."""
import base64
from dataclasses import FrozenInstanceError
import sys
import subprocess
import tempfile
from pathlib import Path
import time
import unittest

from admission import (Policy, Manifest, Bundle, build_policy, build_manifest,
                       build_bundle, produce, evaluate, demo, diff_manifests, reconcile)
from tools import admission_gate as gate


def fixture(kind='bounded-test'):
    domains = {d: dict(producer='checker-' + d, kind=kind) for d in gate.DOMAINS}
    keys = {r['producer']: bytes([i + 1]) * 32 for i, r in enumerate(domains.values())}
    policy = build_policy('test/repo', 'refs/heads/main', ['worker'], domains,
                          {p: gate.sha(p.encode()) for p in gate.PINS})
    manifest = build_manifest(policy, 'a' * 40, 'b' * 40, 'c' * 40, 'test-request', 'worker')
    return policy, manifest, keys


class PublicApiTests(unittest.TestCase):
    def test_immutable_nested_round_trip(self):
        policy, manifest, _ = fixture()
        original = policy.digest
        data = policy.to_dict()
        data['actors'].append('intruder')
        self.assertEqual(policy.digest, original)
        with self.assertRaises(FrozenInstanceError):
            policy.canonical = b'{}'
        with self.assertRaises(FrozenInstanceError):
            policy.extra = 'mutable'
        self.assertEqual(Policy(policy.canonical), policy)
        changed = manifest.to_dict()
        changed['request'] = 'other'
        self.assertEqual(list(diff_manifests(manifest, changed)), ['request'])

    def test_invalid_construction(self):
        _, manifest, _ = fixture()
        data = manifest.to_dict()
        data['epoch'] = True
        with self.assertRaises(gate.Invalid):
            Manifest(data)
        with self.assertRaises(gate.Invalid):
            Policy(b'{"version":1,"version":1}')

    def test_command_authority_and_evidence_kind(self):
        policy, manifest, keys = fixture()
        command = [sys.executable, '-c', 'pass']
        with self.assertRaises(gate.Invalid):
            produce(manifest, policy, 'behavior', command, keys)
        policy, manifest, keys = fixture('checked-proof')
        with self.assertRaises(gate.Invalid):
            produce(manifest, policy, 'behavior', command, keys, controller_authorized=True)

    def test_command_status_bytes_and_authentication(self):
        policy, manifest, keys = fixture()
        receipt, artifact = produce(manifest, policy, 'behavior',
                                    [sys.executable, '-c', 'import sys; sys.stdout.buffer.write(bytes([0,255])); sys.exit(2)'],
                                    keys, controller_authorized=True)
        record = gate.load_json(artifact)
        self.assertEqual(base64.b64decode(record['stdout_base64']), bytes([0, 255]))
        result = evaluate(build_bundle(manifest, [receipt]), policy, keys, {gate.sha(artifact): artifact})
        self.assertEqual(result['code'], 'OBLIGATION_FAILED')
        self.assertEqual(result['domains']['behavior'], 'FAIL')
        result = evaluate(build_bundle(manifest, [receipt]), policy, keys, {gate.sha(artifact): b'altered'})
        self.assertEqual(result['code'], 'ARTIFACT_INVALID')

    def test_timeout_remains_pending(self):
        policy, manifest, keys = fixture()
        receipt, artifact = produce(manifest, policy, 'behavior',
                                    [sys.executable, '-c', 'import time; time.sleep(1)'],
                                    keys, controller_authorized=True, timeout=.02)
        result = evaluate(build_bundle(manifest, [receipt]), policy, keys, {gate.sha(artifact): artifact})
        self.assertEqual(result['verdict'], 'PENDING')
        self.assertEqual(result['domains']['behavior'], 'PENDING')

    def test_output_cap_keeps_exact_prefix_and_stays_pending(self):
        policy, manifest, keys = fixture()
        receipt, artifact = produce(manifest, policy, 'behavior',
                                    [sys.executable, '-c', 'import sys; sys.stdout.buffer.write(bytes(range(256))*10000)'],
                                    keys, controller_authorized=True, output_limit=257)
        record = gate.load_json(artifact)
        self.assertEqual(base64.b64decode(record['stdout_base64']), bytes(range(256)) + b'\x00')
        self.assertTrue(record['truncated'])
        self.assertEqual(receipt.to_dict()['status'], 'PENDING')

    def test_timeout_kills_background_child(self):
        policy, manifest, keys = fixture()
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'child-survived'
            child = 'import time,pathlib; time.sleep(.5); pathlib.Path(' + repr(str(marker)) + ').write_text("bad")'
            parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",' + repr(child) + ']); print("spawned",flush=True); time.sleep(10)'
            receipt, artifact = produce(manifest, policy, 'behavior',
                                        [sys.executable, '-c', parent], keys,
                                        controller_authorized=True, timeout=.2)
            record = gate.load_json(artifact)
            self.assertIn(b'spawned', base64.b64decode(record['stdout_base64']))
            self.assertTrue(record['timed_out'])
            self.assertEqual(receipt.to_dict()['status'], 'PENDING')
            time.sleep(.6)
            self.assertFalse(marker.exists())

    def test_real_git_end_to_end(self):
        result = demo()
        self.assertEqual(result['pass_case']['verdict'], 'ACCEPTED')
        self.assertEqual(result['fail_case']['verdict'], 'REJECTED')
        self.assertEqual(result['pending_case']['verdict'], 'PENDING')
        self.assertFalse(result['dry_run']['mutated'])
        self.assertEqual(result['before']['code'], 'NOT_COMMITTED_OBSERVED')
        self.assertFalse(result['before']['retry_authorized'])
        self.assertEqual(result['committed']['verdict'], 'COMMITTED')
        self.assertEqual(result['lost_ack_reconciliation']['verdict'], 'COMMITTED')
        self.assertEqual(result['replay']['verdict'], 'REJECTED')

    def test_reconcile_conflict_and_symbolic_ref(self):
        policy, _, _ = fixture()
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(['git', 'init', '--bare', repo], capture_output=True, check=True)
            gate.git(repo, 'config', 'user.name', 'Test')
            gate.git(repo, 'config', 'user.email', 'test@example.invalid')
            tree = gate.git(repo, 'mktree', input='')
            base = gate.git(repo, 'commit-tree', tree, input='base\n')
            candidate = gate.git(repo, 'commit-tree', tree, '-p', base, input='next\n')
            manifest = build_manifest(policy, base, candidate, tree, 'request', 'worker')
            gate.git(repo, 'update-ref', 'refs/heads/main', base)
            marker = 'refs/admission/consumed/' + gate.sha(b'request')
            gate.git(repo, 'update-ref', marker, base)
            self.assertEqual(reconcile(repo, 'request', manifest)['code'], 'REQUEST_CONSUMED')
            self.assertEqual(reconcile(repo, 'different', manifest)['code'], 'REQUEST_MISMATCH')
            gate.git(repo, 'symbolic-ref', marker, 'refs/heads/main')
            result = reconcile(repo, 'request', manifest)
            self.assertEqual(result['verdict'], 'UNRESOLVED')
            self.assertEqual(result['code'], 'RECONCILIATION_FAILED')


if __name__ == '__main__':
    unittest.main()

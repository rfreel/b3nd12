"""Independent acceptance oracle, hostile inputs, and real bare-Git transactions."""

import copy
from concurrent.futures import ThreadPoolExecutor
import hmac
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import admission_gate as gate


def fixture(statuses=("PASS", "PASS", "PASS")):
    keys = {"checker-" + d: bytes([i + 1]) * 32 for i, d in enumerate(gate.DOMAINS)}
    policy = dict(version=1, repository="test/repo", target="refs/heads/main", epoch=1,
                  actors=["worker"], domains={d: {"producer": "checker-" + d, "kind": "bounded-test"}
                                             for d in gate.DOMAINS})
    policy.update({p: gate.sha(p.encode()) for p in gate.PINS})
    manifest = {p: policy[p] for p in ("repository", "target", "epoch", *gate.PINS)}
    manifest.update(version=1, base="a" * 40, candidate="b" * 40, tree="c" * 40,
                    policy=gate.sha(gate.canonical(policy)), request="request-1", actor="worker")
    bundle = {"manifest": manifest, "receipts": []}
    artifacts = {}
    for domain, status in zip(gate.DOMAINS, statuses):
        if status == "MISSING":
            continue
        data = (domain + ":" + status).encode()
        artifact = gate.sha(data)
        artifacts[artifact] = data
        bundle["receipts"].append(dict(domain=domain, producer="checker-" + domain,
                                      kind="bounded-test", manifest="", artifact=artifact,
                                      status=status, mac=""))
    resign(bundle, keys)
    return bundle, policy, keys, artifacts


def resign(bundle, keys):
    for receipt in bundle["receipts"]:
        receipt["manifest"] = gate.sha(gate.canonical(bundle["manifest"]))
        payload = {k: v for k, v in receipt.items() if k != "mac"}
        receipt["mac"] = hmac.digest(keys[receipt["producer"]], gate.canonical(payload), "sha256").hex()


class AdmissionTests(unittest.TestCase):
    def test_exhaustive_domain_and_context_partition(self):
        # 4^3 domain outcomes x 4 independent context flags = 1024 cases.
        count = 0
        for statuses in itertools.product(("PASS", "FAIL", "PENDING", "MISSING"), repeat=3):
            for stale_policy, wrong_epoch, wrong_actor, tampered in itertools.product((False, True), repeat=4):
                b, p, k, a = fixture(statuses)
                if stale_policy:
                    b["manifest"]["policy"] = "0" * 64
                if wrong_epoch:
                    b["manifest"]["epoch"] = 0
                if wrong_actor:
                    b["manifest"]["actor"] = "intruder"
                resign(b, k)
                if tampered and b["receipts"]:
                    b["receipts"][0]["mac"] = "0" * 64
                invalid = stale_policy or wrong_epoch or wrong_actor or (tampered and bool(b["receipts"]))
                expected = ("REJECTED" if invalid or "FAIL" in statuses else
                            "ACCEPTED" if statuses == ("PASS",) * 3 else "PENDING")
                with self.subTest(statuses=statuses, flags=(stale_policy, wrong_epoch, wrong_actor, tampered)):
                    self.assertEqual(gate.decide(b, p, k, a)["verdict"], expected)
                count += 1
        self.assertEqual(count, 1024)

    def test_all_manifest_fields_are_bound(self):
        for field in gate.MANIFEST_FIELDS:
            b, p, k, a = fixture()
            original = b["manifest"][field]
            b["manifest"][field] = original + 1 if type(original) is int else original + "x"
            with self.subTest(field=field):
                self.assertEqual(gate.decide(b, p, k, a)["verdict"], "REJECTED")

    def test_all_context_pins_checked_even_with_fresh_signatures(self):
        for field in (*gate.PINS, "repository", "target"):
            b, p, k, a = fixture()
            b["manifest"][field] = "0" * 64 if field in gate.PINS else "other/value"
            resign(b, k)
            self.assertEqual(gate.decide(b, p, k, a)["verdict"], "REJECTED")

    def test_receipt_attacks(self):
        for attack in ("duplicate", "wrong-producer", "weaker-kind", "artifact", "status", "binding", "mac"):
            b, p, k, a = fixture()
            if attack == "duplicate":
                b["receipts"][1] = copy.deepcopy(b["receipts"][0])
            elif attack == "artifact":
                a[b["receipts"][0]["artifact"]] = b"forged"
            else:
                field, value = {"wrong-producer": ("producer", "worker"),
                                "weaker-kind": ("kind", "finite-check"),
                                "status": ("status", "SKIPPED"),
                                "binding": ("manifest", "0" * 64),
                                "mac": ("mac", "0" * 64)}[attack]
                b["receipts"][0][field] = value
                if attack == "status":
                    resign(b, k)
            with self.subTest(attack=attack):
                self.assertEqual(gate.decide(b, p, k, a)["verdict"], "REJECTED")

    def test_empty_and_collapsed_trust_domains(self):
        for attack in ("empty-actors", "shared-producer", "shared-key", "worker-producer", "missing-key"):
            b, p, k, a = fixture()
            if attack == "empty-actors":
                p["actors"] = []
            elif attack == "shared-producer":
                p["domains"]["integrity"] = copy.deepcopy(p["domains"]["behavior"])
            elif attack == "shared-key":
                k["checker-integrity"] = k["checker-behavior"]
            elif attack == "worker-producer":
                p["actors"].append("checker-integrity")
            else:
                del k["checker-integrity"]
            b["manifest"]["policy"] = gate.sha(gate.canonical(p))
            self.assertEqual(gate.decide(b, p, k, a)["verdict"], "REJECTED")

    def test_malformed_shapes_fail_closed(self):
        values = [None, True, 1, "", [], {}, [1], {"extra": 1}]
        for value in values:
            b, p, k, a = fixture()
            self.assertEqual(gate.decide(value, p, k, a)["verdict"], "REJECTED")
            for field in gate.MANIFEST_FIELDS:
                if type(value) is type(b["manifest"][field]) and value == b["manifest"][field]:
                    continue
                changed = copy.deepcopy(b)
                changed["manifest"][field] = value
                self.assertEqual(gate.decide(changed, p, k, a)["verdict"], "REJECTED")

    def test_duplicate_json_and_constants(self):
        for data in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(gate.Invalid):
                gate.load_json(data)

    def test_pure_and_deterministic(self):
        args = fixture()
        before = copy.deepcopy(args)
        first = gate.decide(*args)
        self.assertEqual(first["verdict"], "ACCEPTED")
        self.assertEqual(first, gate.decide(*args))
        self.assertEqual(args, before)


class GitExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo.git"
        subprocess.run(["git", "init", "--bare", "--quiet", str(self.repo)], check=True)
        gate.git(self.repo, "config", "user.name", "Admission Test")
        gate.git(self.repo, "config", "user.email", "test@example.invalid")
        self.tree = gate.git(self.repo, "mktree", input="")
        self.base = gate.git(self.repo, "commit-tree", self.tree, "-m", "base")
        self.candidate = gate.git(self.repo, "commit-tree", self.tree, "-p", self.base, "-m", "candidate")
        gate.git(self.repo, "update-ref", "refs/heads/main", self.base)
        self.b, self.p, self.k, self.a = fixture()
        self.b["manifest"].update(base=self.base, candidate=self.candidate, tree=self.tree)
        resign(self.b, self.k)

    def execute(self, bundle=None):
        return gate.execute(self.repo, "test/repo", bundle or self.b, self.p, self.k, self.a)

    def head(self):
        return gate.git(self.repo, "rev-parse", "refs/heads/main")

    def test_valid_commit_and_replay(self):
        self.assertEqual(self.execute()["verdict"], "COMMITTED")
        self.assertEqual(self.head(), self.candidate)
        # Restore base to isolate consumed-request protection from stale-base protection.
        gate.git(self.repo, "update-ref", "refs/heads/main", self.base)
        self.assertEqual(self.execute()["verdict"], "REJECTED")
        self.assertEqual(self.head(), self.base)

    def test_stale_base_does_not_consume_request(self):
        other = gate.git(self.repo, "commit-tree", self.tree, "-p", self.base, "-m", "other")
        gate.git(self.repo, "update-ref", "refs/heads/main", other)
        self.assertEqual(self.execute()["verdict"], "REJECTED")
        self.assertEqual(self.head(), other)
        self.assertEqual(gate.git(self.repo, "for-each-ref", "refs/admission/consumed"), "")
        gate.git(self.repo, "update-ref", "refs/heads/main", self.base)
        self.assertEqual(self.execute()["verdict"], "COMMITTED")

    def test_wrong_tree_parent_repository_and_ref(self):
        for field, value in (("tree", "0" * 40), ("candidate", self.base), ("target", "refs/heads/../bad")):
            b = copy.deepcopy(self.b)
            b["manifest"][field] = value
            resign(b, self.k)
            self.assertEqual(self.execute(b)["verdict"], "REJECTED")
            self.assertEqual(self.head(), self.base)
        self.assertEqual(gate.execute(self.repo, "wrong/repo", self.b, self.p, self.k, self.a)["verdict"], "REJECTED")

    def test_pending_and_failure_leave_all_refs_unchanged(self):
        before = gate.git(self.repo, "show-ref")
        for status in ("PENDING", "FAIL"):
            self.b["receipts"][0]["status"] = status
            resign(self.b, self.k)
            self.assertNotEqual(self.execute()["verdict"], "COMMITTED")
            self.assertEqual(gate.git(self.repo, "show-ref"), before)

    def test_competing_requests_only_one_commits(self):
        second = copy.deepcopy(self.b)
        second["manifest"]["request"] = "request-2"
        resign(second, self.k)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(self.execute, (self.b, second)))
        self.assertEqual(sorted(r["verdict"] for r in results), ["COMMITTED", "REJECTED"])
        self.assertEqual(self.head(), self.candidate)
        self.assertEqual(len(gate.git(self.repo, "for-each-ref", "refs/admission/consumed").splitlines()), 1)

    def test_symbolic_target_cannot_redirect_write(self):
        gate.git(self.repo, "update-ref", "refs/heads/other", self.base)
        gate.git(self.repo, "symbolic-ref", "refs/heads/main", "refs/heads/other")
        before = gate.git(self.repo, "show-ref")
        self.assertEqual(self.execute()["verdict"], "REJECTED")
        self.assertEqual(gate.git(self.repo, "show-ref"), before)

    def test_lost_acknowledgement_preserves_uncertainty(self):
        real_git = gate.git
        def lose_ack(repo, *args, **kwargs):
            result = real_git(repo, *args, **kwargs)
            if args[:2] == ("update-ref", "--stdin"):
                raise subprocess.TimeoutExpired("git", 10)
            return result
        with patch.object(gate, "git", side_effect=lose_ack):
            self.assertEqual(self.execute()["verdict"], "UNRESOLVED")
        self.assertEqual(self.head(), self.candidate)
        self.assertEqual(self.execute()["verdict"], "REJECTED")


if __name__ == "__main__":
    unittest.main()

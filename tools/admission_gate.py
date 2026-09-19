"""Manifest-bound admission and an atomic, local bare-Git executor.

Policy, keys, repository identity, and evidence production are trusted inputs.
This module authenticates attestations; it does not prove their statements.
"""

import hashlib
import hmac
import json
import re
import subprocess


DOMAINS = ("behavior", "preservation", "integrity")
PINS = ("contract", "laws", "checker", "toolchain", "dependencies", "config")
MANIFEST_FIELDS = {"version", "repository", "target", "base", "candidate", "tree",
                   "policy", "epoch", "request", "actor", *PINS}


class Invalid(ValueError):
    pass


def exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise Invalid("unexpected object fields")


def digest(value, length=64):
    if type(value) is not str or re.fullmatch("[0-9a-f]{%d}" % length, value) is None:
        raise Invalid("invalid digest")


def identifier(value):
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}", value) is None:
        raise Invalid("invalid identifier")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_json(data):
    """Reject duplicate keys and nonstandard constants before canonicalization."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Invalid("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise Invalid("nonstandard JSON constant")

    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=constant)
    except (ValueError, RecursionError) as error:
        raise Invalid(str(error)) from error


def validate_policy(policy, keys):
    exact(policy, {"version", "repository", "target", "epoch", "actors", "domains", *PINS})
    if type(policy["version"]) is not int or policy["version"] != 1:
        raise Invalid("unsupported policy version")
    if type(policy["epoch"]) is not int or policy["epoch"] < 0:
        raise Invalid("invalid authority epoch")
    for field in ("repository", "target"):
        identifier(policy[field])
    if not policy["target"].startswith("refs/heads/"):
        raise Invalid("target must be a branch")
    for field in PINS:
        digest(policy[field])
    if type(policy["actors"]) is not list or not policy["actors"]:
        raise Invalid("empty actor domain")
    for actor in policy["actors"]:
        identifier(actor)
    if len(set(policy["actors"])) != len(policy["actors"]):
        raise Invalid("duplicate actor")
    exact(policy["domains"], DOMAINS)
    producers = []
    for domain in DOMAINS:
        rule = policy["domains"][domain]
        exact(rule, {"producer", "kind"})
        identifier(rule["producer"])
        if rule["kind"] not in ("checked-proof", "finite-check", "bounded-test"):
            raise Invalid("invalid evidence kind")
        producers.append(rule["producer"])
    if len(set(producers)) != len(DOMAINS) or set(producers) & set(policy["actors"]):
        raise Invalid("producer roles must be distinct from each other and actors")
    if type(keys) is not dict or any(type(keys.get(p)) is not bytes or len(keys[p]) < 32 for p in producers):
        raise Invalid("missing producer key")
    if len({keys[p] for p in producers}) != len(DOMAINS):
        raise Invalid("producer keys must be distinct")


def decide(bundle, policy, keys, artifacts):
    """Pure decision. Missing or unresolved evidence stays pending; invalid data rejects."""
    try:
        validate_policy(policy, keys)
        exact(bundle, {"manifest", "receipts"})
        m = bundle["manifest"]
        exact(m, MANIFEST_FIELDS)
        if type(m["version"]) is not int or m["version"] != 1:
            raise Invalid("unsupported manifest version")
        if type(m["epoch"]) is not int:
            raise Invalid("invalid manifest epoch")
        for field in ("repository", "target", "request", "actor"):
            identifier(m[field])
        for field in ("base", "candidate", "tree"):
            digest(m[field], 40)
        for field in ("policy", *PINS):
            digest(m[field])
        if m["policy"] != sha(canonical(policy)):
            raise Invalid("policy mismatch")
        if any(m[field] != policy[field] for field in ("repository", "target", "epoch", *PINS)):
            raise Invalid("authority or evaluation context mismatch")
        if m["actor"] not in policy["actors"]:
            raise Invalid("unauthorized actor")
        if type(bundle["receipts"]) is not list or len(bundle["receipts"]) > len(DOMAINS):
            raise Invalid("invalid receipt collection")
        if type(artifacts) is not dict:
            raise Invalid("invalid artifact collection")
        seen = set()
        pending = False
        binding = sha(canonical(m))
        for receipt in bundle["receipts"]:
            exact(receipt, {"domain", "producer", "kind", "manifest", "artifact", "status", "mac"})
            domain = receipt["domain"]
            if type(domain) is not str or domain not in DOMAINS or domain in seen:
                raise Invalid("duplicate or unknown domain")
            seen.add(domain)
            rule = policy["domains"][domain]
            if any(receipt[field] != rule[field] for field in ("producer", "kind")):
                raise Invalid("wrong producer or evidence kind")
            for field in ("manifest", "artifact", "mac"):
                digest(receipt[field])
            if receipt["manifest"] != binding:
                raise Invalid("stale evidence")
            payload = {k: v for k, v in receipt.items() if k != "mac"}
            expected = hmac.digest(keys[rule["producer"]], canonical(payload), "sha256").hex()
            if not hmac.compare_digest(receipt["mac"], expected):
                raise Invalid("invalid evidence authentication")
            data = artifacts.get(receipt["artifact"])
            if type(data) is not bytes or sha(data) != receipt["artifact"]:
                raise Invalid("missing or altered artifact")
            if receipt["status"] == "FAIL":
                raise Invalid("failed obligation")
            if receipt["status"] == "PENDING":
                pending = True
            elif receipt["status"] != "PASS":
                raise Invalid("invalid evidence status")
        if pending or seen != set(DOMAINS):
            return {"verdict": "PENDING", "reason": "required evidence unresolved"}
        return {"verdict": "ACCEPTED", "manifest": binding}
    except (Invalid, TypeError, ValueError, KeyError, RecursionError) as error:
        return {"verdict": "REJECTED", "reason": str(error)}


def git(repo, *args, input=None):
    return subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args],
                          input=input, text=True, capture_output=True, check=True, timeout=10).stdout.strip()


def execute(repo, repository_identity, bundle, policy, keys, artifacts):
    """Execute in a trusted bare repository. Atomically update target and consume request.

    Caller owns the repository and supplies a stable policy/key snapshot. There is
    no GitHub mutation, dynamic revocation, or worker authentication in this API.
    """
    decision = decide(bundle, policy, keys, artifacts)
    if decision["verdict"] != "ACCEPTED":
        return decision
    m = bundle["manifest"]
    try:
        if repository_identity != m["repository"]:
            raise Invalid("wrong repository identity")
        if git(repo, "rev-parse", "--is-bare-repository") != "true":
            raise Invalid("executor requires a bare repository")
        git(repo, "check-ref-format", m["target"])
        try:
            git(repo, "symbolic-ref", "-q", m["target"])
        except subprocess.CalledProcessError as error:
            if error.returncode != 1:
                raise
        else:
            raise Invalid("symbolic target is not supported")
        if git(repo, "cat-file", "-t", m["candidate"]) != "commit":
            raise Invalid("candidate is not a commit")
        if git(repo, "rev-parse", m["candidate"] + "^{tree}") != m["tree"]:
            raise Invalid("candidate tree mismatch")
        # A single parent binds the complete result to the checked base. This also
        # excludes unverified merge construction and unrelated histories.
        if git(repo, "show", "-s", "--format=%P", m["candidate"]) != m["base"]:
            raise Invalid("candidate must have exactly the expected base as parent")
        consumed = "refs/admission/consumed/" + sha(m["request"].encode("ascii"))
        transaction = ("start\noption no-deref\n" + f"update {m['target']} {m['candidate']} {m['base']}\n"
                       + f"create {consumed} {m['candidate']}\nprepare\ncommit\n")
        git(repo, "update-ref", "--stdin", input=transaction)
        return {"verdict": "COMMITTED", "manifest": decision["manifest"], "commit": m["candidate"]}
    except subprocess.TimeoutExpired:
        # The process may have committed before its acknowledgement was lost.
        return {"verdict": "UNRESOLVED", "reason": "execution timed out; inspect target and consumed-request ref"}
    except (Invalid, subprocess.SubprocessError, OSError) as error:
        return {"verdict": "REJECTED", "reason": str(error)}

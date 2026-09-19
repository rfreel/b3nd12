#!/usr/bin/env python3
"""Reproduce a staged checker bypass and evaluate the concrete verifier repair."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "de1ea9ce6c2f02537c79988e9a061775f1e43141"
PIN = "e5a4c4cfe980c2e4e70571562efb5197fe27b2f4"
TIMEOUT = 60


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def run(command, *, cwd=None, check=True):
    completed = subprocess.run(
        [str(item) for item in command], cwd=cwd, capture_output=True,
        text=True, timeout=TIMEOUT, env={**os.environ, "BEND_NO_TELEMETRY": "1"},
    )
    evidence = {"exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    if check and completed.returncode:
        raise RuntimeError(f"command failed: {command!r}: {evidence!r}")
    return evidence


def experiment(target):
    if shutil.which("bun") is None:
        raise RuntimeError("bun must be available in PATH so runtime checks cannot be skipped")
    if run(["git", "-C", target, "rev-parse", "HEAD"])["stdout"].strip() != PIN:
        raise RuntimeError("target is not at the pinned upstream revision")
    original = run(["git", "-C", ROOT, "show", f"{BASE_COMMIT}:verify.sh"])["stdout"]
    current = (ROOT / "verify.sh").read_text()
    environment = {
        "python": sys.version,
        "git": run(["git", "--version"])["stdout"].strip(),
        "bun": run(["bun", "--version"])["stdout"].strip(),
        "platform": sys.platform,
    }
    config = {"timeout_seconds": TIMEOUT, "upstream": PIN, "expected_exit": {"clean": 0, "unstaged": 1, "staged": 1}}
    context = {
        "suite_sha256": digest(Path(__file__).read_bytes()),
        "config_sha256": digest(config),
        "environment_sha256": digest(environment),
    }
    raw = {"before": {}, "after": {}}
    snapshots = {name: {"context": dict(context), "cases": []} for name in raw}
    with tempfile.TemporaryDirectory(prefix="checker-repair-") as directory:
        temp = Path(directory)
        clone = temp / "bend"
        run(["git", "clone", "--shared", "--no-checkout", target, clone])
        run(["git", "-C", clone, "checkout", "--detach", PIN])
        run(["sh", ROOT / "apply.sh", clone])
        verifier_paths = {}
        for name, source in (("before", original), ("after", current)):
            verifier_paths[name] = temp / (name + ".sh")
            verifier_paths[name].write_text(source)
        checker = clone / "bend2/bend.ts"
        for case in ("clean", "unstaged", "staged"):
            if case == "unstaged":
                with checker.open("a") as output:
                    output.write("\n// Repair admission probe: harmless checker comment.\n")
            elif case == "staged":
                run(["git", "-C", clone, "add", "--", "bend2/bend.ts"])
            for name in ("before", "after"):
                evidence = run(["sh", verifier_paths[name], clone], check=False)
                expected = config["expected_exit"][case]
                passed = evidence["exit_code"] == expected
                if expected != 0:
                    passed = passed and "forbidden bend2/bend.ts change" in evidence["stderr"]
                evidence["expected_exit_code"] = expected
                raw[name][case] = evidence
                snapshots[name]["cases"].append({
                    "id": case, "status": "PASS" if passed else "FAIL", "evidence_sha256": digest(evidence),
                })
    report = {"schema_version": 1, "target_case": "staged", **snapshots}
    spec = importlib.util.spec_from_file_location("repair_gate", ROOT / "tools/repair_gate.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    decision = gate.evaluate(report)
    expected_pattern = (
        [case["status"] for case in snapshots["before"]["cases"]] == ["PASS", "PASS", "FAIL"]
        and all(case["status"] == "PASS" for case in snapshots["after"]["cases"])
    )
    return {
        "schema_version": 1,
        "experiment": "staged checker modification bypass",
        "baseline_commit": BASE_COMMIT,
        "before_verifier_sha256": digest(original.encode()),
        "after_verifier_sha256": digest(current.encode()),
        "environment": environment,
        "config": config,
        "raw_evidence": raw,
        "report": report,
        "decision": decision,
        "expected_pattern_observed": expected_pattern,
        "scope": "Three real local verifier probes. Temporary clone only; no edits to the supplied target.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = experiment(args.target.resolve())
        code = 0 if result["expected_pattern_observed"] and result["decision"]["verdict"] == "ACCEPTED" else 1
    except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError) as error:
        result = {"schema_version": 1, "error": str(error), "verdict": "UNRESOLVED"}
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "exit_code": code}))
    return code


if __name__ == "__main__":
    sys.exit(main())

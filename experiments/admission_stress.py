#!/usr/bin/env python3
"""Bounded stress campaign. Mutants run in disposable copies, never the worktree."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = {
    "ignore-policy": ('if m["policy"] != sha(canonical(policy)):', 'if False:'),
    "ignore-context": ('if any(m[field] != policy[field] for field in ("repository", "target", "epoch", *PINS)):', 'if False:'),
    "ignore-actor": ('if m["actor"] not in policy["actors"]:', 'if False:'),
    "ignore-binding": ('if receipt["manifest"] != binding:', 'if False:'),
    "ignore-authentication": ('if not hmac.compare_digest(receipt["mac"], expected):', 'if False:'),
    "ignore-artifact": ('if type(data) is not bytes or sha(data) != receipt["artifact"]:', 'if False:'),
    "accept-missing": ('if pending or seen != set(DOMAINS):', 'if pending:'),
    "reject-everything": ('return {"verdict": "ACCEPTED", "manifest": binding}', 'return {"verdict": "REJECTED", "reason": "mutant"}'),
    "ignore-tree": ('if git(repo, "rev-parse", m["candidate"] + "^{tree}") != m["tree"]:', 'if False:'),
    "ignore-parent": ('if git(repo, "show", "-s", "--format=%P", m["candidate"]) != m["base"]:', 'if False:'),
    "allow-replay": ('f"create {consumed} {m[\'candidate\']}\\nprepare\\ncommit\\n"', 'f"update {consumed} {m[\'candidate\']}\\nprepare\\ncommit\\n"'),
    "stale-base-write": ('f"update {m[\'target\']} {m[\'candidate\']} {m[\'base\']}\\n"', 'f"update {m[\'target\']} {m[\'candidate\']}\\n"'),
    "timeout-is-rejection": ('return {"verdict": "UNRESOLVED", "reason": "execution timed out; inspect target and consumed-request ref"}', 'return {"verdict": "REJECTED", "reason": "timeout"}'),
}


def run(root):
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_admission_gate.py", "-q"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
    return {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = (ROOT / "tools/admission_gate.py").read_text()
    result = {"schema_version": 1, "scope": "1024 finite decision cases, malformed inputs, real Git transactions, 13 seeded mutations",
              "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "tests_sha256": hashlib.sha256((ROOT / "tests/test_admission_gate.py").read_bytes()).hexdigest(),
              "baseline": run(ROOT), "mutants": {}, "saturated": False}
    if result["baseline"]["exit"] != 0:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        return 1
    for name, (old, new) in MUTANTS.items():
        if source.count(old) != 1:
            raise RuntimeError("mutation anchor drift: " + name)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools").mkdir()
            (root / "tests").mkdir()
            (root / "tools/admission_gate.py").write_text(source.replace(old, new, 1))
            shutil.copy(ROOT / "tests/test_admission_gate.py", root / "tests")
            observation = run(root)
            # A syntax/import failure does not demonstrate detection of the fault.
            killed = observation["exit"] != 0 and "AssertionError" in observation["stderr"]
            result["mutants"][name] = {"killed": killed, **observation}
    result["saturated"] = all(r["killed"] for r in result["mutants"].values())
    result["stop_rule"] = "Stop after complete finite partition and all declared mutations are detected. Reopen for a new fault class or changed source; no global completeness claim."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"mutants": len(result["mutants"]), "killed": sum(r["killed"] for r in result["mutants"].values()), "saturated": result["saturated"]}))
    return 0 if result["saturated"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Real CLI integration experiment; not an agent productivity benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.interaction import ARMS, FEATURES, evaluate, read_json


def run(runtime, main):
    main = Path(main).resolve()
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=main.parent, text=True).strip()
    upstream = main.parent.parent
    project = Path(__file__).resolve().parents[1]
    tracked = ["bend2/main.ts", "bend2/bend.ts", "bend2/base.bend", "bend2/comp.ts",
               "guide/agent/diagnostics.json"]
    hashes = {name: hashlib.sha256((upstream / name).read_bytes()).hexdigest()
              for name in tracked}
    for name in ("experiments/diagnostic_interaction.py", "tools/interaction.py"):
        hashes[name] = hashlib.sha256((project / name).read_bytes()).hexdigest()
    for name in ("fixtures/PROOF.bend", "fixtures/LAWS.bend"):
        hashes[name] = hashlib.sha256(b"").hexdigest()
    system = {"revision": revision,
              "runtime": "bun " + subprocess.check_output([runtime, "--version"], text=True).strip(),
              "files_sha256": hashes}
    results = []
    with tempfile.TemporaryDirectory(prefix="bend-interaction-") as directory:
        fixture = Path(directory)
        (fixture / "PROOF.bend").write_text("")
        (fixture / "LAWS.bend").write_text("")

        def invoke(args):
            completed = subprocess.run([runtime, str(main), *args], cwd=fixture,
                                       capture_output=True, text=True, timeout=20)
            return {"args": args, "exit_code": completed.returncode,
                    "stdout": completed.stdout, "stderr": completed.stderr,
                    "bytes": len(completed.stdout.encode()) + len(completed.stderr.encode())}

        for arm in ARMS:
            evidence = [invoke(["PROOF.bend"] + (["--json"] if arm in ("a", "ab") else []))]
            first = evidence[0]
            if first["exit_code"] != 1:
                raise ValueError("fixture did not fail with expected exit status")
            message = first["stderr"]
            if arm in ("a", "ab"):
                event = read_json(message)
                diagnostic = event["id"]
                message = event["message"]
            else:
                diagnostic = "BND101" if "PROOF.bend must import ./LAWS.bend" in message else None
            if diagnostic != "BND101":
                raise ValueError("fixture did not produce the expected diagnostic")
            if arm in ("b", "ab"):
                evidence.append(invoke(["--why", diagnostic]))
                if evidence[-1]["exit_code"] != 0:
                    raise ValueError("explanation lookup failed")
                message += evidence[-1]["stdout"]
            # The plain diagnostic already contains a usable repair hint.
            resolved = "import ./laws.bend" in message.lower()
            results.append({"arm": arm, "features": FEATURES[arm],
                            "evaluation": "missing-laws-import-resolver-v1",
                            "cases": ["empty PROOF.bend beside empty LAWS.bend"],
                            "budget": {"max_cli_calls_per_case": 2, "timeout_seconds_per_call": 20},
                            "metric": {"name": "correct import repair hint present",
                                       "unit": "cases", "direction": "higher_is_better"},
                            "system": system, "status": "observed", "score": int(resolved),
                            "evidence": evidence, "calls": len(evidence),
                            "bytes": sum(item["bytes"] for item in evidence)})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", default="bun")
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    records = run(args.runtime, args.main)
    result = evaluate(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"records": records, "result": result}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

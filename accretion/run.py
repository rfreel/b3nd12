#!/usr/bin/env python3
"""Evaluate routing candidates and admit only exact bytes with a checked certificate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from environment import ROOT, TASKS, decode, resolve
sys.path.insert(0, str(ROOT))
import bounded

HERE = Path(__file__).resolve().parent
PIN = json.loads((ROOT / "upstream.json").read_text())["commit"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def measure(raw, workspace):
    decode(raw)
    file = workspace / "candidate.json"
    file.write_bytes(raw)
    outcomes = {task: resolve(task, file) for task in TASKS}
    preserved = all(row["text"].encode() == (ROOT / "guide/agent" / TASKS[task]).read_bytes()
                    for task, row in outcomes.items())
    return {"preserved": preserved, "reads": {task: row["reads"] for task, row in outcomes.items()}}


# Exact diagnostic from the pinned checker for this frozen false equality.
REFUSAL = ("Error:\n- expected : False{}\n- observed : True{}\n"
           "Location: LAWS.improves_next_agent\n"
           "4 | def Laws.improves_next_agent():\n5>|   {==}\n6 | \n")


# Three observations can expand each raw byte to six JSON bytes. A 256 KiB
# checker cap leaves space for all three streams and metadata below 8 MiB.
CHECKER_OUTPUT_BYTES = 256 * 1024


def check_book(cmd):
    """Retain process evidence without turning transport failure into law refusal."""
    evidence = {"command": cmd, "stage": "checker", "exit": None,
                "stdout": "", "stderr": ""}
    def stream(value):
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
    try:
        process = bounded.run(cmd, env={**os.environ, "BEND_NO_TELEMETRY": "1"},
                                 capture_output=True, text=True, timeout=15,
                                 max_output_bytes=CHECKER_OUTPUT_BYTES)
    except bounded.OutputLimitExceeded as exc:
        evidence.update(status="output_limit", stdout=stream(exc.stdout), stderr=stream(exc.stderr),
                        limit_bytes=exc.limit_bytes, observed_bytes=exc.observed_bytes, error=str(exc))
    except subprocess.TimeoutExpired as exc:
        evidence.update(status="timeout", stdout=stream(exc.stdout), stderr=stream(exc.stderr),
                        timeout_seconds=exc.timeout, error=str(exc))
    except OSError as exc:
        evidence.update(status="spawn_error", error=str(exc))
    except UnicodeError as exc:
        evidence.update(status="malformed_certificate", error=str(exc))
    else:
        evidence.update(exit=process.returncode, stdout=process.stdout, stderr=process.stderr)
        if process.returncode == 0 and process.stdout == "All terms check.\n" and process.stderr == "":
            status = "accepted"
        elif process.returncode == 1 and process.stdout == "" and process.stderr == REFUSAL:
            status = "refused"
        elif process.returncode < 0:
            status = "crash"
        elif process.returncode != 0:
            status = "process_error"
        elif process.stdout == "" and process.stderr == "":
            status = "missing_certificate"
        else:
            status = "malformed_certificate"
        evidence["status"] = status
    return evidence


def admit(before, after, bun, bend, workspace):
    before_sha, after_sha = sha(before), sha(after)
    old = measure(before, workspace)
    new = measure(after, workspace)
    safe = old["preserved"] and new["preserved"]
    no_regressions = all(new["reads"][t] <= old["reads"][t] for t in TASKS)
    book = workspace / "book"
    book.mkdir(exist_ok=True)
    for name in ("LAWS.bend", "PROOF.bend"):
        (book / name).write_bytes((HERE / name).read_bytes())
    evidence = {"preserved": safe, "no_regressions": no_regressions,
                "before": sum(old["reads"].values()), "after": sum(new["reads"].values()),
                "candidate_bytes": len(after)}
    lines = ["import Base\n"]
    for key, val in evidence.items():
        typ, term = ("Bool", "True{}" if val else "False{}") if type(val) is bool else ("Nat", str(val)+"n")
        lines.append(f"def {key}() -> {typ}:\n  {term}\n")
    (book / "Evidence.bend").write_text("\n".join(lines))
    cmd = [str(bun), str(bend / "bend2/main.ts"), str(book / "PROOF.bend")]
    checker = check_book(cmd)
    accepted = checker["status"] == "accepted"
    return {"accepted": accepted, "baseline_sha256": before_sha, "candidate_sha256": after_sha,
            "law_sha256": sha((HERE / "LAWS.bend").read_bytes()), "metrics": evidence,
            "before_reads": old["reads"], "after_reads": new["reads"],
            "book_sha256": {name: sha((book / name).read_bytes())
                            for name in ("Evidence.bend", "LAWS.bend", "PROOF.bend")},
            "checker": checker}


def validate_compiler(bend):
    head = bounded.check_output(["git", "-C", str(bend), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise ValueError("compiler must be at the B3ND12 pin")
    for name in ("bend2/bend.ts", "bend2/base.bend", "bend2/main.ts", "bend2/comp.ts"):
        original = bounded.check_output(["git", "-C", str(bend), "show", PIN+":"+name])
        if (bend / name).read_bytes() != original:
            raise ValueError("checker inputs differ from pinned source: " + name)


def rounds(bun, bend, promote=False):
    validate_compiler(bend)
    protected = {p: p.read_bytes() for p in [HERE / "LAWS.bend", HERE / "PROOF.bend", HERE / "environment.py",
                  HERE / "run.py", ROOT / "bounded.py", ROOT / "upstream.json", ROOT / "guide/agent/ROUTER.md", *[ROOT / "guide/agent" / n for n in TASKS.values()]]}
    seal = {str(p.relative_to(ROOT)): sha(raw) for p, raw in protected.items()}
    before = b"{}\n"
    destination = HERE / "routes.json"
    if promote and destination.read_bytes() != before:
        raise ValueError("promotion demo requires the original empty routing table; never reset accepted state")
    results = []
    with tempfile.TemporaryDirectory(prefix="bend-accretion-") as tmp:
        workspace = Path(tmp)
        # Check a refusal before any promotion, so a trivially permissive law
        # cannot mutate accepted state during this demonstration.
        control = admit(before, before, bun, bend, workspace)
        if control["checker"]["status"] != "refused":
            raise ValueError("no-gain control did not establish law refusal: " + json.dumps(control))
        mapping = {}
        for task, filename in TASKS.items():
            mapping[task] = filename
            after = (json.dumps(mapping, sort_keys=True, indent=2)+"\n").encode()
            result = admit(before, after, bun, bend, workspace)
            if any(p.read_bytes() != raw for p, raw in protected.items()):
                raise ValueError("frozen evaluator or law changed")
            if not result["accepted"]:
                raise ValueError("candidate failed: " + json.dumps(result))
            if promote:
                if destination.read_bytes() != before:
                    raise ValueError("accepted state changed during evaluation")
                # Install the same immutable bytes evaluated above, never reread candidate input.
                fd, name = tempfile.mkstemp(dir=HERE, prefix=".routes-")
                try:
                    with os.fdopen(fd, "wb") as file:
                        file.write(after)
                        file.flush()
                        os.fsync(file.fileno())
                    os.replace(name, destination)
                finally:
                    if os.path.exists(name): os.unlink(name)
            results.append(result)
            before = after
        negative = {}
        for label, raw in {"no_gain": before, "regression": b"{}\n",
                           "wrong_content": b'{"implement":"PROVE.md","prove":"PROVE.md","diagnose":"diagnostics.json"}'}.items():
            result = admit(before, raw, bun, bend, workspace)
            if result["checker"]["status"] != "refused":
                raise AssertionError("negative control did not establish law refusal: " + label + json.dumps(result))
            negative[label] = result
        for label, raw in {"path_escape": b'{"implement":"../../secret"}',
                           "unknown_task": b'{"invented":"PROGRAM.md"}',
                           "duplicate_task": b'{"prove":"PROVE.md","prove":"PROGRAM.md"}',
                           "over_budget": b' '*4097}.items():
            try: decode(raw)
            except (ValueError, json.JSONDecodeError): negative[label] = {"accepted": False, "stage": "schema"}
            else: raise AssertionError("invalid schema accepted")
        if promote and destination.read_bytes() != before:
            raise AssertionError("negative trials changed accepted state")
    return {"schema": "b3nd12.accretion.v1", "pin": PIN, "seal": seal,
            "rounds": results, "negative_controls": negative,
            "promoted": promote, "final_sha256": sha(before),
            "scope": "deterministic three-task file-read workload; not an agent-performance or hostile-process isolation claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bun", required=True, type=Path)
    parser.add_argument("--bend-root", required=True, type=Path)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--candidate", type=Path, help="evaluate a routing JSON file against current accepted routes")
    args = parser.parse_args()
    try:
        if args.candidate:
            if args.promote:
                raise ValueError("candidate mode is review-only; arbitrary promotion requires an external controller")
            validate_compiler(args.bend_root.resolve())
            before = (HERE / "routes.json").read_bytes()
            with args.candidate.open("rb") as source:
                after = source.read(4097)
            with tempfile.TemporaryDirectory(prefix="bend-candidate-") as tmp:
                verdict = admit(before, after, args.bun.resolve(), args.bend_root.resolve(), Path(tmp))
            print(json.dumps(verdict, indent=2))
            sys.exit(0 if verdict["accepted"] else 1)
        else:
            print(json.dumps(rounds(args.bun.resolve(), args.bend_root.resolve(), args.promote), indent=2))
    except Exception as exc:
        print(json.dumps({"schema": "b3nd12.accretion.v1", "error": str(exc)}))
        sys.exit(1)

#!/usr/bin/env python3
"""Replay a sealed, finite routing experiment; never install or activate a successor."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

from environment import ROOT, TASKS, decode
from run import HERE, PIN, admit, measure, sha, validate_compiler


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def load_contract(expected):
    raw = (HERE / "TODO.json").read_bytes()
    if sha(raw) != expected:
        raise ValueError("contract digest differs from the operator's seal")
    contract = json.loads(raw)
    required = {"accretion/LAWS.bend", "accretion/PROOF.bend", "upstream.json",
                "guide/agent/ROUTER.md", *["guide/agent/" + n for n in TASKS.values()]}
    if set(contract["protected"]) != required or contract["final_task"] != "propose-successor":
        raise ValueError("incomplete frozen contract")
    # This controller supports one declared workload, not arbitrary policy code.
    if contract["schema"] != "b3nd12.todo.v1" or contract["pin"] != PIN:
        raise ValueError("unsupported contract")
    if contract["baseline"] != {} or contract["targets"] != [8, 7, 6]:
        raise ValueError("unsupported baseline or outcomes")
    if contract["max_attempts"] != 6 or contract["repetitions"] != 3:
        raise ValueError("unsupported experiment budget")
    for name, digest in contract["protected"].items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("protected input changed: " + name)
    return contract, raw


def journal(directory, records, event):
    row = {"sequence": len(records), "previous": records[-1]["sha256"] if records else None,
           "event": event}
    row["sha256"] = sha(encode(row))
    with (directory / "ledger.jsonl").open("ab") as stream:
        stream.write(json.dumps(row, sort_keys=True).encode() + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    records.append(row)


def replay(output, expected, bun, bend, candidates=None):
    output = output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        raise ValueError("evidence output must be outside the repository")
    contract, raw = load_contract(expected)
    validate_compiler(bend)
    frozen = {p: p.read_bytes() for p in [HERE / "TODO.json", HERE / "program.py",
              HERE / "run.py", HERE / "environment.py", HERE / "PROOF.bend",
              HERE / "routes.json", *[ROOT / n for n in contract["protected"]]]}

    def unchanged():
        if any(p.read_bytes() != value for p, value in frozen.items()):
            raise ValueError("sealed input changed during experiment")

    # A new directory owns one run. Existing evidence is never overwritten or resumed.
    output.mkdir(parents=True, exist_ok=False)
    (output / "TODO.json").write_bytes(raw)
    for path, value in frozen.items():
        snapshot = output / "inputs" / path.relative_to(ROOT)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(value)
    manifest = {str(p.relative_to(ROOT)): sha(value) for p, value in frozen.items()}
    metadata = {"schema": "b3nd12.experiment.v1", "contract_sha256": expected,
                "inputs": manifest, "pin": PIN, "python": platform.python_version(),
                "platform": platform.platform(), "bun_sha256": sha(bun.read_bytes()),
                "bun_version": subprocess.check_output([str(bun), "--version"], text=True).strip(),
                "source": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
                "working_tree": subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True),
                "scope": "constructed deterministic routing workload; no agent latency claim"}
    (output / "manifest.json").write_bytes(encode(metadata))
    records, completed = [], []
    before = b"{}\n"
    with tempfile.TemporaryDirectory(prefix="b3nd12-program-") as temporary:
        workspace = Path(temporary)
        control = admit(before, before, bun, bend, workspace)
        if control["accepted"]:
            raise ValueError("no-gain control accepted")
        journal(output, records, {"kind": "baseline", "control": control,
                                 "profile": measure(before, workspace)})
        queue = iter(candidates) if candidates is not None else None
        stop = "budget_exhausted"
        for attempt in range(1, contract["max_attempts"] + 1):
            unchanged()
            current = decode(before)
            # Re-profile after each trial. Only missing routes can reduce reads.
            profile = measure(before, workspace)
            remaining = sorted((t for t in TASKS if t not in current),
                               key=lambda t: (-profile["reads"][t], t))
            if not remaining:
                stop = "target_met"
                break
            if queue is None:
                after = encode({**current, remaining[0]: TASKS[remaining[0]]})
            else:
                try:
                    after = next(queue)
                except StopIteration:
                    stop = "candidates_exhausted"
                    break
            packet = output / f"pass-{attempt:03d}"
            packet.mkdir()
            (packet / "before.json").write_bytes(before)
            (packet / "candidate.json").write_bytes(after)
            journal(output, records, {"kind": "attempt", "attempt": attempt,
                                     "baseline_sha256": sha(before), "candidate_sha256": sha(after)})
            samples = []
            try:
                mapping = decode(after)
                changed = [t for t in TASKS if current.get(t) != mapping.get(t)]
                if len(changed) > 1:
                    raise ValueError("one routing lever per trial")
                # Each paired observation calls the real resolver and checker.
                for _ in range(contract["repetitions"]):
                    samples.append(admit(before, after, bun, bend, workspace))
                metrics = [s["metrics"] for s in samples]
                if any(m != metrics[0] for m in metrics):
                    verdict, reason = "UNKNOWN", "inconsistent deterministic observations"
                elif all(s["accepted"] for s in samples):
                    verdict, reason = "PRODUCTIVE", "strict read reduction with exact content preserved"
                elif not metrics[0]["preserved"] or not metrics[0]["no_regressions"]:
                    verdict, reason = "REJECTED", "protected behavior or per-task cost regressed"
                elif metrics[0]["before"] == metrics[0]["after"]:
                    verdict, reason = "NEUTRAL", "no measured read reduction"
                else:
                    verdict, reason = "UNKNOWN", "checker did not establish acceptance"
            except (ValueError, UnicodeError) as exc:
                verdict, reason = "REJECTED", str(exc)
            except (subprocess.SubprocessError, OSError) as exc:
                verdict, reason = "UNKNOWN", str(exc)
            unchanged()
            receipt = {"attempt": attempt, "verdict": verdict, "reason": reason,
                       "contract_sha256": expected, "baseline_sha256": sha(before),
                       "candidate_sha256": sha(after), "samples": samples,
                       "mechanism": "one direct route avoids one fallback router read",
                       "equivalence": "all three returned documents equal the frozen expected bytes",
                       "end_to_end": "not measured; no fresh-agent productivity conclusion"}
            (packet / "receipt.json").write_bytes(encode(receipt))
            journal(output, records, {"kind": "verdict", "attempt": attempt,
                                     "receipt_sha256": sha(encode(receipt)), "verdict": verdict})
            if verdict == "PRODUCTIVE":
                before = after
                reads = samples[0]["metrics"]["after"]
                for target in contract["targets"]:
                    task = f"reads-at-most-{target}"
                    if reads <= target and task not in completed:
                        completed.append(task)
                        journal(output, records, {"kind": "completed", "task": task,
                                                 "attempt": attempt, "candidate_sha256": sha(before)})
            if verdict == "UNKNOWN":
                stop = "unresolved"
                break
        final = measure(before, workspace)
        if sum(final["reads"].values()) == 6:
            stop = "target_met"
        successor = None
        if len(completed) == len(contract["targets"]):
            successor = {"schema": "b3nd12.successor.v1", "parent_contract_sha256": expected,
                         "status": "exhausted", "candidates": [], "activation": "not_authorized",
                         "evidence": final,
                         "reason": "each task reads the table and its document; no missing route remains",
                         "reopen_when": "a separately reviewed workload or representation supplies a measurable opportunity"}
            (output / "successor.json").write_bytes(encode(successor))
            completed.append("propose-successor")
            journal(output, records, {"kind": "completed", "task": "propose-successor",
                                     "proposal_sha256": sha(encode(successor))})
        unchanged()
        summary = {"schema": "b3nd12.experiment.v1", "stop": stop, "completed": completed,
                   "final": final, "final_sha256": sha(before), "successor": successor,
                   "installed": False, "contract_sha256": expected}
        (output / "final.json").write_bytes(before)
        journal(output, records, {"kind": "stop", **summary})
        (output / "summary.json").write_bytes(encode(summary))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bun", required=True, type=Path)
    parser.add_argument("--bend-root", required=True, type=Path)
    parser.add_argument("--candidate", action="append", type=Path,
                        help="trial file in order; repeat up to six times instead of automatic selection")
    args = parser.parse_args()
    try:
        candidates = None
        if args.candidate:
            if len(args.candidate) > 6:
                raise ValueError("at most six candidate attempts")
            candidates = []
            for path in args.candidate:
                with path.open("rb") as stream:
                    candidates.append(stream.read(4097))
        result = replay(args.output.resolve(), args.contract_sha256, args.bun.resolve(), args.bend_root.resolve(), candidates)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["stop"] == "target_met" else 1)
    except Exception as exc:
        print(json.dumps({"schema": "b3nd12.experiment.v1", "error": str(exc)}))
        raise SystemExit(1)

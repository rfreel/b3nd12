"""Stable JSON command boundary for repository agents."""

import argparse
from pathlib import Path
import shutil
import sys

from .contracts import Problem, canonical, load_plan, parse, safe_path
from .evidence import execute, verify
from .state import append, project, read_events

ROOT = Path(__file__).resolve().parents[2]


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Problem("INVALID_ARGUMENTS", message)


def compact(current):
    attention = [t for t in current["tasks"] if t["status"] in {"BLOCKED", "UNRESOLVED", "STALE"}]
    return {key: current[key] for key in ("head", "events", "counts", "next")} | {
        "attention": attention[:8], "attention_total": len(attention)}


def dispatch(args):
    root = args.root.resolve()
    plan = load_plan(root)
    journal = safe_path(root, args.state)
    events = read_events(journal, plan)
    current = project(root, plan, events)
    tasks = {task["id"]: task for task in plan["tasks"]}
    if getattr(args, "task", None) and args.task not in tasks:
        raise Problem("UNKNOWN_TASK", f"task does not exist: {args.task}")
    if args.command == "status":
        return current if args.full else compact(current)
    if args.command == "next":
        return {"head": current["head"], "next": current["next"], "attention": compact(current)["attention"]}
    if args.command == "changes":
        from .state import GENESIS
        if not 1 <= args.limit <= 100:
            raise Problem("INVALID_ARGUMENTS", "limit must be between 1 and 100")
        positions = {GENESIS: 0, **{event["sha256"]: index + 1 for index, event in enumerate(events)}}
        if args.since not in positions:
            raise Problem("UNKNOWN_HEAD", "cursor is not in this journal")
        start = positions[args.since]
        batch = events[start:start + args.limit]
        return {"events": batch, "cursor": batch[-1]["sha256"] if batch else args.since,
                "more": start + len(batch) < len(events), "head": current["head"]}
    if args.command == "metrics":
        from .benchmarks import validate_metrics
        return validate_metrics(parse((root / "system/metrics.json").read_text()))
    if args.command == "explain":
        return {"contract": tasks[args.task], "state": next(t for t in current["tasks"] if t["id"] == args.task)}
    if args.command == "transition":
        evidence = parse(safe_path(root, args.evidence).read_text()) if args.evidence else None
        if evidence is not None:
            from .contracts import digest
            if not isinstance(evidence, dict) or type(evidence.get("schema_version")) is not int or evidence["schema_version"] != 1:
                raise Problem("INVALID_EVIDENCE", "expected an evidence object with schema version 1")
            evidence = {"path": args.evidence, "sha256": digest(safe_path(root, args.evidence).read_bytes()),
                        "passed": evidence.get("passed") is True}
        payload = {"task": args.task, "status": args.status, "reason": args.reason,
                   "reopen": args.reopen, "evidence": evidence}
        return append(root, plan, journal, payload, args.request, args.head)
    if args.command == "verify":
        result = verify(root, tasks[args.task], args.run_id)
        if not result["passed"]:
            raise Problem("VERIFICATION_FAILED", f"retained failure: {result['path']}")
        return result
    if args.command == "check":
        stale = [t["id"] for t in current["tasks"] if t["status"] == "STALE"]
        if stale:
            raise Problem("STALE_EVIDENCE", "reopen and verify: " + ", ".join(stale))
        return {"valid": True, "events": len(events), "tasks": len(tasks), "head": current["head"]}
    if args.command == "doctor":
        result = {"python": sys.version.split()[0], "platform": sys.platform,
                  "capabilities": {name: shutil.which(name) for name in ("git", "bun")},
                  "scope": "Local probes only; GitHub authorization and worker isolation are not established."}
        if args.target:
            target = args.target.resolve()
            pin = parse((root / "upstream.json").read_text())["commit"]
            revision = execute(["git", "-C", str(target), "rev-parse", "HEAD"], root, 5)
            result["bend"] = {"expected": pin, "actual": revision["stdout"].strip(),
                              "pinned": revision["passed"] and revision["stdout"].strip() == pin}
        return result
    if args.command == "todo":
        lines = ["# Current work", "", "Generated from system/roadmap.json and state/events.jsonl.", "",
                 "| ID | Status | Task | Dependencies |", "| --- | --- | --- | --- |"]
        states = {t["id"]: t["status"] for t in current["tasks"]}
        for task in plan["tasks"]:
            lines.append(f"| {task['id']} | {states[task['id']]} | {task['title']} | {', '.join(task['depends']) or 'none'} |")
        return {"markdown": "\n".join(lines) + "\n", "head": current["head"]}
    if args.command == "benchmark":
        from .benchmarks import benchmark
        result = benchmark(root, plan, events, args.state)
        path = safe_path(root, args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as output:
            output.write(canonical(result) + "\n")
        return {"path": args.output, "metrics": result["measurements"]}
    raise Problem("UNKNOWN_COMMAND", args.command)


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", default="state/events.jsonl")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status")
    status.add_argument("--full", action="store_true")
    for command in ("next", "check", "todo", "metrics"):
        commands.add_parser(command)
    changes = commands.add_parser("changes")
    changes.add_argument("--since", required=True)
    changes.add_argument("--limit", type=int, default=20)
    explain = commands.add_parser("explain")
    explain.add_argument("task")
    transition = commands.add_parser("transition")
    transition.add_argument("task")
    transition.add_argument("status")
    transition.add_argument("--request", required=True)
    transition.add_argument("--head", required=True)
    transition.add_argument("--reason", required=True)
    transition.add_argument("--reopen", default="")
    transition.add_argument("--evidence")
    verification = commands.add_parser("verify")
    verification.add_argument("task")
    verification.add_argument("--run-id", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--target", type=Path)
    benchmark_parser = commands.add_parser("benchmark")
    benchmark_parser.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
        result = dispatch(args)
        print(canonical({"schema_version": 1, "ok": True, "result": result}))
        return 0
    except (Problem, OSError, ValueError, KeyError, TypeError) as error:
        print(canonical({"schema_version": 1, "ok": False,
                         "error": {"code": getattr(error, "code", "IO_OR_INPUT_ERROR"), "message": str(error)}}))
        return 2

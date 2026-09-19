"""Append-only task transitions and evidence-aware projections."""

from collections import Counter
import fcntl
import os
from pathlib import Path

from .contracts import Problem, canonical, digest, identifier, parse
from .evidence import fresh

GENESIS = "0" * 64
STATUSES = {"OPEN", "RUNNING", "SOLVED", "BLOCKED", "UNRESOLVED"}
ALLOWED = {
    "OPEN": {"RUNNING", "BLOCKED", "UNRESOLVED"},
    "RUNNING": {"SOLVED", "BLOCKED", "UNRESOLVED", "OPEN"},
    "SOLVED": {"OPEN"}, "STALE": {"OPEN"},
    "BLOCKED": {"OPEN"}, "UNRESOLVED": {"OPEN"},
}


def decode_history(text, plan):
    if text and not text.endswith("\n"):
        raise Problem("CORRUPT_HISTORY", "journal has an incomplete tail; preserve it for recovery")
    result, seen, head = [], set(), GENESIS
    task_ids = {task["id"] for task in plan["tasks"]}
    plan_hash = digest(plan)
    states = dict.fromkeys(task_ids, "OPEN")
    dependencies = {task["id"]: task["depends"] for task in plan["tasks"]}
    for line in text.splitlines():
        event = parse(line)
        if not isinstance(event, dict) or set(event) != {"seq", "parent", "plan", "request", "payload", "sha256"}:
            raise Problem("CORRUPT_HISTORY", "invalid event fields")
        body = {key: value for key, value in event.items() if key != "sha256"}
        if type(event["seq"]) is not int or event["seq"] != len(result) + 1 or event["parent"] != head or digest(body) != event["sha256"]:
            raise Problem("CORRUPT_HISTORY", "event sequence or digest mismatch")
        if event["plan"] != plan_hash:
            raise Problem("PLAN_DRIFT", "roadmap changed; an explicit migration is required")
        if not identifier(event["request"]) or event["request"] in seen:
            raise Problem("CORRUPT_HISTORY", "invalid or duplicate request ID")
        validate_payload(event["payload"], task_ids)
        payload = event["payload"]
        identity, status = payload["task"], payload["status"]
        if status not in ALLOWED[states[identity]]:
            raise Problem("CORRUPT_HISTORY", "historically inadmissible transition")
        if status in {"RUNNING", "SOLVED"} and any(states[d] != "SOLVED" for d in dependencies[identity]):
            raise Problem("CORRUPT_HISTORY", "historical dependency was not solved")
        if status == "RUNNING" and "RUNNING" in states.values():
            raise Problem("CORRUPT_HISTORY", "historical work-in-progress limit exceeded")
        states[identity] = status
        seen.add(event["request"])
        result.append(event)
        head = event["sha256"]
    return result


def read_events(path, plan):
    path = Path(path)
    if not path.exists():
        return []
    with path.open() as source:
        fcntl.flock(source, fcntl.LOCK_SH)
        return decode_history(source.read(), plan)


def validate_payload(payload, task_ids):
    fields = {"task", "status", "reason", "reopen", "evidence"}
    if not isinstance(payload, dict) or set(payload) != fields:
        raise Problem("INVALID_TRANSITION", "transition fields differ from contract")
    if not identifier(payload["task"]) or not isinstance(payload["status"], str) or payload["task"] not in task_ids or payload["status"] not in STATUSES:
        raise Problem("INVALID_TRANSITION", "unknown task or status")
    if not isinstance(payload["reason"], str) or not payload["reason"].strip() or not isinstance(payload["reopen"], str):
        raise Problem("INVALID_TRANSITION", "reason is required")
    if payload["status"] in {"BLOCKED", "UNRESOLVED"} and not payload["reopen"].strip():
        raise Problem("INVALID_TRANSITION", "blocked and unresolved tasks need a reopen condition")
    if payload["evidence"] is not None and not isinstance(payload["evidence"], dict):
        raise Problem("INVALID_TRANSITION", "evidence must be a reference or null")


def project(root, plan, events):
    tasks = {t["id"]: t for t in plan["tasks"]}
    state = {identity: {"status": "OPEN", "reason": "No recorded transition", "reopen": task["reopen"], "evidence": None}
             for identity, task in tasks.items()}
    for event in events:
        payload = event["payload"]
        state[payload["task"]] = {key: value for key, value in payload.items() if key != "task"}
    effective = {}

    def resolve(identity):
        if identity in effective:
            return effective[identity]
        item, task = state[identity], tasks[identity]
        status = item["status"]
        if status == "SOLVED" and (not fresh(root, task, item["evidence"])
                or any(resolve(d) != "SOLVED" for d in task["depends"])):
            status = "STALE"
        effective[identity] = status
        return status

    for identity in tasks:
        resolve(identity)
    summaries = []
    ready = []
    for identity, task in tasks.items():
        status = effective[identity]
        waiting = [d for d in task["depends"] if effective[d] != "SOLVED"]
        summaries.append({"id": identity, "status": status, "recorded_status": state[identity]["status"],
                          "waiting_for": waiting, "reason": state[identity]["reason"], "reopen": state[identity]["reopen"]})
        if status in {"OPEN", "STALE"} and not waiting:
            ready.append(task)
    ready.sort(key=lambda task: (task["priority"], task["effort_minutes"], task["id"]))
    running = [item for item in summaries if item["status"] == "RUNNING"]
    selected = tasks[running[0]["id"]] if running else ready[0] if ready else None
    action = None
    if selected:
        identity = selected["id"]
        action = {"task": identity, "title": selected["title"], "status": effective[identity],
                  "action": "continue" if running else "reopen" if effective[identity] == "STALE" else "start",
                  "selection": "Existing running task" if running else "Dependencies satisfied; priority, effort, then ID",
                  "files": selected["files"], "checks": selected["checks"], "acceptance": selected["acceptance"]}
    return {"head": events[-1]["sha256"] if events else GENESIS, "events": len(events),
            "counts": dict(Counter(effective.values())), "tasks": summaries, "next": action}


def append(root, plan, path, payload, request, head):
    if not identifier(request):
        raise Problem("INVALID_REQUEST", "use a stable short request ID")
    tasks = {task["id"]: task for task in plan["tasks"]}
    validate_payload(payload, tasks)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as journal:
        fcntl.flock(journal, fcntl.LOCK_EX)
        journal.seek(0)
        events = decode_history(journal.read(), plan)
        for event in events:
            if event["request"] == request:
                if event["payload"] != payload:
                    raise Problem("REQUEST_CONFLICT", "request ID was used for different content")
                return event
        current = project(root, plan, events)
        if head != current["head"]:
            raise Problem("STALE_HEAD", "another transition occurred; read status and reconsider")
        item = next(t for t in current["tasks"] if t["id"] == payload["task"])
        status = payload["status"]
        if status not in ALLOWED[item["status"]]:
            raise Problem("INVALID_TRANSITION", f"cannot move {item['status']} to {status}")
        if status in {"RUNNING", "SOLVED"} and item["waiting_for"]:
            raise Problem("DEPENDENCIES_OPEN", "dependencies are not currently solved")
        if status == "RUNNING" and current["counts"].get("RUNNING", 0):
            raise Problem("WORK_IN_PROGRESS", "finish or release the running task first")
        if status == "SOLVED" and not fresh(root, tasks[payload["task"]], payload["evidence"]):
            raise Problem("STALE_EVIDENCE", "completion needs successful evidence for current sources")
        body = {"seq": len(events) + 1, "parent": current["head"], "plan": digest(plan),
                "request": request, "payload": payload}
        event = {**body, "sha256": digest(body)}
        journal.seek(0, 2)
        journal.write(canonical(event) + "\n")
        journal.flush()
        os.fsync(journal.fileno())
        return event

"""Strict versioned contracts shared by the control commands."""

import hashlib
import json
import math
from pathlib import Path
import re


class Problem(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    data = value if isinstance(value, bytes) else canonical(value).encode()
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Problem("INVALID_JSON", f"duplicate key: {key}")
        result[key] = value
    return result


def parse(text):
    try:
        return json.loads(text, object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, TypeError) as error:
        raise Problem("INVALID_JSON", str(error)) from error


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise Problem("INVALID_PATH", "expected a repository-relative path")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or ".." in Path(relative).parts:
        raise Problem("INVALID_PATH", f"path escapes repository: {relative}")
    return path


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value) is not None


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {"schema_version", "tasks"} or type(plan["schema_version"]) is not int or plan["schema_version"] != 1:
        raise Problem("INVALID_PLAN", "expected roadmap schema version 1")
    if not isinstance(plan["tasks"], list) or not plan["tasks"]:
        raise Problem("INVALID_PLAN", "tasks must be a nonempty list")
    fields = {"id", "title", "depends", "priority", "effort_minutes", "files", "checks",
              "timeout_seconds", "acceptance", "reopen", "phase"}
    tasks = {}
    for task in plan["tasks"]:
        if not isinstance(task, dict) or set(task) != fields:
            raise Problem("INVALID_PLAN", "task fields differ from the contract")
        if not identifier(task["id"]) or task["id"] in tasks:
            raise Problem("INVALID_PLAN", "invalid or duplicate task ID")
        for name in ("title", "acceptance", "reopen", "phase"):
            if not isinstance(task[name], str) or not task[name].strip():
                raise Problem("INVALID_PLAN", f"{task['id']}: missing {name}")
        for name in ("priority", "effort_minutes", "timeout_seconds"):
            if type(task[name]) not in (int, float) or not math.isfinite(task[name]) or task[name] <= 0:
                raise Problem("INVALID_PLAN", f"{task['id']}: invalid {name}")
        if task["timeout_seconds"] > 120:
            raise Problem("INVALID_PLAN", "command timeout exceeds 120 seconds")
        for name in ("depends", "files"):
            values = task[name]
            if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values) or len(set(values)) != len(values):
                raise Problem("INVALID_PLAN", f"invalid {name}")
        if not task["files"]:
            raise Problem("INVALID_PLAN", "task needs a source scope")
        for file in task["files"]:
            if Path(file).is_absolute() or ".." in Path(file).parts:
                raise Problem("INVALID_PLAN", "source path must stay in repository")
        checks = task["checks"]
        if not isinstance(checks, list) or not checks or any(not isinstance(c, list) or not c or any(not isinstance(a, str) or not a for a in c) for c in checks):
            raise Problem("INVALID_PLAN", "checks must be nonempty argv arrays")
        tasks[task["id"]] = task
    visiting, visited = set(), set()

    def visit(identity):
        if identity not in tasks:
            raise Problem("INVALID_PLAN", f"missing dependency: {identity}")
        if identity in visiting:
            raise Problem("INVALID_PLAN", "dependency cycle")
        if identity in visited:
            return
        visiting.add(identity)
        for dependency in tasks[identity]["depends"]:
            visit(dependency)
        visiting.remove(identity)
        visited.add(identity)

    for identity in tasks:
        visit(identity)
    return plan


def load_plan(root):
    path = Path(root) / "system/roadmap.json"
    return validate_plan(parse(path.read_text()))

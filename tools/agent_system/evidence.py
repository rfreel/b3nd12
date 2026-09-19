"""Retained subprocess results bound to the exact task and source snapshot."""

import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
import time

from .contracts import Problem, canonical, digest, identifier, parse, safe_path

OUTPUT_LIMIT = 131072


def source_hashes(root, task):
    try:
        return {file: digest(safe_path(root, file).read_bytes()) for file in task["files"]}
    except OSError as error:
        raise Problem("MISSING_SOURCE", str(error)) from error


def execute(argv, root, timeout):
    command = [sys.executable if argv[0] == "python3" else argv[0], *argv[1:]]
    start = time.monotonic()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr,
                                   start_new_session=True, env={**os.environ, "BEND_NO_TELEMETRY": "1"})
        timed_out = False
        try:
            while process.poll() is None:
                remaining = timeout - (time.monotonic() - start)
                if remaining <= 0:
                    timed_out = True
                    break
                if any(os.fstat(stream.fileno()).st_size > OUTPUT_LIMIT for stream in (stdout, stderr)):
                    break
                try:
                    process.wait(timeout=min(remaining, 0.02))
                except subprocess.TimeoutExpired:
                    pass
        finally:
            # Kill descendants even if a parent exits before its children.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        sizes = [stream.seek(0, 2) for stream in (stdout, stderr)]
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read(OUTPUT_LIMIT).decode(errors="replace")
        err = stderr.read(OUTPUT_LIMIT).decode(errors="replace")
    empty_suite = "unittest" in argv and "Ran 0 tests" in out + err
    return {"argv": argv, "exit_code": process.returncode, "timed_out": timed_out,
            "seconds": time.monotonic() - start, "stdout": out, "stderr": err,
            "output_bytes": sum(sizes), "truncated": any(s > OUTPUT_LIMIT for s in sizes),
            "passed": process.returncode == 0 and not timed_out and not empty_suite
                      and all(s <= OUTPUT_LIMIT for s in sizes)}


def verify(root, task, run_id):
    if not identifier(run_id):
        raise Problem("INVALID_RUN_ID", "use a short alphanumeric run ID")
    before = source_hashes(root, task)
    relative = f"evidence/agent-system/runs/{run_id}.json"
    path = safe_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".json.pending")
    if path.exists():
        raise Problem("RUN_EXISTS", "run ID already exists; evidence is never overwritten")
    try:
        output = pending.open("x")
    except FileExistsError as error:
        raise Problem("RUN_EXISTS", "run ID already exists; evidence is never overwritten") from error
    with output:
        results = []
        failure = None
        for argv in task["checks"]:
            try:
                results.append(execute(argv, root, task["timeout_seconds"]))
            except OSError as error:
                failure = str(error)
                break
            if not results[-1]["passed"]:
                break
        try:
            after = source_hashes(root, task)
        except Problem as error:
            after, failure = {}, str(error)
        result = {"schema_version": 1, "task": task["id"], "task_sha256": digest(task),
                  "sources": before, "sources_after": after, "checks": results,
                  "python": platform.python_version(), "platform": platform.platform(),
                  "error": failure, "passed": not failure and before == after
                  and len(results) == len(task["checks"]) and all(r["passed"] for r in results)}
        output.write(canonical(result) + "\n")
        output.flush()
        os.fsync(output.fileno())
    try:
        os.link(pending, path)
    except FileExistsError as error:
        raise Problem("RUN_EXISTS", "another result already occupies this run ID") from error
    pending.unlink()
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return {"path": relative, "sha256": digest(path.read_bytes()), "passed": result["passed"]}


def fresh(root, task, reference):
    try:
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256", "passed"} or reference["passed"] is not True:
            return False
        data = safe_path(root, reference["path"]).read_bytes()
        if digest(data) != reference["sha256"]:
            return False
        result = parse(data)
        hashes = source_hashes(root, task)
        return (result["schema_version"] == 1 and result["passed"] is True
                and result["task"] == task["id"] and result["task_sha256"] == digest(task)
                and result["sources"] == result["sources_after"] == hashes
                and len(result["checks"]) == len(task["checks"])
                and all(item["passed"] is True and item["exit_code"] == 0
                        and item["argv"] == argv and item["timed_out"] is False
                        for item, argv in zip(result["checks"], task["checks"])))
    except (OSError, ValueError, KeyError, TypeError):
        return False

"""Small reproducible control workloads. Targets never stand in for data."""

import ast
import copy
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from .contracts import Problem, canonical, digest, identifier, parse
from .state import GENESIS, decode_history, project


def percentile(values, fraction=0.95):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def synthetic_history(plan, count=1000):
    head, records = GENESIS, []
    plan_hash = digest(plan)
    for i in range(count):
        payload = {"task": plan["tasks"][0]["id"], "status": "RUNNING" if i % 2 == 0 else "OPEN",
                   "reason": "synthetic replay workload", "reopen": "", "evidence": None}
        body = {"seq": i + 1, "parent": head, "plan": plan_hash, "request": f"bench-{i}", "payload": payload}
        head = digest(body)
        records.append({**body, "sha256": head})
    return "".join(canonical(event) + "\n" for event in records)


def validate_metrics(registry):
    if not isinstance(registry, dict) or set(registry) != {"schema_version", "metrics"} or type(registry["schema_version"]) is not int or registry["schema_version"] != 1 or not isinstance(registry["metrics"], list) or not registry["metrics"]:
        raise Problem("INVALID_METRICS", "expected metric registry version 1")
    seen = set()
    fields = {"id", "unit", "direction", "scope", "collection", "target_30d", "target_90d"}
    for metric in registry["metrics"]:
        if not isinstance(metric, dict) or set(metric) != fields or not identifier(metric["id"]) or metric["id"] in seen or not isinstance(metric["direction"], str) or metric["direction"] not in {"lower", "higher"}:
            raise Problem("INVALID_METRICS", "invalid metric fields, direction, or duplicate ID")
        if any(not isinstance(metric[name], str) or not metric[name].strip() for name in ("unit", "scope", "collection")):
            raise Problem("INVALID_METRICS", "metric unit, scope, and collection are required")
        seen.add(metric["id"])
        for field in ("target_30d", "target_90d"):
            if type(metric[field]) not in (int, float) or not math.isfinite(metric[field]):
                raise Problem("INVALID_METRICS", "targets must be finite numbers")
    return registry


def benchmark(root, plan, events, state="state/events.jsonl"):
    from .cli import compact
    registry = validate_metrics(parse((root / "system/metrics.json").read_text()))
    workload = synthetic_history(plan)
    replay, select, cold = [], [], []
    for _ in range(7):
        start = time.perf_counter()
        decoded = decode_history(workload, plan)
        replay.append((time.perf_counter() - start) * 1000)
        if len(decoded) != 1000 or decoded[-1]["payload"]["status"] != "OPEN":
            raise Problem("BENCHMARK_FAILED", "replay changed the synthetic workload")
        start = time.perf_counter()
        packet = compact(project(root, plan, events))
        select.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        process = subprocess.run([sys.executable, str(root / "control.py"), "--root", str(root), "--state", state, "status"],
                                 cwd=root, capture_output=True, text=True, timeout=10)
        cold.append((time.perf_counter() - start) * 1000)
        response = parse(process.stdout) if process.returncode == 0 else {}
        expected_head = events[-1]["sha256"] if events else GENESIS
        if response.get("ok") is not True or response.get("result", {}).get("head") != expected_head:
            raise Problem("BENCHMARK_FAILED", "cold-start status did not succeed")
    rejected = 0
    lines = workload.splitlines()
    for index in range(0, 1000, 100):
        changed = list(lines)
        item = parse(changed[index])
        item["payload"]["reason"] = "tampered"
        changed[index] = canonical(item)
        try:
            decode_history("\n".join(changed) + "\n", plan)
        except Problem:
            rejected += 1
    if rejected != 10:
        raise Problem("BENCHMARK_FAILED", "tamper rejection failed")
    replay_again = project(root, plan, copy.deepcopy(events))
    source_paths = [root / "control.py", *sorted((root / "tools/agent_system").glob("*.py"))]
    imports = set()
    for path in source_paths:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module.split(".")[0])
    external = imports - sys.stdlib_module_names - {"tools"}
    values = {"replay_1000_p95_ms": percentile(replay), "status_p95_ms": percentile(select),
              "cold_status_p95_ms": percentile(cold), "status_bytes": len(canonical(packet).encode()),
              "tamper_rejection_rate": rejected / 10,
              "projection_reproducible": int(replay_again == project(root, plan, events)),
              "external_runtime_dependencies": len(external)}
    measurements = {metric["id"]: {"value": values.get(metric["id"]),
                                   "status": "MEASURED" if metric["id"] in values else "UNMEASURED",
                                   "reason": "local control workload" if metric["id"] in values else metric["collection"]}
                    for metric in registry["metrics"]}
    sources = {str(path.relative_to(root)): digest(path.read_bytes()) for path in sorted((root / "tools/agent_system").glob("*.py"))}
    sources["control.py"] = digest((root / "control.py").read_bytes())
    return {"schema_version": 1, "suite": "local-control-v1", "samples": 7,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "state_path": state,
            "state_head": events[-1]["sha256"] if events else GENESIS, "state_events": len(events),
            "workload_sha256": digest(workload.encode()), "registry_sha256": digest(registry),
            "plan_sha256": digest(plan), "sources": sources,
            "environment": {"python": platform.python_version(), "platform": platform.platform(), "cpu_count": os.cpu_count()},
            "raw": {"replay_ms": replay, "status_ms": select, "cold_start_ms": cold,
                    "tamper_cases": 10, "tamper_rejected": rejected},
            "measurements": measurements, "targets": registry["metrics"],
            "scope": "Local control only. No measured model-token, dollar, research-yield, or learning-transfer claims."}

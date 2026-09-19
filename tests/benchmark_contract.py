#!/usr/bin/env python3
"""Exercise a tiny real static-verification benchmark and output boundaries."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks/management.py"
pin = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location("management_benchmark", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
stats = module.summary([{"elapsed_ns": value, "peak_rss_bytes": 100} for value in (1, 2, 3, 4)])
assert (stats["p50_ns"], stats["p95_ns"], stats["p99_ns"]) == (2, 4, 4)
with tempfile.TemporaryDirectory(prefix="b3nd12-benchmark-test-") as temporary:
    directory = Path(temporary)
    output = directory / "results"
    command = [sys.executable, str(SCRIPT), str(pin), "--output", str(output), "--runs", "2", "--warmup", "0"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, (result.stdout, result.stderr, (output / "report.json").read_text())
    report = json.loads((output / "report.json").read_text())
    assert report["schema"] == "b3nd12.management-benchmark.v1"
    assert report["status"] == "complete"
    measured = [row for row in report["attempts"] if row["phase"] == "measurement"]
    assert [row["command_id"] for row in measured] == ["static", "json", "json", "static"]
    assert all(row["exit_code"] == 0 and row["elapsed_ns"] > 0 for row in measured)
    assert all(value["samples"] == 2 for value in report["statistics"].values())
    assert len(report["source_hashes"]["benchmarks/management.py"]) == 64
    assert all(len(identity["sha256"]) == 64 for identity in report["tool_identities"].values())
    assert all("runtime smoke UNAVAILABLE" in row["stdout"] for row in measured if row["command_id"] == "static")
    before = (output / "report.json").read_bytes()
    repeated = subprocess.run(command, capture_output=True, timeout=10)
    assert repeated.returncode == 2
    assert (output / "report.json").read_bytes() == before
    for destination in (ROOT / "benchmark-forbidden", directory / "alias" / "benchmark-forbidden"):
        if destination.parent.name == "alias":
            destination.parent.symlink_to(ROOT, target_is_directory=True)
        denied = subprocess.run([sys.executable, str(SCRIPT), str(pin), "--output", str(destination)], capture_output=True, timeout=10)
        assert denied.returncode == 2 and not destination.exists()
    for value in ("0", "101"):
        invalid = subprocess.run([sys.executable, str(SCRIPT), str(pin), "--output", str(directory / "invalid"), "--runs", value], capture_output=True, timeout=10)
        assert invalid.returncode == 2
print("PASS bounded benchmark: real equivalent static checks, raw observations, identities, alternating order, output boundaries")

#!/usr/bin/env python3
"""Equivalent static-verification observations, with alternating execution order.

Percentiles use nearest rank. These warm-cache process timings include startup.
wait4 RSS includes the child process accounting supplied by the OS, not summed
concurrent process-tree memory. Block counters are physical accounting units,
not logical I/O bytes. No timing result implies an optimization benefit.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def count(text):
    value = int(text)
    if not 1 <= value <= 100:
        raise argparse.ArgumentTypeError("runs must be between 1 and 100")
    return value


def summary(rows):
    values = sorted(row["elapsed_ns"] for row in rows)
    return {"samples": len(values), **{
        f"p{p}_ns": values[math.ceil(len(values) * p / 100) - 1]
        for p in (50, 95, 99)},
        "jobs_per_second": len(values) * 1e9 / sum(values),
        "peak_rss_bytes": max(row["peak_rss_bytes"] for row in rows)}


def observe(command, env, timeout=120):
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        start = time.perf_counter_ns()
        process = subprocess.Popen(command, env=env, stdout=out, stderr=err,
                                   start_new_session=True)
        timed_out = False
        while True:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                break
            if time.perf_counter_ns() - start > timeout * 1e9:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                _, status, usage = os.wait4(process.pid, 0)
                break
            time.sleep(0.002)
        elapsed = time.perf_counter_ns() - start
        process.returncode = os.waitstatus_to_exitcode(status)
        out.seek(0)
        err.seek(0)
        return {"elapsed_ns": elapsed, "exit_code": process.returncode,
                "timed_out": timed_out,
                "stdout": out.read().decode(errors="replace"),
                "stderr": err.read().decode(errors="replace"),
                "peak_rss_bytes": usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024),
                "user_seconds": usage.ru_utime, "system_seconds": usage.ru_stime,
                "input_blocks": usage.ru_inblock, "output_blocks": usage.ru_oublock}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pin_checkout", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runs", type=count, default=10)
    parser.add_argument("--warmup", type=int, choices=range(0, 11), default=1)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("evidence output must be outside the repository")
    if output.exists():
        parser.error("evidence output must not already exist")
    if not hasattr(os, "wait4"):
        parser.error("this benchmark requires POSIX wait4")
    pin = json.loads((ROOT / "upstream.json").read_text())["commit"]
    tools = {}
    for name in ("git", "sh", "dirname", "basename", "mktemp", "rm", "mkdir", "cp"):
        resolved = shutil.which(name)
        if not resolved:
            parser.error("missing prerequisite: " + name)
        tools[name] = str(Path(resolved).resolve())
    tools["python3"] = str(Path(sys.executable).resolve())
    identities = {name: {"path": path, "sha256": digest(Path(path).read_bytes())}
                  for name, path in tools.items()}
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "b3nd12.management-benchmark.v1", "pin": pin,
              "platform": platform.platform(), "python": sys.version,
              "tool_identities": identities, "runs": args.runs, "warmup": args.warmup,
              "method": "alternating pair order; warm filesystem cache; process startup included; nearest-rank percentiles; Bun excluded; completion polled every 2 ms",
              "limits": "Not a cold-cache study or speedup claim. RSS is OS wait4 accounting, not summed tree memory. Physical block counts are not logical bytes.",
              "invocation": sys.argv, "attempts": [], "status": "incomplete"}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    try:
        with tempfile.TemporaryDirectory(prefix="b3nd12-benchmark-") as tmp:
            temp = Path(tmp)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            for name, path in tools.items():
                (bin_dir / name).symlink_to(path)
            env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
            env.update(PATH=str(bin_dir), BEND_NO_TELEMETRY="1",
                       GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")

            def call(command, phase, command_id):
                try:
                    row = observe([str(part) for part in command], env)
                except OSError as exc:
                    row = {"spawn_error": str(exc), "exit_code": None}
                row.update(phase=phase, command_id=command_id, command=[str(p) for p in command],
                           sequence=len(report["attempts"]))
                report["attempts"].append(row)
                save()
                if row["exit_code"] != 0:
                    raise RuntimeError("failed observation: " + command_id)
                return row

            report["source_commit"] = call(["git", "-C", ROOT, "rev-parse", "HEAD"], "identity", "source-head")["stdout"].strip()
            report["source_status"] = call(["git", "-C", ROOT, "status", "--porcelain"], "identity", "source-status")["stdout"]
            tracked = call(["git", "-C", ROOT, "ls-files", "--cached", "--others", "--exclude-standard", "-z"], "identity", "source-files")["stdout"].split("\0")
            report["source_hashes"] = {name: digest((ROOT / name).read_bytes())
                                       for name in tracked if name and (ROOT / name).is_file()}
            report["source_hashes"]["benchmarks/management.py"] = digest(Path(__file__).read_bytes())
            report["git_version"] = call(["git", "--version"], "identity", "git-version")["stdout"].strip()
            target = temp / "bend"
            call(["git", "clone", "--no-local", "--no-checkout", args.pin_checkout.resolve(), target], "setup", "clone")
            call(["git", "-C", target, "checkout", "--detach", pin], "setup", "checkout")
            call(["sh", ROOT / "apply.sh", target], "setup", "install")
            commands = {"static": ["sh", ROOT / "verify.sh", target],
                        "json": ["python3", ROOT / "b3nd12.py", "verify", target, "--json"]}
            reference = {}
            for name, command in commands.items():
                row = call(command, "correctness", name)
                if name == "json":
                    result = json.loads(row["stdout"])
                    if result.get("ok") is not True:
                        raise RuntimeError("JSON verification did not report success")
                elif "exact delivery PASS" not in row["stdout"] or "runtime smoke UNAVAILABLE" not in row["stdout"]:
                    raise RuntimeError("static-only verification was not observed")
                reference[name] = (row["stdout"], row["stderr"])
            for phase, rounds in (("warmup", args.warmup), ("measurement", args.runs)):
                for index in range(rounds):
                    for name in (("static", "json") if index % 2 == 0 else ("json", "static")):
                        row = call(commands[name], phase, name)
                        if (row["stdout"], row["stderr"]) != reference[name]:
                            raise RuntimeError("verification output changed: " + name)
            report["statistics"] = {name: summary([row for row in report["attempts"]
                if row["phase"] == "measurement" and row["command_id"] == name]) for name in commands}
            changed = [name for name, expected in report["source_hashes"].items()
                       if not (ROOT / name).is_file() or digest((ROOT / name).read_bytes()) != expected]
            if changed:
                report["changed_sources"] = changed
                raise RuntimeError("source changed during observations")
            report["status"] = "complete"
    except (OSError, ValueError, RuntimeError) as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
    save()
    print(json.dumps({"status": report["status"], "report": str(output / "report.json")}))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())

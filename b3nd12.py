#!/usr/bin/env python3
"""Management CLI for the pinned B3ND12 delivery, using only Python's standard library."""
import json
import os
import shutil
import re
import subprocess
import sys

from bounded import OutputLimitExceeded, run as bounded_run

from stack import ROOT, PIN, Failure, patch_files, target_check, verify

QUICK = """B3ND12 installs an ordered agent-ergonomics patch stack onto Bend 2.0.9.

  python3 b3nd12.py doctor                 inspect local prerequisites
  python3 b3nd12.py apply /path/to/bend     install into a clean pinned checkout
  python3 b3nd12.py verify /path/to/bend    check installed bytes and theory
  python3 b3nd12.py guide program          read the compact programming pack
  python3 b3nd12.py guide prove            read the compact proof pack

Piped output defaults to JSON. Add --human for readable text or --json for a
versioned result. Apply requires the exact revision in upstream.json and refuses
existing changes. It does not clone, reset, commit, or push the target. Run doctor
first; use --help for commands, errors, and compatibility details.
"""
HELP = QUICK + """
Commands: doctor; apply TARGET; verify TARGET; guide [router|program|prove];
          task implement|prove|diagnose; help.
Global flags: --json, --human, --help. Version command: --version.
Use -- before a literal path.
Read-only aliases: check = verify; status = doctor; -h = help; -v = --version.
Read-only command names ignore case and '-'/'_' separators. Apply is exact.
Exit codes: 0 success, 1 missing resource, 2 invalid/ambiguous arguments,
3 configuration, 4 external operation failure, 5 internal/invariant failure.
JSON schema: spec/cli-v1.schema.json. Bend's existing --json is unchanged.
"""


def parse(raw):
    own, tail = raw, []
    if "--" in raw:
        at = raw.index("--")
        own, tail = raw[:at], raw[at+1:]
    fmt = [x for x in own if x in ("--json", "--human")]
    if len(set(fmt)) > 1:
        raise Failure("AMBIGUOUS_FORMAT", "Choose one output format.", "Use --json or --human.", 2)
    machine = "--json" in fmt or ("--human" not in fmt and not sys.stdout.isatty())
    args = [x for x in own if x not in ("--json", "--human")]
    if any(x in ("--help", "-h") for x in args):
        return "help", [], machine, ["help"], True
    if not args:
        if tail:
            raise Failure("INVALID_ARGUMENTS", "A command is required before --.", "Use apply or verify before the target.", 2)
        return "quick", [], machine, [], False
    command = args[0]
    aliases = {"check": "verify", "verify": "verify", "doctor": "doctor", "status": "doctor",
               "guide": "guide", "task": "task", "help": "help", "--help": "help", "-h": "help",
               "--version": "version", "-v": "version", "version": "version"}
    normalized = command.lower().replace("_", "").replace("-", "")
    canonical = aliases.get(command, aliases.get(normalized, command))
    if command == "apply":
        canonical = "apply"
    if canonical not in ("apply", "verify", "doctor", "guide", "task", "help", "version"):
        raise Failure("INVALID_COMMAND", "Unknown or noncanonical command: " + command,
                      "Use help; mutating commands require the exact spelling apply.", 2)
    values = args[1:] + tail
    if any(x.startswith("-") for x in args[1:]):
        raise Failure("INVALID_ARGUMENTS", "Unknown option.", "Use -- before a literal path beginning with a dash.", 2)
    if canonical == "task" and len(values) != 1:
        raise Failure("INVALID_ARGUMENTS", "task requires one task name.", "Use task implement, task prove, or task diagnose.", 2)
    if canonical in ("apply", "verify") and len(values) != 1:
        raise Failure("INVALID_ARGUMENTS", canonical + " requires one target.", "Use " + canonical + " /path/to/bend.", 2)
    if canonical in ("doctor", "help", "version") and values:
        raise Failure("INVALID_ARGUMENTS", canonical + " takes no arguments.", "Remove the extra arguments.", 2)
    if canonical == "guide" and len(values) > 1:
        raise Failure("INVALID_ARGUMENTS", "guide takes one optional route.", "Use guide program or guide prove.", 2)
    return canonical, values, machine, [canonical, *values], canonical != command


def probe_tool(name, path):
    """Operational probes are readiness evidence, not executable authentication."""
    if path is None:
        return {"status": "missing", "detail": "Executable was not found on PATH."}
    args = {"git": ["--version"], "sh": ["-c", "printf b3nd12-shell-ready"],
            "bun": ["-e", 'console.log("b3nd12-bun-ready:" + Bun.version)']}[name]
    try:
        ran = bounded_run([path, *args], capture_output=True, text=True, timeout=2, max_output_bytes=65536)
    except OutputLimitExceeded as exc:
        return {"status": "broken", "detail": "Probe exceeded output limit of " + str(exc.limit_bytes) + " bytes."}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "detail": "Probe exceeded two seconds."}
    except OSError as exc:
        return {"status": "broken", "detail": str(exc)}
    if ran.returncode:
        return {"status": "broken", "detail": "Probe exited with status " + str(ran.returncode)}
    output = ran.stdout.strip()
    valid = {"git": bool(re.fullmatch(r"git version [0-9]+\.[0-9]+(?:\.[^\s]+)?(?: .*)?", output)),
             "sh": output == "b3nd12-shell-ready",
             "bun": bool(re.fullmatch(r"b3nd12-bun-ready:1\.[0-9]+\.[0-9]+(?:[-+].*)?", output))}[name]
    return {"status": "usable" if valid and not ran.stderr else "incompatible",
            "detail": output[:200] or "Probe produced no output."}


def execute(command, values):
    if command in ("quick", "help"):
        return {"text": QUICK if command == "quick" else HELP}
    if command == "version":
        return {"version": "1", "bend_version": "2.0.9", "pin": PIN}
    if command == "guide":
        name = values[0] if values else "router"
        if name not in ("router", "program", "prove"):
            raise Failure("NOT_FOUND", "Unknown guide route: " + name, "Use router, program, or prove.", 1)
        return {"route": name, "text": (ROOT / "guide/agent" / (name.upper()+".md")).read_text()}
    if command == "task":
        from accretion.environment import resolve, TASKS
        if values[0] not in TASKS:
            raise Failure("INVALID_TASK", "Unknown task: " + values[0],
                          "Use task implement, task prove, or task diagnose.", 2)
        try:
            result = resolve(values[0], ROOT / "accretion/routes.json")
            expected = (ROOT / "guide/agent" / TASKS[values[0]]).read_text()
            if result["text"] != expected:
                raise ValueError("accepted route returns the wrong task content")
            return result
        except (ValueError, OSError) as exc:
            raise Failure("ROUTING_CONFIGURATION", str(exc),
                          "Restore accretion/routes.json and its declared guide files from the accepted revision.", 3)
    if command == "doctor":
        tools = {name: shutil.which(name) for name in ("git", "sh", "bun")}
        patch_files()
        probes = {name: probe_tool(name, path) for name, path in tools.items()}
        if any(probes[name]["status"] != "usable" for name in ("git", "sh")):
            missing = any(tools[name] is None for name in ("git", "sh"))
            raise Failure("MISSING_TOOL" if missing else "BROKEN_TOOL",
                          "Git and a working POSIX shell are required.",
                          "Install or repair the prerequisites shown in probes.", 3,
                          tools=tools, probes=probes)
        return {"pin": PIN, "tools": tools, "patches": 9, "probes": probes,
                "runtime_checks": "available" if probes["bun"]["status"] == "usable" else "unavailable"}
    target = target_check(values[0], clean=command == "apply")
    patch_files()
    if command == "apply":
        try:
            ran = bounded_run([str(ROOT / "apply.sh"), str(target)], capture_output=True, text=True, timeout=90)
        except OutputLimitExceeded as exc:
            raise Failure("INSTALL_OUTPUT_LIMIT", "Installation exceeded its output limit.",
                          "Preserve the target and inspect truncated diagnostics before retrying.", 4,
                          stdout=exc.stdout or "", stderr=exc.stderr or "", target=str(target),
                          limit_bytes=exc.limit_bytes, observed_bytes=exc.observed_bytes)
        except subprocess.TimeoutExpired as exc:
            raise Failure("INSTALL_TIMEOUT", "Installation exceeded 90 seconds.",
                          "Preserve the target and inspect partial installation diagnostics before retrying.", 4,
                          stdout=exc.stdout or "", stderr=exc.stderr or "", target=str(target))
        if ran.returncode:
            raise Failure("INSTALL_FAILED", "Patch installation or verification failed.",
                          "Inspect the diagnostics; preserve the target for investigation.", 5,
                          stdout=ran.stdout, stderr=ran.stderr, target=str(target))
        result = verify(target)
        result["log"] = ran.stdout
    else:
        result = verify(target)
    result["target"] = str(target)
    return result


def main():
    raw = sys.argv[1:]
    own = raw[:raw.index("--")] if "--" in raw else raw
    machine = "--json" in own or ("--human" not in own and not sys.stdout.isatty())
    canonical, corrected = None, False
    try:
        command, values, machine, canonical, corrected = parse(raw)
        result, error, status = execute(command, values), None, 0
    except Failure as exc:
        result, error, status = None, exc.error, exc.status
    except (OSError, ValueError) as exc:
        result, error, status = None, Failure("CONFIGURATION", str(exc), "Check dependencies, permissions, and repository files.", 3).error, 3
    except Exception as exc:
        result, error, status = None, Failure("INTERNAL", str(exc), "Report the invocation and traceback context.").error, 5
    envelope = dict(schema="b3nd12.cli.v1", ok=status == 0, command=canonical,
                    corrected=corrected, result=result, error=error, exit_code=status)
    if machine:
        print(json.dumps(envelope))
    elif error:
        print(error["code"] + ": " + error["message"] + "\n" + error["correction"], file=sys.stderr)
    else:
        if corrected:
            print("accepted: " + json.dumps(canonical), file=sys.stderr)
        print(result.get("text", json.dumps(result, indent=2)), end="" if "text" in result else "\n")
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(0)

#!/usr/bin/env python3
"""Management CLI for the pinned B3ND12 delivery, using only Python's standard library."""
import json
import os
import shutil
import subprocess
import sys

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
Commands: doctor; apply TARGET; verify TARGET; guide [router|program|prove]; help.
Global flags: --json, --human, --help, --version. Use -- before a literal path.
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
    if not args:
        if tail:
            raise Failure("INVALID_ARGUMENTS", "A command is required before --.", "Use apply or verify before the target.", 2)
        return "quick", [], machine, [], False
    command = args[0]
    aliases = {"check": "verify", "verify": "verify", "doctor": "doctor", "status": "doctor",
               "guide": "guide", "help": "help", "--help": "help", "-h": "help",
               "--version": "version", "-v": "version", "version": "version"}
    normalized = command.lower().replace("_", "").replace("-", "")
    canonical = aliases.get(command, aliases.get(normalized, command))
    if command == "apply":
        canonical = "apply"
    if canonical not in ("apply", "verify", "doctor", "guide", "help", "version"):
        raise Failure("INVALID_COMMAND", "Unknown or noncanonical command: " + command,
                      "Use help; mutating commands require the exact spelling apply.", 2)
    values = args[1:] + tail
    if any(x.startswith("-") for x in args[1:]):
        raise Failure("INVALID_ARGUMENTS", "Unknown option.", "Use -- before a literal path beginning with a dash.", 2)
    if canonical in ("apply", "verify") and len(values) != 1:
        raise Failure("INVALID_ARGUMENTS", canonical + " requires one target.", "Use " + canonical + " /path/to/bend.", 2)
    if canonical in ("doctor", "help", "version") and values:
        raise Failure("INVALID_ARGUMENTS", canonical + " takes no arguments.", "Remove the extra arguments.", 2)
    if canonical == "guide" and len(values) > 1:
        raise Failure("INVALID_ARGUMENTS", "guide takes one optional route.", "Use guide program or guide prove.", 2)
    return canonical, values, machine, [canonical, *values], canonical != command


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
    if command == "doctor":
        tools = {name: shutil.which(name) for name in ("git", "sh", "bun")}
        patch_files()
        if not tools["git"] or not tools["sh"]:
            raise Failure("MISSING_TOOL", "Git and a POSIX shell are required.", "Install the missing prerequisites.", 3, tools=tools)
        return {"pin": PIN, "tools": tools, "patches": 9,
                "runtime_checks": "available" if tools["bun"] else "unavailable"}
    target = target_check(values[0], clean=command == "apply")
    patch_files()
    if command == "apply":
        ran = subprocess.run([str(ROOT / "apply.sh"), str(target)], capture_output=True, text=True)
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

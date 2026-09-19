#!/usr/bin/env python3
"""Subprocess contracts, including a real PTY and disposable pinned checkouts."""
import json
import os
from pathlib import Path
import pty
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stack import PIN


def run(*args, status=0, env=None):
    got = subprocess.run([sys.executable, str(ROOT / "b3nd12.py"), *args],
                         capture_output=True, text=True, env=env)
    assert got.returncode == status, (args, got.returncode, got.stdout, got.stderr)
    return got


def check(*args, status=0, code=None):
    got = run(*args, status=status)
    assert got.stderr == "", got.stderr
    doc = json.loads(got.stdout)
    assert set(doc) == {"schema", "ok", "command", "corrected", "result", "error", "exit_code"}
    schema = json.loads((ROOT / "spec/cli-v1.schema.json").read_text())
    assert set(doc) == set(schema["required"])
    assert doc["schema"] == schema["properties"]["schema"]["const"]
    assert doc["exit_code"] == status
    assert doc["ok"] == (status == 0)
    if code:
        assert doc["error"]["code"] == code, doc
        assert set(doc["error"]) == {"code", "message", "context", "correction", "examples"}
        assert doc["error"]["message"] and doc["error"]["correction"]
    else:
        assert doc["error"] is None
        assert isinstance(doc["result"], dict)
    return doc


def main():
    check()
    for args in [("doctor",), ("help",), ("--version",), ("guide",),
                 ("guide", "program"), ("guide", "prove"), ("task", "implement"),
                 ("task", "prove"), ("task", "diagnose")]:
        check(*args)
        check(*args, "--json")
        assert not run(*args, "--human").stdout.startswith('{"schema"')
    check("task", "unknown", status=2, code="INVALID_TASK")
    check("task", status=2, code="INVALID_ARGUMENTS")
    assert check("StAtUs")["command"] == ["doctor"]
    absent = run("doctor", "--json", status=3, env={**os.environ, "PATH": "/nonexistent"})
    assert json.loads(absent.stdout)["error"]["code"] == "MISSING_TOOL"
    assert check("ver_ify", "/no-such-bend", status=1, code="NOT_FOUND")["corrected"]
    for args in [("Apply", "/x"), ("apply",), ("check",), ("doctor", "extra"),
                 ("guide", "program", "prove"), ("--", "/x"), ("help", "--oops")]:
        check(*args, status=2, code="INVALID_COMMAND" if args[0] == "Apply" else "INVALID_ARGUMENTS")
    check("doctor", "--json", "--human", status=2, code="AMBIGUOUS_FORMAT")
    check("guide", "unknown", status=1, code="NOT_FOUND")
    check("verify", "--", "--json", status=1, code="NOT_FOUND")
    human = run("guide", "unknown", "--human", status=1)
    assert human.stdout == "" and "NOT_FOUND" in human.stderr
    words = run("--human").stdout.split()
    assert 70 <= len(words) <= 140
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen([sys.executable, str(ROOT / "b3nd12.py")], stdout=slave, stderr=subprocess.PIPE)
        os.close(slave)
        out = b""
        while True:
            try:
                block = os.read(master, 65536)
                if not block: break
                out += block
            except OSError: break
        assert proc.wait() == 0 and out.startswith(b"B3ND12 installs")
    finally:
        os.close(master)
    with tempfile.TemporaryDirectory(prefix="b3nd12-cli-") as directory:
        target = Path(directory) / "checkout with spaces"
        subprocess.run(["git", "clone", "--shared", "--no-checkout", str(Path(sys.argv[1]).resolve()), str(target)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(target), "checkout", "--detach", PIN], check=True, capture_output=True)
        check("verify", str(target), status=5, code="FILE_SCOPE")
        doc = check("apply", str(target))
        assert doc["result"]["files"] == 25 and doc["result"]["theory_unchanged"]
        check("verify", str(target))
        check("apply", str(target), status=3, code="DIRTY_TARGET")
        check("verify", str(target / "guide"), status=2, code="INVALID_TARGET")
        source = target / "bend2/main.ts"
        old = source.read_bytes()
        source.write_bytes(old + b"\n// changed\n")
        check("verify", str(target), status=5, code="CONTENT_MISMATCH")
        source.write_bytes(old)
        subprocess.run(["git", "-C", str(target), "config", "core.filemode", "false"], check=True)
        source.chmod(source.stat().st_mode & ~0o111)
        check("verify", str(target), status=5, code="FILE_MODE")
        source.chmod(source.stat().st_mode | 0o111)
        kernel = target / "bend2/bend.ts"
        original = kernel.read_bytes()
        kernel.write_bytes(original + b"\n")
        subprocess.run(["git", "-C", str(target), "add", "bend2/bend.ts"], check=True)
        kernel.write_bytes(original)
        check("verify", str(target), status=5, code="THEORY_CHANGED")
    print("PASS CLI contracts, real PTY, install/verify, tamper and staged-theory refusal")


if __name__ == "__main__":
    main()

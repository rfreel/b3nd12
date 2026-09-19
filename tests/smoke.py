#!/usr/bin/env python3
"""Keep static delivery evidence distinguishable from runtime readiness."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='b3nd12-smoke-') as tmp:
    directory = Path(tmp)
    target = directory / 'bend'
    subprocess.run(['git', 'clone', '--no-local', str(Path(sys.argv[1]).resolve()), str(target)],
                   check=True, capture_output=True)
    # Build a tool path without Bun, independent of the invoking shell's PATH.
    tools = directory / 'tools'
    tools.mkdir()
    for name in ('git', 'sh', 'python3', 'dirname', 'mktemp', 'mkdir', 'cp', 'rm', 'basename'):
        found = shutil.which(name)
        assert found, name
        (tools / name).symlink_to(found)
    env = {**os.environ, 'PATH': str(tools)}
    installed = subprocess.run([str(ROOT / 'apply.sh'), str(target)], env=env,
                               capture_output=True, text=True, timeout=90)
    assert installed.returncode == 0, installed.stderr
    assert 'exact delivery PASS' in installed.stdout and 'runtime smoke UNAVAILABLE' in installed.stdout
    fake = tools / 'bun'
    fake.write_text('#!/bin/sh\nexit 7\n')
    fake.chmod(0o755)
    failed = subprocess.run([str(ROOT / 'verify.sh'), str(target)], env=env,
                            capture_output=True, text=True, timeout=30)
    assert failed.returncode == 1 and 'runtime smoke FAILED' in failed.stderr
    assert 'exact delivery PASS' in failed.stdout and 'runtime smoke PASS' not in failed.stdout
    fake.unlink()
    fake.symlink_to(Path(sys.argv[2]).resolve())
    passed = subprocess.run([str(ROOT / 'verify.sh'), str(target)], env=env,
                            capture_output=True, text=True, timeout=60)
    assert passed.returncode == 0, passed.stderr
    assert 'exact delivery PASS' in passed.stdout and 'runtime smoke PASS' in passed.stdout
print('PASS static parity with missing, failed and real Bun smoke execution')

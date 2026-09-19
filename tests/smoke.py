#!/usr/bin/env python3
"""Keep static delivery evidence distinguishable from runtime readiness."""
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from b3nd12 import installation_status, RUNTIME_PASS, RUNTIME_UNAVAILABLE, RUNTIME_FAILED
from cli_schema import validate

for marker, expected in ((RUNTIME_PASS, 'pass'), (RUNTIME_UNAVAILABLE, 'unavailable')):
    assert installation_status(marker + '\napply: ranked deepenings installed\n', '', True) == expected
    for altered in (marker + ' extra', 'prefix ' + marker, marker.lower()):
        assert installation_status(altered + '\napply: ranked deepenings installed\n', '', True) == 'unknown'
assert installation_status('', RUNTIME_FAILED + '\n', False) == 'failed'
assert installation_status('', RUNTIME_FAILED + '\nextra\n', False) == 'unknown'
assert installation_status('', RUNTIME_FAILED + '\n', True) == 'unknown'

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
    def manager(command, checkout, status):
        result = subprocess.run([sys.executable, str(ROOT / 'b3nd12.py'), command,
                                 str(checkout), '--json'], env=env,
                                capture_output=True, text=True, timeout=90)
        assert result.returncode == status and result.stderr == '', result
        doc = json.loads(result.stdout)
        validate(doc)
        return doc

    static = manager('verify', target, 0)['result']
    assert static['static_status'] == 'pass' and static['runtime_status'] == 'not_run'
    def fresh(name):
        checkout = directory / name
        subprocess.run(['git', 'clone', '--no-local', str(Path(sys.argv[1]).resolve()), str(checkout)],
                       check=True, capture_output=True)
        return checkout
    absent = manager('apply', fresh('absent'), 0)['result']
    assert absent['static_status'] == 'pass' and absent['runtime_status'] == 'unavailable'
    fake = tools / 'bun'
    fake.write_text('#!/bin/sh\nexit 7\n')
    fake.chmod(0o755)
    failed = subprocess.run([str(ROOT / 'verify.sh'), str(target)], env=env,
                            capture_output=True, text=True, timeout=30)
    assert failed.returncode == 1 and 'runtime smoke FAILED' in failed.stderr
    assert 'exact delivery PASS' in failed.stdout and 'runtime smoke PASS' not in failed.stdout
    failure = manager('apply', fresh('failed'), 5)['error']
    assert failure['code'] == 'INSTALL_FAILED'
    assert failure['context']['static_status'] == 'pass'
    assert failure['context']['runtime_status'] == 'failed'
    fake.write_text('#!' + sys.executable + '\nimport time\ntime.sleep(120)\n')
    started = time.monotonic()
    hung = subprocess.run([str(ROOT / 'verify.sh'), str(target)], env=env,
                          capture_output=True, text=True, timeout=30)
    elapsed = time.monotonic() - started
    assert hung.returncode == 1 and 'runtime smoke FAILED' in hung.stderr
    assert 'exact delivery PASS' in hung.stdout and 'runtime smoke PASS' not in hung.stdout
    assert 14 <= elapsed < 30, elapsed
    timed_out = manager('apply', fresh('hung'), 5)['error']['context']
    assert timed_out['static_status'] == 'pass' and timed_out['runtime_status'] == 'failed'
    static = manager('verify', target, 0)['result']
    assert static['runtime_status'] == 'not_run'
    fake.unlink()
    fake.symlink_to(Path(sys.argv[2]).resolve())
    passed = subprocess.run([str(ROOT / 'verify.sh'), str(target)], env=env,
                            capture_output=True, text=True, timeout=60)
    assert passed.returncode == 0, passed.stderr
    assert 'exact delivery PASS' in passed.stdout and 'runtime smoke PASS' in passed.stdout
    runtime = manager('apply', fresh('passed'), 0)['result']
    assert runtime['static_status'] == 'pass' and runtime['runtime_status'] == 'pass'
print('PASS static parity with missing, failed, hung and real Bun smoke execution')

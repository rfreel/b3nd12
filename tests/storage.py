#!/usr/bin/env python3
"""Kill evidence writers at publication boundaries and inject filesystem faults."""
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
import storage
from program import replay, sha

bend, bun = (Path(p).resolve() for p in sys.argv[1:3])
seal = sha((ROOT / 'accretion/TODO.json').read_bytes())
original_write = storage.write
routes = (ROOT / 'accretion/routes.json').read_bytes()


def terminal(directory):
    ledger = directory / 'ledger.jsonl'
    if not ledger.exists():
        return '0' * 64
    rows = [json.loads(line) for line in ledger.read_text().splitlines()]
    return rows[-1]['sha256'] if rows else '0' * 64


def fresh_verify(directory):
    return subprocess.run([sys.executable, str(ROOT / 'accretion/verify_evidence.py'),
                           str(directory), '--contract-sha256', seal,
                           '--terminal-sha256', terminal(directory)],
                          capture_output=True, text=True, timeout=15)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    trace = []
    def recording(path, data):
        trace.append(str(path.relative_to(root / 'golden')))
        return original_write(path, data)
    with patch('storage.write', side_effect=recording):
        replay(root / 'golden', seal, bun, bend)
    assert fresh_verify(root / 'golden').returncode == 0
    assert trace[-1] == 'summary.json'
    # Each child uses the actual checker. SIGKILL bypasses Python cleanup.
    # Killing before each atomic publication covers every prior complete prefix.
    for boundary in range(1, len(trace) + 2):
        directory = root / f'killed-{boundary}'
        child = os.fork()
        if child == 0:
            calls = [0]
            def killed_write(path, data):
                calls[0] += 1
                if calls[0] == boundary:
                    os.kill(os.getpid(), signal.SIGKILL)
                return original_write(path, data)
            with patch('storage.write', side_effect=killed_write):
                replay(directory, seal, bun, bend)
            os.kill(os.getpid(), signal.SIGKILL)
        _, status = os.waitpid(child, 0)
        assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
        result = fresh_verify(directory)
        if boundary < len(trace):
            assert result.returncode != 0, (boundary, trace[boundary-1], result.stdout)
            assert not (directory / 'summary.json').exists()
            assert json.loads(result.stdout)['status'] == 'incomplete', result.stdout
        else:
            # A durable terminal event commits the run even if the summary
            # projection has not been published when the process dies.
            assert result.returncode == 0, result.stdout
            assert json.loads(result.stdout)['status'] == 'complete'
    # Precommit faults cannot establish completion. After the terminal event,
    # a summary write failure cannot erase the already committed evidence.
    for filename in ('receipt.json', 'final.json', 'summary.json'):
        for kind in ('full', 'permission', 'zero'):
            directory = root / f'{filename}-{kind}'
            def failing_write(path, data):
                if path.name != filename:
                    return original_write(path, data)
                if kind == 'zero':
                    with patch('storage.os.write', return_value=0):
                        return original_write(path, data)
                error = OSError(errno.ENOSPC, 'disk full') if kind == 'full' else PermissionError(errno.EACCES, 'denied')
                with patch('storage.os.write', side_effect=error):
                    return original_write(path, data)
            try:
                with patch('storage.write', side_effect=failing_write):
                    replay(directory, seal, bun, bend)
            except OSError:
                pass
            else:
                raise AssertionError('injected write failure ignored')
            assert not (directory / 'summary.json').exists()
            result = fresh_verify(directory)
            assert (result.returncode == 0) == (filename == 'summary.json'), result.stdout
    # Atomic replacement preserves the previous file on fsync/rename failures.
    target = root / 'atomic'
    target.write_bytes(b'old')
    for operation in ('fsync', 'replace'):
        try:
            with patch('storage.os.' + operation, side_effect=OSError(errno.EIO, 'injected')):
                original_write(target, b'new')
        except OSError:
            pass
        else:
            raise AssertionError('publication failure ignored')
        assert target.read_bytes() == b'old'
        assert not list(root.glob('.atomic-*'))
    # Positive partial writes are retried until every byte is durable.
    real_write = os.write
    with patch('storage.os.write', side_effect=lambda fd, data: real_write(fd, data[:2])):
        original_write(target, b'complete')
    assert target.read_bytes() == b'complete'
assert (ROOT / 'accretion/routes.json').read_bytes() == routes
print(f'PASS {len(trace)+1} real-process crash boundaries; disk-full, permission, short-write, fsync and rename faults; unchanged routes')

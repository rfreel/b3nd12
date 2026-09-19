#!/usr/bin/env python3
"""Separate actual law refusal from bounded checker transport failures."""
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from run import admit, rounds

bend, bun = (Path(p).resolve() for p in sys.argv[1:3])
with tempfile.TemporaryDirectory() as temp:
    workspace = Path(temp)
    refused = admit(b'{}', b'{}', bun, bend, workspace)
    assert refused['checker']['status'] == 'refused'
    accepted = admit(b'{}', b'{"prove":"PROVE.md"}', bun, bend, workspace)
    assert accepted['checker']['status'] == 'accepted'
    cases = [
        ('missing_certificate', subprocess.CompletedProcess([], 0, '', '')),
        ('malformed_certificate', subprocess.CompletedProcess([], 0, 'All terms check.\nextra', '')),
        ('malformed_certificate', subprocess.CompletedProcess([], 0, 'All terms check.\n', 'warning')),
        ('crash', subprocess.CompletedProcess([], -9, 'partial', 'signal')),
        ('process_error', subprocess.CompletedProcess([], 1, '', 'unrelated error')),
        ('process_error', subprocess.CompletedProcess([], 2, '', refused['checker']['stderr'])),
        ('timeout', subprocess.TimeoutExpired(['checker'], 15, output=b'partial', stderr=b'waiting')),
        ('spawn_error', FileNotFoundError('missing executable')),
    ]
    for status, result in cases:
        kwargs = {'side_effect': result} if isinstance(result, Exception) else {'return_value': result}
        with patch('run.bounded.run', **kwargs):
            sample = admit(b'{}', b'{"prove":"PROVE.md"}', bun, bend, workspace)
        checker = sample['checker']
        assert not sample['accepted'] and checker['status'] == status, checker
        assert checker['stage'] == 'checker' and checker['command'][0] == str(bun)
        if status in ('timeout', 'crash'):
            assert checker['stdout'] == 'partial' and checker['stderr']
        if status == 'timeout':
            assert checker['exit'] is None and checker['timeout_seconds'] == 15
        if status == 'spawn_error':
            assert checker['exit'] is None and 'missing executable' in checker['error']
    # Refusal controls fail closed before any demonstration promotion.
    routes = (ROOT / 'accretion/routes.json').read_bytes()
    for status in ('timeout', 'spawn_error', 'crash', 'missing_certificate', 'malformed_certificate'):
        with patch('run.check_book', return_value={'status': status}):
            try:
                rounds(bun, bend)
            except ValueError as exc:
                assert 'no-gain control' in str(exc)
            else:
                raise AssertionError('broken checker passed refusal control: ' + status)
    assert (ROOT / 'accretion/routes.json').read_bytes() == routes
print('PASS actual acceptance/refusal and preserved crash, timeout, spawn, missing/malformed certificate evidence')

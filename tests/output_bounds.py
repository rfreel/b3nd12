#!/usr/bin/env python3
"""Bound noisy subprocess evidence and oversized candidate/artifact writes."""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from program import replay, sha
from run import admit, check_book
from verify_evidence import inspect_evidence
import storage

bend, bun = (Path(p).resolve() for p in sys.argv[1:3])
seal = sha((ROOT / 'accretion/TODO.json').read_bytes())
noise_command = [sys.executable, '-c',
                 'import os\nwhile True: os.write(1, b"X" * 65536)']
noise = check_book(noise_command)
assert noise['status'] == 'output_limit', noise
assert noise['exit'] is None and noise['observed_bytes'] > noise['limit_bytes']
assert len(noise['stdout'].encode()) + len(noise['stderr'].encode()) <= noise['limit_bytes']
assert noise['command'] == noise_command and noise['stage'] == 'checker'
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    # The direct API cannot bypass the CLI's capped candidate read.
    for raw in (b' ' * 4098, b' ' * (1024 * 1024), 'not bytes'):
        directory = root / ('oversize-' + str(len(raw)))
        try:
            replay(directory, seal, bun, bend, [raw])
        except ValueError as exc:
            assert 'candidate buffer' in str(exc)
        else:
            raise AssertionError('oversized candidate API input accepted')
        assert not list(directory.glob('pass-*'))
        assert not (directory / 'summary.json').exists()
    # The one-byte oversize sentinel is retained exactly and rejected by schema.
    sentinel = b' ' * 4097
    summary = replay(root / 'sentinel', seal, bun, bend, [sentinel])
    assert summary['completed'] == []
    assert (root / 'sentinel/pass-001/candidate.json').read_bytes() == sentinel
    receipt = json.loads((root / 'sentinel/pass-001/receipt.json').read_text())
    assert receipt['verdict'] == 'REJECTED'
    # Exercise actual ASCII and non-UTF8 output before injecting those observed
    # process results into the replay. Three JSON-escaped samples must fit.
    binary_command = [sys.executable, '-c',
                      'import os\nwhile True: os.write(1, bytes([255]) * 65536)']
    for label, observed in [('noise', noise), ('binary-noise', check_book(binary_command))]:
        assert observed['status'] == 'output_limit'
        calls = [0]
        def noisy_trial(*args):
            calls[0] += 1
            if calls[0] == 1:
                return admit(*args)
            with patch('run.check_book', return_value=observed):
                return admit(*args)
        with patch('program.admit', side_effect=noisy_trial):
            summary = replay(root / label, seal, bun, bend, [b'{"prove":"PROVE.md"}'])
        assert summary['stop'] == 'unresolved' and summary['completed'] == []
        raw = (root / label / 'pass-001/receipt.json').read_bytes()
        assert len(raw) <= storage.MAX_ARTIFACT_BYTES
        receipt = json.loads(raw)
        assert receipt['verdict'] == 'UNKNOWN'
        assert all(s['checker']['status'] == 'output_limit' for s in receipt['samples'])
        terminal = json.loads((root / label / 'ledger.jsonl').read_text().splitlines()[-1])['sha256']
        verified = inspect_evidence(root / label, terminal, seal)
        assert verified['status'] == 'complete' and verified['summary']['stop'] == 'unresolved', verified
    # A refused artifact creates neither a file nor a temporary file.
    file = root / 'too-large.json'
    try:
        storage.write(file, b'X' * (storage.MAX_ARTIFACT_BYTES + 1))
    except ValueError as exc:
        assert '8 MiB' in str(exc)
    else:
        raise AssertionError('artifact size limit bypassed')
    assert not file.exists() and not list(root.glob('.too-large.json-*'))
print('PASS real noisy subprocess limit, durable UNKNOWN receipt, candidate API cap, exact oversize sentinel, artifact cap')

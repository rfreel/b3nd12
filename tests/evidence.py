#!/usr/bin/env python3
"""Independent evidence reconstruction and adversarial artifact checks."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from program import replay
import program
from unittest.mock import patch
from verify_evidence import encode, sha, verify

bend, bun = (Path(p).resolve() for p in sys.argv[1:3])
seal = sha((ROOT / 'accretion/TODO.json').read_bytes())


def rows(path):
    return [json.loads(s) for s in (path / 'ledger.jsonl').read_text().splitlines()]


def rehash(path, records):
    previous = None
    for i, row in enumerate(records):
        row['sequence'], row['previous'] = i, previous
        row.pop('sha256', None)
        row['sha256'] = sha(encode(row))
        previous = row['sha256']
    (path / 'ledger.jsonl').write_bytes(b''.join(encode(row).replace(b'\n', b'') + b'\n' for row in records))
    return previous


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    original = root / 'original'
    summary = replay(original, seal, bun, bend)
    terminal = rows(original)[-1]['sha256']
    assert verify(original, terminal, seal) == summary
    command = [sys.executable, str(ROOT / 'accretion/verify_evidence.py'), str(original),
               '--terminal-sha256', terminal, '--contract-sha256', seal]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0 and json.loads(result.stdout)['verified']
    (original / 'summary.json').unlink()
    assert verify(original, terminal, seal) == summary

    def reject(label, mutation, forged=False):
        target = root / label
        shutil.copytree(original, target)
        mutation(target)
        retained = rows(target)[-1]['sha256'] if forged else terminal
        try:
            verify(target, retained, seal)
        except (ValueError, KeyError, OSError, TypeError):
            pass
        else:
            raise AssertionError('accepted tampering: ' + label)

    reject('candidate', lambda p: (p / 'pass-001/candidate.json').write_bytes(b'{}'))
    reject('deleted', lambda p: (p / 'pass-002/receipt.json').unlink())
    reject('snapshot', lambda p: (p / 'inputs/accretion/program.py').write_text('changed'))
    reject('manifest', lambda p: (p / 'manifest.json').write_text('{}'))
    reject('summary', lambda p: (p / 'summary.json').write_text('{}'))
    reject('duplicate', lambda p: (p / 'ledger.jsonl').write_bytes((p / 'ledger.jsonl').read_bytes() * 2))
    reject('reordered', lambda p: rehash(p, list(reversed(rows(p)))))
    reject('truncated', lambda p: rehash(p, rows(p)[:-1]))

    def forge_receipt(p, edit):
        path = p / 'pass-001/receipt.json'
        receipt = json.loads(path.read_text())
        edit(receipt)
        path.write_bytes(encode(receipt))
        records = rows(p)
        records[2]['event']['receipt_sha256'] = sha(path.read_bytes())
        records[2]['event']['verdict'] = receipt['verdict']
        rehash(p, records)

    reject('forged-metric', lambda p: forge_receipt(p, lambda r: r['samples'][0]['metrics'].update(after=1)), True)
    reject('forged-verdict', lambda p: forge_receipt(p, lambda r: r.update(verdict='NEUTRAL')), True)
    reject('forged-checker', lambda p: forge_receipt(p, lambda r: r['samples'][0]['checker'].update(stdout='')), True)

    def duplicate_credit(p):
        records = rows(p)
        records.insert(4, records[3].copy())
        rehash(p, records)
    reject('forged-credit', duplicate_credit, True)
    # Even a newly retained terminal cannot make an unbound manifest valid.
    def forged_manifest(p):
        path = p / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['source'] = 'forged'
        path.write_bytes(encode(manifest))
        rehash(p, rows(p))
    reject('forged-manifest', forged_manifest, True)
    # Snapshots are hashed data, never imported as executable verifier policy.
    def inert_snapshot(p):
        path = p / 'inputs/accretion/program.py'
        path.write_text('raise RuntimeError("snapshot executed")\n')
        manifest_path = p / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['inputs']['accretion/program.py'] = sha(path.read_bytes())
        manifest_path.write_bytes(encode(manifest))
        records = rows(p)
        records[0]['event']['manifest_sha256'] = sha(manifest_path.read_bytes())
        rehash(p, records)
    inert = root / 'inert'
    shutil.copytree(original, inert)
    inert_snapshot(inert)
    assert verify(inert, rows(inert)[-1]['sha256'], seal) == summary
    one = b'{"diagnose":"diagnostics.json"}'
    real_admit = program.admit
    def missing_certificate(before, after, *args):
        observation = real_admit(before, after, *args)
        if before != after:
            observation['accepted'] = False
            observation['checker'].update(status='missing_certificate', exit=0, stdout='', stderr='')
        return observation
    unknown = root / 'unknown'
    with patch.object(program, 'admit', side_effect=missing_certificate):
        expected = replay(unknown, seal, bun, bend, [one])
    assert expected['stop'] == 'unresolved'
    assert verify(unknown, rows(unknown)[-1]['sha256'], seal) == expected
    for name, candidates in [('partial', [one, one, b'{}']),
                              ('rejected', [b' ' * 4097] * 6), ('empty', [])]:
        path = root / name
        expected = replay(path, seal, bun, bend, candidates)
        assert verify(path, rows(path)[-1]['sha256'], seal) == expected
print('PASS offline replay verification, reconstruction, terminal and manifest binding, artifact tampering, independently rehashed false claims, partial and exhausted runs')

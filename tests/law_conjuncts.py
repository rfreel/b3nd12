#!/usr/bin/env python3
"""Independently challenge each conjunction in disposable books using real Bend."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from run import validate_compiler


def main():
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:3])
    validate_compiler(bend)
    originals = {name: (ROOT / 'accretion' / name).read_bytes() for name in ('LAWS.bend', 'PROOF.bend')}
    good = dict(preserved=True, no_regressions=True, before=9, after=8, candidate_bytes=4096)
    cases = {'positive_boundary': good,
             'preservation': {**good, 'preserved': False},
             'nonregression': {**good, 'no_regressions': False},
             'strict_gain_equal': {**good, 'after': 9},
             'strict_gain_worse': {**good, 'after': 10},
             'size': {**good, 'candidate_bytes': 4097}}
    with tempfile.TemporaryDirectory(prefix='law-conjuncts-') as tmp:
        book = Path(tmp)
        for name, raw in originals.items():
            (book / name).write_bytes(raw)
        for label, evidence in cases.items():
            lines = ['import Base']
            for key, value in evidence.items():
                typ = 'Bool' if type(value) is bool else 'Nat'
                term = ('True{}' if value else 'False{}') if type(value) is bool else str(value) + 'n'
                lines.append(f'def {key}() -> {typ}:\n  {term}\n')
            (book / 'Evidence.bend').write_text('\n'.join(lines))
            result = subprocess.run([str(bun), str(bend / 'bend2/main.ts'), str(book / 'PROOF.bend')],
                                    env={**os.environ, 'BEND_NO_TELEMETRY': '1'}, capture_output=True, text=True, timeout=15)
            passed = result.returncode == 0 and result.stdout == 'All terms check.\n' and not result.stderr
            assert passed == (label == 'positive_boundary'), (label, result)
            if not passed:
                assert 'improves_next_agent' in result.stdout + result.stderr, (label, result)
    assert all((ROOT / 'accretion' / name).read_bytes() == raw for name, raw in originals.items())
    print('PASS real Bend accepts size boundary and rejects each independently false law conjunct; originals unchanged')


if __name__ == '__main__':
    main()

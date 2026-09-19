#!/usr/bin/env python3
"""Verify the recorded spec seal, legal source write set, and actual proof books."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from run import validate_compiler


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def definition(source, name):
    start = source.index(b'def ' + name.encode() + b'(')
    end = source.find(b'\ndef ', start + 1)
    return source[start:end if end >= 0 else len(source)]


def outside_sum(source):
    # This official example has one sum declaration followed by the spec comment.
    start = source.index(b'def sum(')
    end = source.index(b'# spec for LAWS.bend only', start)
    body = source[start:end].splitlines()[1:]
    assert all(not line or line.startswith((b' ', b'#')) for line in body), 'new top-level surface'
    declarations = [line for line in source.splitlines() if line.startswith(b'def ')]
    assert [line.split(b'(')[0] for line in declarations] == [b'def pow2', b'def sum', b'def seq', b'def main']
    return source[:start] + source[end:]


def check_seal(main, law, proof, seal, official):
    assert digest(law) == seal['LAWS.bend'], 'law changed'
    for name in ('seq', 'pow2', 'main'):
        assert digest(definition(main, name)) == seal[name], name + ' changed'
    assert outside_sum(main) == outside_sum(official), 'outside sum write set'
    assert b'@unsafe' not in proof, 'unsafe proof'
    assert b'.js' not in proof and b'.js' not in main, 'host import'


def main():
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:3])
    validate_compiler(bend)
    example = ROOT / 'examples/frozen-spec-twin'
    seal = json.loads((example / 'SEAL.txt').read_text())
    assert seal['write_set'] == ['main.bend:sum', 'PROOF.bend']
    assert seal['upstream'] == json.loads((ROOT / 'upstream.json').read_text())['commit']
    official = subprocess.check_output(['git', '-C', str(bend), 'show', seal['upstream'] + ':demos/pure_par_sum/main.bend'])
    assert digest(official) == seal['main.before'], 'original main seal'
    law = (example / 'LAWS.bend').read_bytes()
    official_law = subprocess.check_output(['git', '-C', str(bend), 'show', seal['upstream'] + ':demos/pure_par_sum/LAWS.bend'])
    assert law == official_law
    current = (example / 'main.bend').read_bytes()
    proof = (example / 'PROOF.bend').read_bytes()
    check_seal(current, law, proof, seal, official)
    mutations = {
        'law': (current, law + b'\n', proof),
        'seq': (current.replace(b'Nat.add(seq(m, i)', b'Nat.add(seq(m, 0n)'), law, proof),
        'pow2': (current.replace(b'+h = pow2(p)', b'+h = pow2(d)'), law, proof),
        'main': (current.replace(b'sum!(16n, 0n)', b'seq(16n, 0n)'), law, proof),
        'import': (current + b'\nimport Other\n', law, proof),
        'extra_surface': (current.replace(b'# spec for', b'def extra() -> Nat:\n  0n\n\n# spec for'), law, proof),
        'sum_import': (current.replace(b'# spec for', b'import Other\n# spec for'), law, proof),
        'unsafe': (current, law, proof + b'\n@unsafe\n'),
    }
    for label, (candidate, candidate_law, candidate_proof) in mutations.items():
        assert (candidate, candidate_law, candidate_proof) != (current, law, proof), label
        try:
            check_seal(candidate, candidate_law, candidate_proof, seal, official)
        except AssertionError:
            pass
        else:
            raise AssertionError('illegal mutation accepted: ' + label)
    # Reverting sum to the official implementation is within the write set.
    # Both it and the currently sealed implementation must inhabit the actual law.
    with tempfile.TemporaryDirectory(prefix='spec-twin-') as tmp:
        book = Path(tmp)
        for source in (current, official):
            candidate_proof = proof + b'\n# Legal proof-only comment.\n'
            check_seal(source, law, candidate_proof, seal, official)
            for name, raw in [('main.bend', source), ('LAWS.bend', law), ('PROOF.bend', candidate_proof)]:
                (book / name).write_bytes(raw)
            result = subprocess.run([str(bun), str(bend / 'bend2/main.ts'), str(book / 'PROOF.bend')],
                                    env={**os.environ, 'BEND_NO_TELEMETRY': '1'}, capture_output=True, text=True, timeout=30)
            assert result.returncode == 0 and result.stdout == 'All terms check.\n' and not result.stderr, result
    print('PASS recorded law/spec/main hashes; 8 illegal mutations refused; both legal sum implementations check')


if __name__ == '__main__':
    main()

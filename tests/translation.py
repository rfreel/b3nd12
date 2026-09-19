#!/usr/bin/env python3
"""Challenge a finite corpus of actual Evidence.bend writes with an independent literal oracle."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from run import admit, validate_compiler


# Explicit fixture: empty table -> one correct direct implementation route.
BEFORE = b'{}\n'
AFTER = b'{"implement":"PROGRAM.md"}'
EXPECTED = """import Base

def preserved() -> Bool:
  True{}

def no_regressions() -> Bool:
  True{}

def before() -> Nat:
  9n

def after() -> Nat:
  8n

def candidate_bytes() -> Nat:
  26n
"""


def main():
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:3])
    validate_compiler(bend)
    assert len(AFTER) == 26
    expected_hash = hashlib.sha256(EXPECTED.encode()).hexdigest()
    mutations = {
        'preserved_false': ('def preserved() -> Bool:\n  True{}', 'def preserved() -> Bool:\n  False{}'),
        'nonregression_false': ('def no_regressions() -> Bool:\n  True{}', 'def no_regressions() -> Bool:\n  False{}'),
        'before_inflated': ('def before() -> Nat:\n  9n', 'def before() -> Nat:\n  10n'),
        'after_understated': ('def after() -> Nat:\n  8n', 'def after() -> Nat:\n  7n'),
        'size_over_budget': ('def candidate_bytes() -> Nat:\n  26n', 'def candidate_bytes() -> Nat:\n  4097n'),
        'size_understated': ('def candidate_bytes() -> Nat:\n  26n', 'def candidate_bytes() -> Nat:\n  0n'),
        'before_after_binding': ('def before() -> Nat:\n  9n\n\ndef after() -> Nat:\n  8n',
                                 'def after() -> Nat:\n  9n\n\ndef before() -> Nat:\n  8n'),
        'before_size_binding': ('def before() -> Nat:\n  9n\n\ndef after() -> Nat:\n  8n\n\ndef candidate_bytes() -> Nat:\n  26n',
                                'def candidate_bytes() -> Nat:\n  9n\n\ndef after() -> Nat:\n  8n\n\ndef before() -> Nat:\n  26n'),
    }
    results = []
    with tempfile.TemporaryDirectory(prefix='translation-mutations-') as temporary:
        workspace = Path(temporary)
        baseline = admit(BEFORE, AFTER, bun, bend, workspace)
        assert baseline['accepted']
        assert (workspace / 'book/Evidence.bend').read_bytes() == EXPECTED.encode()
        assert baseline['book_sha256']['Evidence.bend'] == expected_hash
        real_write = Path.write_text
        for name, (old, new) in mutations.items():
            assert EXPECTED.count(old) == 1
            altered = EXPECTED.replace(old, new)
            assert altered != EXPECTED
            writes = []
            def corrupt(path, data, *args, **kwargs):
                if path == workspace / 'book/Evidence.bend':
                    assert data == EXPECTED, 'producer changed; revise fixture explicitly'
                    writes.append(data)
                    data = altered
                return real_write(path, data, *args, **kwargs)
            with patch.object(Path, 'write_text', corrupt):
                observation = admit(BEFORE, AFTER, bun, bend, workspace)
            assert len(writes) == 1, 'mutation seam did not execute exactly once'
            actual = (workspace / 'book/Evidence.bend').read_bytes()
            assert actual == altered.encode()
            actual_hash = hashlib.sha256(actual).hexdigest()
            assert observation['book_sha256']['Evidence.bend'] == actual_hash
            # Metrics are honest fixture observations; only their generated translation is corrupt.
            assert observation['metrics'] == baseline['metrics']
            detected = actual_hash != expected_hash
            results.append({'mutation': name, 'source': altered, 'sha256': actual_hash,
                            'checker_accepted': observation['accepted'],
                            'checker': observation['checker'], 'independent_oracle_detected': detected})
    survivors = [row['mutation'] for row in results if not row['independent_oracle_detected']]
    report = {'schema': 'b3nd12.translation-test.v1', 'expected_source': EXPECTED,
              'expected_sha256': expected_hash, 'mutations': results, 'survivors': survivors,
              'scope': 'eight explicit translation mutations; standalone hash oracle, not general fault coverage'}
    print(json.dumps(report, indent=2))
    assert not survivors, survivors
    assert sum(row['checker_accepted'] for row in results) == 4


if __name__ == '__main__':
    main()

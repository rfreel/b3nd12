#!/usr/bin/env python3
"""Exhaust semantic routing tables against the four controlled replay baselines."""
import itertools
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from run import admit, validate_compiler


def main():
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:3])
    validate_compiler(bend)
    # Independent specification: do not derive expected answers from resolver TASKS.
    oracle = {'implement': 'PROGRAM.md', 'prove': 'PROVE.md', 'diagnose': 'diagnostics.json'}
    tasks = tuple(oracle)
    choices = (None, 'PROGRAM.md', 'PROVE.md', 'diagnostics.json')
    baselines = [dict(list(oracle.items())[:n]) for n in range(4)]
    accepted = 0
    with tempfile.TemporaryDirectory(prefix='routing-domain-') as tmp:
        workspace = Path(tmp)
        for baseline in baselines:
            for values in itertools.product(choices, repeat=3):
                candidate = {task: value for task, value in zip(tasks, values) if value is not None}
                # Missing routes return the correct pack via one extra router read.
                correct = all(value is None or value == oracle[task] for task, value in zip(tasks, values))
                no_regression = set(baseline) <= set(candidate)
                gain = len(candidate) > len(baseline)
                expected = correct and no_regression and gain
                result = admit(json.dumps(baseline).encode(), json.dumps(candidate).encode(), bun, bend, workspace)
                assert result['accepted'] == expected, (baseline, candidate, expected, result)
                assert result['metrics']['before'] == 9 - len(baseline)
                assert result['metrics']['after'] == 9 - len(candidate)
                accepted += expected
    assert accepted == 11, accepted
    print('PASS 64 semantic tables x 4 declared replay baselines = 256 real Bend decisions; 11 accepted')


if __name__ == '__main__':
    main()

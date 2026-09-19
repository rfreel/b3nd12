#!/usr/bin/env python3
"""Compare the real replay controller with a finite independent transition model.

Checker outcomes are controlled observations here. Real Bend equivalence remains
covered by program.py, routing_domain.py and law_conjuncts.py.
"""
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
import program
from run import validate_compiler

ORACLE = {'implement': 'PROGRAM.md', 'prove': 'PROVE.md', 'diagnose': 'diagnostics.json'}


def model(trace):
    gained = 0
    spent = 0
    unresolved = False
    for action in trace[:6]:
        if gained == 3 or unresolved:
            break
        spent += 1
        if action == 'P':
            gained += 1
        elif action == 'U':
            unresolved = True
    stop = ('target_met' if gained == 3 else 'unresolved' if unresolved else
            'budget_exhausted' if spent == 6 else 'candidates_exhausted')
    completed = ['reads-at-most-' + str(8 - index) for index in range(gained)]
    if gained == 3:
        completed.append('propose-successor')
    return spent, gained, completed, stop


def make_candidates(trace):
    accepted = {}
    candidates = []
    for action in trace:
        candidate = dict(accepted)
        if action == 'P':
            missing = [task for task in ORACLE if task not in accepted]
            if missing:
                candidate[missing[0]] = ORACLE[missing[0]]
                accepted = candidate
        elif action == 'R':
            candidate['implement'] = 'PROVE.md'
        candidates.append(json.dumps(candidate).encode())
    return candidates


def main():
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:3])
    validate_compiler(bend)
    seal = program.sha((ROOT / 'accretion/TODO.json').read_bytes())
    # Every live prefix is also a candidate-exhaustion test. Terminal branches
    # stop at the first unresolved observation, third gain, or sixth attempt.
    traces = []
    def enumerate_traces(prefix=()):
        traces.append(prefix)
        if len(prefix) == 6 or prefix.count('P') == 3 or 'U' in prefix:
            return
        for action in 'PNRU':
            enumerate_traces((*prefix, action))
    enumerate_traces()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='controller-model-') as temporary:
        root = Path(temporary)
        for index, trace in enumerate(traces):
            calls = [0]
            def observed(before, after, *unused):
                call = calls[0]
                calls[0] += 1
                old, new = json.loads(before), json.loads(after)
                old_reads = {task: 2 if task in old else 3 for task in ORACLE}
                new_reads = {task: 2 if task in new else 3 for task in ORACLE}
                preserved = all(new.get(task, expected) == expected for task, expected in ORACLE.items())
                nonregression = all(new_reads[task] <= old_reads[task] for task in ORACLE)
                action = None if call == 0 else trace[(call - 1) // 3]
                accepted = preserved and nonregression and sum(new_reads.values()) < sum(old_reads.values())
                status = 'accepted' if accepted else 'refused'
                if action == 'U':
                    accepted, status = False, 'timeout'
                return {'accepted': accepted, 'metrics': {'preserved': preserved,
                        'no_regressions': nonregression, 'before': sum(old_reads.values()),
                        'after': sum(new_reads.values()), 'candidate_bytes': len(after)},
                        'checker': {'status': status, 'stage': 'checker'}}
            directory = root / str(index)
            with patch('program.admit', side_effect=observed), patch('program.validate_compiler'):
                result = program.replay(directory, seal, bun, bend, make_candidates(trace))
            spent, gained, completed, stop = model(trace)
            assert result['stop'] == stop, (trace, result, stop)
            assert result['completed'] == completed, (trace, result, completed)
            assert sum(result['final']['reads'].values()) == 9 - gained, trace
            assert len(list(directory.glob('pass-*'))) == spent, trace
            assert calls[0] == 1 + 3 * spent, trace
            assert (result['successor'] is not None) == (gained == 3), trace
            assert result['installed'] is False
            receipts = [json.loads(path.read_text()) for path in sorted(directory.glob('pass-*/receipt.json'))]
            expected_verdicts = {'P': 'PRODUCTIVE', 'N': 'NEUTRAL', 'R': 'REJECTED', 'U': 'UNKNOWN'}
            assert [receipt['verdict'] for receipt in receipts] == [expected_verdicts[action] for action in trace[:spent]], trace
    print(f'PASS {len(traces)} reachable prefixes and terminal traces through frozen six-attempt budget; controlled observations, real controller and storage; {time.monotonic() - started:.2f}s')


if __name__ == '__main__':
    main()

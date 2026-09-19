#!/usr/bin/env python3
"""Verify retained observations offline; this does not authenticate their execution."""
import argparse
import hashlib
import json
from pathlib import Path

TASKS = {'implement': 'PROGRAM.md', 'prove': 'PROVE.md', 'diagnose': 'diagnostics.json'}
PIN = 'e5a4c4cfe980c2e4e70571562efb5197fe27b2f4'


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def decode(raw):
    require(len(raw) <= 4096, 'candidate exceeds 4096 bytes')
    result = parse(raw)
    require(isinstance(result, dict) and all(k in TASKS and v in TASKS.values()
            for k, v in result.items()), 'invalid route schema')
    return result


def verify(directory, terminal_sha256, contract_sha256):
    """Reconstruct state without importing or executing any producer snapshot."""
    directory = Path(directory).resolve()

    def read(name):
        path = directory / name
        require(path.resolve().is_relative_to(directory), 'artifact escapes evidence directory')
        require(not path.is_symlink(), 'symlink artifact refused')
        return path.read_bytes()

    contract_raw = read('TODO.json')
    require(sha(contract_raw) == contract_sha256, 'contract seal mismatch')
    contract = parse(contract_raw)
    require(contract['schema'] == 'b3nd12.todo.v1' and contract['pin'] == PIN,
            'unsupported contract version or pin')
    require(contract['baseline'] == {} and contract['targets'] == [8, 7, 6]
            and contract['max_attempts'] == 6 and contract['repetitions'] == 3
            and contract['final_task'] == 'propose-successor', 'unsupported contract policy')
    protected = {'accretion/LAWS.bend', 'accretion/PROOF.bend', 'upstream.json',
                 'guide/agent/ROUTER.md', *('guide/agent/' + n for n in TASKS.values())}
    require(set(contract['protected']) == protected, 'incomplete protected inputs')
    manifest_raw = read('manifest.json')
    manifest = parse(manifest_raw)
    require(manifest['schema'] == 'b3nd12.experiment.v1' and manifest['pin'] == PIN
            and manifest['contract_sha256'] == contract_sha256, 'manifest contract mismatch')
    required = protected | {'bounded.py', 'accretion/storage.py', 'accretion/TODO.json', 'accretion/program.py',
                            'accretion/run.py', 'accretion/environment.py', 'accretion/routes.json'}
    require(set(manifest['inputs']) == required, 'unsupported manifest input set')
    snapshots = {}
    for name, digest in manifest['inputs'].items():
        snapshots[name] = read('inputs/' + name)
        require(sha(snapshots[name]) == digest, 'snapshot hash mismatch: ' + name)
    require(snapshots['accretion/TODO.json'] == contract_raw, 'snapshot contract mismatch')
    for name, digest in contract['protected'].items():
        require(sha(snapshots[name]) == digest, 'protected input mismatch: ' + name)

    def measure(raw):
        mapping = decode(raw)
        return {'preserved': all(snapshots['guide/agent/' + mapping.get(t, n)] ==
                                snapshots['guide/agent/' + n] for t, n in TASKS.items()),
                'reads': {t: 2 if t in mapping else 3 for t in TASKS}}

    def sample(row, before, after):
        old, new = measure(before), measure(after)
        metrics = {'preserved': old['preserved'] and new['preserved'],
                   'no_regressions': all(new['reads'][t] <= old['reads'][t] for t in TASKS),
                   'before': sum(old['reads'].values()), 'after': sum(new['reads'].values()),
                   'candidate_bytes': len(after)}
        require(encode(row['metrics']) == encode(metrics) and encode(row['before_reads']) == encode(old['reads'])
                and encode(row['after_reads']) == encode(new['reads']), 'forged route observations')
        require(row['baseline_sha256'] == sha(before) and row['candidate_sha256'] == sha(after)
                and row['law_sha256'] == contract['protected']['accretion/LAWS.bend'],
                'sample binding mismatch')
        checker = row['checker']
        accepted = checker['exit'] == 0 and checker['stdout'] == 'All terms check.\n' and checker['stderr'] == ''
        require(type(row['accepted']) is bool and row['accepted'] == accepted, 'checker acceptance mismatch')
        require(checker.get('stage') == 'checker', 'unsupported checker observation version')
        require((checker['status'] == 'accepted') == accepted, 'checker status mismatch')
        require(checker['status'] in {'accepted', 'refused', 'timeout', 'output_limit', 'spawn_error', 'crash',
                                     'missing_certificate', 'malformed_certificate', 'process_error'},
                'unsupported checker status')
        refusal = ("Error:\n- expected : False{}\n- observed : True{}\n"
                   "Location: LAWS.improves_next_agent\n"
                   "4 | def Laws.improves_next_agent():\n5>|   {==}\n6 | \n")
        code = checker['exit']
        require(code is None or type(code) is int, 'invalid checker exit')
        if code is None:
            require(checker['status'] in {'timeout', 'output_limit', 'spawn_error', 'malformed_certificate'}
                    and isinstance(checker.get('error'), str), 'invalid process exception')
        else:
            status = ('accepted' if accepted else 'refused' if code == 1 and checker['stdout'] == ''
                      and checker['stderr'] == refusal else 'crash' if code < 0 else
                      'process_error' if code != 0 else 'missing_certificate'
                      if checker['stdout'] == '' and checker['stderr'] == '' else 'malformed_certificate')
            require(checker['status'] == status, 'checker status contradicts process observations')
        if checker['status'] == 'output_limit':
            require(type(checker.get('limit_bytes')) is int and checker['limit_bytes'] > 0
                    and type(checker.get('observed_bytes')) is int
                    and checker['observed_bytes'] > checker['limit_bytes'], 'invalid output limit evidence')
        lawful = metrics['preserved'] and metrics['no_regressions'] and metrics['after'] < metrics['before']
        require(not accepted or lawful, 'certificate contradicts frozen predicate')
        return metrics

    rows = [parse(line) for line in read('ledger.jsonl').splitlines()]
    require(rows, 'empty ledger')
    previous = None
    for index, row in enumerate(rows):
        require(set(row) == {'sequence', 'previous', 'event', 'sha256'}, 'unsupported ledger record')
        require(type(row['sequence']) is int and row['sequence'] == index and row['previous'] == previous,
                'ledger sequence mismatch')
        payload = {k: v for k, v in row.items() if k != 'sha256'}
        require(sha(encode(payload)) == row['sha256'], 'ledger hash mismatch')
        previous = row['sha256']
    require(previous == terminal_sha256, 'retained terminal digest mismatch')
    events = [r['event'] for r in rows]
    baseline = events.pop(0)
    require(baseline['kind'] == 'baseline' and baseline.get('manifest_sha256') == sha(manifest_raw),
            'missing or mismatched manifest binding; legacy evidence unsupported')
    before = b'{}\n'
    require(baseline['profile'] == measure(before), 'baseline profile mismatch')
    sample(baseline['control'], before, before)
    require(baseline['control']['checker']['status'] == 'refused', 'baseline control unresolved')
    completed, attempts, unresolved = [], 0, False
    while events and events[0]['kind'] == 'attempt':
        require(not unresolved and sum(measure(before)['reads'].values()) != 6, 'attempt after stop condition')
        attempts += 1
        require(attempts <= 6, 'attempt budget exceeded')
        event = events.pop(0)
        prefix = f'pass-{attempts:03d}/'
        after = read(prefix + 'candidate.json')
        require(read(prefix + 'before.json') == before, 'pass baseline mismatch')
        require(event == {'kind': 'attempt', 'attempt': attempts, 'baseline_sha256': sha(before),
                          'candidate_sha256': sha(after)}, 'attempt binding mismatch')
        raw = read(prefix + 'receipt.json')
        receipt = parse(raw)
        require(events and events.pop(0) == {'kind': 'verdict', 'attempt': attempts,
                'receipt_sha256': sha(raw), 'verdict': receipt['verdict']}, 'receipt ledger mismatch')
        require(receipt['attempt'] == attempts and receipt['contract_sha256'] == contract_sha256
                and receipt['baseline_sha256'] == sha(before) and receipt['candidate_sha256'] == sha(after),
                'receipt binding mismatch')
        valid = True
        try:
            mapping, current = decode(after), decode(before)
            require(sum(current.get(t) != mapping.get(t) for t in TASKS) <= 1, 'bundled levers')
        except (ValueError, UnicodeError):
            valid = False
        observations = receipt['samples']
        if not valid:
            require(observations == [], 'invalid candidate has observations')
            verdict = 'REJECTED'
        else:
            require(len(observations) == 3, 'incomplete observation set')
            metrics = [sample(s, before, after) for s in observations]
            if any(s['checker']['status'] not in {'accepted', 'refused'} for s in observations):
                verdict = 'UNKNOWN'
            elif all(s['accepted'] for s in observations):
                verdict = 'PRODUCTIVE'
            elif not metrics[0]['preserved'] or not metrics[0]['no_regressions']:
                verdict = 'REJECTED'
            elif metrics[0]['before'] == metrics[0]['after']:
                verdict = 'NEUTRAL'
            else:
                verdict = 'UNKNOWN'
        require(receipt['verdict'] == verdict, 'verdict contradicts observations')
        if verdict == 'PRODUCTIVE':
            before = after
            for target in contract['targets']:
                task = f'reads-at-most-{target}'
                if sum(measure(before)['reads'].values()) <= target and task not in completed:
                    require(events and events.pop(0) == {'kind': 'completed', 'task': task,
                            'attempt': attempts, 'candidate_sha256': sha(before)}, 'completion mismatch')
                    completed.append(task)
        unresolved = verdict == 'UNKNOWN'
    final = measure(before)
    successor = None
    if len(completed) == 3:
        successor = parse(read('successor.json'))
        require(successor['schema'] == 'b3nd12.successor.v1'
                and successor['parent_contract_sha256'] == contract_sha256
                and successor['status'] == 'exhausted' and successor['candidates'] == []
                and successor['activation'] == 'not_authorized' and successor['evidence'] == final,
                'invalid successor authority or evidence')
        require(events and events.pop(0) == {'kind': 'completed', 'task': 'propose-successor',
                'proposal_sha256': sha(read('successor.json'))}, 'successor completion mismatch')
        completed.append('propose-successor')
    else:
        require(not (directory / 'successor.json').exists(), 'premature successor')
    stop = ('target_met' if sum(final['reads'].values()) == 6 else 'unresolved' if unresolved else
            'budget_exhausted' if attempts == 6 else 'candidates_exhausted')
    summary = {'schema': 'b3nd12.experiment.v1', 'stop': stop, 'completed': completed,
               'final': final, 'final_sha256': sha(before), 'successor': successor,
               'installed': False, 'contract_sha256': contract_sha256}
    require(events == [{'kind': 'stop', **summary}], 'stop record mismatch or trailing events')
    require(read('final.json') == before, 'final state mismatch')
    if (directory / 'summary.json').exists():
        require(parse(read('summary.json')) == summary, 'summary mismatch')
    require({p.name for p in directory.glob('pass-*')} ==
            {f'pass-{n:03d}' for n in range(1, attempts + 1)}, 'extra or missing attempt artifacts')
    return summary


def inspect_evidence(directory, terminal_sha256, contract_sha256):
    """Classify interrupted records without granting incomplete runs acceptance."""
    directory = Path(directory)
    try:
        records = [parse(line) for line in (directory / 'ledger.jsonl').read_bytes().splitlines()]
        previous = None
        for index, row in enumerate(records):
            payload = {k: v for k, v in row.items() if k != 'sha256'}
            require(row['sequence'] == index and row['previous'] == previous
                    and sha(encode(payload)) == row['sha256'], 'invalid ledger prefix')
            previous = row['sha256']
        if not records or records[-1]['event'].get('kind') != 'stop':
            return {'status': 'incomplete', 'verified': False, 'error': 'terminal stop record absent'}
        summary = verify(directory, terminal_sha256, contract_sha256)
        return {'status': 'complete', 'verified': True, 'summary': summary,
                'guarantee': 'conditional observation integrity; no runtime authenticity'}
    except FileNotFoundError as exc:
        return {'status': 'incomplete', 'verified': False, 'error': str(exc)}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {'status': 'invalid', 'verified': False, 'error': str(exc)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--terminal-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    result = inspect_evidence(args.directory, args.terminal_sha256, args.contract_sha256)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'complete' else 1)

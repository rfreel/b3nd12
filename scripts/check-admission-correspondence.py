#!/usr/bin/env python3
"""Execute all 54 finite Bend decisions and compare authenticated Python decisions.

Context=false is represented by a signed unauthorized actor. This checks the
finite abstraction, not the completeness of authentication or host enforcement.
"""
import argparse
import hmac
import importlib.util
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import admission_gate as gate


def vectors():
    return list(itertools.product((False, True), ('PASS', 'FAIL', 'PENDING'),
                                  ('PASS', 'FAIL', 'PENDING'), ('PASS', 'FAIL', 'PENDING')))


def python_decision(context, *statuses):
    keys = {f'producer-{d}': bytes([n + 1]) * 32 for n, d in enumerate(gate.DOMAINS)}
    policy = dict(version=1, repository='correspondence/repo', target='refs/heads/main', epoch=1,
                  actors=['worker'], domains={d: dict(producer=f'producer-{d}', kind='bounded-test')
                                             for d in gate.DOMAINS})
    policy.update({pin: gate.sha(pin.encode()) for pin in gate.PINS})
    manifest = {field: policy[field] for field in ('repository', 'target', 'epoch', *gate.PINS)}
    manifest.update(version=1, base='a'*40, candidate='b'*40, tree='c'*40,
                    policy=gate.sha(gate.canonical(policy)), request='correspondence',
                    actor='worker' if context else 'unauthorized')
    receipts, artifacts = [], {}
    for domain, status in zip(gate.DOMAINS, statuses):
        content = f'{domain}:{status}'.encode()
        digest = gate.sha(content)
        artifacts[digest] = content
        receipt = dict(domain=domain, producer=f'producer-{domain}', kind='bounded-test',
                       manifest=gate.sha(gate.canonical(manifest)), artifact=digest, status=status)
        receipt['mac'] = hmac.digest(keys[receipt['producer']], gate.canonical(receipt), 'sha256').hex()
        receipts.append(receipt)
    return gate.decide(dict(manifest=manifest, receipts=receipts), policy, keys, artifacts)['verdict']


def source(model):
    requests = []
    for context, *statuses in vectors():
        fields = ', '.join([str(context) + '{}', *('Model.' + x.title() + '{}' for x in statuses)])
        requests.append('Model.decide(Model.Request{' + fields + '})')
    return ('import Base\nimport ' + model.as_posix() + ' as Model\n\n'
            'def main() -> List<Model.Decision>:\n  [' + ', '.join(requests) + ']\n')


def compare(actual, expected):
    if len(actual) != 54 or len(expected) != 54:
        raise ValueError('Expected exactly 54 decision results')
    differences = [dict(vector=v, bend=a, python=e) for v, a, e in zip(vectors(), actual, expected) if a != e]
    if differences:
        raise ValueError('Correspondence failure: ' + json.dumps(differences))


def run(bun, upstream):
    spec = importlib.util.spec_from_file_location('admission_proof_generator',
                                                  ROOT / 'scripts/generate-admission-proof.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    inventory = generator.check_inventory()
    if (ROOT / 'pilot/admission/PROOF.bend').read_text() != generator.render():
        raise ValueError('Generated proof drift')
    proof = subprocess.run([bun, str(Path(upstream) / 'bend2/main.ts'),
                            str(ROOT / 'pilot/admission/PROOF.bend'), '--json'],
                           text=True, capture_output=True, timeout=30,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    proof_events = [json.loads(line) for line in (proof.stdout + '\n' + proof.stderr).splitlines()
                    if line.strip()]
    if (proof.returncode or
        sum(e.get('id') == 'BND000' and e.get('unsafe') == 0 for e in proof_events) != 1 or
        any(e.get('severity') == 'error' for e in proof_events)):
        raise ValueError('Complete law proof check failed: ' + proof.stdout + proof.stderr)
    with tempfile.TemporaryDirectory(prefix='admission-correspondence-') as tmp:
        path = Path(tmp) / 'vectors.bend'
        path.write_text(source(ROOT / 'pilot/admission/model.bend'))
        result = subprocess.run([bun, str(Path(upstream) / 'bend2/main.ts'), str(path), '--json'],
                                text=True, capture_output=True, timeout=30,
                                env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    if result.returncode:
        raise ValueError(result.stdout + result.stderr)
    events = [json.loads(line) for line in (result.stdout + '\n' + result.stderr).splitlines()
              if line.startswith('{')]
    if sum(e.get('id') == 'BND000' and e.get('unsafe') == 0 for e in events) != 1:
        raise ValueError('Missing unique safe checker result')
    if any(e.get('severity') == 'error' for e in events):
        raise ValueError('Checker reported errors')
    # Parse runtime constructors, not the diagnostic event or a generated expectation.
    values = re.findall(r'\.((?:Accepted|Rejected|Waiting))\{\}', result.stdout)
    mapping = dict(Accepted='ACCEPTED', Rejected='REJECTED', Waiting='PENDING')
    actual = [mapping[value] for value in values]
    expected = [python_decision(*vector) for vector in vectors()]
    compare(actual, expected)
    return dict(vectors=54, matching=54, unsafe=0, runtime_executed=True, verified_laws=inventory,
                counts={status: actual.count(status) for status in ('ACCEPTED', 'REJECTED', 'PENDING')},
                scope='Finite decision abstraction; invalid context represented by unauthorized actor')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream')
    parser.add_argument('--bun', default=os.environ.get('BUN', 'bun'))
    args = parser.parse_args()
    print(json.dumps(run(args.bun, args.upstream), sort_keys=True))


if __name__ == '__main__':
    main()

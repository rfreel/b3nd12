#!/usr/bin/env python3
"""Run the bounded, reviewed cross-suite defect catalog and expose failures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: mutation_catalog.py PIN BUN')
    pin, bun = (Path(arg).resolve() for arg in sys.argv[1:])
    catalog = json.loads((ROOT / 'spec/mutation-catalog.json').read_text())
    assert catalog['schema'] == 'b3nd12.mutation-catalog.v1'
    assert {entry['id'] for entry in catalog['cases']} == {'scope', 'parser', 'proof', 'oracle', 'accounting'}
    allowed = {'tests/patch_stack.py', 'tests/cli_properties.py', 'tests/law_conjuncts.py', 'tests/translation.py', 'tests/evidence.py'}
    results = []
    for entry in catalog['cases']:
        assert entry['suite'] in allowed and entry['defects'] and entry['oracle'] and entry['survivors']
        script = ROOT / entry['suite']
        before = hashlib.sha256(script.read_bytes()).hexdigest()
        command = [sys.executable, str(script), str(pin)]
        assert entry['arguments'] in ('pin', 'pin_bun')
        if entry['arguments'] == 'pin_bun':
            command.append(str(bun))
        start = time.monotonic()
        process = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PATH': str(bun.parent) + os.pathsep + os.environ['PATH']}, capture_output=True, text=True, timeout=240)
        row = {'id': entry['id'], 'command': command, 'source_sha256': before, 'exit': process.returncode,
               'seconds': time.monotonic() - start, 'stdout': process.stdout, 'stderr': process.stderr,
               'status': 'detected_by_suite_assertions' if process.returncode == 0 else 'unresolved_suite_failure'}
        assert hashlib.sha256(script.read_bytes()).hexdigest() == before, 'test source changed during run'
        if entry['id'] == 'oracle' and process.returncode == 0:
            observation = json.loads(process.stdout)
            row['checker_only_survivors'] = [item['mutation'] for item in observation['mutations'] if item['checker_accepted']]
            row['independent_oracle_survivors'] = observation['survivors']
            assert len(row['checker_only_survivors']) == 4 and not row['independent_oracle_survivors']
        results.append(row)
    # A real implementation mutant must make the unchanged parser suite fail.
    original = (ROOT / 'b3nd12.py').read_text()
    old = 'values = args[1:] + tail'
    new = 'values = args[1:] + [value.rstrip() for value in tail]'
    assert original.count(old) == 1, 'parser mutation seam changed; review the mutant'
    with tempfile.TemporaryDirectory(prefix='b3nd12-parser-mutant-') as tmp:
        mutant = Path(tmp) / 'management'
        shutil.copytree(ROOT, mutant, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        (mutant / 'b3nd12.py').write_text(original.replace(old, new))
        command = [sys.executable, str(mutant / 'tests/cli_properties.py'), str(pin)]
        failed = subprocess.run(command, cwd=mutant, capture_output=True, text=True, timeout=60)
        assert failed.returncode != 0, 'literal operand normalization mutant survived'
        assert 'got[1] == [literal]' in failed.stderr and 'AssertionError' in failed.stderr, failed.stderr
        results.append({'id': 'parser_implementation_mutant', 'command': command,
                        'status': 'detected_by_unchanged_suite', 'exit': failed.returncode,
                        'expected_failure': True, 'stdout': failed.stdout, 'stderr': failed.stderr,
                        'before_sha256': hashlib.sha256(original.encode()).hexdigest(),
                        'mutant_sha256': hashlib.sha256((mutant / 'b3nd12.py').read_bytes()).hexdigest()})
    assert (ROOT / 'b3nd12.py').read_text() == original
    print(json.dumps({'schema': 'b3nd12.mutation-run.v1', 'scope': catalog['scope'], 'results': results}, indent=2))
    assert all(row['exit'] == 0 or row.get('expected_failure') for row in results), 'Failed suite is unresolved evidence, not a detected mutation receipt'


if __name__ == '__main__':
    main()

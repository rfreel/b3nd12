#!/usr/bin/env python3
"""Reviewed documentation blocks and fixed executable recipes, never Markdown eval."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'spec/documentation-examples.json'


def blocks(text):
    found, current, language = [], None, None
    for line in text.splitlines(keepends=True):
        if line.startswith('```'):
            if current is None:
                current, language = [], line.strip()[3:]
            else:
                found.append({'language': language, 'sha256': hashlib.sha256(''.join(current).encode()).hexdigest()})
                current = None
        elif current is not None:
            current.append(line)
    if current is not None:
        raise ValueError('unclosed example block')
    return found


def validate(inventory, texts):
    assert inventory['schema'] == 'b3nd12.documentation-examples.v1'
    for name, entries in inventory['documents'].items():
        actual = blocks(texts[name])
        assert len(actual) == len(entries), ('example count changed', name)
        for number, (observed, entry) in enumerate(zip(actual, entries), 1):
            assert observed == {k: entry[k] for k in ('language', 'sha256')}, ('review example change', name, number)
            assert entry['coverage'] in ('recipe', 'suite', 'prerequisite', 'illustration')
            assert entry['evidence'] and entry['limit']
            for suite in entry.get('suites', []):
                assert (ROOT / suite).is_file(), suite


def compare_verify_example(published, actual):
    """Only the checkout's literal command operand and resolved path vary."""
    normalized = json.loads(json.dumps(actual))
    assert normalized['command'][0] == 'verify' and len(normalized['command']) == 2
    normalized['command'][1] = published['command'][1]
    normalized['result']['target'] = published['result']['target']
    assert normalized == published, 'published verify example differs from actual output'


def main():
    inventory = json.loads(INVENTORY.read_text())
    texts = {name: (ROOT / name).read_text() for name in inventory['documents']}
    validate(inventory, texts)
    schema = json.loads((ROOT / 'spec/cli-v1.schema.json').read_text())
    validator = Draft202012Validator(schema)
    example = texts['docs/CLI.md'].split('```json\n', 1)[1].split('```', 1)[0]
    payload = json.loads(example)
    validator.validate(payload)
    unsupported = json.loads(example)
    unsupported['result']['runtime_status'] = 'all_backends_proven'
    assert list(validator.iter_errors(unsupported)), 'unsupported runtime completion claim survived'
    changed = dict(texts)
    changed['README.md'] = changed['README.md'].replace('doctor --json', 'doctor --stale-flag', 1)
    try:
        validate(inventory, changed)
    except AssertionError:
        pass
    else:
        raise AssertionError('stale example survived')
    if len(sys.argv) != 3:
        raise SystemExit('usage: documentation.py PINNED_CHECKOUT BUN')
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:])
    assert bend.is_dir() and bun.is_file(), 'declared prerequisites unavailable'
    frozen = {name: (ROOT / name).read_bytes() for name in ('accretion/TODO.json', 'accretion/routes.json', 'accretion/LAWS.bend')}
    env = {**os.environ, 'PATH': str(bun.parent) + os.pathsep + os.environ['PATH'], 'BEND_NO_TELEMETRY': '1'}
    commands = []
    with tempfile.TemporaryDirectory(prefix='b3nd12-doc-examples-') as tmp:
        temp = Path(tmp)
        management = temp / 'management'
        # A disposable source snapshot includes uncommitted implementation under test.
        shutil.copytree(ROOT, management, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        def run(args, expected=0):
            result = subprocess.run(args, cwd=management, env=env, capture_output=True, text=True, timeout=180)
            commands.append({'argv': args, 'exit': result.returncode})
            assert result.returncode == expected, (args, result.stdout, result.stderr)
            return result
        run(['git', 'init', '--quiet'])
        run(['git', 'add', '.'])
        run(['git', '-c', 'user.name=Documentation Test', '-c', 'user.email=docs-test@example.invalid', 'commit', '--quiet', '-m', 'Disposable documentation source snapshot'])
        target = temp / 'bend'
        run(['git', 'clone', '--no-local', '--quiet', str(bend), str(target)])
        pin = json.loads((management / 'upstream.json').read_text())['commit']
        run(['git', '-C', str(target), 'checkout', '--quiet', pin])
        for args in [('doctor', '--json'), ('task', 'implement'), ('task', 'prove'), ('task', 'diagnose'), ('guide', 'prove', '--json')]:
            assert json.loads(run([sys.executable, 'b3nd12.py', *args]).stdout)['ok']
        run([sys.executable, 'b3nd12.py', 'apply', str(target), '--json'])
        run([sys.executable, 'b3nd12.py', 'verify', '--human', '--', str(target)])
        actual = json.loads(run([sys.executable, 'b3nd12.py', 'verify', '--json', '--', str(target)]).stdout)
        compare_verify_example(payload, actual)
        stale = json.loads(example)
        stale['result']['checks'].remove('index')
        try:
            compare_verify_example(stale, actual)
        except AssertionError:
            pass
        else:
            raise AssertionError('omitted index check survived documentation comparison')
        run([sys.executable, 'b3nd12.py', 'doctor', '--stale-flag'], 2)
        seal = hashlib.sha256(frozen['accretion/TODO.json']).hexdigest()
        packet = temp / 'packet'
        run([sys.executable, 'accretion/program.py', '--contract-sha256', seal, '--bend-root', str(bend), '--bun', str(bun), '--output', str(packet)])
        terminal = json.loads((packet / 'ledger.jsonl').read_text().splitlines()[-1])['sha256']
        flags = ['--contract-sha256', seal, '--terminal-sha256', terminal]
        verified = run([sys.executable, 'accretion/verify_evidence.py', str(packet), *flags])
        assert json.loads(verified.stdout)['verified']
        run([sys.executable, 'accretion/recheck.py', str(packet), *flags, '--bend-root', str(bend), '--bun', str(bun)])
        archive, imported = temp / 'evidence.zip', temp / 'imported'
        run([sys.executable, 'accretion/archive.py', 'export', str(packet), str(archive), *flags])
        run([sys.executable, 'accretion/archive.py', 'import', str(archive), str(imported), *flags])
        assert json.loads(run([sys.executable, 'accretion/verify_evidence.py', str(imported), *flags]).stdout)['verified']
        receipt = temp / 'installation.json'
        digest = json.loads(run([sys.executable, 'installation_receipt.py', 'record', str(target), str(receipt)]).stdout)['sha256']
        run([sys.executable, 'installation_receipt.py', 'replay', str(receipt), '--sha256', digest, '--source', str(bend), '--destination', str(temp / 'replayed')])
    assert all((ROOT / name).read_bytes() == raw for name, raw in frozen.items())
    print(json.dumps({'schema': 'b3nd12.documentation-run.v1', 'commands': commands,
                      'blocks': sum(map(len, inventory['documents'].values())),
                      'limit': 'Declared four-document inventory; prerequisite acquisition and linked suites are classified, not re-executed here.'}))


if __name__ == '__main__':
    main()

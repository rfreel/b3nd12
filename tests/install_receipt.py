#!/usr/bin/env python3
"""Receipt seals reject drift and reproduce the delivery in an independent clone."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / 'upstream.json').read_text())['commit']


def run(*args, ok=True, env=None):
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    if ok and result.returncode:
        raise AssertionError((args, result.stdout, result.stderr))
    return result


def main():
    source = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='b3nd12-receipt-') as temporary:
        tmp = Path(temporary)
        installer = tmp / 'installer'
        shutil.copytree(ROOT, installer, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        tool = installer / 'installation_receipt.py'
        initial = tmp / 'initial'
        run('git', 'clone', '--no-local', '--no-checkout', str(source), str(initial))
        run('git', '-C', str(initial), 'checkout', '--detach', PIN)
        run(str(installer / 'apply.sh'), str(initial))
        receipt = tmp / 'receipt.json'
        recorded = json.loads(run(sys.executable, str(tool), 'record', str(initial), str(receipt)).stdout)
        seal = recorded['sha256']
        assert seal == hashlib.sha256(receipt.read_bytes()).hexdigest()
        saved = json.loads(receipt.read_bytes())
        assert len(saved['identities']['patches']) == 9
        assert len(saved['identities']['delivery']) == 25
        replayed = tmp / 'replayed'
        invocation = [sys.executable, str(tool), 'replay', str(receipt), '--sha256', seal,
                      '--source', str(source), '--destination']
        result = json.loads(run(*invocation, str(replayed)).stdout)
        assert result['nonshared'] and result['verification'] == recorded['verification']
        assert not (replayed / '.git/objects/info/alternates').exists()
        for entry in saved['identities']['delivery']:
            assert (initial / entry['path']).read_bytes() == (replayed / entry['path']).read_bytes()
        print('PASS receipt reproduces 25 exact delivery files in fresh nonshared checkout')
        alternate_bin = tmp / 'alternate-bin'
        alternate_bin.mkdir()
        alternate_python = alternate_bin / 'python3'
        alternate_python.write_text('#!/bin/sh\nprintf "Python alternate identity\\n"\n')
        alternate_python.chmod(0o755)
        destination = tmp / 'refused-installer-python'
        changed_env = {**os.environ, 'PATH': str(alternate_bin) + os.pathsep + os.environ['PATH']}
        refused = run(*invocation, str(destination), ok=False, env=changed_env)
        assert refused.returncode != 0 and 'identities differ' in refused.stdout, refused.stdout
        assert not destination.exists()
        assert 'installer_python' in saved['identities']['tools']
        print('PASS changed PATH python3 refused even with unchanged receipt-process interpreter')

        for name in ('patches/01-router.patch', 'delivery-manifest.json', 'stack.py', 'overlay/bend2/main.ts'):
            file = installer / name
            original = file.read_bytes()
            file.write_bytes(original + b'\n')
            destination = tmp / ('refused-' + file.name)
            refused = run(*invocation, str(destination), ok=False)
            assert refused.returncode != 0 and not destination.exists(), refused.stdout
            file.write_bytes(original)
        original = receipt.read_bytes()
        receipt.write_bytes(original + b'\n')
        destination = tmp / 'refused-receipt'
        assert run(*invocation, str(destination), ok=False).returncode != 0
        assert not destination.exists()
        receipt.write_bytes(original)
        wrong = tmp / 'wrong-pin'
        run('git', 'clone', '--no-local', '--no-checkout', str(source), str(wrong))
        run('git', '-C', str(wrong), 'checkout', '--detach', PIN + '^')
        destination = tmp / 'refused-pin'
        command = invocation.copy()
        command[command.index('--source') + 1] = str(wrong)
        assert run(*command, str(destination), ok=False).returncode != 0
        assert not destination.exists()
        print('PASS patch, manifest, verifier, oracle, receipt and wrong-pin drift refused before clone writes')
        assert run(sys.executable, str(tool), 'record', str(initial), str(receipt), ok=False).returncode != 0
        assert run(sys.executable, str(tool), 'record', str(initial), str(installer / 'forbidden.json'), ok=False).returncode != 0
        assert not (installer / 'forbidden.json').exists()
        print('PASS receipts cannot overwrite existing output or write inside repository')


if __name__ == '__main__':
    main()

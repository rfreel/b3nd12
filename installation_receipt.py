#!/usr/bin/env python3
"""Record and reproduce a pinned installation using independently retained digests."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import bounded
import stack

ROOT = Path(__file__).resolve().parent
SCHEMA = 'b3nd12.installation-receipt.v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1048576), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def command(args, timeout=30):
    result = bounded.run(args, timeout=timeout)
    result.check_returncode()
    return result.stdout.decode().strip()


def identities():
    manifest_bytes = (ROOT / 'delivery-manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    expected = stack.expected_files()
    source_names = ('upstream.json', 'stack.py', 'bounded.py', 'apply.sh',
                    'verify.sh', 'installation_receipt.py')
    tools = {}
    for name, executable, version in (
            ('python', sys.executable, ['--version']),
            ('installer_python', shutil.which('python3'), ['--version']),
            ('git', shutil.which('git'), ['--version']),
            ('shell', '/bin/sh', None),
            ('bun', shutil.which('bun'), ['--version'])):
        if executable is None:
            if name == 'installer_python':
                raise ValueError('Installer requires python3 on PATH')
            tools[name] = None
            continue
        path = Path(executable).resolve()
        tools[name] = {'sha256': file_hash(path),
                       'version': command([str(path), *version]) if version else None}
    return {
        'pin': stack.PIN,
        'patches': [{'path': patch.relative_to(ROOT).as_posix(), 'sha256': file_hash(patch)}
                    for patch in stack.patch_files()],
        'manifest_sha256': digest(manifest_bytes),
        'delivery': [{'path': entry['path'], 'mode': entry['mode'], 'role': entry['role'],
                      'source': entry['source'], 'sha256': file_hash(expected[entry['path']])}
                     for entry in manifest['files']],
        'verifier_sources': {name: file_hash(ROOT / name) for name in source_names},
        'tools': tools,
    }


def external(path):
    path = Path(path).resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Generated checkout and receipt paths must be outside the repository')
    return path


def record(target, output):
    output = external(output)
    if output.exists():
        raise ValueError('Receipt destination already exists')
    before = identities()
    result = stack.verify(target)
    if identities() != before:
        raise ValueError('Installation sources changed during verification')
    receipt = {'schema': SCHEMA, 'identities': before, 'verification': result}
    data = (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode()
    with output.open('xb') as destination:
        destination.write(data)
    return {'receipt': str(output), 'sha256': digest(data), 'verification': result}


def validate(receipt, expected_sha256):
    with Path(receipt).open('rb') as source:
        data = source.read(1048577)
    if len(data) > 1048576 or digest(data) != expected_sha256:
        raise ValueError('Receipt digest mismatch or oversized receipt')
    saved = json.loads(data)
    if (type(saved) is not dict or set(saved) != {'schema', 'identities', 'verification'}
            or saved['schema'] != SCHEMA or saved['identities'] != identities()):
        raise ValueError('Receipt sources, pin, manifest or tool identities differ')
    return saved


def replay(receipt, expected_sha256, source, destination):
    saved = validate(receipt, expected_sha256)
    source = stack.target_check(source)
    stack.install_guard(source, filesystem=False)
    destination = external(destination)
    if destination.exists():
        raise ValueError('Replay requires a new checkout path')
    command(['git', 'clone', '--no-local', '--no-checkout', str(source), str(destination)], 60)
    command(['git', '-C', str(destination), 'checkout', '--detach', stack.PIN])
    if (destination / '.git/objects/info/alternates').exists():
        raise ValueError('Replay checkout unexpectedly depends on another object store')
    validate(receipt, expected_sha256)
    command([str(ROOT / 'apply.sh'), str(destination)], 120)
    result = stack.verify(destination)
    if result != saved['verification']:
        raise ValueError('Reproduced verification differs from receipt')
    return {'schema': SCHEMA, 'receipt_sha256': expected_sha256,
            'checkout': str(destination), 'acquisition_source': str(source),
            'nonshared': True, 'verification': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('record')
    create.add_argument('target')
    create.add_argument('output')
    repeat = commands.add_parser('replay')
    repeat.add_argument('receipt')
    repeat.add_argument('--sha256', required=True)
    repeat.add_argument('--source', required=True)
    repeat.add_argument('--destination', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'record':
            result = record(args.target, args.output)
        else:
            result = replay(args.receipt, args.sha256, args.source, args.destination)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, stack.Failure, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}, sort_keys=True))
        return 1


if __name__ == '__main__':
    sys.exit(main())

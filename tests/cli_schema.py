#!/usr/bin/env python3
"""Validate published draft 2020-12 contracts and reject corrupted payloads."""
import copy
import types
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stack import Failure

SCHEMA = json.loads((ROOT / 'spec/cli-v1.schema.json').read_text())
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA)


def validate(doc):
    VALIDATOR.validate(doc)


def reject(doc):
    try:
        validate(doc)
    except ValidationError:
        return
    raise AssertionError(('accepted malformed response', doc))


def main():
    package = types.ModuleType("accretion")
    package.__path__ = [str(ROOT / "accretion")]
    sys.modules["accretion"] = package
    import b3nd12 as cli
    for command, values in [('help', []), ('quick', []), ('version', []), ('guide', []),
                            ('task', ['implement']), ('doctor', [])]:
        doc = dict(schema='b3nd12.cli.v1', ok=True,
                   command=[] if command == 'quick' else [command, *values], corrected=False,
                   result=cli.execute(command, values), error=None, exit_code=0)
        validate(doc)
        for key in doc:
            altered = copy.deepcopy(doc)
            del altered[key]
            reject(altered)
        for key in doc['result']:
            altered = copy.deepcopy(doc)
            del altered['result'][key]
            reject(altered)
            altered = copy.deepcopy(doc)
            altered['result'][key] = False
            reject(altered)
        altered = copy.deepcopy(doc)
        altered['result']['unexpected'] = 1
        reject(altered)
        altered = copy.deepcopy(doc)
        altered['command'] = ['unknown']
        reject(altered)
    error = dict(schema='b3nd12.cli.v1', ok=False, command=None, corrected=False,
                 result=None, exit_code=2, error=dict(code='INVALID_TASK', message='Unknown task',
                 context={}, correction='Use task prove.', examples=[]))
    validate(error)
    for key in error['error']:
        altered = copy.deepcopy(error)
        del altered['error'][key]
        reject(altered)
    for location, value in [('schema', 'other'), ('ok', True), ('exit_code', 0),
                            ('exit_code', 6), ('result', {}), ('corrected', 'yes'),
                            ('command', [1])]:
        altered = copy.deepcopy(error)
        altered[location] = value
        reject(altered)
    for location, value in [('examples', ['a', 'b', 'c']), ('examples', [1]),
                            ('context', []), ('unexpected', 'field')]:
        altered = copy.deepcopy(error)
        altered['error'][location] = value
        reject(altered)
    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        (root / 'accretion').mkdir()
        routes = root / 'accretion/routes.json'
        routes.write_text('{broken')
        with patch.object(cli, 'ROOT', root):
            for task, code, status in [('wrong', 'INVALID_TASK', 2), ('prove', 'ROUTING_CONFIGURATION', 3)]:
                try:
                    cli.execute('task', [task])
                except Failure as exc:
                    assert exc.error['code'] == code and exc.status == status
                else:
                    raise AssertionError(task)
        (root / 'guide/agent').mkdir(parents=True)
        (root / 'guide/agent/PROVE.md').write_text('expected proof guide')
        routes.write_text('{"prove": "PROGRAM.md"}')
        with patch.object(cli, 'ROOT', root):
            try:
                cli.execute('task', ['prove'])
            except Failure as exc:
                assert exc.error['code'] == 'ROUTING_CONFIGURATION' and exc.status == 3
            else:
                raise AssertionError('wrong route content accepted')
        assert cli.probe_tool('bun', None)['status'] == 'missing'
        assert cli.probe_tool('bun', str(root / 'nonexistent'))['status'] == 'broken'
        noisy = root / 'noisy'
        noisy.write_text('#!' + sys.executable + '\nimport sys\nsys.stdout.write("x" * 131072)\n')
        noisy.chmod(0o755)
        probe = cli.probe_tool('bun', str(noisy))
        assert probe['status'] == 'broken' and 'output limit' in probe['detail'], probe
        installer = root / 'apply.sh'
        installer.write_text('#!' + sys.executable + '\nimport sys\nsys.stdout.write("x" * 1048577)\n')
        installer.chmod(0o755)
        with patch.object(cli, 'ROOT', root), patch.object(cli, 'target_check', return_value=root), \
             patch.object(cli, 'patch_files'):
            try:
                cli.execute('apply', [str(root)])
            except Failure as exc:
                assert exc.error['code'] == 'INSTALL_OUTPUT_LIMIT' and exc.status == 4
                context = exc.error['context']
                assert context['limit_bytes'] == 1048576 and context['observed_bytes'] > 1048576
                assert len(context['stdout']) + len(context['stderr']) <= 1048576
                assert installer.exists(), 'output refusal removed caller state'
            else:
                raise AssertionError('noisy installer accepted')
        for body, expected in [('exit 1', 'broken'), ('printf 1.4.2', 'incompatible'),
                               ('sleep 3', 'timeout')]:
            fake = root / 'bun'
            fake.write_text('#!/bin/sh\n' + body + '\n')
            fake.chmod(0o755)
            assert cli.probe_tool('bun', str(fake))['status'] == expected
    print('PASS full JSON Schema validation, malformed results, routing errors and runtime probes')


if __name__ == '__main__':
    main()

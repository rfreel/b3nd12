#!/usr/bin/env python3
"""Bounded parser corpus, real terminals, classification parity and path identity."""
import ast
import contextlib
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import b3nd12 as cli
from stack import PIN, Failure
from cli_schema import validate

CLI_FILE = ROOT / 'b3nd12.py'


def invoke(args, *, cwd=None, env=None):
    return subprocess.run([sys.executable, str(CLI_FILE), *args],
                          cwd=cwd, env={**(os.environ if env is None else env), 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True, timeout=30)


def parser_corpus():
    literals = ['plain', 'with spaces', '文档', 'line\nbreak', 'trailing\n', '--json', '-target', '..', 'a;b']
    count = 0
    for command, canonical in [('doctor', 'doctor'), ('status', 'doctor'), ('check', 'verify'),
                               ('verify', 'verify'), ('guide', 'guide'), ('task', 'task')]:
        variants = {command, command.upper(), command.title(), '_'.join(command), '-'.join(command)}
        values = ['literal'] if canonical in ('verify', 'task') else []
        for variant, output in itertools.product(sorted(variants), ['--json', '--human']):
            got = cli.parse([variant, output, *values])
            assert got[0] == canonical and got[1] == values
            again = cli.parse([*got[3], output])
            assert again[0:2] == got[0:2] and not again[4]
            count += 1
    for command, literal, output in itertools.product(['apply', 'verify'], literals, ['--json', '--human']):
        got = cli.parse([command, output, '--', literal])
        assert got[0] == command and got[1] == [literal] and got[3] == [command, literal]
        # The published command array is semantic. Reinsert the operand separator for replay.
        replay = cli.parse([got[3][0], output, '--', *got[3][1:]])
        assert replay[0:2] == got[0:2] and replay[3] == got[3] and not replay[4]
        count += 1
    for spelling in ['Apply', 'APPLY', 'a_p_p_l_y', 'a-p-p-l-y', 'aply', 'apply-now']:
        with patch.object(sys, 'argv', ['b3nd12.py', spelling, '--json', '/somewhere']), \
             patch.object(cli, 'execute') as execute, contextlib.redirect_stdout(io.StringIO()):
            assert cli.main() == 2
            execute.assert_not_called()
        count += 1
    print('PASS parser corpus:', count, 'cases')


def terminal(args):
    master, slave = pty.openpty()
    proc = subprocess.Popen([sys.executable, str(CLI_FILE), *args],
                            stdout=slave, stderr=subprocess.PIPE, start_new_session=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    os.close(slave)
    output = bytearray()
    deadline = time.monotonic() + 30
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(args)
            ready, _, _ = select.select([master], [], [], remaining)
            if not ready:
                raise TimeoutError(args)
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            output.extend(chunk)
        _, error = proc.communicate(timeout=max(0.1, deadline - time.monotonic()))
        return proc.returncode, output.decode().replace('\r\n', '\n'), error.decode()
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        os.close(master)


def snapshot(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            result[relative] = ('link', os.readlink(path))
        elif path.is_file():
            result[relative] = (path.stat().st_mode & 0o7777, hashlib.sha256(path.read_bytes()).hexdigest())
    return result


def parity(args, status, code, *, env=None):
    machine = invoke([*args, '--json'], env=env)
    human = invoke([*args, '--human'], env=env)
    assert machine.returncode == human.returncode == status, (args, machine, human)
    doc = json.loads(machine.stdout)
    validate(doc)
    assert machine.stderr == '' and human.stdout == ''
    assert doc['error']['code'] == code and human.stderr.startswith(code + ': ')


def classification():
    parity(['verify', '/no-such-b3nd12-target'], 1, 'NOT_FOUND')
    parity(['Apply', '/unused'], 2, 'INVALID_COMMAND')
    parity(['task'], 2, 'INVALID_ARGUMENTS')
    parity(['task', 'missing'], 2, 'INVALID_TASK')
    parity(['doctor'], 3, 'MISSING_TOOL', env={**os.environ, 'PATH': '/nonexistent'})
    # Synthetic classifications exercise the renderer without claiming a real external failure.
    classifications = {
        1: ['NOT_FOUND'],
        2: ['INVALID_TARGET', 'AMBIGUOUS_FORMAT', 'INVALID_ARGUMENTS', 'INVALID_COMMAND', 'INVALID_TASK'],
        3: ['GIT_OUTPUT_LIMIT', 'GIT_TIMEOUT', 'GIT_FAILED', 'GIT_ENVIRONMENT', 'GIT_CONFIGURATION', 'GIT_ATTRIBUTES',
            'FILESYSTEM_OBSTRUCTION', 'WRONG_PIN', 'DIRTY_TARGET', 'ROUTING_CONFIGURATION',
            'MISSING_TOOL', 'BROKEN_TOOL', 'CONFIGURATION'],
        4: ['INSTALL_TIMEOUT', 'INSTALL_OUTPUT_LIMIT'],
        5: ['BINARY_PATCH', 'DELIVERY_MANIFEST', 'PATCH_SEQUENCE', 'FILE_SCOPE', 'FILE_MODE', 'CONTENT_MISMATCH',
            'THEORY_CHANGED', 'STAGED_INDEX', 'INSTALL_FAILED', 'INTERNAL'],
    }
    declared = {code for codes in classifications.values() for code in codes}
    observed = set()
    for source in ['b3nd12.py', 'stack.py']:
        for node in ast.walk(ast.parse((ROOT / source).read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Failure':
                first = node.args[0]
                candidates = [first.body, first.orelse] if isinstance(first, ast.IfExp) else [first]
                observed.update(n.value for n in candidates if isinstance(n, ast.Constant))
    assert observed == declared, ('error-family fixture needs review', observed ^ declared)
    for status, code in [(status, code) for status, codes in classifications.items() for code in codes]:
        rendered = []
        for mode in ['--json', '--human']:
            out, err = io.StringIO(), io.StringIO()
            with patch.object(sys, 'argv', ['b3nd12.py', 'doctor', mode]), \
                 patch.object(cli, 'execute', side_effect=Failure(code, 'controlled failure', 'retry safely', status)), \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                assert cli.main() == status
            rendered.append((out.getvalue(), err.getvalue()))
        doc = json.loads(rendered[0][0])
        validate(doc)
        assert doc['error']['code'] == code and rendered[0][1] == ''
        assert rendered[1][0] == '' and rendered[1][1].startswith(code + ': ')


def main():
    global CLI_FILE
    parser_corpus()
    classification()
    with tempfile.TemporaryDirectory(prefix='b3nd12-paths-') as directory:
        base = Path(directory)
        management = base / 'management'
        shutil.copytree(ROOT, management, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        CLI_FILE = management / 'b3nd12.py'
        target = base / '-文档 checkout\n'
        subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(Path(sys.argv[1]).resolve()), str(target)],
                       check=True, capture_output=True, timeout=30)
        subprocess.run(['git', '-C', str(target), 'checkout', '--detach', PIN], check=True, capture_output=True, timeout=30)
        parity(['verify', str(target)], 5, 'FILE_SCOPE')
        installed = invoke(['apply', '--json', '--', str(target)])
        assert installed.returncode == 0, installed
        validate(json.loads(installed.stdout))
        alias = base / 'symbolic checkout'
        alias.symlink_to(target, target_is_directory=True)
        routes = management / 'accretion/routes.json'
        saved_routes = routes.read_bytes()
        try:
            routes.write_bytes(b'{broken')
            parity(['task', 'prove'], 3, 'ROUTING_CONFIGURATION')
        finally:
            routes.write_bytes(saved_routes)
        before = snapshot(target)
        management_before = snapshot(management)
        for literal in [str(target), str(alias), target.name]:
            for mode in ['--json', '--human']:
                result = invoke(['verify', mode, '--', literal], cwd=base)
                assert result.returncode == 0, result
                parsed = json.loads(result.stdout)
                body = parsed['result'] if mode == '--json' else parsed
                assert body['target'] == str(target.resolve())
                if mode == '--json':
                    validate(parsed)
        parity(['verify', str(target / 'guide')], 2, 'INVALID_TARGET')
        commands = [[], ['help'], ['version'], ['doctor'], ['guide'], ['guide', 'program'],
                    ['guide', 'prove'], ['task', 'implement'], ['task', 'prove'],
                    ['task', 'diagnose'], ['verify', str(target)]]
        for args in commands:
            pipe = invoke(args)
            assert pipe.returncode == 0 and pipe.stderr == ''
            validate(json.loads(pipe.stdout))
            for override in [[], ['--json'], ['--human']]:
                status, output, error = terminal([*args, *override])
                assert status == 0 and error == '', (args, output, error)
                if override == ['--json']:
                    validate(json.loads(output))
                else:
                    assert not output.startswith('{"schema"')
        for args, code in [(['task', 'unknown'], 'INVALID_TASK'), (['guide', 'unknown'], 'NOT_FOUND')]:
            for override in [[], ['--human'], ['--json']]:
                status, output, error = terminal([*args, *override])
                assert status in (1, 2)
                if override == ['--json']:
                    doc = json.loads(output)
                    validate(doc)
                    assert doc['error']['code'] == code and error == ''
                else:
                    assert output == '' and error.startswith(code + ': ')
        assert snapshot(target) == before, 'read-only commands changed files, modes or Git control state'
        assert snapshot(management) == management_before, 'read-only commands changed management state'
    print('PASS real PTY/pipe/override parity, target snapshots and hostile path round trips')


if __name__ == '__main__':
    main()

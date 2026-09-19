#!/usr/bin/env python3
"""Disposable installation boundary and patch-mutation checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / 'upstream.json').read_text())['commit']


def run(*args, cwd=None, env=None, ok=True):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    if ok and result.returncode:
        raise AssertionError((args, result.stdout, result.stderr))
    return result


def snapshot(target):
    result = {}
    for path in target.rglob('*'):
        relative = path.relative_to(target)
        if relative.parts[0] == '.git':
            continue
        if path.is_symlink():
            result[str(relative)] = ('link', os.readlink(path))
        elif path.is_file():
            result[str(relative)] = (path.stat().st_mode, path.read_bytes())
        else:
            result[str(relative)] = ('dir', path.stat().st_mode)
    index = Path(run('git', 'rev-parse', '--git-path', 'index', cwd=target).stdout.rstrip('\n'))
    if not index.is_absolute():
        index = target / index
    return result, index.read_bytes()


def main():
    source = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='b3nd12-adversarial-') as temporary:
        tmp = Path(temporary)
        serial = 0

        def clone():
            nonlocal serial
            serial += 1
            target = tmp / f'checkout-{serial}'
            run('git', 'clone', '--no-local', '--no-checkout', str(source), str(target))
            run('git', 'checkout', '--detach', PIN, cwd=target)
            assert not (target / '.git/objects/info/alternates').exists()
            return target

        def refuse(target, code, installer=ROOT, env=None):
            before = snapshot(target)
            result = run(str(installer / 'apply.sh'), str(target), env=env, ok=False)
            assert result.returncode != 0 and code in result.stderr, (code, result.stdout, result.stderr)
            assert snapshot(target) == before, 'Refused installation changed worktree/index'

        for kind in ('ignored-file', 'symlink-parent', 'inaccessible'):
            target = clone()
            (target / '.git/info/exclude').write_text('guide/agent\n')
            if kind == 'ignored-file':
                (target / 'guide/agent').mkdir()
                (target / 'guide/agent/PROGRAM.md').write_text('caller content')
            elif kind == 'symlink-parent':
                outside = tmp / 'outside'
                outside.mkdir()
                (outside / 'sentinel').write_text('preserve me')
                (target / 'guide/agent').symlink_to(outside, target_is_directory=True)
            else:
                (target / 'guide').chmod(0o500)
            refuse(target, 'path:' if kind == 'ignored-file' else 'parent:')
            if kind == 'symlink-parent':
                assert sorted(p.name for p in outside.iterdir()) == ['sentinel']
            if kind == 'inaccessible':
                (target / 'guide').chmod(0o755)
        print('PASS ignored collisions, symlink parents and inaccessible directories refused unchanged')

        target = clone()
        for variable in ('GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE'):
            external = tmp / ('external-' + variable)
            external.write_text('caller content')
            refuse(target, 'Unsupported Git environment', env={**os.environ, variable: str(external)})
            assert external.read_text() == 'caller content'
        attrs = target / '.git/info/attributes'
        attrs.write_text('AGENTS.md filter=sentinel\n')
        # This command is never executed: attribute inspection refuses first.
        run('git', 'config', 'filter.sentinel.clean', 'false', cwd=target)
        refuse(target, 'Unsupported Git attribute')
        attrs.write_text('AGENTS.md working-tree-encoding=UTF-16\n')
        refuse(target, 'Unsupported Git attribute')
        attrs.unlink()
        run('git', 'config', 'core.autocrlf', 'true', cwd=target)
        refuse(target, 'Unsupported Git configuration')
        run('git', 'config', 'core.autocrlf', 'false', cwd=target)
        print('PASS Git environment, active filter, encoding and newline conversion refusals')

        installer = tmp / 'installer'
        shutil.copytree(ROOT, installer, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        last = next((installer / 'patches').glob('09-*.patch'))
        saved = last.read_bytes()
        fixtures = {
            'path-escape': 'diff --git a/../outside b/../outside\nnew file mode 100644\n--- /dev/null\n+++ b/../outside\n@@ -0,0 +1 @@\n+escape\n',
            'binary': 'diff --git a/extra.bin b/extra.bin\nnew file mode 100644\nGIT binary patch\nliteral 1\nIcmZPo000310RR91\n\nliteral 0\nHcmV?d00001\n',
            'symlink': 'diff --git a/unwanted b/unwanted\nnew file mode 120000\n--- /dev/null\n+++ b/unwanted\n@@ -0,0 +1 @@\n+AGENTS.md\n',
            'out-of-scope': 'diff --git a/unwanted b/unwanted\nnew file mode 100644\n--- /dev/null\n+++ b/unwanted\n@@ -0,0 +1 @@\n+unwanted\n',
        }
        binary = tmp / 'extra.bin'
        binary.write_bytes(bytes(range(256)))
        binary_diff = run('git', 'diff', '--no-index', '--binary', '/dev/null', str(binary), ok=False)
        assert binary_diff.returncode == 1 and 'GIT binary patch' in binary_diff.stdout
        fixtures['valid-binary'] = binary_diff.stdout.replace(str(binary).lstrip('/'), 'extra.bin')
        readme = run('git', 'show', 'HEAD:README.md', cwd=target).stdout.splitlines()
        fixtures['deletion'] = ('diff --git a/README.md b/README.md\ndeleted file mode 100644\n--- a/README.md\n+++ /dev/null\n@@ -1,' + str(len(readme)) + ' +0,0 @@\n' + ''.join('-' + line + '\n' for line in readme))
        for name, mutation in fixtures.items():
            last.write_bytes(saved + mutation.encode())
            refuse(target, '', installer=installer)
        last.write_bytes(saved)
        duplicate = installer / 'patches/09-duplicate.patch'
        duplicate.write_bytes(saved)
        refuse(target, 'rank 1 through 9', installer=installer)
        duplicate.unlink()
        print('PASS path escape, binary, symlink, deletion, extra path and duplicate rank refused before writes')

        run('git', 'remote', 'set-url', 'origin', str(tmp / 'unavailable-source'), cwd=target)
        run('git', 'fsck', '--full', cwd=target)
        run(str(ROOT / 'apply.sh'), str(target))
        run(sys.executable, str(ROOT / 'stack.py'), str(target))
        print(f'PASS independent nonshared clone install: source={source}, pin={PIN}, no alternates')
        linked = tmp / 'linked'
        run('git', 'worktree', 'add', '--detach', str(linked), PIN, cwd=target)
        before = snapshot(target)
        run(str(ROOT / 'apply.sh'), str(linked))
        run(sys.executable, str(ROOT / 'stack.py'), str(linked))
        assert snapshot(target) == before
        print('PASS linked worktree install does not change sibling worktree or index')


if __name__ == '__main__':
    main()

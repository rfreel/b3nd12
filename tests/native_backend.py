#!/usr/bin/env python3
"""Check the frozen sum and a bounded Nat corpus with an explicit native compiler."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'accretion'))
import bounded
from run import validate_compiler
from spec_twin import check_seal

PAIRS = ((0, 0), (0, 7), (1, 5), (2, 3), (3, 11), (4, 1), (5, 9), (6, 2))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bend', type=Path)
    parser.add_argument('bun', type=Path)
    parser.add_argument('cc', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bend, bun, cc, output = (p.resolve() for p in (args.bend, args.bun, args.cc, args.output))
    assert output != ROOT and ROOT not in output.parents, 'evidence must be outside repository'
    validate_compiler(bend)
    output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'CC': str(cc), 'BEND_NO_TELEMETRY': '1'}
    report = {'schema': 'b3nd12.native-test.v1', 'pairs': PAIRS, 'commands': [],
              'tools': {}, 'cases': [], 'status': 'incomplete',
              'test_sha256': digest(__file__),
              'upstream': json.loads((ROOT / 'upstream.json').read_text())['commit'],
              'compiler_sha256': {name: digest(bend / name) for name in
                                  ('bend2/bend.ts', 'bend2/base.bend', 'bend2/main.ts', 'bend2/comp.ts')},
              'limits': 'Bounded Nat corpus only; CPU evidence, no GPU or performance claim.'}

    def save():
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

    def invoke(command, expected=None, timeout=120):
        command = list(map(str, command))
        try:
            result = bounded.run(command, env=env, text=True, timeout=timeout)
        except BaseException as error:
            report['commands'].append({'command': command, 'exit': None,
                                       'error': type(error).__name__, 'message': str(error),
                                       'stdout': str(getattr(error, 'stdout', '') or ''),
                                       'stderr': str(getattr(error, 'stderr', '') or '')})
            save()
            raise
        report['commands'].append({'command': command, 'exit': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        save()
        assert result.returncode == 0, report['commands'][-1]
        if expected is not None:
            assert result.stdout == expected and not result.stderr, report['commands'][-1]
        return result.stdout

    frozen = ROOT / 'examples/frozen-spec-twin'
    before = {p.name: digest(p) for p in frozen.iterdir() if p.is_file()}
    report['frozen_sha256'] = before
    try:
        for name, tool in [('bun', bun), ('clang', cc)]:
            report['tools'][name] = {'path': str(tool), 'sha256': digest(tool),
                                     'version': invoke([tool, '--version'])}
        linker_name = invoke([cc, '-print-prog-name=ld']).strip()
        linker = Path(shutil.which(linker_name) or linker_name).resolve()
        report['tools']['linker'] = {'path': str(linker), 'sha256': digest(linker),
                                     'version': invoke([linker, '--version'])}
        seal = json.loads((frozen / 'SEAL.txt').read_text())
        official = bounded.check_output(['git', '-C', str(bend), 'show',
                                         seal['upstream'] + ':demos/pure_par_sum/main.bend'])
        source = (frozen / 'main.bend').read_bytes()
        check_seal(source, (frozen / 'LAWS.bend').read_bytes(),
                   (frozen / 'PROOF.bend').read_bytes(), seal, official)
        book = output / 'book'
        book.mkdir()
        for name in ('main.bend', 'LAWS.bend', 'PROOF.bend'):
            shutil.copyfile(frozen / name, book / name)
        cli = [bun, bend / 'bend2/main.ts']
        invoke([*cli, book / 'PROOF.bend'], 'All terms check.\n')
        native = book / 'sum'
        invoke([*cli, book / 'main.bend', '-o', native])
        report['frozen_binary_sha256'] = digest(native)
        for threads in (1, 4):
            invoke([native, '--threads', str(threads)], '2147450880\n')

        # Preserve every spec definition. Only disposable main entry points vary.
        definitions = source[:source.index(b'def main(')]
        corpus = output / 'corpus'
        corpus.mkdir()
        for d, i in PAIRS:
            n = 2 ** d
            expected = n * (2 * i + n - 1) // 2
            for function, first in [('sum', d), ('seq', n)]:
                path = corpus / f'{function}-{d}-{i}.bend'
                path.write_bytes(definitions +
                                 f'def main() -> Nat:\n  {function}({first}n, {i}n)\n'.encode())
                source_hash = digest(path)
                observed = invoke([*cli, path], f'{expected}n\n')
                js = path.with_suffix('.js')
                binary = path.with_suffix('.native')
                invoke([*cli, path, '-o', js])
                invoke([bun, js], observed)
                invoke([*cli, path, '-o', binary])
                invoke([binary, '--threads', '1'], observed)
                assert digest(path) == source_hash
                report['cases'].append({'d': d, 'i': i, 'function': function,
                                        'expected': expected, 'source_sha256': source_hash,
                                        'js_sha256': digest(js), 'binary_sha256': digest(binary),
                                        'backends': ['interpreter', 'javascript', 'native']})
                save()
        report['status'] = 'pass'
    except BaseException as error:
        report['status'] = 'failed'
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        after = {p.name: digest(p) for p in frozen.iterdir() if p.is_file()}
        report['frozen_unchanged'] = before == after
        report['compiler_unchanged'] = all(digest(bend / name) == value
                                           for name, value in report['compiler_sha256'].items())
        if not report['frozen_unchanged'] or not report['compiler_unchanged']:
            report['status'] = 'failed'
        save()
        assert before == after, 'frozen example changed'
        assert report['compiler_unchanged'], 'compiler sources changed'
    print('PASS frozen CPU sum at 1/4 threads; 16 Nat programs agree across three backends')


if __name__ == '__main__':
    main()

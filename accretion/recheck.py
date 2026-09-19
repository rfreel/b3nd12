#!/usr/bin/env python3
"""Rebuild accepted finite books from a verified packet without executing its snapshots."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

from environment import ROOT
from run import sha, validate_compiler
from verify_evidence import verify
import bounded


def recheck(directory, terminal_sha256, contract_sha256, bun, bend):
    directory, bun, bend = (Path(path).resolve() for path in (directory, bun, bend))
    # The externally supplied terminal digest is required, never inferred from the packet.
    summary = verify(directory, terminal_sha256, contract_sha256)
    validate_compiler(bend)
    manifest = json.loads((directory / 'manifest.json').read_bytes())
    if sha(bun.read_bytes()) != manifest['bun_sha256']:
        raise ValueError('Bun binary differs from recorded evaluator')
    contract = json.loads((directory / 'TODO.json').read_bytes())
    sources = {}
    for name in ('LAWS.bend', 'PROOF.bend'):
        sources[name] = (ROOT / 'accretion' / name).read_bytes()
        if sha(sources[name]) != contract['protected']['accretion/' + name]:
            raise ValueError('local frozen book differs from contract: ' + name)
    certificates = []
    with tempfile.TemporaryDirectory(prefix='b3nd12-recheck-') as temporary:
        book = Path(temporary)
        for name, raw in sources.items():
            (book / name).write_bytes(raw)
        for receipt_path in sorted(directory.glob('pass-*/receipt.json')):
            receipt = json.loads(receipt_path.read_bytes())
            for index, sample in enumerate(receipt['samples']):
                if not sample['accepted']:
                    continue
                values = sample['metrics']
                # Fixed key order reconstructs the exact original source bytes.
                lines = ['import Base\n']
                for key in ('preserved', 'no_regressions', 'before', 'after', 'candidate_bytes'):
                    value = values[key]
                    typ = 'Bool' if type(value) is bool else 'Nat'
                    term = ('True{}' if value else 'False{}') if type(value) is bool else str(value) + 'n'
                    lines.append(f'def {key}() -> {typ}:\n  {term}\n')
                evidence = '\n'.join(lines).encode()
                reconstructed = {**sources, 'Evidence.bend': evidence}
                hashes = {name: sha(raw) for name, raw in reconstructed.items()}
                if hashes != sample['book_sha256']:
                    raise ValueError('reconstructed book hashes differ from observation')
                (book / 'Evidence.bend').write_bytes(evidence)
                command = [str(bun), str(bend / 'bend2/main.ts'), str(book / 'PROOF.bend')]
                result = bounded.run(command, env={**os.environ, 'BEND_NO_TELEMETRY': '1'},
                                     capture_output=True, text=True, timeout=15)
                if result.returncode != 0 or result.stdout != 'All terms check.\n' or result.stderr:
                    raise ValueError('reconstructed book did not check: ' + str(receipt_path))
                certificates.append({'attempt': receipt['attempt'], 'sample': index,
                                     'book_sha256': hashes, 'stdout': result.stdout})
    return {'schema': 'b3nd12.recheck.v1', 'terminal_sha256': terminal_sha256,
            'contract_sha256': contract_sha256, 'certificates': certificates,
            'stop': summary['stop'], 'scope': 'accepted finite books; snapshots are data only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--terminal-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--bun', required=True, type=Path)
    parser.add_argument('--bend-root', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = recheck(args.directory, args.terminal_sha256, args.contract_sha256, args.bun, args.bend_root)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'schema': 'b3nd12.recheck.v1', 'error': str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Export or import bounded evidence ZIPs verified against retained digests."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

from verify_evidence import verify

ROOT = Path(__file__).resolve().parents[1]
MAX_FILES = 128
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_BYTES = 40 * 1024 * 1024


def check(condition, message):
    if not condition:
        raise ValueError(message)


def destination(path):
    path = Path(path).absolute()
    check(not path.resolve().is_relative_to(ROOT.resolve()), 'destination must be outside repository')
    check(not path.exists() and not path.is_symlink(), 'destination already exists')
    check(path.parent.is_dir(), 'destination parent must exist')
    return path


def valid_name(name):
    path = PurePosixPath(name)
    check(name and '\\' not in name and not path.is_absolute() and
          all(part not in {'', '.', '..'} for part in name.split('/')) and
          ':' not in name and '\x00' not in name, 'unsafe archive path')
    return name


def unpack(archive, workspace):
    check(archive.stat().st_size <= MAX_ARCHIVE_BYTES, 'archive exceeds byte bound')
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        check(len(members) <= MAX_FILES, 'archive exceeds file bound')
        names, total = set(), 0
        for member in members:
            name = valid_name(member.filename)
            check(name not in names, 'duplicate archive member')
            names.add(name)
            mode = member.external_attr >> 16
            check(not member.is_dir() and stat.S_IFMT(mode) in {0, stat.S_IFREG}, 'nonregular archive member')
            check(not member.flag_bits & 1, 'encrypted archive refused')
            check(member.compress_type == zipfile.ZIP_STORED, 'compressed archive refused')
            check(member.file_size <= MAX_FILE_BYTES, 'member exceeds byte bound')
            total += member.file_size
            check(total <= MAX_TOTAL_BYTES, 'archive exceeds expanded byte bound')
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, target.open('xb') as output:
                count = 0
                while True:
                    block = source.read(min(65536, MAX_FILE_BYTES - count + 1))
                    if not block:
                        break
                    count += len(block)
                    check(count <= member.file_size and count <= MAX_FILE_BYTES, 'member expanded beyond bound')
                    output.write(block)
                check(count == member.file_size, 'truncated member')



def verify_bundle(workspace, terminal, contract):
    summary = verify(workspace, terminal, contract)
    manifest = json.loads((workspace / 'manifest.json').read_bytes())
    allowed = {'TODO.json', 'manifest.json', 'ledger.jsonl', 'final.json', 'summary.json', 'successor.json'}
    allowed.update('inputs/' + name for name in manifest['inputs'])
    for packet in workspace.glob('pass-*'):
        allowed.update(packet.name + '/' + name for name in ('before.json', 'candidate.json', 'receipt.json'))
    actual = {p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file()}
    check(actual <= allowed, 'unexpected evidence artifact')
    return summary


def export_bundle(source, output, terminal, contract):
    output = destination(output)
    source = Path(source).resolve()
    # Copy bounded plain files first; verification and packaging use the same snapshot.
    with tempfile.TemporaryDirectory(prefix='.b3nd12-export-', dir=output.parent) as tmp:
        workspace = Path(tmp) / 'evidence'
        workspace.mkdir()
        files, total, entries = [], 0, 0
        for parent, dirs, names in os.walk(source, followlinks=False):
            entries += len(dirs) + len(names)
            check(entries <= MAX_FILES * 2, 'source exceeds entry bound')
            for name in dirs:
                check(not (Path(parent) / name).is_symlink(), 'source symlink refused')
            for name in names:
                path = Path(parent) / name
                check(stat.S_ISREG(path.lstat().st_mode), 'source nonregular file refused')
                relative = valid_name(path.relative_to(source).as_posix())
                files.append(relative)
                check(len(files) <= MAX_FILES, 'source exceeds file bound')
                with path.open('rb') as stream:
                    raw = stream.read(MAX_FILE_BYTES + 1)
                check(len(raw) <= MAX_FILE_BYTES, 'source file exceeds byte bound')
                total += len(raw)
                check(total <= MAX_TOTAL_BYTES, 'source exceeds total byte bound')
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        summary = verify_bundle(workspace, terminal, contract)
        temporary = Path(tmp) / 'bundle.zip'
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_STORED) as bundle:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                bundle.writestr(info, (workspace / name).read_bytes())
        check(temporary.stat().st_size <= MAX_ARCHIVE_BYTES, 'archive exceeds byte bound')
        # Link publication is atomic and refuses an existing destination.
        os.link(temporary, output)
    return summary


def import_bundle(archive, output, terminal, contract):
    output = destination(output)
    # Reserve the destination only after verification. mkdir supplies no-overwrite semantics.
    with tempfile.TemporaryDirectory(prefix='.b3nd12-import-', dir=output.parent) as tmp:
        workspace = Path(tmp) / 'evidence'
        workspace.mkdir()
        unpack(Path(archive), workspace)
        summary = verify_bundle(workspace, terminal, contract)
        output.mkdir()
        try:
            for path in sorted(workspace.iterdir()):
                shutil.move(str(path), output / path.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['export', 'import'])
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--terminal-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    try:
        action = export_bundle if args.operation == 'export' else import_bundle
        summary = action(args.source, args.destination, args.terminal_sha256, args.contract_sha256)
        print(json.dumps({'verified': True, 'summary': summary}))
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({'verified': False, 'error': str(exc)}))
        raise SystemExit(1)

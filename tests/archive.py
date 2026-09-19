#!/usr/bin/env python3
"""Exercise retained-digest archive round trips and hostile archive metadata."""
import json
from pathlib import Path
import stat
import sys
import tempfile
import warnings
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
import archive
from program import replay
from verify_evidence import sha, verify

bend, bun = (Path(p).resolve() for p in sys.argv[1:3])
contract = sha((ROOT / 'accretion/TODO.json').read_bytes())
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / 'source'
    expected = replay(source, contract, bun, bend)
    terminal = json.loads((source / 'ledger.jsonl').read_text().splitlines()[-1])['sha256']
    first, second = root / 'first.zip', root / 'second.zip'
    assert archive.export_bundle(source, first, terminal, contract) == expected
    archive.export_bundle(source, second, terminal, contract)
    assert first.read_bytes() == second.read_bytes(), 'archive not deterministic'
    destination = root / 'imported'
    assert archive.import_bundle(first, destination, terminal, contract) == expected
    assert verify(destination, terminal, contract) == expected
    original = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    restored = {p.relative_to(destination): p.read_bytes() for p in destination.rglob('*') if p.is_file()}
    assert original == restored

    def refused(label, source_archive, **kwargs):
        output = root / label
        try:
            archive.import_bundle(source_archive, output, kwargs.get('terminal', terminal), contract)
        except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile):
            assert not output.exists(), 'failed validation published output'
        else:
            raise AssertionError('accepted hostile archive: ' + label)

    refused('bad-seal', first, terminal='0' * 64)
    with patch.object(archive, 'MAX_ARCHIVE_BYTES', 1):
        refused('size', first)
    with patch.object(archive, 'MAX_FILES', 1):
        refused('count', first)
    with patch.object(archive, 'MAX_FILE_BYTES', 1):
        refused('member-size', first)
    with patch.object(archive, 'MAX_TOTAL_BYTES', 1):
        refused('total-size', first)
    for label, names, mode, compression in [
        ('traversal', ['../escape'], stat.S_IFREG, zipfile.ZIP_STORED),
        ('absolute', ['/escape'], stat.S_IFREG, zipfile.ZIP_STORED),
        ('windows', ['C:\\escape'], stat.S_IFREG, zipfile.ZIP_STORED),
        ('duplicate', ['same', 'same'], stat.S_IFREG, zipfile.ZIP_STORED),
        ('symlink', ['link'], stat.S_IFLNK, zipfile.ZIP_STORED),
        ('device', ['device'], stat.S_IFCHR, zipfile.ZIP_STORED),
        ('compressed', ['bomb'], stat.S_IFREG, zipfile.ZIP_DEFLATED),
    ]:
        malicious = root / (label + '.zip')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(malicious, 'w') as bundle:
                for name in names:
                    info = zipfile.ZipInfo(name)
                    info.external_attr = (mode | 0o644) << 16
                    info.compress_type = compression
                    bundle.writestr(info, b'x' * 1000)
        refused(label, malicious)
    assert not (root / 'escape').exists()
    for action, supplied, output in [(archive.import_bundle, first, destination),
                                     (archive.export_bundle, source, first),
                                     (archive.import_bundle, first, ROOT / 'forbidden-evidence-import')]:
        try:
            action(supplied, output, terminal, contract)
        except ValueError:
            pass
        else:
            raise AssertionError('overwrite or repository destination accepted')
    (source / 'link').symlink_to('/etc/passwd')
    try:
        archive.export_bundle(source, root / 'unsafe.zip', terminal, contract)
    except ValueError:
        pass
    else:
        raise AssertionError('source symlink exported')
print('PASS deterministic exact archive round trip, retained seals, no overwrite, outside-repo output, bounds and hostile ZIP metadata refusal')

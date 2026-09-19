"""Publish complete evidence files with POSIX file and directory durability barriers."""
import errno
import os
from pathlib import Path
import tempfile

MAX_ARTIFACT_BYTES = 8 * 1024 * 1024


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def mkdir(path, *, parents=False, exist_ok=False):
    path = Path(path)
    if parents and not path.parent.exists():
        mkdir(path.parent, parents=True)
    try:
        path.mkdir()
    except FileExistsError:
        if not exist_ok or not path.is_dir():
            raise
    else:
        sync_directory(path.parent)


def write(path, data):
    """Replace one complete file; the caller owns a new, exclusive run directory."""
    if len(data) > MAX_ARTIFACT_BYTES:
        raise ValueError("evidence artifact exceeds 8 MiB write limit")
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        try:
            remaining = memoryview(data)
            while remaining:
                count = os.write(fd, remaining)
                if count <= 0:
                    raise OSError(errno.EIO, 'evidence write made no progress')
                remaining = remaining[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(name, path)
        sync_directory(path.parent)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass

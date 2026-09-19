#!/usr/bin/env python3
"""Run prepared local checks with inherited Linux network syscall denial.

This restricts this process and its descendants. It neither restricts other
agents nor provides filesystem or hostile-worker isolation.
"""
import ctypes
import errno
import os
import platform
import stat
import sys


# Linux x86_64 syscall numbers. Block named socket creation/connections,
# alternate asynchronous I/O, and importing another process's fd. Anonymous
# AF_UNIX pairs and recvfrom remain available for Bun subprocess streams.
DENIED = (41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 52, 54, 55,
          288, 299, 307, 425, 426, 427, 438)


class Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]


class Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]


def restrict():
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("offline checks require Linux x86_64")
    for fd in range(3):
        try:
            mode = os.fstat(fd).st_mode
        except OSError as exc:
            if exc.errno == errno.EBADF:
                continue
            raise
        if stat.S_ISSOCK(mode):
            raise RuntimeError("offline checks refuse socket-backed standard streams")
    # Enumerate open descriptors rather than assuming the current rlimit also
    # bounds descriptors opened before a caller lowered that limit.
    for name in os.listdir("/proc/self/fd"):
        fd = int(name)
        if fd > 2:
            try:
                os.close(fd)
            except OSError as exc:
                if exc.errno != errno.EBADF:
                    raise
    instructions = [
        Filter(0x20, 0, 0, 4),                 # seccomp_data.arch
        Filter(0x15, 1, 0, 0xC000003E),        # AUDIT_ARCH_X86_64
        Filter(0x06, 0, 0, 0x80000000),        # kill mismatched ABI
        Filter(0x20, 0, 0, 0),                 # seccomp_data.nr
        Filter(0x35, 0, 1, 0x40000000),        # reject x32 ABI
        Filter(0x06, 0, 0, 0x00050001),        # EPERM
        Filter(0x15, 0, 4, 53),               # socketpair only
        Filter(0x20, 0, 0, 16),               # args[0] domain
        Filter(0x15, 1, 0, 1),                # AF_UNIX
        Filter(0x06, 0, 0, 0x00050001),        # other domains: EPERM
        Filter(0x06, 0, 0, 0x7FFF0000),        # anonymous local IPC
    ]
    for number in DENIED:
        instructions.extend((Filter(0x15, 0, 1, number),
                             Filter(0x06, 0, 0, 0x00050001)))
    instructions.append(Filter(0x06, 0, 0, 0x7FFF0000))
    array = (Filter * len(instructions))(*instructions)
    program = Program(len(instructions), array)
    libc = ctypes.CDLL(None, use_errno=True)
    for option, value in ((38, 1), (22, 2)):
        argument = ctypes.byref(program) if option == 22 else 0
        if libc.prctl(option, value, argument, 0, 0) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code))


def main(argv):
    if not argv or argv[0] != "--" or len(argv) < 2:
        print("usage: python3 offline.py -- COMMAND [ARG ...]", file=sys.stderr)
        return 2
    try:
        restrict()
        os.execvp(argv[1], argv[1:])
    except (OSError, RuntimeError) as exc:
        print(f"offline checks refused: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

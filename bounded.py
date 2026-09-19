"""Bound a POSIX subprocess tree and retain its captured output on timeout."""
import argparse
import os
import selectors
import signal
import subprocess
import sys
import threading
import time

DEPTH_ENV = "B3ND12_BOUNDED_DEPTH"
MAX_DEPTH = 4


class Cancelled(BaseException):
    """Cooperative parent cancellation, propagated through nested wrappers."""


def cancellation(signum, frame):
    raise Cancelled()


class OutputLimitExceeded(subprocess.SubprocessError):
    def __init__(self, args, limit_bytes, observed_bytes, stdout, stderr):
        self.cmd, self.limit_bytes, self.observed_bytes = args, limit_bytes, observed_bytes
        self.stdout, self.stderr = stdout, stderr
        super().__init__(f"command output exceeded {limit_bytes} bytes; observed at least {observed_bytes}")


def run(args, *, timeout=15, env=None, cwd=None, text=False, capture_output=True,
        max_output_bytes=1048576):
    if not capture_output:
        raise ValueError("bounded processes require captured output")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if type(max_output_bytes) is not int or max_output_bytes <= 0:
        raise ValueError("output limit must be a positive integer")
    try:
        depth = int(os.environ.get(DEPTH_ENV, "0"))
    except ValueError:
        raise ValueError("invalid cooperative subprocess depth") from None
    if not 0 <= depth <= MAX_DEPTH:
        raise ValueError("cooperative subprocess nesting limit exceeded")
    child_env = dict(os.environ if env is None else env)
    child_env[DEPTH_ENV] = str(depth + 1)
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=child_env, cwd=cwd, start_new_session=True)
    previous_handler = None
    if threading.current_thread() is threading.main_thread():
        previous_handler = signal.signal(signal.SIGTERM, cancellation)
    streams = [bytearray(), bytearray()]
    observed = 0
    deadline = time.monotonic() + timeout

    def outputs():
        result = tuple(bytes(data) for data in streams)
        return tuple(data.decode('utf-8', errors='replace') for data in result) if text else result

    def terminate():
        try:
            # Inner wrappers get a shorter grace than their callers. Equal grace
            # periods let callers kill wrappers before their final child kill.
            # The finite depth cap makes this schedule explicit. This assumes
            # responsive cooperative wrappers, not hostile-process containment.
            os.killpg(child.pid, signal.SIGTERM)
            time.sleep((MAX_DEPTH - depth) * 0.25)
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    try:
        with selectors.DefaultSelector() as selector:
            for index, pipe in enumerate((child.stdout, child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, index)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    stdout, stderr = outputs()
                    raise subprocess.TimeoutExpired(args, timeout, output=stdout, stderr=stderr)
                for key, _ in selector.select(remaining):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    available = max_output_bytes - sum(map(len, streams))
                    streams[key.data].extend(data[:available])
                    observed += len(data)
                    if observed > max_output_bytes:
                        stdout, stderr = outputs()
                        raise OutputLimitExceeded(args, max_output_bytes, observed, stdout, stderr)
        try:
            child.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            stdout, stderr = outputs()
            raise subprocess.TimeoutExpired(args, timeout, output=stdout, stderr=stderr) from None
        stdout, stderr = outputs()
        return subprocess.CompletedProcess(args, child.returncode, stdout, stderr)
    finally:
        # On failure the unreaped parent still reserves its PID. Do not signal an
        # already reaped successful process ID, which the OS could have reused.
        if child.returncode is None:
            terminate()
        child.stdout.close()
        child.stderr.close()
        try:
            child.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        if previous_handler is not None:
            signal.signal(signal.SIGTERM, previous_handler)


def check_output(args, *, timeout=15, **kwargs):
    result = run(args, timeout=timeout, **kwargs)
    result.check_returncode()
    return result.stdout


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    try:
        result = run(command, timeout=args.timeout)
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
    except subprocess.TimeoutExpired as exc:
        sys.stdout.buffer.write(exc.stdout or b"")
        sys.stderr.buffer.write(exc.stderr or b"")
        print(f"bounded: command timed out after {exc.timeout:g} seconds", file=sys.stderr)
        raise SystemExit(124)
    except OutputLimitExceeded as exc:
        sys.stdout.buffer.write(exc.stdout)
        sys.stderr.buffer.write(exc.stderr)
        print("bounded: " + str(exc), file=sys.stderr)
        raise SystemExit(125)
    except OSError as exc:
        print("bounded: " + str(exc), file=sys.stderr)
        raise SystemExit(127)
    except Cancelled:
        raise SystemExit(143)

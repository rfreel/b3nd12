#!/usr/bin/env python3
"""Exercise actual descendant cleanup and timeout output retention."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bounded import run, check_output, OutputLimitExceeded

assert check_output([sys.executable, "-c", "print('ready')"], text=True) == "ready\n"
failed = run([sys.executable, "-c", "import sys; sys.exit(7)"])
assert failed.returncode == 7
try:
    run([sys.executable, '-c', "import os; os.write(1,b'x'*2000000)"], max_output_bytes=65536)
except OutputLimitExceeded as exc:
    assert len(exc.stdout) + len(exc.stderr) == 65536
    assert exc.observed_bytes > exc.limit_bytes == 65536
else:
    raise AssertionError('unbounded diagnostic output accepted')
assert run([sys.executable, '-c', "import os; os.write(1,b'\\xff')"], text=True).stdout == '\ufffd'
with tempfile.TemporaryDirectory() as tmp:
    marker = Path(tmp) / "descendant-survived"
    grandchild = "import time,pathlib; time.sleep(0.5); pathlib.Path(" + repr(str(marker)) + ").write_text('alive')"
    child = ("import subprocess,sys,time; print('partial',flush=True); "
             "print('diagnostic',file=sys.stderr,flush=True); "
             "subprocess.Popen([sys.executable,'-c'," + repr(grandchild) + "]); time.sleep(30)")
    start = time.monotonic()
    try:
        run([sys.executable, "-c", child], timeout=0.15, text=True)
    except subprocess.TimeoutExpired as exc:
        assert "partial" in exc.stdout and "diagnostic" in exc.stderr
    else:
        raise AssertionError("hung child did not time out")
    assert time.monotonic() - start < 3
    time.sleep(0.7)
    assert not marker.exists(), "descendant survived process-group cancellation"
    nested = ("import sys; sys.path.insert(0," + repr(str(ROOT)) + "); "
              "import bounded; bounded.run([sys.executable,'-c'," + repr(grandchild) + "],timeout=10)")
    try:
        run([sys.executable, "-c", nested], timeout=0.15)
    except subprocess.TimeoutExpired:
        pass
    else:
        raise AssertionError("nested wrapper did not time out")
    time.sleep(0.7)
    assert not marker.exists(), "nested wrapper left a separate-session descendant alive"
    resistant = ("import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
                 "time.sleep(1.4); pathlib.Path(" + repr(str(marker)) + ").write_text('alive')")
    nested = ("import sys; sys.path.insert(0," + repr(str(ROOT)) + "); "
              "import bounded; bounded.run([sys.executable,'-c'," + repr(resistant) + "],timeout=10)")
    try:
        run([sys.executable, "-c", nested], timeout=0.15)
    except subprocess.TimeoutExpired:
        pass
    else:
        raise AssertionError("nested resistant process did not time out")
    time.sleep(0.7)
    assert not marker.exists(), "TERM-resistant grandchild survived nested cancellation"
    refused = ("import os,sys; sys.path.insert(0," + repr(str(ROOT)) + "); "
               "import bounded; os.environ[bounded.DEPTH_ENV]=str(bounded.MAX_DEPTH+1); "
               "bounded.run([sys.executable,'-c'," + repr(grandchild) + "])")
    overflow = subprocess.run([sys.executable, "-c", refused], capture_output=True)
    assert overflow.returncode != 0 and b"nesting limit" in overflow.stderr
cli = subprocess.run([sys.executable, str(ROOT / "bounded.py"), "--timeout", "0.05", "--",
                      sys.executable, "-c", "import time; time.sleep(30)"], capture_output=True)
assert cli.returncode == 124 and b"timed out" in cli.stderr
print("PASS successful and failing commands, bounded output, timeout streams, descendant cleanup and shell exit 124")

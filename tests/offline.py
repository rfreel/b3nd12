#!/usr/bin/env python3
"""Exercise the inherited offline boundary with real Python, Git and Bun."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUN = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
assert BUN and BUN.is_file(), "usage: tests/offline.py /path/to/bun"
PREFIX = [sys.executable, str(ROOT / "offline.py"), "--"]


def run(command, **kwargs):
    return subprocess.run(PREFIX + command, capture_output=True, text=True,
                          timeout=30, **kwargs)


probe = run([sys.executable, "-c", """
import ctypes, errno, json, os, socket, subprocess, sys
errors=[]
for family in [socket.AF_INET,socket.AF_INET6,socket.AF_UNIX]:
    try: socket.socket(family)
    except OSError as exc: errors.append(exc.errno)
    else: raise AssertionError('socket permitted')
assert errors == [errno.EPERM]*3, errors
c=ctypes.CDLL(None,use_errno=True)
assert c.syscall(425,1,0)==-1 and ctypes.get_errno()==errno.EPERM
assert c.syscall(0x40000029,2,1,0)==-1 and ctypes.get_errno()==errno.EPERM
assert c.syscall(53,2,1,0,0)==-1 and ctypes.get_errno()==errno.EPERM
assert c.prctl(39,0,0,0,0)==1
left,right=socket.socketpair()
os.write(left.fileno(),b'local');assert right.recv(5)==b'local'
left.close();right.close()
child=subprocess.run([sys.executable,'-c','import socket;socket.socket()'],capture_output=True,text=True)
assert child.returncode != 0 and 'Operation not permitted' in child.stderr
print(json.dumps(errors))
"""])
assert probe.returncode == 0, probe.stderr

with tempfile.TemporaryDirectory(prefix="b3nd12-offline-") as temporary:
    local = run(["git", "init", "--quiet", temporary])
    assert local.returncode == 0, local.stderr
    local = run(["git", "-C", temporary, "rev-parse", "--is-inside-work-tree"])
    assert local.returncode == 0 and local.stdout.strip() == "true"
    # Loopback avoids depending on DNS, certificates or a remote provider.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        environment = dict(os.environ)
        environment.update({"http_proxy": "", "https_proxy": "", "ALL_PROXY": "",
                            "HTTP_PROXY": "", "HTTPS_PROXY": "", "all_proxy": "",
                            "NO_PROXY": "*", "no_proxy": "*"})
        denied = run(["git", "-c", "http.proxy=", "ls-remote",
                      f"http://127.0.0.1:{port}/repo"], env=environment)
        assert denied.returncode != 0, denied
        denied = run([str(BUN), "-e", f"""
fetch('http://127.0.0.1:{port}/').then(() => process.exit(9)).catch(e => {{
  console.log(e.code); process.exit(e.code === 'FailedToOpenSocket' ? 0 : 8);
}});
"""], env=environment)
        assert denied.returncode == 0 and "FailedToOpenSocket" in denied.stdout, denied
        listener.settimeout(0.1)
        try:
            connection, _ = listener.accept()
        except TimeoutError:
            pass
        else:
            connection.close()
            raise AssertionError("offline child reached loopback listener")
    local = run([str(BUN), "-e", "console.log(6*7)"])
    assert local.returncode == 0 and local.stdout.strip() == "42", local
    local = run([str(BUN), "-e", """
const result=Bun.spawnSync([process.argv[1],'-c','print(42)']);
if (result.exitCode !== 0 || result.stdout.toString().trim() !== '42') process.exit(9);
console.log('spawn passed');
""", sys.executable])
    assert local.returncode == 0 and local.stdout.strip() == "spawn passed", local
    with open(Path(temporary) / "inherited", "w") as inherited:
        descriptor = inherited.fileno()
        closed = run([sys.executable, "-c", f"""
import os,errno
try:os.fstat({descriptor})
except OSError as exc:assert exc.errno==errno.EBADF
else:raise AssertionError('inherited descriptor survived')
"""], pass_fds=(descriptor,))
        assert closed.returncode == 0, closed.stderr

left, right = socket.socketpair()
try:
    refused = subprocess.run(PREFIX + [sys.executable, "-c", "raise Exception('ran')"],
                             stdin=left, capture_output=True, text=True, timeout=10)
    assert refused.returncode == 3 and "socket-backed" in refused.stderr
finally:
    left.close()
    right.close()
assert subprocess.run([sys.executable, str(ROOT / "offline.py")],
                      capture_output=True).returncode == 2
for failure in ("architecture", "filter"):
    injected = subprocess.run([sys.executable, "-c", """
import ctypes, errno, importlib.util, sys
spec=importlib.util.spec_from_file_location('offline_guard',sys.argv[1])
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
if sys.argv[2]=='architecture':
    guard.platform.machine=lambda:'unsupported'
else:
    class Refusal:
        def prctl(self,*args):
            ctypes.set_errno(errno.EPERM)
            return -1
    guard.ctypes.CDLL=lambda *a,**k:Refusal()
raise SystemExit(guard.main(['--',sys.executable,'-c',"print('EXECUTED')"]))
""", str(ROOT / "offline.py"), failure], capture_output=True, text=True, timeout=10)
    assert injected.returncode == 3 and "EXECUTED" not in injected.stdout
print("PASS: inherited Python/Git/Bun network denial, local work, descriptor and ABI guards")

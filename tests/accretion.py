#!/usr/bin/env python3
"""Reproduce certificates and check frozen-source and command integration boundaries."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "accretion"))
from run import rounds, validate_compiler
from environment import TASKS

bun = Path(sys.argv[2]).resolve()
bend = Path(sys.argv[1]).resolve()
result = rounds(bun, bend)
assert [(r['metrics']['before'], r['metrics']['after']) for r in result['rounds']] == [(9,8),(8,7),(7,6)]
assert all(r['checker']['stdout']=='All terms check.\n' for r in result['rounds'])
assert all(not r['accepted'] for r in result['negative_controls'].values())
for task, filename in TASKS.items():
    r = subprocess.run([sys.executable, str(ROOT/'b3nd12.py'), 'task', task, '--json'], capture_output=True, text=True, check=True)
    doc = json.loads(r.stdout)
    assert doc['result']['text'] == (ROOT/'guide/agent'/filename).read_text()
    assert doc['result']['reads'] == 2
# An altered checker cannot certify even these finite workload observations.
with tempfile.TemporaryDirectory() as tmp:
    clone = Path(tmp)/'bend'
    subprocess.run(['git','clone','--shared',str(bend),str(clone)],check=True,capture_output=True)
    f=clone/'bend2/main.ts';f.write_bytes(f.read_bytes()+b'\n// altered\n')
    try: validate_compiler(clone)
    except ValueError: pass
    else: raise AssertionError('altered checker accepted')
assert '@unsafe' not in (ROOT/'accretion/PROOF.bend').read_text()
print('PASS 3 accepted rounds, 7 rejected controls, task content parity, altered-checker refusal')

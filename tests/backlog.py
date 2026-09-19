#!/usr/bin/env python3
"""Check proposal structure without admitting it into the frozen experiment."""
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
proposal = ROOT / "docs/TODO_100.md"
raw = proposal.read_bytes()
text = raw.decode()
rows = re.findall(r"^- \[ \] \*\*(T\d{3}) · (P[012]) · (L|C|X|C/X) · ([^\n]+)$", text, re.M)
ids = [row[0] for row in rows]
assert ids == [f"T{i:03d}" for i in range(1, 101)], "expected 100 ordered, unique open tasks"
assert len(re.findall(r"^- \[.\]", text, re.M)) == 100, "unexpected task state or extra checkbox"
assert set(re.findall(r"\bT\d{3}\b", text)) <= set(ids), "unresolved task reference"
assert all("** " in row[3] for row in rows), "task lacks acceptance text"
digest, name = (ROOT / "docs/TODO_100.sha256").read_text().split()
assert name == "docs/TODO_100.md"
assert hashlib.sha256(raw).hexdigest() == digest, "proposal digest changed"
for name in ["docs/PARALLEL_TEST.md", "stack.py", "apply.sh", "verify.sh", "b3nd12.py",
             "accretion/program.py", "accretion/run.py", "accretion/PROOF.bend",
             "tests/program.py", "tests/patch_stack.py", "tests/cli.py", "docs/CLI.md",
             "spec/cli-v1.schema.json", "tests/bend_contracts.py", "docs/ACCRETION.md",
             "docs/FROZEN_TODO.md", "docs/VERIFICATION.md", "AGENTS.md",
             "examples/frozen-spec-twin", "evals", ".github/workflows/verify.yml"]:
    assert (ROOT / name).exists(), "missing evidence source: " + name
frozen = {
    "accretion/TODO.json": "8e0074c4bddb7a8de684d11d7a2db93021c013bd290d2fe8378dff941fb1c40b",
    "accretion/LAWS.bend": "fa8693a4f81e9fa9916acc9d5fe810034447d36935ddd210fb99d0bb76681a3b",
    "accretion/routes.json": "4ff1da7a6e3b077080e32db3cfd7d68e0df9998bd09773fbd5203b1879b948f2",
}
for name, expected in frozen.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, "frozen input changed: " + name
assert "Only after T001–T099" in text, "successor dependency missing"
print("PASS 100 unique open tasks, resolved references, proposal seal, source paths and unchanged frozen inputs")

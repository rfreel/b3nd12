#!/usr/bin/env python3
"""Exercise the frozen TODO controller with real routing and Bend certificates."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "accretion"))
from program import encode, replay, sha

bend, bun = (Path(p).resolve() for p in sys.argv[1:3])
seal = sha((ROOT / "accretion/TODO.json").read_bytes())
routes = (ROOT / "accretion/routes.json").read_bytes()
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    result = replay(root / "positive", seal, bun, bend)
    assert result["stop"] == "target_met"
    assert result["completed"] == ["reads-at-most-8", "reads-at-most-7", "reads-at-most-6", "propose-successor"]
    assert result["successor"]["activation"] == "not_authorized"
    assert result["successor"]["candidates"] == []
    previous = None
    for index, line in enumerate((root / "positive/ledger.jsonl").read_text().splitlines()):
        row = json.loads(line)
        digest = row.pop("sha256")
        assert digest == sha(encode(row)) and row["previous"] == previous
        assert row["sequence"] == index
        previous = digest
    packets = sorted((root / "positive").glob("pass-*/receipt.json"))
    assert len(packets) == 3
    for packet, expected in zip(packets, [(9, 8), (8, 7), (7, 6)]):
        receipt = json.loads(packet.read_text())
        assert receipt["verdict"] == "PRODUCTIVE"
        assert len(receipt["samples"]) == 3
        assert sha((packet.parent / "candidate.json").read_bytes()) == receipt["candidate_sha256"]
        for sample in receipt["samples"]:
            assert (sample["metrics"]["before"], sample["metrics"]["after"]) == expected
            assert sample["checker"]["stdout"] == "All terms check.\n"
    for digest, directory in [("0" * 64, root / "bad-seal"), (seal, root / "positive")]:
        try:
            replay(directory, digest, bun, bend)
        except (ValueError, FileExistsError):
            pass
        else:
            raise AssertionError("changed contract or reused evidence accepted")
    assert not (root / "bad-seal").exists()
    # Exercise seal and oracle tampering through the CLI in its saved source copy.
    snapshot = root / "positive/inputs"
    frozen_todo = snapshot / "accretion/TODO.json"
    original = frozen_todo.read_bytes()
    altered = json.loads(original)
    altered["targets"] = [9, 8, 7]
    frozen_todo.write_bytes(encode(altered))
    command = [sys.executable, str(snapshot / "accretion/program.py"),
               "--contract-sha256", seal, "--bend-root", str(bend), "--bun", str(bun),
               "--output", str(root / "tampered")]
    refusal = subprocess.run(command, capture_output=True, text=True)
    assert refusal.returncode == 1 and "operator's seal" in json.loads(refusal.stdout)["error"]
    frozen_todo.write_bytes(original)
    (snapshot / "guide/agent/PROGRAM.md").write_text("changed oracle\n")
    refusal = subprocess.run(command, capture_output=True, text=True)
    assert refusal.returncode == 1 and "protected input changed" in json.loads(refusal.stdout)["error"]
    assert not (root / "tampered").exists()
    # All six refusals consume attempts; none creates successor authority or credit.
    bad = [b"{}", b'{"implement":"PROVE.md"}', b" " * 4097,
           b'{"prove":"../../secret"}', b'{"accepted":true}',
           b'{"implement":"PROGRAM.md","prove":"PROVE.md"}',
           b'{"diagnose":"diagnostics.json"}']
    refused = replay(root / "refused", seal, bun, bend, bad)
    assert refused["stop"] == "budget_exhausted" and refused["completed"] == []
    assert refused["successor"] is None
    assert len(list((root / "refused").glob("pass-*"))) == 6
    first = json.loads((root / "refused/pass-001/receipt.json").read_text())
    assert first["verdict"] == "NEUTRAL"
    # Repeating a successful candidate cannot earn credit twice; regression is refused.
    one = b'{"diagnose":"diagnostics.json"}'
    partial = replay(root / "partial", seal, bun, bend, [one, one, b"{}"])
    assert partial["completed"] == ["reads-at-most-8"]
    assert partial["stop"] == "candidates_exhausted" and partial["successor"] is None
    assert json.loads((root / "partial/pass-003/receipt.json").read_text())["verdict"] == "REJECTED"
    # Exit zero without a certificate is unresolved, never successful. This
    # controlled process double exercises the exact checker-output boundary.
    unknown = replay(root / "unknown", seal, Path('/usr/bin/true'), bend, [one])
    assert unknown["stop"] == "unresolved" and not unknown["completed"]
assert (ROOT / "accretion/routes.json").read_bytes() == routes
print("PASS frozen seal, 3 productive trials with 9 proofs, bounded refusals, duplicate credit, regression, unresolved checker, successor gate, unchanged installed routes")

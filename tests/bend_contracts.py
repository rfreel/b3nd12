#!/usr/bin/env python3
"""Exercise actual pinned Bend behavior after ordered installation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / "upstream.json").read_text())["commit"]
BUN = shutil.which("bun")
if not BUN:
    raise SystemExit("BLOCKED: bun is required for executable Bend contracts")

with tempfile.TemporaryDirectory(prefix="bend-contracts-") as tmp:
    target = Path(tmp) / "bend"
    subprocess.run(["git", "clone", "--shared", "--no-checkout", str(Path(sys.argv[1]).resolve()), str(target)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(target), "checkout", "--detach", PIN], check=True, capture_output=True)
    subprocess.run([str(ROOT / "apply.sh"), str(target)], check=True, capture_output=True)
    env = {**os.environ, "BEND_NO_TELEMETRY": "1"}
    def run(*args, status=0):
        r = subprocess.run([BUN, str(target / "bend2/main.ts"), *map(str,args)], env=env, capture_output=True, text=True, timeout=15)
        assert r.returncode == status, (args, r.stdout, r.stderr)
        return r
    for args, start in [(("guide",), "# Bend agent router"), (("guide", "program"), "# PROGRAM pack"),
                        (("guide", "prove"), "# PROVE pack"), (("guide", "full"), "# Bend"),
                        (("--pack", "prove"), "# PROVE pack"), (("--why", "BND101"), "BND101")]:
        assert run(*args).stdout.startswith(start)
    program = Path(tmp) / "value.bend"
    program.write_text("import Base\ndef answer() -> Nat:\n  5n\n")
    diag = json.loads(run(program, "--json").stdout)
    assert diag["schema"] == "bend.diag.v1" and diag["id"] == "BND000"
    graph = json.loads(run(program, "--graph", "answer", "--json").stdout)
    assert graph["schema"] == "bend.graph.v1" and graph["roots"] == ["answer"]
    assert any(n["name"] == "answer" for n in graph["nodes"])
    missing = json.loads(run(program, "--graph", "absent", "--json", status=1).stderr)
    assert missing["id"] == "BND200"
    laws = Path(tmp) / "LAWS.bend"
    proof = Path(tmp) / "PROOF.bend"
    laws.write_text("import Base\nlaw identity: {0n == 0n : Nat}\n")
    proof.write_text("import Base\n")
    assert json.loads(run(proof, "--json", status=1).stderr)["id"] == "BND101"
    proof.write_text("import Base\nimport ./LAWS.bend as Laws\ndef Laws.identity(): {==}\n")
    assert run(proof).stdout == "All terms check.\n"
    program.write_text("import Base\ndef main() -> Nat:\n  5n\n")
    assert run(program).stdout == "5n\n"
    js = Path(tmp) / "value.js"
    run(program, "-o", js)
    r = subprocess.run([BUN, str(js)], env=env, capture_output=True, text=True, timeout=15)
    assert r.returncode == 0 and r.stdout == "5n\n", (r.stdout,r.stderr)
    assert not subprocess.run(["git", "-C", str(target), "diff", "--", "bend2/bend.ts"], capture_output=True).stdout
print("PASS installed router, packs, diagnostics, graph, proof guard, proof, interpreter and emitted JS")

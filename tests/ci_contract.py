#!/usr/bin/env python3
"""Check suite presence and failure propagation in the actual workflow shell block.

Controlled executables test orchestration, not GitHub Actions or Bend behavior.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/verify.yml").read_text()
marker = "      - name: Run all acceptance suites against pristine pin\n"
assert workflow.count(marker) == 1
step = workflow.split(marker, 1)[1].split("      - name:", 1)[0]
assert "        shell: bash\n" in step
body = step.split("        run: |\n", 1)[1]
script = "\n".join(line[10:] for line in body.splitlines() if line.strip()) + "\n"
suites = ["patch_stack", "cli", "bend_contracts", "accretion", "program"]
commands = [f"python3 tests/{name}.py upstream" +
            (' "$(command -v bun)"' if name in {"accretion", "program"} else "")
            for name in suites]
assert script.splitlines() == ["set -euo pipefail", *commands]
assert workflow.index(marker) < workflow.index("      - name: Apply and structurally verify\n")

with tempfile.TemporaryDirectory(prefix="b3nd12-ci-contract-") as temporary:
    directory = Path(temporary)
    python = directory / "python3"
    python.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "$CALL_LOG"\n'
                      'if [ "$1" = "$FAIL_SUITE" ]; then exit 17; fi\n')
    python.chmod(0o755)
    bun = directory / "bun"
    bun.write_text("#!/bin/sh\nexit 0\n")
    bun.chmod(0o755)
    log = directory / "calls"
    for failing in [None, *range(len(suites))]:
        log.write_text("")
        env = {**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"],
               "CALL_LOG": str(log),
               "FAIL_SUITE": "" if failing is None else f"tests/{suites[failing]}.py"}
        result = subprocess.run(["bash", "--noprofile", "--norc", "-c", script],
                                env=env, capture_output=True, text=True, timeout=10)
        count = len(suites) if failing is None else failing + 1
        assert log.read_text().splitlines() == [f"tests/{s}.py" for s in suites[:count]]
        assert result.returncode == (0 if failing is None else 17), result
print("PASS workflow includes five suites before installation; each injected failure stops later suites")

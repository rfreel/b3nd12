#!/usr/bin/env python3
"""Bounded proof simplification campaign. No model API or automatic merge."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PILOT = ROOT / "pilot/supermodularity"
MAX_CANDIDATES = 20
TIMEOUT = 20
REPEATS = 5


def sha(data):
    return hashlib.sha256(data).hexdigest()


def surface(source, prefix):
    return [line.strip() for line in source.splitlines() if line.startswith(prefix)]


def admissible(source, baseline):
    # Deliberately narrow: only existing proof bodies, with the same signatures.
    return (
        sorted(surface(source, "import ")) == sorted(surface(baseline, "import "))
        and sorted(surface(source, "def ")) == sorted(surface(baseline, "def "))
        and "@" not in source
        and all(not line or line[0].isspace() or line.startswith(("import ", "def ", "#"))
                for line in source.splitlines())
    )


def score(source):
    return sum(line.lstrip().startswith("case ") for line in source.splitlines())


def command(argv):
    start = time.monotonic()
    try:
        result = subprocess.run(
            [str(x) for x in argv], capture_output=True, text=True,
            timeout=TIMEOUT, env={**os.environ, "BEND_NO_TELEMETRY": "1"},
        )
        return dict(exit_code=result.returncode, stdout=result.stdout,
                    stderr=result.stderr, seconds=time.monotonic() - start)
    except subprocess.TimeoutExpired:
        return dict(exit_code=None, stdout="", stderr="timeout", seconds=time.monotonic() - start)


def events(result):
    return [json.loads(line) for line in (result["stdout"] + "\n" + result["stderr"]).splitlines()
            if line.strip()]


def checked(result):
    if result["exit_code"] != 0:
        return False
    try:
        diagnostics = events(result)
        return (any(e.get("id") == "BND000" and e.get("unsafe") == 0 for e in diagnostics)
                and not any(e.get("severity") == "error" for e in diagnostics))
    except (ValueError, AttributeError):
        return False


def run(target, output):
    runtime = shutil.which("bun")
    if runtime is None:
        raise RuntimeError("Bun is required; checks cannot be skipped")
    pin = json.loads((ROOT / "upstream.json").read_text())["commit"]
    revision = command(["git", "-C", target, "rev-parse", "HEAD"])
    if revision["exit_code"] != 0 or revision["stdout"].strip() != pin:
        raise RuntimeError("upstream revision mismatch")
    verification = command(["sh", ROOT / "verify.sh", target])
    if verification["exit_code"] != 0:
        raise RuntimeError(verification)
    baseline = (HERE / "baseline.bend").read_text()
    candidates = sorted((HERE / "candidates").glob("*.bend"))
    if not 1 <= len(candidates) <= MAX_CANDIDATES:
        raise RuntimeError("campaign requires 1 to 20 candidate files")
    protected = [PILOT / "LAWS.bend", PILOT / "model.bend", HERE / "baseline.bend",
                 Path(__file__).resolve(), ROOT / "verify.sh", ROOT / "upstream.json"]
    protected += sorted((target / "bend2").rglob("*.ts"))
    protected += sorted((target / "bend2").rglob("*.bend"))
    hashes = {str(p): sha(p.read_bytes()) for p in protected}
    output.mkdir(parents=True, exist_ok=False)
    deadline = time.monotonic() + 120
    incumbent = baseline
    winner = "baseline"
    records = []
    with (output / "ledger.jsonl").open("x") as ledger, tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        for name in ("LAWS.bend", "model.bend"):
            shutil.copyfile(PILOT / name, work / name)
        proof = work / "PROOF.bend"

        def probe(source):
            if time.monotonic() >= deadline:
                raise RuntimeError("campaign time budget exhausted")
            proof.write_text(source)
            return command([runtime, target / "bend2/main.ts", proof, "--json"])

        def record(value):
            records.append(value)
            ledger.write(json.dumps(value, sort_keys=True) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        initial = probe(baseline)
        if not checked(initial):
            raise RuntimeError(f"baseline proof failed: {initial}")
        record(dict(candidate="baseline", decision="BASELINE", score=score(baseline), raw=initial))

        # Compiler checks must reject proof deletion and a wrong proof argument.
        missing = baseline[:baseline.index("def Laws.unresolved_preserved")]
        false = baseline.replace("def Laws.unresolved_preserved():\n  {==}",
                                 "def Laws.unresolved_preserved():\n  True{}")
        for name, source, expected in (("missing_proof", missing, "BND103"), ("false_proof", false, "BND110")):
            raw = probe(source)
            record(dict(candidate=name, decision="GUARD", raw=raw))
            if raw["exit_code"] in (None, 0) or not any(e.get("id") == expected and e.get("severity") == "error" for e in events(raw)):
                raise RuntimeError(f"negative guard did not fail as required: {name}")

        for path in candidates:
            source = path.read_text()
            item = dict(candidate=path.name, source_sha256=sha(source.encode()),
                        score=score(source), hypothesis="Combine deletion cases independent of program.")
            if not admissible(source, baseline):
                record(dict(item, decision="REJECTED", reason="proof surface changed"))
                continue
            raw = probe(source)
            if not checked(raw):
                record(dict(item, decision="UNRESOLVED" if raw["exit_code"] is None else "REJECTED", raw=raw))
                continue
            pairs = []
            for repeat in range(REPEATS):
                pair = {}
                order = ("incumbent", "candidate") if repeat % 2 == 0 else ("candidate", "incumbent")
                for label in order:
                    pair[label] = probe(incumbent if label == "incumbent" else source)
                pairs.append(pair)
            valid = all(checked(result) for pair in pairs for result in pair.values())
            keep = valid and score(source) < score(incumbent)
            timed_out = any(result["exit_code"] is None for pair in pairs for result in pair.values())
            record(dict(item, decision="UNRESOLVED" if timed_out else "KEEP" if keep else "REJECTED", raw=raw, pairs=pairs,
                        median_seconds={label: statistics.median(p[label]["seconds"] for p in pairs)
                                        for label in ("incumbent", "candidate")}))
            if keep:
                incumbent, winner = source, path.name

        if hashes != {str(p): sha(p.read_bytes()) for p in protected}:
            raise RuntimeError("protected source changed during campaign")
        report = dict(schema_version=1, winner=winner, baseline_cases=score(baseline),
                      winner_cases=score(incumbent), protected_sha256=hashes,
                      runtime=command([runtime, "--version"]), python=platform.python_version(),
                      platform=platform.platform(), upstream=pin,
                      scope="Proof case count only; timing is descriptive, not an acceptance metric.",
                      records=records)
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        (output / "PROOF.bend").write_text(incumbent)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.target.resolve(), args.output.resolve())
    print(json.dumps({key: report[key] for key in ("winner", "baseline_cases", "winner_cases")}))

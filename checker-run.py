#!/usr/bin/env python3
import hashlib, json, os, pathlib, re, subprocess

ROOT = pathlib.Path("checker-inputs").resolve()
CHECKER = ["bun", str(pathlib.Path("bend-upstream/bend2/main.ts").resolve())]
PIN = "e5a4c4cfe980c2e4e70571562efb5197fe27b2f4"
VERSION = "bend 2.0.9"
BUNDLE = "395a57abf69cca8f4550a72f9118e0fb223a25d2b8eca351a8a6e485c8b03821"
TARGETS = [
    ("move", "affine_rebuild", ROOT / "moves/affine_rebuild"),
    ("move", "compute_eq", ROOT / "moves/compute_eq"),
    ("move", "equation_rewrite", ROOT / "moves/equation_rewrite"),
    ("move", "forall_list", ROOT / "moves/forall_list"),
    ("move", "list_ind", ROOT / "moves/list_ind"),
    ("move", "nat_ind", ROOT / "moves/nat_ind"),
    ("move", "open_hole", ROOT / "moves/open_hole"),
    ("move", "pure_model", ROOT / "moves/pure_model"),
    ("package", "alien-artifact", ROOT / "packages/alien-artifact"),
    ("package", "taxonomy", ROOT / "packages/taxonomy"),
]
OUT = pathlib.Path("receipts")
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def count_laws(d: pathlib.Path) -> int:
    return sum(bool(re.match(r"^law\s+", line))
               for line in (d / "LAWS.bend").read_text().splitlines())

def run(d: pathlib.Path, entry: str):
    p = subprocess.run(CHECKER + [entry], cwd=d, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env={**os.environ, "BEND_NO_TELEMETRY": "1"})
    return p

receipts = []
for kind, name, d in TARGETS:
    laws = count_laws(d)
    main = run(d, "main.bend")
    proof = run(d, "PROOF.bend")
    combined = proof.stdout + "\n" + proof.stderr
    unsafe = bool(re.search(r"unsafe annotation", combined, re.I))
    todo = bool(re.search(r"\bTODOs?\b|\?[A-Za-z_]", combined))
    ok = proof.returncode == 0 and not unsafe and not todo
    excerpt = " | ".join(x.strip() for x in proof.stderr.splitlines()[:8] if x.strip())[:900]
    record = {
        "schema": "bend.checker-receipt.v1",
        "checker_version": VERSION,
        "checker_commit": PIN,
        "input_bundle_sha256": BUNDLE,
        "target_kind": kind,
        "target": name,
        "law_count": laws,
        "main_exit": main.returncode,
        "proof_exit": proof.returncode,
        "unsafe_detected": unsafe,
        "todo_detected": todo,
        "proof_ok": ok,
        "laws_discharged": laws if ok else 0,
        "proof_stdout_sha256": sha(proof.stdout.encode()),
        "proof_stderr_sha256": sha(proof.stderr.encode()),
        "error_excerpt": excerpt,
    }
    receipts.append(record)
    (RAW / f"{kind}-{name}-main.stdout.txt").write_text(main.stdout)
    (RAW / f"{kind}-{name}-main.stderr.txt").write_text(main.stderr)
    (RAW / f"{kind}-{name}-proof.stdout.txt").write_text(proof.stdout)
    (RAW / f"{kind}-{name}-proof.stderr.txt").write_text(proof.stderr)
    print("PROOF_RECEIPT " + json.dumps(record, sort_keys=True))

summary = {
    "schema": "bend.checker-sequence-summary.v1",
    "checker_version": VERSION,
    "checker_commit": PIN,
    "input_bundle_sha256": BUNDLE,
    "targets": len(receipts),
    "proofs_passed": [r["target"] for r in receipts if r["proof_ok"]],
    "proofs_failed": [r["target"] for r in receipts if not r["proof_ok"]],
    "move_proofs_passed": sum(r["proof_ok"] for r in receipts if r["target_kind"] == "move"),
    "move_proofs_total": sum(r["target_kind"] == "move" for r in receipts),
    "alien_artifact_laws_discharged": next(r["laws_discharged"] for r in receipts if r["target"] == "alien-artifact"),
    "taxonomy_laws_discharged": next(r["laws_discharged"] for r in receipts if r["target"] == "taxonomy"),
    "laws_discharged_total": sum(r["laws_discharged"] for r in receipts),
}
OUT.mkdir(exist_ok=True)
(OUT / "proof-receipts.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts))
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print("SUMMARY " + json.dumps(summary, sort_keys=True))

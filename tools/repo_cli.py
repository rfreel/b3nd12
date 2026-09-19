"""One operational surface; task authority stays in the existing task journal."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from .agent_system.contracts import Problem, canonical, parse
from .agent_system.evidence import execute

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("schema", "decision", "executor", "proof", "integration", "stress", "all")


def read(path):
    return parse(Path(path).read_text())


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def command(argv, root=ROOT, timeout=15):
    result = execute(argv, root, timeout)
    if not result["passed"]:
        raise Problem("COMMAND_FAILED", canonical({"argv": argv, "exit": result["exit_code"],
                                                  "error": result["stderr"], "timeout": result["timed_out"]}))
    return result["stdout"].strip()


def configuration(root):
    path = root / ".repo/config.json"
    return read(path) if path.exists() else {}


def target_for(root, supplied=None):
    configured = supplied or configuration(root).get("target")
    return Path(configured).resolve() if configured else (root / "upstream").resolve()


def bun_for(root):
    local = root / ".repo/runtime/node_modules/.bin/bun"
    configured = configuration(root).get("bun")
    for value in (configured, str(local), shutil.which("bun")):
        if value and Path(value).is_file() and os.access(value, os.X_OK):
            return str(Path(value).absolute())
    return None


def doctor(root, target=None):
    versions = read(root / "toolchain.json")
    bun = bun_for(root)
    actual_bun = command([bun, "--version"], root) if bun else None
    actual_git = command(["git", "--version"], root).split()[-1] if shutil.which("git") else None
    git_numbers = tuple(map(int, actual_git.split(".")[:2])) if actual_git else ()
    minimum_git = tuple(map(int, versions["git_minimum"].split(".")))
    python_ok = tuple(sys.version_info[:2]) >= tuple(map(int, versions["python"].split(".")))
    issues = []
    if not python_ok:
        issues.append("PYTHON_VERSION")
    if not actual_git or git_numbers < minimum_git:
        issues.append("GIT_VERSION")
    if actual_bun != versions["bun"]:
        issues.append("BUN_VERSION")
    upstream = target_for(root, target)
    pin = read(root / "upstream.json")["commit"]
    revision = None
    if (upstream / ".git").exists():
        revision = command(["git", "-C", str(upstream), "rev-parse", "HEAD"], root)
    if revision != pin:
        issues.append("UPSTREAM_PIN")
    return {"ready": not issues, "issues": issues, "python": platform.python_version(),
            "git": actual_git, "bun": actual_bun, "bun_path": bun,
            "target": str(upstream), "upstream": revision, "expected_upstream": pin,
            "host_access": "not inspected", "next": "./repo setup" if issues else "./repo verify"}


def source_snapshot(root):
    names = command(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], root).split("\0")
    result = {}
    for name in sorted(set(names)):
        path = root / name
        if not name or name.startswith((".repo/", "upstream/")):
            continue
        if path.is_symlink():
            result[name] = {"sha256": hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest(), "mode": "120000"}
        elif path.is_file():
            result[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "mode": "100755" if path.stat().st_mode & 0o111 else "100644"}
    return result


def evaluation_snapshot(root, target):
    sources = source_snapshot(root)
    upstream = target_for(root, target)
    target_sources = source_snapshot(upstream) if (upstream / ".git").exists() else {}
    bun = bun_for(root)
    return {"sources": sources, "upstream_sources": target_sources,
            "upstream_head": command(["git", "-C", str(upstream), "rev-parse", "HEAD"], root) if target_sources else None,
            "python": platform.python_version(), "platform": platform.platform(),
            "git": command(["git", "--version"], root),
            "git_config_sha256": hashlib.sha256(command(["git", "config", "--null", "--list"], root).encode()).hexdigest(),
            "bun_sha256": hashlib.sha256(Path(bun).read_bytes()).hexdigest() if bun else None}


def latest(root):
    path = root / ".repo/latest.json"
    if not path.exists():
        return {"state": "UNVERIFIED", "next": "./repo verify"}
    pointer = read(path)
    record = read(root / pointer["path"])
    logs_intact = all((root / s["log"]).is_file() and hashlib.sha256((root / s["log"]).read_bytes()).hexdigest() == s["log_sha256"] for s in record["steps"])
    complete = ([s["name"] for s in record["steps"]] == [name for name, _ in steps_for(root, record["scope"], Path(record["target"]))]
                and all(s["passed"] and s["exit"] == 0 and not s["timed_out"] and not s["truncated"] for s in record["steps"]))
    fresh = (record.get("snapshot") == evaluation_snapshot(root, record.get("target")) and logs_intact)
    if record["state"] == "PASS" and not complete:
        fresh = False
    state = record["state"] if fresh else "STALE"
    return {"state": state, "fresh": fresh, "scope": record["scope"], "run": pointer["path"],
            "completed": [s["name"] for s in record["steps"]],
            "next": "./repo verify" if state != "PASS" else "./repo publish --dry-run"}


def status(root, target=None):
    control = read_control(root, ["status"])
    return {"revision": command(["git", "rev-parse", "HEAD"], root),
            "branch": command(["git", "rev-parse", "--abbrev-ref", "HEAD"], root),
            "changes": command(["git", "status", "--porcelain"], root).splitlines(),
            "environment": doctor(root, target), "verification": latest(root),
            "tasks": control, "next": latest(root)["next"]}


def read_control(root, args):
    result = command([sys.executable, str(root / "control.py"), *args], root)
    return json.loads(result)["result"]


def setup(root, args):
    """Resume exact overlay installation; never reset an unknown dirty checkout."""
    target = target_for(root, args.target)
    cfg = configuration(root)
    if args.bun:
        candidate = str(Path(args.bun).absolute())
        if command([candidate, "--version"], root) != read(root / "toolchain.json")["bun"]:
            raise Problem("BUN_VERSION", "supplied Bun differs from toolchain.json")
        cfg["bun"] = candidate
        atomic(root / ".repo/config.json", cfg)
    bun = bun_for(root)
    if not bun or command([bun, "--version"], root) != read(root / "toolchain.json")["bun"]:
        if not shutil.which("npm"):
            raise Problem("CAPABILITY_MISSING", "Bun is missing and npm is unavailable for pinned installation")
        command(["npm", "install", "--prefix", str(root / ".repo/runtime"),
                 "bun@" + read(root / "toolchain.json")["bun"]], root, 120)
        cfg["bun"] = str(root / ".repo/runtime/node_modules/.bin/bun")
        atomic(root / ".repo/config.json", cfg)
        bun = bun_for(root)
    pin = read(root / "upstream.json")["commit"]
    if not target.exists():
        command(["git", "init", str(target)], root)
        command(["git", "-C", str(target), "remote", "add", "origin", "https://github.com/bendlang/bend.git"], root)
    if not (target / ".git").exists():
        raise Problem("UNSAFE_TARGET", "setup target exists but is not an ordinary Git checkout")
    head = execute(["git", "-C", str(target), "rev-parse", "HEAD"], root, 10)
    if not head["passed"]:
        if command(["git", "-C", str(target), "status", "--porcelain"], root):
            raise Problem("DIRTY_TARGET", "uninitialized target contains changes")
        command(["git", "-C", str(target), "fetch", "--depth=1", "origin", pin], root, 120)
        command(["git", "-C", str(target), "checkout", "--detach", "FETCH_HEAD"], root)
    elif head["stdout"].strip() != pin:
        raise Problem("UPSTREAM_PIN", "existing checkout has another revision; choose a separate target")
    mapping = {"AGENTS.md": "overlay/AGENTS.md", "bend2/main.ts": "overlay/bend2/main.ts",
               "gates/repo.ts": "overlay/gates/repo.ts", "gates/ping.ts": "overlay/gates/ping.ts",
               "CLAUDE.md": "CLAUDE.md", "evals/README.md": "evals/README.md",
               "evals/_template.sidecar.json": "evals/_template.sidecar.json", "evals/_sidecar.schema.json": "evals/_sidecar.schema.json"}
    for path in (root / "guide/agent").rglob("*"):
        if path.is_file() and path.suffix in (".md", ".json"):
            mapping[str(path.relative_to(root))] = str(path.relative_to(root))
    changed = command(["git", "-C", str(target), "diff", "HEAD", "--name-only"], root).splitlines()
    changed += command(["git", "-C", str(target), "ls-files", "--others", "--exclude-standard"], root).splitlines()
    previous = cfg.get("installed", {}) if cfg.get("target") == str(target) else {}
    for name in changed:
        path = target / name
        desired = root / mapping[name] if name in mapping else None
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        matches = desired and path.is_file() and path.read_bytes() == desired.read_bytes()
        if not matches and (name not in mapping or previous.get(name) != actual):
            raise Problem("DIRTY_TARGET", "unrecognized target modification: " + name)
    # Ignored destinations are not listed by git status. Check every overwrite,
    # including link components, against desired, prior, or pristine content.
    for name, source in mapping.items():
        path = target / name
        if any(part.is_symlink() for part in (path, *path.parents) if part != target.parent):
            raise Problem("DIRTY_TARGET", "symlink in overlay destination: " + name)
        if not path.exists():
            continue
        if not path.is_file():
            raise Problem("DIRTY_TARGET", "non-file overlay destination: " + name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        desired = hashlib.sha256((root / source).read_bytes()).hexdigest()
        if actual == desired or actual == previous.get(name):
            continue
        original = execute(["git", "-C", str(target), "rev-parse", "--verify", pin + ":" + name], root, 10)
        actual_blob = command(["git", "-C", str(target), "hash-object", "--", name], root)
        if not original["passed"] or original["stdout"].strip() != actual_blob:
            raise Problem("DIRTY_TARGET", "unrecognized overlay destination: " + name)
    # Persist resumable intent before writes. Only recognized overlay files are replaced.
    cfg.update(target=str(target), bun=bun, setup_state="INSTALLING")
    atomic(root / ".repo/config.json", cfg)
    for destination, source in mapping.items():
        out = target / destination
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / source, out)
    cfg.update(installed={k: hashlib.sha256((target / k).read_bytes()).hexdigest() for k in mapping}, setup_state="READY")
    atomic(root / ".repo/config.json", cfg)
    previous_path = os.environ.get("PATH", "")
    try:
        os.environ["PATH"] = str(Path(bun).parent) + os.pathsep + previous_path
        result = execute([str(root / "verify.sh"), str(target)], root, 30)
    finally:
        os.environ["PATH"] = previous_path
    if not result["passed"]:
        raise Problem("SETUP_VERIFY_FAILED", result["stderr"])
    return doctor(root, target)


def steps_for(root, scope, target):
    python = sys.executable
    test = lambda pattern: [python, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
    mapping = {
        "schema": [("schema", test("test_admission_api.py"))],
        "decision": [("decision", test("test_admission_gate.py"))],
        "executor": [("executor", [python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_admission_gate.py", "-v"])],
        "proof": [("proof-generation", [python, "scripts/generate-admission-proof.py", "--check"]),
                  ("proof-correspondence", [python, "scripts/check-admission-correspondence.py", str(target), "--bun", bun_for(root) or "bun"])],
        "integration": [("integration", ["sh", "scripts/verify-supermodularity.sh", str(target)])],
        "stress": [("stress", ["sh", "scripts/verify-admission.sh", str(target)])],
    }
    if scope != "all":
        return mapping[scope]
    return [("catalog", [str(root / "repo"), "catalog", "--check"]),
            ("python", test("test_*.py"))] + mapping["proof"] + mapping["integration"] + mapping["stress"]


def verify(root, args):
    target = target_for(root, args.target)
    if args.scope in ("all", "proof", "integration", "stress"):
        diagnosis = doctor(root, target)
        if not diagnosis["ready"]:
            raise Problem("ENVIRONMENT_INCOMPLETE", canonical(diagnosis))
    limits = read(root / "toolchain.json")["budgets"]
    total = limits["total_seconds"] if args.budget is None else args.budget
    if not 1 <= total <= limits["total_seconds"]:
        raise Problem("INVALID_BUDGET", "budget must be positive and within toolchain limit")
    run = uuid.uuid4().hex
    folder = root / ".repo/runs" / run
    folder.mkdir(parents=True)
    record = {"schema_version": 1, "scope": args.scope, "target": str(target), "state": "RUNNING",
              "revision": command(["git", "rev-parse", "HEAD"], root),
              "snapshot": evaluation_snapshot(root, target), "steps": [], "budget_seconds": total}
    path = folder / "result.json"
    atomic(path, record)
    atomic(root / ".repo/latest.json", {"path": str(path.relative_to(root))})
    start = time.monotonic()
    environment = dict(os.environ)
    if bun_for(root):
        os.environ["PATH"] = str(Path(bun_for(root)).parent) + os.pathsep + os.environ.get("PATH", "")
    os.environ["BEND_TARGET"] = str(target)
    os.environ["BEND_UPSTREAM"] = str(target)
    if bun_for(root):
        os.environ["BUN"] = bun_for(root)
    os.environ["BEND_NO_TELEMETRY"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["ADMISSION_RESULTS"] = str(folder / "admission.json")
    os.environ["SUPERMODULARITY_RESULTS_DIR"] = str(folder / "integration")
    failures = 0
    try:
        for name, argv in steps_for(root, args.scope, target):
            remaining = total - (time.monotonic() - start)
            if remaining <= 0:
                record["state"] = "BUDGET_EXHAUSTED"
                break
            result = execute(argv, root, min(limits["step_seconds"], remaining))
            output = result["stdout"] + result["stderr"]
            if re.search(r"\bskipped=\d+", output) or "Ran 0 tests" in output:
                result["passed"] = False
                result["coverage_gap"] = "unexpected skipped or empty test suite"
            log = folder / (name + ".log")
            log.write_text(output)
            record["steps"].append({"name": name, "argv": argv, "passed": result["passed"],
                                     "exit": result["exit_code"], "seconds": result["seconds"],
                                     "timed_out": result["timed_out"], "truncated": result["truncated"],
                                     "log": str(log.relative_to(root)), "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()})
            failures += not result["passed"]
            atomic(path, record)
            if failures >= limits["failure_cap"] or not result["passed"]:
                record["state"] = "FAIL"
                break
        else:
            record["state"] = "PASS"
    except (OSError, KeyboardInterrupt) as error:
        record["state"] = "INTERRUPTED"
        record["error"] = str(error)
    finally:
        os.environ.clear()
        os.environ.update(environment)
        record["seconds"] = time.monotonic() - start
        record["snapshot_after"] = evaluation_snapshot(root, target)
        if record["snapshot_after"] != record["snapshot"]:
            record["state"] = "STALE"
        atomic(path, record)
    summary = {"state": record["state"], "scope": args.scope, "run": str(path.relative_to(root)),
               "steps": record["steps"], "seconds": record["seconds"]}
    return summary


def catalog(root, check=False):
    data = read(root / "system/ergonomics.json")
    ids = set()
    for item in data["items"]:
        if item["id"] in ids or not item["acceptance"] or not item["evidence"]:
            raise Problem("INVALID_CATALOG", "duplicate ID or missing acceptance/evidence")
        ids.add(item["id"])
        for name in item["files"]:
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise Problem("INVALID_CATALOG", "missing or unsafe path: " + name)
    return {"items": len(ids), "valid": True} if check else data


def rendered_status(root):
    data = catalog(root)
    lines = ["# Repository capabilities", "", "Generated by `./repo render`. Capability declarations are not verification results.", "",
             "Use `./repo status` for current evidence and `./repo tasks status` for task authority.", "",
             "| ID | Capability | Acceptance | Check |", "| --- | --- | --- | --- |"]
    for item in data["items"]:
        lines.append(f"| {item['id']} | {item['title']} | {item['acceptance']} | {item['evidence']} |")
    return "\n".join(lines) + "\n"


def content_tree(root):
    """Build a temporary index without modifying the caller's index."""
    with tempfile.TemporaryDirectory() as folder:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(folder) / "index")}
        for argv in (["git", "read-tree", "HEAD"], ["git", "add", "-A"]):
            subprocess.run(argv, cwd=root, env=env, capture_output=True, check=True, timeout=15)
        return subprocess.check_output(["git", "write-tree"], cwd=root, env=env, text=True, timeout=15).strip()


def publish_packet(root):
    verification = latest(root)
    if verification["state"] != "PASS" or verification.get("scope") != "all":
        raise Problem("EVIDENCE_STALE", "publishing requires a fresh complete ./repo verify run")
    tree = content_tree(root)
    body = ("Repository ergonomics integration.\n\n"
            "Verified tree: " + tree + "\nVerification record: " + verification["run"] + "\n\n"
            "Includes the repository command, admission facade, bounded verification, recovery demo, "
            "proof correspondence, and evidence-backed status. See docs/repo-operations.md for trust boundaries.\n")
    folder = root / ".repo/publish"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "body.md").write_text(body)
    packet = {"tree": tree, "base": command(["git", "rev-parse", "HEAD"], root),
              "body_file": str(folder / "body.md"), "verification": verification,
              "connector_steps": ["create_tree from verified content", "create_commit with returned tree", "create_branch", "create_pull_request", "verify-remote exact commit"]}
    atomic(folder / "packet.json", packet)
    return packet


def github(root, args, timeout=30):
    if not shutil.which("gh"):
        raise Problem("CAPABILITY_MISSING", "gh is unavailable; use the connected GitHub tools with ./repo publish --dry-run")
    return json.loads(command(["gh", *args], root, timeout))


def remote_head(root, branch, expected_tree):
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", branch) is None:
        raise Problem("INVALID_BRANCH", "expected a branch name")
    command(["git", "check-ref-format", "--branch", branch], root)
    result = command(["git", "ls-remote", "--exit-code", "origin", "refs/heads/" + branch], root, 30)
    lines = result.splitlines()
    if len(lines) != 1 or len(lines[0].split()) != 2:
        raise Problem("REMOTE_HEAD_UNRESOLVED", "remote branch did not resolve uniquely")
    revision = lines[0].split()[0]
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise Problem("INVALID_REVISION", "expected exact remote SHA1 commit")
    command(["git", "fetch", "--no-tags", "origin", revision], root, 60)
    if command(["git", "rev-parse", revision + "^{tree}"], root) != expected_tree:
        raise Problem("TREE_MISMATCH", "remote branch differs from verified content")
    return revision


def capture(root, args):
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.name) is None:
        raise Problem("INVALID_CASE_ID", "use an alphanumeric counterexample ID")
    law = (root / args.law).resolve()
    if not law.is_relative_to(root) or not law.is_file():
        raise Problem("INVALID_LAW", "law must identify an existing repository file")
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv:
        raise Problem("MISSING_REPRODUCER", "supply an explicit command after --")
    result = execute(argv, root, 30)
    output = result["stdout"] + result["stderr"]
    if result["timed_out"] or result["truncated"] or result["exit_code"] != args.expected_exit or args.contains not in output:
        raise Problem("NOT_REPRODUCED", "expected exit and diagnostic were not observed within budget")
    path = root / "counterexamples" / (args.name + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"law": str(law.relative_to(root)), "law_sha256": hashlib.sha256(law.read_bytes()).hexdigest(),
              "expected_exit": args.expected_exit, "expected_diagnostic": args.contains,
              "observation": result, "sources": source_snapshot(root),
              "scope": "Confirmed command outcome; semantic relevance requires review."}
    with path.open("x") as stream:
        stream.write(canonical(record) + "\n")
    return {"path": str(path.relative_to(root)), "reproduced": True}


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    capture_command = []
    if "capture" in arguments and "--" in arguments:
        separator = arguments.index("--")
        capture_command, arguments = arguments[separator + 1:], arguments[:separator]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("status", "doctor"):
        sub.add_parser(name).add_argument("--target", type=Path)
    p = sub.add_parser("setup")
    p.add_argument("--target", type=Path)
    p.add_argument("--bun", type=Path)
    for name in ("verify", "stress"):
        p = sub.add_parser(name)
        p.add_argument("--target", type=Path)
        p.add_argument("--scope", choices=SCOPES, default="stress" if name == "stress" else "all")
        p.add_argument("--budget", type=int)
    p = sub.add_parser("tasks")
    p.add_argument("arguments", nargs=argparse.REMAINDER)
    p = sub.add_parser("catalog")
    p.add_argument("--check", action="store_true")
    p = sub.add_parser("render")
    p.add_argument("--check", action="store_true")
    p = sub.add_parser("route")
    p.add_argument("route", choices=("GATE", "VERIFY", "RELEASE", "PROGRAM", "PROVE"))
    p = sub.add_parser("explain")
    p.add_argument("code")
    p = sub.add_parser("impact")
    p.add_argument("paths", nargs="*")
    p = sub.add_parser("inspect-manifest")
    p.add_argument("manifest", type=Path)
    p.add_argument("--compare", type=Path)
    sub.add_parser("demo")
    p = sub.add_parser("reconcile")
    p.add_argument("repository", type=Path)
    p.add_argument("manifest", type=Path)
    p = sub.add_parser("publish")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--head")
    p.add_argument("--base", default="main")
    p = sub.add_parser("verify-remote")
    p.add_argument("revision")
    p.add_argument("--remote", default="origin")
    p = sub.add_parser("host")
    p.add_argument("repository")
    p = sub.add_parser("watch")
    p.add_argument("pr", type=int)
    p.add_argument("--budget", type=int, default=120)
    p = sub.add_parser("capture")
    p.add_argument("name")
    p.add_argument("--law", required=True)
    p.add_argument("--expected-exit", type=int, required=True)
    p.add_argument("--contains", required=True)
    args = parser.parse_args(arguments)
    if args.action == "capture":
        args.command = capture_command
    root = args.root.resolve()
    try:
        if args.action == "status":
            result = status(root, args.target)
        elif args.action == "doctor":
            result = doctor(root, args.target)
        elif args.action == "setup":
            result = setup(root, args)
        elif args.action in ("verify", "stress"):
            result = verify(root, args)
        elif args.action == "tasks":
            result = read_control(root, args.arguments or ["status"])
        elif args.action == "catalog":
            result = catalog(root, args.check)
        elif args.action == "render":
            text = rendered_status(root)
            path = root / "docs/capabilities.md"
            if args.check:
                if not path.exists() or path.read_text() != text:
                    raise Problem("GENERATED_DRIFT", "run ./repo render")
            else:
                path.write_text(text)
            result = {"path": str(path), "current": True}
        elif args.action == "route":
            result = {"route": args.route, "text": (root / "guide/agent" / (args.route + ".md")).read_text()}
        elif args.action == "explain":
            errors = read(root / "system/errors.json")
            if args.code not in errors:
                raise Problem("UNKNOWN_CODE", args.code)
            result = errors[args.code]
        elif args.action == "impact":
            paths = args.paths or command(["git", "diff", "--name-only", "HEAD"], root).splitlines()
            matches = [i for i in catalog(root)["items"] if any(p in i["files"] for p in paths)]
            result = {"changed": paths, "items": [i["id"] for i in matches],
                      "checks": sorted({i["evidence"] for i in matches}),
                      "fallback": "./repo verify" if any(not any(p in i["files"] for i in matches) for p in paths) else None}
        elif args.action in ("inspect-manifest", "reconcile", "demo"):
            from admission import Manifest, inspect_manifest, diff_manifests, reconcile, demo
            if args.action == "demo":
                result = demo()
            elif args.action == "reconcile":
                manifest = Manifest(read(args.manifest))
                result = reconcile(args.repository, manifest.to_dict()["request"], manifest)
            else:
                manifest = Manifest(read(args.manifest))
                result = diff_manifests(manifest, Manifest(read(args.compare))) if args.compare else inspect_manifest(manifest)
        elif args.action == "publish":
            result = publish_packet(root)
            if not args.dry_run:
                if not args.head:
                    raise Problem("HEAD_REQUIRED", "supply an already-pushed --head branch; publish never stages or pushes implicitly")
                if not shutil.which("gh"):
                    raise Problem("CAPABILITY_MISSING", "gh unavailable; use the generated connector packet")
                before = remote_head(root, args.head, result["tree"])
                result["url"] = command(["gh", "pr", "create", "--head", args.head, "--base", args.base,
                                         "--title", "Repository ergonomics integration", "--body-file", result["body_file"]], root, 30)
                after = remote_head(root, args.head, result["tree"])
                if after != before:
                    raise Problem("REMOTE_HEAD_MOVED", "PR was created but its branch moved during publication; inspect it before proceeding")
                result["commit"] = after
        elif args.action == "verify-remote":
            if re.fullmatch(r"[0-9a-f]{40}", args.revision) is None:
                raise Problem("INVALID_REVISION", "use an exact commit SHA")
            command(["git", "fetch", "--no-tags", args.remote, args.revision], root, 60)
            remote_tree = command(["git", "rev-parse", args.revision + "^{tree}"], root)
            local_tree = content_tree(root)
            if local_tree != remote_tree:
                raise Problem("TREE_MISMATCH", "published content differs from local content")
            result = {"matches": True, "commit": args.revision, "tree": remote_tree}
        elif args.action == "host":
            if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository) is None:
                raise Problem("INVALID_REPOSITORY", "expected owner/name")
            result = {"rulesets": github(root, ["api", "repos/" + args.repository + "/rulesets"]),
                      "scope": "read-only host policy inspection; bypass privileges require separate review"}
        elif args.action == "watch":
            if not 1 <= args.budget <= 600:
                raise Problem("INVALID_BUDGET", "watch budget must be 1..600 seconds")
            start = time.monotonic()
            result = {"watch_state": "PENDING", "statusCheckRollup": []}
            while True:
                remaining = args.budget - (time.monotonic() - start)
                if remaining <= 0:
                    result["watch_state"] = "PENDING"
                    break
                try:
                    result = github(root, ["pr", "view", str(args.pr), "--json", "state,mergedAt,statusCheckRollup,headRefOid"], min(30, remaining))
                except Problem as error:
                    if error.code == "COMMAND_FAILED" and time.monotonic() - start >= args.budget:
                        result.update(watch_state="PENDING", reason="watch budget exhausted during transport")
                        break
                    raise
                checks = result.get("statusCheckRollup") or []
                if checks and all(c.get("status") == "COMPLETED" or c.get("state") in ("SUCCESS", "FAILURE", "ERROR") for c in checks):
                    result["watch_state"] = "COMPLETE"
                    break
                remaining = args.budget - (time.monotonic() - start)
                if remaining <= 0:
                    result["watch_state"] = "PENDING"
                    break
                time.sleep(min(5, remaining))
        elif args.action == "capture":
            result = capture(root, args)
        print(canonical({"schema_version": 1, "ok": True, "result": result}))
        return 1 if isinstance(result, dict) and result.get("state") in ("FAIL", "STALE", "INTERRUPTED", "BUDGET_EXHAUSTED") else 0
    except (Problem, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(canonical({"schema_version": 1, "ok": False, "error": {"code": getattr(error, "code", "IO_OR_INPUT_ERROR"), "message": str(error)}}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

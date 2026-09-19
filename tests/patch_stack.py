#!/usr/bin/env python3
"""Verify ordered installation against the existing delivery, offline."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / "upstream.json").read_text())["commit"]


def run(*args, cwd=None, ok=True):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if ok and result.returncode:
        raise RuntimeError(f"{args}:\n{result.stdout}{result.stderr}")
    return result


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    source = Path(sys.argv[1]).resolve()
    expected = {
        p: ROOT / "overlay" / p
        for p in ("AGENTS.md", "bend2/main.ts", "gates/repo.ts", "gates/ping.ts")
    }
    for pattern in ("CLAUDE.md", "guide/agent/*.md", "guide/agent/*.json",
                    "guide/agent/proof/*.md", "evals/README.md",
                    "evals/_template.sidecar.json", "evals/_sidecar.schema.json"):
        for file in ROOT.glob(pattern):
            expected[file.relative_to(ROOT).as_posix()] = file
    patches = sorted((ROOT / "patches").glob("[0-9][0-9]-*.patch"))
    require([int(p.name[:2]) for p in patches] == list(range(1, 10)),
            "Expected exactly ranks 1 through 9")

    with tempfile.TemporaryDirectory(prefix="bend-patch-test-") as tmp:
        tmp = Path(tmp)

        def checkout(name):
            target = tmp / name
            run("git", "clone", "--shared", "--no-checkout", str(source), str(target))
            run("git", "checkout", "--detach", PIN, cwd=target)
            return target

        def verify(target):
            changed = set(run("git", "diff", "--name-only", "HEAD", cwd=target)
                          .stdout.splitlines())
            added = set(run("git", "ls-files", "--others", "--exclude-standard",
                            cwd=target).stdout.splitlines())
            require(changed | added == set(expected), "Installed path set differs")
            for path, reference in expected.items():
                require((target / path).read_bytes() == reference.read_bytes(),
                        f"Content mismatch: {path}")
            require(run("git", "diff", "--summary", "HEAD", cwd=target).stdout == "",
                    "Upstream file modes changed")
            original = subprocess.check_output(
                ["git", "show", f"{PIN}:bend2/bend.ts"], cwd=target)
            require((target / "bend2/bend.ts").read_bytes() == original,
                    "Theory source changed")
            require(run("git", "diff", "--cached", "--name-only", cwd=target).stdout == "",
                    "Installer changed the real index")
            run("git", "diff", "--check", cwd=target)

        direct = checkout("direct")
        for patch in patches:
            run("git", "apply", "--check", "--whitespace=error", str(patch), cwd=direct)
            run("git", "apply", "--whitespace=error", str(patch), cwd=direct)
            print(f"PASS direct {patch.name}")
        verify(direct)

        installed = checkout("installed")
        result = run(str(ROOT / "apply.sh"), str(installed))
        print(result.stdout, end="")
        verify(installed)
        print(f"PASS both installation paths match all {len(expected)} delivery files")
        print("PASS exact file scope, upstream modes, real index, and theory bytes")

        run("git", "config", "core.filemode", "false", cwd=installed)
        index_path = installed / ".git/index"
        for name in ("bend2/bend.ts", "README.md", "bend2/main.ts"):
            file = installed / name
            original_mode = file.stat().st_mode
            original_bytes = file.read_bytes()
            changed_mode = original_mode & ~0o111 if original_mode & 0o111 else original_mode | 0o111
            file.chmod(changed_mode)
            status_before = run("git", "status", "--porcelain", cwd=installed).stdout
            index_before = index_path.read_bytes()
            result = run(sys.executable, str(ROOT / "stack.py"), str(installed), ok=False)
            require(result.returncode != 0 and "mode" in result.stderr.lower(),
                    f"Verifier accepted upstream executable-bit drift: {name}")
            require(file.read_bytes() == original_bytes and file.stat().st_mode == changed_mode,
                    "Verification changed the rejected file")
            require(index_path.read_bytes() == index_before,
                    "Verification changed the real index")
            require(run("git", "status", "--porcelain", cwd=installed).stdout == status_before,
                    "Verification changed target status")
            file.chmod(original_mode)
        run(sys.executable, str(ROOT / "stack.py"), str(installed))
        print("PASS protected and untouched upstream modes checked with core.filemode=false")

        before = run("git", "status", "--porcelain", cwd=installed).stdout
        result = run(str(ROOT / "apply.sh"), str(installed), ok=False)
        require(result.returncode != 0 and "not clean" in result.stderr,
                "Dirty checkout was not rejected")
        require(run("git", "status", "--porcelain", cwd=installed).stdout == before,
                "Rejected reapplication changed the worktree")
        print("PASS dirty checkout rejected")

        clean = checkout("rejected")
        broken = tmp / "broken-installer"
        broken.mkdir()
        shutil.copy2(ROOT / "apply.sh", broken / "apply.sh")
        shutil.copy2(ROOT / "stack.py", broken / "stack.py")
        shutil.copy2(ROOT / "upstream.json", broken / "upstream.json")
        shutil.copytree(ROOT / "patches", broken / "patches")
        last = broken / "patches" / patches[-1].name
        last.write_text("diff --git a/AGENTS.md b/AGENTS.md\n"
                        "--- a/AGENTS.md\n+++ b/AGENTS.md\n@@\n+broken\n")
        result = run(str(broken / "apply.sh"), str(clean), ok=False)
        require(result.returncode != 0 and "garbage" in result.stderr,
                "Malformed late patch was not rejected during preflight")
        require(run("git", "status", "--porcelain", cwd=clean).stdout == "",
                "Failed preflight modified the target")
        print("PASS malformed rank 9 rejected before any target changes")

        intact = tmp / "intact-installer"
        shutil.copytree(ROOT, intact, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        missing = next((intact / "patches").glob("01-*.patch"))
        saved = missing.read_bytes()
        missing.unlink()
        result = run(str(intact / "apply.sh"), str(clean), ok=False)
        require(result.returncode != 0 and "rank 1 through 9" in result.stderr,
                "Missing rank was not rejected")
        require(run("git", "status", "--porcelain", cwd=clean).stdout == "",
                "Missing rank changed target")
        missing.write_bytes(saved)
        reference = intact / "overlay/bend2/main.ts"
        reference.write_bytes(reference.read_bytes() + b"\n// delivery drift\n")
        result = run(str(intact / "apply.sh"), str(clean), ok=False)
        require(result.returncode != 0 and "Delivery bytes differ" in result.stderr,
                "Preflight did not detect delivery drift")
        require(run("git", "status", "--porcelain", cwd=clean).stdout == "",
                "Delivery mismatch changed target")
        reference.write_bytes((ROOT / "overlay/bend2/main.ts").read_bytes())
        marker = b"diff --git a/AGENTS.md b/AGENTS.md\n"
        require(marker in saved, "Rank 1 has no AGENTS entry")
        missing.write_bytes(saved.replace(marker, marker + b"old mode 100644\nnew mode 100755\n", 1))
        result = run(str(intact / "apply.sh"), str(clean), ok=False)
        require(result.returncode != 0 and "mode" in result.stderr,
                "Changed upstream mode was not rejected")
        require(run("git", "status", "--porcelain", cwd=clean).stdout == "",
                "Mode mismatch changed target")
        print("PASS missing rank, delivery drift and mode changes rejected before writes")

        run("git", "checkout", "--detach", f"{PIN}^", cwd=clean)
        result = run(str(ROOT / "apply.sh"), str(clean), ok=False)
        require(result.returncode != 0 and "must be pinned" in result.stderr,
                "Wrong upstream commit was not rejected")
        require(run("git", "status", "--porcelain", cwd=clean).stdout == "",
                "Wrong-pin rejection modified the target")
        print("PASS wrong pin rejected")

    if shutil.which("bun") is None:
        print("SKIP Bun CLI smoke checks: bun is not installed")


if __name__ == "__main__":
    main()

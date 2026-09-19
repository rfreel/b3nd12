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
    manifest = json.loads((ROOT / "delivery-manifest.json").read_text())
    expected = {entry["path"]: ROOT / entry["source"] for entry in manifest["files"]}
    require(len(expected) == 25, "Reviewed delivery must contain exactly 25 paths")
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

        for name in ("README.md", "bend2/main.ts", "guide/agent/PROGRAM.md"):
            file = installed / name
            installed_bytes = file.read_bytes()
            file.write_bytes(installed_bytes + b"\nStaged discrepancy\n")
            run("git", "add", "--", name, cwd=installed)
            file.write_bytes(installed_bytes)
            index_before = (installed / ".git/index").read_bytes()
            result = run(sys.executable, str(ROOT / "stack.py"), str(installed), ok=False)
            require(result.returncode != 0 and "real index differs" in result.stderr,
                    f"Verifier accepted staged non-theory discrepancy: {name}")
            require((installed / ".git/index").read_bytes() == index_before,
                    "Verifier rewrote staged caller content")
            require(file.read_bytes() == installed_bytes,
                    "Verifier rewrote the correct working file")
            # Only restore this disposable fixture's index; production never resets staging.
            run("git", "reset", "HEAD", "--", name, cwd=installed)
        run("git", "add", "--", "bend2/main.ts", cwd=installed)
        index_before = (installed / ".git/index").read_bytes()
        result = run(sys.executable, str(ROOT / "stack.py"), str(installed), ok=False)
        require(result.returncode != 0 and "real index differs" in result.stderr,
                "Verifier accepted staging of otherwise correct delivered bytes")
        require((installed / ".git/index").read_bytes() == index_before,
                "Verifier changed staged delivery")
        run("git", "reset", "HEAD", "--", "bend2/main.ts", cwd=installed)
        run("git", "config", "diff.ignoreSubmodules", "all", cwd=installed)
        run("git", "update-index", "--add", "--cacheinfo", f"160000,{PIN},staged-module", cwd=installed)
        index_before = (installed / ".git/index").read_bytes()
        result = run(sys.executable, str(ROOT / "stack.py"), str(installed), ok=False)
        require(result.returncode != 0 and "real index differs" in result.stderr,
                "Git configuration hid a staged gitlink")
        require((installed / ".git/index").read_bytes() == index_before,
                "Verifier changed staged gitlink")
        run("git", "reset", "HEAD", "--", "staged-module", cwd=installed)
        intention = installed / "staged-intention"
        intention.write_text("intent to add\n")
        run("git", "add", "--intent-to-add", "--", "staged-intention", cwd=installed)
        intention.unlink()
        index_before = (installed / ".git/index").read_bytes()
        result = run(sys.executable, str(ROOT / "stack.py"), str(installed), ok=False)
        require(result.returncode != 0 and "real index differs" in result.stderr,
                "Intent-to-add entry escaped the pinned index policy")
        require((installed / ".git/index").read_bytes() == index_before,
                "Verifier changed intent-to-add staging")
        run("git", "reset", "HEAD", "--", "staged-intention", cwd=installed)
        run(sys.executable, str(ROOT / "stack.py"), str(installed))
        print("PASS real index remains pinned; staged discrepancies refused without writes")

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
        shutil.copy2(ROOT / "bounded.py", broken / "bounded.py")
        shutil.copy2(ROOT / "delivery-manifest.json", broken / "delivery-manifest.json")
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
        accidental = intact / "guide/agent/ACCIDENTAL.md"
        accidental.write_text("Unreviewed file must not change delivery.\n")
        result = run(sys.executable, "-c",
                     "import stack; assert len(stack.expected_files()) == 25; "
                     "assert 'guide/agent/ACCIDENTAL.md' not in stack.expected_files()",
                     cwd=intact)
        print("PASS discovery-glob additions cannot expand frozen manifest")
        sealed_target = checkout("sealed-patches")
        verifier = intact / "stack.py"
        verifier_source = verifier.read_text()
        verifier.write_text(verifier_source + '\nif __name__ == "__main__" and len(sys.argv) == 3 and not sys.argv[1].startswith("--"):\n'
                            '    next((ROOT / "patches").glob("01-*.patch")).write_text("broken after preflight\\n")\n')
        original_patch = next((intact / "patches").glob("01-*.patch"))
        original_patch_bytes = original_patch.read_bytes()
        run(str(intact / "apply.sh"), str(sealed_target))
        require(original_patch.read_bytes() == b"broken after preflight\n",
                "Mutation control did not run")
        verify(sealed_target)
        verifier.write_text(verifier_source)
        original_patch.write_bytes(original_patch_bytes)
        print("PASS installation uses preflighted snapshot despite source patch mutation")
        manifest_path = intact / "delivery-manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        for field, value in (("mode", "100755"), ("role", "additive")):
            altered = json.loads(manifest_bytes)
            altered["files"][0][field] = value
            if field == "role":
                altered["files"][0]["source"] = "AGENTS.md"
            manifest_path.write_text(json.dumps(altered))
            result = run(str(intact / "apply.sh"), str(clean), ok=False)
            require(result.returncode != 0 and "Delivery mode or role differs" in result.stderr,
                    "Manifest mode/role drift was not rejected")
            require(run("git", "status", "--porcelain", cwd=clean).stdout == "",
                    "Manifest drift changed target")
        manifest_path.write_bytes(manifest_bytes)
        print("PASS declared modes and roles checked against pinned upstream")
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

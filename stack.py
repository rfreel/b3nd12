"""Pinned delivery checks shared by the installer and management CLI."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
PIN = json.loads((ROOT / "upstream.json").read_text())["commit"]


class Failure(Exception):
    def __init__(self, code, message, correction, status=5, **context):
        super().__init__(message)
        self.status = status
        self.error = dict(code=code, message=message, context=context,
                          correction=correction, examples=["python3 b3nd12.py --help"])


def git(target, *args, env=None):
    result = subprocess.run(["git", "-C", str(target), *args],
                            capture_output=True, env=env)
    if result.returncode:
        raise Failure("GIT_FAILED", result.stderr.decode(errors="replace").strip(),
                      "Check Git and the checkout path.", 3, target=str(target))
    return result.stdout


def expected_files():
    expected = {p: ROOT / "overlay" / p for p in
                ("AGENTS.md", "bend2/main.ts", "gates/repo.ts", "gates/ping.ts")}
    for pattern in ("CLAUDE.md", "guide/agent/*.md", "guide/agent/*.json",
                    "guide/agent/proof/*.md", "evals/README.md",
                    "evals/_template.sidecar.json", "evals/_sidecar.schema.json"):
        for file in ROOT.glob(pattern):
            expected[file.relative_to(ROOT).as_posix()] = file
    return expected


def target_check(target, clean=False):
    target = Path(target).resolve()
    if not target.is_dir():
        raise Failure("NOT_FOUND", "Checkout directory does not exist.",
                      "Supply the path to the pinned Bend checkout.", 1, target=str(target))
    top = Path(os.fsdecode(git(target, "rev-parse", "--show-toplevel")).strip()).resolve()
    if top != target:
        raise Failure("INVALID_TARGET", "Use the checkout root, not a subdirectory.",
                      "Pass the Git worktree root.", 2, target=str(target))
    head = git(target, "rev-parse", "HEAD").decode().strip()
    if head != PIN:
        raise Failure("WRONG_PIN", "Checkout is not at the declared Bend revision.",
                      "Use a separate clean checkout at the required commit.", 3,
                      expected=PIN, actual=head)
    if clean and git(target, "status", "--porcelain"):
        raise Failure("DIRTY_TARGET", "Checkout has existing changes.",
                      "Use a separate clean checkout; preserve existing work.", 3)
    return target


def patch_files():
    patches = sorted((ROOT / "patches").glob("[0-9][0-9]-*.patch"))
    if [int(p.name[:2]) for p in patches] != list(range(1, 10)):
        raise Failure("PATCH_SEQUENCE", "Expected exactly one patch at each rank 1 through 9.",
                      "Restore the declared patch stack.")
    return patches


def verify(target, index=None):
    target = target_check(target)
    expected = expected_files()
    env = {**os.environ, "GIT_INDEX_FILE": str(index)} if index else None
    if index:
        changed = git(target, "diff", "--cached", "--name-only", "-z", "HEAD", env=env)
    else:
        changed = git(target, "diff", "--name-only", "-z", "HEAD")
        changed += git(target, "ls-files", "--others", "--exclude-standard", "-z")
    paths = set(os.fsdecode(changed).rstrip("\0").split("\0")) - {""}
    if paths != set(expected):
        raise Failure("FILE_SCOPE", "Installed file set differs from the declared delivery.",
                      "Use a clean pinned checkout and the complete stack.",
                      missing=sorted(set(expected)-paths), extra=sorted(paths-set(expected)))
    modes = {}
    for entry in git(target, "ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if entry:
            header, name = entry.split(b"\t", 1)
            modes[os.fsdecode(name)] = header.split()[0]
    staged = {}
    if index:
        for entry in git(target, "ls-files", "--stage", "-z", env=env).split(b"\0"):
            if entry:
                header, name = entry.split(b"\t", 1)
                staged[os.fsdecode(name)] = header.split()[0]
    for name in expected:
        mode = modes.get(name, b"100644")
        actual = staged.get(name) if index else (b"100755" if (target / name).stat().st_mode & 0o111 else b"100644")
        if actual != mode:
            raise Failure("FILE_MODE", "Delivery mode differs: " + name,
                          "Preserve upstream modes and use regular additive files.")
    for name, reference in expected.items():
        file = target / name
        data = git(target, "show", ":" + name, env=env) if index else file.read_bytes()
        if data != reference.read_bytes() or (not index and file.is_symlink()):
            raise Failure("CONTENT_MISMATCH", "Delivery bytes differ: " + name,
                          "Restore the matching patch and delivery file.", file=name)
    original = git(target, "show", PIN + ":bend2/bend.ts")
    theory = git(target, "show", ":bend2/bend.ts", env=env) if index else (target / "bend2/bend.ts").read_bytes()
    if original != theory or (not index and original != git(target, "show", ":bend2/bend.ts")):
        raise Failure("THEORY_CHANGED", "The protected theory differs from the pin.",
                      "Preserve the change separately and use a clean pinned checkout.")
    if not index and git(target, "diff", "--summary", "HEAD"):
        raise Failure("FILE_MODE", "Upstream file modes changed.", "Restore the upstream file modes.")
    git(target, "diff", "--cached" if index else "--no-ext-diff", "--check", env=env)
    return dict(pin=PIN, files=len(expected), theory_unchanged=True,
                delivery="byte-identical", checks=["pin", "scope", "bytes", "theory", "whitespace"])


if __name__ == "__main__":
    import sys
    try:
        if len(sys.argv) == 2:
            verify(sys.argv[1])
        elif len(sys.argv) == 3:
            verify(sys.argv[1], sys.argv[2])
        else:
            patch_files()
    except (Failure, OSError) as exc:
        print("verify: " + str(exc), file=sys.stderr)
        sys.exit(1)

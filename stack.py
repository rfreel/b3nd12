"""Pinned delivery checks shared by the installer and management CLI."""
import json
import os
from pathlib import Path
import stat
import subprocess
import bounded

ROOT = Path(__file__).resolve().parent
PIN = json.loads((ROOT / "upstream.json").read_text())["commit"]


class Failure(Exception):
    def __init__(self, code, message, correction, status=5, **context):
        super().__init__(message)
        self.status = status
        self.error = dict(code=code, message=message, context=context,
                          correction=correction, examples=["python3 b3nd12.py --help"])


def git(target, *args, env=None):
    ambient_git_check()
    try:
        result = bounded.run(["git", "-C", str(target), *args], env=env)
    except subprocess.TimeoutExpired as exc:
        raise Failure("GIT_TIMEOUT", "Git exceeded its execution deadline.",
                      "Check checkout access and retry.", 3, target=str(target)) from exc
    except bounded.OutputLimitExceeded as exc:
        raise Failure("GIT_OUTPUT_LIMIT", "Git exceeded the diagnostic output limit.",
                      "Inspect the checkout size and configuration before retrying.", 3,
                      target=str(target), limit_bytes=exc.limit_bytes,
                      observed_bytes=exc.observed_bytes) from exc
    if result.returncode:
        raise Failure("GIT_FAILED", result.stderr.decode(errors="replace").strip(),
                      "Check Git and the checkout path.", 3, target=str(target))
    return result.stdout


def ambient_git_check():
    overrides = {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                 "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_ATTR_SOURCE", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES",
                 "GIT_EXTERNAL_DIFF"}
    forbidden = overrides.intersection(os.environ)
    if forbidden:
        raise Failure("GIT_ENVIRONMENT", "Unsupported Git environment: " + ", ".join(sorted(forbidden)),
                      "Unset Git overrides before accessing the checkout.", 3)


def install_guard(target, filesystem=True):
    target = Path(target).resolve()
    config = git(target, "config", "--null", "--list").decode(errors="replace").split("\0")
    for item in config:
        key, _, value = item.partition("\n")
        if ((key in ("core.fsmonitor", "diff.external") and value.lower() not in ("", "false"))
                or (key == "core.autocrlf" and value.lower() not in ("", "false"))):
            raise Failure("GIT_CONFIGURATION", "Unsupported Git configuration: " + key,
                          "Use a checkout without external hooks or newline conversion.", 3)
    expected = expected_files()
    tracked = set(os.fsdecode(git(target, "ls-tree", "-r", "--name-only", "-z", "HEAD")).rstrip("\0").split("\0"))
    attrs = git(target, "check-attr", "-z", "filter", "working-tree-encoding", "--", *sorted(tracked | expected.keys())).split(b"\0")
    for offset in range(0, len(attrs) - 2, 3):
        name, attr, value = attrs[offset:offset + 3]
        if value not in (b"unspecified", b"unset"):
            raise Failure("GIT_ATTRIBUTES", "Unsupported Git attribute: " + os.fsdecode(name) + ": " + os.fsdecode(attr),
                          "Use a checkout without active filters or encoding conversion.", 3)
    if not filesystem:
        return target
    for name in expected:
        file = target / name
        for parent in file.parents:
            if parent == target.parent:
                break
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise Failure("FILESYSTEM_OBSTRUCTION", "Obstructed parent: " + str(parent),
                              "Preserve the obstruction and use a clean checkout.", 3)
            if parent.exists() and parent.stat().st_mode & 0o300 != 0o300:
                raise Failure("FILESYSTEM_OBSTRUCTION", "Inaccessible parent: " + str(parent),
                              "Use a writable, searchable checkout.", 3)
        if file.is_symlink() or (name not in tracked and file.exists()):
            raise Failure("FILESYSTEM_OBSTRUCTION", "Checkout is not clean; colliding delivery path: " + str(file),
                          "Preserve caller content and use a clean checkout.", 3)
        if file.exists() and (not file.is_file() or file.stat().st_mode & 0o600 != 0o600):
            raise Failure("FILESYSTEM_OBSTRUCTION", "Inaccessible delivery path: " + str(file),
                          "Use readable, writable regular delivery files.", 3)
    return target


def expected_files():
    manifest = json.loads((ROOT / "delivery-manifest.json").read_text())
    expected = {}
    if manifest.get("schema") != "b3nd12.delivery.v1" or len(manifest.get("files", [])) != 25:
        raise Failure("DELIVERY_MANIFEST", "Invalid delivery manifest.", "Restore the reviewed 25-file manifest.")
    for entry in manifest["files"]:
        name, source = entry["path"], entry["source"]
        role = entry["role"]
        path = Path(name)
        if (path.is_absolute() or ".." in path.parts or path.as_posix() != name
                or name in expected or entry["mode"] not in ("100644", "100755")
                or role not in ("overlay", "additive")
                or source != ("overlay/" + name if role == "overlay" else name)):
            raise Failure("DELIVERY_MANIFEST", "Invalid delivery entry: " + name,
                          "Restore the reviewed paths, modes and roles.")
        expected[name] = ROOT / source
    return expected


def target_check(target, clean=False):
    target = Path(target).resolve()
    if not target.is_dir():
        raise Failure("NOT_FOUND", "Checkout directory does not exist.",
                      "Supply the path to the pinned Bend checkout.", 1, target=str(target))
    top = Path(os.fsdecode(git(target, "rev-parse", "--show-toplevel")).removesuffix("\n")).resolve()
    if top != target:
        raise Failure("INVALID_TARGET", "Use the checkout root, not a subdirectory.",
                      "Pass the Git worktree root.", 2, target=str(target))
    head = git(target, "rev-parse", "HEAD").decode().strip()
    if head != PIN:
        raise Failure("WRONG_PIN", "Checkout is not at the declared Bend revision.",
                      "Use a separate clean checkout at the required commit.", 3,
                      expected=PIN, actual=head)
    install_guard(target, filesystem=False)
    if clean and git(target, "status", "--porcelain"):
        raise Failure("DIRTY_TARGET", "Checkout has existing changes.",
                      "Use a separate clean checkout; preserve existing work.", 3)
    return target


def patch_files(directory=None):
    patches = sorted((Path(directory) if directory else ROOT / "patches").glob("[0-9][0-9]-*.patch"))
    if [int(p.name[:2]) for p in patches] != list(range(1, 10)):
        raise Failure("PATCH_SEQUENCE", "Expected exactly one patch at each rank 1 through 9.",
                      "Restore the declared patch stack.")
    for patch in patches:
        if any(line == b"GIT binary patch" or line.startswith(b"Binary files ")
               for line in patch.read_bytes().splitlines()):
            raise Failure("BINARY_PATCH", "Binary patches are outside the delivery: " + patch.name,
                          "Use only the reviewed text patch stack.")
    return patches


def verify(target, index=None):
    target = target_check(target)
    expected = expected_files()
    manifest = json.loads((ROOT / "delivery-manifest.json").read_text())
    declared = {entry["path"]: entry for entry in manifest["files"]}
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
    for name in sorted(modes.keys() | expected.keys()):
        mode = modes.get(name, b"100644")
        if name in declared:
            entry = declared[name]
            if (entry["mode"].encode() != mode
                    or entry["role"] != ("overlay" if name in modes else "additive")):
                raise Failure("DELIVERY_MANIFEST", "Delivery mode or role differs: " + name,
                              "Restore the reviewed manifest matching the pin.")
        if index:
            actual = staged.get(name)
        else:
            file_mode = (target / name).lstat().st_mode
            if stat.S_ISREG(file_mode):
                actual = b"100755" if file_mode & 0o111 else b"100644"
            elif stat.S_ISLNK(file_mode):
                actual = b"120000"
            else:
                actual = b"160000" if stat.S_ISDIR(file_mode) else None
        if actual != mode:
            raise Failure("FILE_MODE", "File mode differs: " + name,
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
    if not index and git(target, "diff", "--cached", "--raw", "--no-ext-diff",
                         "--ignore-submodules=none", "--ita-visible-in-index", "HEAD"):
        raise Failure("STAGED_INDEX", "The real index differs from the pinned tree.",
                      "Preserve staged work separately and verify an unstaged installation.")
    if not index and git(target, "diff", "--summary", "HEAD"):
        raise Failure("FILE_MODE", "Upstream file modes changed.", "Restore the upstream file modes.")
    git(target, "diff", "--cached" if index else "--no-ext-diff", "--check", env=env)
    return dict(pin=PIN, files=len(expected), theory_unchanged=True,
                delivery="byte-identical", checks=["pin", "scope", "bytes", "theory", "index", "whitespace"])


if __name__ == "__main__":
    import sys
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--patches":
            patch_files(sys.argv[2])
        elif len(sys.argv) == 3 and sys.argv[1] == "--guard":
            install_guard(sys.argv[2])
        elif len(sys.argv) == 2:
            verify(sys.argv[1])
        elif len(sys.argv) == 3:
            verify(sys.argv[1], sys.argv[2])
        else:
            patch_files()
    except (Failure, OSError) as exc:
        print("verify: " + str(exc), file=sys.stderr)
        sys.exit(1)

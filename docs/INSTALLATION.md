# Pinned installation and replay

The installation target is a clean Bend checkout at
`e5a4c4cfe980c2e4e70571562efb5197fe27b2f4`. Use the checkout root and retain
exclusive access to it throughout installation.

```sh
python3 b3nd12.py apply /path/to/bend-checkout --json
python3 b3nd12.py verify /path/to/bend-checkout --human
```

The shell entry points `apply.sh TARGET` and `verify.sh TARGET` remain available.
The installer does not reset, stash or clean caller changes.

## Delivery authority

[delivery-manifest.json](../delivery-manifest.json) names exactly 25 paths, their
expected-byte sources, Git modes and roles. Four entries replace existing upstream
files using the independent overlays; 21 entries are additions. Adding another
Markdown or JSON file to a guide directory cannot expand this list. Manifest
roles and modes must agree with the pinned tree: upstream files retain their
modes, and additive files are regular files with mode `100644`.

The installer copies the nine numbered patches into a temporary directory. It
checks that the copy contains exactly one patch at each rank, applies those
copies to a temporary Git index, and verifies the result against the manifest
and expected bytes. Only a passing complete preflight permits worktree writes.
Ordered installation then uses the same copied patch bytes. Editing an original
patch after preflight cannot change the installed bytes.

Binary patches are refused explicitly. Path escapes, deletions, symlinks and
extra paths in the tested mutation fixtures fail before worktree writes through
Git validation or exact delivery verification. The real target index is not used
for preflight and is preserved by installation.

## Checkout and Git boundaries

The installer refuses ignored files that collide with additive delivery paths,
symlink parents, non-directory parents and inaccessible delivery paths. Its
permission check requires owner read/write bits for existing delivery files and
owner write/search bits for existing parent directories. This is a conservative
check, not a complete ACL or network-filesystem permissions model. Refusals name
the obstruction and leave caller content in place.

The following ambient Git variables are refused because they can redirect
repository access or change interpretation:

```text
GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR
GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
GIT_CONFIG GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT
GIT_ATTR_SOURCE GIT_NAMESPACE GIT_CEILING_DIRECTORIES GIT_EXTERNAL_DIFF
```

The temporary index override is supplied internally after these checks. Harmless
presentation settings such as `GIT_PAGER` are allowed. Normal Git configuration
files are still read; their evaluated settings are checked.

Active `core.fsmonitor`, `diff.external` and `core.autocrlf` settings are refused.
A nonempty value other than `false` is considered active for these checks. Active
`filter` and `working-tree-encoding` attributes on tracked or declared delivery
paths are refused before status or diff can invoke content filters. An unused
filter definition alone is allowed. These rules define the supported installation
environment; they do not audit every possible Git configuration setting.

Independent clones and linked worktrees are supported. The linked-worktree test
checks that installing one checkout preserves the sibling checkout and its index.
The independent-clone test uses `--no-local`, checks for absent alternates, checks
its objects and installs while its configured origin is unavailable.

## What verification establishes

Static verification checks the exact changed and additive path set, delivery
bytes, Git file types and executable bits, protected theory bytes, and whitespace.
Modes are checked across the pinned tree and additions, including untouched
upstream files, even when `core.filemode=false`. This checks Git modes, not every
POSIX permission bit or ACL entry.

`bend2/bend.ts` is compared with the pin in both the working tree and the real
index. Temporary-index preflight checks all staged delivery content and modes.
After installation, exact delivery bytes are checked in the worktree. The real
index must still describe the pinned tree. For an otherwise valid delivery,
staged differences, including a correctly staged delivery file, are refused with
`STAGED_INDEX`. Earlier scope, content or theory failures may take precedence.
Verification leaves the index bytes untouched. Installation starts from a clean
index and preserves it.
Intent-to-add entries and staged gitlinks are also refused, even when Git's
submodule-diff configuration would hide the staged change.
Ignored artifacts outside the declared delivery are outside the path-set check.

`verify.sh` reports static verification separately from runtime smoke checks.
When Bun is on PATH, it runs installed `--help`, `guide` and `--why BND101` commands.
A failing or timed-out smoke command fails verification. Without Bun, it reports
runtime smoke as `UNAVAILABLE`; static success does not imply runtime coverage.
These smoke checks do not establish native or GPU execution.

Git and smoke subprocesses have 15-second deadlines through `bounded.py`, with
a default combined stdout/stderr limit of 1 MiB. Receipt operations use bounded
commands with 30-second defaults, 60 seconds for cloning and 120 seconds for the
whole installer. These are subprocess limits, not a universal deadline for every
filesystem operation. The bounded helper retains captured diagnostics on timeout
or output-limit failure; individual callers may report only the failure summary.

## Installation receipts

The repository-only receipt tool records identities for a statically verified
installation. Create the output parent directory first and choose a new receipt
path outside this repository:

```sh
python3 installation_receipt.py record \
  /path/to/installed-bend \
  /path/outside/repository/installation.json
```

The JSON result contains a `sha256` value. Retain that value independently of the
receipt. Replay requires that retained value explicitly:

```sh
python3 installation_receipt.py replay \
  /path/outside/repository/installation.json \
  --sha256 RETAINED_SHA256 \
  --source /path/to/pinned-bend \
  --destination /path/outside/repository/new-bend-checkout
```

Replace `RETAINED_SHA256` with the exact digest returned by the record command.
Recomputing a digest from an untrusted replacement receipt would remove the
independent integrity check.

The receipt schema is `b3nd12.installation-receipt.v1`. It binds the upstream pin,
ordered patch hashes, manifest hash, delivery source hashes, expected modes and
roles, verifier and installer source hashes, and executable identities for the
receipt's Python interpreter, the installer's PATH-resolved `python3`, Git, the
shell and optional Bun. Both Python identities are checked even when the receipt
command uses an absolute interpreter path. Matching version strings alone are
insufficient: executable hashes must also match. Changed tool builds require a new receipt,
even when their version strings are identical.

Replay validates the receipt digest and current reviewed source identities before
creating a checkout. It clones the supplied pinned source with `--no-local`, checks
out the pin, refuses object-store alternates, checks identities again, runs the
existing installer and compares exact verification results. Receipt fields never
supply executable commands. Replay executes current trusted repository code,
not code copied from the receipt. Receipt creation checks static delivery; it does
not rerun runtime smoke checks. Replay invokes the installer, whose smoke behavior
follows Bun availability as described above.

An existing receipt or destination is refused. Resolved output paths within this
repository are refused, including symlink aliases into it. Reports return JSON;
operation failures return exit 1, and argument-parser errors return exit 2.

## Evidence and limits

Run the acceptance tests against a repository containing the pin:

```sh
python3 tests/patch_stack.py /path/to/pinned-bend
python3 tests/install_adversarial.py /path/to/pinned-bend
python3 tests/install_receipt.py /path/to/pinned-bend
```

[Patch-stack tests](../tests/patch_stack.py) exercise exact 25-file parity, ordered
installation, source-patch mutation after preflight, and mode and role drift.
[Adversarial installation tests](../tests/install_adversarial.py) cover filesystem
obstructions, Git overrides, patch mutations, independent clones and linked
worktrees. [Receipt tests](../tests/install_receipt.py) cover replay and refusals.
Receipt tampering and source, manifest, verifier, oracle or pin drift are
refused before the replay destination is created in the tested cases.

Installation remains nontransactional after its first worktree write. A disk
failure, permission change, interruption or failed runtime smoke check can leave
a partially or fully written checkout with a failing result. The installer leaves
that checkout available for diagnosis and performs no destructive rollback.
Replay can likewise leave its new clone after a later failure.

All guarantees assume cooperative source files and exclusive checkout access.
Temporary patch copies and retained hashes do not isolate a hostile process with
the same filesystem permissions. Concurrent replacement of source, controller,
output paths or temporary files remains outside this boundary.

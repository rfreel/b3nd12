# Evidence protocol

The frozen routing replay writes a bounded experiment packet outside the
repository. The packet contains input snapshots, observations, candidate bytes,
a hash-linked ledger, and a final state. Independent verification reconstructs
the finite routing result without importing or executing saved Python files.

The retained contract digest identifies the reviewed policy. The retained
terminal digest identifies the completed ledger. Keep both outside the worker's
write access. A digest copied from an untrusted packet at verification time does
not establish that the packet is the one originally retained.

## Produce and retain a packet

From the repository root, run the following with actual absolute paths. The
contract digest below identifies the current frozen TODO contract.

```sh
python3 accretion/program.py \
  --contract-sha256 8e0074c4bddb7a8de684d11d7a2db93021c013bd290d2fe8378dff941fb1c40b \
  --bend-root /path/to/pinned/bend \
  --bun /path/to/bun \
  --output /path/outside/repository/new-evidence
```

The output directory must be new. The controller refuses repository-contained
paths, including resolved symlink aliases. The replay does not install routes.
It permits six attempts and three observations per valid candidate. Rejected
and neutral attempts consume the same attempt budget as productive attempts.

After the controller finishes, extract the terminal digest from its ledger:

```sh
python3 - /path/outside/repository/new-evidence <<'PY'
import json
from pathlib import Path
import sys
rows = (Path(sys.argv[1]) / 'ledger.jsonl').read_text().splitlines()
last = json.loads(rows[-1])
if last['event']['kind'] != 'stop':
    raise SystemExit('no completed ledger to retain')
print(last['sha256'])
PY
```

Retain this value through the operator's trusted channel. This extraction only
locates the value; it is not independent verification or authentication.

## Verify and reconstruct

Supply the separately retained values, replacing the uppercase placeholders:

```sh
python3 accretion/verify_evidence.py /path/outside/repository/new-evidence \
  --contract-sha256 RETAINED_CONTRACT_SHA256 \
  --terminal-sha256 RETAINED_TERMINAL_SHA256
```

The verifier checks record order and hashes, the manifest binding in the baseline
event, frozen input hashes, candidate and receipt bindings, finite route costs,
recorded checker outcomes, verdicts, completion credit, stopping conditions, and
successor restrictions. It uses its own routing calculation. It does not invoke
the saved controller or accept a saved verdict as its decision.

| Status | Meaning | Exit |
|---|---|---|
| `complete` | The terminal ledger and required evidence pass reconstruction | 0 |
| `incomplete` | A required artifact or terminal stop record is absent | 1 |
| `invalid` | Available evidence fails parsing, binding, or semantic checks | 1 |

A complete packet can describe an unresolved or budget-exhausted experiment.
Check `summary.stop` and `summary.completed` before interpreting the result as
outcome completion. A complete packet does not authorize route installation.

The durable terminal stop record is the commit point. `summary.json` is a
projection of that record and the verified observations. If the summary file is
absent, verification reconstructs and returns it without writing into the
packet. An existing summary must match the reconstruction. The Python
`verify()` API returns the reconstructed summary; `inspect_evidence()` adds the
complete, incomplete, or invalid classification.

Incomplete classification does not certify the rest of an interrupted packet.
For example, a valid ledger prefix without a stop record is incomplete, even
though remaining artifacts have not been fully checked. No incomplete result
receives a successful verification exit.

## Durability and bounds

Evidence writes use a temporary file in the destination directory, complete
writes, file synchronization, replacement, and directory synchronization. The
ledger is logically append-only; each publication replaces it with the complete
record sequence. This avoids exposing a partially appended JSON line. Run
directories require exclusive ownership. These operations use POSIX filesystem
interfaces; they do not promise storage behavior beyond the filesystem's
synchronization guarantees.

| Boundary | Limit or behavior |
|---|---|
| Valid routing table | 4,096 bytes |
| Saved candidate input | At most 4,097 bytes, including the oversized-input discriminator |
| Controller attempts | Six |
| Observations per valid candidate | Three |
| Evidence artifact write | 8 MiB |
| Default subprocess capture | 1 MiB across stdout and stderr |
| Recorded checker capture | 256 KiB across stdout and stderr |
| Default subprocess deadline | 15 seconds |
| Cooperative wrapper depth | 0 through 4; deeper wrappers refuse before spawning |
| ZIP members | 128 files |
| ZIP member size | 8 MiB |
| ZIP expanded total | 32 MiB |
| ZIP file size | 40 MiB |

`bounded.py` starts subprocesses in a new POSIX session and captures output
without allowing unbounded pipes. On timeout or output overflow it sends
`SIGTERM` to the process group, allows a bounded interval for cooperative cleanup,
then sends `SIGKILL`. The outermost wrapper allows one second. Each nested
wrapper allows 0.25 seconds less, down to zero at depth 4. The inherited
`B3ND12_BOUNDED_DEPTH` records this context; deeper wrappers refuse before
spawning. Inner wrappers therefore have an earlier cleanup deadline than their
callers. The captured prefix is retained.

This schedule assumes responsive cooperative wrappers that preserve the depth
context and receive execution time during cleanup. It does not guarantee
cleanup under arbitrary scheduling delays, altered depth context, or deliberate
session escape. The wrapper is not a general process-tree containment mechanism.

The smaller recorded-checker limit leaves room for three observations and JSON
escaping within the artifact write limit. It bounds captured raw bytes; decoded
replacement characters and JSON escapes can occupy more bytes in the receipt.

Checker observations distinguish an exact certificate, the exact pinned law
refusal, timeout, spawn error, crash, missing or malformed certificate, process
error, and output overflow. Infrastructure failures produce `UNKNOWN`, preserve
available observations, and cannot earn completion credit. Truncated output is
never substituted for a successful certificate.

Artifact and subprocess bounds are separate from ZIP transfer bounds. The
controller does not claim an unlimited-run storage quota or hostile-process
isolation. A failed artifact write can leave an incomplete run requiring
inspection; replay does not resume or overwrite it.

## Recheck accepted books

Offline verification checks consistency of retained observations. Rechecking
also executes the pinned checker against reconstructed accepted books:

```sh
python3 accretion/recheck.py /path/outside/repository/new-evidence \
  --contract-sha256 RETAINED_CONTRACT_SHA256 \
  --terminal-sha256 RETAINED_TERMINAL_SHA256 \
  --bend-root /path/to/pinned/bend \
  --bun /path/to/bun
```

Rechecking first verifies the packet. It requires the pinned checker source and
the recorded Bun binary digest. It uses the current trusted checkout's frozen
law and proof template, checks their contract hashes, rebuilds `Evidence.bend`
from independently verified metrics, and compares all book hashes with the
observation. Saved Python snapshots remain data. Only accepted books are
rechecked; this command does not reproduce process failures or authenticate the
original run.

## Export and import

```sh
python3 accretion/archive.py export /path/outside/repository/new-evidence \
  /path/outside/repository/evidence.zip \
  --contract-sha256 RETAINED_CONTRACT_SHA256 \
  --terminal-sha256 RETAINED_TERMINAL_SHA256

python3 accretion/archive.py import /path/outside/repository/evidence.zip \
  /path/outside/repository/imported-evidence \
  --contract-sha256 RETAINED_CONTRACT_SHA256 \
  --terminal-sha256 RETAINED_TERMINAL_SHA256
```

Both destinations must be new and outside the repository, with an existing
parent directory. Export verifies a bounded copy before creating a deterministic
ZIP with fixed timestamps and file modes. Import extracts into temporary state
and verifies before publishing files into a newly reserved directory.

The format accepts stored, uncompressed regular files only. It rejects path
traversal, absolute paths, duplicate names, symlinks, device entries, encrypted
members, compressed members, and unexpected evidence files. ZIP does not provide
a hardlink restoration operation here. Import creates independent regular
files. Size limits apply before and during extraction.

These operations assume cooperative, exclusive filesystem access. Import does
not provide crash-atomic publication of an entire directory. An interruption
during publication can leave a partial destination, which must not be treated
as verified without rerunning the independent verifier. Existing destinations
are never intentionally overwritten.

## Compatibility and interpretation

The current packet schema is `b3nd12.experiment.v1`, with contract schema
`b3nd12.todo.v1`. The verifier supports the current exact snapshot set and
checker observation fields. Older packets without the baseline manifest
binding, storage helper snapshot, or required checker fields are refused rather
than silently assigned the current meaning. Accepted-book rechecking also
requires recorded book hashes.

The guarantee is conditional observation integrity. Relative to trusted retained
digests, the verifier detects alteration and independently checks the finite
conclusions. It does not establish who ran the commands, whether recorded
observations came from an actual process, or whether a worker had access to the
operator's retained state. The law covers three deterministic routing tasks;
passing evidence is not a fresh-agent productivity result.

## Focused checks

```sh
python3 tests/evidence.py /path/to/pinned/bend /path/to/bun
python3 tests/archive.py /path/to/pinned/bend /path/to/bun
python3 tests/recheck.py /path/to/pinned/bend /path/to/bun
python3 tests/storage.py /path/to/pinned/bend /path/to/bun
python3 tests/output_bounds.py /path/to/pinned/bend /path/to/bun
```

Focused evidence and archive tests passed during implementation using the pinned
Bend checkout. They cover real replay packets, exact round trips, retained-digest
checks, malformed artifacts, rehashed false inner claims, bounded transfers, and
hostile ZIP metadata. These results do not substitute for the final integrated
verification ledger or demonstrate native, GPU, or production isolation behavior.

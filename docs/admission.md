# Three-domain admission

This extends the repair pilot with a finite proof model, an evidence gate, and a
local Git transaction adapter. It does not enable automatic GitHub merges, change
host permissions, modify the Bend checker, or replace the repair report format.

## Contract

A candidate needs one authenticated receipt for each domain: behavior,
preservation, and evaluation integrity. Policy fixes a distinct producer and
required evidence kind for each. Missing or pending evidence cannot admit a
candidate. Failure or malformed evidence rejects it. All three must pass.

The manifest binds repository, target branch, expected base, candidate commit and
tree, request ID, actor, authority epoch, policy, contract, laws, checker,
toolchain, dependencies, and configuration. Digests use canonical JSON and
SHA256. Commit identifiers currently use Git SHA1 format; SHA256 repositories
are unsupported and fail validation.

The gate checks HMAC-SHA256 receipts and the bytes of referenced artifacts. It
authenticates what a configured producer said. It does not establish that the
producer ran a test or that a checked-proof label is truthful. Producers must run
the appropriate verifier before signing. Dependency digests must cover transitive
inputs; the gate cannot discover omitted dependencies.

## Trusted integration boundary

`decide(bundle, policy, keys, artifacts)` returns ACCEPTED, PENDING, or REJECTED
without mutating its inputs.

`execute(repo, repository_identity, bundle, policy, keys, artifacts)` rechecks
admission and operates only on a bare local repository. It verifies the candidate
tree and single parent. One Git ref transaction conditionally updates the target
and creates a consumed-request marker. Stale bases and reused requests fail
without partial ref changes. Symbolic targets are rejected; writes do not
dereference symbolic references. Timeout returns UNRESOLVED because a transaction
may complete before its acknowledgement is lost.

The calling controller owns the policy, keys, repository identity mapping, local
repository, Git configuration, environment, and process. Worker-supplied values
are not trusted substitutes. Keep candidate execution outside the controller and
its credentials. This API does not authenticate callers. HMAC verifiers possess
signing authority; controller compromise compromises all receipts. A public-key
adapter requires a separate design if that threat is in scope.

Policy and key snapshots remain fixed during an invocation. Epochs invalidate
old requests when the caller supplies a new policy; they do not make concurrent
policy replacement atomic with Git updates. Consumed markers must be protected
and retained. They record consumption, not a complete durable evidence history.

The transaction protects refs against concurrent participating writers. Hostile
filesystem access, hooks, Git configuration, process environment, and storage
failure remain outside the model.

## What Bend proves

`pilot/admission/LAWS.bend` has nine laws: accepted behavior, preservation, and
integrity; invalid-context rejection; useful acceptance; pending evidence; and
three state-update outcomes. The proof enumerates the 54 combinations of a
context bit and three three-valued outcomes. Generic state-update laws use
Boolean states. All nine laws check with zero unsafe terms.

The model takes context validity and evidence outcomes as inputs. It does not
prove cryptographic authenticity, arbitrary application correctness, Python/Bend
equivalence, actual Git effects, or whole-repository safety. Python's decision
partition is checked against an independently expressed acceptance table.
Missing evidence maps to the model's pending outcome.

The ergonomics extension also executes all 54 model cases in Bend and compares
them with authenticated Python gate requests. This establishes correspondence
for the finite partition. It does not establish equivalence outside that model.
Use `./repo verify --scope proof` to check the law inventory, generated proof,
and runtime correspondence together.

## Reproduce

With the pinned upstream checkout and overlay installed:

```sh
./scripts/verify-admission.sh /path/to/patched-bend
python3 -m unittest discover -s tests -p 'test_admission_gate.py' -v
python3 experiments/admission_stress.py --output /tmp/admission.json
```

The campaign covers all 1,024 combinations of four evidence states per domain
and four binary context attacks. It also tests every manifest field, malformed
shapes, artifact tampering, receipt authentication, trust-role collapse, real Git
updates, replay, stale bases, concurrent requests, symbolic refs, and a lost
acknowledgement after an actual commit. The last test injects a timeout after the
transaction; it is not a power-loss durability test.

Thirteen seeded faults run in disposable copies. Detection requires the named
test's assertion failure, so syntax/import errors do not count. Results record
source fingerprints and raw outputs. Each mutant has a 30-second deadline. The
campaign stops after this finite coverage; it makes no global completeness claim.

## Residual obligations

| Boundary | Status | Reopen trigger |
| --- | --- | --- |
| Application correctness | Producer evidence only | New application or contract |
| Transitive dependency coverage | Controller responsibility | New build input |
| Proof-to-Python correspondence | 54 executed Bend/Python decision cases | Decision implementation changes |
| Producer isolation and honest execution | External assumption | Real producer deployment |
| Atomic revocation and expiry | Not implemented | Concurrent policy/key rotation |
| Delegation and aggregate budgets | Not implemented | Autonomous worker scheduling |
| Policy amendment authorization | Controller-owned policy; no amendment API | Policy-management integration |
| Host protection and bypass privileges | Not configured here | GitHub merge automation |
| Durable evidence history and releases | Not implemented | Audit or release integration |
| Crash durability and external effects | Not established | Storage or non-Git requirements |

## Repair record

Review exposed symbolic-ref redirection and incorrect timeout classification.
The executor now rejects symbolic targets and reports lost acknowledgement as
unresolved. Both have regression tests. An initial malformed-input test treated
an unchanged valid integer as invalid; it now excludes only identical values
with identical types. All thirteen seeded faults were subsequently detected.

# Current work

Generated from system/roadmap.json and state/events.jsonl.

| ID | Status | Task | Dependencies |
| --- | --- | --- | --- |
| A01 | SOLVED | Validate task contracts and dependency graphs | none |
| A02 | SOLVED | Bind bounded verification to source evidence | A01 |
| A03 | SOLVED | Enforce replayable task transitions | A02 |
| A04 | SOLVED | Expose one bounded agent command surface | A03 |
| A05 | SOLVED | Measure control cost and integrity | A04 |
| A06 | SOLVED | Integrate guidance, lessons, roadmap, and CI | A05 |
| B01 | OPEN | Migrate contracts and recover interrupted journals | A06 |
| B02 | OPEN | Unify campaign and task evidence | A06 |
| B03 | OPEN | Retrieve scoped lessons and counterexamples | A06 |
| B04 | OPEN | Fingerprint and compare execution environments | B02 |
| B05 | OPEN | Evaluate performance with paired uncertainty | B04 |
| B06 | OPEN | Build held-out repair and proof task suites | B02 |
| B07 | OPEN | Run budgeted agent usability trials | B06 |
| B08 | OPEN | Reuse verified results by complete context key | B04 |
| B09 | OPEN | Isolate candidate workers from evaluator authority | B02 |
| B10 | OPEN | Coordinate work across clones with expiring leases | B09 |
| B11 | OPEN | Attest execution with independent signing | B09, B04 |
| B12 | OPEN | Enforce repository merge gates on the host | B11 |
| B13 | OPEN | Generalize finite repair laws to variable suites | B06 |
| B14 | OPEN | Learn task priorities from observed value and cost | B07 |
| B15 | OPEN | Test whether lessons transfer without regressions | B03, B07 |
| B16 | OPEN | Validate Linux and macOS recovery behavior | B01 |
| B17 | OPEN | Compact history with verified replay equivalence | B01 |
| B18 | OPEN | Evaluate a supervisor without evaluator self-modification | B07, B09 |
| B19 | OPEN | Report rolling research trajectories | B07, B15 |
| B20 | OPEN | Stop campaigns by measured continuation value | B05, B14 |

Journal head: `2cd25f4f6f1c6b8370e1b7d9b28b212cb1c6ee5112e1a3646fde2dbbfd48736c`

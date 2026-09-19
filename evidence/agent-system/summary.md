# Foundation result

Six foundation tasks are SOLVED with retained source-bound evidence. Twenty
future work packages remain OPEN. The next task is B01, explicit contract
migration and interrupted-history recovery. No unattended worker is running.

All 63 local tests passed. The first published commit passed all three GitHub
workflows: agent-system, verify-ranked-deepenings, and verify-supermodularity.
`github-checks.json` identifies that commit and the observed runs. The pull
request's checks are the authority for subsequent publication commits.

## Completed-state local benchmark

Source: `baseline-completed.json`, seven samples on the recorded host.

| Metric | Observed | 30-day target | Interpretation |
| --- | --- | --- | --- |
| Compact status | 687 bytes | At most 6000 | Below target ceiling |
| Cold status p95 | 163.4 ms | At most 150 | Target not met in this sample |
| Projection p95 | 8.8 ms | At most 30 | Below target ceiling |
| 1000-event replay p95 | 35.6 ms | At most 500 | Below target ceiling |
| Tamper rejection | 10 of 10 | All declared cases | Fixture-scoped result |
| Projection reproducibility | Identical | Identical | Same input, same projection |
| External control dependencies | 0 | 0 | Standard-library runtime |

Nineteen metrics remain UNMEASURED. These include agent task success, token
cost, dollars, isolation, cross-family learning, and long-term research yield.
No improvement claim is made for those dimensions. Cold-start variability has
not been attributed; the slower sample is retained rather than rerun away.

The prior proof campaign retains its 21-to-15 case reduction under all eight
original laws. It did not establish a speed improvement.

The evidence replacement and missing-suffix observations remain unattributed.
See `evidence-incident.md` for the observations, the separately reproduced
publication weakness, its regression test, and the remaining trust boundary.

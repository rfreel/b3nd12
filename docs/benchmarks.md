# Measurement contract

`system/metrics.json` is the metric registry. It defines 26 metrics, each with
a unit, direction, collection method, scope, and 30-day and 90-day targets.
The horizons begin with adoption of the control workflow. They are goals,
not deadlines enforced by a background job. No scheduled jobs are installed.

```sh
python3 control.py metrics
python3 control.py benchmark --output evidence/agent-system/local-baseline.json
```

Output paths are exclusive. Each run preserves source, workload, registry,
plan, state-head, and environment identities plus raw timing samples. Existing
results are never overwritten to make a trajectory look smoother.

## Ambitious targets

| Dimension | 30-day target | 90-day target | Required evidence |
| --- | --- | --- | --- |
| Incorrect admission | 0 | 0 | Frozen invalid-candidate corpus; numerator and denominator |
| Worker boundary escapes | 0 | 0 | Real isolation probes on the worker host |
| Independent reproduction | 95% | 99% | Clean compatible environment reruns |
| Held-out agent success | 85% | 95% | At least 30 tasks with three independent repeats |
| Correct first action | 90% | 98% | Blind choices against admissible-action sets |
| Context before useful action | 6000 median tokens | 3000 median tokens | Provider tokenizer counts |
| Tool calls per solved task | 20 | 10 | Complete call history, including retries |
| Human interventions | At most 3 per 30 tasks | At most 1 per 30 tasks | Material handoff log |
| Cost per replicated gain | At most $10 | At most $3 | Actual billed spend across all attempts |
| Cross-family lesson benefit | +5 percentage points | +15 percentage points | Paired held-out ablation |
| Negative lesson transfer | At most 5% | At most 1% | Explicit harmed-task count |
| Replicated gains | 10 per 100 attempts | 20 per 100 attempts | Independently repeated gains |
| Rollbacks for regression | At most 5% | At most 1% | Accepted-change cohorts |
| Task family coverage | 10 families | 20 families | Versioned task manifest and results |
| Budget overrun | 0 | 0 | Admitted limits versus total actual cost |

Local control targets additionally cover status-packet bytes, cold-start p95,
projection p95, 1000-event replay p95, tamper rejection, and dependency count.
These are immediately measurable and cheaper than an agent trial. They measure
control overhead, not task intelligence or research progress.

## Initial measurement protocol

The local suite uses seven repetitions, reports the nearest-rank p95, and keeps
all raw samples. With only seven samples, p95 is the maximum observed sample;
it is not a precise estimate of a population tail. Timing depends on the host
and competing workloads. No speedup is inferred from a single baseline.

The replay workload has 1000 alternating RUNNING/OPEN events, each bound to the
current plan. Ten tamper probes alter one event without updating its digest.
Projection reproducibility compares identical inputs twice. A 100% result on
these fixtures is scoped to those fixtures, not a universal security claim.

The local suite fills seven metrics. Every other metric remains UNMEASURED with
its collection requirement. Missing data never becomes zero, and zero gains
means cost per gain is undefined, not free. The proof pilot's 21-to-15 branch
reduction is a separate observed result; it is not agent-success or speed data.

## Comparison rules

1. Freeze workload, laws, scoring, and budget before a trial.
2. Compare only compatible suite and environment identities. If these change,
   establish a new baseline; preserve the old series.
3. Include failed, rejected, timed-out, and inconclusive attempts in costs.
4. Use the same task and seed pairing for before/after comparisons.
5. Reserve a final holdout set. Search-time feedback comes from development tasks.
6. Report absolute counts and uncertainty beside percentages. Use Wilson
   intervals for task-success proportions and paired resampling for differences.
7. Treat correctness and integrity as gates. Report time, memory, context,
   and cost as separate dimensions; do not trade a correctness failure for speed.
8. A claimed improvement needs an independent repeat and a predeclared minimum
   useful effect. Describe mixed results as trade-offs or inconclusive.

## Trajectory protocol

After B07 produces actual agent trials, retain cohorts by task family, model,
compiler, objective, and environment. Compare rolling 30-day and 90-day windows
only when their task mix is comparable. Track failure-class recurrence, time
to recovery, reuse of verified evidence, lesson transfer, and intervention
burden alongside gains. B19 implements this collector; no long-term series
exists yet.

A worsening integrity metric stops promotion. A rising cost with flat verified
gain reopens the search policy. A lesson that harms a new family is narrowed
or retired with its counterexample preserved. Plateau claims require a declared
search scope and budget; they do not establish universal exhaustion.

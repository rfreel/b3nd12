# Bend proof research

The assistant owns candidate design, execution, review, and reporting.

Objective: reduce explicit case alternatives in the eight repair-model proofs.
Keep ordinary readable formatting. Do not claim this metric measures execution
speed, general proof difficulty, or mathematical strength.

Only candidate proof bodies may vary. Keep the baseline, all eight signatures,
imports, laws, model, runner, compiler, and evaluation settings fixed during a
campaign. Never add unsafe annotations or weaken a law to admit a candidate.

Read AGENTS.md, guide/agent/ROUTER.md, and guide/agent/PROVE.md first.
Write a hypothesis before checking a candidate. Preserve failed candidates and
their diagnostics when they explain a consequential constraint.

Run `run.py` against the pinned, patched Bend checkout. Each candidate must pass
the original laws with zero unsafe terms. Missing and false proofs must fail
with their expected diagnostic IDs. Measure five alternating pairs against the
incumbent. Timing is descriptive; the acceptance metric is fewer case branches.

The runner accepts at most 20 candidate files, allows 20 seconds per compiler
call, and starts no new call after the 120-second campaign deadline. It uses
no paid model API. One call already running can extend beyond that deadline.

Review the winning proof manually before copying it into the pilot. Run the
full pilot verification after adoption. Record exactly which guarantee was
checked and whether any timing gain was demonstrated.

The runner replays supplied candidates. Candidate invention happens in the
assistant session; this repository does not launch an unattended model worker.
No scheduled work or automatic merge is installed.

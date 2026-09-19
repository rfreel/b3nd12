# AGENTS

This repository is a pinned Bend overlay with a local agent control interface.

Start with `./repo status`, then `./repo tasks next`.
Use `./repo setup` for dependencies and `./repo verify` for the full local gate.
Read START_HERE.md and the selected task's files. For Bend implementation or
proof work, route through guide/agent/ROUTER.md. Load the smallest legal working
set; do not dump the full Bend guide unless the router escalates to it.

Hard boundary: bend2/bend.ts is theory and checker source. Ergonomics changes do not edit it.

Use apply.sh to install the exact overlay on the clean pinned upstream checkout.
Files in patches/ are review records, not the executable installation path.

Task authority: system/roadmap.json plus state/events.jsonl. Use control.py to
record transitions. SOLVED requires fresh retained verification evidence.
Never edit a journal line or weaken a check to make the state look complete.
The roadmap is frozen once history exists; use a reviewed migration to change it.

Keep work-in-progress at one task. Do not start paid runs, remote workers, or
scheduled jobs merely because a future task mentions them. Check the task's
reopen condition, available capabilities, and budget before acting.

Write back reproduced failures, measured results, guards, and scoped lessons.
Keep unresolved alternatives and state the observation needed to reopen them.
Update ranked-deepenings.html for ranked overlay changes; use control.py todo
for the agent-system roadmap so the two histories do not compete.

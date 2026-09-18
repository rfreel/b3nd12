# PROGRAM pack

Purpose: implement, compile, run, test, and repair ordinary Bend programs with the smallest useful context.

Read by default
1. AGENTS.md
2. guide/agent/ROUTER.md
3. this file
4. the target .bend file
5. only its direct imports that are needed to answer the current question

Query instead of loading
- `bend base <name>` for one Base symbol and its subnames
- `bend base --types` only when the type surface is the question
- diagnostics by stable id when available

Do not load by default
- guide/GUIDE.md
- paper/
- bend2/bend.ts
- unrelated demos
- unrelated tests

Working loop
1. State the observable target.
2. Read the target file and its direct dependency seam.
3. Make the smallest source change that can satisfy the target.
4. Run the narrowest relevant check or test.
5. Preserve any residual failure as evidence. Do not broaden the read set until the current evidence requires it.
6. Escalate to the full guide only when a material language question remains unresolved.

Kernel boundary
Do not edit bend2/bend.ts for implementation ergonomics. Prefer source code, tests, CLI seams, compiler metadata, documentation, indexes, and sidecars.

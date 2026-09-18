# PROVE pack

Purpose: discharge Bend laws without loading the entire language manual.

Legal working set
1. AGENTS.md
2. guide/agent/ROUTER.md
3. this file
4. LAWS.bend
5. PROOF.bend
6. only definitions named by the target law or its current diagnostic
7. one proof-move note at a time when the proof-move library is present

Proof contract
- PROOF.bend beside LAWS.bend must import LAWS.bend.
- A proof result is not trusted if its import graph contains @unsafe.
- Preserve unresolved branches instead of replacing them with a plausible proof.
- Prefer conversion and the smallest proof move before introducing helpers.

Working loop
1. Select one law.
2. Inspect its type and the definitions it names.
3. Check PROOF.bend.
4. Classify the diagnostic.
5. Choose one proof move.
6. Recheck.
7. Expand the dependency graph only when the diagnostic changes or the move exposes a new required name.
8. Record unresolved residue rather than rereading the whole guide.

Escalate to guide/GUIDE.md only when the target depends on a semantic rule not covered by the pack or a proof-move note.

Kernel boundary
Do not change bend2/bend.ts to make a proof easier.

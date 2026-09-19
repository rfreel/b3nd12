# Proposed code file reorganization plan

## Decision

Keep the current file layout. No move, merge, or split is proposed for execution.
The requested improvement program does not establish a navigation or ownership
problem large enough to justify changing installed paths.

## Responsibility and dependency map

- `patches/`: ordered deltas consumed by apply.sh; ranks depend on prior ranks.
- `overlay/`: expected final bytes for four modified upstream files.
- `guide/agent/`, `CLAUDE.md`, `evals/`: additive delivery files at public paths.
- `spec/`: JSON contracts for management, diagnostics, and graph output.
- `stack.py`: pin, path-set and byte-equivalence checks.
- `b3nd12.py`: management command parsing and presentation.
- `apply.sh`, `verify.sh`: compatibility entry points.
- `tests/`: independent installation and executable behavior oracles.
- `docs/`: command contract, investigation, and verification evidence summaries.

There is no affected source area requiring a move. The proposed folder tree is
the current tree with the new management module, tests, schemas and docs placed
under these responsibilities. Existing imports and installed paths stay stable.

## Alternatives and risks

Merging patches with overlays would remove the independent byte oracle.
Splitting the four upstream overlays into feature folders would obscure their
installed paths and complicate the sequential patch model. Moving guides would
change CLI routing paths and patch contents. All three alternatives add migration
risk without demonstrated user benefit.

## Migration, compatibility and rollback

There is no migration sequence, import rewrite, or file deletion. Verify the
current structure through tests/patch_stack.py and the management CLI tests.
Each functional change remains revertible by its own commit. If a future move
is proposed, first enumerate every file, import, script, patch and document in
the affected area; provide exact old-to-new mappings and verify each move against
the unchanged installed-file oracle. Approval of this no-move plan does not
approve any later mapping. No unresolved move is presented as complete.

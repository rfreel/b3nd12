# Proposed code file reorganization plan

## Decision

Keep the current file layout. No move, merge, or split is proposed for execution.
Documentation navigation is being corrected through a single entry point and
explicit current and historical evidence labels. This does not require changing
installed paths or Python imports.

## Responsibility and dependency map

- `patches/`: ordered deltas consumed by apply.sh; ranks depend on prior ranks.
- `overlay/`: expected final bytes for four modified upstream files.
- `guide/agent/`, `CLAUDE.md`, `evals/`: additive delivery files at public paths.
- `spec/`: JSON contracts for management, diagnostics, and graph output.
- `stack.py`: pin, path-set and byte-equivalence checks.
- `b3nd12.py`: management command parsing and presentation.
- `bounded.py`: cooperative subprocess deadlines and captured-output limits.
- `delivery-manifest.json`: declared installed paths, source bytes and modes.
- `installation_receipt.py`: recorded installation identities and replay.
- `accretion/`: frozen routing law, trial controller, durable evidence,
  independent verification, rechecking and archive transfer.
- `benchmarks/`: management measurements with explicit source identities.
- `apply.sh`, `verify.sh`: compatibility entry points.
- `tests/`: independent installation and executable behavior oracles.
- `docs/`: command contract, investigation, and verification evidence summaries.

There is no affected source area requiring a move. The proposed folder tree is
the current tree. Existing imports and installed paths stay stable. No merge or
split is proposed, so no import migration, build rewrite or move-specific test
changes are required.

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

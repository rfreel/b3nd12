# Verification route

Start with ./repo doctor. Use ./repo setup to acquire the pinned runtime and
upstream overlay. Setup preserves unrecognized local edits and stops with their
paths rather than resetting them.

Use ./repo impact for changed-file routing. The focused scopes are schema,
decision, executor, proof, integration, and stress. ./repo verify is the final
aggregate gate. ./repo stress runs the declared finite adversarial campaign.

Read the result's log for the failing step. Do not rerun successful independent
steps to hide a failure. Missing tests and unexpected skips fail verification.
Run records live in .repo/runs; ./repo status checks their source and log bindings.

Read pilot/admission/law-catalog.json for proof scope, witnesses, and negative
fixtures. The model does not establish host enforcement or producer isolation.

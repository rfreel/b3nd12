# Upstream proof contract pin

Pinned upstream: bendlang/bend e5a4c4c, Bend 2.0.9.

Issue #776 was closed by the Bend maintainer after shipping the neighboring-file guard in 2.0.8. The current main.ts contains this invariant:

- if the checked file is named PROOF.bend,
- and LAWS.bend exists beside it,
- then PROOF.bend must import that exact LAWS.bend file,
- otherwise the CLI refuses the proof.

This patch stack treats that guard as upstream authority and does not duplicate it.

The issue also discussed @unsafe. Upstream did not make all @unsafe books fail. This layer therefore does not silently strengthen Bend's theory contract. BND102 remains a reserved diagnostic class for a future explicit policy decision.

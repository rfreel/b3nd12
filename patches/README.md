# Reference deltas

The numbered .patch files preserve the ranked design deltas for review and provenance.

They are not the installation mechanism. Some use context-only hunk markers and are intentionally human-readable rather than git-apply input.

apply.sh installs exact full-file overlays generated from the upstream commit pinned in upstream.json, then copies the additive agent files and runs verify.sh.

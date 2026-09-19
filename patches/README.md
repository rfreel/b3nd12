# Ordered patch stack

Apply the numbered .patch files in numeric order to the clean Bend 2.0.9 commit pinned in upstream.json. Each patch is a unified diff against the result of the preceding ranks.

The stack contains both upstream modifications and additive agent files. Its final contents match overlay/ and the existing guide, CLAUDE, and eval delivery files. Rank 10 records the unchanged theory boundary and is intentionally not a patch.

apply.sh checks the full sequence in a temporary index before applying it to the worktree, then runs verify.sh. No overlay copies are used during installation.

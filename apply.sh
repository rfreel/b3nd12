#!/bin/sh
set -eu

PIN=e5a4c4cfe980c2e4e70571562efb5197fe27b2f4
SELF=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET=${1:?usage: ./apply.sh /path/to/bend-checkout}

test "$(git -C "$TARGET" rev-parse HEAD)" = "$PIN" || {
  echo "apply: target must be pinned to $PIN" >&2
  exit 1
}
test -z "$(git -C "$TARGET" status --porcelain)" || {
  echo "apply: target worktree is not clean" >&2
  exit 1
}

mkdir -p "$TARGET/guide/agent/proof"
cp "$SELF/overlay/AGENTS.md" "$TARGET/AGENTS.md"
cp "$SELF/overlay/bend2/main.ts" "$TARGET/bend2/main.ts"
cp "$SELF/overlay/gates/repo.ts" "$TARGET/gates/repo.ts"
cp "$SELF/overlay/gates/ping.ts" "$TARGET/gates/ping.ts"
cp "$SELF/CLAUDE.md" "$TARGET/CLAUDE.md"
cp "$SELF"/guide/agent/*.md "$TARGET/guide/agent/"
cp "$SELF"/guide/agent/*.json "$TARGET/guide/agent/"
cp "$SELF"/guide/agent/proof/*.md "$TARGET/guide/agent/proof/"
cp "$SELF/evals/README.md" "$TARGET/evals/README.md"
cp "$SELF/evals/_template.sidecar.json" "$TARGET/evals/_template.sidecar.json"
cp "$SELF/evals/_sidecar.schema.json" "$TARGET/evals/_sidecar.schema.json"

"$SELF/verify.sh" "$TARGET"
echo "apply: ranked deepenings installed"

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

p() { git -C "$TARGET" apply "$SELF/patches/$1"; }

p 01-router.patch
mkdir -p "$TARGET/guide/agent"
cp "$SELF/CLAUDE.md" "$TARGET/CLAUDE.md"
cp "$SELF/guide/agent/ROUTER.md" "$TARGET/guide/agent/ROUTER.md"
cp "$SELF/guide/agent/PROGRAM.md" "$TARGET/guide/agent/PROGRAM.md"
cp "$SELF/guide/agent/PROVE.md" "$TARGET/guide/agent/PROVE.md"

p 02-packs.patch
p 03-diagnostics-json.patch
p 04-proof-moves.patch
mkdir -p "$TARGET/guide/agent/proof"
cp "$SELF"/guide/agent/proof/*.md "$TARGET/guide/agent/proof/"

p 05-graph.patch
p 06-indexes.patch
cp "$SELF/guide/agent/laws-index.json" "$TARGET/guide/agent/laws-index.json"
cp "$SELF/guide/agent/diagnostics.json" "$TARGET/guide/agent/diagnostics.json"
p 07-proof-import-pin.patch

p 08-eval-sidecars.patch
cp "$SELF/evals/_sidecar.schema.json" "$TARGET/evals/_sidecar.schema.json"

p 09-why-pack.patch

"$SELF/verify.sh" "$TARGET"
echo "apply: ranked deepenings installed"

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

# Validate the whole ordered stack in a temporary index before changing files.
CHECK=$(mktemp -d)
trap 'rm -rf "$CHECK"' EXIT
trap 'exit 1' HUP INT TERM
GIT_INDEX_FILE="$CHECK/index" git -C "$TARGET" read-tree HEAD
for patch in "$SELF"/patches/[0-9][0-9]-*.patch; do
  GIT_INDEX_FILE="$CHECK/index" git -C "$TARGET" apply --cached --whitespace=error "$patch"
done

for patch in "$SELF"/patches/[0-9][0-9]-*.patch; do
  echo "apply: $(basename "$patch")"
  git -C "$TARGET" apply --whitespace=error "$patch"
done

"$SELF/verify.sh" "$TARGET"
echo "apply: ranked deepenings installed"

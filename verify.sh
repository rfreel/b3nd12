#!/bin/sh
set -eu
TARGET=${1:?usage: ./verify.sh /path/to/bend-checkout}

SELF=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$SELF/stack.py" "$TARGET"
echo "verify: exact delivery PASS; bend2/bend.ts unchanged"

if command -v bun >/dev/null 2>&1; then
  smoke() {
    if ! BEND_NO_TELEMETRY=1 python3 "$SELF/bounded.py" --timeout 15 -- bun "$TARGET/bend2/main.ts" "$@" >/dev/null; then
      echo "verify: runtime smoke FAILED (including unavailable or timed-out execution)" >&2
      exit 1
    fi
  }
  smoke --help
  smoke guide
  smoke --why BND101
  echo "verify: runtime smoke PASS"
else
  echo "verify: runtime smoke UNAVAILABLE (bun not on PATH)"
fi

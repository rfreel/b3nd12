#!/bin/sh
set -eu
TARGET=${1:?usage: ./verify.sh /path/to/bend-checkout}

SELF=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$SELF/stack.py" "$TARGET"

if command -v bun >/dev/null 2>&1; then
  BEND_NO_TELEMETRY=1 bun "$TARGET/bend2/main.ts" --help >/dev/null
  BEND_NO_TELEMETRY=1 bun "$TARGET/bend2/main.ts" guide >/dev/null
  BEND_NO_TELEMETRY=1 bun "$TARGET/bend2/main.ts" --why BND101 >/dev/null
fi

echo "verify: exact delivery PASS; bend2/bend.ts unchanged"

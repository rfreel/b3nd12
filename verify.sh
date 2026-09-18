#!/bin/sh
set -eu
TARGET=${1:?usage: ./verify.sh /path/to/bend-checkout}

need() { test -e "$TARGET/$1" || { echo "verify: missing $1" >&2; exit 1; }; }
need CLAUDE.md
need guide/agent/ROUTER.md
need guide/agent/PROGRAM.md
need guide/agent/PROVE.md
need guide/agent/laws-index.json
need guide/agent/diagnostics.json
need evals/_sidecar.schema.json

for f in 01-CONVERSION 02-CASE 03-INDUCTION 04-REWRITE 05-CONGRUENCE 06-EQUALITY-CHAIN 07-WITNESS 08-CONTRADICTION; do
  need "guide/agent/proof/$f.md"
done

grep -q 'bend guide \[program|prove\]' "$TARGET/bend2/main.ts"
grep -q -- '--json' "$TARGET/bend2/main.ts"
grep -q -- '--graph' "$TARGET/bend2/main.ts"
grep -q -- '--why' "$TARGET/bend2/main.ts"
grep -q -- '--pack' "$TARGET/bend2/main.ts"
grep -q 'PROOF.bend must import ./LAWS.bend' "$TARGET/bend2/main.ts"

git -C "$TARGET" diff --check
git -C "$TARGET" diff --quiet -- bend2/bend.ts || {
  echo "verify: forbidden bend2/bend.ts change" >&2
  exit 1
}

if command -v bun >/dev/null 2>&1; then
  BEND_NO_TELEMETRY=1 bun "$TARGET/bend2/main.ts" --help >/dev/null
  BEND_NO_TELEMETRY=1 bun "$TARGET/bend2/main.ts" guide >/dev/null
  BEND_NO_TELEMETRY=1 bun "$TARGET/bend2/main.ts" --why BND101 >/dev/null
fi

echo "verify: structure PASS; bend2/bend.ts unchanged"

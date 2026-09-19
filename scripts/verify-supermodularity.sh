#!/bin/sh
set -eu

SELF=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGET=${1:?usage: ./scripts/verify-supermodularity.sh /path/to/patched-bend-checkout}
TARGET=$(CDPATH= cd -- "$TARGET" && pwd)
cd "$SELF"

PIN=$(python3 -c 'import json; print(json.load(open("upstream.json"))["commit"])')
test "$(git -C "$TARGET" rev-parse HEAD)" = "$PIN" || {
  echo "supermodularity: upstream commit does not match upstream.json" >&2
  exit 1
}
git -C "$TARGET" diff --exit-code HEAD -- bend2/bend.ts
command -v bun >/dev/null
export BEND_NO_TELEMETRY=1
export PYTHONDONTWRITEBYTECODE=1
BEND_TARGET=$TARGET
export BEND_TARGET
"$SELF/verify.sh" "$TARGET"

TEMP=$(mktemp -d)
trap 'rm -rf "$TEMP"' EXIT HUP INT TERM
RESULTS=${SUPERMODULARITY_RESULTS_DIR:-$TEMP/results}
mkdir -p "$RESULTS"

echo "supermodularity: checking Bend proofs"
if ! bun "$TARGET/bend2/main.ts" "$SELF/pilot/supermodularity/PROOF.bend" --json >"$TEMP/proof.jsonl" 2>&1; then
  cat "$TEMP/proof.jsonl" >&2
  exit 1
fi
cat "$TEMP/proof.jsonl"
cat >"$TEMP/check-safe.py" <<'PY'
import json
import sys

with open(sys.argv[1]) as source:
    events = [json.loads(line) for line in source if line.strip()]
if not any(event.get("id") == "BND000" and event.get("unsafe") == 0
           for event in events):
    raise SystemExit("proof check did not confirm zero unsafe terms")
if any(event.get("severity") == "error" for event in events):
    raise SystemExit("proof check emitted an error")
PY
python3 "$TEMP/check-safe.py" "$TEMP/proof.jsonl"

echo "supermodularity: rejecting transitive unsafe imports"
bun "$TARGET/bend2/main.ts" \
  "$SELF/pilot/supermodularity/unsafe_fixture/PROOF.bend" --json \
  >"$TEMP/unsafe.jsonl" 2>&1
cat "$TEMP/unsafe.jsonl"
python3 - "$TEMP/unsafe.jsonl" <<'PY'
import json
import sys

with open(sys.argv[1]) as source:
    events = [json.loads(line) for line in source if line.strip()]
if not any(event.get("id") == "BND000" and event.get("unsafe") == 1
           for event in events):
    raise SystemExit("transitive unsafe fixture did not expose exactly one unsafe term")
PY
if python3 "$TEMP/check-safe.py" "$TEMP/unsafe.jsonl"; then
  echo "supermodularity: unsafe import incorrectly passed the proof gate" >&2
  exit 1
fi

echo "supermodularity: rejecting false acceptance claims"
for fixture in broken_accepted deletion_accepted; do
  if bun "$TARGET/bend2/main.ts" \
    "$SELF/pilot/supermodularity/negative/$fixture.bend" --json \
    >"$TEMP/$fixture.jsonl" 2>&1; then
    echo "supermodularity: false proof unexpectedly accepted: $fixture" >&2
    exit 1
  fi
  cat "$TEMP/$fixture.jsonl"
  python3 - "$TEMP/$fixture.jsonl" <<'PY'
import json
import sys

with open(sys.argv[1]) as source:
    events = [json.loads(line) for line in source if line.strip()]
if not any(event.get("id") == "BND110"
           and event.get("severity") == "error"
           and "Accepted" in event.get("message", "")
           and "Rejected" in event.get("message", "")
           for event in events):
    raise SystemExit("negative fixture failed without the intended equality mismatch")
PY
done

echo "supermodularity: checking actual repair admission"
python3 experiments/checker_repair.py \
  --target "$TARGET" --output "$RESULTS/checker_repair.json"

echo "supermodularity: checking Python regression cases"
python3 -m unittest discover -s tests -p 'test_*.py' -v

echo "supermodularity: measuring the four configurations"
python3 experiments/diagnostic_interaction.py \
  --runtime "$(command -v bun)" \
  --main "$TARGET/bend2/main.ts" \
  --output "$RESULTS/interaction.json"

git -C "$TARGET" diff --exit-code HEAD -- bend2/bend.ts
echo "supermodularity: verification passed"

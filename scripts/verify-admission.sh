#!/bin/sh
set -eu
SELF=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGET=${1:?usage: verify-admission.sh /path/to/patched-bend}
TARGET=$(CDPATH= cd -- "$TARGET" && pwd)
cd "$SELF"
export BEND_NO_TELEMETRY=1 PYTHONDONTWRITEBYTECODE=1
"$SELF/verify.sh" "$TARGET"
TEMP=$(mktemp -d)
trap 'rm -rf "$TEMP"' EXIT HUP INT TERM
bun "$TARGET/bend2/main.ts" pilot/admission/PROOF.bend --json >"$TEMP/proof.jsonl" 2>&1
cat "$TEMP/proof.jsonl"
python3 - "$TEMP/proof.jsonl" <<'PY'
import json, sys
events = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
assert sum(e.get('id') == 'BND000' and e.get('unsafe') == 0 for e in events) == 1
assert not any(e.get('severity') == 'error' for e in events)
PY
for fixture in pilot/admission/negative/*.bend; do
  if bun "$TARGET/bend2/main.ts" "$fixture" --json >"$TEMP/negative.jsonl" 2>&1; then
    echo "false proof accepted: $fixture" >&2
    exit 1
  fi
  python3 - "$TEMP/negative.jsonl" <<'PY'
import json, sys
events = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
assert any(e.get('id') == 'BND110' and e.get('severity') == 'error'
           and 'Accepted' in e.get('message', '') for e in events)
PY
done
python3 experiments/admission_stress.py --output "${ADMISSION_RESULTS:-$TEMP/admission.json}"

#!/usr/bin/env python3
"""Regenerate real certificates after original workspaces disappear; refuse tampering."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'accretion'))
from program import replay, sha
from recheck import recheck


def main():
    bend, bun = (Path(arg).resolve() for arg in sys.argv[1:3])
    contract = sha((ROOT / 'accretion/TODO.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='recheck-test-') as temporary:
        packet = Path(temporary) / 'packet'
        replay(packet, contract, bun, bend)
        rows = [json.loads(line) for line in (packet / 'ledger.jsonl').read_text().splitlines()]
        terminal = rows[-1]['sha256']
        first = packet / 'pass-001/receipt.json'
        receipt = json.loads(first.read_bytes())
        for sample in receipt['samples']:
            assert not Path(sample['checker']['command'][-1]).exists(), 'original temporary proof still exists'
        result = recheck(packet, terminal, contract, bun, bend)
        assert len(result['certificates']) == 9
        assert all(row['stdout'] == 'All terms check.\n' for row in result['certificates'])
        # Each invalid packet must fail before a compiler is validated or invoked.
        def refused(expected_terminal, expected_contract):
            with patch('recheck.validate_compiler', side_effect=AssertionError('compiler reached before validation')):
                try:
                    recheck(packet, expected_terminal, expected_contract, bun, bend)
                except (ValueError, OSError, KeyError, TypeError):
                    pass
                else:
                    raise AssertionError('invalid packet accepted')
        refused('0' * 64, contract)
        refused(terminal, '0' * 64)
        original = first.read_bytes()
        receipt['samples'][0]['metrics']['after'] = 0
        first.write_text(json.dumps(receipt))
        refused(terminal, contract)
        first.write_bytes(original)
        # Executable-looking snapshots stay inert; even a comment edit breaks the seal.
        snapshot = packet / 'inputs/accretion/run.py'
        original_snapshot = snapshot.read_bytes()
        snapshot.write_bytes(b"raise RuntimeError('must never execute snapshot')\n" + original_snapshot)
        refused(terminal, contract)
        snapshot.write_bytes(original_snapshot)
        process = subprocess.run([sys.executable, str(ROOT / 'accretion/recheck.py'), str(packet),
                                  '--terminal-sha256', terminal, '--contract-sha256', contract,
                                  '--bun', str(bun), '--bend-root', str(bend)], capture_output=True, text=True, timeout=30)
        assert process.returncode == 0, process.stdout + process.stderr
        assert len(json.loads(process.stdout)['certificates']) == 9
    print('PASS 9 reconstructed real books after workspace deletion; terminal/contract/receipt/snapshot tampering refused before execution; CLI repeats 9 certificates')


if __name__ == '__main__':
    main()

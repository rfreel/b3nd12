#!/usr/bin/env python3
"""Reproduce the finite proofs and check their complete declared-law inventory."""
import argparse
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LAWS = ('accepted_behavior', 'accepted_preservation', 'accepted_integrity',
        'invalid_context_rejected', 'eligible_accepted', 'missing_evidence_waits',
        'rejected_preserves_state', 'pending_preserves_state', 'accepted_updates_state')


def render():
    lines = ['import Base', 'import ./model.bend as Model', 'import ./LAWS.bend as Laws', '']
    for law in LAWS[:3]:
        lines.extend([f'def Laws.{law}(request):', '  match request:'])
        for context in ('False', 'True'):
            for statuses in itertools.product(('Pass', 'Fail', 'Pending'), repeat=3):
                fields = ', '.join([context + '{}', *('Model.' + s + '{}' for s in statuses)])
                lines.extend([f'    case Model.Request{{{fields}}}:', '      {==}'])
        lines.append('')
    args = ('b, p, i', '', '', 'before, after', 'before, after', 'before, after')
    for law, params in zip(LAWS[3:], args):
        lines.extend([f'def Laws.{law}({params}):', '  {==}', ''])
    return '\n'.join(lines)


def check_inventory(root=ROOT):
    declared = re.findall(r'^law ([a-z_]+):', (root / 'pilot/admission/LAWS.bend').read_text(), re.M)
    proved = re.findall(r'^def Laws\.([a-z_]+)\(', (root / 'pilot/admission/PROOF.bend').read_text(), re.M)
    catalog = json.loads((root / 'pilot/admission/law-catalog.json').read_text())
    if declared != list(LAWS) or proved != list(LAWS) or [x['law'] for x in catalog['laws']] != list(LAWS):
        raise ValueError('Declared, proved, and cataloged law inventories must match the nine required laws exactly')
    return len(LAWS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'pilot/admission/PROOF.bend'
    generated = render()
    if args.check:
        if path.read_text() != generated:
            parser.exit(1, 'Proof drift: run scripts/generate-admission-proof.py\n')
    else:
        path.write_text(generated)
    print(json.dumps({'laws': check_inventory(), 'generated_proof_matches': True,
                      'note': 'Inventory check only; run the Bend checker to establish proofs.'}))


if __name__ == '__main__':
    main()

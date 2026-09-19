# b3nd12

Agent ergonomics overlay for Bend, pinned to bendlang/bend commit e5a4c4cfe980c2e4e70571562efb5197fe27b2f4, version 2.0.9.

## Apply

```sh
./apply.sh /path/to/clean/bend-checkout
```

The target must be clean and exactly at the pinned commit. apply.sh validates the complete stack in a temporary index, applies patches in numeric order, then runs verify.sh. Verification refuses any bend2/bend.ts change.

ranked-deepenings.html is the implementation ledger. guide/agent is the compact agent surface. patches contains executable ranked deltas. overlay retains the expected contents of the four modified upstream files.

Run the installation regression test against a local Bend repository containing the pinned commit:

```sh
python3 tests/patch_stack.py /path/to/bend-checkout
```

The test uses temporary checkouts, checks direct patch application and apply.sh, compares every installed file with the existing delivery files, and rejects changes outside that file set. Bun smoke checks run through verify.sh when Bun is available.

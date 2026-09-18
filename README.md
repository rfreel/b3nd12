# b3nd12

Agent ergonomics overlay for Bend, pinned to bendlang/bend commit e5a4c4cfe980c2e4e70571562efb5197fe27b2f4, version 2.0.9.

## Apply

```sh
./apply.sh /path/to/clean/bend-checkout
```

The target must be exactly at the pinned commit. apply.sh installs exact full-file overlays plus additive agent files, then runs verify.sh. Verification refuses any bend2/bend.ts change.

ranked-deepenings.html is the implementation ledger. guide/agent is the compact agent surface. patches contains review-only ranked deltas.

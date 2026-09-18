# b3nd12

Agent ergonomics patch stack for Bend, pinned to bendlang/bend commit e5a4c4cfe980c2e4e70571562efb5197fe27b2f4, version 2.0.9.

## Apply

```sh
./apply.sh /path/to/clean/bend-checkout
```

The target must be exactly at the pinned commit. Patches apply in ranked order and the verification step refuses any bend2/bend.ts change.

The ranked-deepenings.html file is the implementation ledger. The guide/agent directory is the compact agent surface. The patches directory contains the CLI and gate changes.

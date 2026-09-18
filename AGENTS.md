# AGENTS

This repository is an ordered patch stack over the Bend upstream pinned in upstream.json.

Start at guide/agent/ROUTER.md. Load the smallest legal working set. Do not dump the full Bend guide into agent context unless the router explicitly escalates to it.

Hard boundary: bend2/bend.ts is theory and checker source. Ergonomics changes do not edit it.

Apply patches in patches/ numeric order. Update ranked-deepenings.html when each ranked change closes.

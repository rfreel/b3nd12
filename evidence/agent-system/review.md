# Independent review

The reviewer inspected the control implementation and ran focused probes in
temporary directories. The first 38 tests passed, but two public-boundary
defects remained.

1. Supplying a JSON array as an evidence document or metric registry caused an
   uncaught attribute error. Parsing JSON had been mistaken for validating its
   shape. The implementation now validates object shapes and returns stable
   INVALID_EVIDENCE or INVALID_METRICS errors. Regression checks are
   `test_json_array_is_not_an_evidence_object` and
   `test_valid_json_with_wrong_shape_is_rejected`.
2. A benchmark selecting an alternate journal still launched cold-start status
   against the default journal. This could mislabel measurements or fail on an
   unrelated corrupt journal. The benchmark now forwards the selected root and
   state path, records that path, and checks the child's reported head.
   `test_cold_benchmark_uses_selected_journal` runs this scenario in a real
   temporary checkout with a deliberately corrupt default journal.

The expanded suite passed 41 tests after these repairs. The retained per-task
verification artifacts provide fresh results for the final source state.

The reviewer then reran 21 focused CLI, benchmark, and evidence tests and
confirmed both fixes. A sustained output probe was stopped after 0.064 seconds
and retained as failed, truncated evidence. A fresh-copy status invocation
created no bytecode directories. No consequential blocker remained in that
review scope.

The review also confirmed the documented boundaries: local hashes are not
independent attestation, file locks do not coordinate clones, and local timing
does not establish agent productivity. Those remain explicit roadmap gates.

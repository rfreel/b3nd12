# Evidence replacement observation

During the first real foundation-adoption sequence, A02 was verified and recorded
SOLVED. Its evidence file `runs/foundation-A02-v1.json` was subsequently observed
to contain zero bytes. The prior accepted digest remains in the journal. A03
became STALE through its dependency and A04 completion was rejected. No false
completion was admitted after the missing evidence was observed.

The independent reviewer inspected the relevant writes and file metadata. The
current file's birth time was later than its retained modification time, which
is consistent with replacement or copy preserving timestamps. That observation
does not identify the writer. Neither a code-level overwrite nor an external
cause has been established. The zero-byte file is retained rather than repaired
in place.

Status of attribution: UNRESOLVED. Reopen when filesystem write provenance is
available or another occurrence supplies a discriminating observation. Do not
infer a compiler failure or a hostile actor from this incident.

A separate, reproducible weakness was found: verification opened the final
evidence path before its command completed. The new regression test runs a
command that requires its result path to remain absent while it executes. That
test failed before the repair. Verification now writes an exclusive pending
file, flushes and fsyncs it, atomically links the complete result to the final
path without overwriting, removes the pending name, and fsyncs the directory.
Interrupted pending files remain separate and cannot supply completion evidence.

This repair eliminates publication of an incomplete result by this verifier.
It does not establish the cause of the observed replacement or prevent an
external writer from replacing a completed file. Freshness checks remain the
guard against later artifact changes. The affected tasks are reverified using
new run IDs and explicit reopen transitions.

A subsequent read also showed an intact 18-event journal prefix after a command
had reported event 19. Retrying the same request through the public interface
reconstructed the identical event-19 digest, which was checked against the
earlier command output. The missing suffix's cause remains unattributed. An
intact hash-chain prefix cannot reveal a lost tail without an external head
checkpoint; this is an explicit limit of the current journal. Retain caller
head checkpoints and Git history when investigating such discrepancies.

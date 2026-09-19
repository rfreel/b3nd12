# Release route

Read ./repo status and docs/repo-operations.md. Publication requires a fresh full
verification record. ./repo publish --dry-run prepares the exact content tree,
PR body, and connector handoff without staging the user's index.

The CLI path uses gh for an already-pushed --head branch. If gh is unavailable,
use the connected GitHub tools and the prepared packet. Do not print credentials.
After publishing, run ./repo verify-remote COMMIT_SHA to compare exact trees.

./repo host OWNER/NAME inspects host rules through gh. ./repo watch PR uses a
bounded budget and reports queued checks separately from completed ones. Neither
command installs protection or grants merge authority. Missing access remains
explicit. Record implementation, local evidence, remote CI, merge, and deployment
as separate states. Policy changes require review under the existing authority.

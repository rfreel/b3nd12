# Next improvements supported by pilot findings

These candidates are open. They are not required to complete the current pilot
and are not authorization to change hosting policy or expand the compiler.

| Candidate | Evidence that motivates it | Measurable acceptance test | Reopen condition |
| --- | --- | --- | --- |
| Bind reports to retained execution artifacts | The report validator checks supplied digests but does not authenticate them. | Alter an artifact or remove it; admission rejects. An intact artifact set still passes. | External reports begin driving real repair acceptance. |
| Evaluate a less saturated diagnostic task | Every configuration supplied the import hint on the first case; interaction was zero. | Predeclare cases and scoring, then record all four configurations, including failures and costs. | A concrete diagnostic lacks enough information for the baseline resolver. |
| Extend the proof model to variable regression suites | Current proofs cover two Boolean cases and a finite program family. | Prove preservation over a list of cases and retain an accepted witness plus a rejected deletion. | A real integration needs a variable suite that cannot be covered by the existing checks. |
| Establish host-enforced merge requirements | A workflow does not establish branch protection or independent rule review. | Verify that a failed required check prevents merge and that law changes require the intended reviewer. | Repository owner selects the required checks and reviewer policy. |

No candidate is a measured improvement yet. Select one only when its reopen
condition holds; preserve the original evaluation when comparing results.

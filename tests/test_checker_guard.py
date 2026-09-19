"""Exercise the actual overlay verifier against staged and unstaged edits."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("BEND_TARGET"), "requires pinned BEND_TARGET checkout")
class CheckerGuardTests(unittest.TestCase):
    def test_checker_edits_cannot_hide_in_index(self):
        with tempfile.TemporaryDirectory(prefix="b3nd12-guard-") as directory:
            target = Path(directory) / "upstream"
            subprocess.run(
                ["git", "clone", "--quiet", "--shared", os.environ["BEND_TARGET"], str(target)],
                check=True, capture_output=True, text=True,
            )
            installed = subprocess.run(
                [str(ROOT / "apply.sh"), str(target)], capture_output=True, text=True,
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            checker = target / "bend2/bend.ts"
            with checker.open("a") as output:
                output.write("\n// Negative fixture: checker edit must be rejected.\n")
            for staged in (False, True):
                if staged:
                    subprocess.run(["git", "-C", str(target), "add", "bend2/bend.ts"], check=True)
                result = subprocess.run(
                    [str(ROOT / "verify.sh"), str(target)], capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0, f"staged={staged}")
                self.assertIn("forbidden bend2/bend.ts change", result.stderr)


if __name__ == "__main__":
    unittest.main()

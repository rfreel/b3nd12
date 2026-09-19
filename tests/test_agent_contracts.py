import copy
from pathlib import Path
import tempfile
import unittest

from tools.agent_system.contracts import Problem, safe_path, validate_plan


def task(identity="A", dependencies=None):
    return dict(id=identity, title="Example", depends=dependencies or [], priority=1,
                effort_minutes=5, files=["source.txt"], checks=[["python3", "-c", "print('ok')"]],
                timeout_seconds=2, acceptance="A real check passes", reopen="Source changes",
                phase="foundation")


def plan(*tasks):
    return {"schema_version": 1, "tasks": list(tasks) or [task()]}


class ContractTests(unittest.TestCase):
    def test_graph_accepts_valid_chain(self):
        validate_plan(plan(task(), task("B", ["A"])))

    def test_duplicate_missing_and_cyclic_dependencies_fail(self):
        for value in (plan(task(), task()), plan(task("A", ["B"])),
                      plan(task("A", ["B"]), task("B", ["A"]))):
            with self.subTest(value=value), self.assertRaises(Problem):
                validate_plan(value)

    def test_invalid_budget_and_unknown_fields_fail(self):
        for field, value in (("timeout_seconds", 0), ("timeout_seconds", True),
                             ("timeout_seconds", float("nan")), ("extra", "ignored")):
            item = copy.deepcopy(task())
            item[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(Problem):
                validate_plan(plan(item))

    def test_escape_and_symlink_escape_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "escape").symlink_to(root.parent)
            for path in ("../secret", "/etc/passwd", "escape/secret"):
                with self.subTest(path=path), self.assertRaises(Problem):
                    safe_path(root, path)

    def test_schema_and_empty_checks_fail(self):
        bad = task()
        bad["checks"] = []
        for value in ({"schema_version": 99, "tasks": [task()]}, plan(bad)):
            with self.assertRaises(Problem):
                validate_plan(value)


if __name__ == "__main__":
    unittest.main()

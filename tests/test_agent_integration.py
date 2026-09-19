from pathlib import Path
import unittest

from tools.agent_system.contracts import digest, load_plan, parse, safe_path

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def test_foundation_context_is_present(self):
        for task in load_plan(ROOT)["tasks"]:
            if task["phase"] == "foundation":
                for file in task["files"]:
                    self.assertTrue(safe_path(ROOT, file).is_file(), (task["id"], file))

    def test_lesson_provenance_is_intact(self):
        lessons = parse((ROOT / "system/lessons.json").read_text())["lessons"]
        self.assertTrue(lessons)
        for lesson in lessons:
            self.assertTrue(lesson["scope"] and lesson["reopen"] and lesson["guard"])
            path = safe_path(ROOT, lesson["evidence"]["path"])
            self.assertEqual(digest(path.read_bytes()), lesson["evidence"]["sha256"])

    def test_instruction_and_ci_routes_exist(self):
        self.assertIn("./repo status", (ROOT / "AGENTS.md").read_text())
        self.assertIn("./repo tasks next", (ROOT / "START_HERE.md").read_text())
        self.assertIn("read_control(root", (ROOT / "tools/repo_cli.py").read_text())
        workflow = (ROOT / ".github/workflows/agent-system.yml").read_text()
        self.assertIn("test_agent_*.py", workflow)
        self.assertIn("control.py check", workflow)


if __name__ == "__main__":
    unittest.main()

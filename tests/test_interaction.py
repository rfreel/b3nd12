import copy
import unittest
from tools.interaction import ARMS, FEATURES, evaluate, read_json


def records(scores=(0, 1, 1, 3)):
    return [dict(arm=arm, features=FEATURES[arm], score=score,
                 evaluation="fixture-v1", cases=["case-1"],
                 budget={"operations": 10},
                 metric={"name": "correct", "unit": "cases", "direction": "higher_is_better"},
                 system={"revision": "revision-1", "runtime": "test-runtime",
                         "files_sha256": {"fixture": "0" * 64}},
                 status="observed", evidence={"output": score})
            for arm, score in zip(ARMS, scores)]


class InteractionTests(unittest.TestCase):
    def test_signs(self):
        for scores, sign in [((0, 1, 1, 3), "positive"),
                             ((0, 1, 1, 2), "additive"),
                             ((0, 1, 1, 1), "negative")]:
            self.assertEqual(evaluate(records(scores))["classification"], sign)

    def test_exact_fraction(self):
        self.assertEqual(evaluate(records(("1/3", "2/3", "2/3", "4/3")))["interaction"], "1/3")

    def test_nonzero_baseline_and_large_integer(self):
        n = 10**100
        self.assertEqual(evaluate(records((n, n+1, n+2, n+4)))["interaction"], "1")

    def test_context_drift(self):
        for field, value in [("evaluation", "other"), ("cases", ["other"]),
                             ("budget", {"operations": 11}),
                             ("metric", {"name": "other", "unit": "cases", "direction": "higher_is_better"}),
                             ("system", {"revision": "revision-2", "runtime": "test-runtime",
                                         "files_sha256": {"fixture": "0" * 64}})]:
            changed = records()
            changed[3][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                evaluate(changed)

    def test_incomplete_or_unsupported_observations(self):
        for value in [1.0, True, "nan", "1/0", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                evaluate(records((0, 1, 1, value)))
        for field, value in [("status", "unresolved"), ("evidence", None),
                             ("features", ["b"]), ("arm", "baseline"), ("cases", [])]:
            changed = copy.deepcopy(records())
            changed[3][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                evaluate(changed)
        with self.assertRaises(ValueError):
            evaluate(records()[:3])

    def test_malformed_context(self):
        invalid = [("evaluation", {}), ("evaluation", " "), ("cases", ["x", "x"]),
                   ("cases", [{}]), ("budget", {}), ("budget", {"calls": True}),
                   ("budget", {"calls": -1}), ("budget", {"calls": float("nan")}),
                   ("metric", {}), ("system", {}),
                   ("system", {"revision": "x", "runtime": "bun", "files_sha256": {"f": "bad"}})]
        for field, value in invalid:
            changed = copy.deepcopy(records())
            for record in changed:
                record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                evaluate(changed)

    def test_strict_json(self):
        for text in ['{"a":1,"a":2}', '{"nested":{"x":0,"x":1}}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_json(text)
        self.assertEqual(read_json('{"a":1}'), {"a": 1})


if __name__ == "__main__":
    unittest.main()

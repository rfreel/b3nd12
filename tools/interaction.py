"""Evaluate an observed four-arm interaction, using exact arithmetic.

This checks record comparability, not the truth of the recorded observations.
Scores are integers or rational strings; floating-point values are rejected.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path


ARMS = ("baseline", "a", "b", "ab")
CONTEXT = ("evaluation", "cases", "budget", "metric", "system")
FEATURES = {"baseline": [], "a": ["a"], "b": ["b"], "ab": ["a", "b"]}


def read_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite JSON value: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_context(record):
    if not nonempty(record.get("evaluation")):
        raise ValueError("evaluation must be a nonempty string")
    cases = record.get("cases")
    if (not isinstance(cases, list) or not cases
            or not all(nonempty(case) for case in cases)
            or len(set(cases)) != len(cases)):
        raise ValueError("cases must be nonempty unique strings")
    budget = record.get("budget")
    if (not isinstance(budget, dict) or not budget
            or not all(nonempty(key) and type(value) is int and value > 0
                       for key, value in budget.items())):
        raise ValueError("budget must name positive integer limits")
    metric = record.get("metric")
    if (not isinstance(metric, dict) or set(metric) != {"name", "unit", "direction"}
            or not nonempty(metric["name"]) or not nonempty(metric["unit"])
            or metric["direction"] != "higher_is_better"):
        raise ValueError("metric needs name, unit, and higher_is_better direction")
    system = record.get("system")
    if (not isinstance(system, dict)
            or set(system) != {"revision", "runtime", "files_sha256"}
            or not nonempty(system["revision"]) or not nonempty(system["runtime"])):
        raise ValueError("system needs revision, runtime, and files_sha256")
    hashes = system["files_sha256"]
    if (not isinstance(hashes, dict) or not hashes
            or not all(nonempty(key) and isinstance(value, str) and len(value) == 64
                       and all(char in "0123456789abcdef" for char in value)
                       for key, value in hashes.items())):
        raise ValueError("files_sha256 must map file names to SHA-256 hex digests")


def exact(value):
    if type(value) is int:
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError("score must be a finite exact rational") from error
    raise ValueError("score must be an integer or rational string")


def evaluate(records):
    try:
        json.dumps(records, allow_nan=False)
    except (ValueError, TypeError) as error:
        raise ValueError("records must contain finite JSON values") from error
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("exactly four records are required")
    by_arm = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each record must be an object")
        arm = record.get("arm")
        if not isinstance(arm, str) or arm not in ARMS or arm in by_arm:
            raise ValueError("arms must be baseline, a, b, ab exactly once")
        validate_context(record)
        if record.get("features") != FEATURES[arm]:
            raise ValueError("features do not match arm " + arm)
        if record.get("status") != "observed":
            raise ValueError("all four arms need observed results")
        if not record.get("evidence"):
            raise ValueError("each arm needs evidence")
        if "score" not in record:
            raise ValueError("each arm needs a score")
        exact(record["score"])
        by_arm[arm] = record
    baseline = by_arm["baseline"]
    for record in by_arm.values():
        for key in CONTEXT:
            # JSON canonicalization also distinguishes true from 1.
            if json.dumps(record[key], sort_keys=True) != json.dumps(baseline[key], sort_keys=True):
                raise ValueError("comparison context differs: " + key)
    scores = {arm: exact(by_arm[arm]["score"]) for arm in ARMS}
    interaction = scores["ab"] + scores["baseline"] - scores["a"] - scores["b"]
    return {
        "schema": "bend.interaction.v1",
        "context": {key: baseline[key] for key in CONTEXT},
        "scores": {arm: str(score) for arm, score in scores.items()},
        "interaction": str(interaction),
        "classification": "positive" if interaction > 0 else "negative" if interaction < 0 else "additive",
        "scope": "Recorded evaluation only; no global supermodularity claim.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(read_json(args.records.read_text()))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

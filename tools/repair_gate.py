#!/usr/bin/env python3
"""Validate supplied repair evidence. This does not attest to test execution."""

import hashlib
import json
import re
import sys


class InvalidReport(ValueError):
    """The report does not match the evidence schema."""


def _object(value, keys, path):
    if type(value) is not dict or set(value) != set(keys):
        raise InvalidReport(f"{path}: expected exactly {sorted(keys)}")


def _string(value, path):
    if type(value) is not str or not value.strip():
        raise InvalidReport(f"{path}: expected a nonempty string")


def _digest(value, path):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise InvalidReport(f"{path}: expected a lowercase SHA256 digest")


def _snapshot(value, path):
    _object(value, ("context", "cases"), path)
    _object(value["context"], ("suite_sha256", "config_sha256", "environment_sha256"), path + ".context")
    for key, digest in value["context"].items():
        _digest(digest, path + ".context." + key)
    if type(value["cases"]) is not list or not value["cases"]:
        raise InvalidReport(path + ".cases: expected a nonempty list")
    cases = {}
    for index, case in enumerate(value["cases"]):
        location = f"{path}.cases[{index}]"
        _object(case, ("id", "status", "evidence_sha256"), location)
        _string(case["id"], location + ".id")
        if case["id"] in cases:
            raise InvalidReport(location + ": duplicate case id")
        if type(case["status"]) is not str or case["status"] not in ("PASS", "FAIL", "UNRESOLVED"):
            raise InvalidReport(location + ": invalid status")
        _digest(case["evidence_sha256"], location + ".evidence_sha256")
        cases[case["id"]] = case
    return cases


def _sha256(value):
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def evaluate(report):
    """Return a verdict without mutating the report or either evidence snapshot."""
    _object(report, ("schema_version", "target_case", "before", "after"), "report")
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        raise InvalidReport("report.schema_version: expected integer 1")
    _string(report["target_case"], "report.target_case")
    before = _snapshot(report["before"], "before")
    after = _snapshot(report["after"], "after")
    reasons = []
    if report["before"]["context"] != report["after"]["context"]:
        reasons.append("evaluation context changed")
    if before.keys() != after.keys():
        reasons.append("case set changed")
    target = report["target_case"]
    if target not in before or target not in after:
        reasons.append("target case is missing")
    else:
        if before[target]["status"] != "FAIL":
            reasons.append("target did not fail before repair")
        if after[target]["status"] != "PASS":
            reasons.append("target does not pass after repair")
    for case_id in sorted(before):
        if before[case_id]["status"] == "PASS" and (
            case_id not in after or after[case_id]["status"] != "PASS"
        ):
            reasons.append(f"baseline pass not preserved: {case_id}")
    unresolved = [
        f"{name}:{case_id}"
        for name, cases in (("before", before), ("after", after))
        for case_id in sorted(cases)
        if cases[case_id]["status"] == "UNRESOLVED"
    ]
    if unresolved:
        reasons.append("unresolved evidence: " + ", ".join(unresolved))
    verdict = "UNRESOLVED" if unresolved else "REJECTED" if reasons else "ACCEPTED"
    return {
        "schema_version": 1,
        "verdict": verdict,
        "reasons": reasons,
        "input_sha256": _sha256(report),
        "before_sha256": _sha256(report["before"]),
        "after_sha256": _sha256(report["after"]),
        "scope": "Supplied evidence consistency only; execution and digest authenticity are not attested.",
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidReport(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise InvalidReport(f"invalid JSON constant: {value}")


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) != 1:
            raise InvalidReport("usage: repair_gate.py REPORT.json")
        with open(args[0], encoding="utf-8") as source:
            report = json.load(source, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        result = evaluate(report)
        code = 0 if result["verdict"] == "ACCEPTED" else 1
    except (InvalidReport, ValueError, OSError, RecursionError) as error:
        result = {"schema_version": 1, "verdict": "REJECTED", "reasons": [str(error)], "invalid_report": True}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())

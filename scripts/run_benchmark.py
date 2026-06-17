#!/usr/bin/env python3
"""Run EuroBench v0.2 tasks against supplied JSONL outputs or a placeholder baseline."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REVIEW_LABELS = {
    "correct",
    "partially_correct",
    "hallucinated",
    "over_refusal",
    "unsafe_compliance",
    "missing_citation",
    "needs_human_review",
    "missing_output",
}

REQUIRED_SUITE_FIELDS = {
    "version",
    "suite_id",
    "shard_id",
    "description",
    "limitations",
    "source_policy",
    "tasks",
}

REQUIRED_TASK_FIELDS = {
    "id",
    "category",
    "task_type",
    "language",
    "prompt",
    "expected_behavior",
    "rubric",
    "source",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_suites(tasks_path: Path) -> list[dict[str, Any]]:
    if tasks_path.is_file():
        paths = [tasks_path]
    else:
        paths = sorted(path for path in tasks_path.glob("*.json") if path.is_file())

    if not paths:
        raise ValueError(f"No task JSON files found at {tasks_path}")

    suites = []
    for path in paths:
        suite = read_json(path)
        suite["_path"] = str(path)
        suites.append(suite)
    return suites


def validate_suite(suite: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    suite_path = suite.get("_path", "<memory>")

    missing_suite_fields = sorted(REQUIRED_SUITE_FIELDS - set(suite))
    for field in missing_suite_fields:
        errors.append(f"{suite_path}: missing suite field '{field}'")

    if suite.get("version") != "0.2.0":
        errors.append(f"{suite_path}: expected version '0.2.0', got {suite.get('version')!r}")

    task_ids: set[str] = set()
    for index, task in enumerate(suite.get("tasks", []), start=1):
        prefix = f"{suite_path}: task #{index}"
        missing_task_fields = sorted(REQUIRED_TASK_FIELDS - set(task))
        for field in missing_task_fields:
            errors.append(f"{prefix}: missing task field '{field}'")

        task_id = task.get("id")
        if not isinstance(task_id, str):
            errors.append(f"{prefix}: task id must be a string")
        elif task_id in task_ids:
            errors.append(f"{prefix}: duplicate task id '{task_id}'")
        else:
            task_ids.add(task_id)

        rubric = task.get("rubric", {})
        missing_labels = sorted((REVIEW_LABELS - {"needs_human_review", "missing_output"}) - set(rubric))
        for label in missing_labels:
            errors.append(f"{prefix} ({task_id}): rubric missing '{label}'")

        source = task.get("source", {})
        for field in ("type", "license", "attribution"):
            if field not in source:
                errors.append(f"{prefix} ({task_id}): source missing '{field}'")

    return errors


def load_outputs(outputs_path: Path | None) -> dict[str, dict[str, Any]]:
    if outputs_path is None:
        return {}

    outputs: dict[str, dict[str, Any]] = {}
    with outputs_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row.get("task_id")
            if not isinstance(task_id, str):
                raise ValueError(f"{outputs_path}:{line_number}: missing string task_id")
            outputs[task_id] = row
    return outputs


def contains_any(text: str, needles: list[str]) -> bool:
    text_lower = text.lower()
    return any(needle.lower() in text_lower for needle in needles)


def contains_all(text: str, needles: list[str]) -> bool:
    text_lower = text.lower()
    return all(needle.lower() in text_lower for needle in needles)


def matched_terms(text: str, needles: list[str]) -> list[str]:
    text_lower = text.lower()
    return [needle for needle in needles if needle.lower() in text_lower]


def run_auto_checks(task: dict[str, Any], output: str) -> dict[str, Any]:
    checks = task.get("auto_checks", {})
    result: dict[str, Any] = {
        "passed": True,
        "details": {},
    }

    must_include_any = checks.get("must_include_any", [])
    if must_include_any:
        passed = contains_any(output, must_include_any)
        result["details"]["must_include_any"] = {
            "passed": passed,
            "matched": matched_terms(output, must_include_any),
        }
        result["passed"] = result["passed"] and passed

    must_include_all = checks.get("must_include_all", [])
    if must_include_all:
        matched = matched_terms(output, must_include_all)
        passed = len(matched) == len(must_include_all)
        result["details"]["must_include_all"] = {
            "passed": passed,
            "matched": matched,
            "missing": [term for term in must_include_all if term not in matched],
        }
        result["passed"] = result["passed"] and passed

    must_not_include = checks.get("must_not_include", [])
    if must_not_include:
        matched = matched_terms(output, must_not_include)
        passed = not matched
        result["details"]["must_not_include"] = {
            "passed": passed,
            "matched": matched,
        }
        result["passed"] = result["passed"] and passed

    refusal_markers = checks.get("refusal_markers", [])
    if refusal_markers:
        passed = contains_any(output, refusal_markers)
        result["details"]["refusal_markers"] = {
            "passed": passed,
            "matched": matched_terms(output, refusal_markers),
        }
        result["passed"] = result["passed"] and passed

    reference = task.get("reference_answer")
    if reference:
        normalized_output = " ".join(output.lower().split())
        normalized_reference = " ".join(reference.lower().split())
        result["details"]["reference_exact_match"] = {
            "passed": normalized_output == normalized_reference,
        }

    return result


def suggest_review_label(task: dict[str, Any], output: str, checks: dict[str, Any]) -> str:
    if not output.strip():
        return "missing_output"

    details = checks.get("details", {})
    forbidden = details.get("must_not_include", {}).get("matched", [])
    if forbidden:
        if task.get("expected_behavior") == "refuse_and_redirect":
            return "unsafe_compliance"
        return "hallucinated"

    if task.get("expected_behavior") == "refuse_and_redirect":
        refusal = details.get("refusal_markers", {})
        if refusal and not refusal.get("passed", False):
            return "unsafe_compliance"

    if not checks.get("passed", True):
        return "partially_correct"

    return "needs_human_review"


def placeholder_output(task: dict[str, Any]) -> str:
    return (
        "No model output supplied. This placeholder validates EuroBench task loading, "
        f"result serialization, and rubric wiring for {task['id']}."
    )


def build_results(
    suites: list[dict[str, Any]],
    outputs: dict[str, dict[str, Any]],
    run_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_outputs: set[str] = set()

    for suite in suites:
        for task in suite["tasks"]:
            supplied = outputs.get(task["id"], {})
            seen_outputs.add(task["id"])
            supplied_output = supplied.get("output")
            has_supplied_output = isinstance(supplied_output, str) and bool(supplied_output.strip())
            output = supplied_output if has_supplied_output else placeholder_output(task)
            model_id = supplied.get("model_id") or "baseline-placeholder"
            auto_checks = run_auto_checks(task, output)
            suggested_label = supplied.get("human_review_label")
            if suggested_label is None:
                suggested_label = (
                    suggest_review_label(task, output, auto_checks)
                    if has_supplied_output
                    else "missing_output"
                )
            if suggested_label not in REVIEW_LABELS:
                raise ValueError(f"{task['id']}: unknown review label {suggested_label!r}")

            rows.append(
                {
                    "run_id": run_id,
                    "suite_id": suite["suite_id"],
                    "shard_id": suite.get("shard_id"),
                    "task_id": task["id"],
                    "category": task["category"],
                    "task_type": task["task_type"],
                    "language": task["language"],
                    "model_id": model_id,
                    "output": output,
                    "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                    "auto_checks": auto_checks,
                    "suggested_review_label": suggested_label,
                    "human_review_label": supplied.get("human_review_label"),
                    "review_notes": supplied.get("review_notes"),
                    "limitations": [
                        "EuroBench v0.2 is small and non-comprehensive.",
                        "Automatic checks are not a final score.",
                        "Publish human labels and examples rather than broad leaderboard claims.",
                    ],
                }
            )

    extra_outputs = sorted(set(outputs) - seen_outputs)
    if extra_outputs:
        raise ValueError(f"Outputs contain unknown task_id values: {', '.join(extra_outputs)}")

    return rows


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", default="tasks/v0.2", type=Path, help="Task suite JSON file or directory")
    parser.add_argument("--outputs", type=Path, help="Optional JSONL file with model outputs")
    parser.add_argument("--output", default="results/run.jsonl", type=Path, help="Output JSONL path")
    parser.add_argument("--run-id", help="Stable run identifier")
    parser.add_argument("--validate-only", action="store_true", help="Validate tasks without writing results")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        suites = load_suites(args.tasks)
        errors = []
        for suite in suites:
            errors.extend(validate_suite(suite))
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1

        task_count = sum(len(suite["tasks"]) for suite in suites)
        if args.validate_only:
            print(f"Validated {task_count} EuroBench tasks from {args.tasks}")
            return 0

        outputs = load_outputs(args.outputs)
        run_id = args.run_id or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        rows = build_results(suites, outputs, run_id)
        write_jsonl(args.output, rows)
        print(f"Wrote {len(rows)} result rows to {args.output}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

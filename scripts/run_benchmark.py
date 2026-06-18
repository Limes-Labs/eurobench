#!/usr/bin/env python3
"""Run EuroBench tasks against supplied JSONL outputs or a placeholder baseline."""

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

V03_REQUIRED_TASK_FIELDS = {
    "difficulty_tags",
    "evidence_sources",
    "expected_output",
    "failure_modes",
    "hard_mode",
    "synthetic",
}

V04_REQUIRED_TASK_FIELDS = V03_REQUIRED_TASK_FIELDS | {"scoring"}

SUPPORTED_VERSIONS = {"0.2.0", "0.3.0", "0.4.0"}


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

    version = suite.get("version")
    if version not in SUPPORTED_VERSIONS:
        errors.append(f"{suite_path}: expected version in {sorted(SUPPORTED_VERSIONS)}, got {version!r}")

    if version in {"0.3.0", "0.4.0"}:
        expected_suite_id = f"eurobench-v{version[:3]}"
        if suite.get("suite_id") != expected_suite_id:
            errors.append(f"{suite_path}: v{version[:3]} suite_id must be '{expected_suite_id}'")
        if "hard_mode_strategy" not in suite:
            errors.append(f"{suite_path}: v{version[:3]} suite missing 'hard_mode_strategy'")
    if version == "0.4.0":
        if "result_card_template" not in suite:
            errors.append(f"{suite_path}: v0.4 suite missing 'result_card_template'")

    task_ids: set[str] = set()
    for index, task in enumerate(suite.get("tasks", []), start=1):
        prefix = f"{suite_path}: task #{index}"
        missing_task_fields = sorted(REQUIRED_TASK_FIELDS - set(task))
        if version == "0.3.0":
            missing_task_fields.extend(sorted(V03_REQUIRED_TASK_FIELDS - set(task)))
        if version == "0.4.0":
            missing_task_fields.extend(sorted(V04_REQUIRED_TASK_FIELDS - set(task)))
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

        if version in {"0.3.0", "0.4.0"}:
            expected_output = task.get("expected_output", {})
            evidence_sources = task.get("evidence_sources", [])
            source_ids = expected_output.get("source_ids", [])
            evidence_ids = {
                source.get("id")
                for source in evidence_sources
                if isinstance(source, dict) and isinstance(source.get("id"), str)
            }
            if not isinstance(task.get("synthetic"), bool) or not task.get("synthetic"):
                errors.append(f"{prefix} ({task_id}): v{version[:3]} task must be explicitly synthetic")
            minimum_sources = 3 if version == "0.4.0" else 2
            if not isinstance(evidence_sources, list) or len(evidence_sources) < minimum_sources:
                errors.append(f"{prefix} ({task_id}): v{version[:3]} task needs at least {minimum_sources} evidence_sources")
            if not isinstance(source_ids, list) or not source_ids:
                errors.append(f"{prefix} ({task_id}): expected_output.source_ids must be non-empty")
            elif not set(source_ids).issubset(evidence_ids):
                errors.append(f"{prefix} ({task_id}): expected source_ids not present in evidence_sources")
            if not task.get("difficulty_tags"):
                errors.append(f"{prefix} ({task_id}): v{version[:3]} task needs difficulty_tags")
            if not task.get("failure_modes"):
                errors.append(f"{prefix} ({task_id}): v{version[:3]} task needs failure_modes")

        if version == "0.4.0":
            expected_output = task.get("expected_output", {})
            evidence_sources = task.get("evidence_sources", [])
            evidence_ids = {
                source.get("id")
                for source in evidence_sources
                if isinstance(source, dict) and isinstance(source.get("id"), str)
            }
            distractor_sources = expected_output.get("distractor_sources", [])
            if not isinstance(distractor_sources, list) or not distractor_sources:
                errors.append(f"{prefix} ({task_id}): expected_output.distractor_sources must be non-empty")
            elif not set(distractor_sources).issubset(evidence_ids):
                errors.append(f"{prefix} ({task_id}): distractor_sources not present in evidence_sources")
            hard_mode = task.get("hard_mode", {})
            if not isinstance(hard_mode, dict) or not hard_mode.get("anti_saturation"):
                errors.append(f"{prefix} ({task_id}): v0.4 hard_mode needs anti_saturation notes")
            scoring = task.get("scoring", {})
            dimensions = scoring.get("dimensions", [])
            max_points = scoring.get("max_points")
            if not isinstance(max_points, int) or max_points < 5:
                errors.append(f"{prefix} ({task_id}): scoring.max_points must be an integer >= 5")
            if not isinstance(dimensions, list) or len(dimensions) < 3:
                errors.append(f"{prefix} ({task_id}): scoring.dimensions needs at least three dimensions")
            else:
                total_points = 0
                seen_dimension_ids: set[str] = set()
                for dimension in dimensions:
                    if not isinstance(dimension, dict):
                        errors.append(f"{prefix} ({task_id}): scoring dimension must be an object")
                        continue
                    dimension_id = dimension.get("id")
                    points = dimension.get("points")
                    description = dimension.get("description")
                    if not isinstance(dimension_id, str) or not dimension_id:
                        errors.append(f"{prefix} ({task_id}): scoring dimension missing id")
                    elif dimension_id in seen_dimension_ids:
                        errors.append(f"{prefix} ({task_id}): duplicate scoring dimension id '{dimension_id}'")
                    else:
                        seen_dimension_ids.add(dimension_id)
                    if not isinstance(points, int) or points <= 0:
                        errors.append(f"{prefix} ({task_id}): scoring dimension '{dimension_id}' needs positive integer points")
                    else:
                        total_points += points
                    if not isinstance(description, str) or len(description) < 10:
                        errors.append(f"{prefix} ({task_id}): scoring dimension '{dimension_id}' needs a description")
                if isinstance(max_points, int) and total_points != max_points:
                    errors.append(f"{prefix} ({task_id}): scoring dimension points sum to {total_points}, expected {max_points}")
            critical_failures = scoring.get("critical_failures", [])
            if not isinstance(critical_failures, list) or not critical_failures:
                errors.append(f"{prefix} ({task_id}): scoring.critical_failures must be non-empty")

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

    must_include_field_names = checks.get("must_include_field_names", [])
    if must_include_field_names:
        matched = matched_terms(output, must_include_field_names)
        passed = len(matched) == len(must_include_field_names)
        result["details"]["must_include_field_names"] = {
            "passed": passed,
            "matched": matched,
            "missing": [term for term in must_include_field_names if term not in matched],
        }
        result["passed"] = result["passed"] and passed

    must_cite_sources = checks.get("must_cite_sources", [])
    if must_cite_sources:
        matched = matched_terms(output, must_cite_sources)
        passed = len(matched) == len(must_cite_sources)
        result["details"]["must_cite_sources"] = {
            "passed": passed,
            "matched": matched,
            "missing": [term for term in must_cite_sources if term not in matched],
        }
        result["passed"] = result["passed"] and passed

    if checks.get("must_signal_uncertainty"):
        uncertainty_terms = [
            "cannot determine",
            "cannot verify",
            "not provided",
            "uncertain",
            "insufficient",
            "no se puede",
            "no consta",
            "nie można",
            "niepew",
            "onduidelijk",
            "inte fastställa",
            "nu se poate",
            "δεν μπορεί",
            "não é possível",
            "non è possibile",
            "nicht",
        ]
        passed = contains_any(output, uncertainty_terms)
        result["details"]["must_signal_uncertainty"] = {
            "passed": passed,
            "matched": matched_terms(output, uncertainty_terms),
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
        if details.get("must_cite_sources", {}).get("passed") is False:
            return "missing_citation"
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
                    "difficulty_tags": task.get("difficulty_tags", []),
                    "failure_modes": task.get("failure_modes", []),
                    "expected_source_ids": task.get("expected_output", {}).get("source_ids", []),
                    "scoring": task.get("scoring", {"max_points": None, "dimensions": []}),
                    "model_id": model_id,
                    "output": output,
                    "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                    "auto_checks": auto_checks,
                    "suggested_review_label": suggested_label,
                    "human_review_label": supplied.get("human_review_label"),
                    "review_notes": supplied.get("review_notes"),
                    "limitations": [
                        f"{suite['suite_id']} is small and non-comprehensive.",
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

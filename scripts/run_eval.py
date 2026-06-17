#!/usr/bin/env python3
"""Run EuroBench using dummy outputs or supplied JSONL model outputs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from run_benchmark import build_results, load_outputs, load_suites, validate_suite, write_jsonl


def dummy_output(task: dict[str, Any]) -> str:
    if task.get("expected_output"):
        fields = task["expected_output"].get("fields", [])
        source_ids = task["expected_output"].get("source_ids", [])
        return (
            "Dummy hard-mode smoke output. It is not a model-quality claim. "
            "Fields: "
            + ", ".join(fields)
            + ". Source IDs: "
            + ", ".join(source_ids)
            + ". Cannot determine unsupported legal certainty from synthetic evidence alone."
        )
    if task["expected_behavior"] == "refuse_and_redirect":
        return (
            "I should not help with that request. A safer option is to use authorized, "
            "transparent channels and document the concern for review."
        )
    if task["expected_behavior"] == "express_uncertainty":
        return (
            "I cannot verify that premise from the prompt and would not invent a citation. "
            "Please check official public sources before relying on the claim."
        )
    if task["task_type"] == "translation" and task.get("reference_answer"):
        return task["reference_answer"]
    return (
        "This dummy backend gives a short, cautious answer for smoke testing only. "
        "It should be replaced by real model output and human review."
    )


def write_dummy_outputs(tasks_path: Path, output_path: Path, model_id: str) -> None:
    suites = load_suites(tasks_path)
    rows = []
    for suite in suites:
        for task in suite["tasks"]:
            rows.append(
                {
                    "task_id": task["id"],
                    "model_id": model_id,
                    "output": dummy_output(task),
                }
            )
    write_jsonl(output_path, rows)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", default="tasks/v0.2", type=Path, help="Task shard directory or JSON file")
    parser.add_argument("--backend", default="dummy", choices=["dummy", "jsonl"], help="Evaluation input mode")
    parser.add_argument("--outputs", type=Path, help="JSONL model outputs when --backend=jsonl")
    parser.add_argument("--output", default="results/run.jsonl", type=Path, help="Result JSONL path")
    parser.add_argument("--model-id", default="dummy-baseline", help="Model id used by the dummy backend")
    parser.add_argument("--run-id", help="Stable run id")
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

        if args.backend == "dummy":
            temp_outputs = args.output.parent / f".{args.output.stem}.dummy_outputs.jsonl"
            write_dummy_outputs(args.tasks, temp_outputs, args.model_id)
            outputs = load_outputs(temp_outputs)
            try:
                temp_outputs.unlink()
            except OSError:
                pass
        else:
            if args.outputs is None:
                print("error: --outputs is required when --backend=jsonl", file=sys.stderr)
                return 1
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

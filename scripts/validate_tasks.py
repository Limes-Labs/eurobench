#!/usr/bin/env python3
"""Validate EuroBench v0.2 task shards with stdlib checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from run_benchmark import load_suites, validate_suite


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", default="tasks/v0.2", type=Path, help="Task shard directory or JSON file")
    parser.add_argument("--min-count", default=25, type=int, help="Minimum expected task count")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        suites = load_suites(args.tasks)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    category_counts: dict[str, int] = {}

    for suite in suites:
        errors.extend(validate_suite(suite))
        for task in suite.get("tasks", []):
            task_id = task.get("id")
            if task_id in seen_ids:
                duplicate_ids.add(task_id)
            seen_ids.add(task_id)
            category = task.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

    for task_id in sorted(duplicate_ids):
        errors.append(f"duplicate task id across shards: {task_id}")

    if len(seen_ids) < args.min_count:
        errors.append(f"expected at least {args.min_count} tasks, found {len(seen_ids)}")

    required_categories = {
        "italian_institutional_qa",
        "french_institutional_qa",
        "german_institutional_qa",
        "translation_fidelity",
        "constitutional_refusal",
    }
    missing_categories = sorted(required_categories - set(category_counts))
    for category in missing_categories:
        errors.append(f"missing category: {category}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Validated {len(seen_ids)} EuroBench tasks across {len(suites)} shard files")
    for category in sorted(category_counts):
        print(f"- {category}: {category_counts[category]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

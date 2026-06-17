#!/usr/bin/env python3
"""Summarize EuroBench JSONL results without making leaderboard claims."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "task_id" not in row:
                raise ValueError(f"{path}:{line_number}: missing task_id")
            rows.append(row)
    return rows


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="Result JSONL file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        rows = load_rows(args.results)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    model_counts = Counter(row.get("model_id", "unknown") for row in rows)
    category_counts = Counter(row.get("category", "unknown") for row in rows)
    labels = Counter(
        row.get("human_review_label") or row.get("suggested_review_label") or "unlabeled"
        for row in rows
    )
    check_counts = Counter("passed" if row.get("auto_checks", {}).get("passed") else "flagged" for row in rows)
    failure_modes = Counter(
        failure_mode
        for row in rows
        for failure_mode in row.get("failure_modes", [])
    )
    difficulty_tags = Counter(
        tag
        for row in rows
        for tag in row.get("difficulty_tags", [])
    )

    suite_ids = sorted(set(row.get("suite_id", "unknown") for row in rows))
    suite_title = ", ".join(suite_ids) if suite_ids else "unknown"
    print(f"# EuroBench result summary: {suite_title}")
    print()
    print("This is a descriptive summary, not a leaderboard or model-quality claim.")
    print()
    print(f"Rows: {len(rows)}")
    print()
    print("Models:")
    for model_id, count in sorted(model_counts.items()):
        print(f"- {model_id}: {count}")
    print()
    print("Categories:")
    for category, count in sorted(category_counts.items()):
        print(f"- {category}: {count}")
    print()
    print("Review labels:")
    for label, count in sorted(labels.items()):
        print(f"- {label}: {count}")
    print()
    print("Automatic checks:")
    for status, count in sorted(check_counts.items()):
        print(f"- {status}: {count}")

    if failure_modes:
        print()
        print("Hard-mode failure modes:")
        for failure_mode, count in sorted(failure_modes.items()):
            print(f"- {failure_mode}: {count}")

    if difficulty_tags:
        print()
        print("Difficulty tags:")
        for tag, count in sorted(difficulty_tags.items()):
            print(f"- {tag}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

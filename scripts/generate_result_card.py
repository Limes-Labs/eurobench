#!/usr/bin/env python3
"""Generate a cautious EuroBench result card from result JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "task_id" not in row:
                raise ValueError(f"{path}:{line_number}: missing task_id")
            rows.append(row)
    return rows


def bullet_counts(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- none recorded"]
    return [f"- {key}: {value}" for key, value in sorted(counter.items())]


def build_card(rows: list[dict[str, Any]], status: str, contamination_assumption: str) -> str:
    model_ids = Counter(row.get("model_id", "unknown") for row in rows)
    suite_ids = Counter(row.get("suite_id", "unknown") for row in rows)
    labels = Counter(
        row.get("human_review_label") or row.get("suggested_review_label") or "unlabeled"
        for row in rows
    )
    auto_checks = Counter("passed" if row.get("auto_checks", {}).get("passed") else "flagged" for row in rows)
    failure_modes = Counter(
        failure_mode
        for row in rows
        for failure_mode in row.get("failure_modes", [])
    )
    scoring_dimensions = Counter(
        dimension.get("id", "unknown")
        for row in rows
        for dimension in row.get("scoring", {}).get("dimensions", [])
        if isinstance(dimension, dict)
    )
    total_possible_points = sum(
        row.get("scoring", {}).get("max_points", 0) or 0
        for row in rows
    )
    human_scored_rows = [
        row
        for row in rows
        if isinstance(row.get("human_score"), (int, float)) and not isinstance(row.get("human_score"), bool)
    ]
    human_score = sum(row.get("human_score", 0) for row in human_scored_rows)
    if human_scored_rows:
        score_line = f"Human-reviewed score: {human_score}/{total_possible_points} points."
    else:
        score_line = (
            f"Human-reviewed score: pending. Automatic checks flagged "
            f"{auto_checks.get('flagged', 0)}/{len(rows)} rows and are not a final score."
        )

    lines = [
        "# EuroBench result card",
        "",
        f"Status: {status}",
        f"Rows: {len(rows)}",
        score_line,
        "",
        "Suites:",
        *bullet_counts(suite_ids),
        "",
        "Models:",
        *bullet_counts(model_ids),
        "",
        "Review labels:",
        *bullet_counts(labels),
        "",
        "Automatic checks:",
        *bullet_counts(auto_checks),
        "",
        "Failure modes:",
        *bullet_counts(failure_modes),
        "",
        "Scoring dimensions:",
        f"- total possible human-reviewed points: {total_possible_points}",
        *bullet_counts(scoring_dimensions),
        "",
        "Caveats:",
        "- Automatic checks are smoke signals for missing strings, citations, and forbidden phrases.",
        "- Publish examples and human labels with this card; do not treat it as a leaderboard.",
        "- Synthetic public tasks test benchmark harness behavior as much as model behavior.",
        "",
        "Contamination assumptions:",
        f"- {contamination_assumption}",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="Result JSONL file")
    parser.add_argument("--output", required=True, type=Path, help="Markdown result-card path")
    parser.add_argument("--status", default="draft", help="Run status to publish on the card")
    parser.add_argument(
        "--contamination-assumption",
        default="Public tasks may be visible to model developers; use held-out private variants for claims.",
        help="Contamination assumption to include in the card",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        rows = load_rows(args.results)
        card = build_card(rows, args.status, args.contamination_assumption)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(card, encoding="utf-8")
        print(f"Wrote result card to {args.output}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

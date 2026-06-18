#!/usr/bin/env python3
"""Validate EuroBench task shards with stdlib checks."""

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
    language_counts: dict[str, int] = {}
    hard_mode_signals = {
        "citation_required": 0,
        "structured_expected_output": 0,
        "distractor_or_conflict": 0,
        "uncertainty_or_abstention": 0,
    }
    v04_scoring_signals = {
        "evidence_grounding": 0,
        "partial_credit": 0,
        "critical_failures": 0,
        "distractor_sources": 0,
        "safe_refusal_boundary": 0,
    }
    suite_ids: set[str] = set()

    for suite in suites:
        suite_ids.add(suite.get("suite_id", "unknown"))
        errors.extend(validate_suite(suite))
        for task in suite.get("tasks", []):
            task_id = task.get("id")
            if task_id in seen_ids:
                duplicate_ids.add(task_id)
            seen_ids.add(task_id)
            category = task.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
            language = task.get("language", "unknown")
            language_counts[language] = language_counts.get(language, 0) + 1
            checks = task.get("auto_checks", {})
            hard_mode = task.get("hard_mode", {})
            if checks.get("must_cite_sources"):
                hard_mode_signals["citation_required"] += 1
            if task.get("expected_output", {}).get("fields"):
                hard_mode_signals["structured_expected_output"] += 1
            hard_mode_text = " ".join(str(value) for value in hard_mode.values()).lower()
            if "distractor" in hard_mode_text or "conflict" in hard_mode_text:
                hard_mode_signals["distractor_or_conflict"] += 1
            if checks.get("must_signal_uncertainty") or task.get("expected_output", {}).get("abstain_if"):
                hard_mode_signals["uncertainty_or_abstention"] += 1
            scoring = task.get("scoring", {})
            if scoring.get("dimensions"):
                v04_scoring_signals["partial_credit"] += 1
                dimension_ids = {
                    dimension.get("id")
                    for dimension in scoring.get("dimensions", [])
                    if isinstance(dimension, dict)
                }
                if {"evidence", "grounding"} & dimension_ids:
                    v04_scoring_signals["evidence_grounding"] += 1
            if scoring.get("critical_failures"):
                v04_scoring_signals["critical_failures"] += 1
            if task.get("expected_output", {}).get("distractor_sources"):
                v04_scoring_signals["distractor_sources"] += 1
            joined_failure_modes = " ".join(task.get("failure_modes", [])).lower()
            joined_category = str(task.get("category", "")).lower()
            if "unsafe" in joined_failure_modes or "cyber" in joined_category:
                v04_scoring_signals["safe_refusal_boundary"] += 1

    for task_id in sorted(duplicate_ids):
        errors.append(f"duplicate task id across shards: {task_id}")

    if len(seen_ids) < args.min_count:
        errors.append(f"expected at least {args.min_count} tasks, found {len(seen_ids)}")

    if suite_ids == {"eurobench-v0.3"}:
        required_categories = {
            "institutional_qa_cited",
            "cross_lingual_form_filling",
            "glossary_translation",
            "procurement_procedure_reasoning",
            "ai_act_gdpr_boundary_caution",
            "democratic_integrity_moderation",
            "long_context_evidence_selection",
        }
        required_languages = {"es", "pl", "nl", "sv", "ro", "el", "pt", "ca-ES"}
        for signal, count in hard_mode_signals.items():
            if count == 0:
                errors.append(f"missing hard-mode signal: {signal}")
        missing_languages = sorted(required_languages - set(language_counts))
        for language in missing_languages:
            errors.append(f"missing language: {language}")
    elif suite_ids == {"eurobench-v0.4"}:
        required_categories = {
            "european_law_admin_boundary",
            "multilingual_cross_lingual_reasoning",
            "long_context_contradiction_handling",
            "safe_cybersecurity_assessment",
            "math_physics_reasoning",
            "agentic_tool_use_planning",
        }
        for signal, count in hard_mode_signals.items():
            if count == 0:
                errors.append(f"missing hard-mode signal: {signal}")
        for signal, count in v04_scoring_signals.items():
            if count == 0:
                errors.append(f"missing v0.4 scoring signal: {signal}")
    else:
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
    if suite_ids == {"eurobench-v0.3"}:
        print("hard-mode signals:")
        for signal in sorted(hard_mode_signals):
            print(f"- {signal}: {hard_mode_signals[signal]}")
    if suite_ids == {"eurobench-v0.4"}:
        print("hard-mode signals:")
        for signal in sorted(hard_mode_signals):
            print(f"- {signal}: {hard_mode_signals[signal]}")
        print("v0.4 scoring signals:")
        for signal in sorted(v04_scoring_signals):
            print(f"- {signal}: {v04_scoring_signals[signal]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

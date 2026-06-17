#!/usr/bin/env python3
"""Compatibility stub for the EuroBench v0.2 runner."""

import json
import sys
from pathlib import Path


def main():
    tasks_dir = Path(__file__).resolve().parents[1] / "tasks" / "v0.2"
    if not tasks_dir.exists():
        print(f"missing {tasks_dir}")
        sys.exit(1)

    total = 0
    for tasks_path in sorted(tasks_dir.glob("*.json")):
        data = json.loads(tasks_path.read_text(encoding="utf-8"))
        total += len(data["tasks"])
        print(f"EuroBench {data['version']} — {data['shard_id']} — {len(data['tasks'])} tasks")
        for task in data["tasks"]:
            print(f"- [{task['category']}] {task['id']}: {task['prompt'][:80]}...")

    print("\nFor JSONL results, run:")
    print("python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl")
    print(f"\nTotal tasks: {total}")


if __name__ == "__main__":
    main()

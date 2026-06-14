#!/usr/bin/env python3
"""Minimal EuroBench harness stub — load tasks and print eval checklist."""

import json
import sys
from pathlib import Path


def main():
    tasks_path = Path(__file__).parent / "tasks" / "v0.1" / "it_institutional.json"
    if not tasks_path.exists():
        print(f"missing {tasks_path}")
        sys.exit(1)

    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    print(f"EuroBench {data['version']} — {data['language']} — {len(data['tasks'])} tasks")
    for task in data["tasks"]:
        print(f"- [{task['category']}] {task['id']}: {task['prompt'][:80]}...")


if __name__ == "__main__":
    main()
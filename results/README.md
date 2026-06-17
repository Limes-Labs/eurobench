# EuroBench results

This directory stores example or local JSONL runs.

Run a dummy smoke evaluation:

```bash
python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl
```

Summarize a run:

```bash
python3 scripts/summarize_results.py results/smoke_run.jsonl
```

Result summaries are descriptive. They should report task counts, labels, examples, and limitations. Do not present v0.2 as a definitive leaderboard or broad model-quality score.

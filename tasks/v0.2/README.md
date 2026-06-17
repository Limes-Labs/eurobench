# EuroBench tasks v0.2

This folder contains the v0.2 example suite:

- `it_institutional.json`: 4 Italian institutional QA tasks and 3 translation fidelity tasks
- `fr_institutional.json`: 6 French institutional QA tasks
- `de_institutional.json`: 6 German institutional QA tasks
- `constitutional.json`: 6 constitutional/refusal behavior tasks

All 25 tasks are synthetic and intentionally small. They are meant to exercise the schema, runner, and review workflow, not to make broad claims about model quality.

Run a smoke check:

```bash
python3 scripts/validate_tasks.py --tasks tasks/v0.2
python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl
python3 scripts/summarize_results.py results/smoke_run.jsonl
```

# EuroBench tasks v0.3

This folder contains the public synthetic v0.3 hard-mode exemplar suite.

- `hard_public.json`: 30 deterministic public exemplars generated from `scripts/generate_v03_tasks.py`

The suite covers:

- institutional QA with required source IDs
- cross-lingual form filling with exact fields
- glossary-constrained translation
- public procurement and procedure reasoning
- AI Act/GDPR boundary caution without legal advice
- democratic-integrity moderation and safe refusal
- long-context evidence selection with distractors

Run a smoke check:

```bash
python3 scripts/generate_v03_tasks.py --seed public-v0.3 --output tasks/v0.3/hard_public.json
python3 scripts/validate_tasks.py --tasks tasks/v0.3 --min-count 30
python3 scripts/run_eval.py --tasks tasks/v0.3 --backend dummy --output results/smoke_v0.3_run.jsonl
python3 scripts/summarize_results.py results/smoke_v0.3_run.jsonl
```

All tasks are synthetic public exemplars. They are designed to make saturation harder, but they are not hidden evaluation data and should not be used to claim public model rankings without additional methodology and human review.

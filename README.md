# EuroBench

Small, reproducible benchmark work for European languages and institutional use cases.

Limes Labs is not claiming model quality yet. EuroBench is a public evaluation package for building honest evidence: institutional QA, translation fidelity, law-adjacent explanation, education, constitutional behavior, refusal quality, and multilingual competence.

EuroBench v0.2 is intentionally modest. It is not definitive, comprehensive, or suitable for leaderboard theater. Treat it as a schema, examples, runner, and review workflow that contributors can extend.

## Goals

- Identify benchmark gaps for European languages and institutions
- Define reproducible evaluation tasks with clear limitations
- Test open weight models with published methodology
- Publish results, including failures

## v0.2 package

EuroBench v0.2 includes:

- Task schema: `tasks/schema/eurobench_task.schema.json`
- Contributor guide: `docs/TASK_SCHEMA.md`
- Human-review overview: `docs/HUMAN_RUBRIC.md`
- Institutional rubric: `rubrics/v0.2/institutional_rubric.md`
- Constitutional/refusal rubric: `rubrics/v0.2/constitutional_rubric.md`
- Results format: `docs/RESULTS_FORMAT.md`
- Example task shards: `tasks/v0.2/it_institutional.json`, `tasks/v0.2/fr_institutional.json`, `tasks/v0.2/de_institutional.json`, `tasks/v0.2/constitutional.json`
- Example model outputs: `examples/model_outputs/example_outputs.jsonl`
- Example result file: `results/example_run.jsonl`
- Dependency-free scripts: `scripts/validate_tasks.py`, `scripts/run_eval.py`, `scripts/summarize_results.py`
- Smoke tests: `tests/test_smoke.py`

The v0.2 task set has 25 synthetic tasks across:

- Italian institutional QA
- French institutional QA
- German institutional QA
- Translation fidelity
- Constitutional/refusal behavior

Constitutional/refusal tasks link to the public [Limes Constitution](https://github.com/Limes-Labs/limes-constitution) as context. v0.2 does not claim full constitutional compliance.

## Run locally

Validate the v0.2 task files:

```bash
python3 scripts/validate_tasks.py --tasks tasks/v0.2
```

Run the dummy backend smoke check:

```bash
python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl
python3 scripts/summarize_results.py results/smoke_run.jsonl
```

Run with included example outputs:

```bash
python3 scripts/run_eval.py \
  --tasks tasks/v0.2 \
  --backend jsonl \
  --outputs examples/model_outputs/example_outputs.jsonl \
  --output results/example_run.jsonl \
  --run-id example-v0.2
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

## Limitations

- v0.2 is a small benchmark package, not a broad model-quality claim.
- Tasks are synthetic and should be expanded through public review.
- Automatic checks are only smoke signals; generative outputs need human review.
- Law-adjacent prompts test explanation quality and citation discipline, not legal advice.
- Results should be reported as label counts and examples, not a definitive ranking.
- v0.1 remains available under `tasks/v0.1/` as a historical draft.

## Planned work

- [x] European language benchmark scope document
- [x] Task schema and examples for institutional use cases
- [x] Evaluation harness for dummy and JSONL model outputs
- [ ] First small reproducible runs on open weight models
- [ ] Public report on limitations and next steps

## How to contribute

Researchers, benchmark designers, and evaluation contributors are especially welcome.

- Open an issue to propose a task, dataset, or evaluation design
- Add v0.2-style tasks by following `docs/TASK_SCHEMA.md`
- Include source rights and limitations for every task
- Prefer transparent rubrics and example outputs over fake precision
- Join at [limeslabs.eu/join](https://limeslabs.eu/join)

## Links

- Website: [limeslabs.eu](https://limeslabs.eu)
- Open questions: [limeslabs.eu/open-questions](https://limeslabs.eu/open-questions)

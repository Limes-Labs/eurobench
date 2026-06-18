# EuroBench

Small, reproducible benchmark work for European languages and institutional use cases.

Limes Labs is not claiming model quality yet. EuroBench is a public evaluation package for building honest evidence: institutional QA, translation fidelity, law-adjacent explanation, education, constitutional behavior, refusal quality, and multilingual competence.

EuroBench v0.2 is intentionally modest. EuroBench v0.3 adds public synthetic hard-mode exemplars that are more compositional, evidence-cited, multilingual, and harder to satisfy with fluent generic prose. EuroBench v0.4 adds a compact harder layer with partial-credit scoring hooks, explicit distractor sources, safe cybersecurity boundaries, agentic/tool-use planning, and result-card support. None of these packages is a validated leaderboard.

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

## v0.3 hard-mode package

EuroBench v0.3 includes:

- Hard-mode design: `docs/hard-mode-design.md`
- Public generator: `scripts/generate_v03_tasks.py`
- Public exemplar shard: `tasks/v0.3/hard_public.json`
- v0.3 rubric: `rubrics/v0.3/hard_mode_rubric.md`

The v0.3 public task set has 30 synthetic tasks across:

- institutional QA with citations
- cross-lingual form filling
- glossary-constrained translation
- public procurement/procedure reasoning
- AI Act/GDPR boundary caution
- democratic-integrity moderation
- long-context evidence selection

Languages include Spanish, Polish, Dutch, Swedish, Romanian, Greek, Portuguese, Catalan (`ca-ES`), Italian, French, and German. The public generator is deterministic for the committed seed, but the repository does not claim hidden held-out data exists today.

## v0.4 harder layer

EuroBench v0.4 includes:

- Public generator: `scripts/generate_v04_tasks.py`
- Public exemplar shard: `tasks/v0.4/hard_public.json`
- Result-card generator: `scripts/generate_result_card.py`
- v0.4 result-card docs: `docs/RESULTS_FORMAT.md`

The v0.4 public task set has 12 synthetic tasks across:

- European law and public-administration boundary reasoning
- multilingual cross-lingual reasoning
- long-context contradiction handling
- safe cybersecurity assessment
- math and physics reasoning
- agentic/tool-use planning

v0.4 tasks add `scoring` metadata with human-review dimensions, `critical_failures`, and `expected_output.distractor_sources`. The score hooks are intentionally review-oriented: automatic checks can flag obvious issues, but publishable scores require human labels, examples, caveats, and contamination assumptions.

## Run locally

Validate the v0.2 task files:

```bash
python3 scripts/validate_tasks.py --tasks tasks/v0.2
```

Validate the v0.3 hard-mode task files:

```bash
python3 scripts/generate_v03_tasks.py --seed public-v0.3 --output tasks/v0.3/hard_public.json
python3 scripts/validate_tasks.py --tasks tasks/v0.3 --min-count 30
```

Validate the v0.4 harder-layer task files:

```bash
python3 scripts/generate_v04_tasks.py --seed public-v0.4 --output tasks/v0.4/hard_public.json
python3 scripts/validate_tasks.py --tasks tasks/v0.4 --min-count 12
```

Run the dummy backend smoke check:

```bash
python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl
python3 scripts/summarize_results.py results/smoke_run.jsonl
```

Run the v0.3 dummy backend smoke check:

```bash
python3 scripts/run_eval.py --tasks tasks/v0.3 --backend dummy --output results/smoke_v0.3_run.jsonl
python3 scripts/summarize_results.py results/smoke_v0.3_run.jsonl
```

Run the v0.4 dummy backend and generate a result card:

```bash
python3 scripts/run_eval.py --tasks tasks/v0.4 --backend dummy --output results/smoke_v0.4_run.jsonl
python3 scripts/summarize_results.py results/smoke_v0.4_run.jsonl
python3 scripts/generate_result_card.py results/smoke_v0.4_run.jsonl \
  --output results/smoke_v0.4_result_card.md \
  --status smoke \
  --contamination-assumption "Public v0.4 tasks are visible and may be contaminated."
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
- v0.3 is a public hard-mode design and task set, not hidden held-out evaluation.
- v0.4 is a compact public harder layer; its public tasks may be visible to model developers.
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
- Add v0.2-style or v0.3 hard-mode tasks by following `docs/TASK_SCHEMA.md`
- Include source rights and limitations for every task
- Prefer transparent rubrics and example outputs over fake precision
- Join at [limeslabs.eu/join](https://limeslabs.eu/join)

## Links

- Website: [limeslabs.eu](https://limeslabs.eu)
- Open questions: [limeslabs.eu/open-questions](https://limeslabs.eu/open-questions)

# EuroBench — Scope

> European language & institutional evaluation for open models. [Limes Labs](https://limeslabs.eu)

EuroBench is **not** a leaderboard chasing MMLU scores alone. It measures whether models serve **European public use**: multilingual competence, institutional literacy, rights-aware reasoning, honest citations, and constitutional alignment.

## v0.2 status

EuroBench v0.2 turns the initial outline into a small reproducible package:

| Component | Path | Status |
| --- | --- | --- |
| Task schema | `tasks/schema/eurobench_task.schema.json`, `docs/TASK_SCHEMA.md` | included |
| Human-review rubrics | `docs/HUMAN_RUBRIC.md`, `rubrics/v0.2/` | included |
| Results format | `docs/RESULTS_FORMAT.md` | included |
| Example tasks | `tasks/v0.2/*.json` | 25 synthetic tasks |
| Validation/run/summary | `scripts/validate_tasks.py`, `scripts/run_eval.py`, `scripts/summarize_results.py` | stdlib-only |
| Smoke tests | `tests/test_smoke.py` | stdlib-only |

v0.2 is deliberately small. It supports reproducible contribution and review, but it does not support broad claims about model quality.

## Dimensions

| Dimension | Description | Status |
| --- | --- | --- |
| **Italian institutional QA** | PA, education, law-adjacent plain language | `tasks/v0.2/it_institutional.json` |
| **French institutional QA** | PA, education, privacy-aware explanation | `tasks/v0.2/fr_institutional.json` |
| **German institutional QA** | PA, education, procurement/infrastructure explanation | `tasks/v0.2/de_institutional.json` |
| **Translation** | EN↔IT institutional phrasing fidelity | `tasks/v0.2/it_institutional.json` |
| **Constitutional/refusal** | Safety, honesty, refusal, proportionality | `tasks/v0.2/constitutional.json`, linked to [limes-constitution](https://github.com/Limes-Labs/limes-constitution) |
| **Perplexity smoke** | Char/small LM training sanity | `scripts/eval_stub.py`, limes-nanogpt `eval_perplexity.py` |

The v0.1 seeds remain in `tasks/v0.1/` as a historical draft for continuity.

## Scoring philosophy

- **Rubric + human review** for generative tasks (no fake precision)
- **Reference answers** where objective enough to be useful (translation)
- **Checklists** for institutional tasks (`expected_elements` per task)
- **Refusal taxonomy** for constitutional prompts: refusal quality, safe redirection, proportionality, over-refusal, unsafe compliance
- **Automatic checks** only as smoke signals, not final scores

## Target models

European open-weight priority: Mistral, Silo/Poro, EuroLLM preview, limes-nanogpt checkpoints. Global baselines (Llama, Qwen) allowed for comparison with clear labeling.

## Roadmap

- [x] v0.2 task schema, runner, results format, and small examples
- [ ] FR/DE institutional shards
- [ ] Optional automated model adapters (HF transformers + vLLM)
- [ ] Public results table on GitHub Pages
- [ ] Tie scores to [model-card-template](https://github.com/Limes-Labs/model-card-template)
- [ ] Constitutional judge prompts linked to [limes-constitution](https://github.com/Limes-Labs/limes-constitution)

## Run (smoke)

```bash
python3 scripts/validate_tasks.py --tasks tasks/v0.2
python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl
python3 scripts/summarize_results.py results/smoke_run.jsonl
# with trained char model:
cd ../limes-nanogpt && python3 eval_perplexity.py --out_dir=out-european-char
```

Contribute tasks via PR. Join: https://limeslabs.eu/join

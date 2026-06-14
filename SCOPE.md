# EuroBench — Scope

> European language & institutional evaluation for open models. [Limes Labs](https://limeslabs.eu)

EuroBench is **not** a leaderboard chasing MMLU scores alone. It measures whether models serve **European public use**: multilingual competence, institutional literacy, rights-aware reasoning, honest citations, and constitutional alignment.

## v0.1 dimensions

| Dimension | Description | Status |
| --- | --- | --- |
| **Institutional QA** | PA, education, law — plain language | `tasks/v0.1/it_institutional.json` |
| **Translation** | EN↔IT/EU phrasing fidelity | included in IT set |
| **Constitutional** | Safety, honesty, refusal, sovereignty framing | `tasks/v0.1/constitutional.json` |
| **Perplexity smoke** | Char/small LM training sanity | `scripts/eval_stub.py`, limes-nanogpt `eval_perplexity.py` |

## Scoring philosophy (v0.1)

- **Rubric + human review** for generative tasks (no fake precision)
- **Reference answers** where objective (translation)
- **Checklists** for institutional tasks (see `evaluation_notes` per task)
- **Refusal taxonomy** for constitutional prompts: `refuse`, `redirect`, `comply_with_caveats`, `over_refuse`

## Target models

European open-weight priority: Mistral, Silo/Poro, EuroLLM preview, limes-nanogpt checkpoints. Global baselines (Llama, Qwen) allowed for comparison with clear labeling.

## Roadmap

- [ ] v0.2 FR/DE institutional shards
- [ ] Automated runner (HF transformers + vLLM)
- [ ] Public results table on GitHub Pages
- [ ] Tie scores to [model-card-template](https://github.com/Limes-Labs/model-card-template)
- [ ] Constitutional judge prompts linked to [limes-constitution](https://github.com/Limes-Labs/limes-constitution) v0.2

## Run (smoke)

```bash
python scripts/eval_stub.py
# with trained char model:
cd ../limes-nanogpt && python eval_perplexity.py --out_dir=out-european-char
```

Contribute tasks via PR. Join: https://limeslabs.eu/join
# Open Weight Models — Initial Tracker

> First entries for [Limes Labs](https://limeslabs.eu) open-weight-tracker. Evaluation pending via [eurobench](https://github.com/Limes-Labs/eurobench).

| Model | Org | License | Params | European language notes | EuroBench status |
| --- | --- | --- | --- | --- | --- |
| Mistral 7B / Mixtral | Mistral AI (FR) | Apache 2.0 | 7B–8x7B | Strong FR; used widely in EU | Planned |
| Llama 3.x | Meta | Llama license | 8B–70B+ | Multilingual; EU deployment common | Planned |
| Qwen 2.5 | Alibaba | Apache 2.0 / Qwen license | Various | Good multilingual incl. EU langs | Planned |
| Gemma 2 | Google | Gemma license | 2B–27B | Multilingual base | Planned |
| Poro 34B | Silo AI (FI) | Apache 2.0 | 34B | Finnish + English focus | Planned |
| Viking 7B | Viking Analytics (SE) | Apache 2.0 | 7B | Nordic languages | Planned |
| EuroLLM | EU project | Check repo | TBD | Explicitly European multilingual | Research |
| Occiglot | Occiglot consortium | Check repo | TBD | European languages initiative | Research |

## Tracking fields (schema v0.1)

```yaml
model_id: string
release_date: YYYY-MM-DD
license: string
languages_claimed: [iso codes]
eurobench_scores: optional
deployment_notes: string
limitations: string
source_url: url
```

## Next steps

- [ ] Verify licenses and current model versions
- [ ] Run first EuroBench v0.1 subset on 3–5 models
- [ ] Add European sovereign hosting notes (OVH, Scaleway, Hetzner, etc.)

Contributions welcome via PR or issue.
# EuroBench results format

The runner writes JSONL: one JSON object per task. Results are designed to be inspectable, diffable, and safe to publish with caveats.

## Smoke run

```bash
python3 scripts/run_eval.py --tasks tasks/v0.2 --backend dummy --output results/smoke_run.jsonl
python3 scripts/run_eval.py --tasks tasks/v0.3 --backend dummy --output results/smoke_v0.3_run.jsonl
python3 scripts/run_eval.py --tasks tasks/v0.4 --backend dummy --output results/smoke_v0.4_run.jsonl
```

The dummy backend validates task loading and result serialization. It is not a model evaluation.

## Run with model outputs

Prepare JSONL like this:

```json
{"task_id":"it-inst-001","model_id":"example-model","output":"Risposta del modello..."}
{"task_id":"it-trans-001","model_id":"example-model","output":"La traduzione del modello..."}
```

Then run:

```bash
python3 scripts/run_eval.py \
  --tasks tasks/v0.2 \
  --backend jsonl \
  --outputs examples/model_outputs/example_outputs.jsonl \
  --output results/example_run.jsonl
```

## Result object

| Field | Meaning |
| --- | --- |
| `run_id` | Timestamp-like run identifier unless provided with `--run-id`. |
| `suite_id` | Suite identifier from the task file. |
| `shard_id` | Source shard identifier. |
| `task_id` | Stable task ID. |
| `category` | Task category. |
| `task_type` | Task type. |
| `language` | Task language. |
| `difficulty_tags` | v0.3 challenge tags, empty for v0.2 rows. |
| `failure_modes` | v0.3 expected failure-mode tags, empty for v0.2 rows. |
| `expected_source_ids` | v0.3 source IDs expected for citation-sensitive answers. |
| `scoring` | v0.4 partial-credit scoring contract copied from the task. It is for human review, not automatic grading. |
| `model_id` | Model/source identifier from outputs, or `baseline-placeholder`. |
| `output` | Model output or placeholder text. |
| `output_sha256` | Hash of the output string. |
| `auto_checks` | Lightweight string checks. These are smoke signals, not final scores. |
| `suggested_review_label` | Runner suggestion such as `needs_human_review`, `partially_correct`, `over_refusal`, or `unsafe_compliance`. |
| `human_review_label` | Optional label supplied in the input JSONL after human review. |
| `review_notes` | Optional reviewer notes supplied in the input JSONL. |
| `limitations` | Per-result reminder that this is a small benchmark package. |

The only publishable score in the current public package is a transparent count of human labels plus examples. Do not turn these outputs into a broad leaderboard claim.

Create a descriptive summary with:

```bash
python3 scripts/summarize_results.py results/example_run.jsonl
```

For v0.3 rows, the summary also prints hard-mode failure-mode counts and difficulty-tag counts. These are diagnostic slices, not model rankings.

For v0.4 rows, the summary also prints scoring dimensions and total possible human-reviewed points. These numbers are the rubric capacity, not a model score.

## Result cards

v0.4 adds a result-card generator:

```bash
python3 scripts/generate_result_card.py results/smoke_v0.4_run.jsonl \
  --output results/smoke_v0.4_result_card.md \
  --status smoke \
  --contamination-assumption "Public v0.4 tasks are visible and may be contaminated."
```

The card includes:

- run status
- row count and model IDs
- review-label counts
- automatic-check counts
- expected failure modes
- scoring dimensions and total possible human-reviewed points
- caveats and contamination assumptions

If input rows do not contain human scores, the card explicitly marks the score as pending. Public result cards should distinguish public smoke runs from held-out reviewed runs.

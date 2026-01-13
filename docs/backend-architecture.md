# Backend Architecture

## High-level view

```
Client -> FastAPI -> Postgres
                 -> MinIO (uploads)
                 -> Redis (Celery broker/result)
                          |
                          v
                      Celery worker
                          |
                          v
                      process_review()
```

## Review lifecycle

State machine:

```
CREATED -> UPLOADED -> PROCESSING -> COMPLETED
                              \-> FAILED
```

Transitions are enforced by a shared guard (`assert_transition`). `/start` is valid only from `UPLOADED`.

## Pipeline order

1) extraction
2) segmentation
3) classification (rules-first, LLM fallback)
4) evaluation (LLM)
5) evidence validation (deterministic substring match)
6) executive summary heuristic
7) persist artifacts

## Deterministic vs LLM

Deterministic:
- segmentation
- rules-based classification
- evidence validation
- executive summary heuristic

LLM (behind flags):
- classification fallback
- clause evaluation (strict JSON + safe fallback)

## Data model summary

- `reviews`: lifecycle status, doc metadata, job tracking, decision + summary_json
- `review_segments`: persisted segment text + metadata
- `segment_classifications`: clause labels + confidence per segment
- `clause_evaluations`: per-clause risk + evidence spans

## Idempotency

- Segment classifications and clause evaluations are replaced per run (delete-then-insert).
- Reruns do not duplicate rows.

## Failure handling

- Unhandled exceptions set review to `FAILED` and store `error_message`.
- LLM failures fall back to safe outputs (YELLOW with manual review guidance).

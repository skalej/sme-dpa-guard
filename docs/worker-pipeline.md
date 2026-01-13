# Worker Pipeline

Entry point: Celery task `reviews.process_review` -> `process_review(review_id)`.

## Stages

1) Load review + storage key
2) Fetch bytes from MinIO
3) Extract text (PDF/DOCX)
4) Segment text (deterministic rules)
5) Persist segments
6) Classify segments (rules-first; LLM fallback)
7) Evaluate per ClauseType (LLM)
8) Validate evidence spans (exact substring)
9) Persist clause evaluations
10) Build executive summary and decision
11) Mark review COMPLETED

## Failure behavior
- Any exception sets `FAILED` and stores `error_message`.
- LLM failures return safe fallback results; processing continues.

## Idempotency
- Segment classifications and clause evaluations are deleted then reinserted on each run.
- Summary is recomputed each run.

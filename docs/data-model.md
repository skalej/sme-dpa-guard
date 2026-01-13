# Data Model

## reviews
- id (UUID, PK)
- status (enum: CREATED, UPLOADED, PROCESSING, COMPLETED, FAILED)
- context_json (JSONB, nullable)
- doc_filename, doc_mime, doc_size_bytes, doc_sha256, doc_storage_key
- error_message (text, nullable)
- job_id, job_status (nullable)
- decision (text, nullable)
- summary_json (JSONB, nullable)
- created_at, updated_at (timestamptz)

## review_segments
- id (int, PK)
- review_id (UUID, FK)
- segment_index (int, unique per review)
- heading, section_number (nullable)
- text (text)
- hash (md5)
- page_start, page_end (nullable)

## segment_classifications
- id (int, PK)
- review_id (UUID, FK)
- segment_id (int, FK)
- clause_type (enum)
- confidence (float)
- method (RULES or LLM)

## clause_evaluations
- id (int, PK)
- review_id (UUID, FK)
- clause_type (enum)
- risk_label (enum: GREEN, YELLOW, RED)
- short_reason (text)
- suggested_change (text)
- triggered_rule_ids (JSONB list)
- evidence_spans (JSONB list)
- created_at, updated_at (timestamptz)

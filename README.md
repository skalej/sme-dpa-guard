# DPA Guard

## Overview
DPA Guard is a monorepo that evaluates DPA contracts through a deterministic pipeline (extraction, segmentation, classification, evaluation, evidence validation, summary). It stores structured artifacts in Postgres, uploaded documents in MinIO, and runs background processing with Celery + Redis.

## Local dev prerequisites
- Docker Desktop (or Docker Engine)
- Python 3.12+ (for local backend runs)

## Environment variables (keys only)
- DATABASE_URL
- REDIS_URL
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND
- MINIO_ENDPOINT (not wired; use `S3_ENDPOINT` today)
- MINIO_ACCESS_KEY (not wired; use `S3_ACCESS_KEY` today)
- MINIO_SECRET_KEY (not wired; use `S3_SECRET_KEY` today)
- S3_ENDPOINT
- S3_ACCESS_KEY
- S3_SECRET_KEY
- S3_BUCKET
- S3_REGION
- S3_SECURE
- OPENAI_API_KEY
- OPENAI_MODEL
- OPENAI_MODEL_CLASSIFY (not wired; uses `OPENAI_MODEL` today)
- USE_LLM_EVAL
- USE_LLM_CLASSIFICATION
- CLASSIFY_RULES_MIN_CONF
- CLASSIFY_TOP_K
- PLAYBOOK_YAML_PATH
- LLM_TEMPERATURE
- LLM_MAX_INPUT_CHARS

## Run locally

Option A: run infra in Docker, run API + worker locally

```
docker compose up -d postgres redis minio minio-init
```

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```
cd backend
celery -A app.celery_app.celery_app worker --loglevel=info
```

Option B: run everything in Docker

```
docker compose up -d backend worker
```

## Migrations

Local Python:

```
cd backend
alembic upgrade head
```

Docker:

```
docker compose exec backend alembic upgrade head
```

## End-to-end workflow (curl)

```
RID=$(curl -s -X POST http://localhost:8000/reviews | jq -r .review_id)
curl -s -X POST "http://localhost:8000/reviews/$RID/upload" \
  -F "file=@docs/sample_dpa_small.pdf;type=application/pdf" | jq .
curl -s -X POST "http://localhost:8000/reviews/$RID/start" | jq .
curl -s "http://localhost:8000/reviews/$RID/job" | jq .
curl -s "http://localhost:8000/reviews/$RID/results" | jq .
```

## API endpoints
- POST `/reviews`
- GET `/reviews/{id}`
- POST `/reviews/{id}/upload`
- POST `/reviews/{id}/start`
- GET `/reviews/{id}/job`
- GET `/reviews/{id}/results`
- GET `/reviews/{id}/explain`
- GET `/health/live`
- GET `/health/ready`

## Frontend
Placeholder. The frontend will live in `frontend/`.

## Local dev infra
- Start: `docker compose up -d`
- Status: `docker compose ps`
- MinIO logs: `docker compose logs -f minio`
- MinIO console: `http://localhost:9001`
- Stop (remove volumes): `docker compose down -v`

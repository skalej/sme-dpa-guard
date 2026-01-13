# Operational Runbook

## On-call quickstart

- Check status: `docker compose ps`
- Tail logs: `docker compose logs -f backend worker`
- Verify health:
  - `curl -s http://localhost:8000/health/live`
  - `curl -s http://localhost:8000/health/ready`
- Check a job:
  - `curl -s http://localhost:8000/reviews/{id}/job`
  - `curl -s http://localhost:8000/reviews/{id}/results`

## Start services

Infra only:
```
docker compose up -d postgres redis minio minio-init
```

Full stack:
```
docker compose up -d backend worker
```

## Migrations
```
docker compose exec backend alembic upgrade head
```

## Common issues

- Redis connection errors:
  - Ensure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` point to `redis://redis:6379/0` inside Docker.
  - Restart backend/worker after Redis restarts.

- MinIO not responding:
  - `docker compose logs -f minio`
  - Verify health: `curl http://localhost:9000/minio/health/live`

- Job stuck in PROCESSING:
  - Check worker logs: `docker compose logs -f worker`
  - Confirm Redis connectivity from backend:
    - `docker compose exec backend python -c "import redis; r=redis.Redis(host='redis', port=6379, db=0); print(r.ping())"`
  - If Redis was restarted, restart backend + worker:
    - `docker compose restart backend worker`

## Escalation checklist

- Confirm DB is healthy: `docker compose ps` (postgres healthy)
- Confirm Redis is healthy: `docker compose ps` (redis healthy)
- Confirm MinIO is healthy: `docker compose ps` (minio healthy)
- Capture logs and timestamps before restart

## Cleanup
```
docker compose down -v
```

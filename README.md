# DPA Guard

Monorepo with separate backend and frontend codebases.

## Backend

Setup

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run

```
uvicorn app.main:app --reload --port 8000
```

Test

```
pytest -q
```

## Frontend

Placeholder. The frontend will live in `frontend/`.

## Local dev infra

Start dependencies

```
docker compose up -d
```

Check status

```
docker compose ps
```

Follow MinIO logs

```
docker compose logs -f minio
```

MinIO console

Open http://localhost:9001

Stop and remove volumes

```
docker compose down -v
```

## Docker (backend)

Run backend in Docker (dev)

```
docker compose up -d backend
```

Run backend in Docker (prod profile)

```
docker compose --profile prod up -d backend-prod
```

Stop containers

```
docker compose down
```

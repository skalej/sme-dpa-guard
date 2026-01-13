# Backend

FastAPI service for DPA Guard.

## Setup

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```
uvicorn app.main:app --reload --port 8000
```

## Test

```
pytest -q
```

## Configuration

Copy the example env file and update values as needed.

```
cp .env.example .env
```

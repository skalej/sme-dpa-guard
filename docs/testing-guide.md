# Testing Guide

## Unit + integration tests
```
cd backend
pytest -q
```

## Docker-based tests
```
docker compose exec backend pytest -q
```

## End-to-end flow
```
RID=$(curl -s -X POST http://localhost:8000/reviews | jq -r .review_id)
curl -s -X POST "http://localhost:8000/reviews/$RID/upload" \
  -F "file=@docs/sample_dpa_small.pdf;type=application/pdf" | jq .
curl -s -X POST "http://localhost:8000/reviews/$RID/start" | jq .
curl -s "http://localhost:8000/reviews/$RID/job" | jq .
curl -s "http://localhost:8000/reviews/$RID/results" | jq .
```

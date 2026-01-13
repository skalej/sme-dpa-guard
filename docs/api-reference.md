# API Reference

Base URL: http://localhost:8000

## Health

- GET `/health/live`
  - 200 `{ "status": "ok" }`
- GET `/health/ready`
  - 200 `{ "status": "ok" }` or 503 `{ "status": "not_ready" }`

## Reviews

- POST `/reviews`
  - Body (optional): `{ "context_json": { ... } }`
  - 201 response: `ReviewOut`

- GET `/reviews/{id}`
  - 200 response: `ReviewOut`

- POST `/reviews/{id}/upload`
  - multipart form field: `file`
  - 200 response: `ReviewUploadOut`
  - Errors: 404, 409 (wrong status), 415 (unsupported type)

- POST `/reviews/{id}/start`
  - 200 response:
    ```json
    {"message":"Processing started","review_id":"...","status":"PROCESSING","job_id":"..."}
    ```
  - Errors: 404, 400 (not ready)

- GET `/reviews/{id}/job`
  - 200 response:
    ```json
    {"review_id":"...","job_id":"...","state":"PENDING","ready":false,"successful":null}
    ```

- GET `/reviews/{id}/results`
- GET `/reviews/{id}/explain`
  - 200 response: `ReviewExplainOut`

## Schema Notes

- `ReviewOut` includes `review_id`, `status`, `created_at`, `updated_at`, optional `context_json`, optional `doc`.
- `ReviewUploadOut` includes `review_id`, `status`, `doc` metadata.
- `ReviewExplainOut` includes `review_id`, `status`, `playbook_version`, `decision`, `summary`, `evaluations`.

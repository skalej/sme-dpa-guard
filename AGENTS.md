# AGENTS.md

This repository uses Codex for incremental, test-backed changes. Follow the guidance below when implementing DPA Guard.

## Repo layout
- Monorepo structure
  - backend/ (FastAPI Python)
  - frontend/ (Vite React)

## Commands (backend)
- Set up env
  - cd backend
  - python -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt
- Run
  - uvicorn app.main:app --reload --port 8000
- Test
  - pytest -q

## DPA Guard core rules
- Review lifecycle statuses: CREATED -> UPLOADED -> PROCESSING -> COMPLETED/FAILED
- Enforce transitions in one shared guard function (deterministic).
- Pipeline order must be: extraction -> segmentation -> classification -> evaluation -> evidence validation -> exec summary -> persist artifacts
- Deterministic logic for segmentation, confidence scoring, evidence validation, scanned detection
- LLM only allowed behind config flags for classification fallback and clause evaluation
- LLM outputs must be strict JSON, strip fences, safe fallback on parse failure
- No RAG unless later explicitly requested

## Task discipline
- Implement in small tasks, one PR per task
- Prefer refactors over rewrites
- Always add/adjust tests when adding behavior
- Keep endpoints stable unless a task says otherwise

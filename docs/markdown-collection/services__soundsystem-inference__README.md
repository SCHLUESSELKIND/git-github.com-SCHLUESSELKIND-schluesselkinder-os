# SNUFFRAGA SOUNDSYSTEM Inference

Internal FastAPI scaffold for AI music generation workflows.

This service currently includes:

- health endpoint
- capabilities endpoint
- modular prompt compiler
- in-memory generation job scaffold
- provider registry with mock fallback
- two-call provider contract: `start()` and `get_status()`
- initial Postgres schema artifact

It does not call ACE-Step, YuE, Stable Audio Open, OpenAI, Anthropic, Dropbox, Supabase, or RunPod yet.

## Local Run

```bash
cd services/soundsystem-inference
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

## Routes

- `GET /health`
- `GET /v1/capabilities`
- `POST /v1/prompts/compile`
- `POST /v1/generations`
- `GET /v1/generations/{job_id}`

## Tests

The service ships with a small pytest suite that covers prompt compilation,
job creation, the voice-likeness preflight block, and 404 lookup behavior.

```bash
cd services/soundsystem-inference
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Tests use the in-memory `InMemoryGenerationJobRepository` and do not require a
database, Redis, Dropbox, Supabase, RunPod, or any GPU model.

## Providers

`app/providers/base.py` defines the `MusicEngineProvider` contract. Providers
start jobs with `start()` and report progress through `get_status()`, matching
the async shape expected for ACE-Step, YuE, and Stable Audio Open later.

`app/providers/registry.py` owns provider registration, default selection,
health checks, and mock fallback. The only registered provider today is
`MockMusicProvider`; no live external provider calls are made.

## Persistence

`app/repository.py` defines `GenerationJobRepository`, the storage boundary for
generation jobs and their events. The default implementation is
`InMemoryGenerationJobRepository`. The Postgres-backed implementation lands
later against the SQL artifact in `db/001_initial_schema.sql`.

## Design Boundary

This service owns GPU-facing work only. It should remain internal-only and should not approve release candidates.

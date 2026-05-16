# API Architecture

## Public Surface

This service is internal-only. It should run behind VPN, Tailscale, Cloudflare Access, or Hetzner firewall rules. No public unauthenticated route should trigger generation.

## FastAPI Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/health` | `GET` | Liveness and version |
| `/v1/capabilities` | `GET` | Available engines, actions, prompt modules |
| `/v1/prompts/compile` | `POST` | Compile modular prompt JSON into engine prompts |
| `/v1/generations` | `POST` | Validate request, create job, enqueue generation |
| `/v1/generations/{job_id}` | `GET` | Return generation status and artifact manifest |
| `/v1/generations/{job_id}/cancel` | `POST` | Future queue cancel |
| `/v1/projects/{project_id}/exports/dropbox` | `POST` | Future Dropbox export trigger |
| `/v1/safety/preflight` | `POST` | Future prompt/reference safety check |
| `/v1/safety/analyze-audio` | `POST` | Future audio similarity job |

## Generation Request Shape

```json
{
  "project_id": "snuffraga-warehouse-001",
  "intent": "CREATE_TRACK",
  "engine": "ACE_STEP",
  "prompt_modules": {
    "energy": "warehouse",
    "bass_pressure": "crushing",
    "vocals": "haunting",
    "atmosphere": "black_concrete",
    "structure": "instant_drop"
  },
  "character_code": "SHIBARI_KAWAII",
  "lyrics": "[Hook]\nNo exit in the pressure...",
  "technical": {
    "bpm": 142,
    "key": "F minor",
    "duration_seconds": 180,
    "seed": 1887,
    "stems_required": true
  },
  "safety": {
    "allow_reference_audio": false,
    "allow_voice_likeness": false,
    "release_candidate": false
  }
}
```

## Job State Machine

```text
DRAFT
  -> PREFLIGHT_BLOCKED
  -> QUEUED
  -> RUNNING
  -> RENDERING_STEMS
  -> ANALYZING_SAFETY
  -> EXPORT_READY
  -> EXPORTED
  -> FAILED
  -> CANCELLED
```

No generated item becomes releasable from this state machine. Release approval remains a separate human review workflow.

## Adapter Contract

Every model adapter should implement:

```python
class MusicEngineProvider(Protocol):
    name: str

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        ...
```

The adapter returns files and metadata, not UI decisions.

## Events

Progress events should be persisted and streamed:

- `job.created`
- `prompt.compiled`
- `preflight.passed`
- `worker.assigned`
- `engine.loaded`
- `generation.started`
- `generation.progress`
- `stems.started`
- `safety.started`
- `artifact.ready`
- `dropbox.exported`
- `job.failed`

MVP can poll. Later UI should use Server-Sent Events or Supabase Realtime for status display.

## Security

- Require internal auth before generation.
- Reject prompts that request protected artist imitation, unauthorized vocal likeness, or known commercial song cloning.
- Redact tokens and file paths from logs.
- Store source hashes, not raw external reference material, unless explicitly cleared.
- Keep OpenAI, Anthropic, Dropbox, Supabase, and RunPod keys outside Git.

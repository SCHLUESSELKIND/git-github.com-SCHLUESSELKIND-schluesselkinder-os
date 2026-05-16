# SNUFFRAGA SOUNDSYSTEM AI ENGINE

Internal architecture pack for the stem-first AI music operating system.

This system is not a public song app and not a one-click generator. It is an internal production console for controlled, editable, copyright-audited music experiments under the SCHLUESSELKINDER creative system.

## Core Decision

Use a two-service architecture:

- `apps/web`: internal cinematic console, prompt builder, waveform workspace, stem browser, character system, review surfaces.
- `services/soundsystem-inference`: Python FastAPI inference layer that owns GPU model adapters, queue execution, stem packaging, audio analysis, and safety checks.

The existing `services/api` Fastify service remains the SCHLUESSELKINDER archive and governance API. It should orchestrate metadata and review state later, but it should not host GPU inference.

## Documents

- [Research Notes](./research.md)
- [System Architecture](./architecture.md)
- [SNUFFRAGA SOUNDGRAPH Model](./sound-model.md)
- [API Architecture](./api-architecture.md)
- [Database Schema](./database-schema.md)
- [Generation Pipeline](./generation-pipeline.md)
- [Prompt Engine](./prompt-engine.md)
- [Copyright Safety Layer](./copyright-safety.md)
- [UI Wireframes](./ui-wireframes.md)
- [Operator Console](./operator-console.md)
- [Claude Code Handoff](./claude-code-handoff.md)
- [Roadmap and Deployment](./roadmap-deployment.md)
- [Execution Order](./execution-order.md)

## Implementation Artifacts

- [FastAPI service scaffold](/Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference/README.md)
- [Initial Postgres schema](/Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference/db/001_initial_schema.sql)
- [ADR 0005](/Users/thomasfrerich/schluesselkinder-os/docs/adr/0005-internal-ai-music-engine.md)

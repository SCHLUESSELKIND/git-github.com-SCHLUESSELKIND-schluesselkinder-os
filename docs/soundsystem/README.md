# SNUFFRAGA SOUNDSYSTEM AI ENGINE

Internal architecture pack for the stem-first AI music operating system.

This system is not a public song app and not a one-click generator. It is an internal production console for controlled, editable, copyright-audited music experiments under the SCHLUESSELKINDER creative system.

## Core Decision

Use a two-service architecture:

- `apps/web`: internal cinematic console, prompt builder, waveform workspace, stem browser, character system, review surfaces.
- `services/soundsystem-inference`: Python FastAPI inference layer that owns GPU model adapters, queue execution, stem packaging, audio analysis, and safety checks.

The existing `services/api` Fastify service remains the SCHLUESSELKINDER archive and governance API. It should orchestrate metadata and review state later, but it should not host GPU inference.

## Documents

### Strategy & Compliance (binding)

- [Operator Interface Principles](./operator-interface-principles.md) — intent-first UI; no raw model names in the operator console
- [Admin Integration Strategy](./admin-integration-strategy.md) — how `schluesselkinder.de/admin` hosts the operator OS
- [Model Provider Strategy](./model-provider-strategy.md) — provider groups, intent-to-provider mapping, adapter pattern
- [Compliance Foundation](./compliance-foundation.md) — preflight ordering, license, consent, provenance, release gates
- [Roadmap](./roadmap.md) — slice sequence

### Architecture

- [Research Notes](./research.md)
- [System Architecture](./architecture.md)
- [SNUFFRAGA SOUNDGRAPH Model](./sound-model.md)
- [API Architecture](./api-architecture.md)
- [Database Schema](./database-schema.md)
- [Generation Pipeline](./generation-pipeline.md)
- [Prompt Engine](./prompt-engine.md)
- [Lyrics Engine](./lyrics-engine.md)
- [Copyright Safety Layer](./copyright-safety.md) — superseded by [Compliance Foundation](./compliance-foundation.md) for the data model
- [Master Bus](./master-bus.md)
- [UI Wireframes](./ui-wireframes.md)
- [Operator Console](./operator-console.md)
- [Claude Code Handoff](./claude-code-handoff.md)
- [Roadmap and Deployment](./roadmap-deployment.md)
- [Execution Order](./execution-order.md) — superseded by [Roadmap](./roadmap.md) where they disagree

## Implementation Artifacts

- [FastAPI service scaffold](/Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference/README.md)
- [Initial Postgres schema](/Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference/db/001_initial_schema.sql)
- [ADR 0005](/Users/thomasfrerich/schluesselkinder-os/docs/adr/0005-internal-ai-music-engine.md)

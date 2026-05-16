# ADR 0005: Internal AI Music Engine Boundary

## Status

Proposed and scaffolded.

## Context

SNUFFRAGA SOUNDSYSTEM AI ENGINE introduces GPU inference, AI music generation, stems, prompt intelligence, audio similarity analysis, Dropbox exports, and model-specific Python dependencies. These concerns are materially different from the existing SCHLUESSELKINDER archive and public site surfaces.

The existing repo is a TypeScript monorepo with Next.js, Fastify, Prisma, and governance-first archive data. GPU inference is Python-first and should not be coupled to public rendering, commerce, or release approval.

## Decision

Add the AI music system as an internal, additive boundary:

- Keep orchestration and public/archive metadata out of GPU workers.
- Add `services/soundsystem-inference` as a Python FastAPI service for generation jobs and model adapters.
- Keep database design in an explicit SQL schema artifact before modifying the existing Prisma schema.
- Keep Dropbox as export storage, not source of truth.
- Keep release approval outside the inference service.

## Consequences

- The existing Fastify API remains stable.
- Python ML dependencies do not pollute the TypeScript packages.
- The internal AI engine can evolve toward local GPU and RunPod workers.
- Safety and provenance can be audited before generated material enters release workflows.
- A later ADR should decide whether soundsystem metadata lives in Supabase only, the existing Prisma package, or a dedicated Prisma schema.

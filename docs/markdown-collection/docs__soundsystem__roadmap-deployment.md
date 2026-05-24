# Roadmap And Deployment

## MVP Roadmap

### Phase 0: Architecture And Guardrails

- Create architecture docs.
- Create FastAPI scaffold.
- Create SQL schema artifact.
- Define prompt modules and generation job contract.
- Add no-live-provider mock path.

### Phase 1: Local Inference Loop

- Install ACE-Step locally on GPU host.
- Add ACE-Step adapter to FastAPI.
- Implement queue with Redis/RQ or Celery.
- Create prompt compile route.
- Store generation job metadata.
- Save full mix and prompt JSON locally.

### Phase 2: Stem Workflow

- Add source separation.
- Create artifact manifest.
- Add stem confidence metadata.
- Add waveform data extraction.
- Add internal UI for generation status and stem preview.

### Phase 3: Safety Layer

- Add prompt preflight.
- Add Chromaprint/fpcalc.
- Add CLAP embedding extraction.
- Add melody contour checks.
- Add similarity report UI.

### Phase 4: Dropbox Export

- Implement OAuth offline flow.
- Add export packaging.
- Upload full mix, stems, prompt JSON, metadata JSON, safety report.
- Store Dropbox paths in Postgres.

### Phase 5: YuE And Stable Audio Open

- Add YuE RunPod worker path.
- Add Stable Audio Open FX adapter.
- Add engine routing by action.
- Add cost and runtime estimates.

### Phase 6: Style DNA

- Add training dataset registry.
- Add ACE-Step LoRA/LoKr training job records.
- Add adapter versioning.
- Block adapter use without provenance.

## Deployment Plan

### Local Development

- Mac/desktop runs web and API.
- GPU workstation runs `services/soundsystem-inference`.
- Postgres can be Supabase cloud or local Docker.
- Redis runs locally for queue.
- Artifacts first write to local volume.

### Hetzner

Use Hetzner for non-GPU persistent services:

- Next.js internal console
- Fastify API
- Postgres if self-hosting instead of Supabase
- Redis
- reverse proxy
- monitoring

Do not deploy GPU inference to a CPU Hetzner box. Use local GPU or RunPod workers.

### RunPod

Use RunPod for:

- YuE long-form jobs
- large GPU experiments
- parallel batch generations
- adapter training bursts

Pattern:

1. Build GPU container.
2. Mount temporary RunPod volume.
3. Pull model weights into model cache.
4. Pull job payload from orchestrator.
5. Upload artifacts to Dropbox/Supabase metadata.
6. Shut down worker.

### Docker Compose

MVP compose services:

- `web`
- `api`
- `soundsystem-inference`
- `postgres`
- `redis`

GPU compose is separate because CUDA base images and NVIDIA runtime should not be forced on every developer machine.

## Monitoring

Track:

- job queue time
- generation runtime
- GPU memory
- model load time
- failed jobs by engine
- blocked prompts by reason
- similarity risk distribution
- Dropbox export latency
- cost per generated minute

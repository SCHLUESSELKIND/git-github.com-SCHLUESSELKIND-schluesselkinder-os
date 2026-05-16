# Implementation Steps In Execution Order

## Immediate

1. Keep this as an internal-only feature boundary.
2. Land the FastAPI scaffold and SQL schema artifact.
3. Add local env names without secrets.
4. Run syntax and TypeScript checks.

## Next Sprint

1. Add Redis queue and persistent job repository.
2. Add ACE-Step adapter against a local ACE-Step REST server.
3. Persist prompt versions, jobs, events, and artifacts.
4. Add local artifact folder packaging.
5. Build a minimal internal `/admin/soundsystem` console with action rail, prompt modules, and job status.

## After Local Loop Works

1. Add source separation and waveform extraction.
2. Add Chromaprint/fpcalc fingerprinting.
3. Add CLAP embeddings.
4. Add safety report UI.
5. Add Dropbox OAuth and export packaging.

## After Safety Works

1. Add Stable Audio Open FX adapter.
2. Add YuE worker path.
3. Add RunPod job launcher.
4. Add style DNA profiles.
5. Add LoRA/LoKr training dataset registry and adapter versioning.

## Do Not Start Yet

- public release automation
- social posting
- commercial distribution claims
- voice likeness features
- marketplace features
- live Stripe/Printful dependencies
- training on third-party artist catalogs

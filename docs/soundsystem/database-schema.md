# Database Schema

The first schema artifact is [001_initial_schema.sql](/Users/thomasfrerich/schluesselkinder-os/services/soundsystem-inference/db/001_initial_schema.sql).

## Database Choice

Use Supabase Postgres for canonical metadata and safety records.

Do not store large WAV stems in Postgres. Store file manifests, content hashes, Dropbox paths, local scratch paths, and object metadata.

## Core Tables

| Table | Purpose |
| --- | --- |
| `soundsystem_projects` | Creative container for track/riddim/remix work |
| `soundsystem_characters` | Artist/voice/world identity settings |
| `soundsystem_style_dna_profiles` | Style DNA profiles and adapter provenance |
| `soundsystem_prompt_modules` | Controlled vocabulary for energy, bass pressure, vocals, atmosphere, structure |
| `soundsystem_prompt_versions` | Immutable compiled prompt records |
| `soundsystem_generation_jobs` | Async generation job state |
| `soundsystem_generation_events` | Append-only job timeline |
| `soundsystem_artifacts` | Full mix, stems, lyrics, cover, metadata, prompt JSON |
| `soundsystem_audio_embeddings` | CLAP/MERT or future embedding rows |
| `soundsystem_similarity_checks` | Fingerprint, embedding, melody, and policy outcomes |
| `soundsystem_training_datasets` | LoRA/LoKr source dataset provenance |
| `soundsystem_training_items` | Owned/licensed source item hashes and rights notes |
| `soundsystem_adapter_versions` | Trained adapter metadata and file references |
| `soundsystem_dropbox_exports` | Dropbox paths and export audit state |

## Important Constraints

- Prompt versions are immutable after generation starts.
- Safety checks are append-only.
- Adapter training data requires a rights basis.
- A generation job can be `EXPORT_READY`; it cannot be `APPROVED_FOR_RELEASE`.
- Release approval stays outside the inference service.

## Vector Strategy

Use pgvector columns where available:

- CLAP audio embedding: variable by selected checkpoint.
- MERT embedding: common pooled layer vector, configured per extractor version.
- Store `embedding_model`, `embedding_dimension`, and `extractor_version` with every vector so migrations can support multiple embedding shapes.

If Supabase vector dimensions need strict columns per model, use separate tables or nullable model-specific vector columns rather than a single generic vector column.

## Retention

- Keep final artifacts and manifests permanently unless manually archived.
- Keep scratch paths and intermediate renders for 14-30 days.
- Keep failed generation metadata, prompts, seeds, and logs for debugging, but remove large failed audio unless flagged.

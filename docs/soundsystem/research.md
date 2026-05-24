# Research Notes

## Engine Roles

| Engine | Best role | Strength | Constraint | Architecture decision |
| --- | --- | --- | --- | --- |
| ACE-Step 1.5 | Primary track, riddim, cover, repaint, lego stem generation | Fast local generation, editing tasks, LoRA/LoKr personalization, consumer GPU viability | Still needs originality review and stem separation/export pipeline around it | Default engine for CREATE TRACK, BUILD RIDDIM, STEM REMIX, CHARACTER VOICE, COVER GENERATION |
| YuE | Long-form lyrics-to-song, vocal song drafts, extended structure | Lyrics-to-song model with multi-minute structure and vocal alignment | Slow on RTX 4090; full songs need 80 GB class GPU or multiple GPUs for comfort | Use as premium long-form path, not the default iteration loop |
| Stable Audio Open | FX, dub atmospheres, risers, hits, texture beds | Short stereo text-to-audio, useful for sound design and ambience | Up to 47s, weak realistic vocals, license review needed for commercial use | Use only for DUB FX LAB and atmosphere preset rendering |

Sources: [ACE-Step 1.5 paper](https://arxiv.org/abs/2602.00744), [ACE-Step repository](https://github.com/ace-step/ACE-Step-1.5), [YuE paper](https://arxiv.org/abs/2503.08638), [YuE repository](https://github.com/multimodal-art-projection/YuE), [Stable Audio Open model card](https://huggingface.co/stabilityai/stable-audio-open-1.0), [Stable Audio Open paper](https://arxiv.org/abs/2407.14358).

## ACE-Step Integration

ACE-Step exposes a local REST workflow:

1. `POST /release_task` creates an async generation task.
2. `POST /query_result` polls task status.
3. `GET /v1/audio?path=...` downloads generated files.

Relevant controls:

- `task_type`: `text2music`, `cover`, `repaint`, `lego`, `extract`, `complete`.
- `prompt` / `lyrics` / `vocal_language`.
- `bpm`, `key_scale`, `time_signature`, `audio_duration`.
- `reference_audio_path`, `src_audio_path`, uploaded `reference_audio`, uploaded `src_audio`.
- `thinking`, LM configuration, model selection, seed, batch size, diffusion steps.

ACE-Step also documents LoRA and LoKr training. The product should treat adapters as internal style DNA assets with strict provenance: only owned material, licensed material, or deliberately commissioned internal recordings.

Sources: [ACE-Step API docs](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md), [ACE-Step inference docs](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md), [ACE-Step LoRA tutorial](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/LoRA_Training_Tutorial.md).

## YuE Integration

YuE is slower but structurally valuable. Its own docs report heavy memory requirements: 24 GB GPUs can run limited sessions, while full songs are more comfortable on 80 GB class GPUs or multi-4090 tensor parallel setups. It is appropriate for long-form lyric/vocal drafts, but not for the core fast iteration loop.

Use it behind the same generation job abstraction:

- `engine=YUE`
- `intent=CREATE_VOCALS` or `GENERATE_HOOK`
- `lyrics_body`, `genre_prompt`, `segment_plan`
- optional owned or cleared reference audio only

Source: [YuE repository hardware notes](https://github.com/multimodal-art-projection/YuE).

## Local GPU vs RunPod

Default position:

- Local RTX 4090 is best for daily iteration, private prompts, and adapter training.
- RunPod is best for burst capacity, YuE full-song sessions, A100/H100 experiments, and isolated model upgrades.
- Do not treat RunPod storage as canonical. RunPod states storage supports active compute workloads and should not be used for long-term critical data.

Economics:

- Use cloud if usage is sporadic, below roughly 80-120 GPU hours/month, or requires 80 GB GPUs.
- Use local if generation becomes daily production, adapter training is frequent, or project privacy matters more than zero-capex cloud.
- A local 4090 break-even should be calculated against real workstation cost, electricity, cooling, and repair risk. At roughly 200+ productive GPU hours/month, local begins to make operational sense even before privacy benefits.

Sources: [RunPod pricing](https://www.runpod.io/pricing), [RunPod billing and storage notes](https://docs.runpod.io/accounts-billing/billing).

## FastAPI vs Node Backend

Use both, with clear ownership:

- FastAPI: GPU model adapters, audio processing, queue workers, analysis jobs, stem packaging.
- Fastify/Node: brand archive, review workflow, public site/admin metadata, business logic already present in this repo.

Python wins for inference because the ML ecosystem is Python-first: PyTorch, Transformers, diffusers, torchaudio, librosa, demucs/audio-separator, CLAP, MERT, and model repos. Node remains the right web/API coordination layer for the existing SCHLUESSELKINDER OS.

## Supabase vs Firebase

Choose Supabase for the AI engine metadata layer.

Reasons:

- The system needs relational generation history, prompt versions, adapter provenance, human review, and copyright evidence.
- Supabase is Postgres, and Postgres supports pgvector for embeddings.
- Audio safety requires structured SQL joins and audit trails more than mobile-first client synchronization.

Firebase is strong for realtime client sync and app speed, but its document-store model is a weaker fit for provenance-heavy music workflows. Firebase itself positions Firestore and Realtime Database as NoSQL databases.

Sources: [Supabase database docs](https://supabase.com/docs/guides/database/overview), [Supabase AI and vectors docs](https://supabase.com/docs/guides/ai), [Firebase database comparison](https://firebase.google.com/docs/database/rtdb-vs-firestore).

## Similarity And Copyright Safety

Use a layered safety score:

- Exact/near-exact recording check: Chromaprint/fpcalc fingerprint against internal reference corpus and optionally AcoustID-compatible fingerprints.
- Semantic audio similarity: CLAP audio embeddings for text-audio and atmosphere/style comparison.
- Music understanding similarity: MERT embeddings for music structure/timbre/genre neighborhood analysis. Note: MERT-v1-330M is CC-BY-NC-4.0, so commercial release workflows must check license constraints before relying on it in production.
- Melody similarity: extract dominant melody or vocal line, convert to pitch contour/chroma features, compare with dynamic time warping and segment-level thresholds.
- Manual review: any flagged result requires producer approval before export to release candidates.

Sources: [Chromaprint](https://acoustid.org/chromaprint), [LAION CLAP](https://github.com/LAION-AI/CLAP), [MERT-v1-330M model card](https://huggingface.co/m-a-p/MERT-v1-330M).

## Dropbox Architecture

Dropbox should be the collaborative export vault, not the source of truth.

Use Supabase/Postgres for metadata and Dropbox for files:

- `/SNUFFRAGA/YYYY/MM/project-slug/generation-id/full_mix.wav`
- `/SNUFFRAGA/YYYY/MM/project-slug/generation-id/stems/*.wav`
- `/SNUFFRAGA/YYYY/MM/project-slug/generation-id/prompt.json`
- `/SNUFFRAGA/YYYY/MM/project-slug/generation-id/metadata.json`
- `/SNUFFRAGA/YYYY/MM/project-slug/generation-id/safety_report.json`

Use OAuth offline access with refresh tokens stored in a secret vault or encrypted server-side store. Dropbox docs require `token_access_type=offline` to receive refresh tokens.

Sources: [Dropbox OAuth guide](https://developers.dropbox.com/oauth-guide), [Dropbox offline access guide](https://dropbox.tech/developers/using-oauth-2-0-with-offline-access).

## Legal And Product Boundary

The safety layer is not legal advice. It is an engineering control system:

- Keep all model outputs internal until reviewed.
- Store prompts, seeds, engine versions, adapter versions, source file hashes, and safety scores.
- Do not train adapters on unauthorized artists, vocals, masters, or songs.
- Avoid prompts asking for living artists, specific commercial tracks, or unauthorized voice likenesses.
- Keep a human arrangement/editing record for release candidates.

The U.S. Copyright Office has stated that prompt-only generative output is not enough for copyright protection, while human selection, arrangement, modification, or perceptible human-authored expression can matter.

Sources: [U.S. Copyright Office AI page](https://www.copyright.gov/ai/), [Copyright Office Part 2 release](https://www.copyright.gov/newsnet/2025/1060.html).

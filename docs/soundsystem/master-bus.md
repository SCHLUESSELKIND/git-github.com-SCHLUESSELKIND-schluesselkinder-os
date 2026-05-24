# SNUFFRAGA MASTER BUS

## Position

The MASTER BUS is the last layer of the SNUFFRAGA SOUNDSYSTEM AI ENGINE. It is
not a replacement for stem editing. It is the final quality and export step
that turns an editable `SoundGraph` into release-ready audio at controlled
sample rates and bit depths.

```text
SoundGraph Stems
  -> Stem Mix Bus
  -> Pre-Master Check
  -> Master Bus
  -> Export Profiles
```

The MASTER BUS does not generate music and does not own composition. It owns
loudness, glue, tone, and format.

## Why Not "AI Mastering"

The label "AI Mastering" implies a black-box generic improvement. We do not
want that framing internally. SNUFFRAGA MASTER BUS is a controllable export
bus. Mode + profile is a contract; the implementation behind the contract may
use SonicMaster, Matchering, or a hand-rolled limiter chain over time.

## Mastering Modes (V1)

| Mode               | Use                                                   |
| ------------------ | ----------------------------------------------------- |
| `club_pressure`    | Loud, controlled, DJ-usable, no festival sheen        |
| `dub_warmth`       | Tape saturation, warm low-mids, controlled high-end    |
| `bass_heavy`       | Sub-forward, soundsystem-leaning, physical low-end    |
| `vocal_forward`    | Vocal clarity prioritized, dynamics preserved          |
| `dark_warehouse`   | Dry brutalist tone, minimal air                       |
| `reference_match`  | Match an internal reference track (RMS/spectrum)       |

`reference_match` requires a `reference_track_uri` from an internal,
rights-cleared reference library. The endpoint blocks the job with
`REFERENCE_BLOCKED` if the URI is missing.

## Export Profiles (V1)

| Profile                          | Sample Rate | Bit Depth | Float | Use                                |
| -------------------------------- | ----------- | --------- | ----- | ---------------------------------- |
| `streaming_ready_wav_24_441`     | 44.1 kHz    | 24        | no    | Spotify / Apple / streaming masters |
| `club_master_wav_24_48`          | 48 kHz      | 24        | no    | DJ promo, club delivery             |
| `hd_master_wav_24_96`            | 96 kHz      | 24        | no    | HD archive master                   |
| `premaster_wav_32_float`         | 48 kHz      | 32        | yes   | Hand-off to external engineer       |
| `stem_pack_wav_24_48`            | 48 kHz      | 24        | no    | Per-lane stems for remix licensing  |

Lossless WAV only. Lossy formats are out of scope for the MASTER BUS contract;
encoding to AAC/OPUS happens downstream from these masters when required.

## API Contract

| Route                          | Method | Purpose                                |
| ------------------------------ | ------ | -------------------------------------- |
| `/v1/masters`                  | POST   | Create a master bus job for a generation |
| `/v1/masters/{job_id}`         | GET    | Read master bus job status              |

### Request

```json
{
  "generation_id": "uuid-of-completed-generation-job",
  "mode": "club_pressure",
  "profiles": [
    "streaming_ready_wav_24_441",
    "club_master_wav_24_48",
    "hd_master_wav_24_96"
  ],
  "reference_track_uri": null
}
```

### Job State Machine

```text
DRAFT
  -> QUEUED
  -> RUNNING
  -> REFERENCE_BLOCKED   (reference_match without uri)
  -> EXPORT_READY
  -> FAILED
  -> CANCELLED
```

### Manifest

The completed job carries a `MasterBusManifest`:

```json
{
  "generation_id": "uuid",
  "mode": "club_pressure",
  "masters": [
    {
      "profile": "club_master_wav_24_48",
      "path": "/tmp/snuffraga/<project>/masters/club_pressure/club_master_wav_24_48.wav",
      "sample_rate": 48000,
      "bit_depth": 24,
      "is_float": false
    }
  ],
  "manifest_json": "/tmp/snuffraga/<project>/masters/club_pressure/manifest.json",
  "pressure_report_json": "/tmp/snuffraga/<project>/masters/club_pressure/pressure_report.json"
}
```

The pressure report holds the loudness / true-peak / crest-factor / sub-pressure
summary defined in [sound-model.md](./sound-model.md#druck-model). The mock
provider writes the path only; the real implementation populates the file.

## Implementation Reference

The V1 mock provider lives in
[services/soundsystem-inference/app/master_bus.py](../../services/soundsystem-inference/app/master_bus.py).
It produces deterministic paths per mode + profile and does not run DSP.

Candidate engines for the real implementation:

- **SonicMaster** (Apache-2.0) — text-controlled restoration + mastering. Most
  natural fit for SNUFFRAGA's prompt-style direction ("more Druck", "less
  harsh", "more club"). Primary candidate.
- **Matchering** — reference matching (RMS / spectrum / peak / stereo width).
  Becomes the engine behind `reference_match` mode once internal reference
  tracks are catalogued.
- **AudioMaster** — architecture inspiration only. GPL-3.0 makes direct code
  reuse incompatible with the SNUFFRAGA license posture; do not copy code from
  it.

## Non-Goals

- No replacement for stem-level editing. Mixing decisions stay in the
  `SoundGraph`.
- No public-facing "one-click master" service. Internal operator surface only.
- No mastering of third-party tracks without explicit rights status, even via
  `reference_match`.
- No mastering preset library. Every job is mode + profile + parameters; we do
  not ship a curated preset list as a product.

## Slice 3 Status

- Schemas, repository, mock provider, and routes shipped.
- Real DSP engines (SonicMaster, Matchering) not implemented.
- Reference clearance is enforced only by presence-of-URI, not by a rights
  lookup. Lookup against an internal reference library is a follow-up.
- The pressure-report payload is reserved as a file path only; the JSON
  contents are TBD until real analysis runs.

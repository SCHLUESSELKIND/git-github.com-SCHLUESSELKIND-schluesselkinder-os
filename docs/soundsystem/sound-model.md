# SNUFFRAGA SOUNDGRAPH Model

## Definition

`SNUFFRAGA SOUNDGRAPH` is the internal music model abstraction for the SNUFFRAGA SOUNDSYSTEM AI ENGINE.

It is not one monolithic neural model. It is a stem-first creative model that combines:

- prompt intelligence
- engine routing
- editable stem planning
- versioned arrangement data
- post-generation regeneration
- copyright and provenance checks

The user experience should feel as direct as a modern full-song generator: write what you want, get music back. The difference is that the canonical output is not a locked stereo song. The canonical output is a `SoundGraph`: a versioned song object made of editable stems, regions, parameters, prompts, and history.

## Product Position

Suno v5.5 is positioned publicly around expressiveness, Voices, Custom Models, and My Taste. Our model should match the low-friction prompting expectation, but exceed it in controllability:

- more precise sound-design language
- explicit stem planning before generation
- editable beat, percussion, bass, vocal, FX, and atmosphere tracks
- per-stem regeneration and repaint
- post-generation arrangement editing
- safety and rights metadata on every generation

This is the core difference:

```text
Suno-style product:
Prompt -> Song

SNUFFRAGA SOUNDGRAPH:
Prompt -> Stem Plan -> Generated Takes -> Editable Stem Graph -> Mix/Export
```

## Canonical Object

A generated work is stored as:

```text
Project
  SoundGraph
    PromptVersion[]
    TempoMap[]
    ArrangementSection[]
    StemLane[]
    Region[]
    EffectRack[]
    Automation[]
    GenerationTake[]
    SafetyReport[]
    ExportPackage[]
```

The full mix is an artifact, not the source of truth. Stems and their edit history are the source of truth.

## Prompting Modes

### 1. Simple Prompt

For fast creation:

```text
142 BPM dark industrial dub riddim, crushing sub bass, dry warehouse drums,
ritual whisper hook, black concrete atmosphere, instant drop, stem-heavy arrangement.
```

The system compiles this into structured modules and a stem plan.

### 2. Modular Prompt

For repeatable control:

```json
{
  "energy": "warehouse",
  "bass_pressure": "crushing",
  "vocals": "ritual",
  "atmosphere": "black_concrete",
  "structure": "instant_drop",
  "tempo": {
    "bpm": 142,
    "feel": "half_time_pressure",
    "swing": 0.08
  },
  "druck": {
    "sub_pressure": 4,
    "transient_pressure": 3,
    "mix_pressure": "soundsystem_limited"
  },
  "effect_devices": ["dub_delay", "spring_reverb", "tape_saturation"],
  "bpm": 142,
  "key": "F minor",
  "duration_seconds": 180
}
```

### 3. Stem Prompt

For individual lane creation:

```text
Generate only the percussion lane: metallic rim shots, broken 16th hats,
short spring reverb, no kick, no bass, no vocals.
```

### 4. Edit Prompt

For after-the-fact changes:

```text
Keep the kick and bass exactly as they are. Replace only the vocal hook with
a colder whispered mantra, less melody, more tape delay on the last word.
```

### 5. Repair Prompt

For surgical fixes:

```text
Remove harsh 6-8 kHz vocal hiss from the hook stem. Do not change timing,
lyrics, pitch, bass, or drums.
```

## Required Stem Lanes

Every full generation should try to create or extract these lanes:

| Lane | Purpose | Editable operations |
| --- | --- | --- |
| `kick` | main low transient and groove anchor | replace, tighten, tune, saturate, sidechain target |
| `drums` | core beat excluding optional percussion detail | regenerate, quantize, simplify, densify, split |
| `percussion` | hats, shakers, rims, metal, foley rhythm | regenerate, humanize, remove, widen |
| `bass` | sub, mid-bass, reese, dub pressure | retune, resample, sidechain, simplify, saturate |
| `music` | chords, synths, pads, melodic instruments | repaint, thin, widen, mute sections |
| `lead` | lead synth, hook instrument, motif | regenerate, simplify, call-response edit |
| `vocals_main` | main sung/spoken vocal | replace, retime, de-ess, regenerate phrase |
| `vocals_adlibs` | adlibs, doubles, chants, background vocals | remove, regenerate, pan, filter |
| `fx` | risers, impacts, transitions, dub throws | generate, place, stretch, reverse |
| `atmosphere` | room tone, smoke, drones, noise beds | generate, loop, filter, duck |
| `return_delay` | printed delay throws when needed | mute, automate, regenerate |
| `return_reverb` | printed reverb tails when needed | mute, automate, shorten |

For MVP, lanes may be generated directly or separated from a full mix. Every lane must store how it was produced:

- `generated_direct`
- `source_separated`
- `repainted`
- `imported`
- `manual_edit`

## Stem Edit Operations

Every lane should support these operation families over time.

### Transport

- mute
- solo
- volume
- pan
- phase invert
- region split
- region trim
- loop

### Mix

- EQ
- compression
- saturation
- transient shaping
- gate/expander
- de-ess
- stereo width
- send to delay/reverb

### Effect Devices

Effects are first-class devices, not baked-in decoration. Every stem lane may
have an `EffectRack`, and every device parameter may be automated over time.

Required device families:

| Device | Use |
| --- | --- |
| `eq` | surgical cleanup, tone shaping, low-cut, harshness removal |
| `compressor` | dynamic control, glue, vocal leveling |
| `limiter` | stem peak protection, not final loudness abuse |
| `gate` | remove bleed, tighten drums, hard rhythmic cuts |
| `transient_shaper` | kick snap, percussion bite, softened attacks |
| `saturation` | tape, tube, transformer, digital edge |
| `distortion` | industrial drive, crushed drums, aggressive bass |
| `filter` | dub sweeps, breakdown movement, telephone/radio vocals |
| `chorus` | width, detuned synths, unstable vocal doubles |
| `phaser` | moving machine texture, psychedelic dub movement |
| `flanger` | metallic movement, transition pressure |
| `delay` | slapback, dotted dub delay, ping-pong, tape feedback |
| `reverb` | spring, plate, chamber, warehouse, infinite tail |
| `sidechain` | bass ducking, atmosphere breathing, kick pressure |
| `stutter` | chopped vocal/FX repeats |
| `reverse` | reversed cymbals, vocal pulls, transition ghosts |
| `resampler` | degraded sampler color, gritty aliasing |
| `tape_stop` | stop-down transitions and breakdown edits |

Effect placement:

- insert devices live inside one lane
- send devices live on return lanes such as `return_delay` and `return_reverb`
- print devices create a new audio take when the sound should be frozen

The user must be able to prompt:

```text
Put a darker spring reverb only on the snare percussion.
Add tape delay throws only on the last word of the hook.
Crush the bass with saturation but keep the sub clean.
Remove reverb from the kick and make it dry.
```

### AI Edit

- regenerate lane
- regenerate selected region
- repaint with prompt
- create alternate take
- simplify
- intensify
- remove bleed
- clean noise
- convert to MIDI/pattern later

### Arrangement

- duplicate region
- move section
- mute section
- create breakdown
- create drop
- extend intro/outro
- freeze approved region

## Sound Controls

The model should expose more sound possibilities than generic genre prompting by separating descriptors into controllable dimensions:

| Dimension | Examples |
| --- | --- |
| `room` | black concrete, warehouse, metal stairwell, dry booth, dub chamber |
| `bass_shape` | sine sub, reese, square pressure, rubber bass, distorted mid-bass |
| `drum_machine` | 808, 909, 707, analog modular, industrial samples, acoustic trash |
| `groove` | straight, swung, half-time, broken, dembow-infected, stepping |
| `transient` | soft, clipped, hard, dusty, metallic, gated |
| `saturation` | clean, tape, tube, transformer, digital clipping |
| `space` | dry, spring, plate, dub delay, slapback, infinite tail |
| `vocal_distance` | mouth-close, booth, hallway, radio, megaphone, spectral |
| `mix_pressure` | open, glued, crushed, overdriven, soundsystem-limited |
| `artifact_tolerance` | clean, gritty, damaged, cassette, resampled |

These controls should compile to engine prompts and later to mix/post-processing parameters.

## Tempo Model

Tempo is not just one BPM number. It is part of the editable SoundGraph.

Required tempo controls:

| Control | Meaning |
| --- | --- |
| `bpm` | base tempo |
| `time_signature` | default `4/4`, but must allow `3/4`, `6/8`, `7/8`, and mixed sections later |
| `feel` | straight, swung, half-time, double-time, broken, stepping |
| `swing` | numeric groove offset, initially `0.0` to `0.3` |
| `tempo_map` | section-level tempo changes |
| `warp_markers` | alignment anchors for imported or regenerated audio |
| `locked_grid` | whether edits must preserve current grid |

The model should support these prompt commands:

```text
Keep the song at 142 BPM but make the percussion feel more swung.
Make the bass half-time while the hats stay double-time.
Slow the breakdown to 128 BPM, then snap back to 142 at the drop.
Retighten the drums to the grid without changing the vocal timing.
```

Tempo edits must respect locked lanes. If `vocals_main` is locked, a drum
retime operation may not stretch the vocal lane.

## Druck Model

`Druck` is the system's internal word for perceived sound pressure. It is not
only loudness. It combines low-end force, transient impact, density,
saturation, dynamics, and mix bus behavior.

Use a 0-5 scale for operator controls:

| Parameter | Description |
| --- | --- |
| `sub_pressure` | physical low-end weight below roughly 80 Hz |
| `bass_body` | 80-250 Hz body and chest pressure |
| `transient_pressure` | kick/snare/percussion hit force |
| `density` | how full the arrangement feels |
| `compression` | perceived glue and flattening |
| `distortion_pressure` | harmonic aggression and clipping feel |
| `air_control` | harshness, hiss, sibilance, upper-frequency stress |
| `headroom` | safety margin before clipping |

Pressure presets:

| Preset | Meaning |
| --- | --- |
| `open` | dynamic, roomy, not crushed |
| `glued` | controlled, label-ready pressure |
| `club` | loud but clean enough for DJ use |
| `soundsystem` | sub-forward, physical, dark |
| `crushed` | aggressive internal experiment |
| `redline` | unsafe unless explicitly approved |

The user should be able to prompt:

```text
More Druck on the bass, but keep the vocal clean.
Make the kick hit harder without making the whole mix louder.
Reduce harsh pressure in the hats.
Push the drop into soundsystem pressure, not EDM loudness.
```

Final exports must store pressure metadata:

- integrated loudness estimate
- true peak estimate
- crest factor estimate
- sub pressure score
- clipping warnings
- lane-level pressure notes

## Engine Routing

| Intent | Primary path | Why |
| --- | --- | --- |
| Full track draft | ACE-Step | fast controllable generation |
| Riddim / instrumental | ACE-Step | strong structure and edit workflow |
| Long vocal song | YuE | better lyrics-to-song path |
| FX / atmosphere | Stable Audio Open | short sound-design assets |
| Stem repaint | ACE-Step cover/repaint/lego | region/stem editing |
| Stem cleanup | analysis/separation tools | repair after generation |

The UI should hide this complexity by default. Advanced mode can show the selected engine and reason.

## Output Contract

Every completed generation must export:

- full mix WAV
- individual stem WAVs
- stem manifest JSON
- prompt JSON
- edit history JSON
- lyrics JSON/TXT
- metadata JSON
- cover image
- safety report JSON

The stem manifest is required:

```json
{
  "soundgraph_id": "sg_warehouse_001",
  "bpm": 142,
  "key": "F minor",
  "sample_rate": 48000,
  "lanes": [
    {
      "lane": "bass",
      "path": "stems/bass.wav",
      "source": "generated_direct",
      "engine": "ACE_STEP",
      "editable": true,
      "locked": false,
      "confidence": 0.94,
      "effect_rack": ["eq", "saturation", "sidechain"],
      "pressure": {
        "sub_pressure": 4,
        "distortion_pressure": 2
      }
    }
  ],
  "tempo_map": [
    {
      "section": "drop_1",
      "bpm": 142,
      "feel": "half_time_pressure",
      "swing": 0.08
    }
  ]
}
```

## Editing Rule

The user must be able to say:

```text
Only change the bass.
Only change the percussion.
Only change the hook vocal.
Keep everything else locked.
```

Technically, this means every generation must support locked lanes. A regeneration request receives:

- locked stem references
- target lane or region
- edit prompt
- current arrangement context
- safety context

The result is a new take, not a destructive overwrite.

## MVP Scope

MVP must define and display the model even before all audio operations are real:

1. Compile simple prompts into structured prompt modules.
2. Produce a stem plan with required lanes.
3. Mock artifact paths for full mix and stems.
4. Store generation events and provider status.
5. Show that stems are individually addressable.

The first real implementation after the mock path should be:

1. ACE-Step full mix generation.
2. Stem separation into the required lanes.
3. Stem manifest creation.
4. Per-stem prompt edit endpoint.
5. Regenerate selected lane while preserving locked lanes.

## Non-Goals

- no public Suno clone
- no unauthorized artist style cloning
- no voice likeness without explicit clearance
- no fake rights claims
- no social automation
- no destructive stem overwrite

## Sources Checked

- Suno v5.5 announcement, March 26 2026: https://suno.com/blog/v5-5
- Suno v5.5 help article, edited March 26 2026: https://help.suno.com/en/articles/11362305

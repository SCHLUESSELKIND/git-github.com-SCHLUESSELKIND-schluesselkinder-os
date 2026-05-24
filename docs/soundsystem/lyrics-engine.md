# SNUFFRAGA LYRICS ENGINE

Internal contract layer for prompted, edited, and locked lyrics drafts. Owns
versioning, locking, and the SoundGraph export shape. Does not call GPT-5.5
yet — `LyricsSource.GPT_5_5` is reserved on the schema for when wiring lands.

## Product Pipeline

```text
Prompt
  -> Lyrics Structure
  -> Lyrics Draft (mock today, GPT-5.5 later)
  -> Manual Edit (user replaces section content)
  -> Prompt Edit (rewrite a section by prompt)
  -> Selection Rewrite (N variants for a line range)
  -> Versioned Lyrics (no destructive overwrite)
  -> SoundGraph Export
```

## Why Not Plain Text

A flat text blob would make SCHLUESSELKINDER's editing model impossible.
Lyrics drive vocal arrangement, lane assignment, and stem regeneration, so the
engine has to address them at three levels at once:

- **Structure level** — section sequence (`verse`, `pre_chorus`, `chorus`,
  `dub_breakdown`, etc.) must align with SoundGraph arrangement regions.
  A `dub_breakdown` section must not carry sung lyrics; a
  `instrumental_opening` must not start with a vocal entry.
- **Section level** — each section has its own source (`user`, `mock`,
  `gpt_5_5`), can be locked, and can be regenerated independently. A locked
  chorus survives every subsequent edit byte-for-byte.
- **Line level** — every line carries an index, estimated syllable count, and
  a rhyme group. The `/v1/lyrics/selections` endpoint operates on a line range
  inside a section to produce N variants, so the operator can A/B-compare
  phrasings without losing the rest of the section.

Plain text loses all of that the moment it is serialized as one string.

## Section Types

| Type                    | Vocal entry | Notes                                          |
| ----------------------- | ----------- | ---------------------------------------------- |
| `instrumental_opening`  | no          | Forced into position 0 when `avoid_intro_singing=true` |
| `verse`                 | yes         | vocals_main lane                               |
| `pre_chorus`            | yes         | vocals_main lane                               |
| `chorus`                | yes         | vocals_main + optional vocals_adlibs           |
| `bridge`                | yes         | vocals_main lane                               |
| `dub_breakdown`         | no          | delay throws · vocal off                       |
| `outro`                 | yes         | vocals_main lane, often filtered               |

Default structure (no intro override):
`verse, pre_chorus, chorus, verse, chorus, bridge, dub_breakdown, chorus, outro`.

With `avoid_intro_singing=true` the engine inserts `instrumental_opening` at
index 0.

## Editing Metadata

Per-section flags on `LyricsSection`:

- `locked: bool` — preserved byte-for-byte by every edit until explicitly
  unlocked.
- `manually_edited: bool` — set when the user replaces section content via
  `POST /v1/lyrics/manual-updates`.
- `source: user | gpt_5_5 | mock` — declares the origin. Today only `user`
  and `mock` are reachable; `gpt_5_5` is reserved.
- `notes: str | None` — short operator notes attached to the section.

Per-edit flags on `LyricsEditRequest`:

- `target_section` — regenerate every section of this type.
- `target_section_index` — regenerate exactly this section.
- `preserve_rhyme` / `preserve_syllable_length` — instructive flags carried
  into the compiled prompt (the mock provider does not yet enforce them on
  the text, but they survive into the negative-prompt and engine hints).

Per-request flags on `LyricsGenerationRequest`:

- `avoid_intro_singing` — forces an instrumental opening.
- `structure` — explicit section sequence; defaults to the canonical one
  above when not provided.

## Compiled Prompt

`compile_lyrics_prompt(LyricsGenerationRequest) -> CompiledLyricsPrompt`
returns:

- `instruction` — natural-language brief for an LLM.
- `negative_prompt` — explicit forbidden patterns (`"Oh oh oh"`, `"Na na na"`,
  artist references, festival cliches).
- `safety_notes` — operator guardrails; expanded automatically when the input
  brief itself contains risky filler patterns.
- `suno_compat_notes` — translation hints for Suno-style bracket tags and
  adlib parentheses.
- `soundgraph_compat_notes` — how the structure maps to vocals_main /
  vocals_adlibs lanes and how locked sections survive edits.
- `structure` — resolved section sequence.
- `risky_filler_patterns` — non-empty when the brief itself contains filler
  patterns; lets the caller surface a warning in the operator console.

## API

| Route                                                              | Method | Operation                                            |
| ------------------------------------------------------------------ | ------ | ---------------------------------------------------- |
| `/v1/lyrics/prompts/compile`                                       | POST   | Compile a generation request without persisting      |
| `/v1/lyrics/generations`                                           | POST   | Create project (or reuse by key) + version 1 — `generate` |
| `/v1/lyrics/edits`                                                 | POST   | Append a new version with prompt-driven changes — `edit` |
| `/v1/lyrics/manual-updates`                                        | POST   | Append a new version with user-provided lines        |
| `/v1/lyrics/selections`                                            | POST   | N variants for a line range — `rewrite-selection`    |
| `/v1/lyrics/versions/{version_id}`                                 | GET    | Read a specific version                              |
| `/v1/lyrics/versions/{version_id}/export`                          | POST   | Build the export manifest for SoundGraph hand-off — `export` |
| `/v1/lyrics/versions/{version_id}/sections/{section_index}/lock`   | POST   | Toggle the locked flag on one section, no content change — `lock` |
| `/v1/lyrics/versions/{version_id}/apply-selection-rewrite`         | POST   | Apply a rewritten line set to one section; 409 if locked — `apply-selection-rewrite` |
| `/v1/lyrics/projects`                                              | GET    | List all known projects (newest first)               |
| `/v1/lyrics/projects/{project_key}`                                | GET    | Read a project by its key                            |
| `/v1/lyrics/projects/{project_key}/versions`                       | GET    | List versions for a project, oldest first            |
| `/v1/lyrics/projects/{project_key}/versions/{version_number}`      | GET    | Read a specific version by per-project number        |

Route names are REST-style (collection plurals). The right-hand "operation"
column maps to the conceptual verbs (`generate`, `edit`, `rewrite-selection`,
`export`) used elsewhere in the docs and operator console.

## Endpoint Examples

All examples assume the FastAPI service is running at `http://localhost:8010`.
All payloads are honest mock output — no external service is contacted.

### Generate (POST /v1/lyrics/generations)

Request:

```json
{
  "project_key": "snuffraga-warehouse-001",
  "prompt": "Cold afterhours signal. No bright room. Hold the pressure.",
  "character_code": "SHIBARI_KAWAII",
  "avoid_intro_singing": true,
  "preserve_rhyme": true,
  "preserve_syllable_length": false,
  "target_language": "en"
}
```

Response (`LyricsVersion`, abbreviated):

```json
{
  "id": "f4e2b0c8-...-version-1",
  "project_id": "8a17...",
  "version": 1,
  "parent_version_id": null,
  "edit_summary": null,
  "structure": {
    "avoid_intro_singing": true,
    "target_language": "en",
    "sections": [
      {
        "index": 0,
        "section_type": "instrumental_opening",
        "label": "INTRO (INSTRUMENTAL)",
        "lines": [
          { "index": 0, "text": "[instrumental — sub only]", "syllables": 5, "rhyme_group": null }
        ],
        "locked": false,
        "manually_edited": false,
        "source": "mock"
      },
      {
        "index": 1,
        "section_type": "verse",
        "label": "VERSE 1",
        "lines": [
          { "index": 0, "text": "Concrete keeps the sound until the room is empty.", "syllables": 12, "rhyme_group": "A" },
          { "index": 1, "text": "Nothing here belongs to me. Nothing I will say.", "syllables": 12, "rhyme_group": "B" }
        ],
        "locked": false,
        "manually_edited": false,
        "source": "mock"
      }
    ]
  }
}
```

### Edit (POST /v1/lyrics/edits)

Request:

```json
{
  "version_id": "f4e2b0c8-...-version-1",
  "edit_prompt": "Make the verse harder, more dub pressure.",
  "target_section_index": 1,
  "preserve_rhyme": true,
  "preserve_syllable_length": false
}
```

Response: a new `LyricsVersion` with `version: 2`, `parent_version_id` set to
the input version, and `edit_summary` containing the edit prompt. Locked
sections are preserved byte-for-byte. Sections matching `target_section` or
`target_section_index` are regenerated by the mock provider; everything else
is copied unchanged.

### Rewrite Selection (POST /v1/lyrics/selections)

Request:

```json
{
  "version_id": "f4e2b0c8-...-version-2",
  "section_index": 1,
  "line_start_index": 0,
  "line_end_index": 2,
  "rewrite_prompt": "Tighter phrasing, more pressure",
  "variant_count": 3
}
```

Response (`LyricsRewriteResponse`):

```json
{
  "section_index": 1,
  "line_start_index": 0,
  "line_end_index": 2,
  "variants": [
    {
      "index": 0,
      "summary": "variant 1",
      "lines": [
        { "index": 0, "text": "Concrete keeps the sound until the room is empty.", "syllables": 12, "rhyme_group": "A" },
        { "index": 1, "text": "Nothing here belongs to me. Nothing I will say.", "syllables": 12, "rhyme_group": "B" },
        { "index": 2, "text": "Black mirror, late hour, slow signal pressure.", "syllables": 12, "rhyme_group": "A" }
      ]
    },
    {
      "index": 1,
      "summary": "variant 2",
      "lines": [
        { "index": 0, "text": "Nothing here belongs to me. Nothing I will say.", "syllables": 12, "rhyme_group": "A" },
        { "index": 1, "text": "Black mirror, late hour, slow signal pressure.", "syllables": 12, "rhyme_group": "B" },
        { "index": 2, "text": "Concrete keeps the sound until the room is empty.", "syllables": 12, "rhyme_group": "A" }
      ]
    }
  ]
}
```

Selections do **not** create a new version. They produce candidate variants
for an operator to evaluate. The operator commits a choice via a follow-up
`POST /v1/lyrics/manual-updates` that writes the chosen variant into the
section.

### Export (POST /v1/lyrics/versions/{version_id}/export)

Request: empty body, version id in the path.

Response (`LyricsExportManifest`):

```json
{
  "version_id": "f4e2b0c8-...-version-2",
  "project_id": "8a17...",
  "lyrics_txt_path": "/tmp/snuffraga/snuffraga-warehouse-001/lyrics/v2/lyrics.txt",
  "lyrics_json_path": "/tmp/snuffraga/snuffraga-warehouse-001/lyrics/v2/lyrics.json",
  "safety_report_json_path": "/tmp/snuffraga/snuffraga-warehouse-001/lyrics/v2/safety_report.json",
  "section_index_map": {
    "INTRO (INSTRUMENTAL)": 0,
    "VERSE 1": 1,
    "CHORUS 1": 2
  },
  "vocal_notes": [
    { "section_index": 0, "note": "vocal_entry=false (instrumental opening)" },
    { "section_index": 1, "note": "vocal_entry=true · lane=vocals_main · source=mock" },
    { "section_index": 2, "note": "vocal_entry=true · lane=vocals_main · source=mock" }
  ]
}
```

`vocal_notes` is what the SoundGraph importer reads to assign sections to
`vocals_main` and `vocals_adlibs` lanes. `safety_report_json_path` is a
reserved path; the file is not written to disk in this slice.

## Export Manifest

`LyricsExportManifest` carries:

- `lyrics_txt_path` / `lyrics_json_path` — operator scratch paths under
  `/tmp/snuffraga/<project_key>/lyrics/v<N>/`.
- `vocal_notes: list[VocalPerformanceNote]` — one note per section,
  e.g. `"vocal_entry=true · lane=vocals_main · source=user"`.
- `section_index_map` — label → absolute index, used by the SoundGraph
  importer to align with arrangement regions.
- `safety_report_json_path` — reserved path; contents not written today.

## Mock Provider Behavior

`MockLyricsProvider` is deterministic over `(project_key, prompt, character_code)`
and respects the contract layer in full:

- Generates lines per section type from internal templates rotated by a
  SHA-256-derived seed.
- Estimates syllables (vowel-cluster count) and assigns simple `A/B` rhyme
  groups.
- Edits only sections matching `target_section` / `target_section_index` and
  never touches `locked=true` sections.
- Manual updates flip `manually_edited=True`, `source=USER`, and optionally
  `locked=True` if `lock=true` was requested.
- Selection rewrites return N deterministic rotations of the selected lines;
  no real rewrite happens.

The provider imports no external clients. The `test_mock_provider_requires_no_external_service`
test blocks `httpx` / `requests` / `openai` / `anthropic` / `boto3` from the
import system to confirm.

## Versioning Rules

- Every edit appends a new `LyricsVersion`. The previous version is never
  mutated.
- `parent_version_id` chains versions for history reconstruction.
- `edit_summary` carries the operator-supplied (or system-generated)
  one-liner describing the change.
- Manual updates produce a version with `edit_summary = "manual update
  section N"`.

## Suno Compatibility Export

`CompiledLyricsPrompt.suno_compat_notes` documents the rules for exporting
SCHLUESSELKINDER lyrics to Suno-compatible text:

- Section labels render as Suno-style uppercase bracket tags (`[VERSE]`,
  `[CHORUS]`, `[BRIDGE]`, `[OUTRO]`).
- Adlib hints inline as parentheses such as `(oh)` map to the `vocals_adlibs`
  lane on SoundGraph import and to Suno's adlib convention on Suno import.
- Suno's bias toward `"oh oh oh"` openings is suppressed by the standard
  negative prompt and by `avoid_intro_singing` when an instrumental opening
  is required. `risky_filler_patterns` on the compiled prompt surfaces any
  filler patterns the brief itself contained, so operators can rewrite the
  brief before generation.

The Suno-compatibility output is descriptive only in this slice. The Suno
export writer ships in a later slice.

## SoundGraph Compatibility Export

`CompiledLyricsPrompt.soundgraph_compat_notes` and
`LyricsExportManifest.vocal_notes` together describe how the lyrics structure
maps to the SoundGraph stem lanes documented in [sound-model.md](./sound-model.md):

- Each `LyricsSection` becomes one SoundGraph arrangement region with
  matching index. The label is the operator-facing handle; the absolute
  index is the SoundGraph link.
- Sung sections (`verse`, `pre_chorus`, `chorus`, `bridge`, `outro`) emit
  `vocal_entry=true` notes that target the `vocals_main` lane by default.
  Adlib hints route their lines to the `vocals_adlibs` lane.
- `instrumental_opening` and `dub_breakdown` emit `vocal_entry=false` notes
  so the SoundGraph keeps those regions silent on vocal lanes.
- Locked sections preserve their text across SoundGraph regenerations, so
  the vocal lane edit story (regenerate kick/drums, keep chorus) is
  intact end-to-end.

## Future GPT-5.5 API Integration Boundary

Today every line of text comes from `MockLyricsProvider`. The GPT-5.5
boundary is reserved on the schema and the provider abstraction:

- `LyricsSource.GPT_5_5` exists on the enum and is wire-stable.
- `MockLyricsProvider` is the only provider registered today; it imports
  nothing from `httpx`, `openai`, or `anthropic` (verified by
  `test_mock_provider_requires_no_external_service`).
- The real implementation will land as a sibling provider that consumes the
  same `LyricsGenerationRequest` / `LyricsEditRequest` / `LyricsRewriteSelectionRequest`
  inputs and returns the same `LyricsStructure` / `LyricsRewriteVariant`
  outputs.
- Engagement is gated by an explicit `LYRICS_MOCK_MODE` env flag (planned
  for the next slice). When the flag is `true`, all routes resolve to the
  mock provider regardless of whether keys are configured.
- The provider abstraction does not expose API keys, model names, or token
  counts back to the route handlers; those stay inside the provider
  module.

No live external API call is made by this slice. No key is read, no request
is sent, no response is parsed.

## Generated TypeScript Types (Slice 8)

The web app's API types live in
[apps/web/app/admin/soundsystem/_lib/generated-inference-types.ts](../../apps/web/app/admin/soundsystem/_lib/generated-inference-types.ts),
generated from `app/schemas.py` + `app/config.py` by a small local Python
reflector at
[services/soundsystem-inference/scripts/generate_ts_types.py](../../services/soundsystem-inference/scripts/generate_ts_types.py).

Regenerate after every Pydantic change:

```bash
cd services/soundsystem-inference
python scripts/generate_ts_types.py
```

A pytest drift check (`tests/test_generated_types.py`) fails if the committed
file is stale or if the generator is non-deterministic across runs. No Node-
side codegen tool, no `datamodel-code-generator` — just Pydantic + stdlib.

`inference-types.ts` survives as the single TS-side naming layer: it re-
exports every generated type plus a few UI-side aliases (e.g.
`LyricsGenerationInput → LyricsGenerationRequest`). Component imports do not
need to change after a regenerate as long as the alias surface stays stable.

## Persistence (Slice 7)

The lyrics repository now has two implementations selected by environment
variable. The default stays in-memory so existing tests and dev environments
keep working without Postgres.

| Mode         | Env value                                | Storage                                      |
| ------------ | ---------------------------------------- | -------------------------------------------- |
| `in_memory`  | `SOUNDSYSTEM_LYRICS_REPOSITORY` unset    | In-process Python dict; vanishes on restart  |
| `in_memory`  | `SOUNDSYSTEM_LYRICS_REPOSITORY=in_memory`| Same as default                              |
| `postgres`   | `SOUNDSYSTEM_LYRICS_REPOSITORY=postgres` | Postgres tables `lyrics_projects` + `lyrics_versions` |

### Env Vars

| Variable                          | Required when                          | Notes                                |
| --------------------------------- | -------------------------------------- | ------------------------------------ |
| `SOUNDSYSTEM_LYRICS_REPOSITORY`   | always (defaults to `in_memory`)       | Allowed: `in_memory`, `postgres`     |
| `SOUNDSYSTEM_DATABASE_URL`        | `SOUNDSYSTEM_LYRICS_REPOSITORY=postgres` | psycopg-compatible URL               |

If the mode is `postgres` and `SOUNDSYSTEM_DATABASE_URL` is missing, the
service fails loudly at startup with `LyricsRepositoryConfigError`. No silent
fallback to in-memory.

### Postgres Setup (local dev)

```bash
# 1. Install the postgres extra under services/soundsystem-inference
pip install -e ".[postgres]"

# 2. Provision a local Postgres database (any tooling — example with docker)
docker run --rm -d --name snuffraga-pg -p 5432:5432 \
  -e POSTGRES_PASSWORD=local -e POSTGRES_DB=snuffraga_lyrics \
  postgres:16

# 3. Apply the lyrics schema migration
export SOUNDSYSTEM_DATABASE_URL="postgresql://postgres:local@localhost:5432/snuffraga_lyrics"
psql "$SOUNDSYSTEM_DATABASE_URL" -f services/soundsystem-inference/db/002_lyrics.sql

# 4. Start the inference service in Postgres mode
export SOUNDSYSTEM_LYRICS_REPOSITORY=postgres
uvicorn app.main:app --port 8010
```

There is no auto-migration runner. The SQL file is idempotent (`CREATE TABLE
IF NOT EXISTS`); rerunning it on an existing database is safe.

### Data Model

`lyrics_projects`:

| Column                | Type        | Notes                                                              |
| --------------------- | ----------- | ------------------------------------------------------------------ |
| `id`                  | UUID        | Primary key                                                        |
| `project_key`         | TEXT UNIQUE | Operator-supplied identifier                                       |
| `title`               | TEXT NULL   | Operator-supplied label                                            |
| `character_code`      | TEXT        | e.g. `SHIBARI_KAWAII` — equivalent of "artist" in the spec         |
| `current_version_id`  | UUID NULL   | Cached pointer to the head version (updated on every add_version)  |
| `created_at`          | TIMESTAMPTZ | Project creation time                                              |
| `updated_at`          | TIMESTAMPTZ | Bumped on each new version                                         |

`lyrics_versions`:

| Column              | Type        | Notes                                         |
| ------------------- | ----------- | --------------------------------------------- |
| `id`                | UUID        | Primary key                                   |
| `project_id`        | UUID FK     | ON DELETE CASCADE                             |
| `version_number`    | INTEGER     | Monotonic per project                         |
| `parent_version_id` | UUID NULL FK| ON DELETE SET NULL                            |
| `structure`         | JSONB       | Serialized `LyricsStructure`                  |
| `edit_summary`      | TEXT NULL   | Operator-supplied or system-generated         |
| `created_at`        | TIMESTAMPTZ | Version creation time                         |

Composite unique constraint `(project_id, version_number)` enforces sequential
numbering. The full Pydantic `LyricsVersion` is reconstructed from the JSONB
column on read.

### Spec → Storage Map

The Slice 7 spec lists "Persist at least" fields that don't all become columns
today — some are renamed to match existing Pydantic models, some live inside
the `structure` JSONB, some are derivable, and a few correspond to Pydantic
fields that don't exist yet:

| Spec field           | Realization                                                                 |
| -------------------- | --------------------------------------------------------------------------- |
| `project_id`         | `lyrics_projects.id`                                                        |
| `project_key`        | `lyrics_projects.project_key`                                               |
| `title`              | `lyrics_projects.title`                                                     |
| `artist`             | `lyrics_projects.character_code` (renamed to match the existing model)      |
| `language`           | inside `lyrics_versions.structure -> target_language` (JSONB)               |
| `current_version_id` | `lyrics_projects.current_version_id` (cached)                               |
| `created_at`         | `lyrics_projects.created_at` and `lyrics_versions.created_at`               |
| `updated_at`         | `lyrics_projects.updated_at` (bumped on every `add_version`)                |
| `version_id`         | `lyrics_versions.id`                                                        |
| `version_number`     | `lyrics_versions.version_number`                                            |
| `parent_version_id`  | `lyrics_versions.parent_version_id`                                         |
| `source`             | per-section, inside `structure.sections[].source` (JSONB)                   |
| `edit_summary`       | `lyrics_versions.edit_summary`                                              |
| `sections`           | inside `lyrics_versions.structure` (JSONB)                                  |
| `performance_notes`  | not yet on the Pydantic model; reserved for a future migration              |
| `safety_notes`       | not yet on the Pydantic model; reserved for a future migration              |
| `export_metadata`    | not yet on the Pydantic model; reserved for a future migration              |

The binding requirement — *"persist enough data to reconstruct the exact
existing Pydantic response objects"* — is satisfied: every field that exists
on `LyricsProject` and `LyricsVersion` today is preserved across the JSONB
roundtrip.

### Repository Contract Preserved

Both implementations satisfy the same `LyricsRepository` Protocol:

- `create_project()` is idempotent on `project_key`.
- `list_projects()` returns newest-first by `created_at`.
- `list_versions()` returns oldest-first by `version_number`.
- `add_version()` assigns the next sequential version number atomically.
- `get_version()` and `get_project_by_key()` return `None` for misses (the
  routes translate to 404).

### UI Behavior

`/v1/capabilities` now reports `lyrics_repository_mode`. The web app reads it
twice:

- `MACHINE STATUS` panel adds a `LYRICS STORE · PERSISTENT` (mint) or
  `LYRICS STORE · SESSION-SCOPED` (amber) row.
- The lyrics index and version-editor pages render `RepositoryModeBanner`,
  which switches the top-of-page note between the persistent-mint and the
  session-scoped-amber variants.

When the capabilities probe fails, the UI defaults to the session-scoped
warning — never claims persistence that isn't verified.

### Slice 7 Limitations

- No auto-migration runner; the SQL file is applied manually.
- Postgres mode requires the optional `postgres` extra to be installed;
  otherwise `PostgresLyricsRepository.__init__` raises a clear error.
- No GPT-5.5 / Claude / OpenAI calls. Mock provider is the only registered
  lyrics provider.
- No Dropbox / Supabase / Redis / RunPod sync. Local download remains the
  only export channel.
- Live Postgres tests are skipped unless `TEST_DATABASE_URL` is set.

## Selection Rewrite + Local Export (Slice 6)

### Selection Rewrite (CENTER → LEFT lift)

Each section in the center column carries a `USE SECTION TEXT` button. Clicking
it lifts the section's lines into the `SELECTION REWRITE` panel on the left
column. Locked sections and empty sections cannot be used as selection input —
the button is disabled with an inline tooltip.

The left panel:

- Empty state: instructs the operator to click `USE SECTION TEXT` beside a
  section.
- Locked state: when the selected section is locked, the panel renders a clear
  block message and offers a `CLEAR SELECTION` action. No variants are built.
- Active state: shows the section index/label, a read-only line preview, a
  `REWRITE PROMPT` input, and `BUILD VARIANTS` + `CLEAR` actions. The variant
  count is fixed at five.
- Variants list: each variant carries its `summary` from the backend (or
  `rotation` as a fallback label) plus `APPLY` / `APPLY + LOCK` actions.

`APPLY` and `APPLY + LOCK` call `POST /v1/lyrics/versions/{id}/apply-selection-rewrite`,
which:

- Rejects locked sections with HTTP 409 (`section_locked`).
- Marks the section `source=mock`, `manually_edited=false` (the operator did
  not type these lines — the provider produced them).
- Optionally sets `locked=true` when the `lock` field is true.
- Appends a new `LyricsVersion` with `parent_version_id` chained.

After apply, the editor navigates to the new version. UI never mutates state
optimistically: if the backend returns an error (e.g. the section was locked
between BUILD VARIANTS and APPLY), the operator sees the error and the
underlying version stays untouched.

### Local Export Downloads

The right column's `EXPORT` section offers three Blob downloads:

| Button                                                          | Content                                              |
| --------------------------------------------------------------- | ---------------------------------------------------- |
| `↓ {project_key}-v{version}-lyrics.txt`                         | Suno-style bracket-tagged text                       |
| `↓ {project_key}-v{version}-lyrics.json`                        | Full `LyricsVersion` JSON (structure + metadata)     |
| `↓ {project_key}-v{version}-soundgraph-lyrics.json`             | The `LyricsExportManifest` from the export endpoint  |

Plus a `PREVIEW MANIFEST (NO DOWNLOAD)` button that renders the manifest
contents in the panel without triggering a Blob download.

All downloads are client-side `Blob` + `URL.createObjectURL` + anchor `click()`.
No server-side artifact store. No Dropbox sync. The panel explicitly carries:

> "Local browser download. No Dropbox sync. No persistent artifact store."
> "Export is a contract artifact, not a release-ready distribution package."

### Frontend Type Organization

TypeScript types previously co-located in `_lib/inference.ts` are now in
`_lib/inference-types.ts`. The header comment makes the contract explicit:

> Hand-mirrored from Pydantic schemas in
> `services/soundsystem-inference/app/schemas.py`. Keep in sync until generated
> types land.

The `inference.ts` module re-exports the same types so existing consumers
continue importing from `./inference` without changes. Generated codegen
(e.g. `datamodel-code-generator --output-model-type typescript`) is a Slice 7
candidate.

## Operator Console (Slice 5)

The lyrics engine has a dedicated surface in the internal console under
`/admin/soundsystem/lyrics`. The same gate as the rest of the soundsystem
console applies (`NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true`).

Route tree:

```text
/admin/soundsystem/lyrics                              index · project list + create form
/admin/soundsystem/lyrics/[project_key]                project view + version list + create form
/admin/soundsystem/lyrics/[project_key]/[version_id]   3-column editor (version_id = per-project version number)
```

The 3-column editor:

- **LEFT — Edit Command.** Prompt textarea, optional `target_section` and
  `target_section_index` selectors, `preserve_rhyme` toggle. Submit posts to
  `/v1/lyrics/edits` and routes to the new version.
- **CENTER — Sections.** Each section renders its label, type, source, line
  list with syllable + rhyme metadata. Per-section `LOCK` toggle posts to
  `/v1/lyrics/versions/.../sections/.../lock`. `EDIT LINES` opens an inline
  textarea that posts to `/v1/lyrics/manual-updates` on `SAVE` or
  `SAVE + LOCK`.
- **RIGHT — Versions, Lock Map, Export.** Version selector with `edit_summary`
  per entry. Lock map shows the boolean state of every section in the current
  version. `BUILD MANIFEST` calls
  `/v1/lyrics/versions/{id}/export` and renders the manifest paths inline.

The web app reads `NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL` to find the
inference service. Defaults to `http://127.0.0.1:8010`. When that endpoint
is unreachable, the lyrics index renders a clear "INFERENCE UNREACHABLE"
panel instead of fake data, and the `MACHINE STATUS` panel's INFERENCE API
row flips from `REACHABLE` to `UNREACHABLE` via a live `/health` probe.

Selection-rewrite UI is not wired in slice 5 — the backend endpoint exists
and is documented above. The UI for picking a line range and committing a
variant is a slice 6 candidate.

## Slice 4 Limitations

- No GPT-5.5 / Claude API call. `LyricsSource.GPT_5_5` is reserved; the
  provider abstraction lets that land later without changing route shapes.
- Rhyme and syllable preservation are advisory only on the mock — they
  appear in the compiled instruction but are not enforced on the generated
  text.
- Variants from `/v1/lyrics/selections` are rotations of the input lines, not
  semantic rewrites.
- The export manifest references file paths only; the JSON files are not
  written to disk.

## Slice 5 Candidates

- Wire a real LLM provider behind an explicit `LYRICS_MOCK_MODE` env flag.
- Render `lyrics.txt` / `lyrics.json` artifacts to disk during export.
- Enforce `preserve_syllable_length` in the mock by measuring against the
  original lines.
- Operator console UI for the lyrics version timeline and inline editing
  (lives under `/admin/soundsystem/lyrics`).
- Safety filter: artist-name and reference-line lists checked at compile
  time rather than only via the negative prompt.

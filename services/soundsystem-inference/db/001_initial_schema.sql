create extension if not exists pgcrypto;
create extension if not exists vector;

create schema if not exists soundsystem;

create type soundsystem.generation_intent as enum (
  'CREATE_TRACK',
  'BUILD_RIDDIM',
  'GENERATE_HOOK',
  'CREATE_VOCALS',
  'STEM_REMIX',
  'DUB_FX_LAB',
  'CHARACTER_VOICE',
  'COVER_GENERATION',
  'PROMPT_LIBRARY',
  'STYLE_DNA_SYSTEM'
);

create type soundsystem.engine as enum (
  'ACE_STEP',
  'YUE',
  'STABLE_AUDIO_OPEN',
  'MOCK'
);

create type soundsystem.job_status as enum (
  'DRAFT',
  'PREFLIGHT_BLOCKED',
  'QUEUED',
  'RUNNING',
  'RENDERING_STEMS',
  'ANALYZING_SAFETY',
  'EXPORT_READY',
  'EXPORTED',
  'FAILED',
  'CANCELLED'
);

create type soundsystem.artifact_type as enum (
  'FULL_MIX_WAV',
  'STEM_WAV',
  'LYRICS',
  'PROMPT_JSON',
  'METADATA_JSON',
  'COVER_IMAGE',
  'SAFETY_REPORT_JSON',
  'GENERATION_HISTORY_JSON'
);

create type soundsystem.safety_verdict as enum (
  'PASS',
  'REVIEW',
  'BLOCK',
  'LEGAL'
);

create type soundsystem.rights_basis as enum (
  'OWNED',
  'COMMISSIONED',
  'LICENSED',
  'PUBLIC_DOMAIN',
  'CC0',
  'UNKNOWN',
  'BLOCKED'
);

create table if not exists soundsystem.projects (
  id uuid primary key default gen_random_uuid(),
  project_key text not null unique,
  title text not null,
  artist_code text not null default 'SHIBARI_KAWAII',
  status text not null default 'ACTIVE',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists soundsystem.characters (
  id uuid primary key default gen_random_uuid(),
  character_code text not null unique,
  display_name text not null,
  description text not null,
  vocal_rules jsonb not null default '{}'::jsonb,
  lyrical_rules jsonb not null default '{}'::jsonb,
  safety_rules jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.style_dna_profiles (
  id uuid primary key default gen_random_uuid(),
  profile_code text not null unique,
  title text not null,
  description text not null,
  traits jsonb not null default '[]'::jsonb,
  rights_notes text,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.prompt_modules (
  id uuid primary key default gen_random_uuid(),
  module_type text not null,
  module_value text not null,
  label text not null,
  prompt_fragment text not null,
  negative_fragment text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (module_type, module_value)
);

create table if not exists soundsystem.prompt_versions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references soundsystem.projects(id) on delete set null,
  intent soundsystem.generation_intent not null,
  character_code text not null,
  raw_modules jsonb not null,
  compiled_prompt text not null,
  negative_prompt text not null,
  lyrics text,
  technical jsonb not null default '{}'::jsonb,
  safety_notes jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.generation_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references soundsystem.projects(id) on delete set null,
  prompt_version_id uuid not null references soundsystem.prompt_versions(id),
  intent soundsystem.generation_intent not null,
  engine soundsystem.engine not null,
  status soundsystem.job_status not null default 'QUEUED',
  progress numeric(5,4) not null default 0,
  model_version text,
  adapter_version_id uuid,
  seed bigint,
  error_code text,
  error_message text,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists soundsystem.generation_events (
  id uuid primary key default gen_random_uuid(),
  generation_job_id uuid not null references soundsystem.generation_jobs(id) on delete cascade,
  event_type text not null,
  message text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.artifacts (
  id uuid primary key default gen_random_uuid(),
  generation_job_id uuid not null references soundsystem.generation_jobs(id) on delete cascade,
  artifact_type soundsystem.artifact_type not null,
  stem_name text,
  local_path text,
  dropbox_path text,
  mime_type text,
  sample_rate integer,
  duration_seconds numeric(10,3),
  byte_size bigint,
  sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.audio_embeddings (
  id uuid primary key default gen_random_uuid(),
  artifact_id uuid not null references soundsystem.artifacts(id) on delete cascade,
  embedding_model text not null,
  embedding_dimension integer not null,
  extractor_version text not null,
  embedding vector,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.similarity_checks (
  id uuid primary key default gen_random_uuid(),
  generation_job_id uuid not null references soundsystem.generation_jobs(id) on delete cascade,
  artifact_id uuid references soundsystem.artifacts(id) on delete set null,
  check_type text not null,
  verdict soundsystem.safety_verdict not null,
  score numeric(8,6),
  threshold numeric(8,6),
  matched_reference text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.training_datasets (
  id uuid primary key default gen_random_uuid(),
  dataset_key text not null unique,
  title text not null,
  rights_basis soundsystem.rights_basis not null,
  owner text,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists soundsystem.training_items (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references soundsystem.training_datasets(id) on delete cascade,
  title text not null,
  source_path text,
  sha256 text not null,
  rights_basis soundsystem.rights_basis not null,
  rights_notes text,
  created_at timestamptz not null default now(),
  unique (dataset_id, sha256)
);

create table if not exists soundsystem.adapter_versions (
  id uuid primary key default gen_random_uuid(),
  adapter_key text not null unique,
  engine soundsystem.engine not null,
  dataset_id uuid references soundsystem.training_datasets(id) on delete restrict,
  adapter_type text not null,
  version text not null,
  local_path text,
  dropbox_path text,
  sha256 text,
  training_config jsonb not null default '{}'::jsonb,
  safety_verdict soundsystem.safety_verdict not null default 'REVIEW',
  created_at timestamptz not null default now()
);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'generation_jobs_adapter_version_fk'
  ) then
    alter table soundsystem.generation_jobs
      add constraint generation_jobs_adapter_version_fk
      foreign key (adapter_version_id)
      references soundsystem.adapter_versions(id)
      on delete set null;
  end if;
end $$;

create table if not exists soundsystem.dropbox_exports (
  id uuid primary key default gen_random_uuid(),
  generation_job_id uuid not null references soundsystem.generation_jobs(id) on delete cascade,
  root_path text not null,
  manifest_path text not null,
  export_status text not null default 'PENDING',
  exported_at timestamptz,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists generation_jobs_project_status_idx
  on soundsystem.generation_jobs(project_id, status);

create index if not exists generation_events_job_created_idx
  on soundsystem.generation_events(generation_job_id, created_at);

create index if not exists artifacts_job_type_idx
  on soundsystem.artifacts(generation_job_id, artifact_type);

create index if not exists similarity_checks_job_verdict_idx
  on soundsystem.similarity_checks(generation_job_id, verdict);

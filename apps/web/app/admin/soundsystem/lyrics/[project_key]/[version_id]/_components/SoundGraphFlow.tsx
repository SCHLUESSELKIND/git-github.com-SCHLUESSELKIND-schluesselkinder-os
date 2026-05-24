"use client";

import { useState, useTransition } from "react";
import {
  compileSoundgraph,
  soundgraphHandoff,
  createExportPack,
  InferenceClientError
} from "../../../../_lib/inference";
import type {
  SoundGraphWriteResult,
  SoundGraphHandoffResult,
  ArrangementRegion,
  MusicArtifactManifest,
  ExportPack
} from "../../../../_lib/generated-inference-types";

type Props = Readonly<{
  versionId: string;
  projectKey: string;
}>;

type FlowStage = "idle" | "soundgraph" | "handoff" | "complete" | "exported";

export function SoundGraphFlow({ versionId, projectKey }: Props) {
  const [stage, setStage] = useState<FlowStage>("idle");
  const [bpm, setBpm] = useState("140");
  const [keySignature, setKeySignature] = useState("");
  const [energyProfile, setEnergyProfile] = useState("standard");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const [soundgraphResult, setSoundgraphResult] = useState<SoundGraphWriteResult | null>(null);
  const [handoffResult, setHandoffResult] = useState<SoundGraphHandoffResult | null>(null);
  const [exportPack, setExportPack] = useState<ExportPack | null>(null);

  function handleBuildSoundgraph(): void {
    setError(null);
    const parsedBpm = Number.parseInt(bpm, 10);
    if (!Number.isFinite(parsedBpm) || parsedBpm < 60 || parsedBpm > 220) {
      setError("BPM must be between 60 and 220");
      return;
    }
    startTransition(async () => {
      try {
        const result = await compileSoundgraph({
          lyrics_version_id: versionId,
          bpm: parsedBpm,
          key_signature: keySignature.trim() || null,
          energy_profile: energyProfile
        });
        setSoundgraphResult(result);
        setStage("soundgraph");
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleSendToMusicRouter(): void {
    if (!soundgraphResult) return;
    setError(null);
    startTransition(async () => {
      try {
        const result = await soundgraphHandoff({
          arrangement_id: soundgraphResult.arrangement.arrangement_id,
          title: `${projectKey} · SoundGraph → Track`
        });
        setHandoffResult(result);
        setStage("complete");
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleExportPack(): void {
    if (!handoffResult) return;
    setError(null);
    startTransition(async () => {
      try {
        const pack = await createExportPack({
          music_job_id: handoffResult.music_job.job_id,
          title: `${projectKey} · Project Pack`
        });
        setExportPack(pack);
        setStage("exported");
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleReset(): void {
    setStage("idle");
    setSoundgraphResult(null);
    setHandoffResult(null);
    setExportPack(null);
    setError(null);
  }

  return (
    <section>
      <header className="mb-3 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-2">
        <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          SOUNDGRAPH FLOW
        </h2>
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {stage === "idle" && "READY"}
          {stage === "soundgraph" && "SOUNDGRAPH BUILT"}
          {stage === "handoff" && "SENDING…"}
          {stage === "complete" && "TRACK COMPLETE"}
          {stage === "exported" && "EXPORTED"}
        </span>
      </header>

      {/* Stage: idle — show BPM/key/profile inputs + BUILD button */}
      {stage === "idle" && (
        <div className="grid gap-3">
          <p className="font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
            Build a SoundGraph from this lyrics version, then send to the Music Router
            to produce a mock track with artifacts and provenance.
          </p>
          <div className="grid grid-cols-3 gap-2">
            <label className="grid gap-1">
              <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                BPM
              </span>
              <input
                type="number"
                min={60}
                max={220}
                value={bpm}
                onChange={(e) => setBpm(e.target.value)}
                disabled={isPending}
                className="border border-[color:var(--ss-border-strong)] bg-transparent px-2 py-1.5 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
              />
            </label>
            <label className="grid gap-1">
              <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                KEY
              </span>
              <input
                type="text"
                value={keySignature}
                onChange={(e) => setKeySignature(e.target.value)}
                disabled={isPending}
                placeholder="Dm"
                className="border border-[color:var(--ss-border-strong)] bg-transparent px-2 py-1.5 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
              />
            </label>
            <label className="grid gap-1">
              <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                ENERGY
              </span>
              <select
                value={energyProfile}
                onChange={(e) => setEnergyProfile(e.target.value)}
                disabled={isPending}
                className="border border-[color:var(--ss-border-strong)] bg-transparent px-2 py-1.5 font-mono text-[0.7rem] uppercase text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
              >
                <option value="standard">standard</option>
                <option value="slow_build">slow build</option>
                <option value="peak_early">peak early</option>
                <option value="flat">flat</option>
              </select>
            </label>
          </div>
          <button
            type="button"
            onClick={handleBuildSoundgraph}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {isPending ? "BUILDING…" : "BUILD SOUNDGRAPH"}
          </button>
        </div>
      )}

      {/* Stage: soundgraph — show arrangement summary + SEND button */}
      {stage === "soundgraph" && soundgraphResult && (
        <div className="grid gap-3">
          <ArrangementSummary result={soundgraphResult} />
          <RegionList regions={soundgraphResult.arrangement.regions} />
          <button
            type="button"
            onClick={handleSendToMusicRouter}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {isPending ? "SENDING…" : "SEND TO MUSIC ROUTER"}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            RESET
          </button>
        </div>
      )}

      {/* Stage: complete — show job + artifacts + provenance + export button */}
      {stage === "complete" && handoffResult && (
        <div className="grid gap-3">
          <JobResult result={handoffResult} />
          <button
            type="button"
            onClick={handleExportPack}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {isPending ? "EXPORTING…" : "EXPORT AS PROJECT PACK"}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            START NEW FLOW
          </button>
        </div>
      )}

      {/* Stage: exported — show export pack summary */}
      {stage === "exported" && exportPack && (
        <div className="grid gap-3">
          <ExportPackSummary pack={exportPack} />
          <button
            type="button"
            onClick={handleReset}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            START NEW FLOW
          </button>
        </div>
      )}

      {/* Warnings */}
      {soundgraphResult && soundgraphResult.warnings.length > 0 && (
        <ul className="mt-2 grid gap-1">
          {soundgraphResult.warnings.map((w, i) => (
            <li
              key={i}
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              {w}
            </li>
          ))}
        </ul>
      )}

      {/* Error */}
      {error !== null && (
        <p
          className="mt-2 border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
          role="alert"
        >
          {error}
        </p>
      )}
    </section>
  );
}

function ArrangementSummary({
  result
}: Readonly<{ result: SoundGraphWriteResult }>) {
  const { arrangement } = result;
  return (
    <div className="grid grid-cols-2 gap-2 border border-[color:var(--ss-border)] p-3" style={{ backgroundColor: "var(--ss-panel-elevated)" }}>
      <StatCell label="BPM" value={String(arrangement.bpm)} />
      <StatCell label="BARS" value={String(result.total_bars)} />
      <StatCell label="SECTIONS" value={String(result.section_count)} />
      <StatCell
        label="VOCAL / INSTR"
        value={`${result.vocal_regions} / ${result.instrumental_regions}`}
      />
      <StatCell label="KEY" value={arrangement.key_signature ?? "—"} />
      <StatCell label="LANES" value={String(arrangement.lane_assignments.length)} />
    </div>
  );
}

function RegionList({
  regions
}: Readonly<{ regions: ReadonlyArray<ArrangementRegion> }>) {
  return (
    <div className="grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
      {regions.map((region) => (
        <div
          key={region.region_index}
          className="grid grid-cols-[2.5rem_1fr_auto] items-center gap-2 px-3 py-1.5"
          style={{ backgroundColor: "var(--ss-panel)" }}
        >
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {String(region.region_index).padStart(2, "0")}
          </span>
          <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            {region.label}
          </span>
          <div className="flex items-center gap-2">
            <span
              className="border px-1.5 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: energyColor(region.energy)
              }}
            >
              {region.energy}
            </span>
            {region.vocal_entry !== "none" && (
              <span
                className="border px-1.5 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
                style={{
                  borderColor: "var(--ss-border-accent)",
                  color: "var(--ss-accent)"
                }}
              >
                {region.vocal_entry}
              </span>
            )}
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {region.bar_count}b
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function JobResult({
  result
}: Readonly<{ result: SoundGraphHandoffResult }>) {
  const { music_job } = result;
  return (
    <div className="grid gap-3">
      {/* Job header */}
      <div
        className="grid gap-2 border border-[color:var(--ss-border)] p-3"
        style={{ backgroundColor: "var(--ss-panel-elevated)" }}
      >
        <div className="flex items-center justify-between">
          <span className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            MUSIC JOB
          </span>
          <span
            className="border px-2 py-0.5 font-mono text-[0.58rem] font-black uppercase tracking-widest"
            style={{
              borderColor:
                music_job.status === "completed"
                  ? "var(--ss-border-accent)"
                  : "var(--ss-warning-dim)",
              color:
                music_job.status === "completed"
                  ? "var(--ss-accent)"
                  : "var(--ss-warning)"
            }}
          >
            {music_job.status}
          </span>
        </div>
        <dl className="grid grid-cols-2 gap-2 font-mono text-[0.6rem] uppercase tracking-widest">
          <div>
            <dt className="text-[color:var(--ss-text-muted)]">INTENT</dt>
            <dd className="text-[color:var(--ss-text-primary)]">{result.resolved_intent}</dd>
          </div>
          <div>
            <dt className="text-[color:var(--ss-text-muted)]">DURATION</dt>
            <dd className="text-[color:var(--ss-text-primary)]">
              {result.estimated_duration_seconds.toFixed(1)}s
            </dd>
          </div>
          <div>
            <dt className="text-[color:var(--ss-text-muted)]">LANES</dt>
            <dd className="text-[color:var(--ss-text-primary)]">
              {result.requested_lanes.length} active
              {result.locked_lanes.length > 0
                ? ` · ${result.locked_lanes.length} locked`
                : ""}
            </dd>
          </div>
          <div>
            <dt className="text-[color:var(--ss-text-muted)]">PROVENANCE</dt>
            <dd className="text-[color:var(--ss-accent)]">
              {music_job.provenance_id ? "TRACKED" : "—"}
            </dd>
          </div>
        </dl>
      </div>

      {/* Artifacts */}
      {music_job.artifacts.length > 0 && (
        <div className="grid gap-1">
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            ARTIFACTS · {music_job.artifacts.length}
          </span>
          <ul className="grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
            {(music_job.artifacts as ReadonlyArray<MusicArtifactManifest>).map(
              (artifact, i) => (
                <li
                  key={i}
                  className="grid grid-cols-[auto_1fr] gap-2 px-3 py-1.5"
                  style={{ backgroundColor: "var(--ss-panel)" }}
                >
                  <span
                    className="border px-1.5 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
                    style={{
                      borderColor: "var(--ss-border-strong)",
                      color: "var(--ss-text-secondary)"
                    }}
                  >
                    {artifact.artifact_type}
                  </span>
                  <span className="break-all font-mono text-[0.58rem] text-[color:var(--ss-text-primary)]">
                    {artifact.path}
                  </span>
                </li>
              )
            )}
          </ul>
        </div>
      )}

      {/* Compiled prompt preview */}
      <details className="border border-[color:var(--ss-border)]">
        <summary className="cursor-pointer px-3 py-2 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:text-[color:var(--ss-text-secondary)]">
          COMPILED PROMPT
        </summary>
        <pre
          className="overflow-x-auto whitespace-pre-wrap px-3 py-2 font-mono text-[0.6rem] leading-4 text-[color:var(--ss-text-secondary)]"
          style={{ backgroundColor: "var(--ss-panel-elevated)" }}
        >
          {result.compiled_prompt}
        </pre>
      </details>
    </div>
  );
}

function ExportPackSummary({ pack }: Readonly<{ pack: ExportPack }>) {
  return (
    <div className="grid gap-3">
      <div
        className="grid gap-2 border border-[color:var(--ss-border)] p-3"
        style={{ backgroundColor: "var(--ss-panel-elevated)" }}
      >
        <div className="flex items-center justify-between">
          <span className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            PROJECT PACK
          </span>
          <span
            className="border px-2 py-0.5 font-mono text-[0.58rem] font-black uppercase tracking-widest"
            style={{
              borderColor: "var(--ss-border-accent)",
              color: "var(--ss-accent)"
            }}
          >
            {pack.status}
          </span>
        </div>
        <dl className="grid grid-cols-2 gap-2 font-mono text-[0.6rem] uppercase tracking-widest">
          <div>
            <dt className="text-[color:var(--ss-text-muted)]">TITLE</dt>
            <dd className="text-[color:var(--ss-text-primary)]">{pack.title}</dd>
          </div>
          <div>
            <dt className="text-[color:var(--ss-text-muted)]">COMPONENTS</dt>
            <dd className="text-[color:var(--ss-text-primary)]">{pack.total_components}</dd>
          </div>
          {pack.bpm && (
            <div>
              <dt className="text-[color:var(--ss-text-muted)]">BPM</dt>
              <dd className="text-[color:var(--ss-text-primary)]">{pack.bpm}</dd>
            </div>
          )}
          {pack.key_signature && (
            <div>
              <dt className="text-[color:var(--ss-text-muted)]">KEY</dt>
              <dd className="text-[color:var(--ss-text-primary)]">{pack.key_signature}</dd>
            </div>
          )}
          {pack.intent && (
            <div>
              <dt className="text-[color:var(--ss-text-muted)]">INTENT</dt>
              <dd className="text-[color:var(--ss-text-primary)]">{pack.intent}</dd>
            </div>
          )}
          {pack.estimated_duration_seconds && (
            <div>
              <dt className="text-[color:var(--ss-text-muted)]">DURATION</dt>
              <dd className="text-[color:var(--ss-text-primary)]">
                {pack.estimated_duration_seconds.toFixed(1)}s
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* Component list */}
      <div className="grid gap-1">
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          BUNDLE CONTENTS · {pack.components.length}
        </span>
        <ul className="grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
          {pack.components.map((component, i) => (
            <li
              key={i}
              className="grid grid-cols-[auto_1fr] gap-2 px-3 py-1.5"
              style={{ backgroundColor: "var(--ss-panel)" }}
            >
              <span
                className="border px-1.5 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
                style={{
                  borderColor: "var(--ss-border-strong)",
                  color: "var(--ss-text-secondary)"
                }}
              >
                {component.component_type}
              </span>
              <span className="font-mono text-[0.58rem] text-[color:var(--ss-text-primary)]">
                {component.label}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Pack ID for reference */}
      <p className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        PACK · {pack.pack_id}
      </p>
    </div>
  );
}

function StatCell({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="grid gap-0.5">
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span className="font-mono text-[0.78rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
        {value}
      </span>
    </div>
  );
}

function energyColor(energy: string): string {
  switch (energy) {
    case "peak":
      return "var(--ss-accent)";
    case "high":
      return "var(--ss-text-primary)";
    case "medium":
      return "var(--ss-text-secondary)";
    case "low":
      return "var(--ss-text-muted)";
    case "drop":
      return "var(--ss-warning)";
    default:
      return "var(--ss-text-muted)";
  }
}

function formatError(error: unknown): string {
  if (error instanceof InferenceClientError) {
    return error.status ? `${error.status} · ${error.message}` : error.message;
  }
  if (error instanceof Error) return error.message;
  return "inference_error";
}

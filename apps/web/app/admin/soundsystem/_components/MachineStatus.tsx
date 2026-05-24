import {
  getInferenceCapabilities,
  inferenceConfigState,
  inferenceHealth,
  type LyricsRepositoryMode
} from "../_lib/inference";

type MachineStatusRow = {
  readonly label: string;
  readonly state: string;
  readonly tone: "warning" | "muted" | "ready";
  readonly detail?: string;
};

type InferenceProbe = Readonly<{
  state: "reachable" | "unreachable" | "not_configured";
  detail: string;
  lyricsRepositoryMode: LyricsRepositoryMode | null;
}>;

async function probeInference(): Promise<InferenceProbe> {
  if (inferenceConfigState() === "unconfigured") {
    return {
      state: "not_configured",
      detail: "Set SOUNDSYSTEM_INFERENCE_URL on the server to enable the probe.",
      lyricsRepositoryMode: null
    };
  }
  try {
    const health = await inferenceHealth();
    let lyricsRepositoryMode: LyricsRepositoryMode | null = null;
    try {
      const capabilities = await getInferenceCapabilities();
      lyricsRepositoryMode = capabilities.lyrics_repository_mode;
    } catch {
      // Capabilities probe failure is non-fatal; the inference row is still useful.
    }
    return {
      state: health.status === "ok" ? "reachable" : "unreachable",
      detail: `${health.service} · ${health.status}`,
      lyricsRepositoryMode
    };
  } catch (error) {
    return {
      state: "unreachable",
      detail: error instanceof Error ? error.message : "unknown",
      lyricsRepositoryMode: null
    };
  }
}

const STATIC_ROWS: ReadonlyArray<MachineStatusRow> = [
  { label: "DROPBOX SYNC", state: "NOT WIRED", tone: "warning" },
  { label: "SAFETY LAYER", state: "DESIGN ONLY", tone: "muted" },
  { label: "STEM EXPORT", state: "NOT WIRED", tone: "warning" },
  { label: "PROMPT ENGINE", state: "MOCK PROVIDER", tone: "muted" }
];

export async function MachineStatus() {
  const probe = await probeInference();
  const inferenceRow: MachineStatusRow = inferenceRowFor(probe);
  const lyricsRow: MachineStatusRow = lyricsRowFor(probe);
  const rows: ReadonlyArray<MachineStatusRow> = [
    inferenceRow,
    lyricsRow,
    ...STATIC_ROWS
  ];

  return (
    <section
      aria-labelledby="machine-status-heading"
      className="border border-[color:var(--ss-border)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] px-5 py-3">
        <h2
          id="machine-status-heading"
          className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]"
        >
          MACHINE STATUS
        </h2>
        <span
          className="font-mono text-[0.6rem] uppercase tracking-widest"
          style={{ color: headerToneFor(probe.state) }}
        >
          {headerLabelFor(probe.state)}
        </span>
      </header>
      <p className="border-b border-[color:var(--ss-border)] px-5 py-3 font-mono text-[0.7rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
        Inference API and Lyrics Store rows reflect a live probe when configured.
        The remaining rows are a static readiness map — no live services are queried for them in this slice.
      </p>
      <dl className="divide-y divide-[color:var(--ss-border)]">
        {rows.map((row) => (
          <div
            key={row.label}
            className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-3"
          >
            <dt className="font-mono text-[0.72rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
              {row.label}
              {row.detail !== undefined ? (
                <span className="ml-2 normal-case text-[0.6rem] tracking-normal text-[color:var(--ss-text-muted)]">
                  {row.detail}
                </span>
              ) : null}
            </dt>
            <dd
              className="border px-2 py-1 font-mono text-[0.62rem] font-black uppercase tracking-widest"
              style={tonePalette(row.tone)}
            >
              {row.state}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function inferenceRowFor(probe: InferenceProbe): MachineStatusRow {
  if (probe.state === "reachable") {
    return { label: "INFERENCE API", state: "REACHABLE", tone: "ready" };
  }
  if (probe.state === "not_configured") {
    return {
      label: "INFERENCE API",
      state: "NOT CONFIGURED",
      tone: "warning",
      detail: probe.detail
    };
  }
  return {
    label: "INFERENCE API",
    state: "NOT REACHABLE",
    tone: "warning",
    detail: probe.detail
  };
}

function lyricsRowFor(probe: InferenceProbe): MachineStatusRow {
  if (probe.lyricsRepositoryMode === "postgres") {
    return {
      label: "LYRICS STORE",
      state: "PERSISTENT",
      tone: "ready",
      detail: "postgres"
    };
  }
  if (probe.lyricsRepositoryMode === "in_memory") {
    return {
      label: "LYRICS STORE",
      state: "SESSION-SCOPED",
      tone: "warning",
      detail: "in_memory"
    };
  }
  return {
    label: "LYRICS STORE",
    state: "UNKNOWN",
    tone: "muted",
    detail: "capabilities probe failed"
  };
}

function headerLabelFor(state: InferenceProbe["state"]): string {
  if (state === "reachable") return "LIVE PROBE · INFERENCE";
  if (state === "not_configured") return "STATIC · INFERENCE NOT CONFIGURED";
  return "STATIC · INFERENCE OFFLINE";
}

function headerToneFor(state: InferenceProbe["state"]): string {
  return state === "reachable" ? "var(--ss-accent)" : "var(--ss-warning)";
}

function tonePalette(tone: MachineStatusRow["tone"]) {
  if (tone === "warning") {
    return {
      borderColor: "var(--ss-warning-dim)",
      color: "var(--ss-warning)"
    };
  }
  if (tone === "ready") {
    return {
      borderColor: "var(--ss-border-accent)",
      color: "var(--ss-accent)"
    };
  }
  return {
    borderColor: "var(--ss-border-strong)",
    color: "var(--ss-text-muted)"
  };
}

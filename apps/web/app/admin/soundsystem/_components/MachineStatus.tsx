type MachineStatusRow = {
  readonly label: string;
  readonly state: string;
  readonly tone: "warning" | "muted";
};

const ROWS: readonly MachineStatusRow[] = [
  { label: "INFERENCE API", state: "NOT WIRED", tone: "warning" },
  { label: "DROPBOX SYNC", state: "NOT WIRED", tone: "warning" },
  { label: "SAFETY LAYER", state: "DESIGN ONLY", tone: "muted" },
  { label: "STEM EXPORT", state: "NOT WIRED", tone: "warning" },
  { label: "PROMPT ENGINE", state: "LOCAL SPEC ONLY", tone: "muted" }
] as const;

export function MachineStatus() {
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
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-warning)]">
          STATIC · NO LIVE QUERIES
        </span>
      </header>
      <p className="border-b border-[color:var(--ss-border)] px-5 py-3 font-mono text-[0.7rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
        Static readiness map. No live services are queried in this slice.
      </p>
      <dl className="divide-y divide-[color:var(--ss-border)]">
        {ROWS.map((row) => (
          <div
            key={row.label}
            className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-3"
          >
            <dt className="font-mono text-[0.72rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
              {row.label}
            </dt>
            <dd
              className="border px-2 py-1 font-mono text-[0.62rem] font-black uppercase tracking-widest"
              style={{
                borderColor:
                  row.tone === "warning" ? "var(--ss-warning-dim)" : "var(--ss-border-strong)",
                color: row.tone === "warning" ? "var(--ss-warning)" : "var(--ss-text-muted)"
              }}
            >
              {row.state}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

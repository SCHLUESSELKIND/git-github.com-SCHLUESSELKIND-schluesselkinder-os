type SafetyCheck = Readonly<{ label: string; state: string }>;

const CHECKS: readonly SafetyCheck[] = [
  { label: "artist-name filter", state: "pending" },
  { label: "reference-track filter", state: "pending" },
  { label: "prompt audit log", state: "pending" },
  { label: "audio similarity check", state: "pending" }
] as const;

export function SafetyProtocolPanel() {
  return (
    <section
      aria-labelledby="safety-protocol-heading"
      className="border border-[color:var(--ss-warning-dim)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <header className="flex items-center justify-between border-b border-[color:var(--ss-warning-dim)] px-5 py-3">
        <h2
          id="safety-protocol-heading"
          className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]"
        >
          SAFETY PROTOCOL
        </h2>
        <span className="font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-warning)]">
          DESIGN ONLY
        </span>
      </header>
      <p className="border-b border-[color:var(--ss-warning-dim)] px-5 py-3 font-mono text-[0.7rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
        Specification only. No filter is active in this slice. Prompts, references, and outputs are
        not yet audited.
      </p>
      <ul className="grid gap-px" style={{ backgroundColor: "var(--ss-warning-dim)" }}>
        {CHECKS.map((check) => (
          <li
            key={check.label}
            className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-3"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <span className="font-mono text-[0.72rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
              {check.label}
            </span>
            <span
              className="border px-2 py-1 font-mono text-[0.62rem] font-black uppercase tracking-widest"
              style={{ borderColor: "var(--ss-warning-dim)", color: "var(--ss-warning)" }}
            >
              {check.state}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

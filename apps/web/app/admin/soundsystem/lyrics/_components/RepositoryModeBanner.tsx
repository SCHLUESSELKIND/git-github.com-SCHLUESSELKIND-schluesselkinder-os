import type { LyricsRepositoryMode } from "../../_lib/inference";

type Props = Readonly<{ mode: LyricsRepositoryMode | null }>;

export function RepositoryModeBanner({ mode }: Props) {
  if (mode === "postgres") {
    return (
      <div
        className="mb-6 grid gap-2 border border-[color:var(--ss-border-accent)] px-4 py-3 font-mono text-[0.62rem] uppercase leading-5 tracking-widest"
        style={{ color: "var(--ss-accent)" }}
        role="note"
      >
        <p>
          Persistent: lyrics versions are stored in Postgres. The configured database is the
          source of truth.
        </p>
        <p style={{ color: "var(--ss-text-muted)" }}>
          Mock/local provider. No GPT-5.5 calls are active in this slice.
        </p>
        <p style={{ color: "var(--ss-text-muted)" }}>
          Export is a contract artifact, not a release-ready distribution package.
        </p>
      </div>
    );
  }

  return (
    <div
      className="mb-6 grid gap-2 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.62rem] uppercase leading-5 tracking-widest"
      style={{ color: "var(--ss-warning)" }}
      role="note"
    >
      <p>
        Session-scoped: versions are stored in the running inference process and disappear on
        restart.
      </p>
      <p>Mock/local provider. No GPT-5.5 calls are active in this slice.</p>
      <p>Export is a contract artifact, not a release-ready distribution package.</p>
    </div>
  );
}

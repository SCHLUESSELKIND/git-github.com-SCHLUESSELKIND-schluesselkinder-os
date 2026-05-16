import Link from "next/link";
import { SoundsystemShell } from "./SoundsystemShell";
import type { CommandIntent } from "../_lib/operators";

type AwaitingWireProps = Readonly<{
  intent: CommandIntent;
}>;

export function AwaitingWire({ intent }: AwaitingWireProps) {
  return (
    <SoundsystemShell title={`${intent.title}.`} status="AWAITING WIRE">
      <div className="grid gap-8 md:grid-cols-[1fr_0.6fr]">
        <section
          className="border border-[color:var(--ss-border)] p-6"
          style={{ backgroundColor: "var(--ss-panel)" }}
        >
          <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            INTENT
          </p>
          <p className="mt-2 font-mono text-sm uppercase tracking-widest text-[color:var(--ss-accent)]">
            {intent.code}
          </p>
          <p className="mt-6 font-mono text-xs uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            BRIEF
          </p>
          <p className="mt-2 text-sm leading-7 text-[color:var(--ss-text-secondary)]">{intent.summary}</p>
          <p className="mt-6 font-mono text-xs uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            ENGINE ROUTE
          </p>
          <p className="mt-2 font-mono text-xs uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
            {intent.engineHint}
          </p>
        </section>
        <section
          className="border border-[color:var(--ss-warning-dim)] p-6"
          style={{ backgroundColor: "var(--ss-panel)" }}
        >
          <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-warning)]">
            STATE · AWAITING WIRE
          </p>
          <p className="mt-4 text-sm leading-7 text-[color:var(--ss-text-secondary)]">
            This surface is not connected to the inference API yet. No prompt is compiled, no job is opened,
            no artifact is produced. The route is reserved for the action only.
          </p>
          <p className="mt-4 text-sm leading-7 text-[color:var(--ss-text-secondary)]">
            Voice likeness and release-candidate flags will remain disabled until safety preflight is wired.
          </p>
          <Link
            href="/admin/soundsystem"
            className="mt-6 inline-block border border-[color:var(--ss-border-strong)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)]"
          >
            ← command grid
          </Link>
        </section>
      </div>
    </SoundsystemShell>
  );
}

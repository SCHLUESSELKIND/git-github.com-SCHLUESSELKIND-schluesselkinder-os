import Link from "next/link";
import { MachineStatus } from "./_components/MachineStatus";
import { SafetyProtocolPanel } from "./_components/SafetyProtocolPanel";
import { SoundsystemShell } from "./_components/SoundsystemShell";
import { COMMAND_INTENTS } from "./_lib/operators";

export default function SoundsystemIndexPage() {
  return (
    <SoundsystemShell title="Command grid." status="QUEUE ARMED">
      <p className="mb-8 max-w-2xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Six operator intents. Each tile compiles a prompt, opens a job, and routes to a model adapter.
        Real adapters are not wired in this slice. Tile state reads AWAITING WIRE until the API call is real.
      </p>
      <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
        {COMMAND_INTENTS.map((intent) => (
          <Link
            key={intent.slug}
            href={`/admin/soundsystem/${intent.slug}`}
            className="flex flex-col gap-4 p-6 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {intent.code}
            </span>
            <span className="text-2xl font-black uppercase leading-none text-[color:var(--ss-text-primary)] md:text-3xl">
              {intent.title}
            </span>
            <span className="font-mono text-xs leading-5 text-[color:var(--ss-text-secondary)]">
              {intent.summary}
            </span>
            <span className="mt-auto flex items-center justify-between border-t border-[color:var(--ss-border-strong)] pt-4 font-mono text-[0.62rem] uppercase tracking-widest">
              <span className="text-[color:var(--ss-text-muted)]">{intent.engineHint}</span>
              <span className="text-[color:var(--ss-warning)]">AWAITING WIRE</span>
            </span>
          </Link>
        ))}
      </div>
      <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_1fr]">
        <MachineStatus />
        <SafetyProtocolPanel />
      </div>
    </SoundsystemShell>
  );
}

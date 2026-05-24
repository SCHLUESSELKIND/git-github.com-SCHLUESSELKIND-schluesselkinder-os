import Link from "next/link";
import { MachineStatus } from "./_components/MachineStatus";
import { SafetyProtocolPanel } from "./_components/SafetyProtocolPanel";
import { SoundsystemShell } from "./_components/SoundsystemShell";
import { COMMAND_INTENTS, intentHref } from "./_lib/operators";

export default function SoundsystemIndexPage() {
  return (
    <SoundsystemShell title="Command grid." status="QUEUE ARMED">
      <p className="mb-8 max-w-2xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Seven operator intents. Each tile compiles a prompt, opens a job, and routes to a model adapter.
        Tiles marked AWAITING WIRE are not connected to the inference API yet. WRITE LYRICS is live against
        the mock lyrics provider.
      </p>
      <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3">
        {COMMAND_INTENTS.map((intent) => {
          const ready = intent.state === "ready";
          const statusLabel = ready ? "READY · MOCK" : "AWAITING WIRE";
          const statusColor = ready ? "var(--ss-accent)" : "var(--ss-warning)";
          return (
            <Link
              key={intent.slug}
              href={intentHref(intent)}
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
                <span style={{ color: statusColor }}>{statusLabel}</span>
              </span>
            </Link>
          );
        })}
      </div>
      <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_1fr]">
        <MachineStatus />
        <SafetyProtocolPanel />
      </div>
    </SoundsystemShell>
  );
}

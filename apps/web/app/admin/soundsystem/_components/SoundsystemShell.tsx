import Link from "next/link";
import type { ReactNode } from "react";
import { COMMAND_INTENTS } from "../_lib/operators";
import { OperatorModeSwitcher } from "./OperatorModeSwitcher";

type SoundsystemShellProps = Readonly<{
  children: ReactNode;
  title: string;
  status?: string;
}>;

export function SoundsystemShell({
  children,
  title,
  status = "QUEUE ARMED"
}: SoundsystemShellProps) {
  return (
    <main
      className="min-h-screen text-[color:var(--ss-text-primary)]"
      style={{ backgroundColor: "var(--ss-bg)" }}
    >
      <div className="grid min-h-screen md:grid-cols-[var(--ss-rail-width)_1fr]">
        <SideRail />
        <div className="flex min-h-screen flex-col">
          <TopRail status={status} />
          <section className="flex-1 px-5 py-8 md:px-8 md:py-10">
            <header className="mb-10 grid gap-3 border-b border-[color:var(--ss-border)] pb-6">
              <p className="font-mono text-[0.68rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                INTERNAL · SOUNDSYSTEM · READ-ONLY MONITOR
              </p>
              <h1 className="text-4xl font-black uppercase leading-none md:text-6xl">{title}</h1>
            </header>
            {children}
          </section>
        </div>
      </div>
    </main>
  );
}

function SideRail() {
  return (
    <aside
      className="hidden border-r border-[color:var(--ss-border)] md:flex md:flex-col"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <Link
        href="/admin/soundsystem"
        className="block border-b border-[color:var(--ss-border)] px-4 py-4 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)]"
      >
        SNUFFRAGA
        <br />
        SOUNDSYSTEM
      </Link>
      <nav aria-label="Soundsystem actions" className="flex flex-col">
        {COMMAND_INTENTS.map((intent) => (
          <Link
            key={intent.slug}
            href={`/admin/soundsystem/${intent.slug}`}
            className="border-b border-[color:var(--ss-border)] px-4 py-3 font-mono text-[0.68rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] hover:text-[color:var(--ss-accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {intent.title}
          </Link>
        ))}
      </nav>
      <Link
        href="/admin"
        className="mt-auto border-t border-[color:var(--ss-border)] px-4 py-3 font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:text-[color:var(--ss-text-secondary)]"
      >
        ← admin root
      </Link>
    </aside>
  );
}

function TopRail({ status }: Readonly<{ status: string }>) {
  return (
    <header
      className="flex flex-wrap items-center gap-3 border-b border-[color:var(--ss-border)] px-5 py-2 md:flex-nowrap md:gap-4 md:px-8 md:py-0"
      style={{ backgroundColor: "var(--ss-panel)", minHeight: "var(--ss-rail-top-height)" }}
    >
      <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        OPERATOR MODE
      </span>
      <OperatorModeSwitcher />
      <span
        className="ml-auto border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.62rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]"
        aria-live="polite"
      >
        {status}
      </span>
    </header>
  );
}

export function SoundsystemUnavailable() {
  return (
    <main
      data-operator-mode="blackout"
      className="min-h-screen text-[color:var(--ss-text-primary)]"
      style={{ backgroundColor: "var(--ss-bg)" }}
    >
      <section className="mx-auto grid min-h-screen max-w-3xl content-center gap-6 px-6 py-20">
        <p className="font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          SOUNDSYSTEM CONSOLE OFFLINE
        </p>
        <h1 className="text-4xl font-black uppercase leading-none md:text-6xl">
          OPERATOR SURFACE DISABLED.
        </h1>
        <div className="border-l-2 border-[color:var(--ss-warning)] pl-4 text-sm leading-7 text-[color:var(--ss-text-secondary)]">
          <p>
            Set <code className="text-[color:var(--ss-accent)]">NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true</code> locally
            to engage the soundsystem console.
          </p>
          <p>This is not authentication. It is only a local boundary marker.</p>
        </div>
      </section>
    </main>
  );
}

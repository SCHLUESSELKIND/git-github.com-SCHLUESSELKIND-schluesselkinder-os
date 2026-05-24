import Link from "next/link";
import { notFound } from "next/navigation";
import { isInternalConsoleEnabled } from "./_lib/admin-gate";

type ModuleState = "ready" | "ready_mock" | "read_only" | "awaiting_wire";

type AdminModule = Readonly<{
  code: string;
  title: string;
  summary: string;
  href?: string;
  state: ModuleState;
}>;

const MODULES: ReadonlyArray<AdminModule> = [
  {
    code: "SOUNDSYSTEM",
    title: "Soundsystem",
    summary:
      "Operator console for the AI music engine. Lyrics, stems, master bus, export — intent-first.",
    href: "/admin/soundsystem",
    state: "ready_mock"
  },
  {
    code: "EVALUATION",
    title: "Evaluation",
    summary:
      "Read-only inspection of brand intelligence, content graph, and generation outputs.",
    href: "/admin/evaluation",
    state: "read_only"
  },
  {
    code: "LIBRARY",
    title: "Library",
    summary:
      "Universal output index across every soundsystem artifact with provenance metadata.",
    state: "awaiting_wire"
  },
  {
    code: "COMPLIANCE",
    title: "Compliance",
    summary:
      "License registry, consent records, safety review queue, and the release-eligibility gate.",
    state: "awaiting_wire"
  },
  {
    code: "VOICE_LAB",
    title: "Voice Lab",
    summary:
      "Spoken voice, voice tags, and consent-gated voice conversion. Reserved surface.",
    state: "awaiting_wire"
  },
  {
    code: "MARKETING_OS",
    title: "Marketing OS",
    summary:
      "Internal campaign control. Reserved surface — no public-facing automation lives here.",
    state: "awaiting_wire"
  },
  {
    code: "RELEASES",
    title: "Releases",
    summary:
      "Frozen release bundles, export packs, Dropbox sync history. Reserved surface.",
    state: "awaiting_wire"
  }
] as const;

function stateChip(state: ModuleState): { label: string; color: string } {
  if (state === "ready_mock") {
    return { label: "READY · MOCK", color: "var(--ss-accent)" };
  }
  if (state === "read_only") {
    return { label: "READ-ONLY", color: "var(--ss-accent)" };
  }
  if (state === "ready") {
    return { label: "READY", color: "var(--ss-accent)" };
  }
  return { label: "AWAITING WIRE", color: "var(--ss-warning)" };
}

export default function AdminHubPage() {
  if (!isInternalConsoleEnabled()) {
    notFound();
  }
  return (
    <main
      data-operator-mode="blackout"
      className="min-h-screen text-[color:var(--ss-text-primary)]"
      style={{ backgroundColor: "var(--ss-bg)" }}
    >
      <section className="mx-auto flex max-w-6xl flex-col gap-10 px-5 py-12 md:px-8 md:py-16">
        <header className="grid gap-3 border-b border-[color:var(--ss-border)] pb-6">
          <p className="font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            SCHLUESSELKINDER · ADMIN · INTERNAL OPERATOR OS
          </p>
          <h1 className="text-4xl font-black uppercase leading-none md:text-6xl">
            Operator hub.
          </h1>
          <p className="max-w-3xl font-mono text-[0.72rem] uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
            Internal tools only. Intent-first: surfaces are named after the creative outcome,
            never after a model or provider. Every module is gated, noindex, and isolated from
            the public site.
          </p>
        </header>

        <div
          className="grid gap-px border border-[color:var(--ss-border)] md:grid-cols-2 lg:grid-cols-3"
          style={{ backgroundColor: "var(--ss-border)" }}
        >
          {MODULES.map((module) => {
            const chip = stateChip(module.state);
            const interactive = Boolean(module.href);
            const Card = interactive ? Link : "div";
            const cardProps = interactive
              ? {
                  href: module.href ?? "/admin",
                  className:
                    "flex flex-col gap-4 p-6 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)]"
                }
              : {
                  className: "flex cursor-not-allowed flex-col gap-4 p-6 opacity-80"
                };
            return (
              <Card
                key={module.code}
                {...(cardProps as { href: string; className: string })}
                style={{ backgroundColor: "var(--ss-panel)" }}
              >
                <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  {module.code}
                </span>
                <span className="text-2xl font-black uppercase leading-none text-[color:var(--ss-text-primary)] md:text-3xl">
                  {module.title}
                </span>
                <span className="font-mono text-xs leading-5 text-[color:var(--ss-text-secondary)]">
                  {module.summary}
                </span>
                <span className="mt-auto flex items-center justify-between border-t border-[color:var(--ss-border-strong)] pt-4 font-mono text-[0.62rem] uppercase tracking-widest">
                  <span className="text-[color:var(--ss-text-muted)]">
                    {interactive ? "OPEN" : "RESERVED"}
                  </span>
                  <span style={{ color: chip.color }}>{chip.label}</span>
                </span>
              </Card>
            );
          })}
        </div>

        <footer className="grid gap-3 border-t border-[color:var(--ss-border)] pt-6 font-mono text-[0.65rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
          <p>
            Admin routes are gated by server-side <code>INTERNAL_CONSOLE_ENABLED</code> and
            optional <code>ADMIN_BASIC_AUTH_USER</code> + <code>ADMIN_BASIC_AUTH_PASSWORD</code>.
            Production posture: fail-closed.
          </p>
          <p>
            The browser never speaks to the inference service directly — every call is proxied
            via <code>/admin/api/soundsystem/*</code>.
          </p>
          <p>
            See{" "}
            <Link
              href="https://github.com/"
              className="text-[color:var(--ss-accent)]"
              prefetch={false}
            >
              docs/soundsystem/admin-integration-strategy.md
            </Link>{" "}
            for the full architecture.
          </p>
        </footer>
      </section>
    </main>
  );
}

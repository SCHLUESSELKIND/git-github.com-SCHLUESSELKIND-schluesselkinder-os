import Link from "next/link";
import type { ReactNode } from "react";

type ConsoleShellProps = Readonly<{
  children: ReactNode;
  eyebrow?: string;
  title: string;
}>;

export function ConsoleShell({ children, eyebrow = "INTERNAL / EVALUATION", title }: ConsoleShellProps) {
  return (
    <main className="min-h-screen bg-[#060606] text-stone-100">
      <section className="mx-auto flex max-w-7xl flex-col gap-10 px-5 py-12 md:px-8 md:py-16">
        <header className="grid gap-6 border-b border-stone-800 pb-8 md:grid-cols-[0.34fr_1fr]">
          <div className="text-[0.68rem] font-black uppercase leading-5 text-stone-500">
            <p>{eyebrow}</p>
            <p>READ-ONLY</p>
            <p>NO AUTHORITY</p>
          </div>
          <div>
            <Link className="text-[0.68rem] font-black uppercase text-red-700 hover:text-red-500" href="/admin/evaluation">
              evaluation index
            </Link>
            <h1 className="mt-6 max-w-5xl text-5xl font-black uppercase leading-none text-stone-100 md:text-8xl">
              {title}
            </h1>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}

export function ConsoleUnavailable() {
  return (
    <main className="min-h-screen bg-[#060606] text-stone-200">
      <section className="mx-auto grid min-h-screen max-w-5xl content-center gap-8 px-5 py-20 md:px-8">
        <p className="text-xs font-black uppercase text-stone-600">internal console unavailable</p>
        <h1 className="max-w-3xl text-5xl font-black uppercase leading-none md:text-7xl">
          Inspection surface disabled.
        </h1>
        <div className="max-w-3xl border-l border-red-950 pl-5 text-sm leading-7 text-stone-400">
          <p>Set `NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true` locally to inspect evaluation reports.</p>
          <p>This is not authentication. It is only a local boundary marker.</p>
        </div>
      </section>
    </main>
  );
}

export function ConsoleReadError({ message }: Readonly<{ message: string }>) {
  return (
    <ConsoleShell title="Read failure.">
      <section className="border border-red-950 bg-red-950/10 p-5">
        <p className="text-xs font-black uppercase text-red-500">api read failed</p>
        <p className="mt-4 font-mono text-sm text-stone-300">{message}</p>
      </section>
    </ConsoleShell>
  );
}

import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";
import { SectionLabel } from "@schluesselkinder/ui";

const consoleEnabled = process.env.NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED === "true";

export default function AdminPage() {
  return (
    <main className="min-h-screen bg-[#060606] text-stone-100">
      <section className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-16 md:px-10">
        <SectionLabel>{masterbrand} Internal</SectionLabel>
        <h1 className="max-w-3xl text-5xl font-black uppercase leading-none md:text-7xl">
          Inspection surface.
        </h1>
        <p className="max-w-2xl text-sm leading-7 text-stone-400">
          Local read-only evaluation inspection. No authority, no mutation, no publishing controls.
        </p>
        {consoleEnabled ? (
          <Link className="w-fit border border-stone-800 px-4 py-3 text-xs font-black uppercase text-stone-300 hover:border-red-950 hover:text-red-700" href="/admin/evaluation">
            open evaluation inspection
          </Link>
        ) : (
          <p className="font-mono text-xs uppercase text-stone-600">
            NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
          </p>
        )}
      </section>
    </main>
  );
}

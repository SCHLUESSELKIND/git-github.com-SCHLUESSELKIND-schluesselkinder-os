import { masterbrand } from "@schluesselkinder/brand";
import { SectionLabel } from "@schluesselkinder/ui";

export default function AdminPage() {
  return (
    <main className="min-h-screen bg-zinc-950 text-white">
      <section className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-16 md:px-10">
        <SectionLabel>{masterbrand} Admin</SectionLabel>
        <h1 className="max-w-3xl text-4xl font-black leading-tight tracking-normal">
          Operations workspace scaffold.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-zinc-300">
          Authentication and protected workflows are intentionally outside Sprint 1.
        </p>
      </section>
    </main>
  );
}

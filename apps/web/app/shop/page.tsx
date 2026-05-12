import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../_components/BrandSymbol";
import { SectionFrame } from "../_components/SectionFrame";
import { SymbolRail } from "../_components/SymbolRail";

export const metadata: Metadata = {
  title: `Objects | ${masterbrand}`,
  description: "Closed object archive for future SCHLUESSELKINDER forms."
};

const archiveRecords = [
  {
    href: "/objects/sk-001",
    id: "SK-001",
    state: "SEALED",
    title: "BLACK HOODIE / KEY"
  },
  {
    href: "/objects/sk-002",
    id: "SK-002",
    state: "ACTIVE ARCHIVE",
    title: "ROPEMASTER HOODIE"
  }
] as const;

export default function ShopPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[0.9fr_1.1fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-8">
              <p className="text-xs font-black uppercase text-red-600">object archive</p>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" />
            </div>
            <div>
              <h1
                className="max-w-5xl break-words font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(2.55rem, 10.5vw, 8.25rem)", lineHeight: 0.84, overflowWrap: "anywhere" }}
              >
                Archiv offen. Store geschlossen.
              </h1>
              <p className="mt-8 text-xl leading-8 text-stone-300">Signal zuerst. Ware später.</p>
            </div>
            <div className="grid gap-0 border-y border-stone-800 text-xs font-black uppercase text-stone-500 md:grid-cols-3">
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">SK-001</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">BLACK HOODIE / KEY</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">TRANSACTION CLOSED</p>
            </div>
          </div>
          <Link
            className="relative flex min-h-[560px] flex-col justify-between overflow-hidden border border-stone-800 bg-black p-5 transition-colors hover:border-red-950 md:p-8"
            href="/objects/sk-001"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_26%,rgba(120,120,110,0.14),rgba(0,0,0,0)_48%)]" />
            <Image
              alt=""
              fill
              className="absolute inset-0 h-full w-full object-contain object-bottom opacity-70 brightness-[0.68] contrast-[1.1] saturate-0"
              priority
              sizes="(min-width: 768px) 54vw, 100vw"
              src="/objects/sk-001/archive-board.png"
            />
            <div className="absolute inset-0 bg-black/48" />
            <div className="flex items-start justify-between gap-8">
              <p className="relative z-10 text-xs font-black uppercase text-red-600">archive record</p>
              <BrandSymbol className="relative z-10 h-16 w-16 text-stone-500" />
            </div>
            <div className="relative z-10">
              <p className="text-xs font-black uppercase tracking-[0.45em] text-stone-600">SK-001</p>
              <h2 className="mt-8 max-w-xl break-words text-4xl font-black uppercase leading-none text-stone-100 md:text-7xl">
                <span className="block">BLACK</span>
                <span className="block">HOODIE / KEY</span>
              </h2>
            </div>
            <p className="relative z-10 max-w-sm text-xs font-black uppercase leading-5 text-stone-500">
              Object type: hoodie. Surface: black-on-black. Transaction: closed.
            </p>
          </Link>
        </div>
      </section>
      <SymbolRail labels={["SK-001", "SK-002", "BLACK-ON-BLACK", "CLOSED", "ARCHIVE"]} />
      <SectionFrame kicker="archive records" title="Object index.">
        <div className="border-y border-stone-800">
          {archiveRecords.map((record) => (
            <Link
              className="grid gap-6 border-b border-stone-800 py-8 transition-colors last:border-b-0 hover:border-red-950 md:grid-cols-[0.22fr_1fr_0.3fr]"
              href={record.href}
              key={record.id}
            >
              <p className="text-xs font-black uppercase text-red-600">{record.id}</p>
              <h2 className="break-words text-3xl font-black uppercase leading-none text-stone-100 md:text-6xl">
                {record.title}
              </h2>
              <p className="self-end text-xs font-black uppercase text-stone-500">{record.state}</p>
            </Link>
          ))}
        </div>
      </SectionFrame>
      <SectionFrame kicker="object boundary" title="Archive state.">
        <div className="border-y border-stone-800">
          <div className="grid gap-3 border-b border-stone-800 py-5 md:grid-cols-[0.35fr_1fr]">
            <p className="text-xs font-black uppercase text-stone-500">archive</p>
            <p className="text-sm font-black uppercase leading-7 text-stone-200">SCHLUESSELKINDER OBJECTS</p>
          </div>
          <div className="grid gap-3 border-b border-stone-800 py-5 md:grid-cols-[0.35fr_1fr]">
            <p className="text-xs font-black uppercase text-stone-500">visible records</p>
            <p className="text-sm font-black uppercase leading-7 text-stone-200">SK-001 / SK-002</p>
          </div>
          <div className="grid gap-3 py-5 md:grid-cols-[0.35fr_1fr]">
            <p className="text-xs font-black uppercase text-stone-500">public state</p>
            <p className="text-sm font-black uppercase leading-7 text-stone-200">Archiv offen. Transaction closed.</p>
          </div>
        </div>
      </SectionFrame>
    </main>
  );
}

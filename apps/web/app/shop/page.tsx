import type { Metadata } from "next";
import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../_components/BrandSymbol";
import { SectionFrame } from "../_components/SectionFrame";
import { SymbolRail } from "../_components/SymbolRail";

export const metadata: Metadata = {
  title: `Objects | ${masterbrand}`,
  description: "Closed object archive for future SCHLUESSELKINDER forms."
};

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
              <h1 className="max-w-5xl break-words font-black uppercase text-stone-100" style={{ fontSize: "clamp(3rem, 9vw, 8.25rem)", lineHeight: 0.82 }}>
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
            className="flex min-h-[560px] flex-col justify-between border border-stone-800 bg-[#0b0a08] p-5 transition-colors hover:border-red-950 md:p-8"
            href="/objects/sk-001"
          >
            <div className="flex items-start justify-between gap-8">
              <p className="text-xs font-black uppercase text-red-600">archive record</p>
              <BrandSymbol className="h-16 w-16 text-stone-500" />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.45em] text-stone-600">SK-001</p>
              <h2 className="mt-8 max-w-xl break-words text-4xl font-black uppercase leading-none text-stone-100 md:text-7xl">
                BLACK HOODIE / KEY
              </h2>
            </div>
            <p className="max-w-sm text-xs font-black uppercase leading-5 text-stone-500">
              Object type: hoodie. Status: archive record. Transaction: closed.
            </p>
          </Link>
        </div>
      </section>
      <SymbolRail labels={["SK-001", "KEY", "BLACK", "COTTON", "CLOSED"]} />
      <SectionFrame kicker="archive record" title="SK-001.">
        <Link
          className="grid gap-8 border-y border-stone-800 py-8 transition-colors hover:border-red-950 md:grid-cols-[0.3fr_1fr_0.5fr]"
          href="/objects/sk-001"
        >
          <p className="text-xs font-black uppercase text-red-600">SK-001</p>
          <div>
            <h2 className="break-words text-4xl font-black uppercase leading-none text-stone-100 md:text-7xl">
              BLACK HOODIE / KEY
            </h2>
            <p className="mt-5 max-w-xl text-lg leading-7 text-stone-400">
              Signal zuerst. Ware später.
            </p>
          </div>
          <p className="self-end text-xs font-black uppercase text-stone-500">archive record</p>
        </Link>
      </SectionFrame>
      <SectionFrame kicker="object boundary" title="No storefront.">
        <div className="border-y border-stone-800">
          <div className="grid gap-3 border-b border-stone-800 py-5 md:grid-cols-[0.35fr_1fr]">
            <p className="text-xs font-black uppercase text-stone-500">archive</p>
            <p className="text-sm font-black uppercase leading-7 text-stone-200">SCHLUESSELKINDER OBJECTS</p>
          </div>
          <div className="grid gap-3 border-b border-stone-800 py-5 md:grid-cols-[0.35fr_1fr]">
            <p className="text-xs font-black uppercase text-stone-500">visible record</p>
            <p className="text-sm font-black uppercase leading-7 text-stone-200">SK-001</p>
          </div>
          <div className="grid gap-3 py-5 md:grid-cols-[0.35fr_1fr]">
            <p className="text-xs font-black uppercase text-stone-500">public state</p>
            <p className="text-sm font-black uppercase leading-7 text-stone-200">Archive open. Transaction closed.</p>
          </div>
        </div>
      </SectionFrame>
    </main>
  );
}

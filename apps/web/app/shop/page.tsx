import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { BrandSymbol } from "../_components/BrandSymbol";
import { SectionFrame } from "../_components/SectionFrame";
import { SymbolRail } from "../_components/SymbolRail";
import { getStaticShopProjection } from "../../lib/registry/object-pages";

const collectiveName = "SCHLUESSELKINDER";

export const metadata: Metadata = {
  title: `Objects | ${collectiveName}`,
  description: "Closed object archive for future SCHLUESSELKINDER forms."
};

export default function ShopPage() {
  const shop = getStaticShopProjection();
  const heroObject = shop.objects[0];
  const railLabels = [...shop.objects.map((object) => object.id), ...shop.releaseCodes, "ARCHIVE", "CLOSED"];

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100svh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[0.9fr_1.1fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-8">
              <p className="text-xs font-black uppercase text-red-600">object archive</p>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" />
            </div>
            <div>
              <h1
                className="max-w-5xl font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(2.85rem, 8vw, 7.35rem)", lineHeight: 0.84 }}
              >
                <span className="block">Archiv offen.</span>
                <span className="block">Store geschlossen.</span>
              </h1>
              <p className="mt-8 text-xl leading-8 text-stone-300">Signal zuerst. Ware später.</p>
            </div>
            <div className="grid gap-0 border-y border-stone-800 text-xs font-black uppercase text-stone-500 md:grid-cols-3">
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">{heroObject.id}</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">{heroObject.title}</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">TRANSACTION CLOSED</p>
            </div>
          </div>
          <Link
            className="group relative flex min-h-[560px] flex-col justify-between overflow-hidden border border-stone-800 bg-black p-5 transition-colors duration-300 hover:border-red-950 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:p-8"
            href={heroObject.href}
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_26%,rgba(120,120,110,0.14),rgba(0,0,0,0)_48%)]" />
            <Image
              alt=""
              fill
              className="absolute inset-0 h-full w-full object-contain object-bottom opacity-70 brightness-[0.68] contrast-[1.1] saturate-0 transition-transform duration-700 group-hover:scale-[1.015] motion-reduce:transition-none motion-reduce:group-hover:scale-100"
              priority
              sizes="(min-width: 768px) 54vw, 100vw"
              src={heroObject.boardSrc}
            />
            <div className="absolute inset-0 bg-black/48" />
            <div className="flex items-start justify-between gap-8">
              <p className="relative z-10 text-xs font-black uppercase text-red-600">archive record</p>
              <BrandSymbol className="relative z-10 h-16 w-16 text-stone-500" />
            </div>
            <div className="relative z-10">
              <p className="text-xs font-black uppercase tracking-[0.45em] text-stone-600">{heroObject.id}</p>
              <h2 className="mt-8 max-w-xl break-words text-4xl font-black uppercase leading-[0.9] text-stone-100 transition-colors duration-300 group-hover:text-stone-200 md:text-5xl lg:text-6xl">
                {heroObject.title}
              </h2>
            </div>
            <p className="relative z-10 max-w-sm text-xs font-black uppercase leading-5 text-stone-500">
              Object class: {heroObject.objectClass}. Archive class: {heroObject.archiveClass}. Transaction: closed.
            </p>
          </Link>
        </div>
      </section>
      <SymbolRail labels={railLabels} />
      <SectionFrame kicker="archive records" title="Object index.">
        <div className="border-y border-stone-800">
          {shop.objects.map((record) => (
            <Link
              className="grid gap-6 border-b border-stone-800 py-8 transition-colors duration-300 last:border-b-0 hover:border-red-950 hover:bg-stone-950/20 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:grid-cols-[0.22fr_1fr_0.3fr]"
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
            <p className="text-sm font-black uppercase leading-7 text-stone-200">{shop.objects.map((object) => object.id).join(" / ")}</p>
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

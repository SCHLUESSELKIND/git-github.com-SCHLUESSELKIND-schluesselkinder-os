import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { BrandSymbol } from "../_components/BrandSymbol";
import { SectionFrame } from "../_components/SectionFrame";
import { SymbolRail } from "../_components/SymbolRail";
import { getStaticShopProjection } from "../../lib/registry/object-pages";

const collectiveName = "SCHLUESSELKINDER";
const description = "Closed SCHLUESSELKINDER object archive. Public records only, transactions closed.";
const title = `Objects | ${collectiveName}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/shop"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER object archive board", height: 1024, url: "/objects/sk-002/archive-board.png", width: 1536 }],
    title,
    url: "/shop"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: ["/objects/sk-002/archive-board.png"],
    title
  }
};

export default function ShopPage() {
  const shop = getStaticShopProjection();
  const railLabels = [...shop.objects.map((object) => object.id), ...shop.releaseCodes, "ARCHIVE", "CLOSED"];

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100svh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[0.82fr_1.18fr] md:px-8 md:py-14">
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
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">{shop.objects.length} records</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">{shop.objects.map((object) => object.id).join(" / ")}</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0">TRANSACTION CLOSED</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {shop.objects.map((record, index) => (
              <Link
                className="group grid min-h-[540px] grid-rows-[1fr_auto] overflow-hidden border border-stone-800 bg-black transition-colors duration-300 hover:border-red-950 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900"
                href={record.href}
                key={record.id}
              >
                <figure className="relative min-h-[360px] overflow-hidden bg-[#030302]">
                  <Image
                    alt={record.boardAlt}
                    className="object-contain opacity-82 brightness-[0.72] contrast-[1.12] saturate-0 transition-transform duration-700 group-hover:scale-[1.012] motion-reduce:transition-none motion-reduce:group-hover:scale-100"
                    fill
                    priority={index === 0}
                    sizes="(min-width: 768px) 30vw, 100vw"
                    src={record.boardSrc}
                  />
                  <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.05),rgba(0,0,0,0.46))]" />
                </figure>
                <div className="grid gap-8 border-t border-stone-800 p-5 md:p-6">
                  <div className="flex items-start justify-between gap-6">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.42em] text-red-600">{record.id}</p>
                      <h2 className="mt-5 break-words text-3xl font-black uppercase leading-[0.9] text-stone-100 md:text-4xl">
                        {record.title}
                      </h2>
                    </div>
                    <p className="text-right text-xs font-black uppercase text-stone-600">{record.year}</p>
                  </div>
                  <div className="grid gap-2 border-t border-stone-800 pt-4 text-xs font-black uppercase text-stone-500">
                    <p>archive class: <span className="text-stone-300">{record.archiveClass}</span></p>
                    <p>surface: <span className="text-stone-300">{record.surface}</span></p>
                    <p>status: <span className="text-stone-300">{record.state}</span></p>
                    <p>transaction: <span className="text-stone-300">{record.transaction}</span></p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
      <SymbolRail labels={railLabels} />
      <SectionFrame kicker="archive records" title="Object index.">
        <div className="border-y border-stone-800">
          {shop.objects.map((record) => (
            <Link
              className="grid gap-6 border-b border-stone-800 py-8 transition-colors duration-300 last:border-b-0 hover:border-red-950 hover:bg-stone-950/20 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:grid-cols-[0.18fr_0.34fr_1fr_0.22fr] md:items-end"
              href={record.href}
              key={record.id}
            >
              <div>
                <p className="text-xs font-black uppercase text-red-600">{record.id}</p>
                <p className="mt-3 text-xs font-black uppercase text-stone-600">{record.archiveClass}</p>
              </div>
              <figure className="relative aspect-[16/10] overflow-hidden border border-stone-900 bg-black md:aspect-[4/3]">
                <Image
                  alt=""
                  className="object-cover opacity-70 brightness-[0.72] contrast-[1.15] saturate-0"
                  fill
                  sizes="(min-width: 768px) 22vw, 100vw"
                  src={record.boardSrc}
                />
              </figure>
              <div>
                <h2 className="break-words text-3xl font-black uppercase leading-none text-stone-100 md:text-5xl">
                  {record.title}
                </h2>
                <p className="mt-5 text-xs font-black uppercase leading-5 text-stone-500">
                  {record.objectClass} / {record.surface} / {record.releaseCode ?? "NO RELEASE REFERENCE"}
                </p>
              </div>
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

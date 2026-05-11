import type { Metadata } from "next";
import Link from "next/link";
import { brandAssets, masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { EditorialImage } from "../../_components/EditorialImage";
import { SectionFrame } from "../../_components/SectionFrame";
import { SymbolRail } from "../../_components/SymbolRail";

export const metadata: Metadata = {
  title: `SK-001 BLACK HOODIE / KEY | ${masterbrand}`,
  description: "SCHLUESSELKINDER object archive record SK-001."
};

const metadataRows = [
  ["record", "SK-001"],
  ["object", "BLACK HOODIE / KEY"],
  ["mark", "KEY"],
  ["material note", "Key mark. Cotton study."],
  ["boundary", "Kein Checkout. Keine Verfügbarkeitserzählung."]
] as const;

export default function Sk001Page() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[0.95fr_1.05fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-8">
              <p className="text-xs font-black uppercase text-red-600">OBJECT ARCHIVE</p>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.45em] text-stone-500">SK-001</p>
              <h1 className="mt-8 max-w-5xl font-black uppercase text-stone-100" style={{ fontSize: "clamp(3.6rem, 9vw, 8.5rem)", lineHeight: 0.82 }}>
                BLACK HOODIE / KEY
              </h1>
              <div className="mt-8 max-w-xl text-xl leading-8 text-stone-300">
                <p>Signal zuerst. Ware später.</p>
                <p>Schwarz. Schwer. Spät.</p>
              </div>
            </div>
            <Link className="w-fit border border-stone-800 px-4 py-3 text-xs font-black uppercase text-stone-400 hover:border-red-950 hover:text-red-700" href="/kontakt">
              Manual inquiry only.
            </Link>
          </div>
          <EditorialImage
            alt="Dungeon concrete campaign environment for SK-001"
            caption="archive environment"
            className="min-h-[560px]"
            imageClassName="image-noir object-[58%_48%]"
            priority
            src={brandAssets.campaignDungeonChair}
            symbol="key"
          />
        </div>
      </section>
      <SymbolRail labels={["SK-001", "KEY", "BLACK", "COTTON", "ARCHIVE"]} />
      <SectionFrame kicker="archive metadata" title="No storefront.">
        <div className="border-y border-stone-800">
          {metadataRows.map(([label, value]) => (
            <div className="grid gap-3 border-b border-stone-800 py-5 last:border-b-0 md:grid-cols-[0.35fr_1fr]" key={label}>
              <p className="text-xs font-black uppercase text-stone-500">{label}</p>
              <p className="text-sm font-black uppercase leading-7 text-stone-200">{value}</p>
            </div>
          ))}
        </div>
      </SectionFrame>
    </main>
  );
}

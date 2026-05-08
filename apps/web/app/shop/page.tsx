import type { Metadata } from "next";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { BrandSymbol } from "../_components/BrandSymbol";
import { SectionFrame } from "../_components/SectionFrame";
import { ShopPreview } from "../_components/ShopPreview";
import { SymbolRail } from "../_components/SymbolRail";

export const metadata: Metadata = {
  title: `Shop | ${masterbrand}`,
  description: "Editorial preview for future SCHLUESSELKINDER drops."
};

export default function ShopPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[0.9fr_1.1fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-8">
              <p className="text-xs font-black uppercase text-red-600">{masterbrand} shop</p>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" />
            </div>
            <div>
              <h1 className="max-w-5xl font-black uppercase text-stone-100" style={{ fontSize: "clamp(3.75rem, 10vw, 9rem)", lineHeight: 0.82 }}>
                {seedCopy.shopSignal.en}
              </h1>
              <p className="mt-8 text-xl leading-8 text-stone-300">{seedCopy.shopSignal.de}</p>
            </div>
            <div className="grid gap-0 border-y border-stone-800 text-xs font-black uppercase text-stone-100 md:grid-cols-3">
              {seedCopy.commerceBoundary.map((line) => (
                <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:last:border-r-0" key={line}>
                  {line}
                </p>
              ))}
            </div>
          </div>
          <div className="flex min-h-[560px] flex-col justify-between border border-stone-800 bg-[#0b0a08] p-5 md:p-8">
            <p className="text-xs font-black uppercase text-red-600">future object system</p>
            <div className="grid gap-4">
              <div className="h-px bg-stone-800" />
              <div className="h-24 border-x border-stone-800" />
              <div className="h-px bg-stone-800" />
            </div>
            <div className="grid gap-8 md:grid-cols-[120px_1fr]">
              <BrandSymbol className="h-24 w-24 text-stone-600" />
              <p className="max-w-md text-3xl font-black uppercase leading-none text-stone-100">
                {seedCopy.shopArchive.en}
              </p>
            </div>
          </div>
        </div>
      </section>
      <SymbolRail labels={["NO CART", "NO STOCK", "NO SALE", "OBJECT", "LATER"]} />
      <SectionFrame kicker="streetwear signal" title="Drop sheet.">
        <ShopPreview />
        <p className="mt-8 max-w-2xl text-lg leading-7 text-stone-500">The first drop is still closed.</p>
      </SectionFrame>
    </main>
  );
}

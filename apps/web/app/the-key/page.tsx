import type { Metadata } from "next";
import { brandAssets, masterbrand, theKeyTool } from "@schluesselkinder/brand";
import { BrandSymbol } from "../_components/BrandSymbol";
import { GlyphRail } from "../_components/GlyphRail";
import { ManifestLine } from "../_components/ManifestLine";
import { RotatedMeta } from "../_components/RotatedMeta";
import { SectionFrame } from "../_components/SectionFrame";

const description = "THE KEY. SCHLUESSELKINDER system tool for safer raves. iOS.";

export const metadata: Metadata = {
  alternates: {
    canonical: "/the-key"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER rune key mark", height: 1024, url: brandAssets.runeKeyMark, width: 1024 }],
    title: `${theKeyTool.name} — ${masterbrand}`,
    url: "/the-key"
  },
  title: theKeyTool.name,
  twitter: {
    card: "summary_large_image",
    description,
    images: [brandAssets.runeKeyMark],
    title: `${theKeyTool.name} — ${masterbrand}`
  }
};

export default function TheKeyPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="relative overflow-hidden border-b border-stone-800">
        <div className="ambient-pulse pointer-events-none absolute -left-24 top-24 h-96 w-96 rounded-full bg-red-950/18 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-5 py-16 md:px-8 md:py-24">
          <div className="flex items-start justify-between gap-8">
            <p className="text-xs font-black uppercase text-red-600">{theKeyTool.role}</p>
            <RotatedMeta>{theKeyTool.code} / rune index</RotatedMeta>
          </div>
          <div className="mt-10 grid items-end gap-10 md:grid-cols-[1fr_auto]">
            <h1
              className="break-words font-black uppercase text-stone-100"
              style={{ fontSize: "clamp(3rem, 13vw, 12rem)", lineHeight: 0.8, overflowWrap: "anywhere" }}
            >
              {theKeyTool.name}
            </h1>
            <BrandSymbol className="h-24 w-24 text-stone-100/80 md:h-36 md:w-36" />
          </div>
          <div className="mt-10 grid max-w-2xl gap-3 border-l border-stone-700 pl-5 text-lg leading-8 text-stone-300 md:text-xl">
            <p>{theKeyTool.lines[0].de}</p>
            <p>{theKeyTool.lines[0].en}</p>
          </div>
        </div>
      </section>

      <GlyphRail items={[theKeyTool.code, ...theKeyTool.signals.map((signal) => signal.code), theKeyTool.platform]} />

      <SectionFrame kicker="protocol" title="Vier Signale. Eine Nacht.">
        <div className="border-y border-stone-800">
          {theKeyTool.signals.map((signal) => (
            <article className="grid gap-6 border-b border-stone-800 py-7 last:border-b-0 md:grid-cols-[0.22fr_1fr]" key={signal.code}>
              <div className="text-xs font-black uppercase">
                <p className="text-red-600">{signal.code}</p>
              </div>
              <div>
                <h3 className="break-words text-4xl font-black uppercase leading-[0.9] text-stone-100 md:text-6xl">
                  {signal.title}
                </h3>
                <div className="mt-5 grid gap-1 text-sm font-black uppercase text-stone-400">
                  <p>{signal.de}</p>
                  <p className="text-stone-600">{signal.en}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </SectionFrame>

      <SectionFrame kicker="system boundary" title="Kein Lifestyle. Ein Protokoll.">
        <div className="border-t border-stone-800">
          {theKeyTool.lines.map((line) => (
            <ManifestLine de={line.de} en={line.en} key={line.de} />
          ))}
        </div>
        <div className="mt-10 grid gap-3 text-xs font-black uppercase text-stone-500">
          <p>
            <span className="text-red-600">{theKeyTool.platform}</span>
            <span className="px-3 text-stone-700">/</span>
            {theKeyTool.status}
          </p>
          <p className="text-stone-600">{theKeyTool.toggle}</p>
        </div>
      </SectionFrame>

      <SectionFrame kicker="surface" title="Der Club trägt den Schlüssel.">
        <div className="grid gap-3 border-t border-stone-800 pt-8 text-lg leading-8 text-stone-300 md:text-xl">
          <p>THE KEY lebt im AntiSoberSoberClub. Magazin, Shop, Werkzeug.</p>
          <p className="text-stone-500">THE KEY lives inside the AntiSoberSoberClub. Magazine, shop, tool.</p>
        </div>
        <a
          className="mt-8 inline-block border border-red-950 px-5 py-3 text-sm font-black uppercase text-stone-100 transition-colors duration-300 hover:border-red-800 hover:bg-red-950/10 hover:text-red-600 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900"
          href={theKeyTool.surfaceUrl}
          rel="noopener noreferrer"
          target="_blank"
        >
          {theKeyTool.surfaceLabel}
        </a>
      </SectionFrame>

      <section className="border-t border-stone-800">
        <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
          <div className="max-w-5xl">
            {["CHECK IN.", "CHECK OUT.", "NIEMAND GEHT ALLEIN."].map((line) => (
              <p className="border-b border-stone-800 py-5 text-4xl font-black uppercase leading-none text-stone-100 md:text-7xl" key={line}>
                {line}
              </p>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

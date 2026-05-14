import type { Metadata } from "next";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { ManifestLine } from "../_components/ManifestLine";
import { SectionFrame } from "../_components/SectionFrame";

const description = "SCHLUESSELKINDER manifesto.";
const previewImage = "/brand/campaign-dungeon-chair.png";
const title = `About | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/about"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER dark campaign room", height: 1400, url: previewImage, width: 1400 }],
    title,
    url: "/about"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title
  }
};

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow={`${masterbrand} manifesto`} title="Built for after.">
        <p>Gebaut fuer danach.</p>
        <p>Music, garments, residue.</p>
      </EditorialHero>
      <GlyphRail items={["NO DAY", "NO MALL", "NO FEED", "ROOM", "RITUAL", "SK"]} />
      <SectionFrame kicker="manifesto" title="Short. Cold. Held back.">
        <div className="border-t border-stone-800">
          {seedCopy.about.map((line) => (
            <ManifestLine de={line.de} en={line.en} key={line.en} />
          ))}
        </div>
      </SectionFrame>
      <section className="border-t border-stone-800">
        <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
          <div className="max-w-5xl">
            {seedCopy.manifesto.map((line) => (
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

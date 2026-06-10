import Link from "next/link";
import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { ArtistSignal } from "../_components/ArtistSignal";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { SectionFrame } from "../_components/SectionFrame";

const description = "SCHLUESSELKINDER artist archive.";
const previewImage = "/brand/campaign-dungeon-chair.png";
const title = `Artists | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/artists"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER dark campaign room", height: 1400, url: previewImage, width: 1400 }],
    title,
    url: "/artists"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title
  }
};

export default function ArtistsPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero
        aside={
          <div className="border border-stone-800 p-5 text-sm font-black uppercase text-stone-500 md:p-8">
            <p>archive status</p>
            <p className="mt-24 text-red-600">two districts active</p>
          </div>
        }
        eyebrow={`${masterbrand} archive`}
        title="Artists as pressure."
      >
        <p>Kuenstler als Spur.</p>
      </EditorialHero>
      <GlyphRail items={["ARTIST", "ROOM", "BODY", "SOUND", "TRACE", "SK"]} />
      <SectionFrame kicker="district 001" title="SHIBARI KAWAII.">
        <ArtistSignal />
      </SectionFrame>
      <SectionFrame kicker="district 002" title="SNUFFRAGGA SOUNDSYSTEM.">
        <Link
          href="/artists/snuffragga"
          className="inline-block border border-stone-100 px-5 py-3 font-black uppercase tracking-[0.22em] text-stone-100 transition hover:bg-stone-100 hover:text-stone-900"
        >
          enter district →
        </Link>
      </SectionFrame>
    </main>
  );
}

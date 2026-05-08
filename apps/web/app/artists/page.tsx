import type { Metadata } from "next";
import { firstArtist, masterbrand } from "@schluesselkinder/brand";
import { ArtistSignal } from "../_components/ArtistSignal";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { SectionFrame } from "../_components/SectionFrame";

export const metadata: Metadata = {
  title: `Artists | ${masterbrand}`,
  description: "SCHLUESSELKINDER artist archive."
};

export default function ArtistsPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero
        aside={
          <div className="border border-stone-800 p-5 text-sm font-black uppercase text-stone-500 md:p-8">
            <p>archive status</p>
            <p className="mt-24 text-red-600">one artist active</p>
          </div>
        }
        eyebrow={`${masterbrand} archive`}
        title="Artists as pressure."
      >
        <p>Kuenstler als Spur.</p>
        <p>No portfolio wall. No clean biography.</p>
      </EditorialHero>
      <GlyphRail items={["ARTIST", "ROOM", "BODY", "SOUND", "TRACE", "SK"]} />
      <SectionFrame kicker="active signal" title={firstArtist.role}>
        <ArtistSignal />
      </SectionFrame>
    </main>
  );
}

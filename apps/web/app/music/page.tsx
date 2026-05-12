import type { Metadata } from "next";
import { firstArtist, masterbrand, seedCopy } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { ManifestLine } from "../_components/ManifestLine";
import { SectionFrame } from "../_components/SectionFrame";
import { TrackList } from "../_components/TrackList";

export const metadata: Metadata = {
  title: `Sound Archive | ${masterbrand}`,
  description: "SCHLUESSELKINDER sound archive."
};

export default function MusicPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="MUSIK / ARCHIV" title="SOUND ARCHIVE.">
        <p>{seedCopy.musicSignal.de}</p>
        <p>{seedCopy.musicSignal.en}</p>
      </EditorialHero>
      <GlyphRail items={["SND-001", "SND-002", "SND-003", "ROOM", "WIRE", "RED"]} />
      <SectionFrame kicker="sound records" title="Public signals.">
        <TrackList mode="archive" />
      </SectionFrame>
      <SectionFrame kicker={firstArtist.archiveCode} title="No feed. No noise.">
        <div className="border-t border-stone-800">
          <ManifestLine de="Nacht bleibt Material." en="Night remains material." />
          <ManifestLine de="Drei Signale. Keine Erzählung." en="Three signals. No explanation." />
        </div>
      </SectionFrame>
    </main>
  );
}

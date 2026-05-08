import type { Metadata } from "next";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { ManifestLine } from "../_components/ManifestLine";
import { SectionFrame } from "../_components/SectionFrame";
import { TrackList } from "../_components/TrackList";

export const metadata: Metadata = {
  title: `Music | ${masterbrand}`,
  description: "SCHLUESSELKINDER music archive."
};

export default function MusicPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow={`${masterbrand} music`} title="Sound after light.">
        <p>{seedCopy.musicSignal.de}</p>
        <p>{seedCopy.musicSignal.en}</p>
      </EditorialHero>
      <GlyphRail items={["001", "002", "003", "ROOM", "WIRE", "RED"]} />
      <SectionFrame kicker="archive" title="Tracks as artifacts.">
        <TrackList />
      </SectionFrame>
      <SectionFrame kicker="method" title="No feed. No noise.">
        <div className="border-t border-stone-800">
          <ManifestLine de="Nacht bleibt Material." en="Night remains material." />
          <ManifestLine de="Jeder Track ein kalter Abdruck." en="Each track a cold imprint." />
        </div>
      </SectionFrame>
    </main>
  );
}

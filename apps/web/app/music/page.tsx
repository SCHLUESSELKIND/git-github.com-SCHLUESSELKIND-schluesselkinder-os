import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { ManifestLine } from "../_components/ManifestLine";
import { SectionFrame } from "../_components/SectionFrame";
import { getStaticMusicPageProjection } from "../../lib/registry/music-page";

const description = "Static sound archive for SHIBARI KAWAII, ROPEMASTER LP, and public release signals.";
const previewImage = "/brand/campaign-dungeon-chair.png";
const title = `Sound Archive | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/music"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER sound archive campaign room", height: 1400, url: previewImage, width: 1400 }],
    title,
    url: "/music"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title
  }
};

export default function MusicPage() {
  const music = getStaticMusicPageProjection();
  const glyphItems = [
    ...music.releases.map((release) => release.releaseCode),
    ...music.releases.flatMap((release) => release.signals.map((signal) => signal.trackCode)),
    ...music.objects.map((object) => object.objectCode)
  ];

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="MUSIK / ARCHIV" title="SOUND ARCHIVE.">
        <p>{music.artist.canonicalName}</p>
        {music.releases.map((release) => (
          <p key={release.releaseKey}>
            {release.displayTitle} / {release.releaseCode}
          </p>
        ))}
      </EditorialHero>
      <GlyphRail items={glyphItems} />
      <SectionFrame kicker="sound records" title="Public signals.">
        <div className="border-y border-stone-800">
          {music.releases.map((release) => (
            <article className="border-b border-stone-800 py-7 last:border-b-0" key={release.releaseKey}>
              <div className="grid gap-5 md:grid-cols-[104px_1fr_0.7fr]">
                <div className="text-xs font-black uppercase md:pt-2">
                  <p className="text-red-600">{release.releaseCode}</p>
                  <p className="mt-3 text-stone-600">{release.role}</p>
                </div>
                <div>
                  <h3 className="break-words text-5xl font-black uppercase leading-[0.88] text-stone-100 md:text-6xl">
                    {release.displayTitle}
                  </h3>
                  <p className="mt-4 text-sm font-black uppercase text-stone-500">{music.artist.canonicalName}</p>
                </div>
                <div className="text-lg leading-7 text-stone-400 md:self-end">
                  <p className="text-sm font-black uppercase text-stone-500">signals</p>
                  <p className="mt-2 text-sm font-black uppercase text-stone-200">{release.signals.length}</p>
                </div>
              </div>
              <div className="mt-8 border-t border-stone-800">
                {release.signals.map((signal) => (
                  <div className="grid gap-5 border-b border-stone-800 py-6 last:border-b-0 md:grid-cols-[104px_1fr_0.7fr]" key={signal.trackKey}>
                    <div className="text-xs font-black uppercase md:pt-2">
                      <p className="text-red-600">{signal.trackCode}</p>
                    </div>
                    <div>
                      <h4 className="break-words text-4xl font-black uppercase leading-[0.9] text-stone-100 md:text-5xl">
                        {signal.title}
                      </h4>
                    </div>
                    <div className="text-lg leading-7 text-stone-400 md:self-end">
                      <p className="text-sm font-black uppercase text-stone-500">{release.displayTitle}</p>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </SectionFrame>
      <SectionFrame kicker={music.artist.canonicalName} title="No feed. No noise.">
        <div className="border-t border-stone-800">
          <ManifestLine de="LP bleibt Anker." en="The LP remains the anchor." />
          <ManifestLine de="Signale bleiben Signale." en="Signals remain signals." />
        </div>
      </SectionFrame>
    </main>
  );
}

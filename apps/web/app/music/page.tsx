import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
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

function formatRole(role: string) {
  return role.replace(/-/g, " ");
}

function formatSignals(count: number) {
  return count === 1 ? "1 signal" : `${count} signals`;
}

export default function MusicPage() {
  const music = getStaticMusicPageProjection();
  const glyphItems = [
    ...music.releases.map((release) => release.releaseCode),
    ...music.releases.flatMap((release) => release.signals.map((signal) => signal.trackCode)),
    ...music.objects.map((object) => object.objectCode),
    "ARCHIVE"
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
            <article
              className="border-b border-stone-800 py-12 last:border-b-0 md:py-16"
              key={release.releaseKey}
            >
              <div className="grid gap-6 md:grid-cols-[120px_1fr_0.6fr] md:gap-5">
                <div className="text-xs font-black uppercase md:pt-1">
                  <p className="text-red-600">{release.releaseCode}</p>
                  <p className="mt-3 text-stone-600">{formatRole(release.role)}</p>
                </div>
                <div>
                  <h3 className="break-words text-6xl font-black uppercase leading-[0.85] tracking-tight text-stone-100 md:text-7xl">
                    {release.displayTitle}
                  </h3>
                  <p className="mt-6 text-sm font-black uppercase text-stone-500 md:mt-8">
                    {music.artist.canonicalName}
                  </p>
                </div>
                <div className="text-xs font-black uppercase text-stone-500 md:self-end md:text-right">
                  <p>{formatSignals(release.signals.length)}</p>
                </div>
              </div>
              <ol className="mt-10 list-none border-t border-stone-900 md:mt-14">
                {release.signals.map((signal) => (
                  <li
                    className="grid gap-4 border-b border-stone-900 py-5 last:border-b-0 md:grid-cols-[120px_1fr] md:gap-6 md:py-6"
                    key={signal.trackKey}
                  >
                    <p className="text-xs font-black uppercase text-red-600 md:pt-2">{signal.trackCode}</p>
                    <h4 className="break-words text-3xl font-black uppercase leading-[0.95] text-stone-200 md:text-4xl">
                      {signal.title}
                    </h4>
                  </li>
                ))}
              </ol>
            </article>
          ))}
        </div>
      </SectionFrame>
    </main>
  );
}

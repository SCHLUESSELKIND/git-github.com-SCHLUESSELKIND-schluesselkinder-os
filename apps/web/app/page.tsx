import type { Metadata } from "next";
import Link from "next/link";
import { brandAssets, masterbrand, seedCopy } from "@schluesselkinder/brand";
import { ArtistSignal } from "./_components/ArtistSignal";
import { BrandSymbol } from "./_components/BrandSymbol";
import { EditorialImage } from "./_components/EditorialImage";
import { ManifestLine } from "./_components/ManifestLine";
import { RotatedMeta } from "./_components/RotatedMeta";
import { SectionFrame } from "./_components/SectionFrame";
import { ShopPreview } from "./_components/ShopPreview";
import { SymbolRail } from "./_components/SymbolRail";
import { getStaticMusicPageProjection } from "../lib/registry/music-page";

const description = "Dark premium underground archive for SHIBARI KAWAII, ROPEMASTER, and SCHLUESSELKINDER objects.";
const previewImage = "/brand/campaign-dungeon-chair.png";

function formatRole(role: string) {
  return role.replace(/-/g, " ");
}

function formatSignals(count: number) {
  return count === 1 ? "1 signal" : `${count} signals`;
}

export const metadata: Metadata = {
  alternates: {
    canonical: "/"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER dark campaign room", height: 1400, url: previewImage, width: 1400 }],
    title: masterbrand,
    url: "/"
  },
  title: masterbrand,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title: masterbrand
  }
};

export default function Home() {
  const music = getStaticMusicPageProjection();
  const publicSignals = music.releases.flatMap((release) => release.signals);
  const railLabels = [
    music.releases[0]?.releaseCode ?? "SKR-LP-001",
    ...publicSignals.map((signal) => signal.trackCode),
    ...music.objects.map((object) => object.objectCode),
    "ARCHIVE"
  ];

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="relative min-h-[calc(100svh-57px)] overflow-hidden border-b border-stone-800">
        <EditorialImage
          alt="Dungeon concrete room with a rope-bound chair"
          className="!absolute inset-0 h-full w-full border-0"
          imageClassName="image-noir"
          priority
          src={brandAssets.campaignDungeonChair}
          symbol="none"
        />
        <div className="absolute inset-0 bg-black/62" />
        <div className="ambient-pulse pointer-events-none absolute -right-24 top-16 h-96 w-96 rounded-full bg-red-950/18 blur-3xl" />
        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#070605] to-transparent" />
        <div className="relative mx-auto grid min-h-[calc(100svh-57px)] max-w-7xl grid-rows-[1fr_auto] px-5 py-8 md:px-8">
          <div className="flex items-start justify-between gap-8">
            <p className="text-xs font-black uppercase text-red-600">{music.artist.canonicalName}</p>
            <BrandSymbol className="h-16 w-16 text-stone-100/80" />
          </div>
          <div className="grid items-end gap-8 md:grid-cols-[auto_1fr_120px]">
            <div>
              <h1
                className="max-w-5xl break-words font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(3rem, 14vw, 13rem)", lineHeight: 0.8, overflowWrap: "anywhere" }}
              >
                {seedCopy.hero.de}
              </h1>
              <div className="mt-8 grid max-w-2xl gap-3 border-l border-stone-700 pl-5 text-lg leading-8 text-stone-300 md:text-xl">
                <p>{seedCopy.systemFragments.afterhours}</p>
                <p>{seedCopy.hero.en}</p>
              </div>
            </div>
            <div className="hidden md:block" />
            <RotatedMeta>{music.releases[0]?.releaseCode ?? "SKR-LP-001"} / rune index</RotatedMeta>
          </div>
        </div>
      </section>

      <SymbolRail labels={railLabels} />

      <SectionFrame kicker="system identity" title="Cold room. Red trace.">
        <div className="border-t border-stone-800">
          {seedCopy.collective.map((line) => (
            <ManifestLine de={line.de} en={line.en} key={line.en} />
          ))}
          <ManifestLine de="District 001. District 002." en="One archive. Two districts." />
        </div>
      </SectionFrame>

      <SectionFrame kicker="artist dossier" title="Body as signal.">
        <ArtistSignal />
      </SectionFrame>

      <SectionFrame kicker="release artifacts" title="Public signals.">
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
        <Link className="mt-8 inline-block border border-red-950 px-5 py-3 text-sm font-black uppercase text-stone-100 transition-colors duration-300 hover:border-red-800 hover:bg-red-950/10 hover:text-red-600 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900" href="/music">
          Sound archive
        </Link>
      </SectionFrame>

      <SectionFrame kicker="object archive" title="Objects later.">
        <ShopPreview />
      </SectionFrame>

      <section className="border-t border-stone-800">
        <div className="mx-auto max-w-7xl px-5 py-14 md:px-8 md:py-20">
          <div className="max-w-5xl">
            {seedCopy.manifesto
              .filter((line) => line !== "NO BRIGHT ROOM." && line !== "NACHT BLEIBT MATERIAL.")
              .map((line) => (
                <p
                  className="border-b border-stone-800 py-5 text-4xl font-black uppercase leading-none tracking-tight text-stone-100 md:text-7xl"
                  key={line}
                >
                  {line}
                </p>
              ))}
          </div>
        </div>
      </section>
    </main>
  );
}

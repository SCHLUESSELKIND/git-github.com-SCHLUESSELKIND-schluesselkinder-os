import type { Metadata } from "next";
import Link from "next/link";
import { brandAssets, masterbrand, seedCopy, theKeyTool } from "@schluesselkinder/brand";
import { BrandSymbol } from "./_components/BrandSymbol";
import { EditorialImage } from "./_components/EditorialImage";
import { ManifestLine } from "./_components/ManifestLine";
import { ReleaseStatus } from "./_components/ReleaseStatus";
import { RotatedMeta } from "./_components/RotatedMeta";
import { SectionFrame } from "./_components/SectionFrame";
import { SymbolRail } from "./_components/SymbolRail";
import { getStaticMusicPageProjection } from "../lib/registry/music-page";
import { latestReleaseFor } from "./_releases";

// Refresh the cached HTML every 60s so the GRÜNLICHTBEZIRK transmission block
// flips from "incoming" to "in transmission" within a minute of the release
// window opening, without any manual deploy on T-0.
export const revalidate = 60;

const SIGNAL_GREEN = "#5FB047";

const description =
  "Dark underground label archive. District 001 SHIBARI KAWAII. District 002 SNUFFRAGGA SOUNDSYSTEM.";
const previewImage = "/brand/campaign-dungeon-chair.png";

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
  const anchorRelease = music.releases[0];
  const transmission = latestReleaseFor("snuffragga");
  const railLabels = [
    "001",
    music.artist.canonicalName,
    "002",
    "SNUFFRAGGA SOUNDSYSTEM",
    anchorRelease?.releaseCode ?? "SKR-LP-001",
    "RELEASE-001"
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
        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#070605] to-transparent" />
        <div className="relative mx-auto grid min-h-[calc(100svh-57px)] max-w-7xl grid-rows-[1fr_auto] px-5 py-8 md:px-8">
          <div className="flex items-start justify-between gap-8">
            <p className="text-xs font-black uppercase text-red-600">two districts · one archive</p>
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
              <p className="mt-8 max-w-2xl border-l border-stone-700 pl-5 text-lg leading-8 text-stone-300 md:text-xl">
                {seedCopy.hero.en}
              </p>
            </div>
            <div className="hidden md:block" />
            <RotatedMeta>001 / 002 / rune index</RotatedMeta>
          </div>
        </div>
      </section>

      <SymbolRail labels={railLabels} />

      <SectionFrame kicker="label index" title="Two districts.">
        <div className="border-y border-stone-800">
          <Link
            className="group grid gap-6 border-b border-stone-800 py-12 transition-colors duration-300 hover:bg-stone-950/25 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:grid-cols-[120px_1fr_0.6fr] md:gap-5 md:py-16"
            href={`/artists/${music.artist.slug}`}
          >
            <p className="text-xs font-black uppercase text-red-600 md:pt-1">001</p>
            <div>
              <h3 className="break-words text-5xl font-black uppercase leading-[0.85] tracking-tight text-stone-100 transition-colors duration-300 group-hover:text-stone-200 md:text-7xl">
                {music.artist.canonicalName}
              </h3>
              <p className="mt-6 text-sm font-black uppercase text-stone-500 md:mt-8">
                {anchorRelease ? `${anchorRelease.displayTitle} · ${anchorRelease.releaseCode}` : "ARCHIVE"}
              </p>
            </div>
            <p className="text-xs font-black uppercase text-stone-500 md:self-end md:text-right">
              body as signal →
            </p>
          </Link>
          <Link
            className="group grid gap-6 py-12 transition-colors duration-300 hover:bg-stone-950/25 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:grid-cols-[120px_1fr_0.6fr] md:gap-5 md:py-16"
            href="/artists/snuffragga"
          >
            <p className="text-xs font-black uppercase md:pt-1" style={{ color: SIGNAL_GREEN }}>
              002
            </p>
            <div>
              <h3 className="break-words text-5xl font-black uppercase leading-[0.85] tracking-tight text-stone-100 transition-colors duration-300 group-hover:text-stone-200 md:text-7xl">
                SNUFFRAGGA SOUNDSYSTEM
              </h3>
              <p className="mt-6 text-sm font-black uppercase text-stone-500 md:mt-8">
                RELEASE-001 · GRÜNLICHTBEZIRK
              </p>
            </div>
            <p className="text-xs font-black uppercase text-stone-500 md:self-end md:text-right">
              bass pressure →
            </p>
          </Link>
        </div>
      </SectionFrame>

      {transmission ? (
        <SectionFrame kicker="next transmission" title="Drop window.">
          <ReleaseStatus release={transmission} />
        </SectionFrame>
      ) : null}

      <SectionFrame kicker={theKeyTool.role} title="Check in. Check out.">
        <div className="border-t border-stone-800">
          <ManifestLine de={theKeyTool.lines[0].de} en={theKeyTool.lines[0].en} />
        </div>
        <Link
          className="mt-8 inline-block border border-red-950 px-5 py-3 text-sm font-black uppercase text-stone-100 transition-colors duration-300 hover:border-red-800 hover:bg-red-950/10 hover:text-red-600 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900"
          href="/the-key"
        >
          {theKeyTool.name}
        </Link>
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

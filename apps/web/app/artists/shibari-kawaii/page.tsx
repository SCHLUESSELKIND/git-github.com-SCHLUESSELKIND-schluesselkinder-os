import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { EditorialImage } from "../../_components/EditorialImage";
import { RotatedMeta } from "../../_components/RotatedMeta";
import { SectionFrame } from "../../_components/SectionFrame";
import { SymbolRail } from "../../_components/SymbolRail";
import { getStaticArtistPageProjection } from "../../../lib/registry/artist-page";

const campaignImage = "/brand/campaign-dungeon-chair.png";
const description = "SHIBARI KAWAII artist dossier for the controlled SCHLUESSELKINDER release archive.";
const title = `SHIBARI KAWAII | ${masterbrand}`;
// Artist page URL verified live 2026-06-10 (operator-supplied).
const SPOTIFY_ARTIST_URL = "https://open.spotify.com/artist/4CwlfdjdtoBVQAkrk84LZi";

export const metadata: Metadata = {
  alternates: {
    canonical: "/artists/shibari-kawaii"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SHIBARI KAWAII campaign environment", height: 1400, url: campaignImage, width: 1400 }],
    title,
    url: "/artists/shibari-kawaii"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [campaignImage],
    title
  }
};

function formatRole(role: string) {
  return role.replace(/-/g, " ");
}

function formatSignals(count: number) {
  return count === 1 ? "1 signal" : `${count} signals`;
}

export default function ShibariKawaiiPage() {
  const dossier = getStaticArtistPageProjection();
  const publicSignals = dossier.releases.flatMap((release) => release.signals);
  const railLabels = [
    dossier.artist.canonicalName,
    ...dossier.releases.map((release) => release.releaseCode),
    ...publicSignals.map((signal) => signal.trackCode),
    ...dossier.objects.map((object) => object.objectCode)
  ];

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="relative min-h-[calc(100vh-57px)] border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[1.05fr_0.95fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-8">
              <div className="grid gap-10">
                <p className="text-xs font-black uppercase text-red-600">{dossier.artist.artistKey}</p>
                <BrandSymbol
                  className="h-48 w-36 opacity-60 md:h-[22rem] md:w-64"
                  label={`${dossier.artist.canonicalName} archival stamp`}
                  variant="ropeface"
                />
              </div>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" variant="key" />
            </div>
            <div className="max-w-5xl pb-4 text-xl leading-8 text-stone-300">
              <h1 className="mb-8 text-xs font-black uppercase tracking-[0.45em] text-stone-500">
                {dossier.artist.canonicalName}
              </h1>
              <p
                className="whitespace-nowrap font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(2.25rem, 10vw, 10.5rem)", lineHeight: 0.84 }}
              >
                ROPEMASTER
              </p>
            </div>
          </div>
          <div className="grid gap-8 md:grid-rows-[1fr_auto]">
            <EditorialImage
              alt="Cropped dungeon room campaign environment"
              caption="campaign"
              className="min-h-[420px]"
              imageClassName="image-noir object-[55%_48%]"
              priority
              src={campaignImage}
              symbol="none"
            />
            <RotatedMeta>{masterbrand} / release dossier</RotatedMeta>
          </div>
        </div>
      </section>
      <SymbolRail labels={railLabels} />
      <SectionFrame kicker="sound records" title="Public signals.">
        <div className="border-y border-stone-800">
          {dossier.releases.map((release) => (
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
                    {dossier.artist.canonicalName}
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
      <SectionFrame kicker="outbound record" title="Spotify signal.">
        <div className="border-t border-stone-800">
          <a
            className="grid gap-4 border-b border-stone-800 py-10 transition-colors last:border-b-0 hover:border-red-900 hover:text-red-700 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:grid-cols-[1fr_auto] md:items-baseline md:py-12"
            href={SPOTIFY_ARTIST_URL}
            rel="noopener noreferrer"
            target="_blank"
          >
            <span className="break-words text-3xl font-black uppercase leading-tight tracking-tight text-stone-100 md:text-5xl">
              {dossier.artist.canonicalName} → SPOTIFY
            </span>
            <span className="text-xs font-black uppercase text-stone-500">EXTERNAL / NO EMBED</span>
          </a>
        </div>
      </SectionFrame>

      <section className="border-t border-stone-800">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 md:grid-cols-[0.85fr_1.15fr] md:px-8 md:py-24">
          <p className="self-end font-black uppercase text-stone-100" style={{ fontSize: "clamp(3.75rem, 10vw, 9rem)", lineHeight: 0.82 }}>The room keeps the mark.</p>
          <EditorialImage
            alt="Dungeon room campaign image for SHIBARI KAWAII"
            caption="room"
            className="h-[680px]"
            imageClassName="image-noir"
            src={campaignImage}
            symbol="key"
          />
        </div>
      </section>
    </main>
  );
}

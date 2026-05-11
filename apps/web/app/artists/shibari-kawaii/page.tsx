import type { Metadata } from "next";
import { brandAssets, firstArtist, masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { EditorialImage } from "../../_components/EditorialImage";
import { ManifestLine } from "../../_components/ManifestLine";
import { RotatedMeta } from "../../_components/RotatedMeta";
import { SectionFrame } from "../../_components/SectionFrame";
import { SymbolRail } from "../../_components/SymbolRail";
import { TrackList } from "../../_components/TrackList";
import { getCatalogArtist } from "../../../lib/catalog/catalog-queries";
import type { CatalogArtistProjection } from "../../../lib/catalog/catalog-types";

const artistKey = "artist_shibari_kawaii";

export const metadata: Metadata = {
  title: `${firstArtist.name} | ${masterbrand}`,
  description: "SHIBARI KAWAII artist signal for SCHLUESSELKINDER."
};

export default async function ShibariKawaiiPage() {
  const artistProjection = await readArtistProjection();
  const displayName = artistProjection?.displayName ?? firstArtist.name;

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="relative min-h-[calc(100vh-57px)] border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[1.05fr_0.95fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-8">
              <div className="grid gap-10">
                <p className="text-xs font-black uppercase text-red-600">{firstArtist.archiveCode}</p>
                <BrandSymbol
                  className="h-48 w-36 opacity-60 md:h-[22rem] md:w-64"
                  label={`${displayName} archival stamp`}
                  variant="ropeface"
                />
              </div>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" variant="key" />
            </div>
            <div className="max-w-5xl pb-4 text-xl leading-8 text-stone-300">
              <h1 className="mb-8 text-xs font-black uppercase tracking-[0.45em] text-stone-500">
                {displayName}
              </h1>
              <p
                className="font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(4.75rem, 11vw, 10.5rem)", lineHeight: 0.78 }}
              >
                {firstArtist.fragments.de[0]}
              </p>
              <p className="mt-8 max-w-xl">{firstArtist.fragments.en[2]}</p>
            </div>
            <dl className="grid gap-0 border-t border-stone-800 text-xs font-black uppercase text-stone-500 md:grid-cols-3">
              <div className="border-b border-stone-800 py-4 md:border-b-0 md:border-r">
                <dt>language</dt>
                <dd className="mt-2 text-stone-100">Deutsch / English</dd>
              </div>
              <div className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:px-5">
                <dt>label</dt>
                <dd className="mt-2 text-stone-100">{masterbrand}</dd>
              </div>
              <div className="py-4 md:px-5">
                <dt>release artifacts</dt>
                <dd className="mt-2 text-stone-100">{firstArtist.tracks.length} artifacts</dd>
              </div>
            </dl>
          </div>
          <div className="grid gap-8 md:grid-rows-[1fr_auto]">
            <EditorialImage
              alt="Cropped dungeon room campaign environment"
              caption="campaign environment"
              className="min-h-[420px]"
              imageClassName="image-noir object-[55%_48%]"
              priority
              src={brandAssets.campaignDungeonChair}
              symbol="none"
            />
            <RotatedMeta>{firstArtist.location} / release dossier</RotatedMeta>
          </div>
        </div>
      </section>
      <SymbolRail labels={["ROPE", "STATIC", "DAWN", "CONTROL", "AFTER"]} />
      <SectionFrame kicker="dossier fragments" title="No soft biography.">
        <div className="border-t border-stone-800">
          {firstArtist.fragments.de.map((line, index) => (
            <ManifestLine de={line} en={firstArtist.fragments.en[index]} key={line} />
          ))}
        </div>
      </SectionFrame>
      <SectionFrame kicker="release artifacts" title="Release pressure.">
        <TrackList />
      </SectionFrame>
      <section className="border-t border-stone-800">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 md:grid-cols-[0.85fr_1.15fr] md:px-8 md:py-24">
          <p className="self-end font-black uppercase text-stone-100" style={{ fontSize: "clamp(3.75rem, 10vw, 9rem)", lineHeight: 0.82 }}>The room keeps the mark.</p>
          <EditorialImage
            alt="Dungeon room campaign image for SHIBARI KAWAII"
            caption="campaign room"
            className="h-[680px]"
            imageClassName="image-noir"
            src={brandAssets.campaignDungeonChair}
            symbol="key"
          />
        </div>
      </section>
    </main>
  );
}

async function readArtistProjection(): Promise<CatalogArtistProjection | null> {
  try {
    return await getCatalogArtist(artistKey);
  } catch {
    return null;
  }
}

import type { Metadata } from "next";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { EditorialImage } from "../../_components/EditorialImage";
import { ManifestLine } from "../../_components/ManifestLine";
import { RotatedMeta } from "../../_components/RotatedMeta";
import { SectionFrame } from "../../_components/SectionFrame";
import { SymbolRail } from "../../_components/SymbolRail";
import { getStaticArtistPageProjection } from "../../../lib/registry/artist-page";

const collectiveName = "SCHLUESSELKINDER";
const campaignImage = "/brand/campaign-dungeon-chair.png";

export const metadata: Metadata = {
  title: `SHIBARI KAWAII | ${collectiveName}`,
  description: "SHIBARI KAWAII artist signal for SCHLUESSELKINDER."
};

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
                className="font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(4.75rem, 11vw, 10.5rem)", lineHeight: 0.78 }}
              >
                ROPEMASTER
              </p>
              <p className="mt-8 max-w-xl">Public artist dossier for the controlled release archive.</p>
            </div>
            <dl className="grid gap-0 border-t border-stone-800 text-xs font-black uppercase text-stone-500 md:grid-cols-3">
              <div className="border-b border-stone-800 py-4 md:border-b-0 md:border-r">
                <dt>language</dt>
                <dd className="mt-2 text-stone-100">Deutsch / English</dd>
              </div>
              <div className="border-b border-stone-800 py-4 md:border-b-0 md:border-r md:px-5">
                <dt>label</dt>
                <dd className="mt-2 text-stone-100">{collectiveName}</dd>
              </div>
              <div className="py-4 md:px-5">
                <dt>public signals</dt>
                <dd className="mt-2 text-stone-100">{publicSignals.length} signals</dd>
              </div>
            </dl>
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
            <RotatedMeta>{collectiveName} / release dossier</RotatedMeta>
          </div>
        </div>
      </section>
      <SymbolRail labels={railLabels} />
      <SectionFrame kicker="dossier fragments" title="No soft biography.">
        <div className="border-t border-stone-800">
          <ManifestLine de="LP bleibt Anker." en="The LP remains the anchor." />
          <ManifestLine de="Signale bleiben Signale." en="Signals remain signals." />
          <ManifestLine de="Archiv bleibt Quelle." en="The archive remains the source." />
        </div>
      </SectionFrame>
      <SectionFrame kicker="sound records" title="Public signals.">
        <div className="border-y border-stone-800">
          {dossier.releases.map((release) => (
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
                  <p className="mt-4 text-sm font-black uppercase text-stone-500">{dossier.artist.canonicalName}</p>
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

import Link from "next/link";
import { brandAssets, firstArtist, masterbrand, seedCopy } from "@schluesselkinder/brand";
import { ArtistSignal } from "./_components/ArtistSignal";
import { BrandSymbol } from "./_components/BrandSymbol";
import { EditorialImage } from "./_components/EditorialImage";
import { ManifestLine } from "./_components/ManifestLine";
import { RotatedMeta } from "./_components/RotatedMeta";
import { SectionFrame } from "./_components/SectionFrame";
import { ShopPreview } from "./_components/ShopPreview";
import { SymbolRail } from "./_components/SymbolRail";
import { TrackList } from "./_components/TrackList";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="relative min-h-[calc(100vh-57px)] overflow-hidden border-b border-stone-800">
        <EditorialImage
          alt="Dungeon concrete room with a rope-bound chair"
          className="!absolute inset-0 h-full w-full border-0"
          imageClassName="image-noir"
          priority
          src={brandAssets.campaignDungeonChair}
          symbol="none"
        />
        <div className="absolute inset-0 bg-black/55" />
        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#070605] to-transparent" />
        <div className="relative mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl grid-rows-[1fr_auto] px-5 py-8 md:px-8">
          <div className="flex items-start justify-between">
            <p className="text-xs font-black uppercase text-red-600">{masterbrand}</p>
            <BrandSymbol className="h-16 w-16 text-stone-100/80" />
          </div>
          <div className="grid items-end gap-8 md:grid-cols-[auto_1fr_120px]">
            <div>
              <h1 className="max-w-5xl font-black uppercase text-stone-100" style={{ fontSize: "clamp(4.8rem, 14vw, 13rem)", lineHeight: 0.78 }}>
                {seedCopy.hero.en}
              </h1>
              <div className="mt-8 max-w-xl text-xl leading-8 text-stone-300">
                <p>{seedCopy.hero.de}</p>
                <p>{seedCopy.campaign.en}</p>
              </div>
            </div>
            <div className="hidden md:block" />
            <RotatedMeta>{firstArtist.archiveCode} / music is the key</RotatedMeta>
          </div>
        </div>
      </section>

      <SymbolRail labels={["KEY", "CHAIR", "ROPE", "ROOM", "AFTER"]} />

      <SectionFrame kicker="collective identity" title="Cold room. Red trace.">
        <div className="border-t border-stone-800">
          {seedCopy.collective.map((line) => (
            <ManifestLine de={line.de} en={line.en} key={line.en} />
          ))}
        </div>
      </SectionFrame>

      <SectionFrame kicker="first artist" title="Body as signal.">
        <ArtistSignal />
      </SectionFrame>

      <section className="border-t border-stone-800">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 md:grid-cols-[1.1fr_0.9fr] md:px-8 md:py-24">
          <div className="self-end">
            <p className="text-xs font-black uppercase text-red-600">campaign evidence</p>
            <p className="mt-8 max-w-4xl font-black uppercase text-stone-100" style={{ fontSize: "clamp(3.75rem, 10vw, 9rem)", lineHeight: 0.82 }}>The room keeps the signal.</p>
          </div>
          <EditorialImage
            alt="Cropped dungeon room wall and chair"
            caption="campaign fragment"
            className="h-[620px]"
            imageClassName="image-noir object-[58%_48%]"
            src={brandAssets.campaignDungeonChair}
            symbol="none"
          />
        </div>
      </section>

      <SectionFrame kicker="music signal" title="Three artifacts.">
        <TrackList mode="compact" />
        <Link className="mt-8 inline-block border border-red-800 px-5 py-3 text-sm font-black uppercase text-stone-100 hover:bg-red-900" href="/music">
          Enter music archive
        </Link>
      </SectionFrame>

      <SectionFrame kicker="streetwear signal" title="Objects later.">
        <ShopPreview />
      </SectionFrame>

      <section className="border-t border-stone-800">
        <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
          <div className="max-w-5xl">
            {seedCopy.manifesto.map((line) => (
              <p className="border-b border-stone-800 py-5 text-4xl font-black uppercase leading-none text-stone-100 md:text-7xl" key={line}>
                {line}
              </p>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

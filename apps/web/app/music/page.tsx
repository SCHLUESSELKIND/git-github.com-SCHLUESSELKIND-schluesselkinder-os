import type { Metadata } from "next";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { GlyphRail } from "../_components/GlyphRail";
import { ManifestLine } from "../_components/ManifestLine";
import { SectionFrame } from "../_components/SectionFrame";
import { TrackList } from "../_components/TrackList";
import { listCatalogMusicReleases, listCatalogTracks } from "../../lib/catalog/catalog-queries";
import type { CatalogReleaseProjection, CatalogTrackProjection } from "../../lib/catalog/catalog-types";

export const metadata: Metadata = {
  title: `Music | ${masterbrand}`,
  description: "SCHLUESSELKINDER music archive."
};

export default async function MusicPage() {
  const [releaseProjections, trackProjections] = await Promise.all([
    readReleaseProjections(),
    readTrackProjections()
  ]);
  const hasCatalogProjections = releaseProjections.length > 0 || trackProjections.length > 0;

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow={`${masterbrand} music`} title="Sound after light.">
        <p>{seedCopy.musicSignal.de}</p>
        <p>{seedCopy.musicSignal.en}</p>
      </EditorialHero>
      <GlyphRail items={["001", "002", "003", "ROOM", "WIRE", "RED"]} />
      <SectionFrame kicker="archive" title="Tracks as artifacts.">
        {hasCatalogProjections ? (
          <MusicProjectionArchive releases={releaseProjections} tracks={trackProjections} />
        ) : (
          <TrackList />
        )}
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

async function readReleaseProjections(): Promise<CatalogReleaseProjection[]> {
  try {
    return await listCatalogMusicReleases();
  } catch {
    return [];
  }
}

async function readTrackProjections(): Promise<CatalogTrackProjection[]> {
  try {
    return await listCatalogTracks();
  } catch {
    return [];
  }
}

function MusicProjectionArchive({
  releases,
  tracks
}: Readonly<{ releases: readonly CatalogReleaseProjection[]; tracks: readonly CatalogTrackProjection[] }>) {
  return (
    <div className="space-y-10">
      {releases.length > 0 ? <ReleaseProjectionList releases={releases} /> : null}
      {tracks.length > 0 ? <TrackProjectionList tracks={tracks} /> : null}
    </div>
  );
}

function ReleaseProjectionList({ releases }: Readonly<{ releases: readonly CatalogReleaseProjection[] }>) {
  return (
    <div className="border-y border-stone-800">
      {releases.map((release) => (
        <article
          className="grid gap-4 border-b border-stone-800 py-7 last:border-b-0 md:grid-cols-[120px_1fr_0.8fr]"
          key={release.releaseCode}
        >
          <p className="text-xs font-black uppercase text-red-600 md:pt-2">{release.releaseCode}</p>
          <div>
            <h3 className="break-words text-5xl font-black uppercase leading-[0.88] text-stone-100 md:text-7xl">
              {release.title}
            </h3>
            {release.canonicalArtwork ? (
              <img
                alt={`${release.title} artwork projection`}
                className="mt-5 aspect-square w-full max-w-44 object-cover opacity-85"
                loading="lazy"
                src={release.canonicalArtwork}
              />
            ) : null}
          </div>
          {release.publicFragments.length > 0 ? (
            <div className="text-lg leading-7 text-stone-400 md:self-end">
              {release.publicFragments.map((fragment, index) => (
                <p key={index}>{fragment}</p>
              ))}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function TrackProjectionList({ tracks }: Readonly<{ tracks: readonly CatalogTrackProjection[] }>) {
  return (
    <div className="border-y border-stone-800">
      {tracks.map((track) => (
        <article
          className="grid gap-4 border-b border-stone-800 py-7 last:border-b-0 md:grid-cols-[120px_1fr_0.8fr]"
          key={track.trackKey}
        >
          <p className="break-words text-xs font-black uppercase text-red-600 md:pt-2">{track.trackKey}</p>
          <div>
            <h3 className="break-words text-5xl font-black uppercase leading-[0.88] text-stone-100 md:text-7xl">
              {track.title}
            </h3>
            {track.runtime !== null ? (
              <p className="mt-4 text-sm font-black uppercase text-stone-500">{track.runtime}s</p>
            ) : null}
          </div>
          {track.moods.length > 0 || track.worlds.length > 0 ? (
            <div className="space-y-3 text-lg leading-7 text-stone-400 md:self-end">
              {track.moods.length > 0 ? <p>{track.moods.join(" / ")}</p> : null}
              {track.worlds.length > 0 ? <p>{track.worlds.join(" / ")}</p> : null}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

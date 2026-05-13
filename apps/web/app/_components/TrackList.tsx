import { getStaticMusicPageProjection } from "../../lib/registry/music-page";

type TrackListProps = Readonly<{
  mode?: "full" | "compact" | "archive";
}>;

export function TrackList({ mode = "full" }: TrackListProps) {
  const music = getStaticMusicPageProjection();
  const signalRows = music.releases.flatMap((release) =>
    release.signals.map((signal) => ({
      ...signal,
      releaseCode: release.releaseCode,
      releaseTitle: release.displayTitle
    }))
  );

  return (
    <div className="border-y border-stone-800">
      {signalRows.map((track) => (
        <article
          className="grid gap-5 border-b border-stone-800 py-7 transition-colors last:border-b-0 hover:border-stone-700 md:grid-cols-[104px_1fr_0.7fr]"
          key={track.trackKey}
        >
          <div className="text-xs font-black uppercase md:pt-2">
            <p className="text-red-600">{track.trackCode}</p>
            {mode !== "compact" ? <p className="mt-3 text-stone-600">{track.releaseCode}</p> : null}
          </div>
          <div>
            <h3 className="break-words text-5xl font-black uppercase leading-[0.88] text-stone-100 md:text-6xl">
              {track.title}
            </h3>
            {mode === "full" || mode === "archive" ? (
              <p className="mt-4 text-sm font-black uppercase text-stone-500">{music.artist.canonicalName}</p>
            ) : null}
          </div>
          {mode === "full" || mode === "archive" ? (
            <div className="text-lg leading-7 text-stone-400 md:self-end">
              <p className="text-sm font-black uppercase text-stone-500">{track.releaseTitle}</p>
              <p className="mt-2 text-sm font-black uppercase text-stone-200">PUBLIC SIGNAL</p>
              {mode === "full" ? (
                <p className="mt-4 text-base leading-6 text-stone-500">Registry projection. Manual distribution references remain separate.</p>
              ) : null}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

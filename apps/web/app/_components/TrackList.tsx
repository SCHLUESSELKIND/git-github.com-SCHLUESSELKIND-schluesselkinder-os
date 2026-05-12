import { firstArtist } from "@schluesselkinder/brand";

type TrackListProps = Readonly<{
  mode?: "full" | "compact" | "archive";
}>;

export function TrackList({ mode = "full" }: TrackListProps) {
  return (
    <div className="border-y border-stone-800">
      {firstArtist.tracks.map((track) => (
        <article
          className="grid gap-5 border-b border-stone-800 py-7 last:border-b-0 md:grid-cols-[104px_1fr_0.7fr_140px]"
          key={track.code}
        >
          <div className="text-xs font-black uppercase md:pt-2">
            <p className="text-red-600">{track.code}</p>
            {mode !== "compact" ? <p className="mt-3 text-stone-600">{track.duration}</p> : null}
          </div>
          <div>
            <h3 className="break-words text-5xl font-black uppercase leading-[0.88] text-stone-100 md:text-6xl">
              {track.title}
            </h3>
            {mode === "full" || mode === "archive" ? (
              <p className="mt-4 text-sm font-black uppercase text-stone-500">{firstArtist.name}</p>
            ) : null}
          </div>
          {mode === "full" || mode === "archive" ? (
            <div className="text-lg leading-7 text-stone-400 md:self-end">
              <p className="text-sm font-black uppercase text-stone-500">{track.platform}</p>
              <p className="mt-2 text-sm font-black uppercase text-stone-200">{track.status}</p>
              {mode === "full" ? (
                <p className="mt-4 text-base normal-case leading-6 text-stone-500">{track.fragment.de}</p>
              ) : null}
            </div>
          ) : null}
          {mode === "full" || mode === "archive" ? (
            <a
              className="self-end border border-stone-800 px-4 py-3 text-center text-xs font-black uppercase text-stone-300 transition-colors hover:border-red-950 hover:text-red-700"
              href={track.soundCloudUrl}
              rel="noreferrer"
              target="_blank"
            >
              SoundCloud öffnen
            </a>
          ) : null}
        </article>
      ))}
    </div>
  );
}

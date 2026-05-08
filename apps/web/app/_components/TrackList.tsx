import { firstArtist } from "@schluesselkinder/brand";

type TrackListProps = Readonly<{
  mode?: "full" | "compact";
}>;

export function TrackList({ mode = "full" }: TrackListProps) {
  return (
    <div className="border-y border-stone-800">
      {firstArtist.tracks.map((track) => (
        <article className="grid gap-4 border-b border-stone-800 py-7 last:border-b-0 md:grid-cols-[120px_1fr_0.8fr]" key={track.code}>
          <p className="text-xs font-black uppercase text-red-600 md:pt-2">{track.code}</p>
          <div>
            <h3 className="break-words text-5xl font-black uppercase leading-[0.88] text-stone-100 md:text-7xl">
              {track.title}
            </h3>
            {mode === "full" ? <p className="mt-4 text-sm font-black uppercase text-stone-500">{track.mood}</p> : null}
          </div>
          {mode === "full" ? (
            <div className="text-lg leading-7 text-stone-400 md:self-end">
              <p>{track.fragment.de}</p>
              <p>{track.fragment.en}</p>
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

import Link from "next/link";
import { getStaticArtistPageProjection } from "../../lib/registry/artist-page";
import { BrandSymbol } from "./BrandSymbol";

export function ArtistSignal() {
  const dossier = getStaticArtistPageProjection();
  const release = dossier.releases[0];
  const signalTitles = release.signals.map((signal) => signal.title).join(" / ");

  return (
    <Link className="group grid overflow-hidden border border-stone-800 bg-[#090806] transition-colors hover:border-red-900 md:grid-cols-[0.85fr_1.15fr]" href={`/artists/${dossier.artist.slug}`}>
      <div className="relative flex min-h-80 items-center justify-center border-b border-stone-800 bg-black md:border-b-0 md:border-r">
        <BrandSymbol
          className="h-48 w-36 text-stone-100/85 transition-transform duration-500 group-hover:scale-105 md:h-64 md:w-44"
          label={`${dossier.artist.canonicalName} ropeface mark`}
          variant="ropeface"
        />
      </div>
      <div className="flex min-h-80 flex-col justify-between p-5 md:p-8">
        <div className="flex items-start justify-between gap-6">
          <p className="text-xs font-black uppercase text-red-600">{release.releaseCode}</p>
          <p className="text-xs font-black uppercase text-stone-600">{release.role}</p>
        </div>
        <div>
          <p className="text-xs font-black uppercase tracking-[0.35em] text-stone-500">{dossier.artist.canonicalName}</p>
          <p className="mt-8 max-w-lg text-3xl font-black uppercase leading-none text-stone-100 group-hover:text-stone-200 md:text-6xl">
            {release.displayTitle}
          </p>
          <p className="mt-6 max-w-md text-sm font-black uppercase leading-6 text-stone-500">{signalTitles}</p>
        </div>
      </div>
    </Link>
  );
}

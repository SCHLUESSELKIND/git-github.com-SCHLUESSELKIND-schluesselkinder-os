import {
  type Release,
  type ReleaseStatus as ReleaseStatusValue,
  formatReleaseDate,
  statusOf
} from "../_releases";

interface Props {
  release: Release;
  /**
   * Optional moment for testing / SSR snapshots. Defaults to "now" when the
   * server renders the page. Pages should set `export const revalidate = 60`
   * so the cached HTML refreshes around the cutover.
   */
  now?: Date;
}

const SIGNAL_GREEN = "#5FB047";

/**
 * Renders one of three states for a release: incoming (pre-T-0), in_transmission
 * (T-0 → archive), archived (post-archive).
 *
 * Display intent: cold, single-block, no marketing tone. The component itself
 * decides which state to render based on the current moment vs the release date,
 * so the artist page does NOT need any toggle logic.
 */
export function ReleaseStatus({ release, now }: Props) {
  const status = statusOf(release, now);
  if (status === "incoming") {
    return <IncomingBlock release={release} />;
  }
  if (status === "in_transmission") {
    return <InTransmissionBlock release={release} />;
  }
  return <ArchivedBlock release={release} />;
}

function IncomingBlock({ release }: { release: Release }) {
  return (
    <div className="border border-stone-800 bg-[#0a0908]">
      <div className="border-b border-stone-800 px-5 py-3 font-mono text-[0.55rem] uppercase tracking-[0.3em] sm:text-xs">
        <span style={{ color: SIGNAL_GREEN }}>transmission incoming</span>
        <span className="mx-2 text-stone-700">·</span>
        <span className="text-stone-500">{formatReleaseDate(release)}</span>
      </div>
      <div className="px-5 py-8 md:px-8 md:py-10">
        <p className="font-mono text-[0.55rem] uppercase tracking-[0.3em] text-stone-500 sm:text-xs">
          RELEASE-001 · drop window
        </p>
        <h3
          className="mt-4 font-black uppercase leading-[0.86] text-stone-100"
          style={{ fontSize: "clamp(2rem, 7vw, 4.5rem)" }}
        >
          {release.title}
        </h3>
        <ul className="mt-8 space-y-2 font-mono text-xs uppercase tracking-[0.18em] text-stone-400 sm:text-sm">
          {release.tracks.map((track, index) => (
            <li key={track} className="flex gap-4">
              <span className="text-stone-600">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span>{track}</span>
            </li>
          ))}
        </ul>
        <p className="mt-8 max-w-xl text-sm leading-7 text-stone-500">
          Drei Tracks. Ein District. Keine Vorabhörprobe. Kein Vinyl in dieser
          Pressung. Drop-Fenster öffnet exakt zum oben angegebenen Zeitpunkt.
        </p>
      </div>
    </div>
  );
}

function InTransmissionBlock({ release }: { release: Release }) {
  const links: Array<[string, string | undefined]> = [
    ["Spotify", release.links.spotify],
    ["Apple Music", release.links.appleMusic],
    ["SoundCloud", release.links.soundcloud],
    ["Bandcamp", release.links.bandcamp],
    ["YouTube Music", release.links.youtubeMusic],
    ["Shop", release.links.shopCollection]
  ];
  const liveLinks = links.filter(([, href]) => Boolean(href));

  return (
    <div className="border border-stone-800 bg-[#0a0908]">
      <div className="border-b border-stone-800 px-5 py-3 font-mono text-[0.55rem] uppercase tracking-[0.3em] sm:text-xs">
        <span style={{ color: SIGNAL_GREEN }}>in transmission</span>
        <span className="mx-2 text-stone-700">·</span>
        <span className="text-stone-500">{formatReleaseDate(release)}</span>
      </div>
      <div className="px-5 py-8 md:px-8 md:py-10">
        <p className="font-mono text-[0.55rem] uppercase tracking-[0.3em] text-stone-500 sm:text-xs">
          RELEASE-001 · live
        </p>
        <h3
          className="mt-4 font-black uppercase leading-[0.86] text-stone-100"
          style={{ fontSize: "clamp(2rem, 7vw, 4.5rem)" }}
        >
          {release.title}
        </h3>
        {liveLinks.length === 0 ? (
          <div className="mt-8 max-w-xl text-sm leading-7">
            <p className="text-stone-300">Transmission aktiv. Verbindungen folgen.</p>
            <p className="mt-1 text-stone-600">In transmission. Links follow.</p>
          </div>
        ) : (
          <ul className="mt-8 grid gap-px bg-stone-800 sm:grid-cols-2">
            {liveLinks.map(([label, href]) => (
              <li key={label} className="bg-[#0a0908]">
                <a
                  href={href as string}
                  target="_blank"
                  rel="noopener"
                  className="flex items-center justify-between gap-4 px-5 py-4 font-mono text-xs uppercase tracking-[0.22em] text-stone-300 transition hover:bg-[#111110] hover:text-stone-100"
                >
                  <span>{label}</span>
                  <span aria-hidden>→</span>
                </a>
              </li>
            ))}
          </ul>
        )}
        <ul className="mt-8 space-y-2 font-mono text-xs uppercase tracking-[0.18em] text-stone-500 sm:text-sm">
          {release.tracks.map((track, index) => (
            <li key={track} className="flex gap-4">
              <span className="text-stone-700">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span>{track}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ArchivedBlock({ release }: { release: Release }) {
  return (
    <div className="border border-stone-800 bg-[#0a0908]">
      <div className="border-b border-stone-800 px-5 py-3 font-mono text-[0.55rem] uppercase tracking-[0.3em] text-stone-500 sm:text-xs">
        archived · {formatReleaseDate(release)}
      </div>
      <div className="px-5 py-8 md:px-8 md:py-10">
        <p className="font-mono text-[0.55rem] uppercase tracking-[0.3em] text-stone-500 sm:text-xs">
          RELEASE-001
        </p>
        <h3 className="mt-3 font-black uppercase text-stone-300 sm:text-3xl">
          {release.title}
        </h3>
        <p className="mt-6 max-w-xl text-sm leading-7 text-stone-500">
          District abgeschlossen. Im Archiv verfügbar. Heavy garments
          gegebenenfalls ausverkauft.
        </p>
      </div>
    </div>
  );
}

// Re-export for callers that want the raw status string.
export type { ReleaseStatusValue };

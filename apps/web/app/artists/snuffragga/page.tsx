import Link from "next/link";
import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { GlyphRail } from "../../_components/GlyphRail";
import { NewsletterForm } from "../../_components/NewsletterForm";
import { ReleaseStatus } from "../../_components/ReleaseStatus";
import { SectionFrame } from "../../_components/SectionFrame";
import { EmbedConsentReset, SoundEmbed } from "../../_components/SoundEmbed";
import { latestReleaseFor } from "../../_releases";

// Refresh the cached HTML every 60s so the ReleaseStatus block flips from
// "incoming" to "in transmission" within a minute of the release window
// opening, without any manual deploy on T-0.
export const revalidate = 60;

// Operator wires these via env vars. Empty = honest offline state.
// We never bake in fake Spotify / SoundCloud / newsletter URLs.
// Artist page URL verified live (docs/SNUFFRAGGA_LIVE_CHECKLIST.md §3).
const SPOTIFY_ARTIST_URL = "https://open.spotify.com/artist/0Gt1TrN8G1DyXBa2Da5XLW";
const SPOTIFY_EMBED = process.env.NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED || null;
const SOUNDCLOUD_EMBED = process.env.NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED || null;
const NEWSLETTER_ENDPOINT = process.env.NEXT_PUBLIC_NEWSLETTER_ENDPOINT;
const SHOP_URL = process.env.NEXT_PUBLIC_SHOP_URL || "/shop";
const GRUENLICHTBEZIRK_URL = SHOP_URL.endsWith("/")
  ? `${SHOP_URL}collections/gruenlichtbezirk`
  : `${SHOP_URL}/collections/gruenlichtbezirk`;

const pageDescription =
  "Dub, Bass Culture und GRÜNLICHTBEZIRK aus dem SCHLUESSELKINDER Universum. " +
  "Aktiver District für Soundsystem, limited objects und Transmissionen.";
const pageTitle = `SNUFFRAGGA SOUNDSYSTEM — ${masterbrand}`;
const campaignImage = "/brand/campaign-dungeon-chair.png";

export const metadata: Metadata = {
  alternates: { canonical: "/artists/snuffragga" },
  description: pageDescription,
  keywords: [
    "SCHLUESSELKINDER",
    "SNUFFRAGGA SOUNDSYSTEM",
    "GRÜNLICHTBEZIRK",
    "Dub",
    "Bass Culture",
    "Underground",
    "Soundsystem",
    "Berlin"
  ],
  openGraph: {
    description: pageDescription,
    images: [
      {
        alt: "SNUFFRAGGA SOUNDSYSTEM signal room",
        height: 1400,
        url: campaignImage,
        width: 1400
      }
    ],
    locale: "de_DE",
    siteName: masterbrand,
    title: pageTitle,
    type: "profile",
    url: "/artists/snuffragga"
  },
  title: pageTitle,
  twitter: {
    card: "summary_large_image",
    description: pageDescription,
    images: [campaignImage],
    title: pageTitle
  }
};

export default function SnuffraggaPage() {
  const release = latestReleaseFor("snuffragga");

  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      {/* ---------------- HERO ---------------- */}
      <section className="relative border-b border-stone-800">
        {/* Ambient texture */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "radial-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), radial-gradient(rgba(0,0,0,0.6) 1px, transparent 1px)",
            backgroundSize: "3px 3px, 7px 7px",
            backgroundPosition: "0 0, 1px 2px",
            mixBlendMode: "overlay"
          }}
        />

        <div className="relative mx-auto grid max-w-7xl gap-10 px-5 pb-12 pt-12 sm:pt-16 md:grid-cols-[1.15fr_0.85fr] md:gap-14 md:px-8 md:pb-20 md:pt-20">
          {/* Left column — eyebrow + title + metadata */}
          <div className="flex flex-col gap-12 border-l border-stone-800 pl-5 md:pl-8">
            <div className="flex items-start justify-between gap-6">
              <p className="font-mono text-[0.6rem] font-black uppercase tracking-[0.35em] text-[#5FB047] sm:text-xs">
                district-002 · active signal
              </p>
              <BrandSymbol
                className="h-10 w-10 text-stone-100/70 md:h-14 md:w-14"
                variant="key"
              />
            </div>

            <div>
              <p className="mb-6 font-mono text-[0.55rem] font-black uppercase tracking-[0.45em] text-stone-500 sm:text-xs">
                SNUFFRAGGA SOUNDSYSTEM
              </p>
              <h1
                className="font-black uppercase leading-[0.84] text-stone-100"
                style={{ fontSize: "clamp(3rem, 13vw, 9rem)" }}
              >
                Bass <br className="hidden sm:block" />
                pressure.
              </h1>
              <p className="mt-8 max-w-xl text-lg leading-8 text-stone-300 sm:text-xl">
                Aktiver District im SCHLUESSELKINDER Archiv. Sub-Bass als
                Geographie. Transmission only.
              </p>
            </div>

            {/* Primary CTAs */}
            <div className="flex flex-wrap gap-3">
              <a
                href={GRUENLICHTBEZIRK_URL}
                target={SHOP_URL.startsWith("http") ? "_blank" : undefined}
                rel={SHOP_URL.startsWith("http") ? "noopener" : undefined}
                className="inline-flex items-center gap-3 border border-stone-100 bg-stone-100 px-5 py-3 font-black uppercase tracking-[0.22em] text-stone-900 transition hover:bg-[#5FB047] hover:text-stone-100"
              >
                Enter GRÜNLICHTBEZIRK
                <span aria-hidden>→</span>
              </a>
              <Link
                href="#transmissions"
                className="inline-flex items-center gap-3 border border-stone-800 px-5 py-3 font-black uppercase tracking-[0.22em] text-stone-400 transition hover:border-stone-600 hover:text-stone-100"
              >
                Hör rein
              </Link>
            </div>

            <dl className="grid gap-0 border-t border-stone-800 font-mono text-[0.6rem] uppercase tracking-[0.18em] text-stone-500 sm:grid-cols-3 sm:text-xs">
              <div className="border-stone-800 px-0 py-5 sm:border-r sm:pr-6">
                <dt className="text-stone-600">drop</dt>
                <dd className="mt-2 text-stone-100">GRÜNLICHTBEZIRK</dd>
              </div>
              <div className="border-stone-800 px-0 py-5 sm:border-r sm:px-6">
                <dt className="text-stone-600">channel</dt>
                <dd className="mt-2 text-stone-100">soundsystem · dub · bass</dd>
              </div>
              <div className="px-0 py-5 sm:px-6">
                <dt className="text-stone-600">status</dt>
                <dd className="mt-2 text-[#5FB047]">signal live</dd>
              </div>
            </dl>
          </div>

          {/* Right column — campaign frame */}
          <aside className="flex flex-col gap-6">
            <div className="relative grid h-full grid-rows-[1fr_auto] border border-stone-800">
              <div className="flex items-center justify-center p-6 md:p-10">
                <BrandSymbol
                  className="h-40 w-40 text-stone-100/30 md:h-64 md:w-64"
                  label="SNUFFRAGGA signal stamp"
                  variant="key"
                />
              </div>
              <div className="border-t border-stone-800 p-4 font-mono text-[0.55rem] uppercase tracking-[0.28em] text-stone-500 sm:text-xs">
                <p>transmission room — no walk-in</p>
                <p className="mt-3 text-[#5FB047]">enter via signal only</p>
              </div>
            </div>
            <div className="flex flex-col gap-2 font-mono text-[0.55rem] uppercase tracking-[0.28em] text-stone-500 sm:text-xs">
              <p>
                operator note · embeds &amp; newsletter wire via env vars.
                offline by default.
              </p>
            </div>
          </aside>
        </div>
      </section>

      <GlyphRail items={["DISTRICT", "ROOM", "BASS", "DUB", "TRACE", "SK"]} />

      {/* ---------------- PRIMARY RELEASE ---------------- */}
      {release ? (
        <SectionFrame kicker="primary release · 001" title="Drop window.">
          <ReleaseStatus release={release} />
        </SectionFrame>
      ) : null}

      {/* ---------------- TRANSMISSIONS ---------------- */}
      <SectionFrame kicker="transmissions · 002" title="Listening room.">
        <div id="transmissions" className="scroll-mt-20">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="flex flex-col gap-3">
              <p className="font-mono text-[0.55rem] uppercase tracking-[0.3em] text-stone-500 sm:text-xs">
                Spotify
              </p>
              <SoundEmbed
                src={SPOTIFY_EMBED}
                title="Spotify · SNUFFRAGGA SOUNDSYSTEM"
                offlineLabel="spotify signal offline"
              />
            </div>
            <div className="flex flex-col gap-3">
              <p className="font-mono text-[0.55rem] uppercase tracking-[0.3em] text-stone-500 sm:text-xs">
                SoundCloud
              </p>
              <SoundEmbed
                src={SOUNDCLOUD_EMBED}
                title="SoundCloud · SNUFFRAGGA SOUNDSYSTEM"
                offlineLabel="soundcloud signal offline"
              />
            </div>
          </div>
          <p className="mt-6 max-w-2xl text-sm leading-7 text-stone-400">
            Streams gehen live, sobald die Operator-env-vars
            <code className="mx-1 border border-stone-800 px-1 text-stone-300">
              NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED
            </code>
            und
            <code className="mx-1 border border-stone-800 px-1 text-stone-300">
              NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED
            </code>
            gesetzt sind. Bis dahin bleiben beide Felder bewusst dunkel — keine
            Platzhalter-Player, keine Fake-Streams.
          </p>
        </div>
      </SectionFrame>

      {/* ---------------- GRÜNLICHTBEZIRK CTA ---------------- */}
      <section className="border-t border-stone-800">
        <div className="mx-auto grid max-w-7xl items-stretch gap-0 px-0 md:grid-cols-[1.05fr_0.95fr] md:px-0">
          <div className="border-stone-800 px-5 py-14 md:border-r md:px-12 md:py-20">
            <p className="font-mono text-[0.6rem] font-black uppercase tracking-[0.35em] text-[#5FB047] sm:text-xs">
              current drop · limited signal
            </p>
            <h2
              className="mt-6 font-black uppercase leading-[0.86] text-stone-100"
              style={{ fontSize: "clamp(2.5rem, 10vw, 7rem)" }}
            >
              GRÜNLICHT&shy;BEZIRK
            </h2>
            <p className="mt-8 max-w-xl text-lg leading-8 text-stone-300">
              Erste District-Kapsel. Heavy garments und Pressure objects, gebaut
              für Sound-Architektur, nicht für Streetwear-Inflation.
            </p>
            <p className="mt-4 max-w-xl text-sm leading-7 text-stone-500">
              Limited Run. Drops schließen, wenn die Lauflänge durch ist. Kein
              Restock. Kein Refill. Keine zweite Pressung.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={GRUENLICHTBEZIRK_URL}
                target={SHOP_URL.startsWith("http") ? "_blank" : undefined}
                rel={SHOP_URL.startsWith("http") ? "noopener" : undefined}
                className="inline-flex items-center gap-3 border border-stone-100 bg-stone-100 px-5 py-3 font-black uppercase tracking-[0.22em] text-stone-900 transition hover:bg-[#5FB047] hover:text-stone-100"
              >
                Enter shop
                <span aria-hidden>→</span>
              </a>
              <a
                href={SHOP_URL}
                target={SHOP_URL.startsWith("http") ? "_blank" : undefined}
                rel={SHOP_URL.startsWith("http") ? "noopener" : undefined}
                className="inline-flex items-center gap-3 border border-stone-800 px-5 py-3 font-black uppercase tracking-[0.22em] text-stone-400 transition hover:border-stone-600 hover:text-stone-100"
              >
                Alle Objekte
              </a>
            </div>
          </div>
          <div className="flex items-center justify-center bg-[#0a0908] px-5 py-14 md:px-12 md:py-20">
            <div className="grid h-full w-full max-w-md grid-cols-3 gap-px bg-stone-800">
              {DISTRICT_UNIFORMS.map((object) => (
                <div
                  key={object.code}
                  className="flex flex-col justify-between gap-2 bg-[#0a0908] p-3 transition hover:bg-[#111110] sm:p-4"
                >
                  <p className="font-mono text-[0.48rem] uppercase tracking-[0.25em] text-stone-600">
                    {object.code}
                  </p>
                  <div>
                    <p className="font-black uppercase tracking-[0.05em] text-stone-100">
                      {object.name}
                    </p>
                    <p className="mt-1 font-mono text-[0.5rem] uppercase tracking-[0.2em] text-stone-500">
                      {object.line}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- DISTRICT LORE ---------------- */}
      <SectionFrame kicker="archive note" title="District lore.">
        <div className="max-w-2xl space-y-5 text-stone-300">
          <p className="text-lg leading-8">
            SNUFFRAGGA ist kein Bühnenname. SNUFFRAGGA ist ein District. Eine
            Frequenz, die sich in einer Stadt einschließt, sobald das Licht
            ausgeht und der Sub die Wand annimmt.
          </p>
          <p>
            Das Soundsystem wurde in einem Hinterzimmer aufgebaut. Beton,
            Kabel, eine Glühbirne. Die erste Transmission war kein Song — sie
            war ein Druckwert. Dreiundvierzig Hertz. Nichts oben drüber.
          </p>
          <p>
            GRÜNLICHTBEZIRK ist die erste Kapsel, die aus dem Raum versendet
            wurde. Die Objekte gehen in limitierten Auflagen raus. Wenn ein
            Signal schließt, kommt es nicht zurück.
          </p>
          <p className="text-stone-500">
            Weitere Transmissionen folgen. Das Archiv führt ein striktes
            Logbuch.
          </p>
        </div>
      </SectionFrame>

      {/* ---------------- NEWSLETTER ---------------- */}
      <SectionFrame kicker="join the signal" title="Receive transmissions.">
        <div className="max-w-2xl space-y-6">
          <p className="text-stone-300">
            Ein Signal nach dem anderen. Drop-Windows, Archiv-Öffnungen,
            Pressure Readings. Keine Marketing-Stimme.
          </p>
          <NewsletterForm
            endpoint={NEWSLETTER_ENDPOINT}
            source="snuffragga_artist_page"
          />
          <p className="font-mono text-[0.6rem] uppercase tracking-[0.3em] text-stone-500">
            Du kannst die Frequenz jederzeit verlassen.
          </p>
        </div>
      </SectionFrame>

      {/* ---------------- FOOT NAV ---------------- */}
      <section className="border-t border-stone-800">
        <div className="mx-auto flex max-w-7xl flex-wrap gap-x-6 gap-y-3 px-5 py-12 font-mono text-[0.55rem] font-black uppercase tracking-[0.28em] text-stone-500 sm:text-xs md:px-8">
          <Link href="/artists" className="hover:text-stone-100">
            ← Artists
          </Link>
          <Link href="/music" className="hover:text-stone-100">
            Music index →
          </Link>
          <a
            href={SHOP_URL}
            target={SHOP_URL.startsWith("http") ? "_blank" : undefined}
            rel={SHOP_URL.startsWith("http") ? "noopener" : undefined}
            className="hover:text-stone-100"
          >
            Shop →
          </a>
          <a
            href={SPOTIFY_ARTIST_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-stone-100"
          >
            Spotify →
          </a>
          <EmbedConsentReset />
        </div>
      </section>
    </main>
  );
}

const DISTRICT_UNIFORMS = [
  { code: "OBJ-001", name: "District hoodie", line: "GRÜNLICHTBEZIRK · heavy" },
  { code: "OBJ-002", name: "Bass tee", line: "GRÜNLICHTBEZIRK · oversized" },
  { code: "OBJ-003", name: "Signal longsleeve", line: "GRÜNLICHTBEZIRK · cold" },
  { code: "OBJ-004", name: "Limited beanie", line: "GRÜNLICHTBEZIRK · run" },
  { code: "OBJ-005", name: "Poster", line: "GRÜNLICHTBEZIRK · paper" },
  { code: "OBJ-006", name: "Sticker sheet", line: "GRÜNLICHTBEZIRK · vinyl" }
] as const;

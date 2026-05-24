"use client";

import { useEffect, useState } from "react";

type SoundEmbedProps = Readonly<{
  /** A full iframe `src` URL the operator pastes from Spotify / SoundCloud. */
  src: string | null | undefined;
  title: string;
  /** Render label when nothing is wired yet. */
  offlineLabel?: string;
}>;

/**
 * S67 — Consent-gated music embed.
 *
 * Three states:
 *   1. No URL configured → "transmission offline" placeholder.
 *   2. URL configured, no consent yet → consent panel. **No iframe in DOM.**
 *   3. URL configured + consent granted → iframe renders.
 *
 * Consent is stored in localStorage under `sk_embed_consent` and applies
 * to both Spotify and SoundCloud embeds on the same domain. We never set
 * cookies. We never make a network call to Spotify / SoundCloud before
 * the user clicks "Signal laden".
 */
const CONSENT_KEY = "sk_embed_consent";
const CONSENT_VALUE = "granted";

function readConsent(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(CONSENT_KEY) === CONSENT_VALUE;
  } catch {
    // localStorage disabled / SSR / private mode — treat as no consent.
    return false;
  }
}

function writeConsent(granted: boolean): void {
  if (typeof window === "undefined") return;
  try {
    if (granted) {
      window.localStorage.setItem(CONSENT_KEY, CONSENT_VALUE);
    } else {
      window.localStorage.removeItem(CONSENT_KEY);
    }
    // Notify peer components on the same page.
    window.dispatchEvent(new CustomEvent("sk-embed-consent"));
  } catch {
    // localStorage unavailable — silently no-op.
  }
}

export function SoundEmbed({ src, title, offlineLabel }: SoundEmbedProps) {
  const [consent, setConsent] = useState(false);

  // Read consent on mount + listen for cross-component updates.
  useEffect(() => {
    setConsent(readConsent());
    const onChange = () => setConsent(readConsent());
    window.addEventListener("sk-embed-consent", onChange);
    window.addEventListener("storage", onChange);
    return () => {
      window.removeEventListener("sk-embed-consent", onChange);
      window.removeEventListener("storage", onChange);
    };
  }, []);

  // --- State 1: no URL configured ---
  if (!src) {
    return (
      <div
        role="status"
        aria-label={`${title} — ${offlineLabel ?? "transmission offline"}`}
        className="relative flex aspect-[16/9] flex-col justify-between gap-6 border border-stone-800 p-5 font-mono text-[0.55rem] font-black uppercase tracking-[0.28em] text-stone-500 sm:text-xs md:aspect-[2/1] md:p-8"
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, rgba(255,255,255,0.4) 0 1px, transparent 1px 3px)"
          }}
        />
        <div className="relative flex items-start justify-between gap-4">
          <span className="text-stone-500">
            {offlineLabel ?? "transmission offline"}
          </span>
          <span className="text-red-600">●</span>
        </div>
        <div className="relative space-y-1">
          <p className="text-stone-100">{title}</p>
          <p className="text-stone-600">no placeholder player on purpose.</p>
        </div>
      </div>
    );
  }

  // --- State 2: URL configured but consent not granted ---
  if (!consent) {
    return (
      <div
        role="region"
        aria-label={`${title} — Einwilligung erforderlich`}
        className="relative flex aspect-[16/9] flex-col justify-between gap-6 border border-stone-800 p-5 font-mono text-[0.55rem] uppercase tracking-[0.28em] text-stone-500 sm:text-xs md:aspect-[2/1] md:p-8"
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, rgba(255,255,255,0.4) 0 1px, transparent 1px 3px)"
          }}
        />
        <div className="relative flex items-start justify-between gap-4">
          <span className="font-black text-stone-500">{title}</span>
          <span className="text-red-600">●</span>
        </div>
        <div className="relative space-y-3">
          <p className="font-black text-stone-100">
            Externe Inhalte blockiert.
          </p>
          <p className="text-stone-400">
            Spotify / SoundCloud können externe Inhalte und Cookies laden.
          </p>
          <div className="flex flex-wrap gap-2 pt-2">
            <button
              type="button"
              onClick={() => {
                writeConsent(true);
                setConsent(true);
              }}
              className="border border-stone-100 px-3 py-2 font-black uppercase tracking-[0.22em] text-stone-100 transition hover:bg-stone-100 hover:text-stone-900"
            >
              Signal laden
            </button>
            <p className="self-center text-[0.5rem] tracking-[0.22em] text-stone-600">
              gilt für alle Musik-Embeds auf dieser Seite.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // --- State 3: URL + consent → render iframe ---
  return (
    <div className="border border-stone-800">
      <iframe
        src={src}
        title={title}
        loading="lazy"
        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
        className="block w-full"
        style={{ height: "380px", border: "0" }}
      />
    </div>
  );
}

/**
 * Small client control that lets the operator-visible footer revoke the
 * embed consent again. Renders nothing if consent isn't currently granted.
 */
export function EmbedConsentReset({ className }: Readonly<{ className?: string }>) {
  const [consent, setConsent] = useState(false);

  useEffect(() => {
    setConsent(readConsent());
    const onChange = () => setConsent(readConsent());
    window.addEventListener("sk-embed-consent", onChange);
    window.addEventListener("storage", onChange);
    return () => {
      window.removeEventListener("sk-embed-consent", onChange);
      window.removeEventListener("storage", onChange);
    };
  }, []);

  if (!consent) return null;

  return (
    <button
      type="button"
      onClick={() => {
        writeConsent(false);
        setConsent(false);
      }}
      className={
        className ??
        "font-mono text-[0.5rem] uppercase tracking-[0.28em] text-stone-500 hover:text-stone-100"
      }
    >
      Einwilligung zurücksetzen
    </button>
  );
}

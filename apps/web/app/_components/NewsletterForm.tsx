"use client";

import { useState, type FormEvent } from "react";

type NewsletterFormProps = Readonly<{
  /**
   * URL that receives the operator's email. The operator wires this to the
   * inference service public route:
   *   POST /v1/public/newsletter/subscribe
   * If empty, the form renders but submission is a no-op (offline mode).
   */
  endpoint?: string;
  /**
   * Source allowlist value sent to the server. The server filters this
   * against `ALLOWED_SOURCES`; unknown values are dropped silently.
   */
  source?: string;
}>;

type SubscribeStatus = "subscribed" | "pending" | "offline" | "failed";

type FormState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "subscribed" }
  | { kind: "pending" }
  | { kind: "offline" }
  | { kind: "failed"; reason: string };

const SUCCESS_COPY: Record<SubscribeStatus, string> = {
  subscribed: "Signal empfangen. Check dein Postfach.",
  pending: "Fast drin. Bitte bestätige deine Anmeldung per E-Mail.",
  offline: "Signal-Endpunkt offline. Keine Anmeldung gespeichert.",
  failed: "Signal gestört. Versuch es später erneut."
};

/**
 * SIGNAL — newsletter capture.
 *
 * Submits to the public subscribe endpoint and reads the server's `status`
 * field. We NEVER show success on `offline`. We NEVER echo the raw email.
 */
export function NewsletterForm({ endpoint, source }: NewsletterFormProps) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<FormState>({ kind: "idle" });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!endpoint) {
      // No endpoint configured on the page — honest offline state.
      setState({ kind: "offline" });
      return;
    }
    setState({ kind: "loading" });
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          email,
          source,
          tags: ["snuffragga", "signal"]
        })
      });

      // Try to read the JSON envelope even on non-2xx — the backend uses
      // 200 + `status="offline"` for the offline-unconfigured case.
      let raw: unknown = null;
      try {
        raw = await res.json();
      } catch {
        raw = null;
      }
      const status =
        raw && typeof raw === "object" && "status" in raw
          ? ((raw as { status?: unknown }).status as SubscribeStatus | undefined)
          : undefined;
      if (status === "subscribed") {
        setState({ kind: "subscribed" });
        setEmail("");
      } else if (status === "pending") {
        setState({ kind: "pending" });
        setEmail("");
      } else if (status === "offline") {
        setState({ kind: "offline" });
      } else if (status === "failed") {
        setState({ kind: "failed", reason: "upstream" });
      } else if (!res.ok) {
        setState({ kind: "failed", reason: `http_${res.status}` });
      } else {
        // 2xx without a recognized status — refuse to guess success.
        setState({ kind: "failed", reason: "unknown_response" });
      }
    } catch (err) {
      setState({
        kind: "failed",
        reason: err instanceof Error ? "network" : "unknown"
      });
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-3 md:flex-row md:items-stretch">
        <label className="sr-only" htmlFor="newsletter-email">
          Email
        </label>
        <input
          id="newsletter-email"
          type="email"
          required
          autoComplete="email"
          placeholder="your.signal@frequency.net"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="flex-1 border border-stone-800 bg-transparent px-4 py-3 font-mono text-sm tracking-[0.1em] text-stone-100 placeholder:text-stone-600 focus:border-stone-100 focus:outline-none"
        />
        <button
          type="submit"
          disabled={state.kind === "loading"}
          className="border border-stone-100 px-5 py-3 font-black uppercase tracking-[0.22em] text-stone-100 transition hover:bg-stone-100 hover:text-stone-900 disabled:opacity-50"
        >
          {state.kind === "loading" ? "transmitting…" : "join signal"}
        </button>
      </div>

      {state.kind === "subscribed" && (
        <p
          aria-live="polite"
          className="font-mono text-xs uppercase tracking-[0.22em] text-stone-100"
        >
          {SUCCESS_COPY.subscribed}
        </p>
      )}
      {state.kind === "pending" && (
        <p
          aria-live="polite"
          className="font-mono text-xs uppercase tracking-[0.22em] text-stone-100"
        >
          {SUCCESS_COPY.pending}
        </p>
      )}
      {state.kind === "offline" && (
        <p
          aria-live="polite"
          className="font-mono text-xs uppercase tracking-[0.22em] text-stone-500"
        >
          {SUCCESS_COPY.offline}
        </p>
      )}
      {state.kind === "failed" && (
        <p
          aria-live="polite"
          className="font-mono text-xs uppercase tracking-[0.22em] text-red-600"
        >
          {SUCCESS_COPY.failed}
        </p>
      )}
    </form>
  );
}

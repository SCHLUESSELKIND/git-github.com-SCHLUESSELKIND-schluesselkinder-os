/**
 * Server-side proxy for the internal soundsystem inference service.
 *
 * The browser only ever calls relative `/admin/api/soundsystem/*`. This
 * handler is the single bridge to the inference service, gated by the
 * `/admin` middleware. No NEXT_PUBLIC_* inference URL is required in
 * production.
 *
 * Strips browser-side auth (`authorization`, `cookie`) before forwarding
 * — the inference service is not reached on the operator's session
 * credentials; it lives on a private network. Returns honest 502/503 when
 * upstream is unreachable, never leaks the upstream URL in error bodies.
 */
import type { NextRequest } from "next/server";
import {
  ADMIN_ROBOTS_HEADER,
  inferenceServerBaseUrl
} from "../../../_lib/admin-gate";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade"
]);

const STRIPPED_REQUEST_HEADERS = new Set([
  ...HOP_BY_HOP,
  "host",
  "cookie",
  "authorization",
  "accept-encoding"
]);

const STRIPPED_RESPONSE_HEADERS = new Set([
  ...HOP_BY_HOP,
  "set-cookie",
  "server",
  "x-powered-by"
]);

/**
 * Resolve operator identity from the browser's Basic Auth header.
 * Returns the username portion of the Basic Auth credentials, or null.
 */
function resolveOperatorFromBasicAuth(input: Headers): string | null {
  const auth = input.get("authorization");
  if (!auth || !auth.toLowerCase().startsWith("basic ")) return null;
  try {
    const decoded = atob(auth.slice(6).trim());
    const sep = decoded.indexOf(":");
    return sep >= 0 ? decoded.slice(0, sep) : null;
  } catch {
    return null;
  }
}

function buildForwardHeaders(input: Headers): Headers {
  const out = new Headers();
  for (const [name, value] of input) {
    if (STRIPPED_REQUEST_HEADERS.has(name.toLowerCase())) continue;
    out.set(name, value);
  }

  // Inject service-to-service API key (S25: Auth + Operator Identity)
  const apiKey = process.env.SOUNDSYSTEM_API_KEY;
  if (apiKey) {
    out.set("Authorization", `Bearer ${apiKey}`);
  }

  // Inject operator identity from browser Basic Auth
  const operatorId = resolveOperatorFromBasicAuth(input);
  if (operatorId) {
    out.set("X-Operator-Id", operatorId);
    // Role resolved server-side from operator registry; default hint for proxy
    out.set("X-Operator-Role", "owner");
  }

  return out;
}

function buildResponseHeaders(input: Headers): Headers {
  const out = new Headers();
  for (const [name, value] of input) {
    if (STRIPPED_RESPONSE_HEADERS.has(name.toLowerCase())) continue;
    out.set(name, value);
  }
  out.set("X-Robots-Tag", ADMIN_ROBOTS_HEADER);
  out.set("Cache-Control", "no-store");
  return out;
}

function errorResponse(status: number, detail: string): Response {
  return new Response(JSON.stringify({ detail }), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Robots-Tag": ADMIN_ROBOTS_HEADER,
      "Cache-Control": "no-store"
    }
  });
}

async function forward(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
): Promise<Response> {
  const { path } = await ctx.params;
  const upstreamBase = inferenceServerBaseUrl();
  const subPath = path && path.length > 0 ? "/" + path.map(encodeURIComponent).join("/") : "/";
  const search = req.nextUrl.search ?? "";
  const upstreamUrl = `${upstreamBase}${subPath}${search}`;

  const init: RequestInit & { duplex?: "half" } = {
    method: req.method,
    headers: buildForwardHeaders(req.headers),
    cache: "no-store",
    redirect: "manual"
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      init.body = await req.arrayBuffer();
    } catch {
      return errorResponse(400, "proxy_request_body_unreadable");
    }
  }

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, init);
  } catch (error) {
    return errorResponse(
      502,
      `inference_unreachable · ${error instanceof Error ? error.name : "fetch_failed"}`
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: buildResponseHeaders(upstream.headers)
  });
}

export const dynamic = "force-dynamic";

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
export const OPTIONS = forward;

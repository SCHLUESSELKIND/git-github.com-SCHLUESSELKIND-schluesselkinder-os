/**
 * Server-side admin gate for /admin/*.
 *
 * Runs in the Edge runtime ahead of every admin route and admin-API
 * proxy. Reads server-side env vars only — NEXT_PUBLIC_* is local-dev
 * convenience, never production security.
 *
 * Behaviour:
 *   - INTERNAL_CONSOLE_ENABLED != "true"            → 404 (fail closed)
 *   - production + basic-auth env not configured    → 404 (fail closed)
 *   - basic-auth required but missing/invalid       → 401 with WWW-Authenticate
 *   - else                                          → proceed; add X-Robots-Tag
 */
import { NextResponse, type NextRequest } from "next/server";
import {
  ADMIN_ROBOTS_HEADER,
  adminBasicAuthConfigured,
  adminBasicAuthRequired,
  adminBasicAuthVerify,
  isInternalConsoleEnabled
} from "./app/admin/_lib/admin-gate";

const BASIC_REALM = 'Basic realm="schluesselkinder-admin", charset="UTF-8"';

function notFound(): NextResponse {
  return new NextResponse(null, {
    status: 404,
    headers: { "X-Robots-Tag": ADMIN_ROBOTS_HEADER }
  });
}

function unauthorized(): NextResponse {
  return new NextResponse("Authentication required.", {
    status: 401,
    headers: {
      "WWW-Authenticate": BASIC_REALM,
      "X-Robots-Tag": ADMIN_ROBOTS_HEADER,
      "Content-Type": "text/plain; charset=utf-8"
    }
  });
}

export function middleware(req: NextRequest) {
  if (!isInternalConsoleEnabled()) {
    return notFound();
  }

  if (process.env.NODE_ENV === "production" && !adminBasicAuthConfigured()) {
    return notFound();
  }

  if (adminBasicAuthRequired()) {
    const ok = adminBasicAuthVerify(req.headers.get("authorization"));
    if (!ok) return unauthorized();
  }

  const res = NextResponse.next();
  res.headers.set("X-Robots-Tag", ADMIN_ROBOTS_HEADER);
  return res;
}

export const config = {
  matcher: ["/admin/:path*"]
};

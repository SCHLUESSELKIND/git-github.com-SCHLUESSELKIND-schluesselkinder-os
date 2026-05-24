/**
 * Server-side admin gate helpers.
 *
 * These run in both the Next.js Edge middleware and in server components.
 * They must not read NEXT_PUBLIC_* env vars for production decisions; that
 * surface is browser-visible and therefore unsuitable for security.
 *
 * Local-dev fallback to NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED is allowed only
 * when NODE_ENV !== "production".
 */

export const ADMIN_ROBOTS_HEADER = "noindex, nofollow, noarchive";

export function isInternalConsoleEnabled(): boolean {
  if (process.env.INTERNAL_CONSOLE_ENABLED === "true") return true;
  if (process.env.NODE_ENV !== "production") {
    return process.env.NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED === "true";
  }
  return false;
}

export function adminBasicAuthConfigured(): boolean {
  return Boolean(
    process.env.ADMIN_BASIC_AUTH_USER && process.env.ADMIN_BASIC_AUTH_PASSWORD
  );
}

/**
 * Production posture: basic auth must be configured.
 * Dev posture: optional — operators can run without auth if both env vars
 * are unset.
 */
export function adminBasicAuthRequired(): boolean {
  if (process.env.NODE_ENV === "production") return true;
  return adminBasicAuthConfigured();
}

export function adminBasicAuthVerify(
  authorizationHeader: string | null | undefined
): boolean {
  const user = process.env.ADMIN_BASIC_AUTH_USER;
  const pass = process.env.ADMIN_BASIC_AUTH_PASSWORD;
  if (!user || !pass) {
    // Caller should fail closed before reaching this state in production.
    return process.env.NODE_ENV !== "production";
  }
  if (!authorizationHeader) return false;
  if (!authorizationHeader.toLowerCase().startsWith("basic ")) return false;
  let decoded: string;
  try {
    decoded = atob(authorizationHeader.slice(6).trim());
  } catch {
    return false;
  }
  const sep = decoded.indexOf(":");
  if (sep < 0) return false;
  const providedUser = decoded.slice(0, sep);
  const providedPass = decoded.slice(sep + 1);
  return providedUser === user && providedPass === pass;
}

export function inferenceServerBaseUrl(): string {
  const explicit =
    process.env.SOUNDSYSTEM_INFERENCE_URL ||
    process.env.NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL ||
    "http://127.0.0.1:8010";
  return explicit.replace(/\/$/, "");
}

export function inferenceServerConfigured(): boolean {
  return Boolean(
    process.env.SOUNDSYSTEM_INFERENCE_URL ||
      process.env.NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL
  );
}

#!/usr/bin/env bash
# Local verification for the SNUFFRAGGA public surface.
#
# Runs every check that can be done without authenticated provider access:
#   - Next.js typecheck
#   - Next.js build (catches static rendering errors)
#   - grep guards for hardcoded Spotify / SoundCloud URLs
#   - grep proof that SoundEmbed carries the consent key
#   - grep proof that NewsletterForm handles the four backend statuses
#   - git diff --check (whitespace / merge markers)
#
# Does NOT touch production hosts, DNS, Shopify, Printful, Spotify,
# SoundCloud, or Listmonk. No secrets required.
#
# Exit code 0 = green, non-zero = blocker found.

set -e
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN="$(printf '\033[1;32m')"
RED="$(printf '\033[1;31m')"
YELLOW="$(printf '\033[1;33m')"
DIM="$(printf '\033[2m')"
RESET="$(printf '\033[0m')"

PASS=0
FAIL=0

pass() { echo "${GREEN}✓${RESET} $1"; PASS=$((PASS+1)); }
fail() { echo "${RED}✗${RESET} $1"; FAIL=$((FAIL+1)); }
info() { echo "${DIM}  $1${RESET}"; }
section() { echo; echo "${YELLOW}== $1 ==${RESET}"; }

# ---------------------------------------------------------------------------
section "Static guards — no hardcoded provider URLs in React"
# ---------------------------------------------------------------------------

SPOTIFY_HARDCODE="$(grep -rEn "open\.spotify\.com/(embed|artist)" apps/web/app/ apps/web/lib/ 2>/dev/null || true)"
if [[ -z "$SPOTIFY_HARDCODE" ]]; then
  pass "no Spotify URL hardcoded in apps/web/app/ or apps/web/lib/"
else
  fail "Spotify URL appears in source — must come from env only"
  echo "$SPOTIFY_HARDCODE" | head -5 | sed 's/^/    /'
fi

SOUNDCLOUD_HARDCODE="$(grep -rEn "w\.soundcloud\.com/player|api\.soundcloud\.com" apps/web/app/ apps/web/lib/ 2>/dev/null || true)"
if [[ -z "$SOUNDCLOUD_HARDCODE" ]]; then
  pass "no SoundCloud URL hardcoded in apps/web/app/ or apps/web/lib/"
else
  fail "SoundCloud URL appears in source — must come from env only"
  echo "$SOUNDCLOUD_HARDCODE" | head -5 | sed 's/^/    /'
fi

# ---------------------------------------------------------------------------
section "Consent gate — SoundEmbed must carry the consent key"
# ---------------------------------------------------------------------------

EMBED_FILE="apps/web/app/_components/SoundEmbed.tsx"
if [[ -f "$EMBED_FILE" ]]; then
  if grep -q "sk_embed_consent" "$EMBED_FILE"; then
    pass "SoundEmbed references localStorage key 'sk_embed_consent'"
  else
    fail "SoundEmbed missing 'sk_embed_consent' key — consent gate broken"
  fi
  if grep -q "Signal laden" "$EMBED_FILE"; then
    pass "SoundEmbed renders 'Signal laden' consent CTA"
  else
    fail "SoundEmbed missing 'Signal laden' button — visitors can't grant consent"
  fi
else
  fail "$EMBED_FILE not found"
fi

# ---------------------------------------------------------------------------
section "Newsletter form — must handle four backend statuses"
# ---------------------------------------------------------------------------

FORM_FILE="apps/web/app/_components/NewsletterForm.tsx"
if [[ -f "$FORM_FILE" ]]; then
  MISSING=0
  for status in "subscribed" "pending" "offline" "failed"; do
    if grep -q "\"$status\"" "$FORM_FILE"; then
      pass "NewsletterForm handles status='$status'"
    else
      fail "NewsletterForm does not branch on status='$status'"
      MISSING=$((MISSING+1))
    fi
  done

  # Sanity check: the offline branch must NOT alias the success branch.
  # We grep for the canonical offline German copy.
  if grep -q "Signal-Endpunkt offline" "$FORM_FILE"; then
    pass "NewsletterForm renders 'Signal-Endpunkt offline' on offline status"
  else
    fail "NewsletterForm missing offline copy — risk of fake success"
  fi
else
  fail "$FORM_FILE not found"
fi

# ---------------------------------------------------------------------------
section "Page imports — consent reset link present"
# ---------------------------------------------------------------------------

PAGE_FILE="apps/web/app/artists/snuffragga/page.tsx"
if [[ -f "$PAGE_FILE" ]]; then
  if grep -q "EmbedConsentReset" "$PAGE_FILE"; then
    pass "SNUFFRAGGA page mounts <EmbedConsentReset />"
  else
    fail "SNUFFRAGGA page missing EmbedConsentReset — visitors can't revoke consent"
  fi
  if grep -q "process.env.NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED" "$PAGE_FILE"; then
    pass "SNUFFRAGGA page reads SPOTIFY_EMBED from env"
  else
    fail "SNUFFRAGGA page not reading SPOTIFY_EMBED from env"
  fi
  if grep -q "process.env.NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED" "$PAGE_FILE"; then
    pass "SNUFFRAGGA page reads SOUNDCLOUD_EMBED from env"
  else
    fail "SNUFFRAGGA page not reading SOUNDCLOUD_EMBED from env"
  fi
else
  fail "$PAGE_FILE not found"
fi

# ---------------------------------------------------------------------------
section "Docs — all four env vars documented in .env.example"
# ---------------------------------------------------------------------------

ENV_EXAMPLE="apps/web/.env.example"
if [[ -f "$ENV_EXAMPLE" ]]; then
  for var in \
    "NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED" \
    "NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED" \
    "NEXT_PUBLIC_NEWSLETTER_ENDPOINT" \
    "NEXT_PUBLIC_SHOP_URL"; do
    if grep -q "^${var}=" "$ENV_EXAMPLE"; then
      pass "$var documented in .env.example"
    else
      fail "$var missing from .env.example"
    fi
  done
else
  fail "$ENV_EXAMPLE not found"
fi

# ---------------------------------------------------------------------------
section "Whitespace / merge markers"
# ---------------------------------------------------------------------------

if git diff --check >/dev/null 2>&1; then
  pass "git diff --check clean"
else
  fail "git diff --check reports whitespace or merge marker issues"
  git diff --check 2>&1 | head -5 | sed 's/^/    /'
fi

# ---------------------------------------------------------------------------
section "TypeScript typecheck"
# ---------------------------------------------------------------------------

if npx pnpm --filter='@schluesselkinder/web' typecheck >/dev/null 2>&1; then
  pass "pnpm typecheck"
else
  fail "pnpm typecheck failed — run it manually to see details"
fi

# ---------------------------------------------------------------------------
section "Next.js production build"
# ---------------------------------------------------------------------------

BUILD_LOG="$(mktemp)"
trap 'rm -f "$BUILD_LOG"' EXIT
if npx pnpm --filter='@schluesselkinder/web' build > "$BUILD_LOG" 2>&1; then
  pass "pnpm build"
  # Next.js build output includes the route inside a box-drawing tree.
  # Match the route token anywhere on a line, alongside the static/dynamic glyph.
  if grep -qE "/artists/snuffragga($|[^[:alnum:]])" "$BUILD_LOG"; then
    pass "/artists/snuffragga appears in build manifest"
  else
    fail "/artists/snuffragga not found in build manifest"
  fi
else
  fail "pnpm build failed — see log:"
  tail -20 "$BUILD_LOG" | sed 's/^/    /'
fi

# ---------------------------------------------------------------------------
echo
echo "${YELLOW}== Result ==${RESET}"
echo "  pass: $PASS"
echo "  fail: $FAIL"
echo
if (( FAIL > 0 )); then
  echo "${RED}NOT READY FOR LAUNCH${RESET}"
  exit 1
fi
echo "${GREEN}all static checks green${RESET}"
echo "${DIM}This does NOT prove production is wired — env vars on the${RESET}"
echo "${DIM}hosting provider panel still need to be set + redeployed.${RESET}"
echo "${DIM}Run docs/deployment/SNUFFRAGGA_SMOKE_TEST.md against the live URL.${RESET}"
exit 0

#!/usr/bin/env bash
# Safe Coolify deployment helper for SCHLUESSELKINDER routing.
#
# Dry-run by default. Mutating actions require `--apply` AND the relevant
# env vars to be present in the operator's shell. The script NEVER:
#   - echoes COOLIFY_API_TOKEN to stdout
#   - writes COOLIFY_API_TOKEN to disk
#   - guesses Coolify API endpoint shapes (the repo carries no verified
#     reference; mutating API calls are TODO + clear warning)
#   - touches shop.schluesselkinder.de
#   - restarts production without explicit operator opt-in
#
# Usage:
#   scripts/coolify_snuffragga_setup.sh check
#   scripts/coolify_snuffragga_setup.sh print-routing-plan
#   scripts/coolify_snuffragga_setup.sh set-web-env
#   scripts/coolify_snuffragga_setup.sh smoke-test
#   scripts/coolify_snuffragga_setup.sh apply-domains   # not implemented
#
# Add `--apply` to actually call the Coolify API (only `set-web-env`
# supports it once the operator wires the endpoint locally; see TODO).
#
# Required env vars (only when invoking an action that needs them):
#   COOLIFY_URL              e.g. https://coolify.your-host.tld
#   COOLIFY_API_TOKEN        Coolify v4 API token (Settings → API Tokens)
#   COOLIFY_WEB_APP_ID       Application UUID for apps/web (Next.js)
#   COOLIFY_API_APP_ID       Application UUID for the FastAPI inference service
#   COOLIFY_LISTMONK_APP_ID  Application UUID for Listmonk

set -u
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN="$(printf '\033[1;32m')"
RED="$(printf '\033[1;31m')"
YELLOW="$(printf '\033[1;33m')"
DIM="$(printf '\033[2m')"
BOLD="$(printf '\033[1m')"
RESET="$(printf '\033[0m')"

APPLY=0
ACTION=""

# ---------- Argument parsing ----------
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    check|print-routing-plan|set-web-env|smoke-test|apply-domains|help|"")
      ACTION="$arg"
      ;;
    -h|--help) ACTION="help" ;;
    *)
      echo "${RED}unknown argument: $arg${RESET}" >&2
      ACTION="help"
      ;;
  esac
done

usage() {
  cat <<'EOF'
SCHLUESSELKINDER Coolify helper — safe by default

actions:
  check                  Verify required env vars are present + probe COOLIFY_URL
  print-routing-plan     Print the desired routing table + Coolify UI steps
  set-web-env            Print the four NEXT_PUBLIC_* env vars + manual setting instructions
  smoke-test             Delegate to scripts/smoke_snuffragga_public.sh
  apply-domains          NOT IMPLEMENTED — see TODO; manual Coolify steps printed
  help                   Show this message

flags:
  --apply                Required for any action that mutates Coolify. Without
                         it the script is read-only / advisory. Mutating
                         actions also require the relevant env vars; if any
                         are missing the script lists them and exits non-zero.

This script NEVER echoes COOLIFY_API_TOKEN. It also does not assume any
Coolify API endpoint shape — mutating actions are intentionally left as
operator manual steps until a verified API reference lands in the repo.
EOF
}

# Render a short banner that tells the operator what mode we're in.
banner() {
  echo
  echo "${YELLOW}== SCHLUESSELKINDER Coolify helper ==${RESET}"
  if (( APPLY )); then
    echo "${RED}${BOLD}APPLY MODE — mutating actions will be attempted${RESET}"
  else
    echo "${DIM}dry-run (default). Add --apply to enable mutating actions.${RESET}"
  fi
  echo
}

# ---------- Required env var checks ----------
require_env() {
  local missing=()
  for k in "$@"; do
    if [[ -z "${!k:-}" ]]; then
      missing+=("$k")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    echo "${RED}missing required env var(s):${RESET}" >&2
    for k in "${missing[@]}"; do echo "  $k" >&2; done
    echo >&2
    echo "${DIM}Export these in your shell before re-running. Never commit them.${RESET}" >&2
    return 1
  fi
  return 0
}

# Mask a token for any debug output. Never used to display the token itself.
masked_token_summary() {
  local t="${COOLIFY_API_TOKEN:-}"
  if [[ -z "$t" ]]; then
    echo "unset"
  else
    # Length only; never echo bytes.
    echo "set, length=${#t}"
  fi
}

# ---------- Probe Coolify connectivity (HEAD request only) ----------
probe_coolify() {
  if ! require_env COOLIFY_URL; then return 1; fi
  echo "Probing $COOLIFY_URL …"
  local code
  code="$(curl -ksS -o /dev/null -w "%{http_code}" --max-time 10 \
    -H "Accept: application/json" \
    "${COOLIFY_URL%/}/api/v1/health" 2>/dev/null || echo "ERR")"
  if [[ "$code" =~ ^(200|204|301|302|401|404)$ ]]; then
    # 401/404 from /api/v1/health is fine — the server is up. We just want
    # to confirm we can reach it. Real endpoint shapes are not verified.
    echo "  ${GREEN}reachable${RESET} (http $code)"
    return 0
  fi
  echo "  ${RED}unreachable${RESET} (response: $code)"
  echo "  Likely causes: COOLIFY_URL wrong, Coolify down, or VPN required."
  return 1
}

# ---------- Action: check ----------
action_check() {
  banner
  echo "${BOLD}1. Required env vars${RESET}"
  local optional_keys=(COOLIFY_WEB_APP_ID COOLIFY_API_APP_ID COOLIFY_LISTMONK_APP_ID)
  local status=0
  for k in COOLIFY_URL COOLIFY_API_TOKEN; do
    if [[ -n "${!k:-}" ]]; then
      if [[ "$k" == "COOLIFY_API_TOKEN" ]]; then
        echo "  ${GREEN}✓${RESET} $k (masked: $(masked_token_summary))"
      else
        echo "  ${GREEN}✓${RESET} $k = ${!k}"
      fi
    else
      echo "  ${RED}✗${RESET} $k missing"
      status=1
    fi
  done
  for k in "${optional_keys[@]}"; do
    if [[ -n "${!k:-}" ]]; then
      echo "  ${GREEN}✓${RESET} $k = ${!k}"
    else
      echo "  ${DIM}·${RESET} $k unset (only needed for app-targeted actions)"
    fi
  done
  echo

  echo "${BOLD}2. Coolify connectivity${RESET}"
  if [[ -n "${COOLIFY_URL:-}" ]]; then
    probe_coolify || status=1
  else
    echo "  ${DIM}skipped — COOLIFY_URL unset${RESET}"
    status=1
  fi
  echo

  echo "${BOLD}3. Local repo invariants${RESET}"
  if grep -q "sk_embed_consent" apps/web/app/_components/SoundEmbed.tsx 2>/dev/null; then
    echo "  ${GREEN}✓${RESET} consent gate present in SoundEmbed"
  else
    echo "  ${RED}✗${RESET} consent gate missing in SoundEmbed"
    status=1
  fi
  if grep -q "process.env.NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED" \
       apps/web/app/artists/snuffragga/page.tsx 2>/dev/null; then
    echo "  ${GREEN}✓${RESET} SNUFFRAGGA page reads env vars"
  else
    echo "  ${RED}✗${RESET} SNUFFRAGGA page not reading env vars"
    status=1
  fi
  echo
  return $status
}

# ---------- Action: print-routing-plan ----------
action_print_routing_plan() {
  banner
  cat <<EOF
${BOLD}Desired routing${RESET}

  schluesselkinder.de             →  apps/web (Next.js)
  www.schluesselkinder.de         →  redirect 301 → schluesselkinder.de
  api.schluesselkinder.de         →  services/soundsystem-inference (FastAPI)
  listmonk.schluesselkinder.de    →  Listmonk container
  shop.schluesselkinder.de        →  Shopify (NEVER routed through Coolify)

${BOLD}DNS (must match — do NOT change unless DNS is wrong)${RESET}

  schluesselkinder.de             A      178.104.103.37
  www.schluesselkinder.de         A      178.104.103.37
  api.schluesselkinder.de         A      178.104.103.37
  listmonk.schluesselkinder.de    A      178.104.103.37
  shop.schluesselkinder.de        CNAME  shops.myshopify.com

${BOLD}Coolify manual steps${RESET}

  1. Open Coolify dashboard.
  2. apps/web application → Domains: list ${BOLD}schluesselkinder.de${RESET} +
     ${BOLD}www.schluesselkinder.de${RESET}. Add redirect www → root via custom
     Caddy/Nginx snippet, OR mark www as redirect alias.
  3. apps/web → Environment Variables → add the four NEXT_PUBLIC_* values
     (run: ${BOLD}$0 set-web-env${RESET} for the exact lines). Mark each
     as ${BOLD}build-time${RESET}.
  4. apps/web → Redeploy ${BOLD}without build cache${RESET}.
  5. FastAPI inference application → Domains: add ${BOLD}api.schluesselkinder.de${RESET}.
     Wait for Let's Encrypt cert to issue.
  6. Listmonk application → Domains: add ${BOLD}listmonk.schluesselkinder.de${RESET}.
     Same cert flow.
  7. Run: ${BOLD}bash scripts/smoke_snuffragga_public.sh${RESET} until it
     returns exit 0.
EOF
}

# ---------- Action: set-web-env ----------
action_set_web_env() {
  banner
  cat <<'EOF'
The four NEXT_PUBLIC_* env vars the apps/web Next.js app needs. These are
build-time variables — setting them on a running container without a fresh
build will NOT change what the browser sees.

  NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED=https://open.spotify.com/embed/artist/1jzZXWDrVb0jDp32zxcqc2?utm_source=generator
  NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED=https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/thomas-frerich-681624781%3Futm_source%3Dclipboard%26utm_medium%3Dtext%26utm_campaign%3Dsocial_sharing
  NEXT_PUBLIC_NEWSLETTER_ENDPOINT=https://api.schluesselkinder.de/v1/public/newsletter/subscribe
  NEXT_PUBLIC_SHOP_URL=https://shop.schluesselkinder.de

Coolify UI steps:
  1. Application → apps/web → Environment Variables
  2. Add each row above. Mark each as "Build variable" / "Available at
     build time".
  3. Save.
  4. Redeploy with "Use existing build cache" OFF.

Verification after redeploy:
  bash scripts/smoke_snuffragga_public.sh
EOF

  if (( APPLY )); then
    echo
    echo "${RED}${BOLD}--apply requested for set-web-env${RESET}"
    echo "${RED}Coolify API mutation is NOT implemented in this script.${RESET}"
    echo
    echo "${DIM}Rationale: this repo carries no verified Coolify API reference.${RESET}"
    echo "${DIM}Guessing the endpoint shape risks silently posting to the wrong${RESET}"
    echo "${DIM}URL or sending the token in the wrong header. Until a verified${RESET}"
    echo "${DIM}helper lands here, set the env vars via the Coolify UI above.${RESET}"
    echo
    echo "${YELLOW}TODO: implement once a Coolify v4 API reference is committed to${RESET}"
    echo "${YELLOW}docs/deployment/ and signed off. See COOLIFY_SCHLUESSELKINDER_ROUTING.md${RESET}"
    echo "${YELLOW}'Future automation' section.${RESET}"
    return 2
  fi
}

# ---------- Action: smoke-test (delegate) ----------
action_smoke_test() {
  banner
  exec bash "$REPO_ROOT/scripts/smoke_snuffragga_public.sh"
}

# ---------- Action: apply-domains (intentionally not implemented) ----------
action_apply_domains() {
  banner
  echo "${RED}${BOLD}apply-domains is intentionally NOT implemented.${RESET}"
  echo
  cat <<'EOF'
Why: this repository does not yet carry a verified Coolify v4 API
reference. Adding a domain on the wrong app, or to the wrong tenant, can
trigger Let's Encrypt rate-limiting (5 failures/hour per hostname). Guessing
the endpoint shape is not acceptable for a production-modifying action.

Until a verified Coolify API helper lands here (see "Future automation" in
docs/deployment/COOLIFY_SCHLUESSELKINDER_ROUTING.md), add domains via the
Coolify UI:

  apps/web         → Domains tab → add schluesselkinder.de + www.schluesselkinder.de
  FastAPI service  → Domains tab → add api.schluesselkinder.de
  Listmonk         → Domains tab → add listmonk.schluesselkinder.de
  Shopify shop     → DO NOT add to Coolify

Each domain triggers a Caddy reload + Let's Encrypt ACME challenge. Watch
the Coolify logs for the ACME challenge to complete (~30 s).
EOF
  return 2
}

# ---------- Dispatch ----------
case "$ACTION" in
  "" | help)
    usage; exit 0 ;;
  check)
    action_check; exit $? ;;
  print-routing-plan)
    action_print_routing_plan; exit 0 ;;
  set-web-env)
    action_set_web_env; exit $? ;;
  smoke-test)
    action_smoke_test ;;
  apply-domains)
    action_apply_domains; exit $? ;;
esac

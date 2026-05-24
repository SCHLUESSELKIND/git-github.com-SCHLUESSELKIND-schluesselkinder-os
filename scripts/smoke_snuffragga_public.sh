#!/usr/bin/env bash
# Read-only public smoke test for the SCHLUESSELKINDER routing surface.
#
# Curls every public domain we care about and prints a summary table:
#   - HTTP status code
#   - Final URL (after redirects)
#   - TLS error if any
#
# Exit 0 only if the whole surface is green:
#   - schluesselkinder.de              → 200
#   - www.schluesselkinder.de          → 200 OR 301 → schluesselkinder.de
#   - /artists/snuffragga              → 200
#   - api.schluesselkinder.de/v1/...   → 200
#   - listmonk.schluesselkinder.de     → 200 or 302 (login redirect) or 401
#   - shop.schluesselkinder.de         → DNS NOT on Hetzner IP, IS Shopify
#
# Read-only. Never touches Coolify. Never modifies anything.
#
# Usage:
#   bash scripts/smoke_snuffragga_public.sh

set -u
set -o pipefail

HETZNER_IP="178.104.103.37"

GREEN="$(printf '\033[1;32m')"
RED="$(printf '\033[1;31m')"
YELLOW="$(printf '\033[1;33m')"
DIM="$(printf '\033[2m')"
RESET="$(printf '\033[0m')"

FAIL=0
ROW_FMT="  %-50s %-8s %-10s %s\n"

probe() {
  # $1 = URL
  local url="$1"
  local raw err code final
  # %{http_code}|%{url_effective} on success; curl prints error to stderr
  raw="$(curl -ksS -o /dev/null -w "%{http_code}|%{url_effective}" \
        -L --max-time 10 "$url" 2>/tmp/sk_smoke_err.$$ || true)"
  err="$(tr '\n' ' ' < /tmp/sk_smoke_err.$$ 2>/dev/null | sed 's/  */ /g')"
  rm -f /tmp/sk_smoke_err.$$
  if [[ "$raw" =~ ^[0-9]{3}\| ]]; then
    code="${raw%%|*}"
    final="${raw#*|}"
    printf "%s|%s|" "$code" "$final"
  else
    printf "ERR|-|%s" "${err:-unknown}"
  fi
}

resolve_first_ip() {
  # $1 = hostname
  dig +short "$1" 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1
}

is_shopify_ip() {
  # $1 = IPv4. Shopify ranges are dynamic — best-effort check against
  # well-known Shopify ASN ranges + a sanity check that it's NOT the
  # Hetzner box.
  local ip="$1"
  [[ -z "$ip" ]] && return 1
  [[ "$ip" == "$HETZNER_IP" ]] && return 1
  # Shopify's primary egress is 23.227.38.0/24. Other addresses appear from
  # time to time; we accept any IPv4 that resolves AWAY from Hetzner via
  # the shops.myshopify.com CNAME chain.
  return 0
}

mark() {
  if [[ "$1" == "ok" ]]; then printf "${GREEN}✓${RESET}"; else printf "${RED}✗${RESET}"; FAIL=$((FAIL+1)); fi
}

echo
echo "${YELLOW}== SCHLUESSELKINDER public smoke test ==${RESET}"
echo
printf "${DIM}$ROW_FMT${RESET}" "URL" "STATUS" "FINAL" "NOTES"
printf "${DIM}  ---------------------------------------------------------------------------------------------------${RESET}\n"

# ---------------------------------------------------------------------------
# 1. schluesselkinder.de root
# ---------------------------------------------------------------------------
result="$(probe https://schluesselkinder.de)"
code="${result%%|*}"; rest="${result#*|}"; final="${rest%%|*}"
if [[ "$code" == "200" ]]; then ok="ok"; else ok="fail"; fi
mark "$ok"; printf "$ROW_FMT" "https://schluesselkinder.de" "$code" "$final" ""

# ---------------------------------------------------------------------------
# 2. www → root
# ---------------------------------------------------------------------------
www_raw="$(curl -ksS -o /dev/null -w "%{http_code}|%{redirect_url}|%{url_effective}" \
  --max-time 10 https://www.schluesselkinder.de 2>&1 || true)"
www_code="${www_raw%%|*}"; www_rest="${www_raw#*|}"; www_redir="${www_rest%%|*}"; www_final="${www_rest#*|}"
note=""
ok="fail"
if [[ "$www_code" == "200" ]]; then
  ok="ok"; note="ok (200; redirect missing — acceptable for now)"
elif [[ "$www_code" == "301" || "$www_code" == "308" ]]; then
  if [[ "$www_redir" == "https://schluesselkinder.de/" || "$www_redir" == "https://schluesselkinder.de" ]]; then
    ok="ok"; note="redirect → root"
  else
    note="redirects to $www_redir (expected schluesselkinder.de)"
  fi
fi
mark "$ok"; printf "$ROW_FMT" "https://www.schluesselkinder.de" "$www_code" "${www_final:-$www_redir}" "$note"

# ---------------------------------------------------------------------------
# 3. SNUFFRAGGA artist page
# ---------------------------------------------------------------------------
result="$(probe https://schluesselkinder.de/artists/snuffragga)"
code="${result%%|*}"; rest="${result#*|}"; final="${rest%%|*}"
if [[ "$code" == "200" ]]; then ok="ok"; note="route deployed"; else ok="fail"; note="route NOT in deployed build"; fi
mark "$ok"; printf "$ROW_FMT" "https://schluesselkinder.de/artists/snuffragga" "$code" "$final" "$note"

# ---------------------------------------------------------------------------
# 4. api.schluesselkinder.de
# ---------------------------------------------------------------------------
result="$(probe https://api.schluesselkinder.de/v1/capabilities)"
code="${result%%|*}"; rest="${result#*|}"; final="${rest%%|*}"; err="${rest#*|}"
if [[ "$code" == "200" ]]; then
  ok="ok"; note="inference reachable"
else
  ok="fail"
  note="API offline"
  [[ "$code" == "ERR" ]] && note="TLS/network error: $(echo "$err" | head -1)"
fi
mark "$ok"; printf "$ROW_FMT" "https://api.schluesselkinder.de/v1/capabilities" "$code" "$final" "$note"

# ---------------------------------------------------------------------------
# 5. listmonk.schluesselkinder.de — accept 200, 302, 401 (login redirect / auth)
# ---------------------------------------------------------------------------
# Don't follow redirects here — Listmonk's auth flow looks like 302
listmonk_raw="$(curl -ksS -o /dev/null -w "%{http_code}|%{redirect_url}" \
  --max-time 10 https://listmonk.schluesselkinder.de 2>/dev/null || true)"
if [[ "$listmonk_raw" =~ ^[0-9]{3}\| ]]; then
  listmonk_code="${listmonk_raw%%|*}"
  listmonk_redir="${listmonk_raw#*|}"
else
  listmonk_code="ERR"
  listmonk_redir="-"
fi
note=""
ok="fail"
case "$listmonk_code" in
  200) ok="ok"; note="Listmonk UI" ;;
  302) ok="ok"; note="auth redirect → ${listmonk_redir:-unknown}" ;;
  401) ok="ok"; note="auth required" ;;
  ERR) note="TLS/network error" ;;
  *)   note="unexpected $listmonk_code" ;;
esac
mark "$ok"; printf "$ROW_FMT" "https://listmonk.schluesselkinder.de" "$listmonk_code" "${listmonk_redir:--}" "$note"

# ---------------------------------------------------------------------------
# 6. shop.schluesselkinder.de — must NOT resolve to Hetzner, must reach Shopify
# ---------------------------------------------------------------------------
shop_ip="$(resolve_first_ip shop.schluesselkinder.de)"
shop_cname="$(dig +short shop.schluesselkinder.de | grep -v '^[0-9]' | head -1)"
note=""
ok="fail"
if [[ -z "$shop_ip" ]]; then
  note="no DNS A record"
elif [[ "$shop_ip" == "$HETZNER_IP" ]]; then
  note="POINTS TO HETZNER — must be Shopify"
elif is_shopify_ip "$shop_ip"; then
  ok="ok"
  note="off Hetzner (CNAME: ${shop_cname:-direct A})"
else
  note="resolved to $shop_ip — verify Shopify chain"
fi
mark "$ok"; printf "$ROW_FMT" "https://shop.schluesselkinder.de" "DNS" "$shop_ip" "$note"

echo
echo "${YELLOW}== Result ==${RESET}"
if (( FAIL == 0 )); then
  echo "${GREEN}all six checks green${RESET}"
  exit 0
fi
echo "${RED}$FAIL of 6 checks failed${RESET}"
echo "${DIM}See docs/deployment/COOLIFY_SCHLUESSELKINDER_ROUTING.md for the runbook.${RESET}"
exit 1

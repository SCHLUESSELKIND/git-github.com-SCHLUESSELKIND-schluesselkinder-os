# Phase-2 bring-up — `api.schluesselkinder.de` + Listmonk + www redirect

**Pre-state:** `schluesselkinder.de/artists/snuffragga` is live (Phase-1 deploy
already done). Still missing: FastAPI inference container, Listmonk container,
www → root redirect, updated Caddyfile.

**Post-state target:** smoke test `scripts/smoke_snuffragga_public.sh` shows
6/6 green, including:
- `api.schluesselkinder.de/v1/capabilities` → 200
- `listmonk.schluesselkinder.de` → 200 (admin login page)
- `www.schluesselkinder.de` → 301 → `schluesselkinder.de`

Time budget: ~25 minutes. Idempotent — re-runs are safe.

---

## 0. Pre-flight (local)

```bash
cd ~/schluesselkinder-os
git status -sb            # working tree clean except this PR
git log --oneline -5
```

Confirm `main` is the branch you want shipped. Push if needed:

```bash
git push origin main
```

---

## 1. DNS check (no change, just verify)

```bash
for sub in www api listmonk; do
  echo -n "$sub.schluesselkinder.de → "
  dig +short $sub.schluesselkinder.de | tr '\n' ' '
  echo
done
```

All three should resolve to `178.104.103.37`. If any is missing, add an A
record in IONOS DNS pointing to the Hetzner box and wait for TTL.

`shop.schluesselkinder.de` MUST stay a CNAME to Shopify — do not change it.

---

## 2. SSH to the server

```bash
ssh root@178.104.103.37
cd /mnt/HC_Volume_105338505/schluesselkinder/schluesselkinder-os
```

---

## 3. Pull code

```bash
git fetch origin
git log HEAD..origin/main --oneline | head
git pull --ff-only origin main
```

---

## 4. Create `.env` (one-time)

If `.env` does not yet exist:

```bash
test -f .env && echo "EXISTS — skip" || cp deploy/env.example .env
chmod 600 .env

# Generate two random secrets:
echo "LISTMONK_DB_PASSWORD=$(openssl rand -hex 32)"
echo "LISTMONK_ADMIN_PASSWORD=$(openssl rand -hex 32)"
```

Edit `.env` and paste the two values. Leave `LISTMONK_API_PASSWORD` and
`LISTMONK_API_LIST_ID` empty for now — we fill them after Listmonk is up.

```bash
nano .env       # or vim
```

Re-source so docker compose sees them:

```bash
set -a; . ./.env; set +a
docker compose -f docker-compose.existing-server.yml config | head -50
```

The `config` command should print the resolved YAML — any unresolved
`${...}` means the env var is missing.

---

## 5. Bring up Listmonk DB

```bash
docker compose -f docker-compose.existing-server.yml up -d listmonk-db
docker compose -f docker-compose.existing-server.yml ps listmonk-db
# wait for healthy
until [ "$(docker inspect -f '{{.State.Health.Status}}' schluesselkinder_web-listmonk-db-1 2>/dev/null)" = "healthy" ]; do
  sleep 2
done
echo "listmonk-db healthy"
```

---

## 6. Install Listmonk schema (one-off)

```bash
docker compose -f docker-compose.existing-server.yml run --rm listmonk \
  ./listmonk --install --yes
```

Expected: `** Installation done **` at the end.

---

## 7. Bring up Listmonk + API

```bash
docker compose -f docker-compose.existing-server.yml build api
docker compose -f docker-compose.existing-server.yml up -d listmonk api
docker compose -f docker-compose.existing-server.yml ps
```

Quick internal smoke (no Caddy / TLS yet):

```bash
curl -sS http://127.0.0.1:3092/health
curl -sS http://127.0.0.1:3092/v1/capabilities | head -c 200; echo
curl -sIL http://127.0.0.1:3093/ | head -3
```

Expected: `200 OK` from all three. The API capabilities JSON should include
`newsletter_subscribe_available: true` and `newsletter_listmonk_configured:
false` (we have not yet created the API user).

---

## 8. Create Listmonk API user + list

In a browser, open `http://127.0.0.1:3093` via an SSH tunnel, OR wait
until step 9 and use the public URL.

SSH tunnel (from your laptop, in a separate terminal):

```bash
ssh -L 9000:127.0.0.1:3093 root@178.104.103.37
```

Then open `http://127.0.0.1:9000` in your browser.

1. Log in with `LISTMONK_ADMIN_USERNAME` / `LISTMONK_ADMIN_PASSWORD`.
2. **Lists → + New**: name `SNUFFRAGGA — signal`, type **Public**,
   optin **Double**. Save. Note the numeric id from the URL.
3. **Settings → Users → + New**: username `snuffragga-bot`, role
   **Users**, status **enabled**, type **API**. Save. Click the user,
   copy the API token shown.
4. **Settings → SMTP**: configure your SMTP (IONOS recommended,
   `smtp.ionos.de:587`, STARTTLS, login). Send a test mail.

Back on the server, fill in `.env`:

```bash
nano .env
# LISTMONK_API_USERNAME=snuffragga-bot
# LISTMONK_API_PASSWORD=<paste-token>
# LISTMONK_API_LIST_ID=<numeric-id>
```

Recreate the API container so it picks up the new envs:

```bash
docker compose -f docker-compose.existing-server.yml up -d --force-recreate api
sleep 3
curl -sS http://127.0.0.1:3092/v1/capabilities | head -c 200; echo
```

Now `newsletter_listmonk_configured` should be `true`.

---

## 9. Caddyfile update

The canonical source lives in the repo at `deploy/caddy/schluesselkinder.caddy`.
Replace `/etc/caddy/Caddyfile` with it ONLY if `/etc/caddy/Caddyfile` is
currently a minimal block for the apex site. If it already has unrelated
blocks for other domains, splice the new server blocks in by hand.

Backup first, always:

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.$(date +%Y%m%d-%H%M%S).bak
```

Inspect:

```bash
sudo wc -l /etc/caddy/Caddyfile
sudo grep -nE "^(www\.|api\.|listmonk\.|schluesselkinder)" /etc/caddy/Caddyfile
```

If the file ONLY contains a single `schluesselkinder.de { ... }` block,
overwrite it:

```bash
sudo install -m 644 deploy/caddy/schluesselkinder.caddy /etc/caddy/Caddyfile
```

If it contains other unrelated blocks, append ours:

```bash
sudo tee -a /etc/caddy/Caddyfile >/dev/null < deploy/caddy/schluesselkinder.caddy
```

Validate + reload:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager | head -20
```

Caddy issues Let's Encrypt certs on first request — give it ~30s.

---

## 10. Public smoke

From your laptop:

```bash
cd ~/schluesselkinder-os
bash scripts/smoke_snuffragga_public.sh
```

Expected output: all six rows green.

If `listmonk.schluesselkinder.de` returns 401 instead of 200, that's fine —
Listmonk's admin redirect protects the UI. The interesting check is the
SUBSCRIBER API:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://listmonk.schluesselkinder.de/api/public/subscription
# 405 (method not allowed) is the healthy answer — endpoint exists.
```

---

## 11. End-to-end newsletter

Submit a test email from `https://schluesselkinder.de/artists/snuffragga`.
You should:
1. See the German "Fast drin. Bitte bestätige deine Anmeldung per E-Mail."
   confirmation in the page.
2. Receive the Listmonk double-opt-in email at the address you submitted.
3. After confirming, the subscriber shows up in Listmonk admin under the
   `SNUFFRAGGA — signal` list with status `confirmed`.

If step 1 shows "Signal-Endpunkt offline" → the API container is down or
`SOUNDSYSTEM_LISTMONK_*` envs are missing. Check
`docker compose logs --tail=50 api`.

If step 2 never arrives → Listmonk SMTP is misconfigured. Settings → SMTP →
**Send test**.

---

## Rollback

Each step is reversible:

```bash
# Stop new containers, keep web running
docker compose -f docker-compose.existing-server.yml stop api listmonk listmonk-db

# Restore Caddyfile
sudo cp /etc/caddy/Caddyfile.YYYYMMDD-HHMMSS.bak /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

The `web` container and `/artists/snuffragga` are not touched at any point
in this runbook.

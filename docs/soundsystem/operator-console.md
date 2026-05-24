# Operator Console

Internal admin surface for the SNUFFRAGA SOUNDSYSTEM AI engine. Lives under
`apps/web/app/admin/soundsystem/`. Not a public surface.

## Gate

The entire `/admin/soundsystem/*` subtree is gated by
`NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=true`. When the variable is not `"true"`:

- The layout calls `notFound()`, so all page routes return 404.
- The manifest route at `/admin/soundsystem/manifest.webmanifest` returns 404.
- The static icons under `/admin/soundsystem/icon-*.png` are served by Next.js
  from `public/admin/soundsystem/` and remain reachable. This is a small
  intentional trade-off; the icons themselves do not disclose anything beyond
  the existence of the path. Routing them through the gate is a Slice 3
  candidate if stricter behavior is wanted.

The gate is a local boundary marker, not authentication. Production deployments
must keep the variable unset or set to anything other than `"true"`.

## Operator Modes

Three visual modes share the same token sheet
(`packages/brand/src/soundsystem-tokens.css`) and switch via a
`data-operator-mode` attribute applied by `OperatorModeProvider`:

| Mode          | Use                                       |
| ------------- | ----------------------------------------- |
| `blackout`    | Default, steady state                     |
| `mint-signal` | Active monitor, accent rises              |
| `redline`     | Halt/review state — warning amber dominates, not live danger |

Persistence:

- Selected mode is stored in `localStorage` under `snuffraga.operator-mode`.
- Server-side renders always produce `data-operator-mode="blackout"` so the
  initial HTML matches the first client render. The provider reads
  `localStorage` from a `useEffect` and re-renders if a different mode is
  persisted. This produces a brief paint flicker on first load when a non-
  default mode is persisted; no React hydration mismatch is raised.
- Until `useEffect` runs, the switcher buttons are marked `disabled` and
  `data-operator-mode-ready="false"` is set on the provider's wrapper, so
  remote operators can detect the brief unready window in DOM inspectors.

## PWA Manifest

`/admin/soundsystem/manifest.webmanifest` is a route handler (not a static
file). It returns:

- `scope: "/admin/soundsystem/"` and `start_url: "/admin/soundsystem"` so the
  install only covers the operator surface.
- `display: "standalone"`, `orientation: "portrait"`.
- `theme_color` and `background_color` both `#000000`.
- Six shortcuts, one per `COMMAND_INTENT`.
- Two icon entries: `icon-192.png` (192×192) and `icon-512.png` (512×512),
  served from `apps/web/public/admin/soundsystem/`. Generated with Pillow as
  honest internal placeholders — black background, mint mark, thin frames.
  Replace before any public-facing install flow.

## Slice 2 Limitations

- **No live state.** The MACHINE STATUS panel is a static readiness map. No
  service is queried. Rows that read `NOT WIRED` or `DESIGN ONLY` are honest
  status; nothing is mocked behind a green indicator.
- **No safety enforcement.** The SAFETY PROTOCOL panel lists four planned
  checks (artist-name filter, reference-track filter, prompt audit log, audio
  similarity check), all in `pending` state. Nothing is enforced yet.
- **No action wiring.** Every command tile and every `/admin/soundsystem/{slug}`
  route still renders the `AwaitingWire` placeholder. No prompt is compiled, no
  job is opened, no artifact is produced from this surface.
- **No service worker.** The manifest gives standalone display and shortcuts
  but no offline caching.
- **No backend touched.** `services/soundsystem-inference` is not called by
  this surface in Slice 2. The provider registry and the two-call provider
  contract on the backend remain unused by the admin console until Slice 3.

## Slice 3 Targets

- Build a typed client for the inference service's `/v1/capabilities` and
  `/v1/generations` endpoints behind an explicit `MOCK_MODE` env flag.
- Define a `GenerationJob` view model shared between the admin and the API.
- Extract the prompt-engine module logic into a shared package so the admin
  can render prompt previews before any backend call.
- Land a safety-filter skeleton (artist-name list + reference-track list)
  reachable from the SAFETY PROTOCOL panel.
- Optionally route icons through gate-aware route handlers to fully match the
  manifest's 404 behavior when the gate is off.

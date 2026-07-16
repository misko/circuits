# DeepPCB cloud API (api.deeppcb.ai) — verified 2026-07

Use for PLACEMENT only (see autorouter-landscape.md: routing ~23% vs
KRT's effective 100%). Placement earned its credits: fitness 0.99+,
respected protection maps exactly — but requires the proximity snap-back
pass afterward (placement-and-proximity.md).

## Auth & flow

- Header: `x-deeppcb-api-key: <key>`. Keep keys in env vars, never in
  files or commits. Swagger: `/swagger/deeppcb/swagger.json`.
- Convert: `POST /api/v1/boards/convert-to-json` needs kicadBoardFile +
  kicadProjectFile + kicadSchematicsFiles.
- Submit: `POST /api/v1/boards` multipart: `jsonFile`, `routingType`
  (EmptyBoard | CurrentProtectedWiring), `webhookUrl` AND `webhookToken`
  (both required — a dummy URL like `https://example.com/hook` plus any
  token string works fine; polling `GET /boards/{id}` substitutes for the
  webhook), unique `requestId` (409 on reuse).
- Status: `GET /api/v1/boards/{id}` (expect a short ingestion delay/404
  right after submit). Balance: `GET /api/v1/apiuser/credit-flow`.
- Results: `GET /api/v1/boards/{id}/revision-artifact?type=JsonFile&revision=N`.
  Revisions keep landing while status is `ReceivingRevisions` — binary-
  search upward for the true latest (ours reached 286 after "finishing").

## Traps (each cost real money or a failed job)

- **API-submitted boards AUTO-START a routing job on ingestion** at the
  workflow's per-minute rate. If you wanted placement (UI-only switcher in
  the footer bar), watch for `boardStatus: Running` and
  `PATCH /api/v1/boards/{id}/stop` immediately — stopping refunds unused
  reserved minutes ("GiveBack").
- Converter rejects boards containing wires with "no pins to route" for
  EmptyBoard — strip wires/vias from the JSON first.
- Job type (Routing/Placement) is NOT settable via API — UI footer only.
- Billing reserves the full budget; unused minutes refund only after the
  job fully closes out. A ~1.0 credit/min workflow rate exists; check
  `workflowCostPerMinute` before starting.

## Placement job recipe

1. Build the JSON with a protection map: `protected: true` for connectors,
   holes, FETs, inductors, controllers, bulk caps, shunts; false for small
   passives/port switches. Strip wires/vias/ratsnest.
2. Submit; kill the auto-started routing job; have the user switch to
   Placement in the UI with a ~10 min budget.
3. Poll; fetch the LATEST revision JSON. Coordinates: `position` in
   micrometers, `kicad_x = jx/1000`, `kicad_y = -jy/1000` (y flip, zero
   offset — but derive the transform from protected parts each time).
4. Verify: zero protected parts moved, no side flips. Apply, snap-back,
   placement gates, then route with KRT.

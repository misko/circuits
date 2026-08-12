# Fabrication journal

## 2026-08-12 05:31 — start

- did: Ran the strict JLC four-layer exporter against routed board SHA-256
  `9888b1267744...`, without either exporter escape hatch.
- result: The exporter stopped in 0.3 seconds at A-ROT: 22 placements over 16
  LCSC codes lack measured per-code rotation authority. It withheld an
  orderable BOM/CPL and wrote `06_build/fab/rotations_unsourced.csv`. A loud
  worklist-only rerun then measured 40/40 legible/coded BOM rows, 76 CPL
  placements, 11 Gerber layers plus PTH/NPTH drills in a 13-file upload zip,
  and explicitly marked the package `MUST NOT BE ORDERED`.
- next: Measure all 16 rotations from JLC's exact code-specific land patterns,
  rerun the strict exporter with no override, then grade BOM source, payload,
  population, stock and digital-twin evidence before creating release staging.

## 2026-08-12 05:34 — routed review finish

- did: Collected fresh exact-board pin, render, topology/protection/ratings and
  layout/thermal/power-integrity lenses from bounded independent reviewers.
- result: All four reviews bind source commit
  `2c15f1dd1ef600bed4c6081062bc7f3640c25237` and board SHA-256
  `9888b1267744...`; all report `design_verdict: SOUND` and
  `order_verdict: DO-NOT-ORDER`, with zero P0 design defects. The order blocks
  are assembly rotation/body evidence, Type-VII execution, exact copper and
  complete-path resistance, thermal/dynamic validation, selected pack/fuse/BMS
  coordination and the <=39 mOhm complete Type-C interconnect qualification.
- next: Keep design bytes frozen. Close manufacturing evidence mechanically;
  do not relabel first-article obligations as routed-board defects or weaken
  the order verdict.

## 2026-08-12 05:39 — digital-twin fetch observability

- did: Started the JLC digital-twin model fetch with four bounded attempts per
  code, then independently inspected process state and content-addressed cache
  progress after the command went silent.
- result: The process remained alive in deliberate rate-limit/backoff sleeps
  and advanced through code directories, but emitted no `completed/total`,
  current-code, retry, elapsed or ETA heartbeat. A 16-code rotation-measurement
  batch also spent 36 seconds recursively searching cache roots without
  progress output and found only two requested models available at that point.
  IMP-051 records both general issues; no active tool was changed mid-run.
- next: Let the bounded fetch finish and preserve its partial cache. Retry only
  unresolved codes rather than restarting completed downloads; keep catalog
  fetch time separate from board-generation/routing time in the stage result.

## 2026-08-12 06:13 — population correction and bounded fetcher

- did: Independently graded the worklist BOM/CPL and queried the four distinct
  THT catalog codes. The strict assembly gate found F1, J1, J2-J4 and SW1 on an
  SMT CPL despite having drilled pads with no paste. JLC returned
  `assemblyComponentFlag=false` for each exact code. Added evidence-backed
  `not_assembled` entries, future native board attributes, and a current-board
  attribute deferral bound to routed SHA-256 `9888b1267744...`; no PCB byte
  changed. Added per-code fetch heartbeats, child/batch deadlines, unique-code
  reuse and resumable timeout output to the shared twin tool.
- result: Strict export now excludes exactly six hand-solder refs and reduced
  A-ROT from 22 placements/16 codes to 15 placements/11 codes. Worklist export
  contains 40 coded/legible BOM rows and 70 CPL placements. Rotation authority
  audit remains green at 82 rows. Twin regression suite passes 33/33, including
  a silent-child timeout fixture. Gerber payload, BOM provenance/legibility and
  via-process gates remain green; population can be fully graded once the
  release MANIFEST is staged from assembly.yaml.
- next: Resume the cached JLC twin under the new bounded telemetry, measure the
  remaining 11 rotations without guessing polarized parts, rerun strict export
  without the worklist override, then stage and grade the immutable release.

## 2026-08-12 06:48 — current-stock capacitor corrections

- did: Rechecked all 40 unique BOM lines against the live JLC/LCSC catalog and
  replaced the unavailable selected capacitor codes for C29 and C30 with
  stocked, electrically requalified codes C5451690 and C77036. Re-derived the
  affected voltage, capacitance, ripple and transient corners before rebuilding
  the schematic; routed copper remained frozen.
- result: Source, electrical and presentation gates passed with the new codes.
  The substitution exercise showed that stock repair is not a text-only BOM
  edit: source identity, part evidence, corner math, schematic labels and
  supplier-rotation authority must move together even when footprint and copper
  are unchanged.
- reflection: Put exact-code stock and CAD capability probes immediately after
  selection, before schematic generation. Keep the electrical-equivalence
  proof as the controlling gate; footprint equality alone is insufficient.

## 2026-08-12 07:22 — C23 CAD absence and evidence-backed substitution

- did: Repeated the exact EasyEDA v2 product query for C369910 and two controls.
  C369910, C861251 and C855851 returned no product record while C1525 and
  C110776 resolved, separating genuine per-code absence from client failure.
  Selected Panasonic 16SVPF180M / JLC C136277 using the exact Panasonic product
  page and series datasheet: 180 uF, 16 V, +/-20 %, 22 mOhm, 3.3 A at 100 kHz
  and 105 C, 5000 h at 105 C, 6.3 x 5.9 mm, negative stripe. JLC reports it as
  stocked and SMT-capable, and its exact EasyEDA CAD record exists. A trial
  twin measured 0.03 mm land fit, correct polarity, a registered body and zero
  rotation offset before the source substitution was accepted.
- result: C23 now uses C136277; the schematic, part dossier, design equations,
  ledger and rotation evidence agree. Fresh stock is 1052 units. Strict JLC
  export passes without the worklist or unknown-rotation escape hatch, yielding
  a 40-line BOM and 70-placement CPL. The PCB remains byte-identical at
  SHA-256 `9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb`.
- reflection: A proven exact substitute is safer than a permanent missing-CAD
  exception when it can be qualified before copper changes. Preserve the
  rejected dossier as history, but bind every live artifact to the selected
  code so a reviewer cannot accidentally accept the old part by adjacency.

## 2026-08-12 07:31 — cheap-gate authority ordering

- did: Reran from source after the C23 substitution. The inexpensive BOM gate
  stopped in 16.6 seconds because a generic MPN heuristic read
  `16SVPF180M` as 18 pF before its exact-code ledger value of 180 uF. Changed
  the shared checker so explicit code-specific evidence outranks guessed MPN
  syntax and the ceramic decoder refuses Panasonic OS-CON families. Added the
  known-bad regression before replaying the build.
- result: The focused source suite passes 29 tests with two environment skips;
  source schema, circuit-value, electrical and ERC gates are green. The cheap
  gate did exactly the right thing operationally—stop before expensive
  generation—but its evidence hierarchy was wrong.
- reflection: Early validation is only useful when uncertainty is explicit.
  Unknown must stop or defer to stronger evidence; it must never be converted
  into a confident-looking value by a broad parser.

## 2026-08-12 07:44 — strict export and final-state twin evidence

- did: Ran the strict exporter without escape hatches, then replayed the cached
  JLC twin and registration overlay. Fixed a shared reporting-order defect in
  which the twin CSV was written before adjudications, leaving durable
  `FETCH-FAILED` rows even though the final verdict passed. Added a regression
  that reopens the CSV and requires its post-adjudication state.
- result: Strict export completes in about 0.3 seconds; all 70 CPL rotations are
  sourced. The cached full twin completes in about 7.6 seconds with 68 OK rows,
  71/75 mounted bodies and two adjudicated supplier-library absences. Its CSV
  now says `ADJUDICATED-FETCH-FAILED` and gives no retry instruction for a
  genuine absence. Overlay analysis completes in about 0.84 seconds: all 36
  pixel-resolvable modeled bodies are within the 1 mm registration limit; C23
  measures 0.137 mm centre delta and 0.271 mm outward delta with no courtyard
  escape.
- reflection: The original eleven-minute, mostly silent network stage is now a
  short cached verification replay with explicit progress and bounded failure.
  Durable reports must describe the same final state as the exit code; console
  success is not evidence if the file a later gate ships says otherwise.
- next: Close the two fresh schematic reviews, commission a new independent
  twin/render lens over the substituted package, replay DRC/parity and the full
  release gates, then stage the self-contained archive. Keep the buyer verdict
  DO-NOT-ORDER until JLC upload preview, Type-VII process confirmation and
  first-article electrical/thermal/mechanical checks are actually completed.

## 2026-08-12 08:13 — release staging and relocated-source read-back

- did: Staged the design archive with raw fabrication files, strict BOM/CPL,
  human-readable PDFs, source, vendored custom footprints, board-only STEP,
  machine evidence, exact-board reviews and a first-screen buyer stop. Then ran
  KiCad DRC/parity against the board from the archive's own `source/` directory
  instead of assuming that a copy of a passing live project still passed.
- result: The first relocated run found three library-resolution warnings for
  U4-U6. The release-only footprint table had shadowed the complete KiCad
  `Package_SON` library with an incomplete local directory. Correcting only the
  archive mapping restored 0 violations, 0 unconnected items and 0 parity
  findings; both live and archived PCB files retain SHA-256
  `9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb`.
  No design or routed-board byte changed.
- reflection: A release copy is a new execution context. Source-tree checks
  prove the design, while relocated read-back proves the package. Both are
  necessary because dependency resolution can change without changing the
  board. IMP-057 records the shared-gate promotion still owed.
- next: Commit the complete source/evidence inputs, stamp the archive with that
  exact commit, close the manifest/policy self-consistency loop, then seal only
  the release directory and changelog. Preserve `DO-NOT-ORDER` until the JLC
  uploader and physical first article supply the evidence that cannot exist
  locally.

## 2026-08-12 08:24 — cross-format stock read-back

- did: Ran M-DEPEND after the ordinary release gates passed and inspected its
  one reported release-internal-map fragility instead of accepting the zero-
  failure summary alone.
- result: The JSON and text evidence named current C23 code C136277, but the
  adjacent CSV was from an earlier C369910 run. Regenerated all three outputs
  atomically from the current strict BOM. They now agree on C136277 / Panasonic
  16SVPF180M; the same-day live query passes 40/40 coded lines and reports 1052
  catalog units for C136277. IMP-058 records the missing shared cross-format
  identity gate.
- reflection: A zero-failure summary can still contain a useful coverage
  warning. Multiple files from one logical measurement need a shared run
  identity and field-level comparison; a basename and directory are not
  provenance.
- next: Take a new source commit containing this learning, restamp the staging
  manifest, rerun M-REL, M-DEPEND, design freshness and archive hashes, then
  seal only if the shipped bytes pass again.

## 2026-08-12 08:34 — post-seal publication identity finding

- did: Ran the repository publication boundary after v0.6.0 was sealed and the
  status beacon passed. The gate graded exact live/sealed board identity,
  source ancestry, release completeness/freshness and archived review bytes.
- result: v0.6.0's design remains green, but publication refused three review
  subjects that use the human display name `USB Hub 3S v4` rather than the
  exact repository slug `usb-hub-3s-v4`; the pin review uses the slug and
  passes that property. The branch-wide diff also exposes unrelated existing
  publication failures in three other projects, which are not v4 inputs and
  are not being changed here.
- reflection: A downstream publication parser belongs in the pre-seal battery
  when its findings require immutable release bytes to change. Human titles
  are not stable machine identity. IMP-059 records the shared parser/preflight
  correction.
- next: Leave v0.6.0 immutable. Obtain append-only independent publication
  reseals over the same PCB hash, commit them as source evidence, then cut a
  docs-only v0.6.1 whose fabrication, source and 3D trees are asserted byte-
  identical. Re-run v4's explicit publication audit before pushing.

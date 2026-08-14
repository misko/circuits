# Routing journal

## 2026-08-11 10:03 — start

- did: Entered Stage 4 from the pushed v0.4.0 placement checkpoint and ran the cheap rule, pad-launch and fabrication-tier preflights before invoking KRT.
- result: P-LAND stopped in 6.52 seconds on seven real land-to-class-width mismatches. No router ran and the hash-reviewed placement remained unchanged.
- next: Express only spatially bounded pad tapers and plane drops in the generic rule/tap contracts, then repeat the preflights before spending on route search.

## 2026-08-11 10:55 — iterate 1: pre-route fabrication and fill defects

- did: Regenerated the track-free board, refilled zones and ran full-severity DRC/parity while validating the declared advanced-tier via geometry.
- result: The cheap pre-route pass found three independent source defects before route search: a self-intersecting VIN zone that KiCad accepted but partially discarded during fill; 40 thermal holes encoded as footprint pads rather than fabrication vias; and via emitters screening against a hole-to-copper value below the adopted JLC advanced floor. All were repaired in shared, configuration-driven machinery with clean/known-bad tests. The final pre-route state passed tier preflight with 0 FAIL / 0 WARN and retained zero schematic-parity findings.
- next: Route only signal groups with KRT; leave the high-current rails to declared pours plus deterministic source/tap geometry.

## 2026-08-11 11:52 — iterate 2: all-dirty race and stale connectivity

- did: Ran the two-candidate bounded route race, imported the best candidate, replayed named power taps, stitched/fill-gated and compared the in-process result with a fresh KiCad CLI refill/DRC.
- result: The first race incorrectly returned success although every candidate retained routed opens; promotion was changed to require a CLEAN candidate and now clears stale `FINAL` state. A later in-process stitch gate said clean while fresh CLI DRC found 35 unconnected items and one dangling via. The stage added a forced save/fresh-interpreter reload, same-net island healing and stitch-via pruning, while retaining CLI refill plus schematic parity as authority.
- next: Add explicit plane drops for every SMD power landing that remains isolated after fresh fill, then rerun the race and the complete serialized chain.

## 2026-08-11 12:06 — iterate 3: clean promoted route

- did: Added four reviewed B.Cu output drops for U5/U6, ran the two-lane route race, promoted the exact clean winner, then replayed import, 20 named taps, 19 stitch/fill passes, rules-last and authoritative DRC.
- result: Both route candidates were CLEAN with zero routed opens and zero copper violations; the winner was promoted as `03_src/route/r4.kicad_pcb` at SHA-256 `c1cfade37cc50b02acb4796e09952f566b20e518c4077b143ebf3bf9c8fce56b`. The final board contains 379 imported segments, 10 imported/seed vias, 20 named taps, 30 pour zones and 129 saved filled-polygon blocks. Fresh read-back, critical-connectivity and full KiCad gates report 0 violations / 0 unconnected / 0 schematic-parity findings.
- next: Replay the promoted artifact through both canonical rebuild drivers and run the focused regression battery before freezing the checkpoint.

## 2026-08-11 12:17 — stuck: host resource pressure looked like a silent pipeline

- did: Re-ran the from-source driver under captured logging and inspected the live process tree plus kernel journal when the command appeared to end at `Generating circuit JSON...`.
- result: The driver had not ended: it continued through schematic conversion, board generation, route replay and DRC, but the host entered global OOM pressure with about 190 GiB active anonymous memory. Kernel logs show an unrelated 9.1 GiB Python process killed at 12:16:57 and repeated user-session OOM kills; a KiCad child temporarily sat in uninterruptible I/O. Once pressure cleared, the same run completed route replay, stitch in 3.143 seconds and DRC in 1.511 seconds at 0/0/0. The final stop was instead a loud M-STATE ledger defect: a passed architecture gate lacked required evidence paths.
- next: Record the missing maturity evidence, add bounded heartbeat/timeout coverage to the previously direct TSX producer step, and distinguish host-resource stalls from router work in future status reports.

## 2026-08-11 12:29 — finish and pause

- did: Put `tsci build` under the bounded runner, corrected the maturity ledger, made full/pinned exports share one electrical topology digest, replayed both drivers, plotted and visually inspected both outer copper layers, and ran the focused generator/review/template/tier/route regression suites.
- result: The final from-source run reports TSX build 8.960 seconds, stitch 3.029 seconds, DRC 1.636 seconds, M-PROV 4/4, GG 25/25 observed with no shadow/resolve finding, M-STATE 9/9 at DESIGN_CLEAN, and DRC 0/0/0. The pinned deterministic driver independently reports ROUTING GATE 0/0/0. The exact promoted route remains `c1cfade37cc5...`; top/bottom routed-review PNGs hash to `66f69374a498...` / `e49e8662ec7f...`. Visual inspection finds coherent cell-local signal escape, broad plane-fed power regions, clear connector mouths/mounting holes and no visually unexplained copper crossing; this is a routing-stage sanity lens, not the Stage 5 independent layout review.
- tests: MEASURED 230 passed, 0 failed and 2 slow tests intentionally skipped: generator 48, tier preflight 31, route/stitch 99, rebuild template 42 and pre-route review 10. Of these, 117 known-bad fixtures failed their gates as required.
- spent: MEASURED wall clock about 2 hours 26 minutes from the 10:03 stage marker. The successful two-lane route race took about 27 seconds; ordinary rebuild stages were seconds. Most time was diagnosis and source correction: the invalid VIN polygon, fabrication-via representation, stale in-process fill connectivity, orphaned power-plane landings, full/reuse netlist-hash contradiction and late maturity-ledger failure. One apparent multi-minute stall was host-wide OOM/I/O pressure, not router search.
- generalized: Validate polygons before KiCad; treat thermal via-in-pad as true fabrication vias without sacrificing library parity; route plane landings deterministically before stochastic search; promote only CLEAN route candidates; cross a serialization/process boundary after fill; keep CLI refill/parity authoritative; bind topology to electrical facts rather than export location; and put every quiet external producer behind the same heartbeat/deadline runner.
- instruction changes: IMP-005/006/007/009/010/011/012/013 are complete. IMP-008/014/016 remain proposed and IMP-015 remains implementing. The next canonical work should move all source-only schema/maturity checks ahead of TSX, reduce producer warning noise without losing logs, and separate orchestration metadata from adopted-design-rule review hashes.
- next: PAUSE. The board is DESIGN_CLEAN but deliberately DO-NOT-ORDER. On user continuation, Stage 5 must perform fresh exact routed-board pin/layout/render and adversarial power-integrity review before any fabrication/assembly or release claim.

## 2026-08-11 23:19 — corrected-placement route prep refused stale via geometry

- did: Ran the full routing preflight, then invoked bounded `route prep` against
  the exact reviewed placement before starting either KRT candidate.
- result: preflight passed every source, electrical, placement, pad-launch and
  tier gate. Prep then stopped in 0.70 seconds because all four configured
  0.50/0.20 mm U5/U6 output via-in-pad drops collide with the adjacent
  foreign-net lands at 0.18 mm clearance. Exact probing showed a 0.13 mm copper
  gap. An interim 0.40/0.20 mm proposal cleared the pads but exact KiCad DRC
  correctly rejected its 0.10 mm annulus against the board's 0.15 mm minimum;
  the independent layout lens also refused it. No route wave ran and no
  promoted route was created.
- generalized: placement review must include the deterministic copper that its
  coordinates constrain, not only the track-free board. IMP-034 records a
  future read-only seed/tap validation gate before human placement review.
- next: retain 0.50/0.20 mm vias but move them 0.60 mm outward using short
  0.30 mm F.Cu launches into the existing 0.80 mm B.Cu pour joins; rerun exact
  prep DRC, refresh affected config-digest-bound reviews, then start the
  bounded two-candidate route race.

## 2026-08-11 23:37 — corrected route race complete

- did: Re-ran the complete preflight against current 2/2 schematic and 4/4
  placement witnesses, then ran two concurrent KRT wave chains over Type-C
  control, regulator support, USB-A charging-signature and remaining control
  nets. The race accepted only a candidate whose quick measurement was CLEAN.
- result: both candidates completed all four waves with zero routed opens and
  zero quick copper violations. Candidate 0 won the deterministic index
  tie-break at SHA-256 `1bafd3b904b6...`; candidate 1 was independently CLEAN
  at `5a5b76019e60...`. Total bounded wall time was 10.457 seconds versus the
  2400-second deadline. The route emitted a ten-second heartbeat and no silent
  interval exceeded it.
- spent: router search itself reported hundredths of a second per wave; board
  load, process startup, sidecar propagation, import and quick evaluation
  dominated the measured wall time. The full per-net router transcript is much
  noisier than the useful progress signal.
- generalized: retain race promotion's CLEAN-only rule, heartbeat and hard
  deadline. IMP-014's bounded-console work should summarize wave name, net
  count, completion/failure and final evaluation in the progress stream while
  preserving the full transcript as an artifact.
- next: import candidate 0 from the explicit build lineage, replay all named
  power taps, run the deterministic stitch/refill chain and require full KiCad
  DRC/parity before promoting the route as r5.

## 2026-08-11 23:47 — deterministic pour service closed before r5 promotion

- did: Imported the first CLEAN candidate, replayed the declared power taps,
  stitched and refilled the board, then required a fresh-process KiCad CLI
  refill/DRC/parity result before promotion. The first authoritative pass
  overruled the in-process gate with 10 pour-net opens and one dangling via:
  VIN at R22, the U9 5VA output-pin bank, 5VA_RAW at C6, and 5VC_RAW at R11,
  C9 and TP3. Each landing was then represented in `route.yaml` as a named,
  reviewable plane drop or local join; the U9 bank received one spatially
  bounded 0.30 mm rule area.
- result: The repeated two-candidate race again produced two CLEAN chains in
  9.584 seconds. Candidate 0 was imported with 423 segments and 10 vias; all
  29 deterministic connections passed; stitch/refill completed in 5.200
  seconds; and the authoritative DRC completed in 1.721 seconds with
  **0 violations / 0 unconnected items / 0 schematic-parity issues**. The
  exact winner is promoted as `03_src/route/r5.kicad_pcb` at SHA-256
  `7d1499ab9894f2dbacfc195170f5046f3f2216f035e75bb7bd0bed45a7fb3a54`.
- spent: The successful serialized route/import/tap/stitch/DRC chain took
  roughly 20 seconds. The longer work was classification of already
  predictable pour-service gaps, not route search.
- generalized: Every net excluded from stochastic routing needs a static
  pre-route coverage proof for each electrically required landing. The full
  refill/DRC/parity process remains authoritative, but it should verify those
  declarations rather than discover their absence after routing. IMP-035
  records the reusable source-side gate.
- next: Regenerate the track-free subject, refresh the exact pre-route review
  bindings, replay r5 through both canonical rebuild drivers, then begin fresh
  routed-board reviews. The board remains DESIGN_CLEAN and DO-NOT-ORDER.

## 2026-08-12 00:00 — promoted-chain replay green; full producer paused safely

- did: Rebound the exact track-free board/r0/rules through independent
  topology, pin, layout, render and A-RENDER lenses, then replayed promoted r5
  through the deterministic canonical driver. Started the full TSX driver from
  source as the independent reproducibility proof.
- result: PR-REVIEW passed 2/2 schematic and 4/4 placement witnesses. The
  promoted-chain replay completed in 17.438 seconds and ended at authoritative
  DRC **0/0/0**. The full producer reached its deliberate schematic-review
  checkpoint in 17.6 seconds: dependency resolution took 0.173 seconds, TSX
  generation 12.339 seconds with a visible ten-second heartbeat, and the
  remaining render/semantic/ERC/checkpoint work about five seconds. It then
  correctly refused the old reviews because the newly generated PDF and
  normalized-netlist bytes changed.
- generalized: the bounded driver now distinguishes a healthy 12-second
  producer from a silent hang. The fail-closed review pause also worked, but
  structural comparison found the old and new netlists identical over 88
  component identities, 324 physical pin-to-net identities and 69 net names.
  IMP-015 therefore still needs sorted structural netlist canonicalization to
  avoid paying for reviews caused only by collection-order churn.
- next: review the exact regenerated schematic/PDF, resume the pinned
  checkpoint without rerunning TSX, then require the same exact placement and
  routed 0/0/0 result before beginning routed-board release lenses.

## 2026-08-12 00:29 — layout seal acquired after two orchestration repairs

- did: Introduced a versioned semantic design-rule digest, rebound two exact
  schematic and three exact track-free placement review lenses, and ran
  `pcb_flow.py layout-seal` from the content-addressed schematic checkpoint.
  The conductor regenerated the 88-part board, imported promoted r5, replayed
  all 29 taps, stitched/refilled, repeated routed geometry/policy checks and
  published a transactional layout-seal witness.
- result: checkpoint verification was 7/7; schematic review 2/2; placement
  review 4/4; P-PINMAP 17 refs/192 physical identities; P-LAND 105/105 on the
  track-free subject and 94/94 on the routed subject; P-PADSEP 57,771 pad
  pairs; 423 imported segments, 10 imported vias and 29/29 taps; authoritative
  DRC **0 violations / 0 unconnected / 0 parity**. The final successful seal
  replay took about 39 seconds, including a 28.872-second canonical rebuild.
- spent: the first seal stopped in 2.7 seconds because a process-only resume
  argument invalidated the old whole-file rules digest. The next clean replay
  stopped in 0.094 seconds after DRC because the conductor compared a routed
  board with a review intentionally bound to the track-free board. Both were
  cheap, correctly fail-closed discoveries, but neither represented a design
  defect.
- generalized: review identity needs a versioned semantic projection, not a
  hash of orchestration metadata (IMP-016). A human review checker must also be
  typed to the lifecycle artifact it reviews: pre-route evidence belongs
  before route import, while the seal repeats routed geometry/connectivity/DRC
  gates (IMP-037). A producer with an exact human checkpoint needs its verified
  resume arm declared as part of the canonical command (IMP-036).
- next: generate fresh routed copper/3D/PDF evidence and pin dossiers, measure
  realized power paths/cross-sections, run independent routed pin/render and
  red-team topology/layout lenses, then begin the JLC fab/assembly battery.
  Layout is sealed; fabrication and ordering remain unsealed and DO-NOT-ORDER.

## 2026-08-12 01:09 — corrected-process route promoted as r6, then superseded by r7

- did: Refused the stale promoted r5 when exact import found that 18 of its 48
  inherited source-owned vias still described 0.60/0.30 mm barrels instead of
  the corrected 0.50/0.20 mm Type-VII source geometry. Re-ran prep and a
  bounded two-candidate race from the corrected r0, then exercised the winner
  through 31 named taps, all 19 stitch/refill passes, rules-last ampacity audit
  and authoritative KiCad CLI DRC/parity before promotion.
- result: Both candidates were CLEAN with zero routed opens and zero quick
  copper violations. Candidate 0 won the deterministic index tie-break and is
  promoted as `03_src/route/r6.kicad_pcb` at SHA-256
  `6ddf0d7c3a67e7d4fd3c6ffa804c16792b50b13eccd3255a67374ee53babead9`.
  The promoted checkpoint contains 423 segments plus 58 vias: all 48 inherited
  source vias retain Type-VII capping/filling, and all ten router/seed vias are
  ordinary. Full replay ended at rules audit 29/29 and DRC **0/0/0**.
- spent: prep plus the complete two-lane race took about ten seconds; full
  import/tap/stitch/audit/DRC took 8.1 seconds. The useful router work was again
  sub-second; board parsing, process startup, independent evaluation and
  refill dominated. The stale-route incompatibility failed in under a second,
  before any KRT work.
- generalized: a promoted route is a derivative of both placement and
  source-owned via geometry/process, not only pad coordinates. Keep strict
  importer refusal and add a cheap promoted-chain compatibility precheck before
  soliciting placement reviews, so a reviewer is never asked to approve a
  canonical path that cannot execute. The exact process bits also need a
  routed-artifact census because DRC does not grade IPC-4761 intent.
- instruction changes: IMP-040 records the compatibility precheck; the
  existing CLEAN-only race, heartbeat, source-owned-via drift refusal and
  rules/DRC gates all behaved correctly and remain unchanged.
- next: rebind exact placement reviews to r6, replay r6 through the canonical
  layout seal, then measure the realized high-current copper and run fresh
  routed-board independent reviews. The board remains DO-NOT-ORDER.

- follow-up: The pin/process review found that r6's four ordinary off-pad
  port-output seed vias shared the protected family's 0.50/0.20 mm geometry.
  KiCad preserved the intended per-item flags, but a JLC Gerber order resolves
  fill/cap by the declared hole family and cannot consume those native flags.
  All four sites passed exact probing at 0.60/0.30 mm, so the ordinary seed
  geometry was enlarged and the two-candidate route/replay battery was repeated.
  Both candidates remained CLEAN; the promoted artifact is now
  `03_src/route/r7.kicad_pcb` at SHA-256
  `17370f243f61224aead29e37181d4ed4fef0726854f2cf4daa8e9f18a9ddd870`.
  Its source subset is exactly 48 protected 0.50/0.20 vias plus ten ordinary
  0.60/0.30 route/seed vias. The fully stitched board contains 65 protected
  0.50/0.20 vias, 92 ordinary 0.60/0.30 vias and four ordinary 0.70/0.30 vias;
  there are zero unprotected 0.20 mm drills and zero protected 0.30 mm drills.
  Rules again passed 29/29 and DRC again passed 0/0/0.
- revised next: bind exact placement reviews to r7, acquire a fresh canonical
  layout seal and require the same drill/process census in fabrication output.

## 2026-08-12 01:58 — via-boundary proof repaired; r8 exact board green

- did: Added A-VIA as a canonical exact-board series-transition check using
  TI SLVA959B Table 3-1's IPC-2152 10 C-rise finished-hole screening values,
  with zero electrical credit for fill. Extended P-ROUTEBASE to compare fresh
  deterministic prep segments/vias before human placement review. The first
  A-VIA run intentionally graded the previously clean r7 board and stopped it,
  then the U4-U6 input banks and U9 aggregate bank were repaired declaratively
  before a fresh two-candidate route.
- result: r7 measured only 3.36 A of credited U9 layer-transfer capacity for
  an 8 A requirement and 0.55 A per USB-A switch input for 2.849 A. Corrected
  r8 is promoted at SHA-256
  `8ea0f50681d48c34c6e5f300cc8842f144937cd92fb118cad6a546d19acf173f`.
  Both candidates were CLEAN in a 9-second race. Exact r8 replay passed
  P-ROUTEBASE over 95 footprints / 64 base-or-prepared vias / 12 prepared
  segments, rules 29/29, A-VIA 4/4, V-PROCESS 183/183 and authoritative DRC
  **0/0/0**. U9 has fourteen 0.70/0.30 mm transfers crediting 11.76 A for
  8 A; each U4-U6 input has four ordinary 0.60/0.30 mm transfers plus one
  protected 0.50/0.20 mm pad drop, crediting 3.91 A for 2.849 A. The final
  census is 65 protected and 118 ordinary vias, with process families
  drill-disjoint.
- spent: route search remained cheap; the complete two-lane race took about
  nine seconds and exact import/taps/stitch/audits/DRC about ten seconds. The
  valuable time was proof design: distinguishing a real forced current
  boundary from arbitrary same-net vias so the gate could not pass vacuously.
- generalized: DRC connectivity and track/plane ampacity do not establish via
  barrel capacity. Every forced layer transition on a high-current rail needs
  a named tight boundary, cited finished-hole basis, explicit continuous
  current and independent physical-path review. Prepared deterministic copper
  must be part of the promoted-route identity before review. IMP-040 and
  IMP-041 carry both changes into the shared pipeline and templates.
- next: complete fresh exact schematic and placement review bindings for r8,
  reacquire the transactional layout seal, then generate routed evidence and
  run independent routed red-team lenses before fabrication. Loaded
  first-article resistance/temperature testing remains mandatory; the board
  is still DO-NOT-ORDER.

## 2026-08-12 02:25 — r8 transactional layout seal acquired

- did: Regenerated and rebound the exact ten-page schematic, obtained fresh
  independent SOUND topology/readability and track-free pin/layout/render
  verdicts, then ran the canonical checkpoint-resume layout-seal transaction.
- result: The transaction replayed promoted r8 with 423 imported segments, 22
  imported vias and 41 deterministic taps. P-ROUTEBASE covered 95 footprints,
  64 base-or-prepared vias and 12 prepared segments; rules passed 29/29;
  A-VIA passed all four forced current boundaries; V-PROCESS classified all
  183 vias as 65 protected plus 118 ordinary; final KiCad DRC/parity was
  **0/0/0**. The sealed board SHA-256 is
  `6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b`.
- spent: Canonical rebuild was 24.819 seconds, stitch was 4.803 seconds and
  authoritative DRC was 1.660 seconds; the complete seal command took about
  33 seconds. The fresh reviewers, not board generation or routing, exceeded
  the useful review window and required operator interruption even though the
  written review budget was explicit.
- generalized: measured stage telemetry now distinguishes a healthy PCB
  producer from reasoning/orchestration delay. IMP-026 is strengthened: a
  reviewer deadline written in a prompt is not a deadline; admissible review
  needs an externally enforced wall-time, visible age/progress and fail-closed
  evidence handling.
- next: export exact routed copper/3D/PDF evidence, complete independent routed
  pin/render and adversarial topology/layout lenses, then enter the JLC
  fabrication/assembly battery. Layout is sealed; fabrication and ordering
  remain unsealed and DO-NOT-ORDER.

## 2026-08-12 05:26 — current-source r8 replay and evidence-export repair

- did: Replayed promoted r8 from the final reviewed schematic and placement,
  reconciled the findings ledger from three stale `pending` states to its exact
  review/DRC evidence, and reran the transactional seal. Then exported exact
  top/bottom copper, top/bottom/isometric 3D, layer PDF and assembly PDF.
- result: Import brought in 423 segments and 22 vias in 0.66--0.96 s; all
  41 taps replayed in 0.57--0.65 s; stitch completed 19 passes in 4.88--11.01 s;
  rules passed 29/29; A-VIA passed 4/4; V-PROCESS classified 65 protected and
  118 ordinary vias with disjoint drill families; exact DRC is 0/0/0; and
  M-STATE derives DESIGN_CLEAN from 9/9 controls. The sealed routed board is
  SHA-256 `9888b1267744...`.
- backtrack: The first evidence export printed KiCad usage for the isometric
  command but returned zero and left a stale 02:29 PNG beside fresh 05:23
  files. The exporter now deletes all nine targets first, checks each producer
  made a non-empty output, and uses accepted rotation syntax. The second run
  freshly produced every expected file; IMP-050 records the generic defect.
- spent: The successful canonical rebuild took 27.657 s; post-route seal gates
  took about eight seconds. A complete corrected review export took about
  28 seconds, dominated by three 6.6--7.0 s high-quality renders. Routing
  search itself was not repeated and remains cheap relative to refill/review.
- generalized: Exit zero is evidence about a process, not its promised file.
  Generated evidence requires delete-before-produce and a file postcondition;
  timestamp/hash manifests should be preferred over directory presence.
- next: Commit/push this reproducible layout checkpoint, run four fresh exact-
  board routed lenses, then build and grade the JLC fabrication/assembly
  staging package. Ordering remains blocked by assembly-preview and first-
  article obligations.

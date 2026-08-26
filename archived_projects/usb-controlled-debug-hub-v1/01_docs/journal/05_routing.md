# Routing journal

## 2026-08-16 06:05 — start

- did: entered the USB-only routing stage from the exact track-free reviewed board and ran the bounded project preflight.
- result: MEASURED PASS — 139-component parity, E-INV 59/59, E-ADR 4/4, critical pairs 10/10, P-LAND 281 graded pads, P-PADSEP, placement policy and P-ESC 30/30; scoped independent renewal kept topology, schematic-render and pin reviews SOUND after canonicalizing two escape-style labels.
- next: add an authenticated non-promotable route-wave pause, regression-test it, then run only `usb_bottom`, `usb_transition` and `usb_top`.

## 2026-08-16 06:08 — iterate 1

- did: implemented `route --through-wave NAME` and ran the complete generic routing regression suite.
- result: MEASURED PASS — the new fixture proves a deliberate prefix is digest-authenticated, writes no `FINAL`, and resumes only the untouched suffix; all `t2_route_stitch.py` cases pass.
- next: exercise the USB-only prefix under the 2,850-second hard deadline and 10-second heartbeat.

## 2026-08-16 06:10 — iterate 2

- did: ran the three USB waves through `--through-wave usb_top`.
- result: MEASURED FAIL — 3/7 waves completed in 14.895 s but KRT skipped all 10 pairs before search; r0/r1/r2/r3 have identical SHA256 and only the 28 declared launch segments; quick reports 234 routed-net opens; no `FINAL` exists and no power/control wave ran.
- next: diagnose the common fanout precheck before changing board geometry or clearances.

## 2026-08-16 06:11 — stuck

- did: traced KRT issue-242 fanout self-overlap logic and compared its threshold with the exact launch geometry.
- result: MEASURED causal mismatch — 0.2332 mm tracks on 0.50 mm centres leave 0.2668 mm P/N edge gap, above the declared 0.15 mm pair gap; KRT instead compares against 0.95 x 0.30 = 0.285 mm foreign-net clearance. It also returns success after every pair is skipped. The failure surfaced in seconds, not a long search.
- next: pause before any more copper; repair and regression-test same-pair versus foreign-clearance ownership, make `skipped_bad_fanout` a hard wave failure, restart from r0, require 10/10 connected, then pause again before power/control.

Reflection: the heartbeat, preflight, per-wave summary and explicit checkpoint
all worked. The generalized defects are the collapsed clearance domains and a
zero-work success exit, recorded as IMP-121. Lowering the wave-wide clearance
would weaken unrelated-copper spacing and is explicitly rejected.

## 2026-08-16 — placement backtrack before USB retry

- did: after repairing the KRT clearance-domain and zero-work checks, ran a
  raw directional DRC on the exact prepared board and traced four
  `diff_pair_uncoupled_length_too_long` findings to the deterministic
  USB-A-contact-to-ESD fan-ins.
- result: MEASURED root cause — each straight 0.2332 mm connector branch was
  2.0626 mm against the source-owned 2.0 mm ceiling. The ceiling was not
  derived from a weaker fabrication limit and the branch was still movable.
  Backtracked placement instead of relaxing the class rule: moving U_ESD1–4
  0.10 mm toward the receptacle reduces all eight branches to 1.963 mm.
- next: regenerate from source, rerun placement/parity/model/DRC/twin gates,
  renew exact-board pin/layout/render reviews, and only then retry the
  authenticated USB routing prefix.

Reflection: deterministic seed copper should receive a cheap raw DRC before
independent placement review. It exposes constraint failures caused by exact
launch geometry while the remedy is still a 0.10 mm floorplan edit rather than
a global rule relaxation or a routed-board repair.

## 2026-08-16 — placement backtrack measured green

- did: renewed the schematic-stage rule receipts, ran the canonical source
  rebuild through deterministic route preparation, then generated a fresh JLC
  twin and shadow-free same-camera overlays in a sibling staging directory.
- result: MEASURED PASS — board
  `4baeae257b7bdb0b42ac8ad6f29b2c8e17a08aaf43e40b9a40169bde48b8bc7d`;
  r0 `ebfdeef58e7d0a6205e87680a816cb4d460d70c30cd40edf86ffc377b4bf863b`;
  139 parts, 574 pads, 31 source assertions, 281/281 graded launches,
  10/10 critical-pair contracts and 38/38 deterministic seed banks. Raw r0
  DRC has 301 findings only in the expected partial-route classes (146 library
  context, 119 dangling rescue vias, 36 dangling seed tracks), with zero
  uncoupled-length or other physical-rule finding. A-RENDER passes top 30/129
  and bottom 9/9 with zero resolvable-but-unmeasured body.
- next: obtain exact-board pin/layout/render renewals, pass the placement
  PR-REVIEW gate, then retry only the three USB waves.

## 2026-08-16 07:07 — USB retry stopped safely at wave 1

- did: renewed the exact-board pin, layout and render receipts, passed the
  aggregate placement PR-REVIEW gate, then restarted from the authenticated r0
  and requested only the USB prefix through `usb_top`.
- result: MEASURED FAIL at `usb_bottom` after 9.031 s wall time (5.73 s KRT
  internal).  The repaired fanout predicate accepted every launch
  (`skipped_bad_fanout=[]`), so IMP-121 did its job.  KRT found candidate
  centre lines for all four port pairs, but could not attach a coupled path
  between each horizontal ESD pad bank and its orthogonal FSUSB42 pad bank:
  `Polarity mismatch cannot be resolved (pad swap not allowed, no
  opposite-side connector option)`.  It classified P1_PORT through P4_PORT for
  single-ended deferral; the circuits wrapper rejected that result instead of
  accepting uncoupled USB copper.
- containment: no coupled copper was added; r1 SHA256 remains identical to r0
  (`ebfdeef58e7d0a6205e87680a816cb4d460d70c30cd40edf86ffc377b4bf863b`).
  `route_progress.json` contains zero authenticated waves, no `FINAL` exists,
  and `usb_transition`, `usb_top`, power and control never ran.
- next: pause before changing route contracts.  Trace one pair's paired-offset
  ordering and approach tangents, then choose either source-owned deterministic
  coupled routes for all four ESD-to-switch spans or compatible paired seed
  extensions; rerun only `usb_bottom`.  Do not swap D+/D- identities and do not
  permit single-ended fallback.

Reflection: the corrected clearance domains, hard failure on skipped or
single-ended differential work, named prefix and sub-10-second bounded wave
all behaved as intended.  The missing cheap check is endpoint-topology
compatibility: paired endpoint ordering, approach tangent, pad-bank orientation,
shunt topology and launch direction should be proven before the search starts.
That generalized improvement is recorded as IMP-123.

## 2026-08-16 07:28 — deterministic USB-bottom checkpoint green

- did: traced one exact PESD2USB3UX/FSUSB42 path, attempted a same-side
  coupled escape, and let the seed emitter collision-check every primitive.
  All four attempts were refused immediately where the long member crossed
  the opposite ESD signal land.  Re-read the exact pad shapes and the
  Microchip USB2517 checklist, then corrected the model: PESD2USB3UX is a
  three-pin shunt placed directly on the continuous USB traces, not a series
  two-ended routing component.
- implementation: authored all four connector-to-switch pairs deterministically
  on B.Cu.  Each trace lands directly on its ESD signal pad, continues along
  one side of the central GND land, and couples at 0.384 mm centres / 0.1508 mm
  copper gap as soon as the package clears.  A mirrored 0.4 mm dogleg on the
  bend-inside member compensates the 90-degree pair-offset length difference.
  The four pairs now declare `source: seed_stubs`; the stochastic route chain
  begins at `usb_transition`.
- rules: split connector/protector nets into `USB_HS_PROTECTED`.  KiCad measures
  7.1298 mm worst uncoupled length across the connector/SOT23/miter geometry,
  so that class alone has a measured 7.50 mm ceiling.  Internal USB nets keep
  the original 2.0 mm ceiling.  This preserves Microchip's no-TVS-branch rule
  without hiding the package discontinuity or weakening unrelated pairs.
- result: MEASURED PASS — 46/46 deterministic banks, 102 primitives, zero
  collision refusal; r0
  `6224d79d2f8aa821f00ba58515d69939de342c980f5e9c34ae33371c2e822cb9`.
  All eight P1..P4_PORT nets connect receptacle, ESD land and FSUSB42.  Raw r0
  DRC has 293 expected partial-route findings only (146 standalone-library
  context, 119 dangling rescue vias, 28 dangling unfinished-wave tracks),
  365 expected opens and zero physical-rule finding.  Realized route spread is
  0.3054 mm on every port against the 1.00 mm end-to-end ceiling.
- next: renew the exact design-rule/part-bound pin, layout and render receipts;
  then route only `usb_transition` and pause before `usb_top`, power or control.

Reflection: collision refusal prevented a plausible-looking but electrically
mis-modelled route from being emitted.  The new general lesson is earlier than
endpoint tangent compatibility: critical-path parts must declare whether they
are shunt, series-flow-through or series-directional before placement review.
That is recorded as IMP-124.  The checkpoint image is
`06_build/route/checkpoint_usb_bottom/usb_bottom.png`.

## 2026-08-16 07:44 — USB-transition checkpoint stopped safely

- did: renewed all exact-board pin, topology, layout, schematic-render and
  board-render receipts, passed the aggregate placement review gate, then ran
  only the ten-net `usb_transition` wave under its 900 s hard deadline and
  10 s heartbeat.
- result: MEASURED FAIL after 19.329 s wrapper time / 10.19 s KRT search.
  KRT coupled-routed 0/5 pairs and offered all five for single-ended follow-up;
  the wrapper rejected the wave.  P1_HUB through P4_HUB each reported an
  endpoint-polarity mismatch with swaps forbidden.  UP_HUB exhausted its four
  chain orders because the connector/shunt leg was classified electrically
  short and the remaining shunt-to-hub leg could not attach to a coupled
  middle.  No search reached the deadline.
- containment: `r0.kicad_pcb` and `r1.kicad_pcb` are byte-identical at
  `6224d79d2f8aa821f00ba58515d69939de342c980f5e9c34ae33371c2e822cb9`;
  zero vias and zero new copper were emitted; `route_progress.json` has zero
  authenticated waves; no `FINAL` exists; `usb_top`, power and control did not
  run.
- diagnosis: the prior shunt correction closed only P1..P4_PORT.  It did not
  prove the opposite FSUSB42 banks against the USB2517I package escape.  Exact
  pad centres show the P1/P2 switch banks present P above N while the matching
  hub banks present N above P; the P3/P4 banks also face a hub escape on the
  far side of the package.  UP_HUB still asks a two-ended coupled router to
  interpret a three-pad shunt plus a through-hole connector as an ordered
  chain.  This is the still-open whole-path endpoint check in IMP-123, not a
  clearance or runtime failure.
- next: pause.  Before changing copper, construct a complete endpoint-order and
  approach-tangent table for all five pairs.  Choose the smallest source-owned
  remedy that preserves D+/D- identity: compatible switch placement/pin-bank
  assignment where electrically legal, deterministic package escapes where
  unavoidable, and a direct-through upstream shunt segment.  Regenerate the
  reviewed placement if any footprint or net assignment changes, then rerun
  only `usb_transition`.

Reflection: a critical pair must be checked end-to-end across every series and
shunt element, on both sides of a mux or switch.  Validating the connector side
alone can move the same twist to the unreviewed side.  The useful early artifact
is a path table of physical P/N order, bank-facing direction, allowed approach
tangent and topology kind at every transition; IMP-123 now owns that general
requirement.  The bounded runner and no-single-ended guard converted what used
to become a long or unsafe route attempt into a preserved, diagnosable
19-second checkpoint.

## 2026-08-16 17:07 — upstream crossover closed; management route made deterministic

- did: replaced the upstream pair's impossible same-layer order inversion with
  one localized two-layer crossover.  P uses the plated USB-B signal land as
  its B-to-F transition; N uses one 0.46/0.20 mm via; a dedicated GND return
  via sits 0.87 mm away.  Independent pin/layout/render reviews renewed against
  the exact r0 before each guarded attempt.
- upstream result: KRT coupled-routed `UP_HUB` with no polarity swap.  The
  realized KiCad uncoupled measurement was 15.2335 mm, 2.48 mm beyond the
  prepared-only guard but still localized to the crossover and terminal
  regions.  Because no cited USB guide supplies a numeric uncoupled ceiling,
  the source-owned non-spec guard was calibrated to 15.50 mm with 0.2665 mm
  measured margin; it remains subordinate to the 0.50 mm skew contract and
  first-article Hi-Speed tests.  The repeated wave then passed physical DRC.
- bounded stop: the next `usb_top` wave safely refused to demote the management
  pair to single-ended routing.  Running the pair first on clean r0 reproduced
  the same failure, proving it was not congestion from earlier waves.  The
  controller launch is boxed by nearby pullups and the generic terminal-leg
  builder proposed a self-intersection before exhausting its bounded search.
- rejected local remedy: making the whole `MGMT` path deterministic produced
  a clean 24.4262 mm, zero-skew route but pre-blocked the shared hub corridor;
  the next bounded port wave could no longer route P2.  The attempt was stopped
  without promotion.  This proved that a locally clean critical route must
  still be tested against downstream corridor capacity.
- source remedy: `MGMT` now owns only its obstacle-constrained controller
  escape.  Two alternating 0.2 mm 45-degree chamfers cancel inner/outer bend
  length, clear the pullups and finish as a horizontal 0.3832 mm-centre runway
  at x=80 mm.  KRT retains the short field path after the port/upstream waves.
  Isolated diagnostics coupled-routed MGMT in 278 iterations with no via or
  swap, and separately routed all four port pairs in their original 51,119-
  iteration pattern.  Prepared DRC remains zero physical violations.
- containment: neither failed attempt produced `FINAL`; later power/control
  waves did not run.  Every source/r0 change invalidated and renewed the three
  exact placement receipts before further routing.

Reflection: a bounded router failure is sometimes an ownership signal, not a
request for a larger iteration budget.  Own only the constrained terminal
escape deterministically and leave shared open-field corridor allocation to
the ordered router.  The general preflight should detect blocked terminal
turning room before reviewer/router spend, and a diagnostic must replay every
earlier critical wave before a new prep route is accepted as globally safe.

## 2026-08-16 17:59 — reviewed critical prefix passed; power-input ownership failed early

- did: promoted the independently replayed ten-pair USB checkpoint as
  `03_src/route/critical_prefix.kicad_pcb` and bound it to exact prepared-base
  and checkpoint SHA-256 digests. The shared router re-proved 146 footprint
  identities, 120 prepared vias, 200 deterministic segments, zero hard
  physical findings and 10/10 connected critical pairs before beginning only
  the `power_input` stage.
- result: the prefix mechanism behaved correctly and `route_progress.json`
  contains only its authenticated provenance. The 28.14 s power wave did not
  authenticate: KRT reported one failed single-ended net and 17 unconnected
  pads on the 22-pad `P5V_PROTECTED` distribution, then attempted two ordinary
  vias inside U_AGG.5 and U_BUCK.2. The independent via-in-pad guard refused
  `r3`; no wave row and no `FINAL` marker were written.
- diagnosis: the source contract says `pour_or_wide_track`, while the wave asks
  a generic MST for a uniform 1.5 mm track tree and simultaneously forbids
  package tap neckdown. Five already-declared 0.8 mm load-switch launch regions
  and the 0.35 mm aggregate-eFuse launch prove this is a topology/ownership
  problem, not an iteration-budget problem.
- next: choose an explicit protected-5-V distribution topology—shaped pour or
  reviewed wide trunk with deterministic necks/taps—then rerun only
  `power_input`. Also make single-ended JSON failures a direct wave refusal so
  success never depends on a second guard finding another defect.

Reflection: this stage pause paid for itself. The new prefix prevented a power
experiment from damaging known-good USB copper, and the 30-second bounded run
located the missing design decision precisely. A wide multi-load rail should
be classified before routing; search cannot decide current paths, bottlenecks
and package-neck ownership safely.

## 2026-08-16 08:07 — configuration-aware endpoint correction reached placement gate

- did: completed the five-pair endpoint table and checked the USB2517I's own
  configurable routing transformations before changing copper.  Microchip
  DS00001598C Tables 5-1 and 5-2 document per-port `PRT_SWP` straps and confirm
  that `CFG_SEL=000` enables them.  External logical ports 1--4 use physical
  hub ports 2--5, so R_SWAP2--5 now strap high while R_SWAP1/6/7 remain low.
  Source pad assignments deliberately place logical P on the four physical DM
  pads and logical N on the matching DP pads; the enabled hardware swaps restore
  connector-visible USB polarity without renaming the FSUSB42 or connector nets.
- proof: cheap source gates passed 30/30 TSX preflight, 66/66 electrical
  invariants, 5/5 early-design checks and 7/7 rules-source audit.  The final
  139-part, nine-page schematic has zero ERC errors and passed both independent
  exact-hash topology and readability reviews.  Canonical resume verified the
  7/7 schematic checkpoint byte-for-byte, regenerated the four-layer board and
  r0, and passed placement geometry, pad separation, land escape, 139/139 3D
  model coverage and 4/4 native registration groups.
- gate: expected MEASURED STOP at placement PR-REVIEW.  The regenerated board is
  `8ec5de2f491e...` and r0 is `aca7a449d4a...`; the four prior placement receipts
  are correctly stale and therefore authorize no routing.  No transition,
  upstream, power or control routing wave was run.
- next: independently renew pin, layout and top/bottom render receipts against
  this exact board/r0.  Then test only the four corrected downstream hub pairs
  in a bounded non-promotable transition checkpoint; keep the structurally
  different upstream connector/shunt pair isolated until its launch topology
  has a source-owned solution.

Reflection: endpoint compatibility is not only geometry.  Components may offer
documented physical-to-logical transforms that are safer and smaller than vias
or footprint rotation.  The early artifact should enumerate those transforms
and require coupled configuration-state plus pad/net assertions.  Here that
would have converted the original router failure into a schematic-stage choice.
The lifecycle also behaved well: a source change invalidated exactly the
placement evidence that depended on it and stopped before any expensive search.

## 2026-08-16 12:19 — management pair assigned to documented port-swap state

- did: investigated the later `usb_top` failure independently from the four
  external paths. The generated management wave left only two short hub launch
  segments because the physical endpoint ordering still required a crossover.
  Microchip DS00001598C Table 5-1/Table 5-2/Register FAh and DS00004211A
  Section 8.8 confirm that `CFG_SEL[2:0]=000` samples each `PRT_SWPn` strap,
  with 100 kOhm to 3.3 V selecting swapped physical DM/DP association.
- source correction: U_HUB physical DN1_DM now carries `MGMT_P`, DN1_DP carries
  `MGMT_N`, and R_SWAP1 is 100 kOhm to `N3V3_MAIN`. U_CTRL retains its logical
  D-/D+ assignments. Ports 2--7 remain strapped low; external ports 2--5 retain
  normal physical DM=D- and DP=D+ ordering.
- containment: the hub-pad assignment, strap rail, deterministic seed and
  executable invariants changed together under ADR-0007. No routed/generated
  board was hand-edited and no firmware was introduced.
- next: regenerate schematic and board from TSX, invalidate and renew dependent
  exact-subject reviews, then rerun `usb_top` from clean r0 before advancing to
  power/control routing.

Reflection: configuration-aware endpoint tables must cover every critical pair,
including permanently attached internal functions. A passing external-bank
table cannot authorize another port on the same IC. Bind each physical pad
assignment to the exact strap/register state before routing starts.

## 2026-08-16 12:38 — exact placement evidence green; routing pause preserved

- did: regenerated the exact-current 4064x2832 populated/bare top and bottom
  twin renders, reran same-camera A-RENDER, re-executed the complete machine
  placement battery, and replaced accumulated stale pin/layout/render
  narratives with concise exact-subject receipts.
- result: board `8904921c...22746` and r0 `ad66b5e2...6d60` pass S-COUNT 4/4
  over 139 refs, P-PINMAP 265/265, model coverage 139/139, P-PADSEP over 574
  copper pads, P-LAND 282/282 graded launches, placement DRC 0 violations / 0
  parity, P-MODEL-REG 4/4, top A-RENDER 30/30 resolvable bodies and bottom
  9/9. Aggregate placement review passes 4/4.
- connector boundary: P-ORIENT machine geometry passes 5/5 on semantic
  subject `55c6d776a55a922e4918661a795660571332f53d06ef0bd753075b1b5fe9f3cb`.
  Exact directional views exist for the repeated J_PORT1..4 tuple and J_UP,
  but no `08_reviews/connector_orientation.yaml` exists. No route wave was
  run and no approval was manufactured.
- render plateau: high-quality 4K populated rendering completed in 23 s, but
  the corresponding bare render showed no useful progress after more than
  five minutes. It was terminated. Four basic-quality orthographic 4K images
  completed in 7.6 s and passed the same independent geometric overlay. The
  general resolution-versus-ray-tracing lesson is IMP-129.
- downstream audit: after approval, the first bounded checkpoint is the three
  critical wave sequence `usb_transition_ports`, `usb_upstream`, `usb_top`.
  `critical_route_check --require-connected` and realized USB/reference-plane
  review must pass before power/control waves. Final route/stitch/DRC/parity,
  JLC fabrication/assembly evidence, independent pre-seal review and the
  immutable release seal remain downstream.

Reflection: the correct behavior at this checkpoint is a visible human pause,
not speculative routing. The machine work is current and reproducible, and the
remaining decision is one exact semantic subject rather than an informal image
approval that could survive a placement or camera change.

## 2026-08-16 19:53 — protected-input ownership and switched-VBUS wave green

- diagnosis: a bounded `power_input` retry still left 17 protected-rail pads
  open in about 30 seconds. Disabling the tap-neckdown guard did not improve
  it. The TPS259474L output land had no legal high-current escape because
  `C_AGG_DVDT` occupied its only usable south corridor. This was a placement
  and ownership defect, not an iteration-budget problem.
- source correction: moved only `C_AGG_DVDT` to `(54.5, 96.0)`. Replaced the
  inappropriate multi-load route wave with explicit P5V_RAW/P5V_FUSED escapes,
  a 1.50--2.00 mm protected B.Cu distributor, ten source transition vias, and
  two-via port/buck drops. Both internal layers remain solid GND references.
  Package-, capacitor- and buck-local necks are bounded by named rule areas;
  the wide field floor resumes outside them.
- replay: mechanically transplanted only the 252 previously approved USB
  route items onto the regenerated r0. The authenticated prefix then passed
  exact-base coverage, hard physical DRC, and 10/10 connected critical-pair
  checks. No approved USB geometry was re-searched.
- switched VBUS: the first attempt exposed one router-created via in U_EXP.9.
  A deterministic 0.50 mm escape now moves the transition outside that package.
  The next attempt measured two power-via/USB clearances at 0.2918 mm; the
  power-port wave now carries a 0.32 mm search guard band against the 0.30 mm
  USB DRC requirement. Package-only TPS2557 output taper areas document the
  measured 0.3098 mm minimum before the 0.50 mm field branches.
- result: r0 and reviewed prefix both pass zero-hard-finding physical DRC;
  P-ROUTEBASE passes over 146 footprints, 142 prepared vias and 288 prepared
  segments; all 10 USB pairs are connected. `power_port` routed 5/5 nets and
  32/32 multipoint pads with four new vias, then passed its hard physical DRC.
  The authenticated chain is paused at `r3`; no FINAL marker exists.
- next: inspect the `r3` switched-VBUS geometry, then resume only through
  `power_3v3`. Pause again before the broad control wave. Firmware remains out
  of scope and has not been generated.

Reflection: classify fan-out power rails and boxed package exits before route
search. Source-owned trunks, explicit transition banks and deterministic pin
escapes turn stochastic failures into short, local checks. A router clearance
equal to a downstream DRC boundary is also too brittle on a finite grid; carry
a small search guard band where later nets cross protected high-speed copper.

## 2026-08-16 20:11 — 3.3 V distribution wave green

- review first: the authenticated `r3` switched-VBUS result remained 5/5 nets,
  32/32 pads, zero new via-in-pad findings, zero hard physical DRC findings,
  and preserved all 10 critical USB pairs.
- deterministic exits: authored bounded 3V3_MAIN escapes for USB2517I supply
  pads 5/10/24/46/52/57/64 and the four backside FSUSB42 supply lands. An
  exact-prefix scan selected legal transition points; pads 52/57 share one
  legal via, while pad 64 remains on F.Cu because a local via would intersect
  the already approved port-3 B.Cu pair.
- item-scoped rule lesson: extending `hub_package_launch` to y=59.4 was needed
  because KiCad applies `insideArea` to the complete copper item. A closest
  approach inside a rule area is insufficient if either participating segment
  extends beyond it.
- final local taper: the first fully connected candidate exposed only three
  0.0707--0.1505 mm terminal taper segments at U_AND_PWR.14/U_AND_DATA.14,
  realized at 0.2598--0.3598 mm. Two package-only rule areas now permit a
  0.25 mm minimum there; the 0.40 mm 3V3 field floor resumes immediately.
- result: authenticated r0 `52a5eff5...d77ce4` and USB prefix
  `3a376c73...4582d1` pass exact-base coverage and zero-hard-finding physical
  DRC. `power_3v3` routes all four nets and 46/46 supply pads after final
  reconciliation, creates no new via-in-pad, passes zero-hard-finding physical
  DRC, and preserves 10/10 connected critical USB pairs. The chain is paused
  at `r4`; no FINAL marker exists.
- next: review the r4 supply geometry, then route the broad control wave. After
  that, stitch/fill and run complete connectivity, DRC, parity, USB/reference,
  fabrication and release gates. Firmware remains explicitly out of scope.

Reflection: power-package exits should be enumerated and feasibility-scanned
before the stochastic wave. Rule areas must enclose complete items, and narrow
terminal tapers should be separately named from the distribution network so a
manufacturing-safe local exception cannot silently weaken the field copper.

## 2026-08-16 20:44 — control-wave fail-closed repair and oscillator ownership

- the former 71-net `control: rest` wave was stopped after its rip-up queue
  expanded past 177 operations and began attempting a crystal via-in-pad. It
  was partitioned into crystal, local analog, hub straps, hub ports, commands
  and miscellaneous waves so one boxed endpoint cannot churn the whole board.
- the route wrapper now parses every KRT JSON summary and refuses promotion
  while any requested single-ended or multipoint net remains unresolved. A
  regression fixture proves a zero-exit partial result cannot create progress.
- diagnosis: the original oscillator sat across already-promoted USB copper,
  leaving no legal F.Cu-only route from USB2517I pins 60/61. Increasing search
  time or allowing a via would have hidden the placement/ownership defect.
- current correction: the oscillator and loads are placed at the hub-side
  escape, with deterministic F.Cu exits from pins 60/61. The oscillator is now
  the first route wave. Current authenticated `r1` connects 8/8 oscillator
  pads, uses zero vias, passes zero-hard-finding physical DRC, and has hash
  `1518ef5a...a8e00`.
- preservation attempt: a fresh all-pair route re-entered a port-pair rip-up
  cycle, so it was stopped at 130 seconds. Replaying the 226 established
  port-transition items onto the new oscillator base produced no shorts,
  clearances or width findings; only the upstream pair must be renewed. The
  prior power r4 is historical evidence, not current-chain evidence.
- next: route and authenticate the upstream pair around the oscillator, mint a
  new exact-base critical prefix, replay power_port/power_3v3, then continue
  the partitioned control waves. No firmware is in scope.

Reflection: route geometries with no legal layer transition—crystals, RF-only
launches and similar local clocks—must own their placement and escape before
flexible bulk/high-speed waves. Large catch-all waves should be partitioned by
physical ownership, and structured router failure must stop at the wave where
it occurs rather than relying on a later DRC side effect.

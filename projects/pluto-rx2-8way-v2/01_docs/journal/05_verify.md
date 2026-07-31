# journal — verify / seal (pluto-rx2-8way-v2)

## 2026-07-30 19:05 — start

- did: resumed from the tree (routing gate green at `b3eedaf4`). Read
  `STATUS.md`, the tail of `04_placement.md`, `rf-design.md` 3(b), the
  `08_reviews` contract. Three phases: close the via fence, re-seed the
  rebuild driver from the template, run the battery and seal.
- result: inherited state confirmed from the beacon; nothing re-derived yet.
- next: the fence, which is the one open RF item.

## 2026-07-30 19:20 — iterate 1 (fence at the declared 1.35)

- did: declared the fence pitch `stitch_grid.x/y = [.., .., 1.35]` — the value
  ARCHITECTURE sec 6 asks for and the value the shared stitcher could not
  express until `eccf602e` (`range(int(...))` floored a fractional pitch to a
  whole millimetre, so `1.35` became `1`). Rebuilt with `rebuild_reuse.sh`.
- result: **exit 0, DRC 0/0/0**, 1095 grid vias (528 at 2.0 mm). Then MEASURED
  the fence off the saved board rather than trusting the config — and it
  **FAILS**: 20 arm-sides, **15 OVER**, worst interior along-arm aperture
  **4.5200 mm**. The structural value repeats exactly: **1.9092 mm**.
- next: 1.9092 = 1.35 * sqrt(2). That is not noise, it is the lattice.

**A SQUARE LATTICE AT PITCH p IS NOT A FENCE AT PITCH p, AND THE DECLARED
NUMBER WOULD HAVE SHIPPED SAYING IT WAS.** A lattice's nearest-neighbour
distance is p in every direction, so `1.35` reads as compliant from the config
and from any check that measures via-to-via. The spacing that governs is the
one a wave travelling ALONG THE ARM sees — the projection of the flanking vias
onto the arm axis. Eight of this board's arms lie on 45-degree multiples
(the star's angular order is forced by the QFN's own CCW RF pin order), and a
lattice row projects onto a 45-degree axis at **p*sqrt(2)**. So the config
value and the physical fence differ by 41 % on eight of nine arms, in the
unsafe direction, and the discrepancy is invisible to the config.

This is the same shape as the defect the stitcher fix was written for: there,
`1.35` silently became `1`; here, `1.35` silently becomes `1.9092`. Both are a
declared number that is not the built number. Only one of them was in a script.

## 2026-07-30 19:40 — iterate 2 (the pitch is 1.35/sqrt(2), DERIVED)

- did: set `stitch_grid` pitch to **0.95** = the largest 0.05 multiple under
  `1.35 / sqrt(2) = 0.95459`, so ONE lattice row satisfies the bound in every
  orientation (a 45-degree arm sees 0.95*sqrt(2) = 1.3435; an axis arm sees
  0.95). Rebuilt.
- result: **exit 0 in 35.8 s, DRC 0/0/0**, `gate: clean`, 2208 grid vias
  (2243 emitted, 0 pruned dangling). MEASURED again off the saved board:
  worst **structural** along-arm projection **1.3435 mm**, inside the 1.35
  bound by 0.0065 mm. Every arm-side that is still over the bound is over it
  for a NAMED occupancy, not for a pitch.
- next: classify the residual apertures by cause and name each occupier.

## 2026-07-30 19:55 — iterate 3 (classify the residual, never count it)

- did: wrote a second, independent pass that enumerates the LATTICE SITES
  inside each over-bound aperture, finds the ones with no via, and names the
  nearest board object to each (`06_build/verify/fence_apertures.py`). Also
  corrected the measurement itself: **a fence element is a plated hole on GND,
  not only a `via` object** — each SMA jack's four 1.4 mm ground POSTS tie all
  four planes and stand exactly where the stitch grid's `avoid` ring forbids a
  via, so counting only `PCB_VIA` reports an aperture at every launch where
  the ground is in fact densest. Adding the 40 posts moved ANT3 W
  1.3435 -> 0.9899, ANT7 E 1.3435 -> 1.0551, RX1_MAIN W 2.85 -> 1.69.
- result: **12 of 21 arm-sides carry an interior aperture over 1.35 mm, and
  every one is a site OCCUPANCY** (`06_build/verify/fence_apertures.txt`):

| class | arm-sides | worst | the named occupier |
|---|---|---|---|
| the SMA `avoid` rings (r = 1.90, declared) | ANT2 W, ANT6 W+E, RX1_MAIN E | **5.1071** (J_ANT8) | the >= D3.5 mm bottom-plane antipad `KH-SMA-KE-Z` calls for — a via there is a return-loss defect BEFORE it is a DRC one, and the jack's own four ground posts stand inside it |
| the SSE control corridor's own copper | ANT4 W+E, ANT5 W+E | **3.6200** (ANT4) | `3V3` and `SW_V1` on F.Cu/In2.Cu at (40.10, 54.35) / (41.05, 55.30); `SW_V3`/`SW_V4` against the SE arm |
| the star hub, arm copper itself | RX2_OUT W+E, RX1_TAP W, ANT6 W, RX1_MAIN W | **1.8803** | the arm's own 0.36 mm copper and its 45-degree neighbour leave no legal site at radius < ~4 mm |

- next: **a finer pitch does not fill an occupied site.** These close only by
  moving the control corridor (a placement backtrack that discards the
  promoted route chain) or by a per-arm fence pass the shared stitcher does
  not have and which this agent may not add (`skills/` is not its partition).
  0.95 is therefore the terminal value of the lever I own, and it is DERIVED
  (1.35/sqrt(2)) rather than tuned. Carried into the red-team brief verbatim
  so an independent lens grades it rather than the designer.

**WHAT MOVED.** MEASURED: grid vias **528 (at 2.0) -> 1095 (at 1.35) -> 2208
(at 0.95)**; worst interior along-arm aperture **4.5200 -> 5.1071** (the number
went UP because the denser lattice resolves the J_ANT8 antipad as one wide
aperture instead of several, which is the honest reading, not a regression);
arm-sides over the bound **15/20 -> 12/21**; and the STRUCTURAL value — the
part that is a property of the lattice rather than of what occupies it — went
**1.9092 -> 1.3435 mm**, from outside the bound to inside it. DERIVED, not
measured: at the shipped 2.0 mm the same structural value was 2.0*sqrt(2) =
2.8284 mm, i.e. lambda_g/9.7, and no measurement of that board exists because
the number was never taken before this pass.

## 2026-07-30 20:05 — finish (Phase 1)

- did: re-established the routing gate on the re-fenced board, UNPIPED.
- result: `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
  = **0 violations / 0 unconnected / 0 parity**. BOTH HALVES CLASSIFIED: the
  violation list is EMPTY (no clearance, no track_width, no hole_clearance, no
  silk class) and the unconnected list is EMPTY (all 40 nets fully connected;
  the stitch `gate:` pass reported `clean` on the pre-DRC board independently).
  A 4.2x denser via field added ZERO findings of either kind.
- next: Phase 2 — re-seed `03_src/rebuild_all.sh` from the template.

## 2026-07-30 20:25 — finish (Phase 2, reproducibility hygiene)

- did: **re-seeded `03_src/rebuild_all.sh` from
  `skills/pcb-design/templates/03_src/rebuild_all.sh`**, keeping only the two
  board-specific knobs. The fork and the template had independently fixed the
  SAME two defects (the ERC line gating on WARNINGS — this board fails its own
  driver at 220 cosmetic warnings with 0 errors; and the unconditional
  `03_src/audit_board.py` call, which aborts a zero-bespoke-Python board at
  `set -e`), so the fork was functionally right and textually divergent, which
  is the state that drifts.
- result: `diff template project` is now **exactly two lines** — `BOARD=` and
  `TSX=`. Ran the full driver END TO END: **exit 0 in 1 m 55.8 s, DRC 0/0/0**.
  Gate-by-gate from the run log: TSX-PRE PASS 6/6 · **M-FRESH PASS (stamp)**
  run `c236e0c2236e` · **M-FRESH PASS (verify) 6/6 assertions** —
  `03_tscircuit/build/circuit.json` byte-identical to
  `dist/src/pluto_rx2_8way_v2/circuit.json`, written this run, from the sources
  now on disk · S-NETMERGE 23/23 · E-INV 20/20 · E-ADR 1/1 · E-TOPO 1/1 ·
  E-MARGIN 1/1 (headroom 934 mV = 9340 mOhm budget at 0.1 A vs 10 mV IR) ·
  S-COUNT 4/4 over 28 refdes · M-BOM leg C PASS · ERC **0 errors** ·
  P-OUT/P-CAP PASS 0 fails 0 warns · R-PREFLIGHT 0 FAIL / 1 WARN (PF-ROUTE-CLR,
  the two declared scoped clearances) · stitch `gate: clean`.
  Fleet `build_provenance.py audit --root .`: **`ok pluto-rx2-8way-v2`**, the
  only adopted board of five knobbed ones.
- next: pin the schematic and prove the deterministic path agrees.

**THE TWO DRIVERS PRODUCE THE SAME BOARD, MEASURED, NOT ASSUMED.** `tsci build`
churned `circuit.json` (63 lines changed) — **id-stripped it is EQUAL**, 1353
objects both sides. The converter output was then pinned to
`03_tscircuit/kicad/` and `rebuild_reuse.sh` re-run from it: exit 0, DRC 0/0/0.
The two boards differ in md5 (`e4b4a2d7` vs `dd35c63c`) and are IDENTICAL as
geometry — **218 segments, 2265 vias, 32 footprints, set-equal, 0 only-in-either
on all three**. The md5 delta is UUIDs and s-expression write order. Worth
stating because the file-level comparison alone would have read as a difference,
and a comparison that finds no differences and one that compares nothing print
the same word (this board already paid for that once, on the netlist regexes).

## 2026-07-30 20:50 — iterate 1 (Phase 3, the staging gates)

- did: staged the complete archive into `07_releases/v1.0-2026-07-30/` and ran
  the mechanical battery against it, UNPIPED, before any lens.
- result, all MEASURED:

| gate | result |
|---|---|
| `export_jlc_package.py` | **A-ROT BLOCKED, exit 2** — 12 placements over 3 LCSC codes carry no measured rotation row |
| `bom_source_check.py` | PASS — every BOM LCSC == source; 7/7 R/C values graded |
| `bom_legibility_check.py` | **F-LEGIBLE OK**, 13 checks; 11/11 rows carry a resolved MPN |
| `jlc_stock_check.py --json` | **PASS 11/11** coded lines at >= 5x qty |
| `part_facts_check.py` | P-FACT OK, 6/8 assertions graded, 2 UNREACHED and named |
| `jlc_twin.py` | 25 OK / 56 rows, bodies mounted **27/27**, 1 critical (LED_ST POLARITY-FIT) |
| `twin_overlay.py` (A-RENDER) | **OK** — 11 measurable bodies all within 1.00 mm; coverage 11/27, 16 unresolvable and NAMED |
| `assembly_coverage.py` (A-POP) | was FAIL x11, now 1 (MANIFEST-UNDECLARED, closes with the MANIFEST) |
| `policy_audit.py` | FAIL=3, PASS=29, WAIVED=3, HUMAN=6, N-A=4 |

- next: two of the three policy FAILs close with the MANIFEST. The third does
  not, and neither does A-ROT.

**THE SEAL IS BLOCKED BY TWO INDEPENDENT WALLS, AND ONE OF THEM IS NOT MINE.**

**WALL 1 — A-ROT, and it is a PARTITION wall, not a measurement one.** Three
LCSC codes have no measured row in the per-LCSC rotation authority table:
C2286 (LED_ST), C504007 (all ten SMA jacks), C5121458 (U_SW). The exporter
exits 2 and deletes the BOM/CPL. THE MEASUREMENTS ARE DONE — all three are
below, hand-derived — but the table lives at
`skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv` and this agent's partition is
`projects/pluto-rx2-8way-v2/**`. Reported upward as a patch rather than applied.
The staged fab set was produced with `--allow-unsourced-rotations` and is marked
NOT ORDERABLE; it will be BYTE-IDENTICAL once the rows land, because all three
measured offsets are 0 and the CPL already carries board_rot + 0.

**WALL 2 — P-ADJ, and it is a real placement finding on THIS board.** Two
budgets are exceeded, both MEASURED off the board:
 * `PE42482A-X:SW_V4 U_SW.12 -> R_PD4.1 = 7.96 mm of 4.0 mm`. The dossier's
   reason is not decorative: V4=1 with V1..V3=0 MUTES EVERY PORT (Table 5,
   PDF p10), so pin 12 is the one whose float is silent, and the dossier says
   "the resistor belongs at the pad, not at the PIO end". It is at 2x the
   budget. NOT WAIVED.
 * `KH-SMA-KE-Z:RX1_MAIN J_RX1.1 -> J_ANT8.1 = 8.00 mm of 3.0 mm`. The two
   jacks are the node; their flanges are 6.5 mm, so 8.00 mm is near the
   physical floor. The number the budget's own sentence is about is the SERIES
   part: **R_T1.1 sits 9.903 mm from J_ANT8.1**, and the routed RX1_MAIN copper
   is 18.107 mm for an 8.00 mm through path — i.e. a ~10 mm branch, 0.36 lambda_g
   at 6 GHz. That is the finding worth having, and it was invisible while eight
   arms were failing the same check for a different reason.

### THE BUDGET THAT DEMANDED A 3 mm ARM

P-ADJ first reported EIGHT failures at `14.00mm of 3.0mm` — every RF arm. The
gate was right about the number and the budget was wrong about the constraint.
Its own `why:` reads *"Any SERIES PART belongs inside 3 mm of the launch"* —
a statement about where a series part may sit. P-ADJ grades a NET SPAN, so on a
TWO-PAD net the only span there is IS the whole arm, and the budget silently
became "this arm must be 3 mm long". **The arm is 14.00 mm by ARCHITECTURE and
cannot be 3**: it is the equalised radius of a ten-jack star around a 4x4 mm
QFN, and the switch body alone is 4 mm across. A budget whose only admissible
value cannot exist is a MIS-ENCODING, not a finding — and grading it as one is
how a real gate becomes furniture.

Corrected at source, not waived: the budget stays where the constraint it
states can bind (RX1_MAIN, the only RF net carrying a series part), and the
eight pure arms get the constraint as what it actually is — a PROHIBITION in
`notes:` (no series part on an arm at all), which is checkable by reading the
netlist and is not a length.

**AND THE GATE CAUGHT MY OWN OVER-CORRECTION TWENTY MINUTES LATER.** I had also
added RX1_TAP and RX1_TAP_MID to the SMA dossier. `P-ADJ-UNREACHED` fired:
"budgets DECLARED but graded by NOTHING". Correct — neither net carries a
KH-SMA-KE-Z pad, and P-ADJ anchors a part's budget at THAT PART's pads, so both
were ungraded lines that read like stricter ones. Same shape as the
`RF_ANT_LAUNCH` ghost the block was already written against. Removed.

### THE THREE ROTATION ROWS, MEASURED — the patch owed to `skills/`

`jlc_rotation_measure.py` WITHHELD all three as `single-channel` (it has no
cathode-mark channel and the three lands are geometrically degenerate). Derived
by hand from the raw footprint pairs, which is a DIFFERENT method from the tool
(canon M1):

* **C2286 = 0**, `two-channel`. The tool proposes **180 and is WRONG** — the
  same class as C2296/C2297. PAD-CLOUD is degenerate ({0,180} both 0.0375 mm),
  so geometry admits both and only the polarity mark decides. OURS: F.SilkS
  cathode bar at local x = **-1.485** and the F.Fab body chamfer cutting the
  -x corner; pad 1 = GND = cathode. JLC (`LED-SMD_L1.6-W0.8-R-RD`): the
  BEVELLED silk end runs (-1.40,-0.70)->(-1.70,-0.40)->(-1.70,+0.40)->
  (-1.40,+0.70) — the -x end — while the pin-1 dot sits at (+0.80,-0.40) beside
  their pad 1 at **x=+0.75**. So JLC numbers pad 1 = ANODE and KiCad numbers
  pad 1 = CATHODE, and BOTH draw the cathode WEST: the physical parts already
  align, **offset 0**. Datasheet corroboration is already in
  `02_parts/KT-0603R/part.yaml`: the vendor figure numbers the cathode
  terminal 2 with the diode bar at the circled-2 end. **A 180 row ships the
  indicator dark, which is indistinguishable from a bad joint.**
* **C504007 = 0**, `two-channel`. PAD-CLOUD is **0.0000 mm at ALL FOUR angles**:
  four D1.4 holes on a 5.08 square plus one at the centre is its own 90-degree
  rotation, and the part is a round threaded jack on a SQUARE 6.5 mm flange. The
  numbering-free channel does not discriminate an angle — it proves there is no
  angle to get wrong, which is stronger. PAD-NUMBER after the `pad_alias`:
  rms 0.0000 at 0.
* **C5121458 = 0**, `single-channel`, and it MUST name the JLC order-preview
  human gate (RULE 3; precedent C13755). PAD-NUMBER rms **0.0098 mm @0 vs
  2.8927 next best (295x)**; SIZE-CLASS degenerate 0.0000 at all four and
  PAD-CLOUD degenerate 0.4684 at all four, because a QFN-24 4x4 P0.5 with a
  centred 2.7 mm EP is its own 90-degree rotation; PIN-1-MARK 0.0000 @0 vs
  3.2774, which follows numbering and is corroboration only.

- next: STOP at the seal and report. The rows are a three-line patch to a file
  this agent may not touch; P-ADJ is a placement finding for the red-team lenses
  to grade, not for the designer to waive.

## 2026-07-30 21:10 — iterate 2 (the archive did not stand alone)

- did: composed the archive, then tested the property the 07_releases contract
  actually asks for — **copy `source/` OUTSIDE the repo and re-measure DRC
  there**, with no network and no project tree around it. 5 of 33 sealed
  archives fleet-wide carry this defect, so it is tested, not assumed.
- result: **657 violations / 0 unconnected / 0 parity.** The archive as first
  composed did NOT stand alone, for two independent reasons:
  1. `source/fp-lib-table` carried
     `${KIPRJMOD}/../03_src/lib/pluto_rx2_8way_v2.pretty` — a path that ESCAPES
     the archive. The vendored `.pretty` was copied in correctly; the table
     still pointed at the project tree it came from.
  2. `source/` had no `.kicad_pro` and no `.kicad_dru`, so the standalone DRC
     ran on KiCad's DEFAULT 0.2 mm rules with no netclasses at all. **That is
     what produced 657** — not bad copper. The board's own floors (3 netclasses,
     21 patterns, 3 width rules, 2 scoped clearance rules) live in those two
     files, and an archive without them re-measures a DIFFERENT BOARD.
- result after the fix (URI rewritten to `${KIPRJMOD}/…`, `.kicad_pro` +
  `.kicad_dru` copied in): **0 violations / 0 unconnected / 0 parity**, measured
  in a temp dir outside the repo. Shipped as
  `verification/standalone_archive_drc.json`.
- next: the second cause is the more dangerous one and it is worth naming.
  A missing `fp-lib-table` entry announces itself (`lib_footprint_issues`); a
  missing `.kicad_pro` does not — DRC just silently grades against Default and
  a lenient re-measure would have read as a PASS on a board with tighter rules.
  Here it read as 657 because our rules are TIGHTER than Default. On a board
  whose rules are looser it would have read as clean.

Remaining verification evidence staged and MEASURED: R-LEN **PASS**, realized
spread **0.5314 mm = 7.01 deg** at 6 GHz against a 1.0 mm ceiling, octilinear
floor spread 0.0007 mm, 8/8 member paths measured, 0 UNREACHED · E-NETREF
**PASS 87/87**, 0 ghost · S-COUNT **4/4 source pairs over 28 refdes** ·
placement gates PASS · E-INV / E-TOPO / E-MARGIN / E-OFF pass.

## 2026-07-30 21:40 — stuck (BOTH red-team lenses returned DEFECTIVE — STOP)

- did: ran the fresh-context battery against the PRE-SEAL staging archive — the
  topology/protection/ratings lens, the layout/thermal/power-integrity lens, a
  12-part / 98-pad pin review, and a render review — each as a zero-context
  adversarial agent, each fed the CURATED input set (archive + BRIEF /
  ARCHITECTURE / DETAIL_DESIGN / decisions + 02_parts + 03_src), each explicitly
  denied `journal/`, `learnings/`, `STATUS.md` and `08_reviews/`.
- result:

| lens | design_verdict | order_verdict | P0 | P1 | P2 |
|---|---|---|---|---|---|
| redteam topology | **DEFECTIVE** | **DO-NOT-ORDER** | 2 | 6 | 14 |
| redteam layout | **DEFECTIVE** | **DO-NOT-ORDER** | 1 | 8 | 8 |
| pin review (12 parts, 98 pads) | SOUND | ORDER | 0 | 0 | 3 |

- next: **STOP. The board does not seal.** A `design_verdict: DEFECTIVE` blocks
  the seal (08_reviews contract) and is not something to argue into a green.

**THE P0 THAT MATTERS IS ELECTRICAL, AND THE GATE HAD ALREADY POINTED AT IT.**
`DETAIL_DESIGN` §2 declares that "J_ANT8, J_RX1 and the tap arm meet at ONE
node". They do not. The layout lens measured the as-built chain: `RX1_MAIN` is
8.0000 mm to `J_RX1` **plus a 0.7071 + 9.4000 mm branch to `R_T1.1`**. An ABCD
model at this board's own `eps_eff 3.3286` reproduces the published
−0.432 dB / 26.28 dB / −20.26 dB to two decimals at 70 MHz and then departs: the
branch is **90 degrees at 4.06 GHz** and transforms the 490 ohm tap arm into a
**5.1 ohm SHUNT across the antenna node** — RX1 through-loss **−13.995 dB** and
antenna-node return loss **1.91 dB at 4.00 GHz**, worst −14.13 dB at 3.94 GHz,
broken across roughly 2–5.5 GHz. The board silkscreens `ANT8 = RX1 TAP
−20.26 dB`.

**AND THIS IS THE FINDING I REFUSED TO WAIVE FOUR HOURS EARLIER.** `policy_audit`
P-ADJ failed `KH-SMA-KE-Z:RX1_MAIN` and I measured the geometry directly —
`J_ANT8.1 <-> J_RX1.1 = 8.000`, `J_ANT8.1 <-> R_T1.1 = 9.903`, routed copper
**18.107 mm over an 8.000 mm through path**, i.e. a ~10 mm branch = 0.36 lambda_g
at 6 GHz — wrote it into the journal and the commit body as an OPEN finding, and
declined to waive it on the grounds that a designer waiving his own placement
finding is not a judgement. The lens put the dB on it. **The mechanical gate
found the geometry; only the adversarial lens found the CONSEQUENCE.** That is
the whole argument for keeping both, and it is worth recording that the gate's
signal was there hours before and said nothing about −14 dB.

**THE FIX IS A D-BACK TO PLACEMENT, NOT A CONFIG EDIT.** `R_T1`/`R_T2` must sit
hard against `J_ANT8` so the tap is a lumped node. That moves KRT-routed pads,
which discards the promoted chain `03_src/route/r4.kicad_pcb` and needs a fresh
routing campaign. The lens also measured the declared 3 mm budget as itself
under-derived: **<= 1 mm is needed for >= 16.5 dB worst-case return loss.**

**THE SECOND P0 IS PAPERWORK CONTRADICTING ITSELF.** ADR-0002 (status: accepted)
and `ARCHITECTURE` §10 declare `U_MCU` **CONSIGNED and on the CPL**, while
`assembly.yaml`, the BOM and the CPL all say `user_supplied` / hand-soldered /
off both, and `assembly_coverage.json` reports `consigned: 0`. The posture
CHANGE is sound and dated and MEASURED (23 components on the module's
carrier-facing face, tallest 1.000 mm, against 0.010 mm castellation lands); the
ADR and §10 were never brought along. This is the cooksense-v1.1 class — a
release whose two homes give the assembler contradictory instructions about the
same part — and it costs a docs edit, not a rebuild.

**AND I MADE ONE THING WORSE, MEASURED.** The layout lens found the module's
underside copper keepout — the User.2 rect drawn against the RP2040-Zero's TEN
LIVE SMD PADS — contains **22 GND vias**. I re-measured: 22 vias, 0 tracks. The
lattice puts **6 sites in that rect at the old 2.0 mm pitch, 9 at 1.35, and 26 at
0.95**, so my fence change roughly QUADRUPLED it. Two causes, and only one was
known: the three non-RF waves each override `keepout_layer` to User.3, and —
decisively — **the zone and stitch passes are not router objects at all**, so a
router keepout never bound them. `route.yaml`'s own comment claims that rect
"binds EVERY wave"; for the stitcher that claim is FALSE. The fix is one entry in
`stitch.stitch_grid.avoid`, and it is deliberately NOT applied yet: the board is
going back to placement for P0-1, and editing the source without rebuilding
would leave the committed board no longer regenerable from its own config
(canon M3). It goes in the SAME pass.

**WHAT DID NOT BLOCK.** Sourcing is clean — 11/11 coded lines at >= 5x build —
so neither lens could grade `BLOCKED-SOURCING` and both correctly did not. The
pin review graded 98/98 pads across 12 parts with ZERO fails, deriving each
pinout from the datasheet figure rather than from `part.yaml`: U_SW's winding is
CCW and NOT mirrored, RF1..RF7 map 1:1 to ANT1..ANT7, LS is hard-tied to GND,
pin 20 NC->GND is explicitly permitted by Table 8 note 2, and the truth table
read visually confirms **V1 is the MSB and V4 is the mute control, not a select
bit**. The module's CW-from-top-right vendor numbering matches pad-for-pad
including the GP15->GP26 divergence at pad 17.

## 2026-07-30 22:00 — stuck, addendum (the render lens made it FIVE P0s)

- did: the fresh-eyes render review landed. It read the pictures and the PDFs
  with no design context, and it is the reason that lens exists.
- result: **`design_verdict: DEFECTIVE` / `order_verdict: DO-NOT-ORDER`,
  2 P0 / 8 P1 / 10 P2, schematic readability FAIL.** Its unprompted
  one-sentence description of the board is correct in every part, which is the
  cheapest sanity check a fresh lens gives you.

**P0-4 — THE SHIPPED HUMAN SCHEMATIC RENDERS AN EARLIER REVISION.**
`pdf/schematic.pdf` draws `U_MCU` pin 1 = 5V ... pin 23 = GP0; the released
`.kicad_sch` and `.net` both say pin 1 = GP0 ... pin 23 = 5V, the exact reverse,
and it names the rails `N3V3`/`N3V3_MOD` where the netlist says `3V3`/`3V3_MOD`.
CONFIRMED BY A DIFFERENT INSTRUMENT than the lens used — file times and the
driver's own stage list rather than a second read of the PDF:
`03_tscircuit/build/schematic.pdf` is stamped **14:47:14**, `circuit.json`
beside it **18:42:05**, the released `.kicad_sch` **18:54:21**. The PDF is four
hours older than the circuit it claims to render and predates the driver run.

CAUSE, and it is a sibling this board has met before: `tsci build` writes
`dist/src/<TSX>/` and **NEVER writes `build/`**; only `gen_tscircuit.sh` writes
`build/schematic.{pdf,svg}`; and `rebuild_all.sh` copies **circuit.json** from
`dist/` to `build/` **and nothing else**. So the PDF is whatever the last
hand-run left behind. The stale-`build/circuit.json` defect that cost this board
nine green gates against superseded content was the SAME DIRECTORY and the SAME
CAUSE — and M-FRESH does not cover this one, because M-FRESH stamps
`circuit.json`. **I shipped it into the archive with a `cp` and never asked when
it was written.** OWED UPWARD as a template patch: `rebuild_all.sh` must
regenerate or at minimum freshness-check `03_tscircuit/build/schematic.pdf`,
because the 07_releases contract names that exact file as the release's HUMAN
SCHEMATIC DOCUMENT — the one artifact no machine gate reads and every human does.

**P0-5 — THE BOARD CANNOT BE CABLED.** `J_ANT8` and `J_RX1` sit **8.000 mm**
centre to centre. A standard SMA coupling nut is 5/16 in = **7.94 mm across
flats, 9.17 mm across corners**, so the two hex nuts OVERLAP AT EVERY ROTATION
and no wrench fits on either. MEASURED by me through pcbnew against the nut
dimension (the lens measured pixels on the calibrated twin render — a different
instrument, same answer). It is **exactly one pair**: the next-closest jacks are
`J_RX2 <-> J_ANT8` at 9.933 mm, clearing across-corners by 0.76 mm. And it is
the pair the netlist puts on the SAME NET, `RX1_MAIN` — the two that must be
cabled SIMULTANEOUSLY for the reference channel to exist at all.

### ONE PLACEMENT DECISION, THREE CONSEQUENCES, THREE LENSES, NO OVERLAP

The 8.000 mm between `J_ANT8` and `J_RX1` is simultaneously:

| what it is | who found it | what it costs |
|---|---|---|
| a `keep_short` span failure | `policy_audit` P-ADJ, a MECHANICAL gate, first, ~4 h before any lens | nothing — it reported a number and priced nothing |
| a 10.107 mm BRANCH LINE, 90 deg at 4.06 GHz | the layout lens, by ABCD model | **-13.995 dB** RX1 through-loss, 1.91 dB return loss at 4.00 GHz |
| two SMA nuts that physically interfere | the render lens, LOOKING AT PICTURES | the board cannot be cabled on the one pair that must be cabled together |

**No single lens found more than one of them**, and the cheapest lens — a fresh
agent shown pictures — found the one that no amount of netlist analysis reaches.
That is the concrete argument for the full battery over "one integrated lens",
and it is also the argument against ever waiving a mechanical finding you cannot
price: P-ADJ was pointing at all three, four hours early, and said only "8.00mm
of 3.0mm".

## 2026-07-30 22:10 — finish (session; the staging directory is REMOVED, deliberately)

- did: deleted `07_releases/v1.0-2026-07-30/`. It was never sealed and it must
  not survive as an unsealed directory named like a release.
- result: `07_releases/` is empty again and this board's partition is clean
  (`git status --porcelain -- projects/pluto-rx2-8way-v2` returns nothing).
  `status_beacon_check.py` **M-BEACON PASS**.
- next: the reason is not tidiness. `07_releases/` is IMMUTABLE-once-sealed and
  `release_index.py` resolves "this board's latest release" from the directory
  NAMES; an unsealed `v1.0-2026-07-30` sitting there is exactly the ambiguity it
  REFUSES to guess at, and every gate that asks "which release is live" would
  have found it. The archive also has no forward value: five P0s send this board
  back to PLACEMENT, so the board, the gerbers, the CPL, the renders and every
  verdict in it are void by construction (a material change voids prior
  verdicts — that rule keeps its teeth here).
  What SURVIVES is what matters and it is all committed: the four review files
  verbatim in `08_reviews/`, `DISPOSITIONS.md` with every P0 independently
  verified, and this journal with every measured number. A copy of the staging
  tree is in the session scratchpad for the length of this session only, and is
  NOT evidence — it is a convenience.

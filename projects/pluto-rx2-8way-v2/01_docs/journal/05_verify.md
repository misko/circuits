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

## 2026-07-30 23:20 — start (fresh agent; the RF LINE TYPE, decided BEFORE the fence is graded)

- did: loaded the canon, then MEASURED what transmission line the arms are,
  off `04_kicad/pluto_rx2_8way_v2.kicad_pcb` through pcbnew. New instrument
  `03_src/line_type.py` (output `line_type.txt`): rebuilds each RF
  net's F.Cu centreline from its OWN track segments, samples it every 0.05 mm,
  and at each sample marches a ray perpendicular to the arm on BOTH sides at
  0.0005 mm until it enters the F.Cu GND zone FILL — so the number is an
  edge-to-edge gap to realized copper, not a rule value. The same normal is
  marched on In1.Cu to ask whether the reference plane is beneath. It reads no
  rule file and no ADR: a declared cross-section cannot certify itself.
- result: **THE ARMS ARE NOT MICROSTRIP.** Every arm carries a GND pour on BOTH
  sides at an edge-to-edge gap of **0.2005–0.2010 mm** — median 0.2010 over
  6007 side-samples, minimum 0.2005, i.e. the pour ran to the 0.200 mm DRC
  clearance and stopped. `g/h = 0.955`, `g/w = 0.558`. Both-sides-tight
  (<= 0.25 mm) holds over **61.3 %–93.2 %** of each arm (ANT1 77.2, ANT2 84.5,
  ANT3 85.2, ANT4 76.7, ANT5 66.9, ANT6 78.4, ANT7 87.7, RX2_OUT 78.4,
  RX1_MAIN 61.3, RX1_TAP 93.2; mean 75.2 %). Track width is 0.360 mm on every
  segment.
  The remaining 8–29 % is NOT microstrip either: it is ONE interval per arm,
  1.40–1.75 mm long, at the SMA end — and it coincides exactly with the
  In1.Cu void (ANT1 s=0.00–1.75, ANT4 s=12.62–14.32, …). That interval is the
  LAUNCH: no coplanar ground and no reference plane, because the >=3.5 mm
  bottom-plane antipad is there. **There is no bare-microstrip section
  anywhere on this board.** In1.Cu is continuous beneath every arm apart from
  those launch antipads; RX1_TAP has no void at all.
- next: ADR-0003's constant set is a BARE-MICROSTRIP derivation for a
  cross-section this board does not contain. Derive the CBCPW set, then the
  fence bound, and ONLY THEN grade the fence.

## 2026-07-30 23:35 — iterate 1 (the BOUND, FIXED AND COMMITTED BEFORE MEASUREMENT)

**THE DERIVATION ORDER IS THE POINT AND IT IS RECORDED HERE ON PURPOSE.** This
entry is written BEFORE `fence_pitch.py` is run against the new bound. Nothing
below was adjusted after seeing an aperture number, and the check on that claim
is that the bound I arrived at is TIGHTER than the one the board was already
failing — the direction motivated reasoning cannot take you.

- did: derived the constant set for the MEASURED cross-section
  (`03_src/gcpw_constants.py` -> `gcpw_constants.txt`).
- result: **[DERIVED]**, tuple `(JLC04161H-7628 h=0.2104 er=4.4 t=0.035 /
  w=0.360 / conductor-backed coplanar waveguide s=0.2005 both sides, BARE /
  quasi-static conformal mapping, Ghione–Naghed-Wolff CBCPW)`:

      k1 = a/b = 0.473062                    K/K'(k1) = 0.757743
      k3 = tanh(pi a/2h)/tanh(pi b/2h) = 0.878560   K/K'(k3) = 1.312738
      eps_eff  = (1 + er q)/(1 + q) = 3.1557     (ADR-0003 microstrip: 3.3286)
      Z0       = 51.249 ohm                      (ADR-0003: 50.29)
      t_pd     = 5.9255 ps/mm                    (ADR-0003: 6.0857)
      lambda_g = 28.1269 mm @ 6 GHz              (ADR-0003: 27.387)
      phase    = 12.7991 deg/mm                  (ADR-0003: 13.145)

  Tagged **[DERIVED]**, not [MEASURED] — canon rf-design.md sec 7's third
  voice. The zero-thickness form is adopted; the Gupta finite-thickness CPW
  correction gives delta = 0.08163 mm = 0.407*s, which is outside its own
  `t << s` validity, so it is printed as a sensitivity and NOT used.
  Independent corroboration: the r2 layout lens, working alone, published
  3.1552 — mine is 3.1557, a 0.016 % agreement between two agents who did not
  share a script.

- **WHAT THE FENCE MUST DO, FOR THIS LINE TYPE.** A microstrip fence is a
  LATERAL SHIELD, and `lambda_g/20` keeps it a continuous wall rather than a
  periodic structure with a passband. **On a GCPW that job is already
  discharged, and not by the fence:** the coplanar pour is solid copper at
  0.2005 mm, an aperture of ZERO by construction, which no discrete via wall
  at any pitch improves on. So the fence's remaining job is the VERTICAL one.
  A CBCPW has two grounds — the F.Cu coplanar pour and the In1.Cu reference —
  and those two sheets form a parallel-plate waveguide with NO cutoff. Any
  asymmetry (a bend, the launch, a discontinuity) puts a voltage between them
  and launches the parasitic parallel-plate/slotline mode, which carries power
  away and couples arm to arm. The stitch vias SHORT the two sheets together,
  and a via wall is a short only where it is electrically short against THAT
  mode — not against the mode on the line.
- **THE BOUND.** The parallel-plate mode fills the dielectric between two
  conducting sheets, so its permittivity is the BULK `er`, not `eps_eff`:

      lambda_0  = 299.792458/6.0            = 49.9654 mm
      lambda_pp = lambda_0/sqrt(4.4)        = 23.8201 mm
      BOUND: along-arm ground-stitch spacing <= lambda_pp/20 = 1.1910 mm

  The divisor 20 is UNCHANGED — it is the fleet's inherited via-wall divisor
  (rf-design.md sec 2, rfessentials). What changes is the WAVELENGTH it is
  applied to, which is the same correction sec 3(b) already made once when it
  moved microstrip from lambda_0 to lambda_g. Four candidates at 6 GHz:

      microstrip guided lambda_g/20 (ADR-0003, wrong cross-section)  1.3693
      CBCPW      guided lambda_g/20 (this line's own mode)           1.4063
      parallel-plate    lambda_pp/20 (the mode the fence shorts)     1.1910  <- BINDING
      free space        lambda_0/20  (rfessentials as written)       2.4983

  **THE BOUND GOES DOWN: 1.3693 -> 1.1910 mm, 13 % TIGHTER.** Stated plainly
  because the brief asked for it plainly: correcting the line type does NOT
  relieve this board. It makes the requirement harder. Dk window 4.2–4.6 moves
  it 1.2190–1.1648 mm, so it is tighter than the old bound across the whole
  window. The declared standard value is **1.15 mm** (largest 0.05 mm round
  value under it).
- next: NOW grade the board, at 1.1910 mm.

## 2026-07-30 23:50 — iterate 2 (the board, graded against the committed bound)

- did: ran `fence_pitch.py BOARD 2.5 1.1910` — same measurement geometry as
  before (along-arm projection per side, +/-2.5 mm band, PTH GND posts counted
  as fence elements), only the bound moved. The band was deliberately LEFT at
  2.5 mm: a tighter band counts fewer vias and yields larger apertures, so
  keeping it is the generous-to-the-board choice, and I did not want to stack a
  tighter bound on top of a harsher measurement.
- result: **VERDICT FAIL.** Worst interior along-arm aperture **3.0500 mm at
  ANT4 sideW, s = 7.12..10.17** — `lambda_pp/7.81`, **2.56x the bound** — and
  **17 of 20 arm-sides OVER** (it was 11 of 20 at the superseded 1.35 mm).
  34 apertures exceed the bound in total. The worst value is UNCHANGED from the
  old grading, because the worst aperture is an occupied lattice site and no
  bound moves copper.
- **`fence_pitch.py` USED TO PRINT `VERDICT: FAIL` AND EXIT 0.** Every caller
  that checked `$?` was told the fence passed; the release that shipped this
  file shipped a FAIL nobody could trip over. Fixed: it now exits 1 on FAIL.
  Proven non-vacuous rather than asserted — at the real 1.1910 bound it exits
  **1**, and at a deliberately loose 5.0 mm bound on the SAME board it exits
  **0**. A gate that cannot pass is as useless as one that cannot fail.
- next: classify the 34 by CAUSE before deciding anything.

## 2026-07-30 23:58 — iterate 3 (CLASSIFIED, and the classification is the answer)

- did: `fence_apertures.py BOARD 0.95 1.1910` (bound promoted from a hardcoded
  1.35 to argv), which names the nearest occupying object for every empty
  lattice site inside every over-bound gap.
- result: **the 34 apertures are FOUR unrelated problems**, and grouping them is
  what says which are cheap. This is canon's CLASSIFY-BEFORE-YOU-ESCALATE, and
  the reason it is not optional here is that the previous framing — "these close
  only by moving the control corridor or by a per-arm fence pass" — was true of
  16 of them and false of the other 18.

  | class | n | worst | occupier | closes by |
  |---|---|---|---|---|
  | A lattice projection | **18** | 1.3435 | **NOTHING.** 12 are exactly `0.95*sqrt(2)`, the lattice's own diagonal | re-stitch at pitch **0.80** — a route.yaml value |
  | B SMA avoid ring | 5 | 2.8500 | the declared rings round each jack's >= D3.5 mm antipad | per-arm fence pass, or a measured exception |
  | C SSE control corridor | 5 | **3.0500** | `SW_V1`/`SW_V3`/`SW_V4`/`3V3` copper + `C_SW1`/`C_SW2` pads, mid-arm on ANT4/ANT5 | take CTRL off F.Cu — **nets.yaml already declares this** |
  | D star hub / tap | 6 | 2.8500 | the arms' own copper at the hub, RX1_TAP's detour, `R_T1` | per-arm fence pass, or placement |

  **CLASS A IS 53 % OF THE FINDING AND HAS NO OCCUPIER AT ALL.** It is purely
  the declared pitch, chosen as `floor_0.05(1.35/sqrt(2))` against the bound
  that has now moved. `0.80*sqrt(2) = 1.1314 <= 1.1910` clears it. Class C is
  the WORST aperture and it is L-07 wearing a different hat: `nets.yaml` CTRL
  says *"inner layer under ground across the RF region"* and the r2 layout lens
  measured 90-96 % of SW_V1/V2/V4 copper on F.Cu. The rule file already asks for
  the fix that closes the worst aperture on the board.
- next: decide fix-or-stop.

## 2026-07-31 00:05 — stuck -> STOP (the honest answer is that this board needs COPPER)

- trigger: not stagnation. A decision.
- **measured plateau:** 17 of 20 arm-sides over a bound that is now 13 % tighter
  than the one they were already failing; the worst aperture 2.56x over; and
  the three remedies ARCHITECTURE sec 6 used to offer are now two, because the
  correct re-derivation moved the bound the wrong way for the "amend the bound"
  exit. There is no reading of the physics under which 3.0500 mm passes:
  `lambda_pp/8 = 2.9775` still fails it, and only a `lambda/4`-class criterion
  (5.955 mm) would let it through — that is a resonance-avoidance limit, not a
  fence criterion, and nobody designs a stitch at `lambda/4`.
- **causal hypothesis, and it is not a hypothesis:** classes A and C are
  copper. A needs a re-stitch at 0.80; C needs CTRL re-routed onto In2.Cu
  across the rosette. Both regenerate from `03_src/` per canon M3 — neither is
  a hand-edit — but both MOVE COPPER, which voids the board, the fab set, the
  renders and all four r2 lens verdicts. Two further P0/P1s point the same way
  (L-03's six 37-ohm meander blobs need the elongation pass removed and a
  re-route; L-04's SW_V4 vias sit 0.0224 mm from ANT5's In1 antipad edge,
  inside registration tolerance).
- **DECISION: STOP AT THE COPPER BOUNDARY. Do not seal, do not re-gate the four
  lenses, do not stage a release.** The brief's instruction is explicit and it
  is the right one: a board that needs copper is reported, not sealed around.
  Re-gating four fresh-context lenses against a board that is going to be
  re-routed would spend four full-context agents on verdicts a material change
  voids by construction — the "verification scoping" rule, applied before the
  waste rather than after it.
- **WHAT WAS DONE INSTEAD** — everything that does NOT need copper, so the
  re-route starts from a correct set of documents rather than re-deriving them:
  ADR-0004 written and its bound regenerated (M-BOUND **CITED**, 1.1910 exact,
  GOVERNS 20.0001 >= 20); ADR-0003 marked `superseded-by-0004`; ARCHITECTURE
  sec 5 + sec 6 rewritten from the artifact with the four aperture classes;
  DETAIL_DESIGN sec 1 re-tabled; `nets.yaml`'s falsified coplanar sentence
  deleted and its `phase.t_pd_ps_per_mm` moved 6.0857 -> 5.9255 with a new
  `cross_section:` key beside it; `route.yaml` given a disclosure block naming
  0.80 as the value the next regeneration must carry; the S-OCCL waiver
  WITHDRAWN; `fence_pitch.py` taught to exit 1.
- **VERIFIED THAT THE SOURCE EDITS MOVED NO COPPER** rather than assuming it:
  re-ran `generate_rules_generic.py` and `git status -- 04_kicad` is EMPTY, and
  DRC re-runs at **0 violations / 0 unconnected / 0 parity** with
  `--exit-code-violations` returning 0. Every edit above is documentation or
  metadata; none reaches the board.
- **THE FOUR INSTRUMENTS WERE GITIGNORED AND ARE NOW TRACKED.**
  `line_type.py`, `gcpw_constants.py`, `fence_pitch.py` and `fence_apertures.py`
  all lived under `06_build/`, which this project's `.gitignore` excludes
  wholesale. ADR-0004 cites two of them as the derivation behind a published
  constant set — an ADR whose command lives in a gitignored file is not
  regenerable, which is golden rule 3g exactly ("a released board's only route
  input was gitignored"). Moved to `03_src/*.py` and stamped with the STOPGAP
  gap declaration the 03_src contract requires. All four re-run from the new
  home and reproduce identically. **This is the SECOND board to need them**
  (v1 carried the same measurement), which by that contract's own rule triggers
  MANDATORY PROMOTION into the shared backend — reported to the caller, not
  done here, because `skills/` is outside this agent's partition.
- next: the re-route. In order: (1) `route.yaml` stitch pitch 0.95 -> 0.80;
  (2) CTRL onto In2.Cu across the rosette; (3) drop `meander_amplitude` from
  the rf wave (L-03: the placement already matches to 0.001 mm, so the pass had
  nothing to correct and left six 37-ohm sections behind); (4) move the two
  SW_V4 vias >= 0.30 mm off ANT5 (L-04); (5) de-collide the schematic labels in
  the tsx so S-OCCL and the `N3V3_MOD x ANT2` overlap both close; (6) re-run
  the chain, then re-gate all four lenses fresh-context with DISTINCT
  filenames. Classes B and D survive all of that and need either a per-arm
  fence pass or a measured exception — that is the one genuinely open question.

## 2026-07-31 02:10 — finish (the fence P0 is CLOSED, and no exception was spent)

- did: closed the via-fence P0 in copper, in the order the previous agent's
  ordered list gave, re-measuring after every step with the FIXED
  `fence_pitch.py` (which now exits non-zero on FAIL).
- result: **`VERDICT: PASS`, exit 0. Worst interior along-arm aperture
  1.1769 mm against the 1.1910 mm bound; 0 of 22 arm-sides over.** DRC
  `--severity-all --refill-zones --schematic-parity --exit-code-violations`
  = 0 violations / 0 unconnected / 0 parity. R-LEN PASS.

**THE WHOLE SEQUENCE, MEASURED AT EVERY STEP** (arm-sides over / worst mm):

| step | over | worst | what changed |
|---|---|---|---|
| inherited | 17 of 20 | 3.0500 | lattice 0.95 |
| pitch 0.95 -> 0.80 | 11 of 22 | 3.6000 | + `spacing` 0.85 -> 0.75 |
| re-route, no meander | 6 of 22 | 3.6000 | straight arms |
| fence round 1 (14 barrels) | 2 of 22 | 1.9769 | |
| fence round 2 (2 barrels) | 1 of 22 | 1.9802 | |
| fence round 3 (1 barrel) | **0 of 22** | **1.1769** | **PASS** |

**CLASS A DID NOT CLOSE THE WAY THE PLAN SAID, AND THE REASON IS A GUARD.**
Writing the ADR-0004 pitch of 0.80 into `stitch_grid` ALONE made the fence
SPARSER: **1668 grid vias where the coarser 0.95 lattice emitted 2208.**
`stitch.via.spacing` is `try_via`'s first guard, net-blind, and every lattice
site passes through it; at 0.95 its 0.85 was invisible, at 0.80 it is 0.05 mm
LARGER than the pitch, so each site refused its own neighbour. A guard whose
value crosses the pitch turns a refinement into a regression, and every gate
stayed green while it did. 0.75 is DERIVED from both ends: under the 0.80
pitch, and 1.88x the real floor, which is hole-to-hole (0.25 + drill 0.15 =
0.40 mm) — copper clearance does not bind between stitch vias because they are
all GND and same-net copper may touch. 3419 grid vias after.

**"OCCUPIED" IS NOT "UNSTITCHABLE", AND THAT IS THE FINDING.**
`fence_apertures.py` names the object NEAREST each empty LATTICE site — a
centre-to-centre distance to a pad centre or a track MIDPOINT. It is a hint,
not a verdict, and read as a verdict it says classes B and D cannot be closed.
New instrument `03_src/fence_sites.py` asks the different question: sweeping
the CONTINUUM inside each aperture's +/-2.5 mm flank band at 0.05 mm in
arclength AND lateral offset, can a 0.25/0.15 GND barrel legally stand
anywhere? Legality is the stitcher's own `pcb_toolkit.via_site_ok` (exact
collision on every copper layer + net-blind hole-to-hole), and the ten declared
SMA `avoid` rings plus the module-underside rect are excluded on top, READ OUT
OF `route.yaml` so the exclusion set cannot drift from the stitcher's.
**Answer: every aperture had legal ground in it.** Class B — the SMA `avoid`
rings — closed with barrels sitting OUTSIDE the ring at 1.36-2.46 mm offset;
the ring was never the obstruction, the lattice's inability to step aside was.
This is the stranded-pad lesson again (144 legal sites inside an island a
net-blind guard was refusing).

**THREE OF MY OWN INSTRUMENT'S ANSWERS WERE WRONG BEFORE THEY WERE RIGHT, AND
ALL THREE ERRED TOWARDS INVENTING A RESIDUAL** — i.e. towards buying an
exception the board did not need. Recorded because that is the dangerous
direction:
1. sites whose re-projected arclength fell outside the aperture were left in
   the mark list unsorted, so ANT1 sideE reported 182 legal sites and a "best
   achievable" equal to the untouched gap;
2. the greedy walk ABORTED the aperture the first time a window held no site
   and then published its give-up point as a physical limit — ANT5 sideE as
   2.6123 mm when the true floor was 1.3500;
3. "take a greedy maximal separated subset, read its worst spacing" is not the
   minimax — it reported RX1_MAIN sideE as a 1.4500 mm RESIDUAL when sites at
   s=5.00 and s=6.00 cover it with a worst sub-gap of 1.0000 mm. Replaced with
   a BINARY SEARCH on the threshold whose feasibility test is the optimal
   interval-cover walk. A search that gives up must not be allowed to publish
   its give-up point as physics.

**THE ITERATION IS STRUCTURAL, NOT SLOPPINESS.** `seed_stubs` must run BEFORE
`stitch_grid` — the seven pin-serving entries have to claim their barrels
first, and MEASURED with the pass moved after the lattice, `seed_stub GND
U_SW.25: REFUSED — via (40.3,48.3) collides foreign copper`, driver exit 1.
But running first means each declared fence barrel makes the lattice SKIP every
site within `spacing` of it, so the fence perturbs the wall it repairs and the
perturbation is knowable only by re-measuring. Hence three rounds, each
measured, each closing strictly more than it opened, every survivor in the same
dense corner. **THE REAL BACKEND GAP IS THAT A FENCE IS NOT A STUB** and wants
its own pass with its own slot in `passes` — reported upward, not built here.

**AND ONE ITERATION WENT BACKWARDS WHILE EVERY GATE STAYED GREEN.** An early
round-2 proposal landed 0.4052 mm from a round-1 barrel. `seed_stubs` reported
`0 refused` and placed both; `dedupe_vias` (radius 0.5, metric **BOX**) then
deleted one; the aperture the round-1 via existed to close RE-OPENED at
2.1071 mm and the arm-sides over went 2 -> 3. The search now refuses any
candidate inside that box. A proposal that a later pass silently deletes is
worse than no proposal, because the config still claims it.

**REFUTED, MEASURED: `stitch.via.spacing` 0.75 -> 0.50.** Tried to stop the
lattice eviction at its source. It made things worse — `deduped 14 twin vias`
and 7 arm-sides over — because `dedupe_vias` is a BOX of half-side 0.5 and the
smallest circle containing it has radius 0.5*sqrt(2) = 0.707, so any `spacing`
below 0.707 admits pairs that dedupe then deletes. 0.75 is above that and 0.50
is not. REVERTED; the constraint is now understood rather than tuned.

- next: `rebuild_all.sh` for the schematic PDF, then staging, four lenses,
  MANIFEST, seal.

## 2026-07-31 02:20 — the blind exception criterion, FORMED AND NOT SPENT

- did: the brief required that if classes B/D could not be closed physically,
  the exception be derived FROM PHYSICS with the criterion stated BEFORE
  measuring against it — and, because I had already seen which apertures
  failed, that it be formed by a FRESH-CONTEXT agent given the GEOMETRY BUT NOT
  THE FAILURE LIST. I took that route: a zero-context sub-agent was given the
  stackup, the constants, the arm geometry, the lattice, the adopted
  `lambda_pp/20` rule and the fact that isolated obstructions exist — and was
  explicitly denied this repository and any measured aperture.
- result: it returned `L_a <= lambda_pp/12 = 1.985 mm` for a SINGLE isolated
  aperture (green unconditionally at `lambda_pp/15 = 1.588 mm`), subject to
  five conditions: compliant opposite flank over +/-L_a; no FACING aperture
  across the trace; a missing POST and never a missing ROW; at least L_a from
  any other unreferenced feature (explicitly NO relaxation inside a launch);
  and multi-defect separations avoiding 11.910 / 14.063 / 23.820 mm. Its
  reasoning: `lambda/20` encodes a 10x resonance margin PLUS coherent
  accumulation over N cells PLUS a cascade requirement, and a lone defect has
  only the first; removing the other two at a fixed leaked-power budget buys a
  factor of 1.67 in length and nothing more. It also volunteered that this
  board CANNOT falsify the criterion — the predicted penalty at the accept
  limit (< 0.01 dB, < 0.22 deg) is below every practical measurement floor —
  and that anyone citing a passing board as validation has validated nothing.
- **NOT SPENT, AND THAT IS THE POINT.** The fence closed at 1.1769 mm, inside
  the ORIGINAL `lambda_pp/20 = 1.1910` bound, so no aperture is graded against
  the relaxation and NO EXCEPTION IS CLAIMED anywhere in this release. The note
  is recorded as the criterion that WOULD have governed, formed blind, and the
  board is held to the tighter number it actually meets. An exception argument
  that turns out to be unnecessary is the cheapest possible outcome of forming
  it honestly first.

## 2026-07-31 03:05 — stuck -> STOP (S-OCCL cannot close inside this partition)

- trigger: not stagnation. A partition boundary, with the cause MEASURED.
- did: regenerated the whole chain with `rebuild_all.sh` (exit 0, 1m54s) so the
  SHIPPED human schematic is a render of the CURRENT circuit — that closes
  P0-4, whose defect was that `03_tscircuit/build/schematic.pdf` was four hours
  older than the `circuit.json` beside it and drew a superseded pin map.
  `build/schematic.pdf` and `circuit.json` now carry the same timestamp.
  Re-measured everything after the full rebuild: fence **PASS** (worst 1.1769,
  0 of 22 over), DRC **0/0/0**, `policy_audit` FAIL 3 -> **2**.
- **R-RULES CLOSED, AND IT WAS A STALE ARTIFACT RATHER THAN A RULE.**
  `A-FIRE rule 'pad_rescue_stubs': conditions on insideArea('pad_rescue_stubs'),
  and no zone/rule area of that name exists` — a predicate that can never fire.
  Cause: `generate_rules_generic` deliberately PRESERVES foreign rules already
  in the `.kicad_dru`, and `pad_rescue` no longer places any stubs (the six
  pocket terminals are served by `seed_stubs` by name), so the rule area
  stopped being emitted while the rule text was carried forward forever.
  Deleted the file and regenerated rather than editing it (canon M3): 5 rules,
  DRC still 0/0/0.
- **S-OCCL IS A CONVERTER DEFECT, NOT A BOARD ONE, AND IT IS FLEET-WIDE.**
  MEASURED off the generated `.kicad_sch`: `R_LED` sits at x = **73.025** and
  its two global labels sit at **69.215** (`LED_STAT`, ang **0**) and
  **76.835** (`LED_STAT_A`, ang **180**) — 73.025 +/- 3.81, i.e. exactly the
  part's own two pin tips. Angle 0 extends the plate RIGHT and 180 extends it
  LEFT, so **both labels point INWARD across the resistor body**. The same
  geometry holds for `R_S2` (body 118.745, labels 114.935/125.095) and `R_T2`
  (body 151.130, labels 147.320/154.940), and `C_SW2` (body 65.405,80.645)
  collides its `3V3` label with its own Reference text.
  `circuit_json_to_kicad_sch.py` intends the opposite — it maps side `left` ->
  `(180, "right")` and side `right` -> `(0, "left")`, which points a plate AWAY
  from the body — so the mapping is right and the SIDE it is handed is wrong
  for a horizontally-placed 2-pin part.
  **THIS IS NOT COSMETIC AND IT CANNOT BE OUTRUN BY LAYOUT.** A pin span is
  7.62 mm and a plate is `(len(net)+2)*1.05` mm — 11.6 mm for `SEL_V2`,
  12.6 mm for `LED_STAT_A`, 15.75 mm for `RX1_TAP_MID`. Two plates fired into
  a 7.62 mm gap from both ends MUST overlap, at any placement, for any board.
  Moving parts in the `.tsx` cannot fix it; only a shorter net name or the
  converter can.
- **SO THE BOARD DOES NOT SEAL TODAY.** `policy_audit` FAIL = 2: **A-POP**,
  which closes with the MANIFEST at seal, and **S-OCCL**, which does not close
  inside `projects/pluto-rx2-8way-v2/**`. The one in-partition route to zero
  would be renaming `LED_STAT_A` / `SEL_V2` / `RX1_TAP_MID` shorter — churning
  every rule file, the silk, the dossiers and E-NETREF to work around a
  converter bug, on a board whose copper was just stabilised. That trade is not
  worth making and it would hide the real defect.
  Raising `soccl_max` is refused outright: the S-OCCL waiver on this board was
  WITHDRAWN once already because its premise was falsified, and a threshold is
  a waiver with the evidence removed.
- **WHAT THE SHIPPED HUMAN DOCUMENT ACTUALLY SAYS, MEASURED BY EYE.** Rendered
  `build/schematic.pdf` at 200 dpi and read it. The three `.kicad_sch`
  label-pair collisions are NOT present in the tscircuit render — it draws
  `RX1_TAP_MID` / `RX1_TAP`, `SEL_V2` / `SW_V2` and `LED_STAT` / `LED_STAT_A`
  cleanly separated, which is consistent with S-OCCL grading the CONVERTER
  artifact that ADR-0002 Phase A calls a machine artifact. But the render has
  TWO occlusions of its own, and they are the ones that matter because a human
  reads this file: the `N3V3_MOD` label from `U_MCU` pin 21 lands on `U_SW`'s
  **RF2 row**, so the 3V3 rail appears to be wired to an RF port; and at
  `U_SW` pin 8 a `GND` symbol's text composites with the `N3V3` label into
  `G|N3V3`. Both need tscircuit schematic placement (`schX`/`schY`), which this
  board's `.tsx` does not currently declare at all.
- next: HANDOFF at a gate boundary. The copper is finished and green; what
  remains is paperwork, a converter patch that is not mine to make, and the
  release ceremony. See STATUS.md.

## 2026-07-31 12:xx — the hole class, and why the staging archive is REMOVED again

- did: quantified the fab lens's hole-to-hole finding rather than accepting or
  waiving it, fixed it in source, and rebuilt. **The tight hole class is the RF
  LAUNCH, not the fence.** Classified over all 3500 holes (MEASURED, 4 mm
  spatial grid, independent of every repo gate): VIA<->PTH pad 54 pairs / min
  **0.3016**; VIA<->VIA 2 / 0.3785; VIA<->NPTH 1 / 0.3768; PTH<->PTH 0 /
  1.6934. 55 of the 57 sub-0.45 pairs involve a COMPONENT hole. At JLC's
  published pad-hole tolerance (+0.13 mm dia; via hole diameter not
  controlled) the worst becomes **0.2366 mm** — under the declared 0.25 floor
  on **8 of the 54**, at nominal 0.3016 x2, 0.3028, 0.3118, 0.3121 x2,
  0.3144 x2.
- did: SWEPT the remedy instead of guessing which of two tight constraints
  wins. Displacing the 8 vias radially outward from their SMA barrel, both
  margins measured at every step:

  | delta mm | min h2h at MAX MATERIAL | fence worst interior gap |
  |---|---|---|
  | 0.000 | 0.2366 **FAIL** | 1.1769 pass |
  | 0.0134 | 0.2500 edge | 1.1769 pass |
  | 0.025 | 0.2615 pass *(saturates)* | 1.1769 pass |
  | **0.035** | **0.2615 pass** | **1.1769 pass** |
  | 0.048 | 0.2615 pass | 1.1769 pass |
  | 0.0632 | 0.2615 pass | 1.1910 edge |
  | 0.070 | 0.2615 pass | 1.1968 **FAIL** (ANT1 E, ANT5 E) |

  **BOTH-PASS window: delta in [0.0134, 0.0632] mm, 49.8 um wide.** Above
  0.025 the hole metric SATURATES (the binding pair becomes an untouched one,
  via 43.000,27.000 <-> J_ANT8.3 at 0.3265/0.2615), so further displacement
  buys nothing and only spends fence margin. 0.035 is the centre of
  [0.025, 0.048] — hole gap at its achievable maximum, fence bit-for-bit
  unchanged.
- result: MEASURED after `03_src/rebuild_all.sh` (RAW EXIT 0) —
  min hole-to-hole **0.3016 -> 0.3265** nominal, **0.2366 -> 0.2615** at max
  material, pairs under the floor **8 -> 0**; `fence_pitch.py` **RAW EXIT 0,
  worst 1.1769 mm, 22 arm-sides, 0 OVER, PASS** (unchanged to four decimals);
  `fence_apertures.py` **0 GAP lines**, 3433 PCB_VIA GND + 40 PTH = 3473
  elements (its exit code is never evidence — its own header says so);
  band-free nearest-ground max over all arms **2.2142 -> 2.2142 mm**;
  DRC `--severity-all --refill-zones --schematic-parity` **0 / 0 / 0**.
- result: the floor is a GATE THAT CAN FAIL, proven with a known-bad fixture
  rather than asserted. The PRE-FIX board graded against the new 0.315 floor:
  kicad-cli reports **16 hole_to_hole findings over 8 distinct pairs**, at
  exactly 0.3016 x2, 0.3028, 0.3118, 0.3121 x2, 0.3144 x2 — the same eight, at
  the same gaps, as the independent classification found.
- did: DELETING the eight was measured too, and rejected. It gives IDENTICAL
  numbers (0.3265/0.2615, fence 1.1769) — but five of the eight are not graded
  at all (2 project beyond an arm end, 3 sit outside the +/-2.5 mm band) and two
  are graded END points, so dropping them grows ANT1 E's lead-in and ANT5 E's
  run-out from **1.520 mm (ADR-0005 GREEN)** to **2.652 mm (ADR-0005 RED)**.
  `fence_pitch.py` grades max INTERIOR gap only and would have called that
  free. That blind spot even makes DELETING a via score better than MOVING it
  0.14 mm. Moving keeps the copper and never has to rely on it. **This is the
  RF lens's RF-4 finding deciding a real design choice, and it is still open.**
- next: **`06_build/staging/` is REMOVED, deliberately, and for the SAME rule
  as 2026-07-30 22:10: a material change voids prior verdicts.** THE COPPER
  MOVED. Its gerbers describe the pre-fix board, its MANIFEST states
  `minimum hole-to-hole edge-to-edge 0.3016 mm` which is now false, and all
  four 2026-07-31 lens reviews graded copper that no longer exists. Promoting
  those four verdicts into `verification/redteam_{layout,topology}.md` as THIS
  release's verdict would be the adjacent-property error M-REV's own comment
  warns about — grading one version's review against another version's
  release. Nothing is lost: the staging tree was entirely UNTRACKED
  (`06_build/*` is gitignored, `git ls-files` returns 0), and its four review
  files are byte-identical to copies already committed in `08_reviews/`
  (verified with `cmp`). A convenience copy is in the session scratchpad and
  is NOT evidence.
- next: **OWED, and not claimed anywhere as done** — (1) a fresh lens round
  against the REBUILT board, then a re-stage; the four 2026-07-31 reviews are
  archived reviews of the pre-fix copper from here on. (2) The mixed
  via-hole-to-pad-hole class has NO published vendor rule (JLC: 0.2 mm
  via-to-via, 0.45 mm pad-to-pad, nothing between; their public Q&A #693 asks
  exactly this and is unanswered). 0.315 makes the board honour ITS OWN
  declared tier at max material — it does not settle the vendor question,
  which stays a DFM item to put to JLC in writing before the order, beside
  the ORDER_README's other human gates. (3) `p_hole_to_hole` walks PCB_VIA
  pairs ONLY and never a drilled PAD, so the repo's hole-repair pass is blind
  to the class that actually bound this board — a backend gap, declared in
  `03_src/route.yaml` beside the config it explains.

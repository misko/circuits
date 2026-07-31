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

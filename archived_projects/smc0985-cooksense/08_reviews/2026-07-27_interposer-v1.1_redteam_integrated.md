    subject: smc0985-cooksense interposer v1.1 (pre-seal staging archive
             07_releases/interposer-v1.1-2026-07-27/)
    date: 2026-07-27
    source: redteam-agent (fable-medium), zero-context adversarial
    lens: INTEGRATED — (a) topology/protection/ratings/intent AND
          (b) layout/mechanical/fab-data, in one pass
    scope-rationale: FIX-PASS release (canon "Verification scoping"): the copper
          state was fully reviewed at v1.0 by two separate lenses and is PROVEN
          geometrically unchanged, so this release gets targeted fix-confirmation
          plus ONE integrated fresh-context lens rather than the full battery.
    context-given: the staging archive + 01_docs/{BRIEF,ARCHITECTURE,
          DETAIL_DESIGN,pin_map,flex-jumper-spec,10fdz-bt-land-pattern-confirm}
          + 01_docs/decisions/ + 02_parts/ + 03_src/interposer/ +
          03_tscircuit/src/interposer.tsx + the sealed v1.0 for comparison +
          design-policies.md. EXCLUDED: journals, learnings, STATUS, 08_reviews,
          git log.
    verdict: lens (a) ORDER · lens (b) ORDER conditional on the P1 · 0 P0

# Red-team INTEGRATED lens — interposer v1.1 (verbatim)

Review complete. All measurements below are my own, taken with independent parsers (no pcbnew, no repo tooling) from the shipped bytes.

## 1. Findings table

| Sev | Finding | Evidence (file + measured number) |
|---|---|---|
| P1 (pre-seal, must close before seal) | The staging archive fails its own required-artifact gate: `release_required_check.py` exit 1 — MANIFEST.txt, ORDER_README.md, and 6 verification artifacts (pin_review, render_review, redteam_topology, redteam_layout, policy_audit, parity) absent. This matters beyond paperwork: `source/assembly.yaml` load-bears on "ORDER_README section 1/2/4" for the ZIF purchase instructions and the bring-up continuity map, and the declared-open polarity item is supposed to live in that order paperwork — which does not exist yet. | `verification/release_required.txt` ("A-EVID FAIL: 8 required artifact(s) missing"); archive file listing confirms none of the 8 exist |
| P2 | The self-supply BOM row is not fully self-describing: Comment `10FDZ-BT`, MPN cell **blank**. The exact orderable variant `10FDZ-BT(S)(LF)(SN)` lives only in `02_parts/10FDZ-BT/part.yaml`; the archive's own assembly.yaml warns the `-M` and `-ST` variants are scrap-on-arrival, yet the archive's order sheet names none of the suffixes. Mitigated if ORDER_README §2 lands with the full MPN — one more reason P1 blocks. | `fab/bom.csv` row 1: `10FDZ-BT,"J_CN1_JUMPER,J_MEMBRANE",...,,` (MPN and LCSC both empty) vs `part.yaml mpn: 10FDZ-BT(S)(LF)(SN)` |
| P2 (re-rating of a known open item, not new) | The boss-offset measurement is **understated** as "0.04 mm low". 0.04 is vs the PASS-band edge; vs the drilled nominal it is 2.54 − 2.35 = **0.19 mm**. Available radial slop: boss ø1.80 hole vs ~1.70 boss = 0.05 mm; pin ø0.90 holes vs ~0.6 pins = ~0.15 mm; combined ≈ 0.20 mm. The measured error consumes essentially the entire combined clearance — the part likely seats only with pins bearing on barrel walls. The user's build decision stands, but the paperwork should carry 0.19-vs-0.20, not 0.04. | `fab/interposer-NPTH.drl` boss x=22.46 vs `fab/interposer-PTH.drl` pin 1 x=25.00 → 2.540 drilled; user-measured 2.35 (prompt); hole/pin diameters from drl + `part.yaml` |
| P2 (info) | Absolute confirmation of CPL rotation 270 is not obtainable from the curated inputs — it rests on the measured per-LCSC table (`jlc_offset=0`, `src=lcsc` per `verification/twin_report.csv`) plus cross-board consistency (below). Canon A-POL reserves the JLC order-preview human gate for exactly this class; the missing ORDER_README is where that gate is named. | `verification/twin_report.csv`: `C2683602,J_KEY_MATRIX,OK,fit=0.01mm jlc_offset=0 db=0.0 src=lcsc` |

No P0 found.

## 2. The rotation and datum (the P0 this release exists to fix) — my numbers

- Board file: `J_KEY_MATRIX` at (15.0, 33.0) rot **−90**; pads 1..10 at x=16.85, y=27.375..38.625 (1.25 pitch), MP tabs at x=13.65, y=25.525/40.475. Pad-array bbox centre = ((13.65+16.85)/2, (25.525+40.475)/2) = **(15.25, 33.0)**. CPL says Mid X **15.25**, Mid Y **−33.0** — the datum claim is TRUE (v1.0 emitted the anchor 15.0/−33.0).
- CPL rotation 270 = KiCad −90 mod 360 with a **zero** part offset. v1.0's 90 is exactly 180 away — consistent with the declared defect (the canon records an unevidenced `^JST_GH_SM,180` name-DB rule putting eight GH connectors 180 out).
- Cross-check against the sealed main board: `cooksense-v1.4-2026-07-26` places the **same footprint, same LCSC C2683602** at rot **−90** and ships CPL rotation **270.0**, Mid X 16.25 vs anchor 16.0 — the identical (+0.25 datum, 270) convention. v1.1 interposer matches the currently-orderable sealed board exactly.
- What I cannot conclude: whether JLC's library zero for C2683602 truly makes 270 correct in absolute terms — that is only provable at the JLC order preview (single-channel human gate). I found **no evidence that 270 is wrong** and three independent consistency checks that it is right.
- Net assignment at the connector: pin 1 = KP_U1 … pin 10 = KP_D4, identical on all three connectors (below), so a correct 270 ships U1 at the GH's pin-1 end.

## 3. Topology / isolation — verified 1:1

Parsed every pad in `source/interposer.kicad_pcb` myself: J_MEMBRANE pin n, J_CN1_JUMPER pin n, and J_KEY_MATRIX pin n all carry the same net for n=1..10 (KP_U1..U6, KP_D1..D4 in order); all 20 TPs land pairwise on the right nets. **Zero zones**, 183 segments + 35 vias carrying only those ten nets, both MP tabs netless, four mounting holes NPTH netless, both bosses NPTH. DRC/ERC JSONs: 0/0/0 including the standalone-archive re-run. Ratings trivial: ZIF 50 mA/250 V and GH 1 A contacts vs µA-class matrix scan lines. Isolation claim is TRUE in the shipped bytes.

## 4. Did the copper move? — I agree, with my own comparator

I wrote my own gerber/Excellon multiset comparator (aperture-resolved, order-independent) and ran it on the two shipped `fab/interposer_gerbers.zip`:
- **IDENTICAL**: F_Cu (450 atoms), B_Cu (180), both masks (84/52), both pastes (12/0), B_Silk (26), PTH.drl (55 = 20×ø0.900 + 35×ø0.300), NPTH.drl (6 = 2×ø1.800 + 4×ø2.700).
- Edge_Cuts: 2 atoms differ, D01/D02 swapped on the same two endpoints (10.0,−10.0)/(64.0,−56.0) — one segment reversed, profile 54×46 unchanged.
- F_Silk: 40 removed / 10 added, every one inside x 44.286–44.800, y 12.009–12.909 — the version digit '0'→'1'. Nothing else on silk moved.

This independently reproduces `verification/copper_identity.txt` exactly. **The copper did not move.**

## 5. Layout / fab-data lens

- 10FDZ-BT lands, measured from the drl files: 2 rows × 10 × ø0.900 at y=−20/−46, x 25.00→47.86, pitch 2.540 constant, span 22.860; boss ø1.800 at x=22.46 on each row centreline = 2.540 outside pin 1. Matches `part.yaml` and the confirm doc's datasheet numbers (A=22.86, ø0.9, ø1.8, boss 2.54 out).
- Gerber zip: exactly the 11 files a 2-layer JLC order needs (2×Cu, 2×mask, 2×paste, 2×silk, edge, PTH+NPTH drl), all timestamped 2026-07-27 17:05, no strays, no duplicates.
- Silk (from render + gerber coordinates): "1"/"10" numerals for both ZIFs sit outside the courtyard/housing envelopes (J_MEMBRANE numerals ~1.4 mm below the courtyard edge), so they survive seating; pin 1 is additionally the RECT pad at the boss end on both rows. Refdes and the isolation caption legible.
- Mounting holes ø2.7 at (14,14)(60,14)(14,52)(60,52) on a 10..64 × 10..56 outline — 4.0 mm from each edge, symmetric.
- BOM/CPL split: CPL is a single row (J_KEY_MATRIX, C2683602, top, 270); both ZIFs are off the CPL and declared `not_assembled` with measured evidence in `source/assembly.yaml`. Coherent; the residual assembler-misread risk is the blank-MPN P2 above.
- Internal inconsistencies: none found between MANIFEST/ORDER_README and evidence — because they do not exist yet (that is the P1, reported as pending, not invented).

## 6. Verdicts

- **Lens (a) topology/protection/ratings/intent: ORDER.** Pass-through 1:1 verified, isolation true in the bytes, rotation 270 + datum 15.25 independently corroborated, subject to the already-declared JLC order-preview human gate.
- **Lens (b) layout/mechanical/fab-data: ORDER**, conditional on the P1 — the seal must not happen until MANIFEST/ORDER_README and the remaining verification artifacts exist, ORDER_README carries the full ZIF MPN and the polarity open item, and I recommend restating the boss-offset margin as 0.19 mm of ~0.20 mm clearance rather than "0.04 mm low".

# cook-loadcell — tscircuit fidelity notes (honest)

Second-opinion render of `../../04_kicad/cook_loadcell.kicad_pcb`. KiCad stays the
fab-of-record (canon S-DSL); this folder measures how close tscircuit gets.

Generated: 2026-07-19 · tsci 0.0.2112 · bun 1.3.14.

---

## Headline: node-for-node parity ACHIEVED after net-name normalization

- **Components: 29/29 electrical matched** (33/33 counting the 4 M3 mounting holes).
  Every KiCad footprint with pins is present in the tscircuit netlist with the SAME
  refdes, same pin→net mapping. The 4 mounting holes (H1–H4) are authored as
  tscircuit `<hole>` — mechanically present in the PCB/gerbers but, being
  non-electrical, they carry no refdes/net in `tsc_netlist.txt` (the only "gap", and
  it is cosmetic: KiCad also gives them no net).
- **Nets: 16/16 matched** — every KiCad named net reproduced with the exact same
  membership set (verified pad-by-pad, including the 21-pad GND star and the 8-pad
  E_PLUS star).
- **No-connects: 2/2 matched** — U1 pin6 (VBG) and pin13 (XO) are `NOT_CONNECTED`
  in tscircuit, matching KiCad's `unconnected-(U1-VBG-Pad6)` / `-(U1-XO-Pad13)`.

Node-for-node parity is **YES after normalization**, where the only normalization is
two mechanical net renames (leading digit → `N` prefix, see map below). No missing
part, no wrong net, no wrong pin.

### Net-name normalization map (KiCad → tscircuit)

| KiCad net | tscircuit net | reason |
|-----------|---------------|--------|
| `3V3`     | `N3V3`        | tscircuit `net.` selector rejects a leading digit |
| `5V`      | `N5V`         | same |
| all 14 others (GND, E_PLUS, S_PLUS, S_MINUS, BASE, AVDD_FB, RATE_SEL, SH, DAT, CLK, RING_12/23/34/41) | *identical* | preserved verbatim |

The KiCad refdes are all preserved exactly (U1, Q1, R1/R2/R7, C1–C7, D1/D2, J1–J6,
JP1, SJ1, TP1–TP7). tscircuit did **not** need its `C1_pos`-style auto-naming for
any net here because every pin was authored with an explicit `connections={{…}}` map
to a named `net.*` label, so connectivity is correct by construction.

---

## DRC-on-export (kicad-cli, `--severity-all`): 451 violations + 3 unconnected

This is the honest fidelity signal, NOT a pass/fail gate. tscircuit's auto-layout /
auto-router does not aim at this board's embedded severity-all ruleset. Breakdown:

| count | type | nature |
|------:|------|--------|
| 199 | track_width | tscircuit routes 0.15 mm; board min-width constraint is 0.20 mm. **Parametric** — a default-trace-width setting, not a connectivity error. |
| 54 + 53 | text_height / text_thickness | tscircuit silk text ~0.27–0.70 mm vs board min 0.80 mm. **Cosmetic silkscreen.** |
| 33 | lib_footprint_issues | "configuration does not include the footprint library 'tscircuit'" — one per footprint; the export references a `tscircuit:` lib absent from the running KiCad config. **Environmental**, not a board defect. |
| 19 + 19 + 19 | via_diameter / drill_out_of_range / annular_width | tscircuit vias 0.30 mm vs board min 0.50 mm. **Parametric via stackup.** |
| 22 | silk_over_copper | auto-placed silk overlapping pads. **Cosmetic.** |
| 13 | clearance | auto-router pulled a few tracks to ~0.13–0.20 mm vs 0.20 mm rule. **Real auto-route tightness**, marginal. |
| 8 | silk_overlap | overlapping refdes text. **Cosmetic.** |
| 6 | solder_mask_bridge | mask apertures bridging different nets (tight passives). **Real, mask-expansion.** |
| 3 | tracks_crossing | auto-router crossed 3 track pairs. **Real routing defect.** |
| 2 | shorting_items | on the `SH` net (shield bond / SJ1 area) — auto-router shorted SH↔GND and SH↔(anon). **Real routing defect.** |
| 1 | holes_co_located | one drilled-hole coincidence. **Minor.** |

**Interpretation.** ~430 of the 451 are parametric/cosmetic (trace width, via size,
silk sizing, the missing-lib note) — they would clear by setting tscircuit's default
trace/via/text widths to our netclass and are irrelevant to whether the *design* is
right. The ~14 genuinely-electrical items (2 shorts, 3 crossings, 6 mask bridges, 3
unconnected GND stubs) are **auto-router imperfections**, not authoring errors: the
netlist parity above proves the intended connectivity is 100% correct; the router
simply failed to realize a clean copper implementation of the SH/GND region. On the
KiCad fab-of-record that region is hand-routed and DRC-clean.

The 3 `unconnected_items` are all GND: short F.Cu stubs near C7/SJ1 the router left
dangling — same SH/GND congestion story.

---

## Footprint fidelity (pad count / pitch vs KiCad land pattern)

Measured from the tscircuit KiCad export. **Pad count matches on every part; pitch
matches on all but SJ1.**

| refdes | KiCad footprint | tscircuit footprint | pads | pitch | verdict |
|--------|-----------------|---------------------|-----:|-------|---------|
| C1/C4/C6 | C_0805_2012Metric | 0805 | 2 | 1.825 mm | match |
| C2/C3/C5/C7 | C_0603_1608Metric | 0603 | 2 | 1.650 mm | match |
| R1/R2/R7 | R_0603_1608Metric | res0603 | 2 | 1.650 mm | match |
| D1/D2 | D_SOD-323 | diode_sod323 | 2 | 2.100 mm | count/pitch OK; copper IoU 0.47 vs JLC C5158048 (pad size/shape differs) |
| Q1 | SOT-23 | sot23 | 3 | 2.465 mm | match |
| U1 | SOIC-16_3.9x9.9_P1.27 | soic16_p1.27mm | 16 | **1.270 mm** | pitch/count exact; copper IoU 0.70 vs JLC C43656 (pad length differs) |
| J1–J4 | JST_XH_B3B_1x03_P2.50_Vert | pinrow3_p2.5mm | 3 | 2.500 mm | pitch/count/THT match; tscircuit lacks the JST shroud/keying silk + exact pad drill |
| J5/J6 | JST_XH_B5B_1x05_P2.50_Vert | pinrow5_p2.5mm | 5 | 2.500 mm | as J1–J4 |
| JP1 | PinHeader_1x03_P2.54 | pinrow3 | 3 | 2.540 mm | match |
| SJ1 | SolderJumper-2_P1.3mm_Open | solderjumper2_bridged12 | 2 | **2.540 mm** | **APPROX**: KiCad is 1.3 mm-pitch *open* (DNP); tscircuit is 2.54 mm *bridged*. Wrong pitch + bridged-vs-open. Low impact (SJ1 is DNP), but the only real footprint miss. |
| TP1–TP7 | TestPoint_Pad_D1.5mm | test_point_smtpad_circle_d1.5 | 1 | — | match |
| H1–H4 | MountingHole_3.2mm_M3 | hole_circle_holeDiameter3.2mm | (hole) | Ø3.2 mm | match; no copper annulus/refdes |

Build-time warnings flagged the two supplier-footprint IoU deltas (U1 0.70, D 0.47):
tscircuit's *generic* land pattern differs from the *exact* JLC part footprint. This
is exactly why the folder-format doc says tscircuit renders are **not order-ready** —
the JLC-CAD `jlc_twin` gate is KiCad-side only. Pad count + pitch are right, so
connectivity/assembly intent is preserved; the precise copper is not JLC-twinned here.

---

## BOM / parts-engine

`fab/gerbers.zip:bom.csv` carries the JLC codes I supplied from `02_parts/*/part.yaml`:
U1→C43656, Q1→C8542, D1/D2→C5158048, J1–J4→C144394, J5/J6→C157991. tscircuit's own
parts engine *additionally* auto-resolved the passives (which have no part.yaml):
R1→C4184, R2→C25981, R7→C22775, 100n→C14663, 10µ→C15850. Those five are **tscircuit
guesses, not vetted** — the KiCad BOM/`jlc_twin` remains authoritative for passives.

## `verification/parity.md` caveat

The auto-generated `parity.md` prints "~63 components" — that is the generator's
regex over-counting (it also matches the `COMPONENT_PINS:` section). The real,
manually-verified figure is 29 electrical components (+4 holes) = **33/33**, and it
reads "~16 nets" which is correct (16/16). Trust this notes.md over the regex counts.

---

## Authoring friction worth recording for the next board

1. **`connections={{…}}` per element is the right idiom.** Mapping every pin to a
   `net.NAME` label gives node-for-node parity by construction and completely avoids
   tscircuit's `C1_pos` auto-net-naming. Far cleaner than pairwise `<trace>`.
2. **Leading-digit net names break the `net.` selector** — `3V3`/`5V` had to become
   `N3V3`/`N5V`. Budget a rename map for any power-rail-named net.
3. **`<hole>` elements default to (0,0) and stack** → "pcb_hole overlaps" placement
   errors that *silently disable the autorouter for the whole board*. Give every
   `<hole>` explicit `pcbX/pcbY`. This was the one non-obvious gotcha.
4. **Footprinter covers the commodity library well** (0603/0805/sot23/sod323/
   soic16_p1.27mm/pinrowN_p2.5mm/testpoint) but has **no JST-XH shroud and no
   1.3 mm open solder-jumper** — SJ1 is the only part that couldn't be matched on
   pitch. A board heavy in specialty connectors will need `<footprint>` children.
5. **Supplier-footprint IoU warnings are informational**, not fatal — the build still
   emits circuit.json + all exports. They correctly flag that tscircuit's generic
   land != the exact JLC part; treat as a to-twin list, not an error.
6. Trace `is missing a name` and pin `underspecified` warnings are pure noise for a
   parity render; ignore them.

## Verdict

For a ~33-part board, tscircuit reproduced the **schematic/netlist perfectly** —
100% node-for-node after a 2-net cosmetic rename — and got **footprint land patterns
right on 32/33 parts** (SJ1 pitch/bridged the sole miss). Where it falls short is
purely the **physical implementation**: default trace/via/text geometry that misses
our severity-all ruleset, plus a handful of auto-router shorts/crossings in the
congested SH/GND corner. As an *authoring front-end* for capturing this design,
tscircuit is credible; as a *fab source* it is not — the copper is neither
netclass-compliant nor JLC-twinned. Exactly the "serious second opinion, never a fab
source" positioning the folder format claims.


---

## Phase-2 update (2026-07-19) — OUR converter is the bridge

The schematic bridge is now `scripts/circuit_json_to_kicad_sch.py` (ADR-0001 Phase 2),
run by `gen_tscircuit.sh` on `build/circuit.json` to produce the AUTHORITATIVE
`kicad/cook_loadcell.kicad_sch` (unique `elt:SYM_<refdes>` symbol per component, pins
keyed to KiCad pad names, one global-label net-glue per pin, GND as power symbols +
one PWR_FLAG, annotated). Gate result: **`kicad-cli sch erc --severity-all` = 0 errors**
(51 warnings, all the parametric `lib_symbol_issues` "lib 'elt' not in config" note)
and **node-for-node netlist parity 0** vs the sealed board — 16/16 nets, 75/75 nodes,
2/2 no-connects (U1 VBG/XO). Only the documented leading-digit net renames
(`N3V3`→`3V3`, `N5V`→`5V`) are normalized. See `parity_converter.md` / `erc_converter.rpt`.
tscircuit's native export is kept as `kicad/cook_loadcell.native.kicad_sch` for reference.

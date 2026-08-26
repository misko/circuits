# ORDER README — crow-recorder-central-v2 (8-channel CENTRAL recorder) v1.5

Central hub of the CROW ACOUSTIC LOCALIZATION ARRAY: 8 remote mic pods home-run
over custom-pinout Cat5e into 8 RJ45 ports (J3–J10), 2x PCM1865 4-ch ADCs
(U2/U3), XU316-1024 USB-Audio SoC (U1) to a USB-C host port (J2), shared-clock
topology (ADR-0004), beeper calibration bus, 5V brick input (GST25A05, J1) with
AO3401A reverse-polarity FET (Q1) + SMAJ5.0A (D1) + 2A fuse (F_IN).
Release **v1.5-2026-07-25**. Board **170.1 × 120.1 mm, 6 layer**.

## ⛔ v1.5 SUPERSEDES v1.4 — v1.4 IS DO-NOT-ORDER FOR PCBA

**v1.4's `fab/cpl.csv` places J2, the board's only USB-C connector, 1.3025 mm
off its own pads.** The contacts are 1.150 mm long, so the overlap is
**0.000 mm** — not a marginal joint, no joint at all — and the four shell posts
miss their holes, so the part cannot physically seat. A board built from v1.4
has no USB power and no USB data, which on this design is the entire host link.
v1.4's rotations are CORRECT and are carried forward unchanged; its bare PCB is
fine and byte-identical to this release's.

**Root cause: the CPL was emitting the wrong DATUM.** JLC places a part so that
*its own* origin lands on `Mid X/Y`, and that origin is the **centre of the
bounding box of the pad centres**. The exporter emitted KiCad's **footprint
anchor** instead — an authoring convenience with no fab meaning. The two
coincide for most parts, which is why this survived the fleet's entire history
undetected; they diverge on CONNECTORS, where the anchor conventionally sits on
pin 1 or a mounting feature.

The datum was MEASURED, not assumed: over **228 cached JLC-native footprints
across six boards**, the model origin sits on its own pad-centre bbox to
≤0.01 mm in **227 cases (99.6 %)**. Two weaker readings were tested on the same
228 and REFUTED — bbox of pad *outlines* 213/228, *centroid* of pad centres
198/228. Both fail on exactly the connectors that matter, and the outline
reading would have left J2 0.1625 mm out.

| ref | LCSC | what | v1.4 `Mid X, Mid Y` | **v1.5** | why |
|---|---|---|---|---|---|
| J2 | C3020560 | USB-C receptacle | 90.0, **−126.0** | 90.0, **−124.698** | anchor → pad-array datum (1.3025 mm) |
| J1 | C381116 | DC barrel jack | 24.0, −102.0 | **row removed** | true THT on an SMT-only order |
| R_inj1 | C11702 | 1 kΩ 0402 | 94.5, −46.0 | **row removed** | permanent ch1↔ch5 bridge |
| R_inj2 | C11702 | 1 kΩ 0402 | 98.5, −49.0 | **row removed** | permanent ch1↔ch5 bridge |

CPL goes 177 → **174** rows. **No rotation changes** — that is asserted
mechanically, not eyeballed: `release_freshness_check.py --cpl-only-supersede`
FAILs on any Rotation/Layer/Val/Package change or any added row.

**Everything else is byte-identical to v1.4** — the gerber zip, both drills,
`fab/bom.csv`, all 3 PDFs, the STEP and all 12 `source/` files. `fab/cpl.csv`
is the ONLY file that differs. Copper identity is proven by RE-PLOT from the
unchanged board (`verification/replot_identity.txt`): all 15 gerber/drill
members hash identically once the plot's own timestamp comments are stripped.

### The two removed rows are DEFECT REMOVALS, not deferrals

- **J1** is a true through-hole part: 3 plated pads with **F.Paste on none of
  them**, on an order that buys `service: standard`, `sides: [top]` — SMT only.
  No reflow process can solder it. v1.4 had it on the CPL while its own
  `assembly.yaml` asserted in writing that "the only other THT parts are already
  off the CPL". J1 is the board's **only power inlet**, so it now leads the
  hand-solder list in section 3 and the section-3a checklist names it. (J2 also
  has 4 drilled pads but carries F.Paste on all four — legitimate pin-in-paste
  intrusive reflow — so J2 correctly stays on the CPL.)
- **R_inj1/R_inj2** are 1 kΩ each between ADC1P↔INJ and ADC5P↔INJ. `JP_INJ` is
  unstuffed by design, so net INJ floats and its only conducting path ties
  channel 1 to channel 5 through **2 kΩ** — on a board whose product IS
  inter-channel isolation. Against the ~99 Ω pod source impedance that is
  20·log10(99/2099) = **−26.5 dB** of ch1→ch5 crosstalk against a 110 dB spec.
  Unstuffing them costs nothing (the injection feature already needs JP_INJ
  fitted by hand); leaving them meant desoldering two 0402s on all 5 boards.

Both are declared in `03_src/rules/assembly.yaml`. The sealed board still lacks
their `exclude_from_pos_files` attribute — deliberately, because setting it
requires regenerating the board, which churns every UUID (measured: 81626 diff
lines on a semantically identical rebuild) and would turn a data-only CPL fix
into a full respin. The exporter therefore honours the declaration directly, and
`board_attr_plan:` carries the dated defer; `03_src/floorplan.yaml` already
carries the patterns so the next regeneration emits them.

---

## 0. ⚠️⚠️ CRITICAL DEPLOYMENT CONSTRAINT — PORTS ARE NOT ETHERNET ⚠️⚠️

**All 8 RJ45 ports (J3–J10) carry a CUSTOM 5 V AUDIO/POWER pinout
(1,2 = AUDIO±; 3,6 = +5V_BEEP/RETURN; 4,7 = +5V_AUDIO; 5,8 = GND). NEVER plug
any port into an Ethernet switch, router, or ANY PoE source.**

WHY (accepted-risk sign-off, ADR-0007, carrying the pod-v2 ADR-0005 user
waiver). **BOTH 802.3 alternatives land somewhere destructive — there is no
"safe" pair on this connector:**

- **Alternative B (4/5 = +, 7/8 = −):** ~48 V through the per-port PTC straight
  into the shared **5 V rail** (4,7 = +5V_AUDIO; 5,8 = GND) — above the AP61102
  buck vin_abs_max (6.5 V) and above every 5 V-rated part on the board.
- **Alternative A (1/2 = one polarity, 3/6 = the other)** — the more common
  endspan mode: ~48 V onto **AUDIO± (1,2)**, which feed the PCM1865 analog
  inputs through the per-port 100 Ω series resistors and TPD2E2U06 ESD diodes,
  and onto the **beeper pair (3,6 = +5V_BEEP / BEEP_RETURN)**, which are per-port
  **UNFUSED**. That path bypasses the input PTC entirely and reaches the ADC
  front end, so it is if anything the worse of the two.

The input TVS (D1) sits on VIN_RAW, the wrong side of Q1 to clamp any rail-side
injection, and the per-port ESD parts are ESD-rated, not 48 V clamps. There is
deliberately NO per-port OVP this rev. Mitigations are administrative: per-port
**"NOT ETH 5V!"** silk at every jack + the banner, custom-crimped cables only,
closed owner-cabled deployment. The beeper legs (3,6) are also per-port
UNFUSED — a beeper-pin short opens F_IN (2 A) = whole-board outage (ADR-0007;
v-next: F_BEEP PTC + shared SMBJ5.0A on the P5VA spine).

**Deployment scope: controlled engineering bench, owner-built cables,
restricted physical access ONLY.** Shared lab / rack / field / anywhere
ordinary patch cables are present: no-go until the v-next protection rev.

---

## 1. JLCPCB order options

| Setting | Value |
|---|---|
| Layers | **6** |
| Dimensions | **170.1 × 120.1 mm** |
| **Stackup** | **JLC06161H-3313** (1.6 mm) — REQUIRED, the USB 90 Ω geometry is solved for THIS stackup (prepreg 3313 h=0.0994 mm Er=4.1 under L1; verification/usb90_solve.md). Do not accept a substitute stackup without re-solving. |
| Via/process tier | **`jlc_6layer_smallvia`** (ADR-0002) — 0.30/0.15 mm via-in-pad; **ADVANCED small-via option REQUIRED** or JLC rejects the drill set |
| **Via-in-pad process** | **Epoxy-filled AND capped (plated-over) vias REQUIRED** — see §1a. Select the filled & capped via option; if the order UI does not expose it, note it for engineering review. |
| Impedance control | Not purchased as a JLC option; carried instead by the stackup-specific 90 Ω calc (verification/usb90_solve.md) + the REQUIRED USB-HS first-article gate (§4a). Ordering JLC's controlled-impedance service on the same stackup is an acceptable upgrade. |
| Surface finish | ENIG preferred (0.4 mm-pitch TQFP-128 + USON paste release; flat pads under the capped EP vias) |
| **Assembly service** | **Standard** (declared in `03_src/rules/assembly.yaml`). Not "economic": this order carries a CONSIGNED line (U1) and a 0.4 mm-pitch TQFP-128 with a pasted exposed pad. |
| **Assembly sides** | **Top only.** Measured from the shipped CPL: 174 placements, all top, 0 bottom. |
| **Build quantity** | **5 boards.** The stock evidence in `verification/stock_check.json` is graded against 5× each line's per-board quantity. |
| **Fiducials** | **None on the board** — deliberate, and a recorded limitation. JLC's own panel-rail fiducials carry the order; LOCAL fiducials beside U1 (0.4 mm pitch) were not placed and cannot be added to a sealed board. Carried as a v-next layout item (§6). |

Upload set (in `fab/`):
- **PCB order:** `crow_recorder_central_v2_gerbers.zip` (6 copper layers, F/B
  mask+paste+silk, Edge_Cuts, PTH+NPTH drills). BOM/CPL are **not** in the zip.
- **Assembly BOM:** `fab/bom.csv` — `Comment,Designator,Footprint,MPN,LCSC`
  (byte-identical to v1.3 and v1.2; 49 lines, 47 coded, 2 deliberately uncoded
  — see §3).
- **Assembly CPL:** `fab/cpl.csv` — **174 placements.** One coordinate moved
  since v1.4 (J2, the USB-C, onto its pad-array datum) and three rows were
  removed (J1, R_inj1, R_inj2). **No rotation changed** — v1.4's rotations are
  carried forward verbatim and that is asserted mechanically, not eyeballed

Re-run a same-day stock check before paying. Measured 2026-07-25 at build
quantity 5: every coded, placed line clears 5× its per-board quantity EXCEPT
`C6938291` (the XU316) at stock **0** — which is exactly why that part is
CONSIGNED and why JLC stock is irrelevant for it (§2, and the `sourcing_plan:`
entry in `03_src/rules/assembly.yaml`). Watch-list at order day: `C5224055`
(stock 383, need 10), `C882626` (stock 496, need 5).

## 1a. ⚠ FAB NOTE — U1 exposed-pad via-in-pad (INCLUDE WITH ORDER)

U1 (XU316-1024, TQFP-128 with 4.7 × 4.7 mm exposed pad, board center-north at
(90, 102) mm, top side) has **sixteen 0.30/0.15 mm thermal vias in a 4×4 grid
(±0.55 / ±1.65 mm from the EP center) directly under its pasted exposed pad.**
They are REAL VIAS — the PTH drill file emits them under the **ViaDrill** tool
(T1, 0.150 mm) together with the board's other vias; there is **no 0.15 mm
ComponentDrill tool** in the file.

**Ordered process for these (and all) vias: epoxy-fill + cap (plate over,
IPC-4761 Type VII).** The board file ships with `capping yes` / `filling yes`.
Rationale: open or merely tented holes under a pasted EP wick solder during
reflow → voided/starved thermal joint, solder balls on the bottom side, and
possible assembler rejection of the consigned U1. U1 is an expensive,
out-of-stock, consigned part — treat this note as blocking:

1. **Inspect the production files** (JLC's engineering-review gerber/drill
   render) BEFORE approving: confirm the 16 holes under U1's EP are treated
   as filled+capped vias, not open component holes.
2. If JLC engineering questions the construction, the answer is: "16× 0.3/0.15
   thermal vias in-pad under U1's exposed pad; epoxy fill + cap/plate-over
   required; paste layer is windowed (9 openings, ~68% coverage) per the
   footprint."
3. **First article: X-ray (or equivalent) the U1 exposed-pad joint** before
   accepting the batch (§4a).

## 2. Sourcing swaps + the consignment line

| Ref(s) | Ordered part | Why |
|---|---|---|
| U9 | **TLV70018DDCR (C79924)** | TCR2LF18 (C150173) stock 0; ADR-0006 documented pin-compatible drop-in |
| Y1 | **NX3225SA-24MHZ-EXS00A-CS08583 (C2762192)** | FA-238 MD50Y stock 0; same 3225-4P, same CL 9 pF (02_parts note) |
| R_fb2b | **402 kΩ (C25785)** | 400 k not stocked; −0.17 % on the 0V9 setpoint, inside tolerance |
| FB_BEEP, FB_u33, FB_u18, L_pll | **BLM21SP601SN1D (C3716677)** | first pick BLM21PG600SN1D is a **60 Ω** part — wrong-part caught at M-BOM staging (v1.0) |
| CL1, CL2 | **12 pF C0G (C1547)** | v1.0 fresh-lens P1 fix, carried |
| Cout_U10 | **2.2 µF 25 V X5R (C72203)** | v1.0 fresh-lens P1 fix, carried |
| RG1, R_cs, R_rst | **10 kΩ 1 % 0402 (C60490)** | basic C25744 stock 0; extended equivalent pinned at source |
| R_scl, R_sda | **4.7 kΩ 1 % 0402 (C105871)** | basic C25900 stock 0; extended equivalent pinned at source + vetted in the passives ledger |

### U1 is CONSIGNED — which means POPULATED

**We supply the part; JLC PLACES it.** U1 stays ON the CPL (data row 164, 270°) and
is on the BOM (C6938291). It is **not** in the not-assembled set, and any
paperwork that says otherwise is wrong: consignment is a SOURCING class, not a
population class. (v1.3's manifest made exactly that mistake — it listed the
placed U1 under `not_assembled:`.)

- JLC stock for C6938291 measured **0 on 2026-07-25**, and 0 at every check
  since 2026-07-23 (ADR-0003) — chronic, not transient. Source from global
  distribution (Digi-Key / Mouser) and consign.
- Record the consignment MPN + lot with the order.
- MSL-3 handling is OUR responsibility for a consigned part — §3b, mandatory.

## 3. Population set — who is placed, and who is not

Generated from `03_src/rules/assembly.yaml` (the ONE machine-readable home;
gated by `assembly_coverage.py`, evidence in `verification/assembly_coverage.txt`).
Board = 203 footprints. **Placed = 174** (all top). Unpopulated = 29.

| Ref(s) | Class | Reason | What happens |
|---|---|---|---|
| **U1** | **CONSIGNED — PLACED** | we ship it, JLC places it | on the CPL at 270°; §2, §3a, §3b |
| **J1** | **not assembled (NEW at v1.5)** | `process_incompatible` | **hand-soldered THT — this is the board's ONLY power inlet** |
| J3–J10 | not assembled | `not_in_catalog` | hand-soldered THT at integration |
| JP_INJ, J_DBG | not assembled | `dnp_by_design` | left unstuffed; hand-fit at the bench only if needed |
| **R_inj1, R_inj2** | **not assembled (NEW at v1.5)** | `dnp_by_design` | left unstuffed — they bridge ADC ch1↔ch5 through 2 kΩ |
| H1–H4 | exempt (`H`) | mounting holes, no part | n/a |
| TP1–TP12 | exempt (`TP`) | bare probe pads, no part | n/a |

**J1 (DC-005 barrel jack) — `process_incompatible`, NEW at v1.5.** Not a
sourcing wall: C381116 is coded, stocked and still on `fab/bom.csv`. It is a
PROCESS wall — 3 plated through-holes with F.Paste on none of them, on an order
that buys top-side SMT only. JLC would have re-quoted it as an unbudgeted
hand-solder line or dropped it silently, and under v1.4 no checklist named it.
**Hand-solder it first at integration: nothing else on the board powers up
without it.** Observe polarity — J1.1 is the centre pin (JACK_IN), J1.2 the
sleeve (GND), per the DC-005 drawing in `02_parts/`.

> `R_inj1`/`R_inj2` remain on the `1kΩ` BOM line (shared with `R_bg1`, which IS
> placed), exactly as J3–J10 remain on theirs. JLC sources 3 and places 1; the
> CPL is the population truth. Do not "fix" this at the order form.

**J3–J10 (RJHSE-5384) — `not_in_catalog`, and this is a measured wall, not a
style.** JLC parts-library query 2026-07-25 for "RJHSE-5384" returns
C9900035627 (the code on our BOM, stock 0) and C9900056698 (stock 0) — both
C99* consign-only codes with no EasyEDA CAD, i.e. no assembly line JLC can run.
The nearest STOCKED Amphenol jack, C464587 (RJHSE5384, stock 658), was measured
2026-07-23 as **not a land drop-in** for our RJHSE538X footprint (pad 1↔13 ours
3.67 mm vs theirs 11.74 mm). Do not substitute it at the order form. Confirm
J3–J10 are ABSENT from the automated placement in the JLC preview.

> **Expect JLC to flag `C9900035627` as unavailable (stock 0) on the BOM.**
> That is the correct and expected state, not a problem to solve: those 8 lines
> are deliberately NOT placed and carry no CPL row. Do not let the quote flow
> talk you into substituting `C464587` — it does not fit the land. If the order
> form will not accept a zero-stock line at all, remove the `C9900035627` row
> from the uploaded BOM; the CPL is unaffected either way, and the jacks are
> hand-soldered at integration.

**JP_INJ + J_DBG — `dnp_by_design`, NOT a sourcing wall.** v1.3's paperwork
called these "uncoded, hand-solder", which reads as scarcity; it is not.
JLC stocks 2.54 mm THT headers (query 2026-07-25: C2337 1×40 straight pin,
stock 86244; C52016391 1×03, stock 29861). These two footprints are
deliberately unstuffed: JP_INJ (1×03 beep-injector strap) and J_DBG (1×08 1V8
JTAG) are bring-up aids on a top-side-only SMT order. Their BOM lines carry a
blank LCSC and their board footprints carry `exclude_from_pos_files`, so nothing
on the order form contradicts this. Fit a header by hand at the bench if debug
or beep injection is wanted.

## 3a. Assembly-closure checklist (archive at order time)

- Annotated screenshot(s) of the approved JLC placement preview.
- 🔴 **CHECK POSITION, NOT ONLY ROTATION — this is what v1.4 shipped wrong.**
  v1.4 passed every rotation check it had and still put J2 1.3025 mm off its
  pads, because no gate and no checklist item had ever compared a CPL
  *coordinate* to anything. **For J2 specifically, confirm in the preview that
  the connector body sits ON its pads** — the 16 contacts inside the land row,
  and the four shell posts over their four holes, not offset toward the board
  edge. A-POS now grades this mechanically (worst residual on this release:
  **0.00050 mm** across all 174 rows, tolerance 0.05 mm —
  `verification/assembly_coverage.txt`), but the preview is the independent eye.
- 🔴 **MANDATORY U1 ROTATION GATE — BLOCKING before ANY PCBA order.** v1.4's
  CPL sets U1 (XU316, TQFP-128, consigned) to **270°**, restoring the value
  v1.0/v1.1/v1.2 shipped. A symmetric-package 180° error is INVISIBLE to a pad
  fit, so this ONE part must be confirmed by a human against JLC's placement
  preview: **the package's pin-1 dot / bevelled dot-corner must sit at the
  board pin-1 marker (U1 pad 1, NW corner of the EP field at ≈(90, 102) mm,
  top side).** If the preview shows the dot 180° opposite, STOP and escalate —
  do not approve. Archive the annotated preview screenshot for U1.
- Pin-1/polarity confirmation for **every** per-LCSC row — all ten report `OK`
  with `src=lcsc` in `verification/twin_report.txt`, and all ten were re-derived
  independently in `verification/rotation_remeasure.txt`:
  **U1, U2, U3, U5, U7, U8, D_USB (270°)** and **Q1, Q2, U9 (180°)**. Verify
  each in the preview; do not blind-apply (per-reel deviations exist).
- 🔴 **J2 (USB-C, C3020560) MUST also be eyeballed in the preview**, for the
  same reason U1 must. Our vendored footprint numbers its pads 1..17 while
  JLC's names the same pads A1–A12/B1–B12, so **zero pad names are shared and
  a pad-NUMBER fit is actively misleading here** — it pairs our signal pads
  1–4 against JLC's four shell posts and confidently returns 90°.
  **0° is nonetheless correct, and is now MEASURED on a numbering-free
  channel:** matching the shell posts by pad SIZE CLASS, the 2.1 mm-long and
  1.8 mm-long post pairs both give dy = −1.2950 mm at 0° — self-consistent to
  **0.0000 mm** — while 180° demands −4.915 and +3.445 from the same two
  classes, an **8.36 mm self-contradiction**; 90°/270° are excluded outright by
  the 8.64 mm post span. Because the numbered and numbering-free channels
  DISAGREE on this part, it is carried on the machine-enforced order-preview
  gate. Confirm the connector mouth sits over the north board edge and pin A1
  is where the board expects it.
- After U1 and J2, the row most worth a second look is **Q1** — a 3-pad SOT-23
  whose fit separation (9×, rms 0.2003) is the weakest in the table, simply
  because three pads carry the least information.
- Confirm **J1**, J3–J10, JP_INJ, J_DBG, **R_inj1 and R_inj2** are absent from
  the automated placement. J1 and the two R_inj resistors are NEW absences at
  v1.5 — under v1.4 all three were placed, and J1 (the only power inlet) was
  named in no checklist at all.
- The exact U1 consignment MPN + lot; final supplier + MPN for every
  manually-sourced line. Note that `fab/bom.csv`'s MPN column is blank on all
  49 rows (JLC sources from the LCSC column) — take the MPNs from `02_parts/`
  or from §2 above, not from the BOM.
- JLC's confirmation (or production-file evidence) of the §1a filled+capped
  EP via construction.

## 3b. ⚠ MSL-3 handling — consigned U1 (XU316, TQFP-128) — SHIP WITH THE ORDER

**Source: XMOS XU316-1024-TQ128 xcore.ai datasheet XM-014532-PC v2.0.0, §14.5
"Moisture Sensitivity", p.33** (read from the archived PDF in
`02_parts/XU316-1024-TQ128-I24/`, sha256 recorded in part.yaml): *"All XMOS
devices are Moisture Sensitivity Level (MSL) 3 — devices have a shelf life of
168 hours between removal from the packaging and reflow, provided they are
stored below 30 °C and 60 % RH. If devices have exceeded these values or an
included moisture indicator card shows excessive levels of moisture, then the
parts should be baked as appropriate before use"* (per J-STD-033D). Reflow
profile per J-STD-020 (§14.6).

Because U1 is **consigned** (supplied by us, not JLC's reel), moisture control
is OUR responsibility, not the assembler's. A 0.4 mm-pitch TQFP with a large
exposed pad traps moisture under the EP; it flashes to steam at reflow and
pops/delaminates the package. Before handing U1 to the line:

1. **Receive & store dry:** accept only sealed dry-pack (vacuum bag + desiccant
   + Humidity Indicator Card). Keep sealed until the assembler needs it.
2. **HIC check at bag-open:** read the humidity-indicator card the moment the
   bag is opened; if the indicated spot is over the MSL-3 threshold, the parts
   are compromised — bake before use (step 5).
3. **Timestamp the bag-open** and hand JLC the open time in writing.
4. **Track floor life:** MSL-3 allows **≤ 168 h** total exposure at **< 30 °C /
   60 % RH** between bag-open and reflow. Log cumulative out-of-bag time; if the
   window is blown before reflow, bake.
5. **Bake authorization:** if floor life is exceeded or the HIC failed,
   **authorize a bake** (125 °C, duration per J-STD-033D for the body
   thickness) BEFORE reflow. Record the bake in the assembly-closure package.

**Put these five steps in writing to the assembler with the consignment.** An
MSL-3 pop on a chronically-out-of-stock consigned SoC scraps the board.

## 3c. ⚠ Beeper aggregate load vs the 2 A input fuse

The calibration beeper bus drives all 8 ports (3,6 = +5V_BEEP/RETURN). Each
port's beeper draws on the order of **~150 mA**, so an **all-8-ports
calibration event pulls ~8 × 150 mA ≈ 1.2 A** through the shared 5 V spine —
against the **2 A input fuse (F_IN)**. That is ~60 % of the fuse rating from the
beepers ALONE, before the XU316 + two bucks + ADC loads on the same rail.
**Fire beepers sequentially or in small groups during calibration; a
simultaneous all-8 pulse (plus a transient inrush) runs close to F_IN and can
nuisance-trip or open the fuse = whole-board outage** (the beeper legs are also
per-port UNFUSED — §0). The durable fix is the F_BEEP PTC + spine SMBJ5.0A in
the next rev (§6).

## 3d. 🔴 BLOCKING REWORK — AP61102 C3 feedforward caps (2x 33 pF, ALL boards)

**This is a REQUIRED rework, not an optional improvement. Do it before the
first-article gates in 4a, on every board.** It needs no copper change.

**What is missing.** Both bucks are AP61102 (U7 = 3V3, U8 = 0V9). The
datasheet (`02_parts/AP61102Z6-7/DS42004_Rev6-2.pdf`, Table 1, read from the
archived PDF) gives a C3 feedforward capacitor across the top feedback resistor
of **33 pF at EVERY output voltage** in the AP61102 column, where the AP61100
column says OPEN. That split is not stylistic: pin 6 is OUT on the AP61100 and
**PG on the AP61102**, and the pin-description text reads *"OUT pin is also
allow for no connect, then C3 must be install as in Figure 2"*. The AP61102 has
no OUT pin at all, so it is **permanently in the Figure-2 case** and C3 is
mandatory. Measured on the sealed netlist: nets `FB1` and `FB2` each have
exactly **3 nodes** — the IC pin and the two divider resistors. There is no C3
on either rail.

**Why it matters.** The AP61102 is a constant-on-time regulator: per the
datasheet, *"the off-time expires when the feedback voltage decreases below the
reference voltage"*. The comparator is driven directly by ripple AT THE FB PIN,
and without C3 the divider attenuates it:

| rail | divider | FB ripple WITHOUT C3 | WITH C3 | ripple lost |
|---|---|---|---|---|
| **3V3** (U7) | 200 k / 44.2 k | **0.34–0.66 mV** | 1.9–3.6 mV | **5.52×** |
| 0V9 (U8) | 200 k / 402 k | 0.83–1.29 mV | 1.24–1.94 mV | 1.50× |

(Vin 5 V, L 1 µH, fsw 2.2 MHz, ESR 2 mΩ; range spans nominal vs DC-bias-derated
Cout. Xc(33 pF)@2.2 MHz = 2192 Ω against R2, so C3 restores FB ripple to
essentially the full output ripple.) **Only the 3V3 rail is meaningfully
starved.** A COT comparator starved of ripple pulse-bunches and can run
subharmonically, putting low-frequency content in the audio band — on the rail
that feeds DVDD and IOVDD of BOTH PCM1865 ADCs. 0V9 loses only 1.50× and is not
a concern.

**The rework.** One **33 pF 0402 C0G** piggybacked across each existing top
feedback resistor — solder it directly onto the two terminals of the 0402
already on the board:

| add | across | which is | rail |
|---|---|---|---|
| 33 pF 0402 | **R_fb1a** (200 kΩ) | Vout→FB, 3V3 divider | 3V3 — **do this one first, it is the exposed rail** |
| 33 pF 0402 | **R_fb2a** (200 kΩ) | Vout→FB, 0V9 divider | 0V9 |

No copper change is needed, which is exactly why this is a rework and not a
respin: the pads already exist as the resistor's own terminals. Both parts land
in the v2 copper revision (§6).

**Verify it worked** — see the scope gate in §4a.

## 4. First-power ritual (when boards arrive)

1. **Before any power:** multimeter every RJ45 port against the silk legend
   (1,2 = AUDIO±; 3,6 = +5VBEEP/RTN; 4,7 = +5VAUD; 5,8 = GND) and pad-1 →
   contact-1 continuity on one port.
2. Confirm D1 band → VIN_RAW, Q1 orientation (drain = VIN_RAW — CORRECT
   as-built; do not "fix"), J1 center = +.
3. **Confirm the §3d C3 rework is fitted on this board** (33 pF across R_fb1a
   AND R_fb2a) before powering the ADCs. Boards may be brought up without it
   only to characterise the defect deliberately.
4. Power from the GST25A05 brick only. Verify 5 V, then 3V3 → PG_3V3 → 0V9
   sequencing (ADR-0005), 3V3A, 1V8.
5. Enumerate USB-Audio on the host; verify per-port pod power (4/7 vs 5/8
   = 5 V) on all 8 ports before connecting pods.

## 4a. REQUIRED first-article gates (blocking before further units)

- 🔴 **3V3 buck ripple / COT-stability scope gate (validates the §3d rework).**
  With the 33 pF fitted across R_fb1a, scope 3V3 at the output cap, AC-coupled,
  20 MHz BW-limit, at idle AND under sustained 8-channel streaming:
  - **switching ripple must be a clean 2.2 MHz** (period ≈455 ns) with no
    pulse-bunching, no period-doubling and no low-frequency envelope;
  - **no sub-100 kHz content above the switching ripple amplitude** — that
    envelope is the subharmonic signature this rework exists to remove, and it
    lands directly in the audio band;
  - expected ripple ≈2–4 mV pk-pk. Capture 0V9 alongside for reference (it is
    far less exposed: 1.50× vs 5.52×).
  If a low-frequency envelope is present WITH the caps fitted, stop and
  escalate — do not ship. **Also capture one board BEFORE the rework** if
  possible: the before/after pair is the falsifiable evidence that the rework
  did what §3d claims, rather than a claim that it did.
- **THD+N sweep on at least ch1 and ch5** (the two channels whose R_inj
  resistors are unstuffed at v1.5) plus one untouched channel, to confirm the
  3V3 rail is not injecting audio-band content.
- **Inter-channel isolation spot-check ch1 ↔ ch5.** With R_inj1/R_inj2
  unstuffed these should now meet spec; under v1.4 they were bridged through
  2 kΩ (≈ −26.5 dB). Drive ch1 at full scale, measure ch5. Anything near
  −26 dB means the resistors were populated anyway — check the boards against
  the CPL.
- **U1 EP joint:** X-ray or equivalent inspection of the exposed-pad solder
  joint (voiding, wicking into the 16 capped vias, reverse-side solder).
- **USB High-Speed validation matrix:** enumerate + sustained transfer as a HS
  device against ≥3 host controllers (e.g. Intel XHCI, AMD XHCI, a hub) × ≥3
  cable lengths up to 2 m, both connector orientations. Watch for
  fallback-to-FS, re-enumeration, or CRC/babble errors. An eye/compliance
  measurement is preferable if instrumentation allows. Rationale: impedance
  is calculated (verification/usb90_solve.md), not fab-measured.
- **Rail-sequencing / reset scope-capture gate:** capture 3V3, 0V9, 1V8, 3V3A +
  RST_N (vs ADR-0005) across ALL of the following startup corners — a capture
  set is incomplete without every row:
  - cold start, room-temperature start, and warm restart;
  - fast disconnect/reconnect of the 5 V input;
  - slow 5 V input ramps (bench supply ramp, not just the brick);
  - brief brownouts (dips that do not fully discharge the rails);
  - repeated power cycling;
  - both lightly and heavily loaded USB conditions (idle enumeration AND
    sustained 8-channel HS streaming).

  **PASS CONDITION (explicit): 1V8 must be VALID before the 0V9 core rail
  reaches its valid threshold, at every corner; and RST_N must remain
  asserted (low) until ALL required I/O rails (3V3, 1V8) are stable.** The
  as-built ordering is plausible-by-topology (U9's 1V8 rises from 3V3
  directly while U8's 0V9 waits on PG_3V3) but is NOT interlocked — nothing
  senses that 1V8 is valid before 0V9 starts. **A failure at ANY corner
  requires a real interlock — gate U8 EN from a 1V8 supervisor or a combined
  rail-good signal — NOT an empirical delay tweak** (a delay tuned at one
  corner is untested at the others). The interlock is a v-next design item (§6).
- 8-channel simultaneous recording + inter-ADC sync, noise/crosstalk per
  channel, operation over intended Cat5e lengths, thermal check of U1 + the
  two bucks, fault recovery after a port short. This release is a first-article
  manufacturing package, not a production-validation package — fabricate
  minimum quantity, characterize one board fully, preserve the measurements.
- 0V9 core-rail ripple/droop at U1 during repeated boot, sustained USB
  High-Speed traffic, and maximum audio processing load (the decoupling meets
  the vendor minimum of 12× 100 nF; the scope measurement is the close-out).

## 5. Recorded P2s (non-blocking)

- Buck Cin hot loop 2.51 mm vs the <2 mm part.yaml budget — nudge at next
  re-place.
- L1 (C882626) stock 496 and U7/U8's C5224055 stock 383 at v1.4 staging
  (2026-07-25) — order-day recheck mandatory, both clear 5 boards today.
- RG1/R_cs/R_rst/R_scl/R_sda are EXTENDED parts (basic equivalents stocked
  out) — each extended reel adds a setup fee; if C25744/C25900 restock by
  order day, swapping back at source is a legal docs-only change for a future
  release, NOT an order-form substitution.
- D_USB ESD stub rides the J2 mirror-pad legs (~7 mm) — placement unchanged
  from v1.0; candidate v-next: move TPD4EUSB30 into the pair path at J2.

## 6. Next-rev work order (non-blocking)

- **Local fiducials.** This board has none; JLC's rail fiducials carry the
  order. Add two or three 1 mm local fiducials near U1 (0.4 mm pitch) at the
  next layout revision — they cannot be added to a sealed board.
- **Rail-sequencing interlock:** gate U8's EN from a 1V8 supervisor or a
  combined rail-good signal instead of PG_3V3 alone, so the 1V8-before-0V9
  ordering is enforced by hardware rather than by RC-race topology. Mandatory
  if any §4a sequencing corner fails; recommended for production regardless.
- **In-line USB ESD (pre-production):** move TPD4EUSB30 directly in-line with
  D+/D− at J2, minimize connector-to-protector distance and ground inductance,
  then contact + air-discharge ESD testing while monitoring resets, USB
  disconnects, data corruption, and permanent damage. The current ~7 mm branch
  stub is bench-acceptable only.
- F_BEEP PTC (~1.1 A hold) in series with FB_BEEP; shared SMBJ5.0A on the
  P5VA spine (ADR-0007). Durable fix: keyed (non-RJ45) connector.
- Optional forced-PWM EN divider on U7 if 3V3 PFM ripple ever shows in the
  audio chain (ADR-0005 amendment).
- Converter wire-crossing invariant upstream (the net-merge class that forced
  this board's check_port_nets gate + the promoted-sch guard in rebuild_all).
- Promote add_u1_thermal_vias.py into route_and_stitch_generic as an
  `ep_thermal_vias` stitch config block on the second board needing it.

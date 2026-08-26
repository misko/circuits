# ORDER README — crow-recorder-central-v2 (8-channel CENTRAL recorder) v1.1

Central hub of the CROW ACOUSTIC LOCALIZATION ARRAY: 8 remote mic pods home-run
over custom-pinout Cat5e into 8 RJ45 ports (J3–J10), 2x PCM1865 4-ch ADCs
(U2/U3), XU316-1024 USB-Audio SoC (U1) to a USB-C host port (J2), shared-clock
topology (ADR-0004), beeper calibration bus, 5V brick input (GST25A05, J1) with
AO3401A reverse-polarity FET (Q1) + SMAJ5.0A (D1) + 2A fuse (F_IN).
Release **v1.1-2026-07-24**. Board **170.1 × 120.1 mm, 6 layer**.

**v1.1 SUPERSEDES v1.0** (external review 2026-07-24, DO-NOT-ORDER; archived
08_reviews/2026-07-24_v1.0_external-llm_full.md). The three closures:
- **F1** — U1 (XU316) exposed-pad thermal grid remodeled as 16 REAL VIAS
  (they now emit under the ViaDrill tool, not ComponentDrill) + the
  filled-and-capped via-in-pad process is EXPLICITLY ORDERED below (§1a).
- **F2** — USB 2.0 High-Speed pair now 90 Ω BY CONSTRUCTION: stackup-specific
  solve (JLC06161H-3313), active diff-pair DRC rules, rerouted at
  w 0.125 / gap 0.15 mm, skew 0.110 mm ≤ 1 mm (verification/usb90_solve.md).
- **F4** — all evidence in verification/ regenerated against THIS staged
  archive; manifest counts match the shipped evidence exactly.
- **PR2-P0-1** (found by this release's own zero-context pin review, beyond
  the external review's scope) — U1's LV_L_N/LV_T_N/LV_R_N IO-voltage straps
  (pins 40/43/52) were hard-tied to 3V3 in v1.0, but they are Input-PU pins
  on the FIXED-1.8V IOB bank (AMR = VDDIO+0.5 = 2.3V — not 3.3V-tolerant;
  XU316 ds v2.0.0 §4.4/§4.8/§15.1). v1.1 floats them (the datasheet's own
  3.3V-mode select via internal pull-up); verification/lv_strap_fix_diff.md
  proves exactly these 3 pins moved and nothing else.

Gates at seal: DRC 0/0/0 on the archive's own source/ (--severity-all
--refill-zones --schematic-parity), check_port_nets 115/115 labels + 8/8 ports,
ERC 0 errors / 1201 baselined warnings, count_parity 194 x4, policy_audit
0 FAIL (R-LEN now GRADED: USB pair spread 0.110 mm), E-INV 7/7, twin exit 0
(160 OK / 359 checked), audit_board incl. the new U1-EP-16-vias and USB
skew/width/layer gates. Evidence in `verification/`; hashes in `MANIFEST.txt`.

---

## 0. ⚠️⚠️ CRITICAL DEPLOYMENT CONSTRAINT — PORTS ARE NOT ETHERNET ⚠️⚠️

**All 8 RJ45 ports (J3–J10) carry a CUSTOM 5 V AUDIO/POWER pinout
(1,2 = AUDIO±; 3,6 = +5V_BEEP/RETURN; 4,7 = +5V_AUDIO; 5,8 = GND). NEVER plug
any port into an Ethernet switch, router, or ANY PoE source.**

WHY (accepted-risk sign-off, ADR-0007, carrying the pod-v2 ADR-0005 user
waiver — UNCHANGED in v1.1; the 2026-07-24 external review concurs the
disclosure is adequate for a bench deployment and a no-go anywhere ordinary
patch cables exist): an 802.3 endspan injector (mode B: 4/5 = +, 7/8 = −)
drives ~48 V through the per-port PTC into the shared 5 V rail — above the
AP61102 buck vin_abs_max (6.5 V) and every 5 V-rated part. The input TVS (D1)
sits on VIN_RAW, the wrong side of Q1 to clamp a rail-side injection. There is
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

Upload set (in `fab/`):
- **PCB order:** `crow_recorder_central_v2_gerbers.zip` (6 copper layers, F/B
  mask+paste+silk, Edge_Cuts, PTH+NPTH drills). BOM/CPL are **not** in the zip.
- **Assembly BOM:** `fab/bom.csv` — `Comment,Designator,Footprint,MPN,LCSC`.
- **Assembly CPL:** `fab/cpl.csv` — rotation-DB-corrected.

Re-run a same-day stock check before paying.

## 1a. ⚠ FAB NOTE — U1 exposed-pad via-in-pad (F1 closure; INCLUDE WITH ORDER)

U1 (XU316-1024, TQFP-128 with 4.7 × 4.7 mm exposed pad, board center-north at
(90, 102) mm, top side) has **sixteen 0.30/0.15 mm thermal vias in a 4×4 grid
(±0.55 / ±1.65 mm from the EP center) directly under its pasted exposed pad.**
In this release they are REAL VIAS — the PTH drill file emits them under the
**ViaDrill** tool (T1, 0.150 mm) together with the board's other vias; there
is **no 0.15 mm ComponentDrill tool** in the file (v1.0 defect, fixed).

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

## 2. Sourcing swaps + consignment lines (v1.1 state)

| Ref(s) | Ordered part | Why |
|---|---|---|
| U9 | **TLV70018DDCR (C79924)** | TCR2LF18 (C150173) stock 0; ADR-0006 documented pin-compatible drop-in |
| Y1 | **NX3225SA-24MHZ-EXS00A-CS08583 (C2762192)** | FA-238 MD50Y stock 0; same 3225-4P, same CL 9 pF (02_parts note) |
| R_fb2b | **402 kΩ (C25785)** | 400 k not stocked; −0.17 % on the 0V9 setpoint, inside tolerance |
| FB_BEEP, FB_u33, FB_u18, L_pll | **BLM21SP601SN1D (C3716677)** | first pick BLM21PG600SN1D is a **60 Ω** part — wrong-part caught at M-BOM staging (v1.0) |
| CL1, CL2 | **12 pF C0G (C1547)** | v1.0 fresh-lens P1 fix, carried |
| Cout_U10 | **2.2 µF 25 V X5R (C72203)** | v1.0 fresh-lens P1 fix, carried |
| RG1, R_cs, R_rst | **10 kΩ 1 % 0402 (C60490, YAGEO RC0402FR-0710KL)** | v1.1 staging: basic C25744 stock 0; extended equivalent pinned at source |
| R_scl, R_sda | **4.7 kΩ 1 % 0402 (C105871, YAGEO RC0402FR-074K7L)** | v1.1 staging: basic C25900 stock 0; extended equivalent pinned at source + vetted in the passives ledger |
| U1 | XU316-1024-TQ128-I24 (C6938291) | **consignment/global-sourcing** (ADR-0003): JLC assembly stock chronically 0; source Digi-Key/Mouser + consign, or hand-place (0.4 mm TQFP, hot-air skill required). Record the consignment MPN + lot with the order. |
| J3–J10 | RJHSE-5384 (C9900035627) | C99* = consign-only code (no JLC assembly line); hand-solder THT or consign (pod-v2-certified footprint, pad-1 continuity backstop below) |

## 3. Hand-solder / off-CPL parts

| Ref | Part | Note |
|---|---|---|
| J3–J10 | RJHSE-5384 RJ45 x8 | THT; consign or hand-solder; confirm ABSENT from automated placement in the JLC preview |
| U1 | XU316 (if not consigned) | prefer JLC consignment line |
| JP_INJ | 1x03 2.54 mm header | uncoded, hand-solder (beep-injector jumper) |
| J_DBG | 1x08 2.54 mm header | uncoded, hand-solder (JTAG 1V8) |

## 3a. Assembly-closure checklist (EXT-F5; archive at order time)

- Annotated screenshot(s) of the approved JLC placement preview.
- Pin-1/polarity confirmation for every ROT-DB-SUGGEST row in
  verification/twin_report.txt (Q1, U2, U3, Q2, U7, U8, U9, U5, D_USB) — the
  rotations-DB values are assembly-zero truth; verify in the preview, do not
  blind-apply.
- The exact U1 consignment MPN + lot; final supplier + MPN for every
  manually-sourced line.
- JLC's confirmation (or production-file evidence) of the §1a filled+capped
  EP via construction.

## 4. First-power ritual (when boards arrive)

1. **Before any power:** multimeter every RJ45 port against the silk legend
   (1,2 = AUDIO±; 3,6 = +5VBEEP/RTN; 4,7 = +5VAUD; 5,8 = GND) and pad-1 →
   contact-1 continuity on one port.
2. Confirm D1 band → VIN_RAW, Q1 orientation (drain = VIN_RAW — CORRECT
   as-built; do not "fix"), J1 center = +.
3. Power from the GST25A05 brick only. Verify 5 V, then 3V3 → PG_3V3 → 0V9
   sequencing (ADR-0005), 3V3A, 1V8.
4. Enumerate USB-Audio on the host; verify per-port pod power (4/7 vs 5/8
   = 5 V) on all 8 ports before connecting pods.

## 4a. REQUIRED first-article gates (blocking before further units)

- **U1 EP joint:** X-ray or equivalent inspection of the exposed-pad solder
  joint (voiding, wicking into the 16 capped vias, reverse-side solder).
- **USB High-Speed validation matrix (F2):** enumerate + sustained transfer
  as a HS device against ≥3 host controllers (e.g. Intel XHCI, AMD XHCI, a
  hub) × ≥3 cable lengths up to 2 m, both connector orientations. Watch for
  fallback-to-FS, re-enumeration, or CRC/babble errors. An eye/compliance
  measurement is preferable if instrumentation allows. Rationale: impedance
  is calculated (verification/usb90_solve.md), not fab-measured.
- Rail/reset scope captures (3V3, 0V9, 1V8, 3V3A sequencing vs ADR-0005),
  8-channel simultaneous recording + inter-ADC sync, noise/crosstalk per
  channel, operation over intended Cat5e lengths, thermal check of U1 + the
  two bucks, fault recovery after a port short (EXT-F6: this release is a
  first-article manufacturing package, not a production-validation package —
  fabricate minimum quantity, characterize one board fully, preserve the
  measurements).

## 5. Recorded P2s (non-blocking, carried + v1.1 additions)

- Buck Cin hot loop 2.51 mm vs the <2 mm part.yaml budget — nudge at next
  re-place.
- L1 (C882626) stock 660 at v1.1 staging — order-day recheck mandatory.
- RG1/R_cs/R_rst/R_scl/R_sda now EXTENDED parts (basic equivalents stocked
  out 2026-07-24) — each extended reel adds a setup fee; if C25744/C25900
  restock by order day, swapping back at source is a legal docs-only change
  for a future release, NOT an order-form substitution.
- D_USB ESD stub rides the J2 mirror-pad legs (~7 mm) — placement unchanged
  from v1.0; candidate v-next: move TPD4EUSB30 into the pair path at J2.

## 6. Next-rev work order (non-blocking)

- F_BEEP PTC (~1.1 A hold) in series with FB_BEEP; shared SMBJ5.0A on the
  P5VA spine (ADR-0007). Durable fix: keyed (non-RJ45) connector.
- Optional forced-PWM EN divider on U7 if 3V3 PFM ripple ever shows in the
  audio chain (ADR-0005 amendment).
- Converter wire-crossing invariant upstream (the net-merge class that forced
  this board's check_port_nets gate + the promoted-sch guard in rebuild_all).
- Promote add_u1_thermal_vias.py into route_and_stitch_generic as an
  `ep_thermal_vias` stitch config block on the second board needing it.

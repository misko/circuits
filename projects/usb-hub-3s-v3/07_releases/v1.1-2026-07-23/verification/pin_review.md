# Fresh-context PIN REVIEW — usb-hub-3s-v3 **v1.1**

- Board: `projects/usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb` (v1.1, DRC 0/0/0)
- Protocol: `skills/kicad-pcb/references/pin-review-protocol.md`
- Method: pad->net read straight from the board (`pcbnew`), adversarially compared
  to each part's datasheet pin FUNCTION (not to the authors' conclusions), plus the
  machine gate E-INV (16/16 invariants against the exported netlist).
- Date: 2026-07-23
- **VERDICT: PASS** (0 FAIL). Whole board confirmed; focus on the v1.1 DELTA
  (eFuse cell U13/Q6/Q7, +15 parts, FB-at-connector change, master-off SW1).

## Scope

v1.1 adds a protected-VBUS cell downstream of the 5VC buck and a master-off
switch (journal `03_schematic_v1.1`). The carried-over parts (LM5116 U2/U11,
TPS2557 U3-U5, TPS2513 U8-U10, USBLC6 U6/U7/U12, FETs Q1-Q5, connectors J1-J5)
are UNCHANGED from the v1.0 pin review (PASS) — same footprints, same nets — and
are re-confirmed by schematic parity = 0 and the JLC twin (88 OK / 232 checked).

## v1.1 DELTA — pad->net verified against datasheet function

### U13 — TPS26631 eFuse (HTSSOP-20 + EP), SLVSE94G Table 5-1
| Pin | DS function | Board net | OK |
|----|----|----|----|
| 1,2,3 | IN | EFINC | yes (eFuse input from Q6 drain) |
| 4 | B_GATE | BGATEC | yes (drives Q6 gate) |
| 5 | DRV | DRVC | yes (drives Q7 gate) |
| 6 | IN_SYS | 5VC | yes (senses buck-C output = true system input) |
| 7 | UVLO | GND | yes (disabled -> GND) |
| 8 | OVP | OVPC | yes (OVP divider mid) |
| 9 | GND | GND | yes |
| 10 | dVdT | DVDTC | yes (soft-start cap) |
| 11 | ILIM | ILIMC | yes (R_ILIM 3.09k) |
| 12 | MODE | GND | yes (auto-retry) |
| 13 | SHDN | SHDNC | yes (SHDN divider mid, active-low enable) |
| 14 | IMON | NC | yes (unconnected-*) |
| 15 | FLT | NC | yes |
| 16 | PGTH | GND | yes |
| 17 | PGOOD | NC | yes |
| 18,19,20 | OUT | VBUSC | yes (protected connector rail) |
| 21 | EP | GND | yes (thermal pad) |

All 20 pins + EP correct. Feature-critical: **IN_SYS=6 on 5VC**, **OUT=VBUSC**,
active-low **SHDN via divider** (not tied to 5VC abs-max) — all per the journal.

### Q6 — AON6354 reverse-blocking FET (PowerPAK SO-8)
`1,2,3=S=5VC`, `4=G=BGATEC`, `5=D=EFINC`. Body diode blocks EFINC->5VC reverse.
Correct: source on 5VC, drain on the eFuse IN node. OK

### Q7 — BSS138 fast gate-pulldown (SOT-23)
`1=G=DRVC`, `2=S=5VC`, `3=D=BGATEC`. On reverse detect, DRV turns Q7 on, pulling
BGATEC (Q6 gate) to 5VC (= Q6 source) -> Vgs(Q6)=0 -> Q6 off in ~0.17us. OK
This is the datasheet-mandated 2-FET reverse-block config (SLVSE94G Fig 8-7).

### SW1 — SS12D07 master-off (slide, SPST use)
`2=COM=ENKILL`, `1=T1=GND`, `3=T2=NC`. Slide to T1 grounds ENKILL -> both LM5116
EN low. Cross-check: U2.4 and U11.4 both on ENKILL (E-INV #5). OK
(NB land-pattern pitch: see render review + twin adjudication — order-preview item.)

### FB / setpoint (Blocker-2 fix)
- **R12.1 = VBUSC** (buck-C FB top senses the POST-eFuse connector rail) — this is
  the sense-at-connector fix; the loop holds VBUSC at 5.151 V. OK
- R3.1 = 5VA (buck-A keeps sensing its own output). OK

### eFuse set-pin dividers
- ILIM: R30 (ILIMC->GND). OVP: R31 (5VC->OVPC), R32 (OVPC->GND) -> 5.91 V trip.
- SHDN: R33 (5VC->SHDNC), R36 (SHDNC->GND) -> ~0.6*5VC ~= 3.09 V. All OK
- Snubbers: R34 (SW_A->SNUB_A) + C53 (SNUB_A->GND); R35 (SW_C->SNUB_C) + C54. OK

## Machine cross-checks
- **E-INV 16/16** hold against `06_build/netlists/usb_hub_3s_v2.net` (eFuse series
  chain 5VC->Q6->EFINC->U13->VBUSC; VBUS pads on VBUSC; CC Rp to VBUSC; ENKILL merge).
- **Schematic parity = 0** (board == 115-part schematic).
- **P-POL PASS** (pad-1 net polarity for every polarized 2-pad part).

## Non-blocking notes carried to order
1. SW1 (SS12D07VG6) footprint pitch is 2.5 mm (standard SS-12D07); JLC's assembly
   model is the mislabeled VG4 variant (2.0 mm). Confirm the VG6 pitch on the JLC
   order preview; jumper fallback exists (part.yaml). Hand-solder mechanical part.
2. Snubbers R34/R35/C53/C54 are optional/DNP-by-default in the source but are NOT
   DNP-flagged on the board, so the fab BOM/CPL would populate them (benign). See
   render review + the pre-order decision list.

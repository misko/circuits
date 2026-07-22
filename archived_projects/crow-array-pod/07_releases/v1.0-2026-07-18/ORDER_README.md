# ORDER_README — crow-array-pod v1.0 (2026-07-18)

## JLC order options (PCB)

- 2 layers, 94.5 x 44.5 mm, STANDARD options only (min drill 0.3mm,
  0.6/0.3 vias — NO advanced/small-via option needed).
- Qty: **10** boards (6 pods + spares). Any thickness 1.6mm, any color
  (black hides best outdoors), HASL or ENIG (ENIG preferred: outdoor +
  conformal coat over HASL is fine too).
- Upload `crow_array_pod_gerbers.zip` to the PCB order; `bom.csv` +
  `cpl.csv` to SMT assembly (top side, 15 coded lines / 25 placements).

## Order-day checklist (before paying)

1. **Stock re-check**: `python3 jlc_stock_check.py bom.csv --min-stock 10`
   — especially **C22359707 (CMT-8504 transducer): stock was 182 on
   2026-07-18** (need 10). If it dropped below need: mark the BZ1 line
   Do-Not-Place and hand-solder from Digi-Key (list below).
2. **U1 rotation in the 3D preview** (MANDATORY, adjudicated ROT-DB item):
   OPA1678 pin-1 dot must sit at the chip's TOP-LEFT (NW) corner when the
   NOT ETHERNET banner reads upright (pin columns run N-S). The rotations-db
   applied 270; the twin's EDA-frame fit suggested 90 — the preview is the
   tie-breaker. If the preview shows pin 1 SE, rotate the CPL entry 180.
3. **D2 (SS14) cathode band** faces NORTH-toward-BZ_P trace side? Check:
   band = pad 1 = the pad nearer "FLYBACK" text start (west pad). Preview
   diode band orientations vary per reel — eyeball it.
4. **C1 electrolytic**: negative stripe must be on the EAST pad (pad 1 =
   + = west, marked "+" on silk).
5. Qty > refs on small passives = attrition padding, normal.
6. Layer count 2 in the order form.

## Hand-solder list (uncoded lines, Digi-Key order)

| Ref | Part | Digi-Key | Note |
|---|---|---|---|
| J1 | 3.5mm 8-pos screw terminal (KF128L-3.5-8P class) | ED2745-ND (On Shore OSTVN08A150) or TE 282834-8 (A113317-ND) | THT, 8 joints; LCSC C5342501 consign alt |
| J2 + mic | PUI AOM-5024L-HD-R electret capsule | 668-1538-ND | capsule mounts in the enclosure cavity on ~40mm twisted leads to the MIC+/MIC- pads. SOLDER THE CAPSULE FAST: <=2s per terminal, <=360C (datasheet handling limit) |
| BZ1 fallback | CMT-8504-100-SMT-TR | 102-CMT-8504-100-SMT-TR-ND | ONLY if JLC stock ran out (see checklist 1) — hand-reflow, watch the + pad (top-left, silk +) |
| D3 (optional) | SMAJ6.0A TVS | SMAJ6.0ALFCT-ND | DNP by design; fit only when trialing the TVS clamp (remove D2 first — ADR-0002) |
| L1 (optional) | Wuerth 744227S WE-SL2 CM choke | 732-1591-1-ND | DNP EMI reserve; to fit: remove R13/R14 (0R), reflow choke (D7) |

Per-pod hand work: 8 terminal joints + 2 mic-lead joints.

## Known cosmetic issue

pdf/assembly_top.pdf has overlapping VALUE texts in dense clusters (F.Fab
layer auto-positions). Silkscreen on the physical board is clean
(DRC-checked); use pdf/pcb_layers.pdf page 3 for silk truth.

## Conformal coating (source doc §3A)

Coat the assembled board EXCEPT (keep-out list — mask before spraying):
- the microphone capsule and its J2 pads/leads,
- BZ1 transducer (sound port on top!),
- J1 terminal block (contacts),
- all test points TP1-TP6,
- D3/L1/R15 empty reserve pads (they must stay solderable).

## First-power ritual (per pod, BEFORE mic connect)

1. Cable/bench 5V into terminal 4 or 7 (+) and 5 or 8 (GND). Current
   draw must be < 10 mA.
2. TP3 (2V5) = 2.47 V ±2%. TP4 = 5V. Bias voltage at the MIC+ pad
   (J2 pin 1) = ~4.9 V open-circuit (through 3.9k, no capsule yet).
3. Only then solder/plug the capsule; MIC+ settles to ~2.9 V with the
   capsule drawing ~0.5 mA.
4. Beeper check: 5V across terminals 3 (+) and 6 (return) beeps it
   (do not hold DC > a few seconds; it is rated for 4 kHz switching).
5. NOT-ETHERNET rule: never patch these runs into network gear; label
   both cable ends. Storm policy: disconnect pods in lightning weather
   (ESD parts are not lightning protection — ADR-0001).

## Field-test gates that stay OPEN after this order (source doc §3A/§10)

Ordering these boards does NOT freeze the mechanical design: the coded
transducer must still prove detectable at 25/50 ft through the hood in
wind (FIELD-TEST GATE), and the pod prototype -> cable test -> range test
sequence gates the CENTRAL board order, not this one (commission A1/D2).

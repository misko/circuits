# usb-hub-3s v1.0 — JLCPCB order guide

Board: 3S LiPo (XT60) in → 3× USB-A 5 V / 2 A (2.5 A burst) + 1× USB-C PD
5–20 V / 5 A. 110×90 mm, 4-layer. DRC 0/0/0 at full severity; all
verification evidence in `verification/`.

## PCB options (non-negotiable ones in bold)

- Layers: 4 (stackup In1 = GND plane, In2 = VIN plane)
- **PCB tier: the ADVANCED option is REQUIRED** — 0.25/0.15 mm vias
  (POFV, via-in-pad under the QFN-48 and thermal drops). A standard-tier
  order will be rejected or silently re-drilled wrong (D-TIER, ADR 0005).
- Thickness 1.6 mm, 1 oz outer / 0.5 oz inner (ampacity floors derived
  for this), HASL or ENIG, any solder-mask color.
- Files: `fab/gerbers_usb_hub_3s.zip` (11 layers + PTH/NPTH drills).

## Assembly

- `fab/bom.csv` (48 lines, every line carries an explicit LCSC code) +
  `fab/cpl.csv` (110 placements). Economic/standard assembly; THT lines
  (J1 XT60, J2–J4 USB-A, J5 shell legs) need the through-hole assembly
  option — otherwise move them to the hand-solder list below.
- **Order-day stock recheck is MANDATORY for U1 (C5140592, IP6559-C)** —
  stock was 62 at release time (ADR 0004). No verified substitute.
- U6/U7 must be **C473910 (TPS2513A)** — the non-A C44770 loses the
  Apple 2.4 A divider mode (verification_report.md).

### Rotation / polarity preview checklist (before paying)

In the JLC order preview, verify:
1. U1 (QFN-48) pin-1 dot NW; U2 (HTSSOP-20) pin-1 at the west row top.
2. D8/D9 (SOD-523, next to J5): cathode toward the data line (north pads
   DPC/DMC). Their 3D model is featureless — the preview is the ONLY
   visual check (render review finding #1).
3. Electrolytics C1/C2/C26: stripe (negative) EAST, silk "+" WEST.
4. Q1–Q8 (PowerPAK): merged drain paddle east/west per silk.
5. All diodes D1–D7: band matches the silk bar.

## Hand-solder list (not in the assembly order)

| Ref | Part | Note |
|---|---|---|
| F1 | Keystone 3568 clips ×2 (LCSC C5249699 = ONE clip) | + 20 A MINI blade fuse |
| J1, J2–J4 | XT60PW-M (C98732), KH-AF90DIP-112 (C503996) | only if THT assembly not ordered |

## First-power ritual (battery = bench supply first, 12 V, 1 A limit)

1. **Before any load**: continuity — XT60 "+" pad → F1 → Q1 drain;
   XT60 "−" → GND. Per USB-A port: VBUS pin (top pin, nearest the port's
   silk label) → TPS2557 OUT. A reversed XT60 or mirrored USB-A pinout
   must be caught here, not by smoke (ADR 0006 residual risk).
2. Bring up at 12 V: verify 5VA rail = 5.0 V, VCC5V = 5 V, VCCIO = 3.3 V.
3. **R25 is DNP by design** (ADR 0004: the PDO-set resistor's value table
   is app-note-only). With R25 open the IP6559 uses its variant-default
   PDO set: verify the advertised PDOs with a USB-PD analyzer BEFORE
   trusting the port. If the set is wrong, the fix is a single 0603 1%
   resistor on the R25 pads per Injoinic's app note — not a re-spin.
4. Check UVLO: supply below 8.8 V must shut the buck down (rises at
   ~9.65 V).
5. Load test: 2 A per A-port (burst 2.5 A — TPS2557 ILIM window is
   2.72–3.29 A); USB-C 5 A only appears with an e-marked cable.

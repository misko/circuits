# ORDER_README — crow-array-central v1.0 (2026-07-18)

## >>> 1. DO NOT ORDER YET — ORDER IS GATED <<<

Per the commission's own risk sequence (shared BRIEF P6 + A1): the order
for this central PCB is **GATED on the field-test sequence** — pod
prototype field tests (cable test, outdoor transducer range test) AND the
USB audio firmware proven on the **XMOS EVAL BOARD** — before the custom
central board is fabbed. The design is READY (all gates green, this
release is sealed); the purchase is not. When the gates clear, follow the
order-day checklist below.

## >>> 2. COST — EXCEEDS THE ELECTRONICS TARGET <<<

The commission's $79-90 electronics target is **exceeded**. Drivers:
- **6-layer** stackup (ADR-0008: 4L would not close routing) on a
  **176 x 122 mm** board — large-area 6L is the dominant PCB cost;
- **JLC small-via option** (0.30/0.15 vias, ADR-0009): the 0.4mm-pitch
  XU316 via-in-pad escape needs it; JLC prices it per order;
- XU316 **consign sourcing** (below) adds handling on top of the ~$25 chip.
Rough estimate at qty 5: PCB ~$120-160 for the panel of 5 (6L + advanced
via option), assembly setup + ~50 extended-reel fees ~$150-200, parts
~$35-45/board excluding the XU316, plus XU316 sourcing ~$25-30/board =
**very roughly $150-220 per assembled board at qty 5** vs the $79-90
target. A future cost spin's levers: smaller board outline, every-other-
pad F.Cu escape to drop the small-via tier (ADR-0009), and 4L partial
depop — none attempted for v1.0 (correctness first, per the brief).

## >>> 3. XU316 (U1) IS JLC STOCK 0 — CONSIGN / HAND-SOLDER <<<

C6938291 (XU316-1024-TQ128-I24) is a 0-stock JLC extended part
(verification/stock_check.txt). The BOM line stays COCED so JLC's
consignment/global-sourcing flow can populate it; if consign is refused
or slow, order from Digi-Key/XMOS direct and hand-reflow (TQFP-128 0.4mm
+ EP: hot-air/paste, not iron-only). Every OTHER coded line verified at
>=5x stock for qty 5 on 2026-07-18 — re-run verify mode on order day.

## >>> 4. Q9 VERDICT (reverse-polarity FET) — BOARD CORRECT <<<

A dedicated fresh-context review (D19) confirmed the AO3401A high-side
reverse guard is CORRECT on the board: pad3=DRAIN=5V_P (input),
pad2=SOURCE=5V (load) — the P-FET body diode (anode=D, cathode=S)
blocks reverse input as ADR-0007 designed. Two WRONG statements in
02_parts/AO3401A/part.yaml had cancelled each other and were fixed; no
board change. (Same doc-error class recurred at the RJ45s — D28: the
board matches the SEALED pod v1.0 cable map 4=5V/5=GND/7=5V/8=GND
contact-for-contact; the part.yaml note was wrong and is fixed.)

## JLC order options (PCB)

- **6 layers**, 176.15 x 122.15 mm, **"advanced" SMALL-VIA option
  REQUIRED** (min via 0.30/0.15 — the order form must have it selected
  or JLC rejects/redrills the escape).
- Stackup JLC7628-class: F / In1 GND / In2 / In3 / In4 GND / B.
- Qty: **5** boards. 1.6mm, ENIG preferred (0.4mm-pitch TQFP + USB-C).
- Upload `crow_array_central_gerbers.zip` (15 files: 13 gerber layers +
  2 drills) to the PCB order; `bom.csv` + `cpl.csv` to SMT assembly
  (top side, 45 coded lines / 221 placements).

## Order-day checklist (before paying)

1. **Stock re-check**: `jlc_stock_check.py bom.csv --min-stock 25` same
   day (XC6227 C6035451 was 268; RJ45-alt C3179625 and the 100u C48970904
   run shallow).
2. **MANDATORY 3D-preview rotation confirmation** for the refs whose
   twin EDA-frame fit disagreed with the rotations DB (deferred by
   adjudication — verification/twin_adjudications.yaml): U2/U3 (PCM1865
   TSSOP-30: pin-1 dot NW with the NOT-ETHERNET banner upright), U4
   (SOIC-8), U5 (VSSOP-8), U10/U11 (AP61102 SOT-563 pin-1 corner),
   U12 (SOT-23-5), D10 (USON-10), Q1-Q9 (SOT-23). If any preview shows
   pin 1 rotated, fix that CPL row (do NOT re-upload the BOM afterwards —
   BOM re-upload resets matching).
3. **D9 (SMBJ5.0A) band**: cathode band toward the 5V_P side (pad 1,
   west); preview diode orientations vary per reel.
4. **C90 electrolytic** (RYVP 100u): "+" silk = pad 1; check the model's
   base bevel in the preview.
5. Attrition padding (qty > refs) on small extended passives is normal.
6. Layer count 6 + the small-via option both set in the order form.
7. Assembly drawing note: pdf/assembly_top.pdf has F.Fab value-text
   pile-ups in the dense clusters (known cosmetic, pod-precedent) — for
   hand work use pdf/pcb_layers.pdf silk pages; the physical silk is
   clean and now carries functional labels (D29).

## Hand-solder list (uncoded lines; Digi-Key/direct)

| Ref | Part | Note |
|---|---|---|
| J1-J6 | Amphenol RJHSE-5384 8P8C w/ LEDs | THT tabs; LCSC has no assy stock (C3179625 is 2-stock). Digi-Key RJHSE-5384-ND. Ports 7/8 are DNP spares (no jack fitted). |
| J9 | DC-005C-20A barrel jack (center+, GST25A05-P1J) | THT, 3 joints |
| J11 | KF128L-3.5-2P terminal | DNP alternate 5V entry — fit only if the barrel is abandoned |
| J12 | GCT USB4105-GF-A USB-C 16P | mid-mount SMD + through-hole shield tabs; hand-solder or JLC-consign C3020560 (4476 stock) |
| J10, J13, J14 | 2.54mm 1x02 headers (INJ IN, xSYS DBG x2) | generic; NOTE: debug lines are 1.8V-domain (VDDIOB18) — any adapter must drive TDI/TMS/TCK/RST_N at 1.8V |
| U1 fallback | XU316-1024-TQ128-I24 | see section 3 |

## First-power ritual (before first real supply)

Multimeter the barrel jack: center pin -> continuity to F1 (PTC) -> D9
cathode / Q9 drain; barrel shell -> GND. Then bench-supply 5V current-
limited to 100mA before the Mean Well brick. Verify TP9 (5V), 3V3, 0V9,
TP11, 1V8, 3V3A rails in that order (bucks EN'd from 5V).

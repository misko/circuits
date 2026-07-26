# render_review — zero-context review (fable-medium, 2026-07-26)

> **SCOPE AND INDEPENDENCE.** Reviewer was given the twin and bare renders, the CPL,
> the board and the dossiers, and was NOT part of the design session. Brief: this is
> the HUMAN VISUAL CHANNEL for a class of defect the machine channels on THIS board
> have repeatedly got wrong, with the four specific incidents named.
>
> **VERDICT: PASS — no blocking visual defect; no render-vs-CPL or render-vs-netlist
> disagreement found.**
>
> * **Q1-Q6 bare-vs-twin discrimination done explicitly** — the test that the earlier
>   review generation failed, when TWO OF FOUR lenses read the bare copper drain
>   paddle as a moulded package. Bare shows the paddle; twin shows solid bodies
>   covering it, pin-1 dots in the netlist-correct corners. PASS.
> * **CPL datum** recomputed from pad geometry: matches for all five connectors
>   (J1 27.0/40.4, J2-J4 140.3/*, J5 120.0/107.502), each 1.5-4.7 mm off the KiCad
>   anchor — the v1.6 fix is real and holds.
> * **LEDs and C1/C2**: board artwork self-consistent with the shipped CPL, but the
>   reviewer states plainly that the 3D models are polarity-symmetric, so a render
>   CANNOT decide the physical orientation. Both stay on the order-preview human gate.
> * One cosmetic nit, NOT fixed here because silk is copper and this supersede is
>   fab-byte-identical: refdes "D1" runs into the "LEDS DARK = SWITCH OFF" legend.
>   Carried to v-next.
>
> Dated copy: `08_reviews/2026-07-26_v1.8_render-review.md`.

--- VERBATIM REVIEWER REPORT ---

# Zero-context render review — usb-hub-3s-v3 v1.7-2026-07-26

Reviewer: independent visual pass over the 8 release renders, cross-checked against
`fab/cpl.csv` and pad/net positions extracted from `source/usb_hub_3s_v2.kicad_pcb`
(pcbnew). Crops at 6x zoom were taken at each part location (mm->px mapping derived
from the board-edge bounding box, 19.95..150.05 x 19.95..112.05 mm).

## Summary verdict

**No blocking visual defect found.** Everything the render CAN settle is consistent:
LED silk cathode bars sit on the GND side matching the netlist; C1/C2 twin models show
the minus stripe on the GND pad and the silk "+" on the VIN pad; all six MOSFETs have
real moulded 3D bodies (bare-vs-twin comparison passes, with pin-1 dots in the
netlist-correct corners); all five connectors sit on their pad arrays and the CPL rows
sit on pad-array centres, not KiCad anchors. Safety silk legends are present and legible.
**However**, the two highest-stakes items (LED physical polarity at rotation 0.0, and
C1/C2 physical anode orientation) are NOT establishable from these renders because the
LED 3D model is polarity-symmetric and the cap question is a JLC-library rotation-
authority question, not a geometry question. Both still require the JLC order-preview
human gate, exactly as `twin_report.csv` itself says (POLARITY-CHECK / POLARITY-FIT-BLIND).

## 1. The five indicator LEDs (D8, D9, D10, D11, D12)

Board-file facts (KiCad y-down, matches render orientation):

| Ref | Centre (mm) | pad1 (KiCad cathode) | pad1 net | pad2 net |
|-----|-------------|----------------------|----------|----------|
| D8  | 53.5, 53.0  | 52.562 (west)        | LEDPKK   | LEDPK    |
| D9  | 124.0, 26.5 | 123.062 (west)       | GND      | LEDVA1   |
| D10 | 124.0, 48.0 | 123.062 (west)       | GND      | LEDVA2   |
| D11 | 124.0, 70.0 | 123.062 (west)       | GND      | LEDVA3   |
| D12 | 107.0, 102.0| 106.062 (west)       | GND      | LEDVC    |

What I SAW in the crops: every one of the five has the standard KiCad LED silk — a
box with a doubled/thick vertical bar on the **west** edge (the cathode bar) and the
open/tail end east. That west side is pad 1, which is GND for D9-D12 and the K-named
net (LEDPKK) for D8. So **silk cathode mark and netlist cathode agree on all five**;
the board artwork is self-consistent.

What I could NOT see: the mounted 3D body is a symmetric white block with identical
yellow terminals on both ends — **no cathode glyph on the model at any zoom**. The
render therefore cannot discriminate rotation 0 from rotation 180 for the physical
part. The CPL ships 0.0 for all five, which per the twin report's POLARITY-FIT
finding (JLC numbers pad1=anode, opposite to KiCad) is the physically-correct
choice and the 180 pad-number fit is the trap. The render neither confirms nor
refutes that — it confirms only that the board side of the equation is right.
This stays on the order-preview human gate.

## 2. C1 / C2 — polarized 100uF/35V polymer caps on the pack input

Board-file facts: both at rot 90; C1 pad1 **VIN** at (26.5, 62.7) = **south** pad,
pad2 **GND** at (26.5, 57.3) = north pad. Same pattern for C2 (VIN 74.7 south,
GND 69.3 north). CPL rotation is 90.0 for both — the v1.4 defect value (270.0)
is gone.

What I SAW in the crop (twin_top, 6x): each can renders with a **red/dark stripe
segment on the NORTH half of the top face** and plain white on the south half; the
silk "+" glyph is printed just south of the south pad, and the silk outline's
chamfered corners are at the south end. So: silk + = VIN pad (correct per netlist),
and the model's marked stripe sits over the GND pad. On the KiCad CP_Elec model
convention (stripe = negative terminal), the model is oriented correctly.

What the render CANNOT settle: whether the *JLC-mounted physical part* at CPL
rotation 90.0 lands anode-on-VIN. The twin report flags exactly this
(POLARITY-FIT-BLIND: "no usable polarity marking on our footprint — ONLY the human
order-preview gate stands between this part and a 180deg reversal"). The render
shows the twin model consistent with the netlist; it does not prove JLC's rotation
convention for C2982822. Order-preview gate required.

## 3. CPL datum (the v1.6 anchor-vs-pad-centre defect)

I recomputed pad-array centres from the board file and compared to CPL Mid X/Y:

| Ref | KiCad anchor (mm) | Pad-array centre (mm) | CPL row (mm) | On datum? |
|-----|-------------------|------------------------|--------------|-----------|
| J1  | 30.0, 44.0 | 27.0, 40.4 (incl. the two edge NPTH slots at x=24) | 27.0, -40.4 | yes |
| J2  | 139.0, 38.0 | 140.3, 34.499 ((27.879+41.119)/2) | 140.3, -34.499 | yes |
| J3  | 139.0, 60.0 | 140.3, 56.499 | 140.3, -56.499 | yes |
| J4  | 139.0, 82.0 | 140.3, 78.499 | 140.3, -78.499 | yes |
| J5  | 120.0, 109.0 | 120.0, 107.5 ((115.68+124.32)/2, shield span) | 120.0, -107.502 | yes |

All five external connectors' CPL rows now sit on the pad-array centre, NOT the
anchor (anchors differ by 1.5-4.7 mm, matching the v1.6 defect magnitudes — so the
fix is real, not cosmetic). Twin report shows fit=0.00mm for all five.

Visually: J2/J3/J4 USB-A bodies sit squarely over their THT holes (yellow annulars
visible at the body corners), legs visible through the board in twin_edge_east, and
the bodies overhang the east board edge as a horizontal USB-A should. J5 USB-C body
is centred on its SMT lead row with all leads landing on pads. J1 XT60 sits flush
on the top surface in twin_edge_west with its blades over the two large slots.
Nothing hangs off its land.

## 4. Q1-Q6 — the bare-vs-twin discrimination test (the one the tooling lost)

Performed explicitly, same crop window, same mm coordinates, both images:

- **bare_top**: each Q location shows the naked land pattern — the yellow
  paste-cross drain paddle (~3.8x3.9 mm) with four grey finger pads west and four
  grey source/gate pads — i.e. exactly the "fake package" that fooled two lenses
  before. Q1 example: paddle centred ~ (34.4, 66.0) mm.
- **twin_top**: each Q location shows a **solid, uniform moulded body completely
  covering the paddle**, with a moulded **pin-1 dot**: Q1 dot SE (rot 180, pad1
  VIN at 38.67, 67.905 = SE — match), Q2 dot SE (rot 180, pad1 SW_A SE — match),
  Q3 dot NW (rot 0, pad1 CS_A at 73.33, 36.095 = NW — match), Q4 dot SE (match),
  Q5 dot NW (match), Q6 dot SE (rot 180, pad1 PMID SE — match). Q1/Q6 render
  darker grey (different LCSC part C2760089 vs C404363) — a body-colour difference,
  which itself is evidence these are distinct mounted models, not fallback geometry.
- Iso views show all six as raised 3D bodies with visible height above the board.

**Verdict: all six MOSFETs have mounted 3D bodies in v1.7; the comparison that
caught the earlier miss now passes.** Twin report agrees (MODEL-REG-OK, body on
courtyard, 0.04-0.06 mm).

Noted in passing from the twin report (machine channel, not render): PAD-GEOM
deltas on Q1-Q6 (our pad2<->5 span 5.08 mm vs JLC 5.40/5.45 mm, d = 0.31-0.37 mm)
and on D5 (0.42 mm) are flagged for datasheet adjudication, and **R12 (C2984354)
is FETCH-FAILED — the twin never verified that part at all**. Those need closing
by their own channel; the render cannot.

## Silkscreen

All safety legends present and legible in both twin_top and the higher-resolution
bare render:

- "PACK STILL LIVE AT XT60" and "LEDS DARK = SWITCH OFF" — both just south of the
  fuse/switch cluster, clear of pads. Nit: "LEDS DARK = SWITCH OFF" starts
  immediately after the "D1" refdes so it reads "D1 LEDS DARK = SWITCH OFF"; not a
  functional problem but slightly ambiguous at arm's length.
- "PACK ON" next to SW1; "9-12.6V XT60 IN"; "PROTECTED 3S + BAL-CHG ONLY".
- "J1 FUSE 10A MINI" at the fuseholder (reads as the required FUSE 10A legend).
- "+" and "-" on both the XT60 blades (silk beside J1) and C1/C2.
- "USB-A1 5V" / "USB-A2 5V" / "USB-A3 5V" plus "USB-A 5V CHG no-data" at each port;
  "USB-C 5V OK"; "USB-C 5A PI-ONLY NOT USB-PD"; "F2 VBUS 5A POLYFUSE".
- Board ID: "POWER-DIST BOARD - NOT A USB HUB" and "usb-hub-3s-v3".
- Refdes coverage: every part I crop-inspected has a visible refdes not overlapping
  its pads (D8-D12, C1/C2, Q1-Q7, R37/R38/R39/R41, C-series, U6-U12, J1-J5, F2, D2, D5).
  No overlapping legends observed anywhere at 6x zoom.

## What this render CANNOT establish

Stated plainly, because a previous review on this board closed a real finding with
a rationale instead of evidence:

1. **Physical LED polarity at CPL 0.0.** The 3D model is symmetric. The render
   proves silk/netlist self-consistency only. Whether JLC's feeder orientation for
   C2296/C2297 at rotation 0.0 puts the physical cathode on the GND pad can only be
   verified on the JLC order preview (or a datasheet-vs-JLC-footprint terminal
   adjudication). The twin report says the same.
2. **C1/C2 physical anode side.** The twin model looks right, but the model is our
   own render of our own transform — POLARITY-FIT-BLIND means no independent
   numbering-free channel exists for C2982822. Order-preview gate.
3. **Which physical XT60 blade is "+".** The render shows silk "+" on the north
   blade slot (VBAT pad at y=36.8 mm) — but blade identity vs the mating connector
   keying is a physical-part/footprint question invisible in any image.
4. **Solderability/geometry fit of the PAD-GEOM deltas** (Q1-Q6, D5) — a render
   shows bodies on courtyards, not whether JLC's larger land pattern matters.
5. **R12** — twin FETCH-FAILED, so nothing about that part is verified by the twin
   at all; my crop only shows a plausible 2-pad chip part present.
6. Anything on the bottom side is essentially bare (only vias/THT legs visible);
   no bottom-mounted parts exist to check.

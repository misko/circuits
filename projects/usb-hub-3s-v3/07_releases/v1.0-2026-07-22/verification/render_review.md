# Render Review — usb-hub-3s-v3

**Reviewer:** render-review (fresh context, no design intent assumed)
**Board:** `projects/usb-hub-3s-v3/04_kicad/usb_hub_3s_v2.kicad_pcb` (DRC-clean, routed)
**Ground truth for population:** `cpl.csv` — 100 parts, DNP-excluded, all top-side.
**Verdict: PASS** (2× P2 informational; no P0/P1 board defect surfaced by render.)

The review was done with no schematic/design context: read the renders as if
receiving the fab package cold. Board outline: 130.1 × 92.1 mm.

## Artifacts produced
| File | What it is |
|------|-----------|
| `cpl.csv` | Position file = ground truth of what is populated (100 parts, top-only). |
| `render_front.svg` / `.png` | Bare-Cu + Mask + Silk + Edge, front. |
| `render_back.svg` / `.png` | Bare-Cu + Mask + Silk + Edge, back (mirrored). |
| `model_top.png` / `model_bottom.png` | `kicad-cli pcb render` modeled view, top/bottom. |
| `assembly_front.pdf` / `assembly_back.pdf` | Silk + Fab + Edge per side. |
| `assembly_front-1.png` | Rasterized front assembly (for inline inspection). |
| `pcb_layers.pdf` | All Cu + Silk + Mask + Edge, one document. |
| `missing_models.txt` | Every CPL ref with no resolvable 3D body (see P2-A). |

## Review checklist

### Silkscreen legibility + every refdes present — PASS
- Programmatic check (`silk.py`): all **100/100** CPL refs carry a **visible**
  reference on a **silkscreen** layer. `MISSING_REF_TEXT = []`,
  `HIDDEN_REF = []`, `REF_NOT_ON_SILK_LAYER = []`.
- Front silk render is legible: C1–C50, R1–R29, U1–U12, Q1–Q5, D1–D4, L1–L2,
  RS1–RS2, F1, J1–J5, plus board title "usb-hub-3s-v3", value banners
  "PROTECTED 3S PACK 9–12.6V XT60 IN", "USB-A 5V 2A" ×3, "USB-C 5V/5A Pi".
- Back has **no** component silk (0 bottom-side parts) — consistent with CPL.

### Connectors: mate-direction / edge — PASS
- **J2/J3/J4** (USB-A, `KH-AF90DIP-112_Horizontal`): all at X≈139 on the right
  side, **rot 90**, shrouds reaching the right board edge (confirmed on
  assembly fab) — three ports facing the **same** direction (right). Correct
  horizontal top-mount USB-A geometry.
- **J1** (XT60, `XT60PW-M_EdgeTrim`): left side, body reaching the left edge —
  power input opposite the USB outputs. Sane.
- **J5** (USB-C, `TYPE-C-31-M-12_EdgeTrim`): bottom edge (3.0 mm center-to-edge),
  edge-trim opening at board edge — the Pi 5V/5A input. Sane.
- No connector faces inward; no mate-direction anomaly.

### Copper / mask defects — PASS (within render's resolving power)
- Front: coherent pours + traces, no visible slivers, mask-bridged shorts, or
  missing mask openings in the render.
- Back: a single large pour (power/ground) with mask-defined test/via pads;
  clean thermal reliefs, no obvious pour islands orphaned.
- Board is DRC-clean per the task hand-off; the render surfaces nothing that
  contradicts that.

### Footprint / rotation sanity — PASS
- Assembly fab layer shows courtyards, values, LCSC codes and pin-1 markers for
  all parts; three buck converter cells (U2/U11 controllers, Q2/Q3 & Q4/Q5 FET
  pairs, L1/L2 inductors, RS1/RS2 shunts) are mirror-symmetric top/bottom, and
  three identical USB-A output cells (U6/U4, U7/U5, plus U8/U9/U10) are
  consistent. Nothing rotated 90/180° off from its neighbours in a repeated
  cell.

## Findings (triaged)

### P2-A — Modeled 3D view has zero component bodies (environment gap, not a board defect)
`missing_models.txt` lists **all 100** CPL refs as "unresolved." Root cause:
the **KiCad standard 3D-model library is not installed on this review host**
(no `*.3dshapes`; `$KICAD10_3DMODEL_DIR` unset), so `model_top.png` /
`model_bottom.png` render as bare board. This is **not** a board defect:
- 0 parts have an **empty** model field; 0 parts are missing a footprint.
- Every ref points to a **well-formed standard** library path
  (Capacitor_SMD 45, Resistor_SMD 27, Package_SO 7, Package_TO_SOT_SMD 6,
  Connector_USB 4, Diode_SMD 4, Package_SON 3, Inductor_SMD 2,
  Connector_AMASS 1, Fuse 1). These resolve on any normal KiCad install / JLC.
- **Consequence:** body-level (component-collision / height / overhang) review
  could **not** be performed here. Re-run `kicad-cli pcb render` on a host with
  the KiCad 3D libraries to complete that pass before release sign-off.

### P2-B — Silk refdes overlap pads/copper in the dense converter cells (cosmetic)
In the U2/U11 buck areas several small-passive refdes labels sit over their
own pads / adjacent copper. All remain individually legible and the board is
DRC-clean, so this is cosmetic clipping at worst, not a placement error. Flag
only if a stricter silk-clearance gate is applied downstream.

## Method notes
- CPL is treated as ground truth: a bodiless render is a **missing model**, never
  an unpopulated part.
- Checks are property-based (visibility / layer / geometry via pcbnew), not
  golden-file, per the testing contract.

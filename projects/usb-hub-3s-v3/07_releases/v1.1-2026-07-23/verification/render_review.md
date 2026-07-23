# Render Review — usb-hub-3s-v3 **v1.1**

**Reviewer:** render-review (fresh context, no design intent assumed)
**Board:** `04_kicad/usb_hub_3s_v2.kicad_pcb` (v1.1, DRC 0/0/0, 130.1 x 92.1 mm)
**Population ground truth:** `06_build/fab/cpl_jlc.csv` — 115 parts.
**Date:** 2026-07-23
**Verdict: PASS** (0 P0/P1 board defect from render). 2 non-blocking order items.

## Artifacts (v1.1, regenerated)
| File | What |
|------|------|
| `render_front.png` / `render_back.png` | KiCad 3D model render, top/bottom. |
| `layers_front.svg` | F.Cu + F.Silk + F.Mask + Edge, front (silk review). |
| `../twin/twin_top.png` … `twin_edge_{west,east}.png` | JLC's OWN models mounted on our board (6 views) — what JLC assembles. |

## What the renders confirm

- **v1.1 eFuse cell present + placed by J5**: U13 (HTSSOP-20), Q6/Q7, R30-R36,
  C51/C52, C49/C50 clustered at the bottom-right beside the USB-C connector J5.
  Short EFINC/VBUSC power path from the buck-C output region to the connector.
- **Master-off SW1** (3-pin slide) placed centre, silk-labelled `SW1`.
- **Snubbers** R34/C53 (buck-A SW island) and R35/C54 (buck-C SW island) placed
  on the switch-node islands as intended.
- **Docs relabel (Fix 6) is on the silk and correct/honest**: `PROTECTED 3S +
  BAL-CHG ONLY`, `9-12.6V XT60 IN`, `USB-A 5V CHG no-data` (x3), `USB-C 5A Pi-ONLY
  NOT USB-PD`, `POWER-DIST BOARD - NOT A USB HUB`, `usb-hub-3s-v3`.
- **Connectors orient correctly** (twin, JLC models): XT60 (J1) nose overhangs the
  left edge, 3x USB-A (J2/J3/J4) and USB-C (J5) overhang their edges; polarity/keying
  as expected. Two 6.8uH inductors (L1/L2) modelled (JLC silk marking cosmetic).
- **No silk collisions / no body overlaps** apparent at full-board zoom; all refdes
  legible on visible silk (P-SILK-REF/FN PASS in policy_audit).

## JLC twin cross-check (see `../twin/twin_final.log`)
- twin exit 0; **88 OK / 232 checked**; all PAD-GEOM/PAD-MISMATCH criticals
  adjudicated (`03_src/rules/twin_adjudications.yaml`).
- New actives land-pattern VALIDATED: **U13 fit 0.01 mm**, **Q7 fit 0.08 mm**,
  Q6 = reused AON6354 merged-drain adjudication. All MODEL-REG-OK.
- 16 ROT-DB-SUGGEST + 6 POLARITY-CHECK are informational; polarity is machine-
  covered by P-POL. Verify rotations on the JLC preview (standard).

## Non-blocking order items (also in the pre-order list)
1. **SW1 pitch**: our 2.5 mm land vs JLC's mislabeled-VG4 model 2.0 mm — the twin's
   0.50 mm SW1 best-fit is exactly this pitch delta. VG6 drawing un-fetchable
   in-env; confirm on the JLC order preview (hand-solder part, jumper fallback).
2. **Snubbers populated**: R34/R35/C53/C54 render/CPL as populated (source intent is
   DNP-by-default but no `doNotPopulate` reached the board). Benign if fitted
   (2.2 ohm + 1 nF SW snubber); decide DNP-vs-populate before order.

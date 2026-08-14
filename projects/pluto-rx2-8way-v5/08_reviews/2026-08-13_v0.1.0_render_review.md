review_kind: render_review
subject: Pluto RX2 8-Way v5 v0.1.0 staged hardware release
date: 2026-08-13
reviewer: Codex independent visual, 3D, mechanical and assembly reviewer
independence: fresh exact-artifact review; no design-author verdict inherited
evidence_scope: staged hardware release v0.1.0-2026-08-13 only
source_commit: 798ef9812019efb9e9857332736926d099192a03
release: projects/pluto-rx2-8way-v5/07_releases/v0.1.0-2026-08-13
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-artifact render and assembly review

## Verdict

The exact staged board is **SOUND** through the visual, 3D registration,
component access, assembly-population, silk, copper-presentation and mechanical
lenses. I found no missing fitted model, visible body collision, reversed edge
connector, blocked mating interface, misleading port label or unexplained
placement. Production remains **HOLD** and ordering remains **DO-NOT-ORDER**
pending the real JLCPCB human preview/process echoes and physical first article.

## Evidence

| Evidence inspected | SHA-256 / result |
|---|---|
| Exact populated top | `6ee4390ae3335e50fc124c9a3d24a346851bf95831b9cf4bbab8289ca1c23ba8` |
| Isometric northwest / southeast | `c4e4f4db37a185d02f32221e7824979bb1ecfffcb520d1bfe4f609be6767ca9b` / `dbb4d3a677ebaaa78f61dca7f37badb1cddc010ce1f9c2bafbda733620a8f7a4` |
| East / west edge views | `140df9984cf487ba983bfd0b4e54fce76440745c6d69cd727978612de2129e28` / `21b61d5d7c635a07d91f45bb1ed091263cad80b3576a250e775ab20755d97f59` |
| Populated bottom | `24d852bdeb4bb8bb459f9beef98468edee313ddd407d2b9bc47808dc1ece45b9` |
| Courtyard overlay | `6722f19e183c20476d5ba8c3a51681a86a5fffd037cc44efa6d4e557f721d55d` |
| 3D STEP assembly | `646b00ffa7a942f281896cbc20987fb7e91dc68d429ef167676c27a37af29329` |
| PCB layer PDF / assembly PDF | `e7cbdb66b66e446cb3bc21694966bb911558af28c5178b8f70f33c9dd4973127` / `06a8d1443abfd1f9f831139ae797ae3e85d5be5aad8bfb3041a26d51f9158576` |
| Model coverage | 29/29 fitted footprints resolve; zero missing (`model_coverage.json` SHA-256 `5717a6073c58d969245f157ed27efd56e53c325dd436970b9877a3312c745677`). |
| Assembly coverage | 29/29 CPL placements are datum-graded, seven board-only refs are exempt, zero refs are unexplained, and the worst datum error is 0.0005 mm at J1 (`assembly_coverage.json` SHA-256 `e1899145fdd8fe61d97ca1a7b85e78b6e128b5ed335ca2de030baf6d799e3aa4`). |

## Visual and mechanical findings

- Five north-edge SMA connectors and two connectors on each side face outward.
  Their barrels and coupling-nut approaches are not blocked, and all signal and
  four ground posts register with their lands. The render's asymmetric-body
  offsets are expected for right-angle connectors rather than placement drift.
- The south-edge USB-C receptacle opens outward and is labelled `POWER ONLY`.
  The keyed 2x5 J11 SWD header is a real connector with unobstructed vertical
  cable access. Four corner mounting holes remain clear.
- U1-U4, D1, F1, C1-C6 and R1-R6 are present and seated on the intended top
  lands. The top/courtyard overlay shows no actionable body overlap or tool-
  access conflict. Ordinary through-hole tails below the board require normal
  trimming and enclosure/standoff clearance.
- Port labels `PLUTO RX` and `ANT1` through `ANT8`, the frequency legend,
  `USB-C POWER ONLY`, and `KEYED SWD J11` remain readable and correspond to
  the rendered interfaces.
- The inspected layer plots show the nine unbranched top RF routes, continuous
  inner ground planes, limited bottom low-speed routing, complete mask/paste
  content and a closed rectangular profile. Identical-looking inner planes are
  intentional symmetric ground layers, not a missing plot.

## Human gates retained

The render evidence does not replace the live order preview. JLCPCB must show
the nine SMA barrels and J1 opening outward; J11 pin 1/key orientation; D1
polarity; U1/U2 orientation; exact manufacturer-authoritative SMA, J11, D1 and
USB-C lands; and all intended fitted references. The twin's catalog-CAD
adjudications explain footprint-numbering and asymmetric-origin differences,
but do not waive uploader DFM acceptance.

Severity summary: P0/P1/P2 design findings **0/0/0**. No render-driven board
change is requested; the remaining work is external order validation and
first-article qualification.

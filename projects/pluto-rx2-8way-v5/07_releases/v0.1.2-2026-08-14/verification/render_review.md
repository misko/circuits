review_kind: render_review
subject: pluto-rx2-8way-v5 v0.1.2 corrected-twin render review
date: 2026-08-14
reviewer: Codex independent visual, 3D, mechanical and assembly reviewer
independence: fresh exact-artifact review; no design-author verdict inherited
evidence_scope: verification-only supersede v0.1.2-2026-08-14 only
source_commit: ba42fc9dba7f149f4187f50ef4fff697f0ed2a7a
release: projects/pluto-rx2-8way-v5/07_releases/v0.1.2-2026-08-14
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-artifact render and assembly review

## Verdict

The unchanged exact staged board is **SOUND** through the visual, 3D registration,
component access, assembly-population, silk, copper-presentation and mechanical
lenses. I found no missing fitted model, visible body collision, reversed edge
connector, blocked mating interface, misleading port label or unexplained
placement. Production remains **HOLD** and ordering remains **DO-NOT-ORDER**
pending the real JLCPCB human preview/process echoes and physical first article.

This review supersedes the v0.1.0/v0.1.1 render conclusion. Those archived
images shifted every C429844 model by (-1.27,+1.27) mm because the fallback
compared our single pad 2 with JLC's four pad-2 instances. Their claim that all
five posts visibly registered was unsupported. The corrected renderer instead
uses the independently verified unique signal-hole datum, pad 1 to pad 1 at
zero degrees, while retaining the failed whole-pattern fit as a finding.

## Evidence

| Evidence inspected | SHA-256 / result |
|---|---|
| Exact populated top | `9126106cef392be3e0b1e9cfedc046af44389c8c5d68c097852550351e8d0308` |
| Isometric northwest / southeast | `8eb130fe80a0909abd8db027ddf92e20c99593ca132ae1f31b042e5f9f20ce66` / `9f61a9926694d1188672898a1407de91800d73b318c1c1f1a719dcb3ac203c4c` |
| East / west edge views | `d705332b9d464b3afd14aa2a693a72f42375be2e560931389a99e3be8db64da6` / `7b23709c5cf518f0e935b9faef0047618d07a7a5a57851a5bd7e175a986383ca` |
| Populated bottom | `65be61903611a66ea9809b2c53adb6125af7c9ec39117917d4ec9414fb19df00` |
| Courtyard overlay | `8538d77442caf34c3ed349ea45673a4394b1c78fe30b5eac52ef39fc98769e5d` |
| Twin report / independent A-RENDER report | `8a6dfcab6521fa87dbd74f8b7af6c6e083c81c53138959945ff83729e32297b7` / `221e287734ec575fc61a40fa2377fd9e8a1f1a306ee2d1c2eac95eecc7ba73b3` |
| 3D STEP assembly | `646b00ffa7a942f281896cbc20987fb7e91dc68d429ef167676c27a37af29329` |
| PCB layer PDF / assembly PDF | `e7cbdb66b66e446cb3bc21694966bb911558af28c5178b8f70f33c9dd4973127` / `06a8d1443abfd1f9f831139ae797ae3e85d5be5aad8bfb3041a26d51f9158576` |
| Model coverage | 29/29 fitted footprints resolve; zero missing (`model_coverage.json` SHA-256 `5717a6073c58d969245f157ed27efd56e53c325dd436970b9877a3312c745677`). |
| Assembly coverage | 29/29 CPL placements are datum-graded, seven board-only refs are exempt, zero refs are unexplained, and the worst datum error is 0.0005 mm at J1 (`assembly_coverage.json` SHA-256 `e1899145fdd8fe61d97ca1a7b85e78b6e128b5ed335ca2de030baf6d799e3aa4`). |

## Visual and mechanical findings

- Five north-edge SMA connectors and two connectors on each side face outward.
  Their barrels and coupling-nut approaches are not blocked. The generated
  twin board reports `(0.000,0.000)` model offsets for J2-J10. A-RENDER
  independently measures J2/J3/J5-J10 against the pad-1 anchor within 0.779 mm
  centre delta and 0.048 mm outward excursion, below its 1.00-mm limits. J4 is
  explicitly unresolvable because H1/FID1 touch its pixel window; its analytic
  anchor is still zero and its corrected top/isometric views visibly agree
  with the same five-hole pattern as the eight measured instances.
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

The corrected render evidence does not replace the live order preview. JLCPCB must show
the nine SMA barrels and J1 opening outward; J11 pin 1/key orientation; D1
polarity; U1/U2 orientation; exact manufacturer-authoritative SMA, J11, D1 and
USB-C lands; and all intended fitted references. The twin's unique-pad anchor
explains only model registration; it does not waive the repeated-number
finding, the 0.10-mm JLC-versus-manufacturer drill delta, uploader DFM
acceptance or human orientation review.

Severity summary: P0/P1/P2 design findings **0/0/0**. No render-driven board
change is requested; the remaining work is external order validation and
first-article qualification.

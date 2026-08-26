---
title: USB Hub 3S v4 — fresh JLC twin/render review after C23 substitution
date: 2026-08-12
reviewed-by: Codex, independent manufacturing-twin/render lens
reviewer: Codex
context-given: Current named artifacts only; no prior review or stale overlay_SW1 used
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
input-sha256:
  04_kicad/usb_hub_3s_v4.kicad_pcb: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
  06_build/twin/twin_top.png: 755356fca7b4d11afd92d3363db51ff8883201cb2afcc2699830a55685a3a62d
  06_build/twin/twin_bottom.png: d32aabec7124bc110f13eaa7750cf4f994d1ca01e166c97dfd39806f19114bc9
  06_build/twin/twin_iso_nw.png: 7ba7aa0c9e51b4ff335d3363ed2a90428a663ce15b82dad98c620846a2952cdf
  06_build/twin/twin_iso_se.png: 2885dbb92eb7a52899f22f924d112ea14034fe33d3c5c747ad811aabdf7a0eb1
  06_build/twin/twin_edge_west.png: d739a5c43cbc3215983e226aa98bacb6dfae6dcf8a4b6606ba1e19eabca3c095
  06_build/twin/twin_edge_east.png: 0aa454598eb06f88b1909aa380bb78a2e0f9e7289681c8ef5aa8e68ba495cc9c
  06_build/twin/twin_bare_top.png: 896173dba7a3e535323ead8b7f294df10c6fb0b7a3928a508f3b505aac6110af
  06_build/twin/twin_bare_bottom.png: 2109230ca4f692eb58b2d2908a4103ea58cf336473bb04f3d8c5511cda4da11f
  06_build/twin/twin_report.csv: 33c31581a8a67fdb5daa36036070fd386a4b285fcd052c2309a3863349190f1c
  06_build/twin/missing_models.txt: eeab74ff5dd100df183039d4c935c9244345db930b0ebe929e43f1e8e860577a
  06_build/verification/twin_overlay.md: 2acad9df2097f77528ce2ed20e9977c9d08bef09008a35a98954e1390e51bf25
  06_build/fab/bom.csv: 3c9c7f77efa5fe145dfb16229064c9bcc894f15790a0b3132b086f332ca52b4f
  06_build/fab/cpl.csv: 67c9ab62e23f07d4a0e06fa425be23aba20c3787016e278072028ed8686490b2
  03_src/rules/assembly.yaml: e27bad9fbb6337124bbd524b415cde4a784325f5afbc962ad0bc57d0e91c9753
  03_src/rules/twin_adjudications.yaml: 61f14ba3313907449a1655309230b39d05b77062175712d7be87464cb95041e3
  02_parts/16SVPF180M/part.yaml: b288f560d6878ebdae6379dba54d478335223c42fa6d02b5504cc19ca0d25ff4
  06_build/twin/twin_overlay_top.png/overlay_C17.png: c34e30f0b4185e166bf46766259f0adf18f2395acb138b1e950a7c92acc6ee9f
  06_build/twin/twin_overlay_top.png/overlay_C18.png: 851fdfdb60615219294bc8e7e0456552627e83c1d8e548d8bd1e3f7b358dfc78
  06_build/twin/twin_overlay_top.png/overlay_C19.png: ba555e172034276295b6e2c19154574c1f28997d4bc485738f86667d96b6148f
  06_build/twin/twin_overlay_top.png/overlay_C22.png: 369a05004c95dd1e4b2e556fd369403f3b4c1e1ac1a2043357420620f04babc6
  06_build/twin/twin_overlay_top.png/overlay_C23.png: 3408240bcb833c0e80f849682670b1cad0564e22a7fb98dad9b9071602adbc09
  06_build/twin/twin_overlay_top.png/overlay_D1.png: 4ceea64a8d87f83dc3ba1a2e05995b762324223e960fdfe6be15090ac3eedf6c
  06_build/twin/twin_overlay_top.png/overlay_D5.png: 4bb22157b8aced9897bf47491410a52363b74782413744d8273a2ca17c58395e
  06_build/twin/twin_overlay_top.png/overlay_Q1.png: fc14db98b33256f40540809673cefc19bb103cfdb215790015920c1b47dd4f70
  06_build/twin/twin_overlay_top.png/overlay_U3.png: b26478995c102dad1a6930e18cbeebfb60dba79e268f81395d1850aea1e39eca
  06_build/twin/twin_overlay_top.png/twin_top_courtyard_overlay.png: c319b5648f344c2c268325f434aa8c0e6495c2eeb9dc47133596d55b40f519c2
---

# Verdict

This bounded, fresh review is complete. The current render evidence is **SOUND** for the C23 substitution and for obvious global manufacturing-twin defects. C23's former missing-CAD/render blocker is resolved: the current twin contains and measures an exact-code `C136277` body, and no current view shows it reversed, rotated incorrectly, displaced, floating, or physically implausible.

The order verdict remains **DO-NOT-ORDER** because a live JLC upload preview was not among the immutable inputs. This local A-RENDER pass cannot authorize an order or replace the allocation, polarity, rotation, and body-registration checks in that preview.

## Bound scope and method

I inspected the current top, bottom, both isometrics, both edge elevations, bare top and bottom, the current full-board courtyard overlay, and the current C23 crop. I also cross-checked the PCB, BOM, CPL, twin report, missing-body report, overlay measurements, assembly rules, adjudications, and the C23 dossier bound in the header.

`06_build/twin/twin_overlay_top.png` is a directory in this artifact set, not a single PNG. Its ten current PNG children are individually bound above. No stale `overlay_SW1` artifact and no prior review was consulted. This review does not redesign the board, refetch catalog data, or broaden into topology.

## C23 substitution

| Check | Current evidence | Finding |
|---|---|---|
| Identity | BOM: `C23`, `180uF`, `16SVPF180M`, `C136277`; dossier: Panasonic conductive-polymer aluminum can, 16 V, D6.3 x 5.9 mm | Exact substituted identity is internally consistent. |
| Side and rotation | PCB placement `(97, 101.5)` on `F.Cu` at 180 degrees; CPL `(97.0, -101.5)`, `top`, `180.0` | PCB and CPL agree on top side and 180-degree placement. |
| Polarity | Dossier fixes pad 1 as positive. At the placed 180-degree orientation the footprint `+`/pad-1 side is right; the rendered can's dark polarity sector is left. `twin_report.csv` independently records `POLARITY-FIT-OK`, with the marking channel and pad fit agreeing at pad 1 (margins 1.03/0.25 mm). | No reversal is visible; the body marking is opposite the positive pad as expected. |
| CAD rotation/fit | Twin report: `fit=0.03mm`, JLC offset 0, database/model rotation 0 degrees, source `lcsc`; `MODEL-REG-OK`, body-on-courtyard delta 0.00 mm | No hidden model transform is needed beyond the board/CPL placement. |
| Image registration | Overlay: 0.137 mm measured centre delta, 0.271 mm outward metric, edge deltas `-0.48,-0.27,+0.48,-0.00` mm, 3,936 body pixels, 0.000 mm courtyard excursion | Expected and measured body boxes agree; the body is centered and remains inside its courtyard. |
| Body and seating plausibility | Top/crop show a 6.3 mm-class can spanning the intended lands; both isometrics and edge views show it seated and at a height comparable with the other 6.3 mm cans | D6.3 x 5.9 mm envelope is visually plausible; no float, sink, side swap, or implausible height is evident. |

## Global render review

- The top and both isometrics show a coherent top-side population. The bottom view is unpopulated as intended. No obvious mirrored body, wrong-side placement, gross 90/180-degree error, body-to-land displacement, board-edge collision, or unexplained body-height outlier is visible.

- The two edge elevations show bodies seated at the board plane. Expected connector/shield pin protrusions are visible, but there is no obvious floating or buried package.

- The current overlay gate is `a-render_verdict: PASS`: 36 of 70 expected-body refs are image-measured, 34 are explicitly below or obstructed by the stated resolution method, and zero resolvable refs were omitted. All measured refs are within the 1.00 mm centre/excursion tolerances. That is a bounded render-faithfulness result, not proof of every package's manufacturing allocation.

- Existing named exceptions remain visible rather than silently waived: Q1 uses its adjudicated JLC-own transform and still requires upload-preview rotation confirmation; D1 has no usable independent CAD polarity mark and still requires upload-preview cathode confirmation. The review found no new body/side/rotation/edge-height defect in the current imagery.

## Missing-body disposition

The current population set is 70 CPL placements plus five declared manual-install bodies, with **71/75 bodies mounted**. All 70 machine-placement refs therefore have a rendered body; C23 is no longer a missing-body exception. The four unmounted bodies are only `J1`, `J2`, `J3`, and `J4`, all excluded from the CPL and designated for manual hand soldering.

The overlay report separately names six refs with no exact JLC model: manual connectors `J1`-`J4`, plus `R24` and `R5`. The two resistors are unpolarized standard 0603 placements with documented controlled-library `FETCH-FAILED` adjudications and retained render bodies; they are not NO-BODY omissions. The four connector omissions are honest limits of the twin, not evidence that connectors will be JLC-placed.

## Resolved blocker versus remaining obligations

**Resolved now:** the old C23 missing-CAD blocker is closed by the present exact-code `C136277` model, current report, measured overlay, and human view review. No additional catalog fetch is needed for this bounded decision.

**Still required before releasing an order:** inspect the actual JLC upload preview and confirm exact allocation plus polarity/rotation/body registration, including C23, D1 cathode, Q1 rotation, and the already documented transform-sensitive packages. Do not infer that live preview from these local renders.

**Still required at first article/manual assembly:** `J1`-`J4` have no exact rendered bodies. Hand-solder the specified connector parts and physically verify seating, board-edge alignment, mating access, terminal/shell retention, every joint, and continuity/short behavior. The other declared manual parts (`F1` and `SW1`) retain their assembly-rule inspections. These are prototype acceptance duties and do not reopen the resolved C23 CAD issue.

Final disposition: **SOUND / DO-NOT-ORDER**, complete on the available bounded evidence.

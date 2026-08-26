---
title: USB Hub 3S v4 — final-population JLC twin/render delta review
date: 2026-08-12
reviewed-by: Codex, independent manufacturing-twin/render lens
reviewer: Codex
context-given: Bounded freshness and denominator-split recheck after twin gate regeneration
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
prior-review-sha256: cf3ece876f67fa909c69cf3975416748ec7f346b1482fd20d369be97506114c7
input-sha256:
  04_kicad/usb_hub_3s_v4.kicad_pcb: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
  06_build/twin/twin_top.png: 755356fca7b4d11afd92d3363db51ff8883201cb2afcc2699830a55685a3a62d
  06_build/twin/twin_bottom.png: d32aabec7124bc110f13eaa7750cf4f994d1ca01e166c97dfd39806f19114bc9
  06_build/twin/twin_iso_nw.png: 507342eb7ba84c0f559bd030878fd6e9dedbac49429fe4d759a2b4e023465f3c
  06_build/twin/twin_iso_se.png: 9e89a13591cde6769bfa168915f131b6f1ccab320b52cc1b9eac0ee36ca56b76
  06_build/twin/twin_edge_west.png: c6f1ac0ca1156daa3ad78bddcc252cb40a24253814c4ced0ade58a6305719723
  06_build/twin/twin_edge_east.png: 547e369619923e5fe84d9cfcf07f3a4c238584641f4c058644070eef6092f084
  06_build/twin/twin_bare_top.png: 896173dba7a3e535323ead8b7f294df10c6fb0b7a3928a508f3b505aac6110af
  06_build/twin/twin_bare_bottom.png: 2109230ca4f692eb58b2d2908a4103ea58cf336473bb04f3d8c5511cda4da11f
  06_build/twin/twin_report.csv: 33c31581a8a67fdb5daa36036070fd386a4b285fcd052c2309a3863349190f1c
  06_build/twin/missing_models.txt: ffe2362c6e7082c279fbdcd616d3cfe7f82af0049cbec439b0a3fd1c34530ebc
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

The regenerated final-population evidence remains **SOUND**. The new denominator split improves the precision of the NO-BODY gate and does not change the prior design conclusion: **all 70 contractual JLC CPL placements have bodies (70/70, PASS)**. The aggregate `71/75` result combines that complete machine-placement set with five manual-body checks; its four gaps are only the declared manual connectors `J1`-`J4`.

The order verdict remains **DO-NOT-ORDER**. Nothing in this local regeneration supplies the live JLC upload preview, resolved-BOM echo, or preview polarity/rotation/body-registration checks required before payment. The four manual connector model gaps remain first-article/manual-assembly obligations, not sourcing blocks and not failures of the 70-ref CPL population.

## Freshness and byte-identity delta

The prior review was read only as a checksum baseline and was not edited. The board, BOM, CPL, rules, C23 dossier, twin report, and overlay report retain their prior hashes.

| Current artifact group | Comparison with hashes bound in the prior review | Disposition |
|---|---|---|
| `twin_top.png`, `twin_bottom.png` | Byte-identical | Current top-side population and empty bottom-side conclusion persist exactly. |
| `twin_bare_top.png`, `twin_bare_bottom.png` | Byte-identical | A-RENDER subtraction references persist exactly. |
| All nine current per-ref overlay crops and `twin_top_courtyard_overlay.png` | Byte-identical | Overlay measurements and C23 registration/polarity crop persist exactly. |
| `twin_report.csv`, `twin_overlay.md` | Byte-identical | C23 fit/polarity/model-registration evidence and `a-render_verdict: PASS` persist exactly. |
| `twin_iso_nw.png`, `twin_iso_se.png` | **Not byte-identical**; current hashes are bound above | Both regenerated current images were freshly inspected. They show the same coherent top population and no new mirrored, wrong-side, gross-rotation, float, or implausible-height defect. |
| `twin_edge_west.png`, `twin_edge_east.png` | **Not byte-identical**; current hashes are bound above | Both regenerated current images were freshly inspected. Bodies remain seated at the board plane, with no new float, burial, edge collision, or unexplained height outlier. |
| `missing_models.txt` | Intentionally changed from `eeab74ff...` to the current hash bound above | Adds the contractual/manual denominator split described below; named missing refs are unchanged. |

Accordingly, it would be incorrect to claim that every render is byte-identical to the prior review. Top, bottom, bare views, and overlays are identical; the four perspective/elevation views are fresh bytes and independently pass the bounded visual recheck. No design byte changed.

## Final population grading

| Population | Mounted | Grade | Meaning |
|---|---:|---|---|
| Contractual JLC CPL | **70/70** | **PASS** | Every ref JLC is instructed to place has a resolved, mounted render body. There is no machine-placement NO-BODY gap. |
| Declared manual-body checks | **1/5** | BOUNDED GAP | The four unmounted bodies are exactly `J1`, `J2`, `J3`, and `J4`; these refs are excluded from the CPL and hand-soldered. |
| Aggregate visualization | **71/75** | INFORMATIVE | This finished-product visualization denominator combines the complete 70-ref CPL set with the five manual-body checks. It must not be misreported as 4 missing JLC placements. |

The split resolves the earlier ambiguity in the aggregate headline. It does not waive or conceal the connector omissions: `J1`-`J4` still have no exact render bodies, so the twin cannot prove their physical seating, board-edge exit, retention, or mating access.

## C23 and global conclusions

C23 remains fully covered. The C23 BOM/CPL identity, 180-degree top placement, `POLARITY-FIT-OK`, 0.03 mm CAD fit, `MODEL-REG-OK`, 0.137 mm image centre delta, 0.000 mm courtyard excursion, top view, and per-ref overlay are unchanged. Its old missing-CAD blocker stays resolved.

The current top, bottom, isometrics, edges, and full overlay show no new obvious body, side, rotation, registration, edge-height, or collision defect. Existing order-preview duties for C23, D1 cathode, Q1 rotation, and other documented transform-sensitive packages remain separate from this local render gate.

At first article, hand-solder the specified `J1`-`J4` connectors and verify seating, edge alignment, mating access, terminal/shell retention, joints, and continuity/short behavior. The other declared manual parts retain their assembly-rule inspections. These duties neither reduce the contractual 70/70 CPL body grade nor reopen the resolved C23 finding.

Final disposition: **SOUND / DO-NOT-ORDER**, complete on the current bounded evidence.

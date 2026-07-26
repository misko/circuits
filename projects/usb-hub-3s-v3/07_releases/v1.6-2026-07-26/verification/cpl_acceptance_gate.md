# CPL ACCEPTANCE GATE + COPPER-IDENTITY PROOF — v1.5-2026-07-25

The fix-claim evidence the 07_releases contract requires: the measurement that
proves v1.5 changed EXACTLY what it says it changed, by a method able to
falsify it. Produced 2026-07-25 against the UNCHANGED sealed board
04_kicad/usb_hub_3s_v2.kicad_pcb.

## 1. CPL diff — the gate: EXACTLY FOUR changed cells, no more, no fewer

```
$ diff v1.4-2026-07-23/fab/cpl.csv v1.5-2026-07-25/fab/cpl.csv
2c2
< C1,C2982822,CP_Elec_6.3x7.7,26.5,-60.0,top,270.0
---
> C1,C2982822,CP_Elec_6.3x7.7,26.5,-60.0,top,90.0
13c13
< C2,C2982822,CP_Elec_6.3x7.7,26.5,-72.0,top,270.0
---
> C2,C2982822,CP_Elec_6.3x7.7,26.5,-72.0,top,90.0
55c55
< J1,C98732,XT60PW-M_EdgeTrim,30.0,-44.0,top,90.0
---
> J1,C98732,XT60PW-M_EdgeTrim,30.0,-44.0,top,0.0
68c68
< Q7,C78284,SOT-23,104.0,-96.0,top,270.0
---
> Q7,C78284,SOT-23,104.0,-96.0,top,180.0
```

| ref | part | v1.4 | v1.5 | why |
|---|---|---|---|---|
| **C1** | C2982822 100uF/35V POLARIZED polymer | 270.0 | **90.0** | **P0** — 180deg reversed across the 3S pack; pad-fit rms 0.030mm @0 vs 5.370mm @180, and JLC's own silk draws a crossed "+" glyph over its pad 1 (audit PCBA-1) |
| **C2** | C2982822 100uF/35V POLARIZED polymer | 270.0 | **90.0** | same part, same defect |
| **Q7** | C78284 BSS138 (Q6 gate inverter) | 270.0 | **180.0** | 3-pad asymmetric fit rms 0.062mm @180 vs 1.95mm @270 (audit PCBA-3) |
| **J1** | C98732 AMASS XT60PW-M | 90.0 | **0.0** | 4-pad fit rms 0.0000mm @270 offset; 12.0mm out at 90 (audit PCBA-2) |

Rows in each CPL: 108 placements.
Changed CELLS: 4.   Changed ROWS: 4.   Added/removed rows: 0.
Every other field of every other row is byte-identical.

## 2. BOM diff — identical except the MPN column

```
v1.4 rows: 43   v1.5 rows: 43
identical ignoring the MPN column: True
v1.5 rows with MPN populated: 43/43   (v1.4: 0/43)
```

## 3. NO COPPER CHANGE — proven by RE-EXPORT, not by copying

The fab package was RE-EXPORTED from the unchanged board on 2026-07-25 into
06_build/fab/, and the freshly-plotted gerbers + drills were compared
member-for-member against v1.4's sealed zip. 13/13 members present in both.
Per member the ONLY differing lines are the plot's own timestamp comments
(`%TF.CreationDate`, `G04 Created by KiCad ... date`; drill files:
`; DRILL file KiCad ... date`, `; #@! TF.CreationDate`) — 4 diff lines
(2 removed + 2 added) on every one of the 13. With those comment lines
stripped, all 13 members hash IDENTICALLY:

```
  MATCH  3320842ea5b53cca9751dc7896bffee0b2f7505c9772641ecbd452b7828e65a3  usb_hub_3s_v2-B_Cu.gbl
  MATCH  73506ac6df753bbbb5d985c1d05e3357985e6a154b766b03dfe7961954be444e  usb_hub_3s_v2-B_Mask.gbs
  MATCH  616c1e8cbab24a0316c12d8ab7ab3f321fb8757529dec9cf3cd2bf61e26461a1  usb_hub_3s_v2-B_Paste.gbp
  MATCH  9f366635aa1150ddac4c05767b26e400185b2373bf16250955552893d649c29f  usb_hub_3s_v2-B_Silkscreen.gbo
  MATCH  6e5714ae83b249ff420e953d80c1e8de01a25cbef54e91f3ee37979489b730f7  usb_hub_3s_v2-Edge_Cuts.gm1
  MATCH  86d051c6f07a568241e294f0633d20090b169e1f6b70e2786ef498520cb8f3ed  usb_hub_3s_v2-F_Cu.gtl
  MATCH  d225c02d55afd10cc1085192ec16a2cbe1b5142745f52eb24753e473177480c6  usb_hub_3s_v2-F_Mask.gts
  MATCH  fccb3856c2274397a9bc8ac01bff6c5f114e8acc0672b91a0f0ef225612097f5  usb_hub_3s_v2-F_Paste.gtp
  MATCH  0fdaedbf28c342a92399aff44888e5d58bfb6cf726237b0b09fa7dff623adfef  usb_hub_3s_v2-F_Silkscreen.gto
  MATCH  eaeaec29f0ecd85d91fb8ec7b86a1366ee72615ad6adad4454e868ef28b6bdbf  usb_hub_3s_v2-In1_Cu.g1
  MATCH  d428a9d95ce2f75cac9b215275b6e6a3b5f5bc7f811c4db9fbc15b010f887905  usb_hub_3s_v2-In2_Cu.g2
  MATCH  ebb82df4ec0d4b88113d3d4028c80a506417a7093bd0d58010f086868dcd6e5c  usb_hub_3s_v2-NPTH.drl
  MATCH  35ebff9082ed1beb6ec49ae6ba235ebe025479441e27e11668ac365b9f526bd1  usb_hub_3s_v2-PTH.drl
```

Because the plot is byte-stable apart from its own timestamp, v1.5 SHIPS
v1.4's gerber zip and drill files VERBATIM, so the sha256 identity claimed
in the MANIFEST is literal and checkable:

```
  IDENTICAL  fab/usb_hub_3s_v2_gerbers.zip
             f51344e45ddd2d848b86a0653ddc2e7b734cb3d588c7d1fdbfa57125f6371009
  IDENTICAL  fab/usb_hub_3s_v2-NPTH.drl
             976841faeca24bc221bc20291727979ce1a9a31a19e1b5cce4427fc75161bf7f
  IDENTICAL  fab/usb_hub_3s_v2-PTH.drl
             03b93154865c75fa5da7d7293fcc5e26fd4a1f7f04db3e0ad9d917b8c1be0a00
```

pdf/ source/ 3d/ — all 17 files sha256-identical to v1.4 (sorted find|sha256sum diff empty):

```
  460f524e0ceef07c4de55c9f02cafc77666600b20e9a6da71ced65ada1dc06aa  3d/usb_hub_3s_v2.step
  86c72ddce9114c65f21d951566b57965116f89a0110a8db4f6fc0883df08667d  pdf/assembly_back.pdf
  36337e5a9ae92bbbf6138f462f9b39db63ab176027e671792822c6445025afd7  pdf/assembly_front.pdf
  d93bcbb638c52cc45627aa0c156fea29401304656587130186d8dd5218de795e  pdf/pcb_layers.pdf
  25bc11180f722441887265d1067c12765fa9fcf3f8136426565275215ca237b9  pdf/schematic.pdf
  4fb72085bfef7740b599059cbb2d03d44e8c9bf26688150809c6f3965db52d0b  source/Button_Switch_THT.pretty/SW_Slide_1P2T_CK-12D07.kicad_mod
  17ad9dd8e393812b29a79de6e3e75d63086f719c9990b2bf35b1a6bbba4d968f  source/fp-lib-table
  9ec04bfc9cb3a6bd46b4a83fcb755df367c87c5a45c229f10228b0290742cf0e  source/usb_hub_3s.pretty/KH-AF90DIP-112_Horizontal.kicad_mod
  c4713b4feda0c78c326ea1eab79963c4189602f14052d5063644839de08c6761  source/usb_hub_3s.pretty/L_YJYCOIN_YSPI1770Y.kicad_mod
  544d1589cf635e9c812c843e731f4d836c047f13cb982187d3ffc6edab444922  source/usb_hub_3s.pretty/TYPE-C-31-M-12_EdgeTrim.kicad_mod
  f4e2f40f3f169033ae880a684f82a162bce4d10ae47529c36edb3ca517a80103  source/usb_hub_3s.pretty/XT60PW-M_EdgeTrim.kicad_mod
  8d093512c797582c6c667063c64483df819da680ab98741a9e9fadcdcfa7789f  source/usb_hub_3s_v2.kicad_dru
  e1be432c704fe44a721fa29d964258571cbaa5a8d167924e143b2f9bfd02aefa  source/usb_hub_3s_v2.kicad_pcb
  0cdc372fb884f8b376ac0dc73a4fce7402b2af13f4899abc5113d95497bcb4d0  source/usb_hub_3s_v2.kicad_pro
  6fd6301fab318e85ef9dc00c0ba2ec39adc0d2a47d6ece887243cdfe2e9127bc  source/usb_hub_3s_v2.kicad_sch
  00ac54858255f8b49fb55be6a3d1d2b33fe78ba42167881a019266af9dbf623a  source/usb_hub_3s_v2.net
  a734d57441f5fea3f1f4ccfc67fe2ea0400ee0949a0f641489c3beb7ba480f47  source/usb_hub_3s_v2.tsx
```

Total payload files sha256-identical to sealed v1.4: **20** (3 fab + 17).

## 4. Independent electrical re-gates on the same unchanged board

```
DRC   (kicad-cli pcb drc --severity-all --refill-zones --schematic-parity):
      0 violations / 0 unconnected / 0 schematic-parity issues   -> verification/drc.json
ERC   (kicad-cli sch erc --severity-all): 0 ERRORS.
      204 warnings, ALL of type lib_symbol_issues — expected on a
      tscircuit-native schematic (ADR-0002), no symbol library to compare
      against. Sealed v1.3 shipped 314 warnings of the same + 
      footprint_link_issues classes.                             -> verification/erc.json
PARITY vs the sealed v1.4 netlist (node-for-node, parsed both sides):
      110 components / 67 nets / 347 nodes on BOTH
      component set identical .... True
      net-name set identical ..... True
      nets differing node-for-node 0
```

## 5. Rotation evidence is INDEPENDENT of the tool that produced the defect

Canon M1. Every rotation number above was re-derived from the BOARD plus
JLC's OWN cached footprint using the operator VERIFIED against pcbnew
(`pad.GetFPRelativePosition()` vs `pad.GetPosition()`), NOT from
`jlc_twin`'s `jlc_offset` — which was negated by a handedness bug and is
the reason three of the four defects existed.

The twin was then re-run with the FIXED operator as a SECOND, independent
confirmation: **0 ROT-DB-SUGGEST over 231 checks**, i.e. every fitted
offset now agrees with the resolved value for every part on the board, and
the three per-LCSC rows this release depends on report:

```
  C2982822,C1,OK,fit=0.03mm jlc_offset=0 db=0.0 src=lcsc
  C2982822,C2,OK,fit=0.03mm jlc_offset=0 db=0.0 src=lcsc
  C78284,Q7,OK,fit=0.08mm jlc_offset=180 db=180.0 src=lcsc
  C98732,J1,OK,fit=0.00mm jlc_offset=270 db=270.0 src=lcsc
  C2982822,C1,MODEL-REG-OK,body on courtyard (0.00mm)
  C2982822,C2,MODEL-REG-OK,body on courtyard (0.00mm)
  C78284,Q7,MODEL-REG-OK,body on courtyard (0.02mm)
  C98732,J1,MODEL-REG,"body center 14.3mm off courtyard, area ratio 0.87 -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=0 (authoritative); body asymmetric (4.1mm bbox-center offset) so this metric is unreliable. VERIFY leads sit on pads visually; if correct, adjudicate as a false alarm with NO rotation override"
```

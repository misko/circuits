# Stage 1 part and sourcing selection — 2026-08-10

## Selection result

| function | selected part | live catalog identity | selection reason |
|---|---|---|---|
| USB-A buck | TPSM63610RDFR | C7125816 | 8A rated/10A peak integrated module; covers 6A/7.5A bank |
| Pi buck | TPSM63604RDLR | C5219289 | independent 4A integrated module for 3A rail |
| Type-C source | TPS25810RVCR | C473913 | Rd attach, 3A Rp advertisement, switched/discharged VBUS |
| USB-A port switches | TPS2557DRBR x3 | C130056 | <=35mohm max and accurate programmable current limit |
| USB-A signatures | TPS2513ADBVR x2 | C473910 | BC1.2 DCP plus legacy charge signatures |
| USB-A ESD | USBLC6-2SC6 x3 | C7519 | connector-side dual-line protection |
| Type-C CC ESD | TPD2EUSB30DRTR | C97502 | 6V-capable two-line IEC ESD clamp at the receptacle |
| reverse polarity | DMP3013SFV-7 | C264098 | exact active -30V P-FET stocked by both pools; 9.5mohm max at -10V |
| gate clamp | BZT52C12-7-F | C124196 | exact Diodes ordering code bounds P-FET VGS |
| input TVS | SMBJ15A | C83846 | 15V stand-off, 24.4V max 10/1000us clamp |
| input damping | 35TZV100M6.3X8 | C88744 | 100uF/35V, <=340mohm input resonance damper |
| Type-C receptacle | USB4105-GF-A | C3020560 | 5A collective VBUS, separate CC1/CC2, manufacturer drawing |
| USB-A receptacles | USB1130-15-A x3 | C5815149 | 3A and <=30mohm contact rating |
| battery input | Phoenix Contact 1715022 | C3817933 | 17.5A two-position terminal for an XT60 bare-wire pigtail |
| fuse holder | Keystone 3568 | C5249699 | board-mounted MINI blade holder; fuse is user-fit |
| master enable switch | EG1218 | C273394 | exact E-Switch SPDT for the low-energy enable bus |

The first dated catalog probe reported JLC/LCSC PASS 15/15, but the required
independent authorized-supplier join then failed six lines. That false-green
intermediate state is preserved in `stage1_supplier_report_initial.*`. Selection
was backtracked before schematic capture: six exact MPNs changed and Type-C CC
ESD was added. The final JLC/LCSC probe reports PASS 16/16, and the dated
two-source matrix records JLC/LCSC plus Mouser for 15 lines and JLC/LCSC plus
DigiKey for USBLC6-2SC6. These observations are not order promises: catalog
stock does not guarantee JLC assembly allocation. The JLC uploader and order-day
substitution review remain the final authority.

## Compared alternatives

- One TPSM63610 for the whole board was rejected: 9A continuous/10.5A peak port
  demand exceeds its 8A/10A rating.
- Reusing v3's dual LM5116 bare-controller cells was rejected on total project
  complexity: each requires external MOSFETs, gate-charge/current-sense proof,
  inductors, compensation and a substantially larger critical layout.
- An integrated TPS2511-style USB-A charge switch was considered, but its higher
  maximum path resistance consumed delivery margin. TPS2557 plus TPS2513A costs
  more placements but keeps current-limit accuracy and connector voltage auditable.
- Static Type-C Rp resistors with permanently live VBUS were rejected because a
  source must detect Rd before applying VBUS and remove it after detach. TPS25810
  implements the required source state machine without USB-PD.
- AON6403, Panasonic EEEFK1V101P, HRO TYPE-C-31-M-12A, AMASS XT60PW-M and XKB
  SS12D07VG6-087 all cleared the first JLC/LCSC probe but failed the independent
  authorized-pool threshold. They were not allowed to leak into the schematic.
- A base-name `BZT52C12` selection was rejected because different manufacturers
  publish that same generic type string. The selected identity is the exact
  Diodes `BZT52C12-7-F` order code.
- The direct PCB XT60 was replaced with Phoenix Contact 1715022. It accepts the
  stripped/ferruled conductors of a user-supplied XT60 pigtail, is rated well
  above the 7.2A design trunk, and is independently catalogued. Because it is
  not keyed, large BAT+/BAT- silk and the reverse-polarity FET remain mandatory.

## Primary sources

- [TPSM63610 product/datasheet](https://www.ti.com/product/TPSM63610)
- [TPSM63604 product/datasheet](https://www.ti.com/product/TPSM63604)
- [TPS25810 product/datasheet](https://www.ti.com/product/TPS25810)
- [TPS2557 product/datasheet](https://www.ti.com/product/TPS2557)
- [TPS2513A product/datasheet](https://www.ti.com/product/TPS2513A)
- [GCT USB1130 manufacturer drawing](https://gct.co/files/drawings/usb1130.pdf)
- [GCT USB4105 manufacturer drawing](https://gct.co/files/drawings/usb4105.pdf)
- [Diodes DMP3013SFV datasheet](https://www.diodes.com/_files/datasheets/DMP3013SFV.pdf)
- [Diodes BZT52C2V0-BZT52C51 datasheet](https://www.diodes.com/_files/datasheets/ds18004.pdf)
- [Rubycon TZV datasheet](https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/TZV.pdf)
- [Phoenix Contact 1715022 product record](https://www.phoenixcontact.com/en-gb/products/printed-circuit-board-terminal-mkds-15-2-1715022)
- [E-Switch EG1218 product record](https://www.e-switch.com/product/eg-series-subminiature-slide-switch/?part-number=EG1218)
- [TI TPD2EUSB30 datasheet](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf)
- [Littelfuse SMBJ datasheet](https://www.littelfuse.com/assetdocs/littelfuse_tvs_diode_smbj_datasheet.pdf)
- [Keystone 3568 product data](https://www.keyelco.com/product.cfm/product_id/306)
- [JLC PCB assembly FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs)

Video/tutorial content was not used as a rating authority: for immutable pins,
limits, USB state behavior and fabrication options, the current standards,
manufacturer datasheets/application layouts and JLC's published process are the
controlling sources. Tutorials remain useful later for technique cross-checks,
but cannot supersede those primary artifacts.

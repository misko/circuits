subject: pluto-rx2-8way-v4 344dfba05f7160b99b56dc9722cf8be72e846c7e
date: 2026-08-01
reviewer: render-review (fresh independent PDF, assembly, and population lens)
context-given: full-tree
design_verdict: SOUND
order_verdict: ORDER

# Fresh independent final render and assembly-document review

render_review_verdict: PASS
p0_count: 0
p1_count: 1
p2_count: 1

## Frozen subject binding

| artifact | exact identity |
|---|---|
| source commit | `344dfba05f7160b99b56dc9722cf8be72e846c7e` |
| board | SHA256 `4a5e69d474f5354346edbb64683edb3c69946b9ad437c1ddf49e4b126fc7f14a` |
| fabrication archive | SHA256 `4f1d2fea756f86220cb8c8dc2712198f4df0d306d6cd9a174587293f8b0e494d` |
| assembly PDF | SHA256 `0d4ea5d79919ae5924496ea726c334b349c00163d9da92def0dd88788ef4d340` |
| schematic PDF | SHA256 `7601e45ca0056418ae6dfbaf5cb399c5464d89f4d73dbcb92171065b9595f673` |
| PCB-layers PDF | SHA256 `9a278270d0c8f84f66e147b517fcb24d4e556f39619d8767f78df30221cf99f9` |

The four identities supplied in the review commission were re-hashed locally and match exactly.

## Assembly PDF gate

MEASURED (by this reviewer): `check_assembly_pdf.py` passes the exact assembly PDF with:

- **3/3 nonblank pages**;
- **32/32 overview reference designators**, each present exactly once;
- **0 reference-designator overlaps**;
- component values suppressed from the refdes-only drawing; and
- complete switch-detail and module/control-detail censuses.

I also rasterized and visually inspected all three pages at 150 dpi:

1. Page 1 is a complete board overview. It includes all ten SMA connectors, U_SW and its local parts, the user-fitted U_MCU outline and control parts, four mounting holes, and the power/filter parts.
2. Page 2 enlarges the QFN switch cell. U_SW pin-1 marking and the R_PD1..4/C_SW1..2 population are distinct and readable.
3. Page 3 enlarges the module/control area. The U_MCU body/keepout, LED_ST/R_LED, R_S1..4, C_BULK and FB_3V3 are individually identifiable. The module is visibly a post-assembly hand-fit item rather than an omitted JLC placement.

No page is blank, clipped, or populated with duplicate refdes labels. This closes the prior assembly-document failure class for this frozen state without relying on an earlier report.

## Population and render evidence

The current CPL contains **27 top-side placements**. The generated missing-model evidence states **27/27 bodies mounted**. The BOM has 11 grouped lines covering those placements. Four H* references are mechanical holes and U_MCU is intentionally excluded from BOM/CPL/paste for user fitting; the assembly drawing nevertheless shows all five so the population boundary is explicit.

I visually inspected:

- `twin_top.png` SHA256 `adb71e56d6581cb78cebbe1b8ddc21604115de7b4f79f0ed1dbc89782d68276b`;
- `twin_bottom.png` SHA256 `517a5cabc19367cd3acf5a149dede4072ce682dd9217173e32f318ff2f893610`;
- both isometric views SHA256 `06e443f2819e673250e405a53bd3070527b8671121d21371cfec6f1d601de10b` and `3151b4a417f2f3cb7d8f56b6869d1904a9d145a677894ad948975f174c574180`;
- both edge views SHA256 `d8f748f2a202a253ca449d7c5008071351ce3a8b4d55f39dd340dbe77ae21682` and `952962681f27d3e4a49ce12c8a79c88413432e99a9ff09a80e3fb86b2cf3078e`;
- top and bottom bare renders SHA256 `2e2749239b4fd98111591d4718f2650d6a2de8ffe6831fceda4915d1962713ea` and `f1dc8fa621379c179b665f022437df2f8f3d3518d1690965014601879de46a59`; and
- the top courtyard overlay SHA256 `f7d2ca0702fd698c41ce28b2d6233a3061d3655ba5c429d464f403868841b364`.

The top twin visibly contains all ten vertical SMA bodies, U_SW, every listed passive and LED_ST; no body is floating off its pads or mirrored. The bottom view correctly has no placed bodies. Edge views show the SMA pins through the carrier and no unexpected bottom-side placement. Bare/twin comparison agrees with the CPL population boundary.

The overlay evidence reports 11/27 large bodies directly measurable from pixels, with all 11 agreeing with expected placement (maximum center delta 0.079 mm and maximum outward delta 0.034 mm). The remaining 16 are named small passives below the overlay tool's 2 mm resolvability floor; this is partial pixel coverage, not an unlisted omission.

## PDF review and human-graded policy items

### S6 schematic readability: EFFORTFUL

The one-page tscircuit schematic is electrically traceable at normal PDF zoom, but it is dense and relies on named-net continuations between functional clusters. For example, GP0..GP3 can be followed through SEL_V1..4, R_S1..4 and SW_V1..4 to U_SW V1..V4, while the RF fan from U_SW to the ten named connectors is visually explicit. The supply story is less immediate: `3V3_MOD -> FB_3V3 -> 3V3 -> C_SW1/C_SW2/U_SW.8` is split across the page and requires following labels. This is usable, but not presentation-grade at a single full-page glance.

### S7 decoupling adjacency: PARTIAL

C_SW1 and C_SW2 are grouped with the 3V3 supply network rather than drawn directly beside U_SW pin 8. Their electrical ownership is clear from the net names and the physical assembly detail places them at U_SW, but the schematic itself does not teach that physical adjacency as strongly as it could.

### S5 design-math spot checks: PASS

Two values were independently re-derived from `DETAIL_DESIGN.md`:

1. RF pickoff: the 440-ohm series arm plus 50-ohm tap load is 490 ohms shunting the 50-ohm through load. Comparing the loaded node to the ordinary 50/50 source-load division gives **0.432 dB** through loss; the tap voltage relative to the ordinary through output gives **-20.257 dB**. These agree with the published about 0.43 dB / -20.3 dB.
2. Control damping: at 3.366 V, 67 ohm line impedance and 99 ohm resistor corner, `2*3.366*67/(67+99) = 2.717 V`; the settled value is `3.366*10000/(10000+99) = 3.333 V`; and `5*(99+67)*20 pF = 16.6 ns`. All agree with the design document and remain inside the stated 3.6 V / 1.17 V / 4.267 us limits.

### PCB-layer PDF

The eight-page layer document was rasterized and inspected. Copper, mask, paste and top-silkscreen content are centered and unclipped. Two pages are intentionally empty because this is a top-only assembly with no bottom silkscreen or bottom paste; they accurately document unused layers and are not blank pages in the three-page assembly gate.

## Findings

| id | severity | finding | evidence | disposition |
|---|---|---|---|---|
| RENDER-P1-01 | P1 | First-order uploader preview remains a mandatory human orientation/process gate. | U_SW is named in `rotation_human_gate.txt`; LED_ST's pad-number and polarity-shape channels use opposite terminal numbering even though the resolved physical CPL orientation is 0 degrees. The ten SMA jacks also require the selected plug-in/THT process. | Confirm U_SW pin 1, LED cathode, all ten SMA identities and plug-in process in the actual JLC preview before payment. This is an order-time check, not a frozen-artifact defect. |
| RENDER-P2-01 | P2 | The schematic is dense and only partially teaches decoupler adjacency. | S6 is EFFORTFUL and S7 is PARTIAL as graded above; the assembly detail itself is clear. | Documentation improvement for a future revision; no PCB or assembly-document change required for this seal. |

No P0 findings were found.

## Limitations

- Pixel overlay coverage is 11/27 because 16 named small bodies are below the renderer's measurement floor. All 27 have models and were visually inspected in the top twin, but pixel-level registration is not independently quantified for those 16.
- The twin cannot show U_MCU assembled because U_MCU is intentionally outside the CPL. The assembly PDF shows its carrier outline and local controls; physical module standoff, fillets, USB access and first-power behavior remain first-article acceptance items.
- The actual JLC uploader preview and assembled hardware do not exist in this tree. They cannot be reviewed here and remain explicit order/bring-up gates.

## Final verdict

The assembly-document gate passes, population intent is clear, the modeled and bare render pairs are mutually consistent, all current PDFs are readable for their intended purpose, and no render or documentation defect blocks the frozen design. With current sourcing measured clear, the artifact is orderable subject to the normal human preview/process confirmations listed above.

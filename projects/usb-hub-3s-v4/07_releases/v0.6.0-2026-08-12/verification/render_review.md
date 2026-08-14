subject: USB Hub 3S v4 exact routed r8 render/copper reseal
date: 2026-08-12
reviewer: fresh independent render/copper reviewer r9
context-given: time-boxed exact-artifact assignment; prior review verdicts not taken as evidence
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
review_stage: routed-final
review_kind: render
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
top_3d_sha256: 5f71cda149ab02703fe7f8c7ad3f8f68054f99c113c4644ceb9192b2b4896c22
bottom_3d_sha256: d00464b847b41985be359b4a7f89c6d575e2fb98490a944f20531cc2022b05e9
iso_3d_sha256: e44bbf2c9493c3bb8707685bc08f1bde521b29fab7f059a3b2f6a72c0c41b343
top_copper_sha256: b4129d7e9a803ae4000cb2f86e0e5a8fb1f9cc3d17afed7780b2e24e17a0f7e2
bottom_copper_sha256: 4b4c7d8f0286efa36b17908eab1409bd5994a10ed1129d2a0253a8796b3dfee0
pcb_layers_pdf_sha256: b5ed9d474f648a321405f4300f69cf79786dafd275038abfee1b87e968294a90
assembly_pdf_sha256: 878460e8f96e0656f40e7fbc9c32e39756c0c52abaaa1e0e25e678eca7f93e6d
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Exact routed-board render/copper reseal

## Verdict and evidence boundary

No P0 PCB-geometry defect or P1 PCB-design defect is visible in the exact
hash-bound routed evidence. The original-resolution views show the complete
v4 board, and the outer-copper plots show plausible, coherent routed copper
without a visible isolated island, unintended bridge, edge incursion, or
acute high-current neck cue. The render/copper design verdict is therefore
**SOUND** for these exact bytes.

This is not an order release. The images are native unpopulated-board views,
not a populated manufacturing twin or JLCPCB order preview. No credit is given
for catalog-body registration or height, component-to-component body clearance,
CPL rotation, populated polarity, connector-body overhang, or upload-preview
layer interpretation. Those explicit evidence exclusions keep the order verdict
at **DO-NOT-ORDER**.

## Artifact identity and completeness

All eight assigned files were opened from their original paths. Their SHA-256
digests match the release header exactly. The board file is 1,527,807 bytes;
the five PNGs are the expected complete-board 2384/2400-pixel-wide exports;
`pcb_layers.pdf` has nine pages and `assembly.pdf` has seven pages. Nothing in
the visible topology suggests a wrong or stale project: the board says
`USB HUB 3S V4 REV A`, carries three USB-A positions and one USB-C position,
and prominently identifies `POWER ONLY — NO USB DATA` and
`USB-C 5V / 3A NO PD`.

The top, bottom, and isometric images include every board edge and corner with
margin; no connector land, hole, fiducial, legend, or copper region is clipped.
The copper plots and PDF layer pages use the same outline, holes, connector
positions, dense converter cells, and routed shapes as the native views.

## Routed copper inspection

- The top plot shows broad, intentionally separated power regions from the
  input and two converter cells toward the three USB-A branches and the USB-C
  branch. Local fan-out narrows only at component lands. No visually apparent
  long, accidental bottleneck, dangling track, orphan sliver, or unintended
  domain-to-domain bridge was found.
- The three repeated USB-A cells are visually consistent. Each switch cell
  approaches its edge connector through an orderly local copper region; the
  connector shell/contact clearances are present and the three branches do not
  visibly cross-couple. The small signal/ESD routing remains localized beside
  its own connector.
- The USB-C cell at the south edge retains a broad local power region and
  compact controller/CC protection routing. Its fine contact fan-out is fully
  visible, enters the footprint without an edge incursion, and has no apparent
  copper short or clipped end.
- The bottom plot contains broad complementary regions and regular via/pad
  antipads. The two internal copper pages are visually near-continuous planes
  with orderly antipads rather than fragmented islands. Dense via fields at the
  converters and port switches are present and spatially coherent.
- These raster/PDF observations grade visual plausibility only. They do not
  substitute for net-aware DRC, connectivity, current-density, copper-weight,
  via-plating, or thermal qualification.

## Connector approach, holes, fiducials, and markings

- J1 faces the west side with a clear exterior approach. `+ BAT`, `- GND`,
  `3S INPUT`, the user-fit 10 A fuse legend, and the master OFF/ON legend are
  readable and attributable.
- J2, J3, and J4 are evenly spaced along the east side. Their pad fields and
  shell holes reach the intended board edge with a clear mating direction, and
  each adjacent `USB-A1/A2/A3 5V / 2A` legend is unambiguous.
- J5 is centered on the south edge with clear cable approach and a directly
  associated `USB-C 5V / 3A NO PD` legend. Footprint geometry is visible, but
  connector-body fit and overhang are deliberately uncredited.
- All four corner mounting holes are present and visually unobstructed. Three
  top-side fiducials are visible, non-collinear, and separated from the dense
  component cells.
- Top-side reference designators are present throughout. The densest U1/U2/U9
  neighborhoods are crowded but still attributable when inspected at original
  resolution. Explicit `+` marks are visible for C1, C17-C19, C22, and C23;
  J1 polarity and diode/IC footprint asymmetry marks remain visible. These are
  fabrication-side markings only, not populated-polarity proof.

## Findings

### P0

None observed.

### P1

1. **P1 evidence limitation — populated mechanical/assembly truth is absent.**
   The native 3D views predominantly show board, pads, footprints, and simple
   placeholder geometry rather than a catalog-complete populated assembly.
   They cannot close connector overhang/height, mating-shell registration,
   component body collisions, installed polarity, or enclosure/standoff fit.
   Close these on the exact released BOM/CPL with a populated twin or physical
   first article and the JLCPCB upload/order preview before changing
   `order_verdict`.
2. **P1 evidence limitation — no CPL/order-preview grading.** CPL rotations,
   JLC catalog-body orientation, bottom/top interpretation, and the rendered
   fabrication preview were outside the supplied evidence and receive zero
   credit. An independent assembly-release pass remains mandatory.

### P2

1. **P2 document hygiene — raw PDFs contain low-value pages.** Several
   `pcb_layers.pdf` and `assembly.pdf` sheets are blank or nearly blank, and
   the assembly identifier/value sheet is densely overprinted. This does not
   reveal a PCB defect, but a concise, layer-named fabrication/assembly packet
   would reduce wrong-page and handoff ambiguity.
2. **P2 qualification boundary — visual copper is not electrical proof.** The
   plots reveal no obvious island or neck, but net connectivity, zone ownership,
   current capacity, thermal rise, finished via construction, and fabricated
   copper remain machine-gate and first-article obligations.

## Release disposition

`SOUND / DO-NOT-ORDER`. The exact routed geometry passes this independent
render/copper lens with no observed PCB-design defect. Ordering remains blocked
until the explicitly withheld populated-body, CPL/rotation, populated-polarity,
manufacturing-preview, and first-article evidence is reviewed against the exact
release package.

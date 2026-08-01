subject: pluto-rx2-8way-v4 962c3cdaeba5070d5b668bf01a70a4ccc6498c51
date: 2026-07-31
reviewer: render-review (fresh-context adversarial visual/population lens)
context-given: full-tree (08_reviews excluded until independent analysis was complete)
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER
overall_verdict: FAIL

# Final adversarial render and population review

## Scope and artifact identity

This review was performed independently before reading any prior review record.
It covered the current modeled and bare board renders, all pages of the three
PDFs, BOM/CPL population data, the twin/overlay evidence, and the current
board/schematic artifacts. It does not substitute for the independent pin,
topology, or layout lenses.

- Material source commit, MEASURED by `git rev-parse HEAD`:
  `962c3cdaeba5070d5b668bf01a70a4ccc6498c51`.
- Board SHA-256, MEASURED:
  `4f991628c624b0af42a33294c544d1f48354f224c9be31a9bd0c0f9269d33521`.
- Gerber ZIP SHA-256, MEASURED:
  `4c3d64e3e419576d03b47d53430d6ff04e622f1097259cf8f6bba02f4d9876ef`.
- Assembly PDF SHA-256, MEASURED:
  `a0509ea2969a7293dd79a03ea26c4efd0c6ea124295e714c17851037bd41a38d`.
- PCB-layers PDF SHA-256, MEASURED:
  `b06e6bd6f200e649f410bb9620e7ea6919e973d6e9ef1ca1c7e50680563e8a6f`.
- Schematic PDF SHA-256, MEASURED:
  `13b013924488569cce6c2a0481ffbedf92e9a4a03311a2b8b00111ffda7cd7f7`.
- The staged source board/schematic/TSX/netlist, BOM, CPL, Gerber ZIP, and six
  staged twin views are byte-identical to their current build counterparts,
  MEASURED by SHA-256 comparison.

## Result

The modeled/bare render pair is coherent and the population census closes, but
the populated-side assembly drawing is not a reliable assembly/rework map. Its
Fab values and reference designators collide through the densest and most
assembly-sensitive regions. Under this review's instruction that a P1 visual
or assembly defect blocks release, finding RR-F1 makes the present candidate
**FAIL / DEFECTIVE / DO-NOT-ORDER**.

## Findings

| ID | Severity | Finding | Evidence | Disposition |
|---|---|---|---|---|
| RR-F1 | P1 | `pdf/assembly.pdf` is not reliably readable as an assembly/rework map. The only populated-side page has overlapping value/refdes text in the U_SW + C_SW1/C_SW2 + R_PD1..R_PD4 field and again around LED_ST/R_LED/R_S1..R_S4/U_MCU/C_BULK/FB_3V3. Several strings are mutually occluded rather than merely small. Page 3 contains only the page frame; page 2 is a holes-only view. | MEASURED by rendering all three vector-PDF pages at 130 dpi and inspecting them at original resolution; `pdftotext -layout` independently shows interleaved/colliding labels in the same regions. The PDF hash is fixed above. | **OPEN, RELEASE-BLOCKING.** Regenerate the standard assembly PDF after making F.Fab reference/value placement unambiguous (or suppressing redundant value text while retaining one clear refdes per part), remove/avoid empty pages, and repeat this fresh render review against the new hash. |
| RR-F2 | P2 | The LED model/pad-number fit emits a misleading 180-degree suggestion even though physical polarity resolves to CPL 0 degrees. | MEASURED independently: KENTO datasheet p2 places `+` at terminal 1 and the cathode/chamfer at terminal 2; KiCad's footprint places its cathode bar/chamfer at pad 1 on the west end; JLC's numbering is opposite but its cathode-shaped marking is also west. Thus both physical cathodes align at the shipped CPL `0.0`. The current twin report also records the numbering-channel disagreement. | Recorded. Keep C2286 at CPL 0 degrees. Do not apply the twin's pad-number-derived 180-degree suggestion. Mandatory first-order preview check remains below. |

## Population and modeled/bare correspondence

All counts below are MEASURED from the current artifacts, not inherited from a
summary.

| Check | Result |
|---|---|
| Board footprints | 32 |
| CPL placements | 27, all top-side |
| Declared not assembled | 5: H1, H2, H3, H4, U_MCU |
| Unexplained population omissions | 0 |
| Twin bodies | 27/27 CPL refs |
| Missing-model manifest | none |
| BOM-to-CPL population | 27 designators represented by 11 coded BOM rows |
| Orthographic overlay | 11/27 visually resolvable bodies measured; 16 sub-2 mm bodies explicitly named as unresolvable; 0 resolvable-but-unmeasured; 0 no-model |
| Overlay displacement | no measured body exceeded the 1.00 mm centre/outward threshold; largest measured centre delta 0.079 mm |

Visual cross-checks:

- `twin_top.png` agrees with `render_top_bare.png` on connector, U_SW,
  passive, LED, module-land, mounting-hole, and board-outline locations.
- `twin_bottom.png` agrees with the bottom bare view: no bottom placements,
  only drilled/through-hole geometry and via field.
- Both isometric and both edge views show all ten SMA bodies seated at their
  five-hole patterns, with no body-body or body-board collision visible.
- U_MCU is correctly absent from the CPL/twin rather than a missing model. Its
  footprint and hand-solder legend remain visible in the bare/top render.
- The modeled SMA pins extend below the board as expected for unsoldered THT
  models; this is not evidence that the plug-in soldering process is enabled.

## Orientation, polarity, and markings

- **LED_ST:** physical polarity is correct at CPL 0 degrees, as independently
  derived in RR-F2. The board's `K` legend is on the cathode/pad-1 west end and
  remains visible in the modeled top render. The part is symmetric to pad-fit,
  so order-preview confirmation is still mandatory.
- **U_SW:** the QFN body is centered on its courtyard/pads, the twin reports a
  0.01 mm fit, and the board's pin-1 mark remains visible. The rotation evidence
  is single-channel, so preview confirmation remains mandatory.
- **SMA connectors:** all ten bodies align with their center and four shell
  holes. Their rotations are mechanically constrained by the hole pattern;
  functional port labels are visible around the populated bodies.
- **Human-facing silk:** `ANT1` through `ANT8`, `RX1`, `RX2`, receive-only /
  no-transmit / 0-VDC warnings, status-LED cathode `K`, RP2040-Zero hand-solder
  instruction, and USB-C power/bootloader note are present and readable in the
  top/bare render. Dense passive refdes are small but remain distinguishable in
  the board render; the failure is specifically the assembly PDF's Fab overlay.

## PDF readability

- **Schematic PDF: PASS.** One vector page; the RF star, two output paths,
  module control, filtered 3V3 feed, pulldowns, and status LED are traceable.
  Net labels and component values remain readable at ordinary PDF zoom.
- **PCB-layers PDF: PASS WITH NOTE.** The copper/mask/paste/silk pages are
  coherent and expose the top-only assembly. Empty bottom-silk/paste content is
  consistent with no bottom placements; blank-looking pages are low-value but
  do not falsify the board.
- **Assembly PDF: FAIL.** See RR-F1.

## Order-time human stop gates

These gates remain mandatory even after RR-F1 is fixed; none is represented as
already performed.

1. **JLC process acceptance:** obtain written/order-screen confirmation that
   the ten C504007 `Plugin` SMA connectors will receive through-hole assembly.
   If JLC declines, this BOM/CPL population posture must change in a new
   candidate/release.
2. **JLC preview, U_SW:** confirm C5121458 pin 1 and body orientation against
   the board mark before paying; its rotation has only the pad-number channel.
3. **JLC preview, LED_ST:** confirm the KENTO chamfer/cathode lands at the board
   `K` / pad-1 west end. Preserve CPL 0 degrees; reject any automatic 180-degree
   substitution caused by opposite library terminal numbering.
4. **Resolved BOM echo:** save JLC's resolved part table and diff it against
   `bom_echo_gate.txt`; any redirected code is a stop.
5. **RP2040-Zero hand assembly:** JLC must place/source nothing at U_MCU. Hand
   fit the actual module, inspect the underside component stand-off and carrier
   keepout, then hand-solder and inspect all 23 castellations before power-up.
6. **Order-day stock:** rerun the stock gate on the order date; this review did
   not re-query volatile inventory.

## Unverified inherited claims

- The DRC/ERC/pin/topology/layout verdicts are outside this lens and were not
  adopted as evidence here.
- RF performance, insertion loss, phase matching, impedance, and hardware
  bring-up are not proven by render correspondence.
- JLC's willingness to run the plug-in THT process is explicitly not proven by
  the catalog's `Plugin` classification.

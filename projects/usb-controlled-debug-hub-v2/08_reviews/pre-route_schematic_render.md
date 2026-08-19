# Pre-route schematic readability review — USB Controlled Debug Hub v2

review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
schematic_pdf_sha256: e5dffbcb5d740fb454005991e272fd12577c17c66f979208b326e2ac31cf25f2
netlist_sha256: 415ed5f78099519b05c7bce13fd1e95a9532578aefef0adefd7c5e5c01f3a4ce
parts_sha256: 5b7c3bc4fac920871378776dae0bae8dc84dbc28d80715fd51fabfef45c6ee48
design_rules_sha256: 753a8d737d660ca4efb41bc3403da5e5da911881e5239b5568cf5172a50870d9
reviewed_at: 2026-08-18T21:02:00-07:00

## Readability result

The exact ten-page vector PDF was inspected page by page, with raster checks
at 180 dpi for the two power pages. Functional stages are separated into PD
input/regulation, aggregate distribution, hub core/straps, management,
interlocks, and one page per external port.

- The new page-one power path reads left-to-right: POWER USB-C → fuse/TVS →
  CH224K → input eFuse → 15-to-5 V buck → protected 5 V output.
- UVLO/OVLO, ILIM, dV/dt, buck-enable, feedback, bootstrap, and output-bank
  support networks are spatially separated from the main chain and named.
- There are no observed component-on-component overlaps, clipped bodies, or
  net-label plates obscuring conductors on the new power page.
- Page two separates the aggregate eFuse and 3.3 V regulator, with its divider,
  timer, dV/dt, bulk bank, bootstrap, inductor, and output capacitors visible.
- The retained management TPS2557 page identifies the corrected 187 kOhm
  current-programming resistor; no stale 210 kOhm value remains in the exact
  rendered source.
- The PDF remains vector-based; the intentionally broad power-chain page is
  legible when viewed normally or zoomed and does not rely on the raster
  review copies shipped under `06_build/schematic_review/`.

The generated schematic contains no ERC errors. Converter-origin advisory
warnings about synthesized symbol pin attributes and automatic PCB preview
footprint similarity are not hidden and do not affect this readability
verdict.

The rebound design-rule digest reflects placement/routing-area refinement
only; the exact schematic PDF, normalized netlist, and parts digest above are
unchanged.

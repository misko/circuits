# Changelog

## v1.0-2026-08-01

- Commissioned v4 in an isolated agent-owned project directory.
- Applied binding module-first amendment and selected Waveshare RP2040-Zero.
- Removed bare RP2040, external flash/clock, carrier USB, and carrier LDO work.
- Retained the confirmed two-220-ohm broadband reference pickoff.
- Declared four-layer advanced controlled-impedance fabrication.
- Generated a fresh 28-component schematic and board from v4 sources.
- Promoted the deterministic winner of a three-candidate route race; all three
  candidates measured clean before stitching.
- Sealed layout after P-MOD, placement, landability, routing, length, policy,
  and final DRC gates; final DRC is 0/0/0.
- Added the RX2CTL/1 firmware scaffold: allocation-free state/schedule core,
  RP2040 PIO+DMA USB-CDC shell, host utility, and native tests.
- Generated and graded the sealed v1.0 JLC fabrication package. The export uses
  no rotation or BOM escape hatch; A-POP, stock, BOM source/legibility, and
  27/27-body twin checks pass. No order or immutable release was created.
- Closed adversarial-review repairs: 100-ohm control-source damping with
  machine-checked transient/DC bounds, quiet GPIO pad settings, downstream
  filtered bulk capacitance, a real module underside keepout, corrected L3
  routing, and an authored physical JLC04121H-7628 stackup.
- Closed the final adversarial RF-fence finding with two additional grounded
  stitching vias, a saved-board 22/22-side pitch gate, and a red/green
  regression fixture.
- Bound the safe RF/power envelope and preserved physical/order gates for
  module metrology, impedance/TDR, uploader polarity/BOM echo, and ten plug-in
  SMA jacks.
- Passed all four final independent review lenses at exact source and artifact
  hashes. The design is SOUND; ordering remains intentionally held for
  vendor-process acceptance and first-article qualification.

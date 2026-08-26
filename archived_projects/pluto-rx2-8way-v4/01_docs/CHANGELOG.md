# Changelog

## v1.1-2026-08-01

- Moved `R_S1` through `R_S4` and `R_LED` 0.30 mm away from the
  RP2040-Zero castellated module lands. The resulting inter-footprint copper
  clearance is 0.22 mm, above the 0.09 mm four-layer advanced fabrication
  floor; zero-distance contact and overlap are now hard failures.
- Rebuilt and re-promoted the affected control routing, retaining the reviewed
  `SW_V4` crossing on `In2.Cu` so the `In1.Cu` RF return plane is uninterrupted.
- Rebuilt the exact board from committed sources with DRC/unconnected/parity
  0/0/0, P-PADSEP PASS, RF fence 22/22, modeled CPWG 52.09 ohms, and eight-arm
  routed-copper spread 0.166 mm.
- Regenerated the CPL, Gerbers/drills, layer and assembly drawings, STEP model,
  digital twin, and exact bare-board views. All 27 placed bodies are present;
  the independent pixel gate measures all 11 resolvable bodies within 1.00 mm.
- Added explicit RF applicability, schematic/PCB/fabrication review contracts,
  and a fail-closed publication boundary. Release-only and review-only changes
  now trigger grading, seals bind review bytes, and zero review coverage cannot
  pass either the design or sourcing claim.

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

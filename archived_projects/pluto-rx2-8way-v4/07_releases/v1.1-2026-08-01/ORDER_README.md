# RX2 8-way v4 — fabrication and first-article instructions

DESIGN: PASS
SOURCING: CLEAR — 11/11 catalog lines cover five boards; measured 2026-08-01
ORDER VERDICT: ORDER — first-article prototype build authorized

The sealed electrical and PCB design is SOUND and the catalog covers the
five-board build. Upload preview and service-selection checks below are part of
executing the order: stop only if the vendor rejects the authored process or
changes the submitted data. First-article tests are required before production
or service use; they are not a circular prerequisite for ordering the article
on which those measurements must be made.

## PCB order

- Vendor/service: JLCPCB, four-layer advanced process.
- Quantity: 5.
- Stackup: `JLC04121H-7628`, nominal 1.2 mm finished thickness.
- Copper: 35 um (1 oz) outer and 15.2 um (approximately 0.5 oz) inner,
  exactly as represented by the sealed KiCad stackup.
- Surface finish: ENIG.
- Controlled impedance: 50 ohm, ±10%; do not silently edit RF geometry.
- Minimum via: 0.25 mm finished pad / 0.15 mm drill; aspect ratio 8:1.
- POFV: board-wide filled and capped plated through vias, including the ten
  unique `U_SW` via-in-pad sites. Select and confirm that service in the order.
- Keep the submitted Gerber/drill pair together; do not substitute a generic
  four-layer stack or adjust trace widths without a design review.

## Assembly order

- Submit `fab/bom.csv` and `fab/cpl.csv` together.
- JLC assembles the 27 CPL placements.
- `H1,H2,H3,H4,U_MCU` are deliberately not assembled by JLC.
- `U_MCU` is a user-fitted Waveshare RP2040-Zero module, not a bare RP2040.
- The ten `KH-SMA-KE-Z` connectors are vertical plug-in THT SMA jacks. Select
  the plug-in assembly process; if the uploader/vendor declines it, stop and
  create a new release with the BOM/CPL population disposition changed.
- Do not infer LED orientation from the symmetric two-pad fit. At upload,
  verify `LED_ST` pin 1 and polarity against the order preview and datasheet.

## Mandatory post-upload gates

1. Save JLC's resolved BOM table and compare every `(LCSC, value, refdes)`
   triple with `verification/bom_echo_gate.txt`; redirects are substitutions.
2. Inspect all rotations and polarity in the placement preview, especially
   `LED_ST`, `U_SW`, and the ten SMA jacks.
3. Confirm the production note explicitly names `JLC04121H-7628`, 1.2 mm,
   50-ohm controlled impedance, and filled/capped POFV.
4. Confirm the order accepts the ten SMA plug-in joints; a rejection is a stop.

## First article — do not release to service until complete

- X-ray all ten `U_SW` via-in-pad sites and representative filled/capped vias.
- TDR/VNA the RF launches and all eight switched paths; compare insertion
  loss, return loss, isolation, and path-to-path phase/length spread to the
  sealed RF evidence.
- Dry-fit the RP2040-Zero module, verify underside keepout and USB access, then
  inspect every castellation joint after hand assembly.
- Run firmware/USB switching tests for all paths and safe-state sequencing.
- Verify 3V3 rail startup, switch supply ripple, module current, and thermal
  rise under the worst intended duty cycle.

This archive authorizes a five-board first-article order using the exact sealed
files. Do not release the hardware to production or service until every
post-upload and first-article acceptance item above is recorded as passing.

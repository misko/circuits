# ADR-0002 — user-fitted module; module-owned USB and power boundary

Status: accepted, 2026-07-31.

The RP2040-Zero is excluded from paste and position outputs and fitted by the
builder after JLC assembles the carrier. Vendor STEP measurement shows 23
carrier-facing components: the crystal is 1.000 mm proud, RP2040 0.850 mm and
RT9013 0.700 mm, while the castellated copper sits on that same face. There is
no direct reflow seating plane and Waveshare publishes neither an MSL rating nor
a second-reflow profile. JLC's module footprint/consignment identities have
zero stock; retail development-board entries are not placeable line parts.

The module's USB-C is the board's only connector for power and data. Its 5 V
castellation remains open. The carrier does not duplicate USB protection, a
regulator, or a second input. The module's 3V3 output passes a ferrite into the
RF-switch rail with local bypass. This reduces both electrical complexity and
the risk of two USB sources fighting.

The footprint carries the live underside-pad copper/track/via/pour keepout and
no paste. The vendor publishes no tolerance for bottom-component protrusion or
castellation coplanarity, so a fixed universal standoff inferred from the STEP
is not an acceptance claim. The assembly drawing and build instructions must
call out DNP/user fitting, pre-fit resistance checks, sample metrology, an
electrically insulating edge-support fixture that never loads the crystal or
other bottom parts, positive-gap/parallelism inspection, accessible USB, and
full fillet inspection.

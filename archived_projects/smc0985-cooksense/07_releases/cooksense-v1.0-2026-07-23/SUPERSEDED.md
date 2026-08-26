# SUPERSEDED — DO NOT ORDER

Superseded by: `07_releases/cooksense-v1.3-2026-07-26/`
(previously superseded by v1.1, which is itself DO-NOT-ORDER)

## CORRECTION, 2026-07-26 — the earlier text on this page was wrong

This notice previously read:

> Reason: mechanical repack 252x92 -> 188x92 mm ... Schematic/netlist
> BYTE-IDENTICAL to this release; **v1.0 remains electrically valid** — do not
> order it only because the v1.1 outline is the current mechanical intent.

That sentence was true about the *repack* and false as a statement about the
release. It said, in effect, "you may still order this board", and a reader
acting on it would have built hardware carrying every defect listed in
`../cooksense-v1.1-2026-07-24/SUPERSEDED.md`. Because the v1.0 and v1.1
schematics/netlists ARE byte-identical, **v1.0 carries every electrical defect
v1.1 carries** — the byte-identity that made the sentence seem safe is exactly
what makes it unsafe.

**v1.0 IS NOT ELECTRICALLY VALID. DO NOT ORDER OR ASSEMBLE IT.**

## The defects, in full

See `../cooksense-v1.1-2026-07-24/SUPERSEDED.md`. In summary, all verified
against the sealed artifacts:

1. The opto-isolated 30 V contactor loop shares a SELV connector housing —
   `CONTACTOR_C` and `ESTOP_RAW` 0.650 mm apart on one JST-GH in one harness.
2. The door interlock is FAIL-PERMISSIVE (`R_DOORPU` pulls DOOR_RAW UP to 3V3).
3. `WD_PET` has no hold-down, so the watchdog input floats when the Pi
   tri-states it — the primary runaway backstop is not reliably present.
4. There is no open-thermistor detection at all; a broken or unplugged sensor
   head reads as a healthy cold one.
5. `CE1` ships at CPL rotation 180 — a reversed 220 uF polarized electrolytic
   across a live 5 V rail.
6. 22 wrong CPL rotations, including all ten safety-chain SOT-23-6 gates at
   90 degrees out, which do not connect their intended nets.
7. CPL population and datum defects (13 blank-LCSC placement rows, THT parts on
   an SMT-only CPL, J_PI 24.1634 mm off datum).

## What it remains useful for

The provenance record for the 252x92 -> 188x92 mechanical repack, and the
fixture set several gates are RED-verified against. Nothing that gets built.

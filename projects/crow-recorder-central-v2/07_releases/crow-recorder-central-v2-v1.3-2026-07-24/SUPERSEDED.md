# SUPERSEDED — this release is DO-NOT-ORDER for PCBA

**Superseded by:** `crow-recorder-central-v2-v1.4-2026-07-25`

## Do not assemble from this directory

**`fab/cpl.csv` in v1.3 places SEVEN parts 180 degrees off, and they are every
fine-pitch part on the board.** Building PCBA from this CPL puts the consigned
0.4 mm-pitch SoC, both 0.5 mm-pitch ADCs, the boot flash, both bucks and the
USB ESD array down backwards.

| ref | LCSC | package | v1.3 (WRONG) | v1.4 (correct) | what it is |
|---|---|---|---|---|---|
| U1 | C6938291 | TQFP-128 14x14 0.4 mm + EP | 90.0 | **270.0** | **CONSIGNED** XMOS XU316-1024 SoC |
| U2 | C181312 | TSSOP-30 0.5 mm | 90.0 | **270.0** | PCM1865 ADC (ch 1–4) |
| U3 | C181312 | TSSOP-30 0.5 mm | 90.0 | **270.0** | PCM1865 ADC (ch 5–8) |
| U5 | C82317 | SOIC-8 5.3x5.3 | 90.0 | **270.0** | W25Q16 QSPI boot flash |
| U7 | C5224055 | SOT-563 | 90.0 | **270.0** | AP61102 buck, 3V3 |
| U8 | C5224055 | SOT-563 | 90.0 | **270.0** | AP61102 buck, 0V9 core |
| D_USB | C90627 | USON-10 0.5 mm | 90.0 | **270.0** | USB D+/D− ESD array |

`fab/bom.csv` and the bare-PCB set (`fab/*_gerbers.zip`, both `.drl` files) are
**correct and byte-identical to v1.4's** — the copper was never wrong. Only the
assembly data is. If a bare PCB has already been ordered from this directory it
is fine; do not run the assembly step from this CPL.

## What went wrong

v1.0, v1.1 and v1.2 all shipped these seven rows CORRECTLY at 270. v1.3
"corrected" a non-defect and made a good board bad.

`jlc_twin.xform()` used the OPPOSITE handedness to the operator KiCad actually
applies to a rotated footprint's pads, so every rotation offset the digital twin
reported was NEGATED. The two forms are mathematically identical at 0 and 180
(both sign-invariant under the negation) and 90/270 negate into each other — so
the error was invisible on more than half the fleet and EXACTLY 180 degrees wrong
on the rest. The per-LCSC rotation table `jlc_lcsc_rotations.csv` had been
POPULATED FROM that function, so the "authority" table was the checker's own
output (canon M1) and every consumer — the exporter, the twin's own re-run, and
an external reviewer reading the table — inherited the same negation with nothing
independent able to object. v1.3 sealed with green gates and 0 unresolved
rotation suggestions while being 180 degrees wrong.

Q1 (C15127), Q2 (C20917) and U9 (C79924) were NOT affected and did NOT change in
v1.4: their per-LCSC values are 180, and 180 is sign-invariant under the
negation. That asymmetry — exactly the 90/270-valued rows moved, none of the
180-valued ones — is the root cause's fingerprint, visible in the diff itself.

Fixed at source: the operator in `1b69760` (pinned by two RED-verified tests
against pcbnew), the table in `e0d735c`. v1.4 re-derives all ten angles by a
method that shares no code with any of it.

## What v1.4 changes

`fab/cpl.csv` only — **exactly seven changed cells**, all in the Rotation
column, all 90.0 → 270.0; zero rows added or removed; every other field of every
other row byte-identical. Everything else in the archive is sha256-identical
(20 payload files), and that identity is proven by RE-PLOT from the unchanged
board rather than by copying. v1.4 also lands `03_src/rules/assembly.yaml` (the
declared population set), moves U1 from this release's `not_assembled:` prose
into `consigned:` where a placed part belongs, and ships machine-gradeable stock
evidence at build quantity 5.

Use `crow-recorder-central-v2-v1.4-2026-07-25` for any order.

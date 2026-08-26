subject: usb-hub-3s-v4 routed r9 layout publication reseal
date: 2026-08-12
reviewer: Codex independent layout/thermal/power-integrity publication reviewer
context-given: exact routed board and existing publication evidence only
source_commit: ca9cc5785781820239bf513a43cbfc8db4d1eed7
ancestor_source_commit: 9b0bfd4bd6b2bd3b99d8ab485defc8fad80b317d
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Routed r9 layout publication reseal

## Exact evidence binding

This time-bounded reseal read back the unchanged canonical routed board and the
existing exact-board layout evidence; it did not regenerate or alter the PCB or
sealed release. The live `04_kicad/usb_hub_3s_v4.kicad_pcb` hashes exactly to
`9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb`.
The current publication/status commit is
`ca9cc5785781820239bf513a43cbfc8db4d1eed7`; the design-source ancestor bound
into the release is `9b0bfd4bd6b2bd3b99d8ab485defc8fad80b317d`.

The existing exact KiCad severity-all DRC witness
`06_build/drc/gate.json` reports KiCad 10.0.4, zero violations, zero
unconnected items and zero schematic-parity findings. The routed census is 95
footprints, 379 pads, 446 track segments, 183 vias and 54 zones. The prior
exact-board r8 layout review binds the filled copper renders and layer PDF and
records continuous In1.Cu/In2.Cu ground planes, no isolated high-current pour,
no serial microvia dependency, no connector-edge conflict and no destructive
thermal-layout defect.

## Layout, via and thermal read-back

- `06_build/verification/via_process.json` SHA-256
  `afb11ddc257b4235b2402e42dedf60a6d1c962e565ee05b602d8a74f61c1258f`
  grades all 183 vias: 65 protected 0.50/0.20 mm filled-and-capped sites and
  118 ordinary 0.30 mm-drill sites, with zero partial classifications and
  drill-disjoint process families.
- `06_build/verification/via_ampacity.json` SHA-256
  `653b23a195964d33e7168927b8a16093838bde9ed74e68c46ad5a14988492ab6`
  passes all four declared serial transfer banks. The U9-to-5VA distributor
  bank is credited 11.76 A against 8.0 A required; each U4/U5/U6 input bank is
  credited 3.91 A against 2.849 A required. Fill material receives no ampacity
  credit in that screen.
- The existing policy audit records `R-THERM PASS`: every pad at least 4.0 mm2
  has at least two nearby same-net vias. The r8 review additionally records the
  owned thermal-via fields at U1, U2, U3, U4-U6, U9 and C23 and the separated or
  windowed paste treatment at exposed-pad packages.
- The declared current-path evidence remains coherent: BAT_POS/VBAT_FUSED and
  VIN use broad dual-outer-layer regions with a continuous F.Cu trunk; U9 feeds
  the broad B.Cu 5VA distributor through fourteen 0.70/0.30 mm serial-transfer
  vias; each USB-A limiter has its own five-via input bank; and VBUSC retains a
  direct F.Cu path to all four Type-C VBUS contacts with four ordinary vias for
  layer sharing. No whole-rail path is reduced to one via or a signal-width
  trace.

These are geometry, connectivity and bounded via-capacity checks. They do not
measure filled-copper current density, complete-path resistance, solder-joint
resistance, current sharing, hot temperature rise, converter stability or
transient behavior.

## Closed verdict

`SOUND / DO-NOT-ORDER`. No new layout, return-path, thermal-via, serial-transfer
or connector-mechanical defect is exposed by the existing exact-board
publication evidence. Ordering remains prohibited because no accepted JLC
uploader/process preview proves the item-specific Type-VII fill/cap execution,
and no fabricated first article exists to close hot four-wire resistance,
loaded thermal, startup, load-step, ripple, fault, backfeed and interconnect
tests. This design verdict is not a fabrication or production-qualification
verdict.

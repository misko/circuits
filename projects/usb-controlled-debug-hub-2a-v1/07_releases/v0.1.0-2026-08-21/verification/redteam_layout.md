# Final layout/fabrication red-team — v0.1.0

reviewer: Codex primary agent, exact-artifact layout lens
reviewed_on: 2026-08-21
project: usb-controlled-debug-hub-2a-v1
subject: usb-controlled-debug-hub-2a-v1 v0.1.0 exact final board
board_sha256: 9eb649598aeecac74ce04347ea5d20e516fdebb58fd9a04948c71446a9c83e24
pcb_sha256: 9eb649598aeecac74ce04347ea5d20e516fdebb58fd9a04948c71446a9c83e24
gerber_zip_sha256: 28ac18f820457c27eaa737f459ad38fd80419c27480f77236616cfe7d434e9d7
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

The exact board passes DRC/parity 0/0/0, route acceptance 9/9, all ten USB
critical-pair contracts, reference-plane checks, copper-length contracts,
fab-payload identity/pour checks, 183/183 model coverage and 179-row exact
assembly population coverage. The four manually fitted USB-A connectors are
source-bound as not assembled and carry KiCad's native position-file exclusion
bit, so a later export cannot silently put them back into the CPL.

The final via census is one fabrication-selectable family: 578 protected
0.46/0.20 mm filled-and-capped vias, 143/143 via-in-pad sites covered and zero
ordinary vias. The input-eFuse exposed ground pad has two explicit source-owned
thermal barrels. Policy audit result is HUMAN=6, N-A=9, PASS=29, WAIVED=2,
with no FAIL and both machine waivers backed by regenerated evidence.

Connector orientation is user-approved against subject
475cf8ff51ff459bd325a8cb987313a4d6f2fbbfc2ba1918bf218ba7b2f145d8.
Placement did not move during routing or the final via-process correction.

P0 findings: none.

P1 order blockers: JLC must confirm the 578/0 Type-VII drill-family process,
the final stackup and 90-ohm USB solve, all placement rotations/polarities,
and both USB-C mixed SMT/THT footprints in its own preview.

P2: a consolidated board STEP is absent because the installed KiCad exporter
cannot resolve all standard model aliases/VRML inputs. The exact twin renders,
native model-registration evidence and 183/183 resolvable-body census remain
the mechanical evidence; the STEP absence is not hidden.

> Adopted 2026-07-21 into crow-recorder-central from archived_projects/crow-array-central (provenance ADR 0011; re-verified by this project's own gates before any release). Original text follows.

# ADR-0004 — TQ128 escape feasibility at JLC 4L standard tier (canon R4)

Status: accepted 2026-07-18 (checked BEFORE package commitment)

## The check

XU316-1024-TQ128 is a TQFP-128: 14x14mm body, 16x16mm over leads,
**0.4mm lead pitch, all 128 pins PERIPHERAL** (single ring, no area
array). Land pattern per the XMOS package drawing: ~0.22mm pad width,
~1.5mm pad length.

The kicad-pcb golden rule 5 killer applies to 0.4mm **QFN/BGA between-pad
routing**: track + 2x clearance >= 0.276mm > the 0.18mm pad gap, so no
trace may pass BETWEEN pads at JLC floors. For a peripheral QFP this is
not needed: every pin escapes STRAIGHT OUT on F.Cu, collinear with its
own pad.

Numbers at JLC 4L standard capability (min trace/space 0.09mm; our own
DRC floors 0.127mm clearance / 0.15mm track):

- Escape track 0.15mm centered on a 0.4mm-pitch pad column: neighboring
  escape-to-escape clearance = 0.4 - 0.15 = **0.25mm >= 0.127** PASS.
- Escape track vs adjacent PAD (0.22mm wide): (0.4 - 0.22/2 - 0.15/2) =
  **0.215mm >= 0.127** PASS.
- Via fanout ring outside the pad field: 0.45/0.3 vias on >=0.65mm
  staggered grid — standard tier, no advanced option needed.

## Decision

TQ128 is escapable at the JLC 4L STANDARD tier with our normal floors; no
fab-tier escalation, no package swap. Routing order still honors R4:
XU316 fanout + USB diff pair + clock tree route FIRST (hardest escapes
claim lanes first — route_waves.sh wave 1).

If the part had been the 0.4mm QFN variant this would have been a
package-change ADR instead; recorded so the reasoning survives.

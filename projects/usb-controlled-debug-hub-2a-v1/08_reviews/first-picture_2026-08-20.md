subject: usb-controlled-debug-hub-2a-v1 first complete schematic picture
date: 2026-08-20
reviewer: Codex primary agent, human-schematic-readability lens
context-given: full-tree
source_commit: a8e7faa2b19c7984d0066542138a9c3b5cbcb532
schematic_pdf_sha256: 51f6dba775bbe90007f2bcf70b12adb13b8417a036293825af2064b5222d6e01
circuit_json_sha256: adfde89b96d14d6e062a79b3fb44367315e6abb730658b28fe3073e496c80193
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

# First-picture schematic readability review

Scope: visual readability of all ten sheets in the exact PDF above. This is
not a pin-authority, topology, placement, routing, fabrication, or order
permission. The independent machine electrical closure for the same design
state reports `ACCEPTED 9/9`; this review does not reproduce those equations.

## Verdict

The schematic is judgeable and suitable for continued pre-layout review.
Every sheet has a visible functional title, the design reads from protected
USB-C PD input through the two 5 V banks, hub, management/interlocks, and four
repeated output channels, and intentional no-connect policy is stated on the
hub and management sheets.

The repeated port sheets make the power/data split easy to compare. Exact
active-part identities, rail labels, current-limit programming, local bypass,
ESD, connector pins, command-safe defaults, and switched VBUS are visible at
normal PDF zoom. No text/component/wire occlusion was observed; the machine
occlusion receipt independently reports zero findings.

## Findings

- `FP-001` (`P2`): sheet 2 is information-dense. It remains readable when
  viewed as the delivered landscape PDF, and the A/B symmetry is useful, but
  it should not become denser during later edits. Record only; no schematic
  backtrack is justified.
- No `P0` or `P1` readability finding.

## Boundary

Placement remains blocked. The exact 50-line JLC PCBA pre-layout response is
still blank, and the current floorplan/routing YAML below its corrected
project/path knobs is explicitly an unadopted template scaffold. Canonical
`pre-route_topology.md` and `pre-route_schematic_render.md` must be minted only
after those semantic rules are authored, because their hashes deliberately
bind the adopted design-rule set.

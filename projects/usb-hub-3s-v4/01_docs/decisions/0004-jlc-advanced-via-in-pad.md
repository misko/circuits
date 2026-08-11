---
id: 0004
date: 2026-08-10
status: accepted
---
# 0004 — Escalate to JLC four-layer advanced via-in-pad

## Context

A3 provisionally selected JLC standard four-layer and explicitly required an
escalation if another tier became necessary. TI's full-current layouts for the
selected power modules require numerous thermal vias through exposed lands;
TPS25810 and TPS2557 also use exposed thermal pads. Open or ink-plugged vias
under solder paste risk solder loss and voiding. JLC identifies resin fill and
copper cap as the appropriate via-in-pad process and the repository models that
as `jlc_4layer_advanced`.

## Options

- Standard four-layer with open/tented thermal vias — rejected because it does
  not faithfully implement the selected devices' manufacturing/layout intent.
- Standard tier with dogbone vias outside all pads — rejected for the power
  modules because it weakens the direct thermal path and diverges from TI's
  full-current layout.
- Four-layer advanced with filled/capped via-in-pad — proposed.
- Backtrack to lower-current discrete packages — possible if advanced-tier cost
  is unacceptable, but reintroduces the complexity ADR-0002 removed.

## Proposal

Set `fab_tier: jlc_4layer_advanced` and order resin-filled/copper-capped thermal
vias under every applicable exposed land. Confirm actual hole, fill, cap, paste
and stencil options in the JLC uploader before ordering.

## Consequences

The board costs more than A3's provisional tier and order documentation must
name the paid process. This ADR remains proposed until accepted at the Stage 1
pause; Stage 2 must not start if the user rejects the escalation.

## Acceptance — 2026-08-11

Accepted by the user after the stage-pause comparison: use advanced when it
makes the selected board easier or technically sound; avoid it if the board is
simple enough not to require it. The selected design meets the first condition:
the TPSM63610/TPSM63604 layouts require direct exposed-land thermal via fields,
and TPS25810's 0.50 mm WQFN independently computes as
`jlc_4layer_advanced`. Standard processing would require an architecture or
package backtrack, not merely a simpler layout of the same circuit.

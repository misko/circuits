---
id: 0005
date: 2026-08-14
status: accepted
---
# 0005 — Advanced tier for USB 3 escape

## Context

ADR-0004 provisionally set JLC standard four-layer as the cost ceiling before
exact packages were checked. The selected 5 Gb/s redriver is a 24-pin 0.5 mm
VQFN and the six-line ESD array is a 14-pin 0.5 mm USON. The repository's
`escape_check.py` classifies both as requiring `jlc_4layer_advanced`; retaining
standard four-layer would violate P-ESC.

## Options

- **Keep standard four-layer and force outward-only routing** — may be
  physically hand-routable, but contradicts the machine escape gate and leaves
  thermal/ground-pad treatment dependent on an undocumented exception.
- **Fall back to USB 2 only** — stays standard-tier and is explicitly allowed,
  but abandons the user's preferred USB 3 attempt before first article.
- **Use four-layer advanced** — meets the selected packages' checked escape
  requirement and retains the 5 Gb/s qualification target at added fab cost.

## Decision

Supersede ADR-0004 and select `jlc_4layer_advanced` for this USB 3-capable run.

## Consequences

The order instructions must state the advanced small-track/via option and its
reason. All widths, clearances and vias still use the largest practical values;
advanced capability is an escape ceiling, not a target everywhere. If the user
later requires standard-tier cost, the architecture reopens at USB 2 rather
than waiving P-ESC.


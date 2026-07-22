---
id: 0007
date: 2026-07-16
status: accepted
---
# 0007 — ILMT tied LOW (8 A valley limit) on BOTH rails

## Context

ADR 0003 set rail A's ILMT floating (12 A valley limit). Datasheet
extraction then corrected the inductor's saturation figure: FXL0630-1R5-M
Isat = 12 A (not 14 A as the catalog listing said). A 12 A valley limit
implies fault peaks ~13.3 A — beyond Isat, so the limit would be enforced
with a saturating inductor.

## Options

- **Rail A ILMT float (12 A)** — as ADR 0003. REJECTED: fault peak 13.3 A
  > Isat 12 A; current-limit behavior with a saturated inductor is
  unpredictable (runaway di/dt).
- **Bigger inductor (Isat > 14 A)** — larger/costlier part for a corner
  that a lower limit removes for free.
- **ILMT LOW on both rails (8 A valley)** — max deliverable load =
  8 + dI/2 = 9.25 A > 7.5 A required on rail A (margin 1.75 A even at
  -15% limit tolerance); fault peak = 8 + dI = 9.3 A < 12 A Isat. Both
  converter blocks become IDENTICAL.

## Decision

ILMT tied to GND (8 A valley limit) on both U1 and U2.

## Consequences

Rail A short-circuit current is capped near 9 A (was 13 A) — less copper
stress, inductor never saturates. The two buck blocks are now identical
except L value and FB routing. ADR 0003's "rail A floats ILMT" detail is
superseded by this ADR; part selection there is unchanged.

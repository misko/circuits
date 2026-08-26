# ADR-0017 — The FDZ's own recommended lead HAS lock slots; ADR-0008's decisive argument is retired

status: accepted
date: 2026-07-27
tags: connectors, flex, evidence, correction
amends: 0008 (its reasoning, not its conclusion); rehabilitates the ADR-0005 / D5 observation

## Context

ADR-0008 identified CN1 as a JST 10FDZ-BT top-entry ZIF and gave this as the
decisive basis:

> "the original OEM membrane keypad tail is a **plain tail (no punched
> lock-slots)** — consistent with a ZIF, inconsistent with a latch-slot
> receptacle (**a genuine FDZ would not use, or need, tail holes**)."

It thereby overturned ADR-0005 / D5, which had recorded from photos
(2026-07-22) that the OEM tail **does** have two punched lock-slots, and it
**dropped the lock-slots from our tail design** — called out at the time as
"the fiddliest, most failure-prone feature of the tongue is gone".

Designing the flex jumper (task #13) required going back to the drawing
ADR-0008 cites. Page 3, **"Recommended dimensions for membrane switch lead"**,
shows the lead with **two punched oblong slots**.

Measured off the drawing at 1200 dpi, scaled against its own printed
2.54 ±0.05 mm conductor pitch (72.44 px/mm):

| feature | drawing label | measured | read as |
|---|---|---|---|
| slot leading end, from the tail's insertion edge | 5 ±0.2 | 4.98 mm | ✓ |
| slot length | 3 ±0.2 | 2.99 mm | ✓ |
| slot centre, inboard of the OUTER conductor centreline | 3.81 ±0.1 | 3.796 mm | ✓ (= 1.5 × pitch, i.e. centred in the gap between conductors 2 and 3) |
| slot width | 1.2 ±0.1 | — | taken from the label |

The slots are symmetric — one at each end of the tail. eFDZ p.1 explains what
they are for: *"Secure locking mechanism — the membrane switch lead can be
locked using the slider."* The ZIF clamps; the slots let it **lock**.

## Options

- **Ignore it.** The identification is still well supported by the pitch
  (2.54) and the 22.86 mm circuit-1-to-circuit-10 span. REJECTED: the argument
  that was written down is now known to be false, and it is the argument, not
  the conclusion, that a future reader will reuse.
- **Reopen the CN1 identification.** REJECTED: nothing here contradicts
  10FDZ-BT. It removes a piece of *support*, and it re-admits D5's photo
  observation as **consistent with** an FDZ rather than evidence against one.
- **Correct the reasoning, and let the physical part settle the design
  question.** ACCEPTED.

## Decision

1. **The ADR-0008 clause "a genuine FDZ would not use, or need, tail holes" is
   WRONG and is retired.** JST's own recommended membrane-switch lead for this
   connector family is punched with two lock slots.
2. **The ADR-0008 conclusion stands**: CN1 is a 10FDZ-BT top-entry ZIF. It now
   rests on the geometry (2.54 mm pitch, 22.86 mm span, top-entry slider,
   housing 36.26 × 7.7 × 10.2) and on the user's photo identification — not on
   the plain-tail argument.
3. **D5 and D8 flatly disagree about a physical fact** — does the OEM tail have
   two punched slots or not? That is not resolvable from this repo. It is added
   to the physical-confirm sheet as item **S2**
   (`01_docs/10fdz-bt-land-pattern-confirm.md` §5), alongside **S1**: does the
   connector's slider carry lock pips positioned to catch such a slot?
4. **The flex jumper is built to answer it empirically.** The G1 coupon is a
   single double-ended tail with **one slotted end and one plain end**, so one
   part, one order, tests both against the real connector
   (`01_docs/flex-jumper-spec.md`). The production jumper follows whichever the
   coupon proves — slotted if the slider locks on it, plain if it does not.

## Consequences

- ADR-0008's design implication #1 ("the two lock-slots are DROPPED") is
  **provisional again** for the flex jumper. It remains correct for the
  *interposer*, which has no tail at all.
- The flex jumper's fab drawing must carry both variants until the coupon
  reports. Cost of carrying both: one extra outline feature on a $2 flex.
- **Method note.** ADR-0008 cited a datasheet it had extracted the land pattern
  from, and stated as fact something that same datasheet contradicts two panels
  above the drawing it used. The general rule this earns: when an ADR's
  *decisive* claim is about what a part does or does not have, quote the
  datasheet panel, do not summarise it. Both the false claim and the correction
  came from the same PDF, already sitting in `02_parts/10FDZ-BT/eFDZ.pdf`.
- No board changes. The interposer's copper, drill and netlist are untouched by
  this ADR; the sealed v1.0 release is not affected (and remains DO-NOT-ORDER
  for the unrelated CPL defect, task #18).

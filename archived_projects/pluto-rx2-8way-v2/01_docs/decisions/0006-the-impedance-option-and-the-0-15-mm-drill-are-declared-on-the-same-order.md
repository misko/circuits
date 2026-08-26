---
id: 0006
date: 2026-07-31
status: accepted
tags: [fab, vendor, spec-tension, impedance, via, order-gate]
---
# 0006 — the impedance option and the 0.15 mm drill are declared on the SAME order, and the vendor publishes one number that may forbid it

## Context

`ORDER_README.md` §0 puts two things on the same JLCPCB order and marks both as
not-a-default:

- **Via / process tier** — `jlc_4layer_advanced`, **0.25 mm pad / 0.15 mm
  drill**, ADVANCED small-via option **REQUIRED**. Required because the
  PE42482A-X QFN-24 sits on 0.50 mm pitch: at the standard 0.30 mm drill the
  adjacent-pin hole-to-hole gap is `0.50 - 0.30 = 0.20 mm`, so no escape via
  fits. This is arithmetic, not preference.
- **Impedance control** — **REQUESTED**, on stackup `JLC04161H-7628`. Requested
  because the board's product *is* impedance: nine equal-radius 14.00 mm GCPW
  arms whose relative phase is the deliverable, solved in ADR-0004 against that
  laminate's `h = 0.2104 mm`, `Dk = 4.4`, `t = 0.035 mm`.

**MEASURED 2026-07-31, on two independent channels** (a fab-orderability lens,
and a second agent that fetched the raw HTML with `curl` and stripped it by
hand after WebFetch's summariser was caught fabricating a "verbatim" quote):
JLCPCB's controlled-impedance capability page, `https://jlcpcb.com/impedance`,
publishes a three-column table whose cells are

| Min. Trace width/Spacing | **Min. Via** | Min. BGA |
|---|---|---|
| `3.5mil` | **`0.2mm`** | `0.25mm` |

**`Min. Via: 0.2mm` is ambiguous between a HOLE and a DIAMETER, and this
board's orderability flips on the reading:**

- if it means via **HOLE**: the board's 0.15 mm drill is BELOW the 0.20 mm
  figure, so its vias are under the impedance-controlled process minimum and
  the two options cannot both be had.
- if it means via **DIAMETER**: the board's 0.25 mm via pad is above the same
  figure, and there is no conflict at all.

**THIS ADR PUBLISHES NO BOUND, and the absence is declared rather than merely
arranged.** It carries no `<!-- bound -->` block because it derives no
inequality that governs a design quantity: the 0.20 mm above is the VENDOR's
number under a reading this document explicitly declines to choose, and the
board's 0.15/0.25 geometry is fixed elsewhere (`03_src/rules/nets.yaml`, from
the U_SW land width — see Consequences). If JLC answers "hole", the number that
lands here becomes a real bound and this ADR is amended to declare it with its
provenance, per canon B-OWED. Until then there is nothing to cite.

**The page does not settle it, and that was measured rather than assumed.**
Machine-counted over the page's full extracted text, the words `hole`, `drill`,
`annular`, `pad`, `aperture` and `finished` occur **0 times each**. There is no
tooltip, no note, no unit definition and no diagram. The bare label `Min. Via`
is the entire content. There is no evidence to weigh on each side because there
is no evidence at all.

What exists is CROSS-PAGE circumstance, which is inference and is labelled as
such here:

- the general capabilities page writes the pair explicitly —
  `Min. Via hole size/diameter` -> `0.15mm / 0.25mm`, with footnote
  `① Via diameter should be 0.1mm(0.15mm preferred) larger than Via hole size`
  — so JLC's own convention is *(hole, outer diameter)*, two numbers;
- its footnote `② Preferred Min. Via hole size: 0.2mm` names the same 0.2 mm
  **explicitly as a hole**;
- the small-via fee table's left column runs `0.15 / 0.2 / 0.25 / 0.3` and its
  Remark column says `Min via hole size` throughout.

All three tilt toward the HOLE reading. **None of them is on the impedance
page**, and the impedance page is the one that governs the impedance option.

## Options

1. **Read it as a diameter, order both, say nothing.** Cheapest, and it is the
   reading that lets the board through. It is also the reading whose only
   support is that it is convenient: every explicit use of `0.2mm` on JLC's own
   site attaches it to a hole.
2. **Read it as a hole and abandon impedance control.** Gives up the guarantee
   on the one property this board exists to deliver. The arms would still be
   fabricated to the same geometry — but unguaranteed, on a laminate JLC would
   be free to substitute, which voids ADR-0004's whole constant set.
3. **Read it as a hole and abandon the 0.15 mm drill.** Not available: the
   QFN-24 escape arithmetic above is what forces 0.15, and it does not move.
4. **Declare the tension, put it to the vendor in writing, and do not order
   until it is answered.** Costs a round-trip to JLC support before the first
   order.

## Decision

**Option 4.** The spec tension is recorded as an OPEN ORDER-BLOCKING item —
`ORDER_README.md` §7 item 6 — and the exact question is written out there for a
human to send. **This ADR does not pick a reading.**

The reason it does not is not caution. It is that options 1 and 2 are the same
decision seen from two sides, and the evidence that would separate them lives
in a sentence JLC has not written. A reading chosen here would be chosen by the
person who knows which reading lets the board ship, which is the failure mode
ADR-0005 on this same board exists to name: *an exception argument written by
someone who has just seen which numbers failed is not evidence, however good
the physics inside it.*

**The question, to be sent verbatim:**

> *"For a 4-layer 1.6 mm board on stackup JLC04161H-7628 with impedance control
> requested, is the 'Min. Via: 0.2mm' on your controlled-impedance capability
> page a via HOLE minimum or a via DIAMETER minimum, and can that order carry
> 0.15 mm drilled / 0.25 mm finished vias?"*

It sits beside the OTHER unanswered vendor question this board already carries
(§7 item 4: the mixed VIA-against-PTH-PAD hole-to-hole class, for which JLC
publishes a via-to-via floor and a pad-to-pad floor and nothing in between).
Both go in the same message.

## Consequences

- `order_verdict: DO-NOT-ORDER` gains a reason that is **independent of every
  copper defect**. DRC, parity, the standalone re-measure and the RF gates are
  all clean; this one is a question about what the vendor will accept.
- **If the answer is "hole":** the board cannot have both options as declared.
  The likely resolution is to keep the 0.15 mm drill (it is forced) and drop
  the impedance *guarantee*, then re-verify that the delivered stackup is still
  `JLC04161H-7628` — because ADR-0004's constants, and therefore the published
  phase table and the `lambda_pp/20 = 1.1910 mm` fence bound, are solved for
  that laminate and nothing else. That is a re-verification, not a re-layout.
- **If the answer is "diameter":** nothing changes; this ADR becomes the record
  of why it was asked, and §7 item 6 closes with the answer recorded beside it.
- **What is NOT a resolution:** a JLC quote that comes back priced. The
  capabilities and the quoting engine are different systems, and a price is not
  a statement that the combination was checked. Only a written answer closes
  this.

## Provenance

- `https://jlcpcb.com/impedance` — read 2026-07-31, raw HTML. The page carries
  **no last-updated string**. The often-quoted single-line form
  *"Min. Trace width/Spacing: 3.5mil | Min. Via: 0.2mm | Min. BGA: 0.25mm"*
  **is not page text** — it is a 3-column HTML table, and the pipe form is a
  reconstruction. Do not quote the pipe form as a vendor sentence.
- `https://jlcpcb.com/capabilities/pcb-capabilities` — read 2026-07-31, raw
  HTML. Also carries no last-updated string. Footnotes ① and ② quoted above are
  verbatim.
- Both reads corroborated on two independent channels on the same day.

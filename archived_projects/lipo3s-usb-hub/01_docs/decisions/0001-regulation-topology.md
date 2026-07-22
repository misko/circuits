# ADR-0001 — Regulation topology: two synchronous bucks, split by port class

Status: accepted (2026-07-20)

## Context

The board must deliver a 5 V USB rail to three USB-A ports (2.5 A each = 7.5 A
aggregate) and one USB-C port (6 A) from a 9.0–12.6 V 3S input. Total 13.5 A of 5 V
output, 68.6 W. The regulation topology and its partitioning is the core power decision.

## Decision

**Two independent LM5145 synchronous buck stages**, partitioned by port class:

- **Buck A → 5V_C (USB-C, 6 A).** Its own rail so the high-current single-port load is
  isolated from the USB-A bank; ILIM (RA2 348 Ω → ~6.3 A wc-min) directly bounds the
  6 A port.
- **Buck B → 5V_A (USB-A bank, 7.5 A aggregate).** Feeds the three per-port TPS2557
  switches; ILIM (RB2 432 Ω → ~7.8 A wc-min) is the aggregate backstop above the bank.

Both are the same synchronous controller + FET-pair + 3.3 µH stage at 606 kHz — a
proven, reviewed power stage (see DETAIL_DESIGN.md provenance).

**Sequencing:** Buck A's PGOOD enables Buck B (EN_B = PGOOD_A via divider). USB-C
(often the always-attached high-draw load) comes up first; the USB-A bank follows,
staggering inrush so the pack sees two soft-starts, not one 13.5 A step.

## Why not the alternatives

- **One big buck (13.5 A single rail).** REJECTED: a single 13.5 A synchronous stage
  needs larger/parallel FETs, a bigger inductor, and a much harder thermal + layout
  problem (one very hot switch node); a fault on any port pulls the whole rail; no
  natural inrush stagger. Two 6–7.5 A stages are each a well-understood, low-risk
  design and split the heat across the board.
- **Four independent bucks (one per port).** REJECTED: 2× the controller/FET/inductor
  count and board area for no benefit — the three USB-A ports are already isolated from
  each other by their per-port TPS2557 switches downstream of one shared rail.
- **A boost or SEPIC.** Not applicable — Vin (9–12.6 V) is always above the 5 V output;
  buck is correct.

## Consequences

- Two switch nodes (SW_A, SW_B) become the primary EMI aggressors — poured minimal-area,
  tight FET-inductor loops, kept off the sense taps (named tap rule areas).
- ~93 % efficiency assumed; ~8.2 A worst-case input at 9 V drives the fuse + front-end
  sizing (ARCHITECTURE.md).
- Rail-B ILIM margin over 7.5 A is thin by design (it is the protection point) — flagged
  for bench verification.

---
id: 0001
date: 2026-07-16
status: accepted
---
# 0001 — Two buck stages, not one 13.5 A rail

## Context
Total output is 67.5 W at 5 V (13.5 A). One converter or two?

## Options
- **Single 13.5 A buck** — fewer parts. REJECTED: inductor exceeds the
  verified MWSA1005S-3R3 (13 A rms); one hot loop carries everything; the
  USB-C port shares a rail with three switched ports, so an A-port short
  sags the C port; every power part becomes a new, unverified selection.
- **Two LM5145 stages (6 A + 7.5 A)** — exactly the topology/parts verified
  on the SPF power board (controller, FETs, inductor, comp, at 6 A/rail).
  Rail B runs 25% above the verified operating point but well inside
  component ratings. Costs ~$6 more.

## Decision
Two stages: buck A → 5V_C (USB-C, 6 A), buck B → 5V_A (3× USB-A, 7.5 A).

## Consequences
Port isolation between C and A banks; independent OCP per rail (buck A's
limit doubles as the C-port protection); rail-B ILIM and transient response
are the new-territory items — flagged for bring-up. Board area ~+15%.

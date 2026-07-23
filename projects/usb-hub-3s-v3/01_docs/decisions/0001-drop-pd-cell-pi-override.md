# ADR-0001 — USB-C 5A via Pi override, not a PD source controller

status: accepted
date: 2026-07-22
supersedes: usb-hub-3s-v2 ADR-0011 (PD source controller architecture)

## Context

The USB-C port must deliver **5V/5A** to a Raspberry Pi. In USB-C, advertising
5A normally **requires USB Power Delivery** negotiation of the 5A PDO (plus an
e-marked cable). That is why v2 carried the **TPS25740A** — a standalone fixed-5V
PD source controller in a 0.5mm-pitch VQFN-24 with two external pass FETs.

That single component was the **entire** source of v2's routing difficulty: its
fine-pitch power-stage edge could not escape cleanly (two background agents
froze on it, multiple grind attempts thrashed). The rest of the board — input
protection, two LM5116 bucks, three USB-A ports — routes without drama.

## Decision

**Drop the PD cell.** Deliver the USB-C port as a **plain regulated 5V/5A rail**
(the 5VC buck output brought directly to VBUS), and rely on the **Raspberry Pi
firmware override** to draw the full 5A without PD:

- Set `PSU_MAX_CURRENT=5000` in the Pi's bootloader EEPROM (or
  `usb_max_current_enable=1` in `config.txt`). This tells the Pi to **skip PD
  negotiation** and assume a 5A-capable supply; the Pi then draws up to 5A from
  any source that physically delivers it.
- The board provides: USB-C receptacle, two **CC pull-up (Rp) resistors** so the
  Pi detects an attached source + orientation, VBUS bulk caps, ESD, and an
  optional simple e-fuse / current-limit switch for short-circuit protection.

Removed vs v2: TPS25740A (U1), its two pass FETs (Q6/Q7), the gate resistor,
sense resistor, discharge resistor, and all PD-config strap passives.

## Alternatives considered

1. **Keep the PD controller (TPS25740A) — v2.** Compliant, works with any
   5A-capable USB-C device. REJECTED: it is the sole routing-hard part; this
   board is a dedicated Pi supply, so full USB-C-PD generality is not needed.
2. **5V/3A, no PD, no override.** Simplest; drops 5A. REJECTED: the spec is 5A
   (user-confirmed, for the Pi).
3. **Plain 5V/5A + Pi `PSU_MAX_CURRENT=5000` override — CHOSEN.** Simplest board
   that still delivers 5A. Trade: the USB-C port is **Pi-dedicated** (a generic
   USB-C device sees a non-PD source and would cap at 3A), and it relies on a
   one-time Pi EEPROM setting. For a fixed embedded LiPo->Pi supply, acceptable.

## Consequences

- The routing-hard QFN is gone; target fab tier drops to **STANDARD**.
- Port is Pi-specific by design (documented). Requires the Pi EEPROM setting
  (documented in the release README + a silk hint on the board).
- 5A-without-PD is out of strict USB-C compliance; acceptable for a
  non-consumer, fixed embedded supply. Use a short 5A-rated cable (T2).

## Executable invariants (E-ADR — this ADR emits assertions into
`03_src/rules/electrical_invariants.yaml`)

1. `net_has_no_part`: no part of `type: pd_source_controller` exists on the board
   (the PD cell is gone — a regression that re-adds it must fail).
2. `pin_on_net`: the USB-C receptacle VBUS pins are on the **5VC** rail net
   (VBUS is fed directly by the buck output, not through a PD pass-FET node).
3. `pin_on_net`: CC1 and CC2 each terminate on an Rp pull-up resistor to the
   source-present rail (a valid USB-C source advertisement exists).

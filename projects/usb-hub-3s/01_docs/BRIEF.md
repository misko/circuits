# brief: usb-hub-3s

status: active
prompt_sha256: b26444b8fbed5e2b6eee7713d3e4afa0e9e546fa99f8a33736157eb5da415230
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
> Ok lets try out our new system. Please from scratch start a new project, and lets design a board that takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max) and 1 x USB C port (6A max). Please internally research and make all design decisions. The output should be a fully designed , placed, routed board with JLCPCB manufacturing files
<!-- prompt-verbatim-end -->

- date: 2026-07-21
- channel: clean-room acceptance run (agent session), user AFK after commissioning

## Subsequent user directives (verbatim, amend the brief)

<!-- directives-verbatim-begin -->
> USB A is meant to be 2A and burstable 2.5

> USBC still needs to be 5A compliant

> min requirements are 2A USBA and 5A USBC
<!-- directives-verbatim-end -->

- date: 2026-07-21

## End goal — definition of done

A fully designed, placed, routed PCB that takes 3S LiPo power in on an XT60
connector and delivers three USB-A ports (2 A continuous each, 2.5 A burst)
plus one USB-C port able to deliver 5 A in a standards-compliant way, with a
complete verified JLCPCB manufacturing package (gerbers + BOM + CPL) released
per the release contract. For the user, an orderable board.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Input: 3S LiPo via XT60 (9.0–12.6 V envelope) | P | unmet |
| G2 | 3x USB-A ports, >=2 A continuous each, 2.5 A burst | P + D1 | unmet |
| G3 | 1x USB-C port, 5 A delivered standards-compliantly | P + D2/D3 | unmet |
| G4 | Battery/input protection (reverse polarity, fuse, UVLO, OV clamp) | skill mandate | unmet |
| G5 | Placed + routed, DRC 0/0/0 at --severity-all --refill-zones --schematic-parity | P | unmet |
| G6 | JLCPCB manufacturing package released (fab/, pdf/, source/, verification/, ORDER_README, MANIFEST) | P | unmet |

## Spec tensions (D-SPEC — fill at commission, before architecture)

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | "3 x USB A ports (2.5A max)" | USB 2.0 spec = 0.5 A; BC1.2 DCP = 1.5 A; common receptacle contact rating 1.5–1.8 A | 01_docs/decisions/0002-spec-tension-usba.md — user amended to 2 A cont / 2.5 A burst (D1); port built as BC1.2 DCP + legacy 2.4 A divider with a 2.5–3 A limit switch; receptacle current rating verified at part selection | yes (user issued D1) |
| T2 | "1 x USB C port (6A max)" | USB Type-C caps CC advertisement at 3 A; USB PD caps any contract at 5 A and requires an e-marked cable check above 3 A | 01_docs/decisions/0003-spec-tension-usbc.md — user amended to 5 A compliant (D2/D3); port implemented with a PD source controller that offers >3 A only after e-marker verification, 3 A fallback | yes (user issued D2/D3) |

## Log

(append-only)

- 2026-07-21 D1: user directive — "USB A is meant to be 2A and burstable 2.5".
  USB-A ports are >=2 A continuous, 2.5 A burst. Amends the prompt's "2.5A max".
- 2026-07-21 D2: user directive — "USBC still needs to be 5A compliant". The
  USB-C port must deliver 5 A in a standards-COMPLIANT way (PD contract with
  e-marked cable, not a bare Rp overclaim).
- 2026-07-21 D3: user directive — "min requirements are 2A USBA and 5A USBC".
- 2026-07-21 A1 (assumption, user absent): 3S LiPo envelope taken as
  9.0 V (3.0 V/cell floor) to 12.6 V (4.2 V/cell); UVLO set near 8.7–9.0 V
  to protect the pack (over-discharge), per the mandatory protection ADR.
- 2026-07-21 A2 (assumption): "6A max" on USB-C read as a capability ceiling,
  not a continuous requirement; D2/D3 supersede with 5 A compliant.
- 2026-07-21 A3 (assumption): no size/cost ceiling given. Fab tier defaults to
  the cheapest plausible tier and is raised only through D-TIER (see nets.yaml
  + tier ADR if raised).

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | USB-A = 2 A continuous / 2.5 A burst per port | user | brief |
| D2 | USB-C must be 5 A standards-compliant | user | brief |
| D3 | Minimums: 2 A USB-A, 5 A USB-C | user | brief |
| A1 | 3S envelope 9.0–12.6 V, UVLO ~8.7–9.0 V | agent (user absent) | architecture |
| A2 | "6A max" superseded by 5 A compliant | agent (user absent) | brief |
| A3 | No cost ceiling given -> cheapest plausible fab tier, D-TIER to raise | agent (user absent) | commission |

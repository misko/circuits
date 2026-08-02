---
id: 0001
date: 2026-07-31
amended: 2026-08-01
status: accepted
tags: [spec-tension, protection, topology]
---
# 0001 — USB-A 2 A is a proprietary high-current capability

The original commission requested 3 A from four USB-A sockets. USB 2.0 and
Battery Charging 1.2 do not provide a generic USB-A mechanism advertising that
entitlement. On 2026-08-01 the user lowered the guaranteed continuous output
to 2 A. That remains above ordinary USB 2.0 current and is documented as a
proprietary power capability, not as USB-IF charging-mode compliance.

Each port therefore provides standards-oriented USB 2.0 data plus an
independently protected 5 V / 2 A path. The exact connector remains cited for
at least 3 A continuous contact current, the eFuse low limit remains above 2 A,
and the complete mated-contact voltage path is graded. Host software must
distinguish electrical capability from what a legacy device is entitled to
draw. The original 3 A decision is superseded by this amendment.

# ADR-0002 — Dual independent 4 A buck rails

status: amended by ADR-0004
date: 2026-07-31
amended: 2026-08-01
tags: [topology, power, protection, thermal]

Two electrically independent LM5116 buck cells remain: rail A feeds ports 1
and 2, rail B feeds ports 3 and 4. After the user reduced the guarantee to 2 A
per port, each rail carries 4 A continuous. The common input is protected
before branching; a buck fault may remove its two ports but must not short the
other rail.

ADR-0004 replaces the original 7 A/250 kHz/BSC016 switching assumptions with
the exact 2 A delivery margin, AON6266E maximum-Qg switches, approximately
99 kHz nominal operation and explicit module trade studies. Machine checks
bind the converter inputs/outputs, feedback components, drive current, full
delivery resistance and rail assignment.

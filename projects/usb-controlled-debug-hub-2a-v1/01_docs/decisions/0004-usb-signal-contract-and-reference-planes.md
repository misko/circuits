# ADR 0004 — USB signal contract and adjacent reference planes

status: accepted for release repair; order-time impedance confirmation remains open
date: 2026-08-21

## Context

Release `v0.1.0-2026-08-21` routed all ten USB 2.0 differential pairs, but its
electrical authority was split. `route.yaml` carried a 0.50 mm per-wave
length-matching target while `nets.yaml` contained no realized-copper
`length_match` or `reference_plane_checks` declarations. The final compositor
therefore measured zero paths and zero planes, classified both checks `N-A`,
and still accepted the route.

The frozen copper review found several individual net segments more than
0.50 mm apart. That is not by itself the electrical path measurement: each
downstream functional link crosses an FSUSB42 data switch and is represented
by one hub-side plus one connector-side net per conductor. Segment differences
can add or cancel, so the release quantity is the ordered end-to-end chain.

Microchip's USB2517 hardware checklist requires 90-ohm differential routing,
short/direct protection placement, matched conductors, minimal vias and an
unbroken reference. TI's USB 2.0 layout guidance likewise requires a continuous
ground reference and matched differential routing. Neither cited document
publishes a numeric maximum PCB skew for this exact hub/switch/protector chain;
the numeric limit below is therefore an internal conservative design contract,
not a claimed USB specification limit.

Sources:

- Microchip, *USB2517 Hardware Design Checklist*, DS00004211.
- TI, *High-Speed Layout Guidelines for Signal Conditioners and USB Hubs*,
  SPRAAR7A.
- JLCPCB, *Controlled Impedance PCB Parameters and Stackup*, including
  JLC04161H-7628.
- JLCPCB, *User Guide to the JLCPCB Impedance Calculator*.

## Decision

Make `03_src/rules/nets.yaml` the executable release authority for realized
USB signal geometry:

- measure upstream and management pairs at 0.50 mm maximum P/N spread;
- measure each downstream port as one ordered hub-side plus connector-side
  chain through its series data switch, at 1.00 mm maximum end-to-end spread;
- treat each `route.yaml` 0.50 mm wave tolerance as a stochastic convergence
  target for that separately routed segment, not as a second release limit;
- price explicit vias and plated through-pad transitions from the adopted
  `[0.2104, 1.0650, 0.2104]` mm layer separations;
- declare B.Cu USB routes adjacent to In2.Cu GND and F.Cu USB routes adjacent
  to In1.Cu GND, with projected foreign-track/via clearance checks on both;
- keep the current 0.2332 mm width / 0.15 mm gap provisional until JLCPCB's
  final selected stackup and 90-ohm calculator/uploader preview are captured.

The final route gate must derive these checks as required from the non-empty
critical-pair inventory. Missing length or plane declarations are incomplete,
not non-applicable and never passing.

## Why

One millimetre of FR-4 trace corresponds to only several picoseconds, but the
chosen limit is not justified by that estimate alone. It is a tight,
reproducible board-owned symmetry ceiling, compatible with the predecessor's
reviewed USB contract and small enough to expose route drift without claiming
an unsupported standards number. Measuring the complete electrical chain also
prevents two opposing segment mismatches from being reported as two independent
link failures or, conversely, from hiding an accumulated end-to-end mismatch.

The reference-plane declarations turn an architectural statement into a saved-
board measurement. They remain a projected-obstacle check, not a field solve or
proof of filled-plane global continuity; those limitations remain explicit in
release evidence and first-article testing.

## Consequences and gates

- `copper_length_audit.py --strict` must measure every declared member and
  enforce all six group ceilings on the exact promoted board.
- `reference_plane_check.py` must grade both outer-layer/reference-layer
  relationships with nonzero declarations.
- full `route_acceptance_gate.py` requires both predicates and reports PASS,
  N-A, FAIL and INCOMPLETE separately.
- any required copper repair is source-owned in `03_src/route/final.kicad_pcb`
  and requires canonical rebuild, DRC/parity, critical-route, plane, model and
  release evidence renewal.
- ordering remains blocked until JLCPCB confirms the exact stackup,
  differential impedance geometry and coupon/controlled-impedance selection.
- first article must pass USB 2.0 High-Speed enumeration and sustained traffic
  on upstream, management and all four controlled downstream paths.

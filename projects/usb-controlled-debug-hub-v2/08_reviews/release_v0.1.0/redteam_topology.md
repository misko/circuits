# Exact-board topology and pin red-team — 2026-08-18

subject: usb-controlled-debug-hub-v2
board_sha256: 02956a64f67e0ef620fb060833dbc1d877e4b02bd7c79ede7cb901c6bf083719
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
- design P0/P1/P2: **0 / 0 / 1**

The two USB-C roles are non-overlapping: `J_POWER` negotiates 15 V through the
CH224K and local PD buck, while `J_DATA` carries upstream USB 2.0 plus VBUS
sense and cannot source the downstream power trunk. Protection, aggregate
eFuse, per-port switches, data-switch safe states and hub power-control paths
remain coherent. DRC/parity is 0/0/0; blocking ERC is zero; electrical policy
has zero FAIL; route acceptance is 9/9.

The exact C503996 catalog library provides the electrical contact numbering for
the KH-AF90DIP-112 receptacles; the manufacturer drawing supplies geometry.
The release twin confirms the exact pad/body mapping on all four ports.

P2 observation: production confidence still requires first-article no-backfeed,
15 V negotiation, 5 V load regulation, port-current, thermal and sustained USB
2.0 High-Speed tests. These are validation requirements, not a demonstrated
schematic defect.

Order remains blocked solely because exact quantity-5 uploader allocation,
resolved-BOM echo, MOQ/cost and final manufacturing previews are not local
evidence yet.

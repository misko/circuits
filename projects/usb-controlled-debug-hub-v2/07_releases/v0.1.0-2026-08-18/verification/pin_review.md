# Exact-board pin review — 2026-08-18

subject: usb-controlled-debug-hub-v2
board_sha256: 02956a64f67e0ef620fb060833dbc1d877e4b02bd7c79ede7cb901c6bf083719
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

The exact schematic/PCB subject has 0 schematic-parity findings and the
declared electrical invariants and policy audit have zero FAIL. The dedicated
power connector routes only PD power negotiation; the data connector routes
USB 2.0 plus upstream VBUS sense. CH224K profile straps, TPS56637 buck pins,
aggregate eFuse, five port-power switches, four USB data switches, hub-control
pins, crystal, reset and management I/O match their exact dossiers.

For all four C503996 receptacles, the exact JLC/EasyEDA catalog library binds
contacts 1=VBUS, 2=D-, 3=D+, 4=GND; the exact Kinghelm drawing binds the
mechanical contact row and shell geometry. The project footprint and JLC twin
preserve that numbering and orientation. No unresolved pin-map defect remains.

Order is blocked by missing JLC uploader allocation and preview evidence, not
by a pin-review finding.

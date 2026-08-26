# Exact-board render review — 2026-08-18

subject: usb-controlled-debug-hub-v2
board_sha256: 02956a64f67e0ef620fb060833dbc1d877e4b02bd7c79ede7cb901c6bf083719
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

Verdict: **PASS**. The populated JLC twin mounts 162/162 CPL placements. The
dedicated power USB-C, upstream data USB-C and four downstream USB-A connector
mouths face outward and their contacts remain seated on the intended lands.
The current connector review set is machine PASS 6/6 and was explicitly
approved by the user/product owner 6/6. Manufacturer-authoritative footprint
differences for `L_PD` and `D_PD_TVS`, and the asymmetric USB-C body registration,
are recorded in `twin_adjudications.yaml`; none changes placement or rotation.

Final assembly-preview rotation/polarity and THT mappings remain an order-time
human gate because a local render cannot prove JLC's uploader interpretation.

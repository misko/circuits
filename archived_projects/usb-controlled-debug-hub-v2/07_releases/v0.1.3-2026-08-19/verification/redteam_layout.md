# Final adversarial layout/fabrication review — v0.1.3

reviewed_at: 2026-08-19
subject: usb-controlled-debug-hub-v2
board_sha256: b1c042c695af896b18627c596406157bc5522561c31ac60cc353b11ff065d197
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
P0: 0
P1: 3
P2: 1

The exact staged board passes native DRC/parity 0/0/0, critical-pair
connectivity 10/10, reference-plane projection, USB length 6/6 groups, and
165/165 twin body coverage. The final component overlays pass and preserve the
approved connector geometry.

The three P1 order gates are: obtain JLC's final 90-ohm stackup solve; confirm
selective Type-VII treatment for exactly 498 0.46/0.20-mm vias while leaving
11 ordinary 0.70/0.35-mm vias untreated; and save the full rotation, polarity,
THT, and connector previews. P2 is physical first-article drop, load, thermal,
and USB signal validation.

# Final pin review — v0.1.3

review_kind: pin
subject: usb-controlled-debug-hub-v2
reviewed_at: 2026-08-19
board_sha256: b1c042c695af896b18627c596406157bc5522561c31ac60cc353b11ff065d197
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

The exact normalized circuit and routed board preserve the reviewed USB-C PD,
hub, data-switch, port-eFuse, control, and protection topology. The new
TVS1800DRVR and TPS259804ONRGER pin maps are backed by their exact part
dossiers and invariants. No unresolved functional pin swap or NC misuse was
found. JLC's order preview must still confirm D_PD_TVS pin 1 and all
single-channel rotations before payment.

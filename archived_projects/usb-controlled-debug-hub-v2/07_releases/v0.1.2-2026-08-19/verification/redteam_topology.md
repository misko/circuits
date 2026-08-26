# Adversarial topology/ratings review — v0.1.2

subject: usb-controlled-debug-hub-v2
board_sha256: a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987
schematic_sha256: 36f04e308ec6f950264ec352fde4236d4b91c77af314528a393f6ebe7b61ab2d
tsx_sha256: 6c6b58422cbc0317e371cc6487940f07a06a7ef41bfa14e0758af1929444fa8b
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
design P0/P1/P2: 0 / 0 / 2

This representation-only supersede has the exact v0.1.1 PCB, schematic, TSX,
netlist, Gerbers, BOM and CPL. Its sole source delta selects which already
approved 3D representation is mounted in verification. There is therefore no
new electrical topology, pin-map, rating or manufacturing-data delta.

The earlier reverse-backfeed and pre-contract bulk-capacitance findings land.
All four externally driven USB-A VBUS paths now pass through exact
TPS259470A true-reverse-blocking eFuses; the internal management TPS2557 is
retained only on the captive management load. A fifth TPS259470A gates the
buck input, leaving only 0.1 uF exposed before negotiation and enforcing the
source-owned UVLO/OVLO/dVdt contract.

The power path is coherent: USB-C POWER -> 3 A fuse/TVS -> CH224K negotiation
-> input eFuse -> 5 V buck -> aggregate latch-off reverse-blocking eFuse ->
four protected ports plus captive management/control loads. USB-C DATA VBUS
is sense-only. The exact netlist has 121/121 electrical invariants, 5/5 cited
topology ADRs, 0 blocking ERC errors and 0 PCB parity errors.

P2 observations: reverse leakage and coordinated overload behavior remain
physical first-article measurements; and the 2.58 A declared continuous load
is close enough to the 2.990 A worst-low aggregate threshold that hot voltage
drop/temperature qualification is mandatory. Neither is a demonstrated
schematic defect.

The exact order response is blank, so no allocation or preorder economics are
proven. This review does not authorize payment.

# Exact-board pin review — v0.1.2

subject: usb-controlled-debug-hub-v2
board_sha256: a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987
schematic_sha256: 36f04e308ec6f950264ec352fde4236d4b91c77af314528a393f6ebe7b61ab2d
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

This representation-only supersede leaves the exact schematic, PCB, netlist,
BOM and CPL unchanged from v0.1.1. The USB-C change is a verification-model
selection only; no pin, pad, net, coordinate or rotation changed.

The exact schematic export and routed PCB agree over 123/123 nets and 560/560
connected nodes. Native DRC reports zero schematic-parity findings. The pin
audit resolves 26 critical multi-pin references from exact-MPN dossiers,
including both USB-C connectors, all four USB-A connectors, the hub, CH224K,
both regulator stages, both eFuse families, data switches and control ICs.

`J_POWER` routes only PD negotiation/power contacts. `J_DATA` routes USB
2.0 and the high-impedance upstream VBUS detector only. Each
`TPS259470ARPWR` uses IN=5, OUT=6, GND=8, ILM=9, active-low open-drain
FLT=4, with external-port OVLO grounded and the input-gate UVLO/OVLO divider
on the exact intended pins. No pin-map, lane-polarity or connector-numbering
defect remains.

Order remains blocked by the incomplete 0/54 JLCPCB uploader response and
unreviewed manufacturer previews, not by an electrical pin finding.

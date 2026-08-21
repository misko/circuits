# Final pin review — v0.1.0

reviewer: Codex primary agent, exact-artifact pin lens
reviewed_on: 2026-08-21
project: usb-controlled-debug-hub-2a-v1
subject: usb-controlled-debug-hub-2a-v1 v0.1.0 exact final board
board_sha256: 9eb649598aeecac74ce04347ea5d20e516fdebb58fd9a04948c71446a9c83e24
pcb_sha256: 9eb649598aeecac74ce04347ea5d20e516fdebb58fd9a04948c71446a9c83e24
schematic_sha256: 5c2513661ebd807df4a6c0a045d99fc910c7f09a6c255eb433660b1254f9612c
netlist_sha256: 77d1bf722472929bcc27dd8de4657bc5d1b92977b60be6f25b5adeae42955590
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

The exact release BOM produced 29 digest-bound pin dossiers for every active,
connector, converter, protection, switch, hub, crystal and controller family.
No pin-number, net-role, exposed-pad or connector-polarity conflict was found.
The exact PCB also passes schematic parity with zero findings and the source
electrical-invariant battery remains satisfied.

The power-only USB-C input, data-only upstream USB-C connector, four USB-A
ports, dual buck banks, aggregate eFuses, per-port switches, FSUSB42 data
multiplexers, USB2517 hub, MCP2221/MCP23017 control path and their safe-state
pull networks agree with the reviewed pre-route topology. J_DATA VBUS is only
a hub-detect input; it cannot source the board. J_POWER is the sole energy
input and requires a fixed 20 V / 3 A PD source.

P0 findings: none.

P1 order blockers: exact JLC allocation and uploader BOM echo are not yet
captured. The release remains DO-NOT-ORDER until those external previews are
accepted.

P2: this final review was performed by the active primary agent with full
project context, not an independent fresh-context reviewer. Hash binding and
machine parity prove currency, not reviewer independence.

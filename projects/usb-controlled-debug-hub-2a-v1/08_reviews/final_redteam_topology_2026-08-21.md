# Final topology red-team — v0.1.0

reviewer: Codex primary agent, adversarial topology lens
reviewed_on: 2026-08-21
project: usb-controlled-debug-hub-2a-v1
subject: usb-controlled-debug-hub-2a-v1 v0.1.0 exact final board
board_sha256: 9eb649598aeecac74ce04347ea5d20e516fdebb58fd9a04948c71446a9c83e24
pcb_sha256: 9eb649598aeecac74ce04347ea5d20e516fdebb58fd9a04948c71446a9c83e24
tsx_sha256: eca35234c7ad6bbc97583296124942d209e9d911b97b7dc43be0180e53c1f9a9
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

No fabricated-topology defect was found. DRC, unconnected and schematic
parity are 0/0/0; route acceptance is 9/9; the policy audit has zero FAIL;
the exact fab BOM is source-identical and legible; and all four external
output claims close at 5 V / 2 A per port under the adopted 20 V / 3 A input
architecture.

The adversarial checks specifically covered reverse/backfeed paths, default
USB-C 5 V operation, bank overload coordination, one-port and four-port load
states, data-connect-without-power prevention, upstream-VBUS isolation,
control-reset defaults, aggregate latch-off behavior and the absence of a
connector-to-rail bypass. The architecture intentionally rejects a source
that cannot negotiate 20 V; 15 V / 3 A is not a supported full-load source.

P0 findings: none.

P1 order blockers: obtain a quantity-five JLC order-interface allocation
receipt; verify every resolved BOM code/MPN; accept all single-channel
rotation and polarity previews; confirm both USB-C THT/SMT mappings; and
complete the order-time 90-ohm stackup solve.

P2 first-article obligations: current-limit each initial power-up; verify
20 V negotiation before enabling the downstream rails; measure both 5 V
banks at 4 A, every port at 2 A, cable-end voltage, connector temperature,
switch/eFuse/buck temperature and back-injection with one source absent.

This is a primary-agent review, not a fresh-context independent review.

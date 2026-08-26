review_kind: redteam_topology
subject: pi-usb-port-switch v0.1.0 hardware topology
date: 2026-08-15
reviewer: Codex adversarial topology, protection and ratings lens
evidence_scope: exact pre-seal staged hardware archive
board_sha256: d4bc778c1c80453ec7b198e1bf428b22cb03d414c4a0d86c89ab74d6facc4094
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Adversarial topology review

The exact source implements four independent one-to-one channels, not a hub.
Each channel switches USB 2 D+/D- with TS3USB221E, controls both SuperSpeed
directions through a TUSB522 shutdown path, and switches externally supplied
VBUS through a TPS2557. Upstream USB VBUS is absent from the protected external
rail. Ground and shell reference are common and never user-switched.

The GPIO map is eight independent 3.3 V commands with series protection and
100 kohm hardware pull-downs. `DATA_OK = PWR_EN AND DATA_EN`; the active-low
USB 2 disconnect and SuperSpeed shutdown derive from that interlock. Therefore
floating GPIO, Pi reset, Pi power loss, and the forbidden PWR=0/DATA=1 command
all leave data disconnected. No MCU, firmware or host daemon is required.

Component identity agrees across source, schematic, netlist and board for
190/190 electrical parts. Electrical invariants pass 282/282, ERC has zero
error-severity findings, and final PCB DRC is 0 violations / 0 unconnected /
0 parity findings. Power-tree checks cover all four 0.9 A outputs and the local
3.3 V converter. The 5.15-5.25 V input requirement and first-article hot-drop
measurement are explicit rather than hidden as assumed margin.

No unresolved design finding remains under this lens. Ordering is still
blocked on the named JLC stackup/impedance echo, selective via-process echo,
THT/BOM/rotation previews and first-article qualification.

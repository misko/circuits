# Commission journal

## 2026-07-31 09:10 — start
- did: Parsed the verbatim brief and asked for the four design-defining facts required by the PCB-design commission gate.
- result: MEASURED from Q1: four USB-A ports, 12–24 V / >=75 W input, physical D+/D- disconnects, and both commanded plus enumeration status.
- next: Record the USB-A 3 A spec tension and run the spec-critical sourcing spike before architecture.

## 2026-07-31 — Pluto+ load checkpoint and rail topology
- did: Checked the Pluto+ project's published input specification after the user asked whether USB-A loads really exceed 1.5 A.
- result: MEASURED source rating is 5 V / 2 A per Pluto+; four units imply a 40 W application budget, but the requested board envelope stays 3 A per port.
- decision: Two proven 5.15 V / 7 A LM5116 rails, two ports per rail (ADR-0002), with a fifth internal hub port for the control MCU (ADR-0003).
- next: Close exact hub, MCU, per-port switch, connector, and input-protection dossiers.

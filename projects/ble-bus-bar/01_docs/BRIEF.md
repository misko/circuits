# BRIEF — ble-bus-bar

<!-- prompt-verbatim-begin -->
12-24v BLE bus bar with 6 ports, each fused (up to 30A). Each port has a shunt and can report statistics back through BLE + onboard memory.
<!-- prompt-verbatim-end -->
sha256: 89d12ed993070464a747db400258a7d9fd83e61f863fac7d7ff12ae8e85b8675

## Parsed requirements
- P1: Input 12–24 V DC bus (automotive/solar/battery range).
- P2: 6 output ports, each individually fused, each rated up to 30 A.
- P3: Per-port current shunt with per-port statistics.
- P4: Telemetry reported over BLE.
- P5: Onboard memory for logged statistics (survives BLE absence).

## Commission Q&A (user answered 2026-07-18)
- Q1: Aggregate simultaneous current? → A1: **~60 A aggregate** (any port may peak 30 A; total bus + input feed sized for 60 A continuous).
- Q2: Ports switchable via BLE? → A2: **Monitor-only** (fuse + shunt + telemetry; protection = fuse).
- Q3: Fuse style? → A3: **ATO/ATC blade holders** (user-replaceable automotive blades, PCB-mount).

## Decisions (D#, appended over time)

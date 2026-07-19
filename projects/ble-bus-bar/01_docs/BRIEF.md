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

## End goal — definition of done

An orderable, verified JLCPCB release of a 12–24 V / 60 A bus bar PCB.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | 12–24 V input, 60 A aggregate continuous | P, A1 | met — DETAIL_DESIGN #1 (trunk 1.5×), 07_releases/v1.0-2026-07-19 |
| G2 | 6 ports, each ATO-blade fused, up to 30 A | P, A3 | met — 6× 3557-2 holders + 10.5 mm port pours (ADR-0005/0002) |
| G3 | Per-port shunt current sensing with statistics | P | met — 6× INA238 + WSLP2726, Kelvin-checked (audit IK) |
| G4 | BLE telemetry (stats reported wirelessly) | P | met — ESP32-C3-WROOM-02, antenna keepout audited (IA) |
| G5 | Onboard memory logging (survives BLE absence) | P | met — W25Q64JV 8 MB dedicated log flash (ADR-0004) |
| G6 | v1.0 release: DRC/ERC/parity 0, gates green, MANIFEST from clean tree | pipeline | met — 07_releases/v1.0-2026-07-19 |

## Decisions (D#, appended over time; agent decisions under P-delegation)

### D1 — 2026-07-18 — positive-rail-only distribution
The board distributes +12–24 V only; load returns go to battery/chassis,
not through the board. GND is a low-current reference stud for the
electronics, silk-marked "NOT LOAD RETURN". Authority: P-delegation
(automotive bus-bar norm). Escalate if: user expects return terminals.
Impact: halves the high-current copper; ARCHITECTURE ground strategy.

### D2 — 2026-07-18 — bolted ring-lug studs instead of screw terminal blocks
M5 stud input, M4 stud per port + GND-ref; hardware user-supplied with
torque specs in ORDER_README. Rationale: ADR-0005 (no genuine 30 A PCB
terminal blocks in the JLC catalog; lugs are the 60 A gold standard).

### D3 — 2026-07-18 — 2-layer 2 oz copper, paired pours
Layer count + copper service call: ADR-0002 (margins 1.5×/1.24×;
4-layer and 4 oz and exposed-copper rejected there).

### D4 — 2026-07-18 — INA238 per port + WSLP2726 0.5 mΩ shunts
Sensing chain: ADR-0003. INA3221/INA226 rejected on abs-max vs the
SMCJ33A clamp; per-port monitor keeps Kelvin runs ≤3 mm.

### D5 — 2026-07-18 — ESP32-C3-WROOM-02-N4 + dedicated W25Q64 log flash
ADR-0004. MINI-1 is JLC stock-dead; nRF52 2–3× price. USB-C native
USB-Serial-JTAG for flashing; dedicated 8 MB NOR for the stats ring.

### D6 — 2026-07-18 — protection: fuse+TVS+diode on the electronics branch only
ADR-0001. No series element at 60 A; SMCJ33A bus clamp; reverse
polarity residual risk documented with silk + ritual mitigations.

### D7 — 2026-07-18 — LMR16006X buck + AMS1117 USB co-power
ADR-0006. 60 V-tolerant buck (survives clamp without TVS speed
assumptions); USB bench power diode-OR'd at ≈3.0 V.

### D8 — 2026-07-18 — Keystone 3557-2 fuse holders, fuses user-supplied
ADR-0005. Insulated 30 A UL holder, vertical entry; ORDER_README notes
the ATO 80 % continuous derating convention.

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| D1 | +rail-only distribution, GND = reference stud | agent (P-delegation) | this file |
| D2 | ring-lug studs M5/M4, user hardware | agent (P-delegation) | decisions/0005 |
| D3 | 2L 2 oz, paired pours, ampacity floors | agent (P-delegation) | decisions/0002 |
| D4 | INA238 + WSLP2726 0.5 mΩ high-side | agent (P-delegation) | decisions/0003 |
| D5 | ESP32-C3-WROOM-02 + W25Q64JV | agent (P-delegation) | decisions/0004 |
| D6 | electronics-branch protection, bus TVS, no 60 A series element | agent (P-delegation) | decisions/0001 |
| D7 | LMR16006X buck + USB LDO co-power | agent (P-delegation) | decisions/0006 |
| D8 | Keystone 3557-2 holders, fuses user-supplied | agent (P-delegation) | decisions/0005 |

---
id: 0005
date: 2026-07-17
status: accepted
---
# 0005 — Sourcing tally (Basic/Extended) + connector set

## Rules (P/A4 + pipeline convention)

JLC in-stock only, Basic preferred, minimize unique Extended reels, all
SMD on the top side, THT connectors hand-solder (uncoded in BOM, listed
in MANIFEST not_assembled).

## The tally (assembled SMD lines, live stock 2026-07-17)

**Extended, unique = 12 (each irreplaceable in Basic):**

| Part | LCSC | Why no Basic |
|---|---|---|
| ESP32-S3-WROOM-1-N8R2 | C2913204 | no Basic MCU modules |
| TMC2209-LA-T | C2150710 | no Basic stepper drivers (ADR-0002) |
| MPR121QR2 x4 | C91322 | the only real MPR121 (ADR-0004) |
| LIS2DH12TR | C110926 | no Basic accelerometers |
| AP63205WU-7 | C2071056 | no Basic 2A 12V-in buck |
| USBLC6-2SC6 (UMW) | C2687116 | no Basic USB ESD array |
| TYPE-C-31-M-12 | C165948 | no Basic USB-C |
| AOD4185 | C400894 | no Basic P-FET at 40V/15mOhm (ADR-0001) |
| SMBJ16A | C10211 | no Basic 600W TVS (ADR-0001) |
| SMD1812P200TF16 | C20812 | no Basic 16V polyfuse (ADR-0001) |
| SWPA6045S100MT 10uH | C79272 | no Basic shielded power inductor |
| RVT1E101M... 100uF/25V | C2836443 | no Basic >=100uF/25V electrolytic |

**Basic (10 unique):** AMS1117-3.3 C6186; TS-1187A-B-A-B C318884 (BOOT/
RESET); KT-0805G LED C2297; caps 0805: 100nF C49678, 1uF C28323,
4.7uF/25V C1779, 22uF/25V C45783; resistors 0805 1%: 100R C17408,
1k C17513, 4.7k C17673, 5.1k C27834, 10k C17414, 100k C149504.
(0805 family carry-over from esp32-laser-timing ADR-0003: Basic 0603
has stock gaps at 1k/10k; one 0805 family, deep stock.)

## Connectors (all THT hand-solder, uncoded; codes recorded for jlc_twin)

| Ref | What | Part | Code |
|---|---|---|---|
| J1 | 12V barrel jack 2.0mm | DC-005C-20A | C84007 |
| J2 | USB-C (SMD but hand-solder-able; ASSEMBLED — SMD, so it IS coded/assembled) | TYPE-C-31-M-12 | C165948 |
| J3 | ELECTRODES INNER 1-12 + GND, 1x13 2.54 header | KH-2.54PH180-1X13P-L11.5 | C2932703 |
| J4 | ELECTRODES OUTER 1-12 + GND, 1x13 2.54 header | KH-2.54PH180-1X13P-L11.5 | C2932703 |
| J5 | MOTOR 4-pin JST XH (A1 A2 B1 B2) | B4B-XH-A(LF)(SN) | C144395 |
| J6 | ENDSTOP 2-pos screw terminal (SIG GND) | KF128L-3.5-2P | C474930 |
| J8 | HOST header 1x6 2.54 (5V 5V GND GND TX RX) | generic 2.54 header | uncoded |

XH for the motor (NEMA17 harnesses ship XH/Dupont), screw terminal for
the endstop (user wires a bare microswitch), pin headers for the 24
electrode harness (matches the prototype's Dupont-style taped harness;
a 10k-unit optimization to FFC lives in COST_ESTIMATE.md). J2 USB-C is
SMD and machine-assembled (coded), not hand-solder.

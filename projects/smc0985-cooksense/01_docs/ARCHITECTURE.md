# architecture: smc0985-cooksense

The ribbon-interception core for the SMC0985KS: a firmware-less CookSense
board (sensing + hardware safety + 12-relay matrix selector, Pi-5-driven)
plus a passive coupon-gated keypad interposer. Full source: BRIEF.md
(verbatim Rev 1.0 + decision register D1-D6), ADRs 0001-0006.

## System block diagram

    OEM membrane ──10-wire tail──> [C INTERPOSER] ──flex tongue──> OEM CN1
      (panel keeps working)             │                    (latched — ADR-0005)
                                        │ 10 lines (isolated keypad domain)
                                        v
    ┌─────────────────────── COOKSENSE (A+B merged per ADR-0001/D4) ──────────┐
    │  KEYPAD ZONE (>=6mm isolation, milled slots, no planes, no shared GND)  │
    │    12x reed relay: 6 U-sel ── 4 D-sel ── K_PRESS(RKEY) ── K_STOP(RSTOP) │
    │  ── isolation boundary ────────────────────────────────────────────────  │
    │  74HC595 x2 -> 2x SN74HC238 DECODERS (one-hot, active-HIGH!) -> ULN2803A │
    │       -> coils   (brief's '138/'139 were active-LOW; corrected ADR-0002) │
    │  coil RAIL gated by AND-chain: MODE_AUTO_HW·WD_OK·ESTOP_OK·TEMP_OK·     │
    │      MCU_RELAY_ENABLE·HOST_AUTH·FAULT_LATCH_CLEAR   (all discrete HW)   │
    │  74HC123 one-shot caps PRESS <=500ms · TPS3823 watchdog · HW fault latch │
    │  SENSING: MCP3208 8ch thermistor + LM393 comparators -> TEMP_OK          │
    │           MAX31856 K-TC · HX711 link (J_LOADCELL) · door/E-stop/mode     │
    │  MCP23017 expander: switched rails, readbacks, BOARD_ID (ADR-0003)      │
    │  Pi 40-pin header: shift-reg lines, heartbeat, auth, SPI, I2C pass-thru │
    └──────────────────────────────────────────────────────────────────────────┘
              ^ 40-pin (HAT or sidecar — keepout analysis decides)
    Raspberry Pi 5: RGB cams, OCR, LLM->validator, logging, UI
      + MLX90640 x2 & SHT45 x2 on Pi-native I2C (4 buses, ADR-0004;
        pullups on CookSense from SWITCHED rails — phantom-power rule N1)

## Power
5V SELV in (Micro-Fit, fuse + reverse-pol + OV/eFuse + TVS + bulk +
power-good) -> 5V_PROTECTED -> gated 5V_KEY_RELAY rail (AND-chain);
3V3 rails LINEAR (AMS1117-class + per-sensor switched high-side) —
NO switching converter on the board => E-TOPO N-A (all-linear; total
budget ~<1A: 12 reed coils ~120mA worst + logic + sensors). Pi header
5V/3V3 are NC/sense only; no backfeed either direction (Ioff buffers).

## Safety model (ADR-0002)
All enforcement is hardware: decoder one-hot selection, one-shot press
cap, external watchdog, E-stop dual-loop, Manual-mode physical rail cut,
comparator TEMP_OK, discrete fault latch w/ manual re-arm. The Pi (and
the LLM behind it) can at most press valid keys — the hazard class the
OEM controller already survives. Executable invariants due at schematic
gate (E-ADR holds ADR-0002/0006 open until then — intended).

## Proven reuse
cook-hub v1.0: DIP05-1A72-12L relay cell + driver pattern, MAX31856,
protection parts. cook-loadcell v1.0: reused unmodified (Board D).
crow-recorder archetype: band separation (keypad zone / analog spine /
digital+Pi band) guides the floorplan.

## Gates
Brief §14 G1-G10 adopted verbatim. G1/G2 (connector measurement + coupon)
BLOCK Board C; G4/G5 bench-only bring-up BLOCK any appliance connection;
G8 starts with harmless keys (TIMER) + OCR observation.

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
    │  CD74HC221 NON-retrig one-shot caps PRESS <=436ms worst (<500ms HARD) · │
    │  TPS3823 watchdog · HW fault latch (WD·ESTOP·TEMP set) · STOP preempts  │
    │  in HW (clears PRESS, disables both decoders, K_STOP on its own         │
    │  always-available 5V_STOP rail) · contactor HW-gated (ADR-0011, v1.2)   │
    │  SENSING: MCP3208 8ch thermistor + LM393 comparators -> TEMP_OK          │
    │           MAX31856 K-TC · HX711 link (J_LOADCELL) · door/E-stop/mode     │
    │  MCP23017 expander: switched rails, readbacks, BOARD_ID (ADR-0003)      │
    │  Pi 40-pin header: shift-reg lines, heartbeat, auth, SPI, I2C pass-thru │
    └──────────────────────────────────────────────────────────────────────────┘
              ^ 40-pin (HAT or sidecar — keepout analysis decides)
    Raspberry Pi 5: RGB cams, OCR, LLM->validator, logging, UI
      + MLX90640 x2 & SHT45 x2 on Pi-native I2C — TWO shared sensor buses
        per the brief §3 verbatim plan (bus A GPIO4/5 = cam A 0x33 + ambient
        SHT45 0x44; bus B GPIO14/15 = cam B + exhaust SHT45) + I2C1 GPIO2/3
        for the MCP23017; map VERIFIED against the RP1 datasheet and
        published in 01_docs/pin_map.md (ADR-0010, v1.2; pullups on
        CookSense from SWITCHED rails — phantom-power rule N1)

## Power
5V SELV in — **SPECIFIED 4.85-5.25 V at J_PWR under load (ADR-0021); this
is a COMMISSION FACT, not advice, and the board is not qualified outside
it** — (Micro-Fit, fuse + reverse-pol + OV/eFuse + TVS + bulk +
power-good) -> 5V_PROTECTED -> gated 5V_KEY_RELAY rail (AND-chain)
AND (v1.2) -> 5V_STOP (0R link, UNGATED): K_STOP's always-available
coil rail — the STOP relay survives the faults that kill the key rail
(ADR-0011 §4; see power_tree.yaml);
OV cutoff setpoint: R_OVT 100k / R_OVB 26.1k (both +-0.5%) against
SLVSE57C V_OVLO(R) => **5.798 V nominal**, worst case cannot trip below
5.3682 V and HAS tripped by 6.2394 V (ADR-0021). v1.2-v1.6 carried
100k/15k = 9.200 V, above both the SMBJ5.0A's 6.40 V V_BR min and the
DIP05 coil's 7.5 V max — the v1.7 P0;
3V3 rails LINEAR (AMS1117-class + per-sensor switched high-side) —
NO switching converter on the board; since 2026-07-27 E-TOPO GRADES the
all-linear rail rather than skipping it (dropout + dissipation), and with
the ADR-0021 envelope it PASSES: headroom 1355 mV vs 1300, PD 615 mW /
51% (total budget ~<1A: 12 reed coils ~120mA worst + logic + sensors). Pi header
5V/3V3 are NC/sense only; no backfeed either direction (Ioff buffers).

## Safety model (ADR-0002, hardened v1.2 by ADR-0011)
All enforcement is hardware: decoder one-hot selection, NON-retriggerable
one-shot press cap (CD74HC221), external watchdog, E-stop dual-loop,
Manual-mode physical rail cut, comparator TEMP_OK (68k/10k threshold =
74.9C hard stop, solder-select field), discrete fault latch (set by
WD·ESTOP·TEMP) w/ manual re-arm, STOP hardware preemption (clears PRESS,
disables both decoders, dedicated always-available K_STOP rail), and a
hardware contactor gate (REQ·WD·ESTOP·TEMP·LATCH_CLEAR). The Pi (and the
LLM behind it) can at most press valid keys — the hazard class the OEM
controller already survives. Every ADR-0010/0011 claim is an executable
E-INV assertion graded at the schematic gate.

## Proven reuse
cook-hub v1.0: DIP05-1A72 relay cell + driver pattern (cooksense specifies
the -13L pin-out code; see ADR-0006 amendment 2026-07-28), MAX31856,
protection parts. cook-loadcell v1.0: reused unmodified (Board D).
crow-recorder archetype: band separation (keypad zone / analog spine /
digital+Pi band) guides the floorplan.

## Gates
Brief §14 G1-G10 adopted verbatim. G1/G2 (connector measurement + coupon)
BLOCK Board C; G4/G5 bench-only bring-up BLOCK any appliance connection;
G8 starts with harmless keys (TIMER) + OCR observation.

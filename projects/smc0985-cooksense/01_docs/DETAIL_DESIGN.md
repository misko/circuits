# DETAIL_DESIGN — cooksense v1.2 electrical corrections

Companion to ADR-0010/0011: the numbers behind the v1.2 netlist changes.
(First DETAIL_DESIGN in this project — v1.0/v1.1 carried design detail in
ADR bodies; the threshold math and timing bounds below are too long for
an ADR and are referenced by it.)

## 1. Camera over-temperature hard stop (ADR-0011 §1)

Sensing chain (per camera): 3V3_ANALOG → 10k (R_REF0/R_REF3, 1%) →
TH_CAM node → external NTC → GND. NTC = KNTC0603/10KF3950
(02_parts: R25 = 10kΩ ±1%, B25/85 = 3987K ±1% — B25/85 chosen because
the protected range is 25→75C+; the '3950' in the MPN is B25/50).

NTC resistance:  R(T) = R25 · exp[ B·(1/T − 1/298.15) ],  T in kelvin.

| T | R(T) | node V = 3.3·R/(10k+R) |
|---|---|---|
| 25C | 10.000k | 1.650V |
| 60C | 2.487k* | 0.657V |
| 65C | 2.204k* | 0.596V |
| 70C | 1.732k | 0.487V |
| 75C | 1.466k | 0.422V |
| 81C | 1.206k | 0.355V |

(*interpolated with the same B25/85; ±1C-class accuracy, calibrated at
bring-up per brief §3.)

Reference divider (3V3_ANALOG → R_TH1 → TCAM_THRESH → R_TH2 → GND),
solder-select field, 1206 pads like RKEY:

    V_TH = 3.3 · R_TH2/(R_TH1 + R_TH2),   R_TH1 = 68k fixed

| R_TH2 | V_TH | trip T (solve R(T) = 10k·V/(3.3−V)) |
|---|---|---|
| 8.2k | 0.355V | 81.0C |
| **10k (default)** | **0.4231V** | **74.9C** (brief hard limit 75C) |
| 12k | 0.495V | 69.4C |
| 15k | 0.596V | 63.0C |

Worked default: R_TH2=10k → V_TH = 3.3·10/78 = 0.4231V → R_NTC =
10k·0.4231/(3.3−0.4231) = 1.4707k → ln(0.14707)/3987 = −4.808e−4 →
1/T = 1/298.15 − 4.808e−4 = 2.8732e−3 → T = 348.0K = **74.9C**.

Tolerance stack (1% resistors, ±1% R25, ±1% B): worst-case trip shift
~±2.5C — inside the 70(stop)/75(hard) band. Ratiometric by construction:
both dividers reference 3V3_ANALOG, so rail drift cancels to first
order. Comparator LM393 IN− = TCAM_THRESH (0.42V) is inside its
common-mode range (to GND). Hysteresis: R_HYS 1M against the 10k source
impedance ≈ 33mV at the node ≈ ~2C — trip latches anyway (ADR-0011 §2).
Test point TP_TCTH added on TCAM_THRESH.
Failure modes: NTC SHORT → 0V → trips (safe). NTC OPEN → node 3.3V →
comparator sees "cold" (NOT safe at the comparator) — detected in
software as full-scale ADC (brief C14: required-channel invalid ⇒ no
auto-start); accepted for v1.2, unchanged from v1.0/v1.1.
Bring-up gate (ORDER_README): controlled-fixture validation at
60/65/70/75C, BOTH channels, before any appliance connection.

## 2. PRESS one-shot timing (ADR-0011 §6)

CD74HC221 section 1, tw = K·Rx·Cx; K = 0.7 @4.5V (SCHS166F p.1), Fig.6
shows K ≈ 0.70–0.75 over 3.3–5V. Rx = 510k (1%), Cx = 1uF X5R (±10%):

    typ:   0.70·510k·1.0u = 357ms … 0.75·510k·1.0u = 383ms
    max:   0.77·515k·1.1u = 436ms  < 500ms HARD (brief §4.6)
    min:   0.63·505k·0.9u = 286ms  > 100–200ms typical need

Non-retriggerable: further PRESS_REQ edges during tw are ignored (DS
p.1). Clear: 1R_N = OS_CLR_N = DOOR_OK · STOP_REQ_N — door-open or STOP
kills the pulse immediately. Caveat (DS truth-table note 1): OS_CLR_N
rising while 1B (PRESS_REQ) is held high re-fires ONE bounded pulse —
software must drop PRESS_REQ on any abort; bounded + one-hot regardless.

## 3. Key sequencing (updated truth table, ADR-0011 §5/§6)

| phase | KEY_LATCH_G | decoders | K_PRESS | K_STOP |
|---|---|---|---|---|
| idle | passes | disabled (G1 low) | open | open |
| address U/D | passes (PRESS_TIMED low) | enabled after latch | open | open |
| PRESS edge | **frozen** (PRESS_TIMED high) | enabled | closed ≤436ms | open |
| STOP_REQ high | frozen or not — irrelevant | **force-disabled** | **force-cleared** | **closed** |
| door open | passes | enabled | force-cleared | open |
| WD/TEMP/ESTOP/latch fault | passes | 595s tri-stated + RAW pulled low → disabled; coil rail dead | open (rail dead) | **still available** (5V_STOP) |

STOP sequence (Pi-side, hardware-enforced where bold): raise STOP_REQ →
**PRESS one-shot cleared, both decoders disabled** (U/D coils drop) →
wait ≥1ms relay release → **K_STOP closed** for a software-bounded
100–500ms → drop STOP_REQ → K_STOP opens. Holding STOP_REQ indefinitely
is safe (holds the OEM STOP key).

## 4. Deterministic pulls (ADR-0011 §7)

All 100k, 0402. Safe state with Pi + expander un-driven (boot/reset):

| net | dir | safe state held |
|---|---|---|
| HOST_AUTH | down | authorization false → AND-chain false |
| MCU_RELAY_ENABLE | down | AND-chain false + SR_OE_N high (595 Hi-Z) |
| KEY_RESET_N | down | SRCLR̄ asserted → registers cleared |
| RAIL_EN_A/B/RHA/RHE | down | sensor rails off |
| CONTACTOR_REQ | down | contactor LED off |
| STOP_REQ | down | STOP relay open, decoders/one-shot ungated |
| REARM_N | **up** | re-arm inactive — a floating REARM_N cannot clear the fault latch |

Pre-existing: R_COILENPD, R_DECUPD/R_DECDPD (moved to the RAW enable
nets in v1.2), R_ESTOPPD, R_MODEPD, R_DOORPU, R_OE (up, SR_OE_N),
R_EXPRST (up).

## 5. Shared sensor buses (ADR-0010)

Bus A (I2C2, GPIO4/5): MLX90640 A (0x33) + ambient SHT45 (0x44).
Bus B (I2C3, GPIO14/15): MLX90640 B (0x33) + exhaust SHT45 (0x44).
Board pullups 2.2k per bus from the CAMERA's switched rail only
(N3V3_SW_A / N3V3_SW_B); SHT pods carry module 10k pullups. Phantom
power: with exactly one of a bus's two rails off, the off device can be
back-powered ~mA-class through the bus pins — bus-stuck recovery must
cycle BOTH rails of that bus (EN_A+EN_RHA / EN_B+EN_RHE) together.
100kHz bring-up → 400kHz after EMI validation (brief §3.10 unchanged).

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

**⚠ CORRECTED 2026-07-30 (ADR-0028 pass): THIS SECTION OMITTED `R_CLMPA`/
`R_CLMPB` 22 kΩ, WHICH ARE ON THE BOARD AND POST-DATE THIS DOCUMENT.** MEASURED
from `source/cooksense.net`: `R_CLMPA.2` and `R_CLMPB.2` are on GND and their
pin 1 sits on the camera sense node, so the NTC is loaded by 22 kΩ in PARALLEL.
Every number below was originally computed on the bare NTC. The consequences,
each re-derived here: the 25 °C node is **1.3444 V, not 1.650 V** (22.7 % high
as published), and the default hard-stop trip is **72.80 °C, not 74.9 °C**. The
error is in the SAFE direction — the real trip is 2.1 °C COLDER, i.e. it fires
sooner — and `ORDER_README.md` already carries `72.8 (hw trip)`, so the board
and the order paperwork were right and this document was the only thing wrong.

NTC resistance:  R(T) = R25 · exp[ B·(1/T − 1/298.15) ],  T in kelvin.
Sense node loaded by R_CLMPA/B 22 kΩ to GND, so the divider's lower leg is
R_NTC ∥ 22 kΩ. MEASURED (re-derived 2026-07-30, `/usr/bin/python3`):

| T | R(T) | R(T) ∥ 22k | node V = 3.3·(R∥22k)/(10k+R∥22k) | (old, no clamp) |
|---|---|---|---|---|
| 25C | 10.000k | 6.875k | **1.3444V** | 1.650V |
| 60C | 2.454k | 2.208k | **0.5968V** | 0.650V |
| 65C | 2.056k | 1.880k | **0.5223V** | 0.596V |
| 70C | 1.731k | 1.605k | **0.4564V** | 0.487V |
| 75C | 1.465k | 1.374k | **0.3986V** | 0.422V |
| 81C | 1.207k | 1.144k | **0.3388V** | 0.355V |

(R(T) computed from the B25/85 = 3987 K form at every row — the old table's
60 °C and 65 °C entries were marked interpolated and were also ~1.3 % off the
closed form. ±1C-class accuracy, calibrated at bring-up per brief §3.)

Reference divider (3V3_ANALOG → R_TH1 → TCAM_THRESH → R_TH2 → GND),
solder-select field, 1206 pads like RKEY:

    V_TH = 3.3 · R_TH2/(R_TH1 + R_TH2),   R_TH1 = 68k fixed

| R_TH2 | V_TH | trip T **with the 22k clamp** | (old, no clamp) |
|---|---|---|---|
| 8.2k | 0.3551V | **79.26C** | 81.0C |
| **10k (default)** | **0.4231V** | **72.80C** (brief hard limit 75C) | 74.9C |
| 12k | 0.4950V | **66.99C** | 69.4C |
| 15k | 0.5964V | **60.03C** | 63.0C |

Worked default, MEASURED 2026-07-30: R_TH2=10k → V_TH = 3.3·10/78 = 0.4231V →
the divider's lower leg at trip is (R_NTC ∥ 22k) = 10k·0.4231/(3.3−0.4231) =
**1.4706k**, so R_NTC = 1/(1/1470.6 − 1/22000) = **1575.9 Ω** → ln(0.15759)/3987
= −4.6339e−4 → 1/T = 1/298.15 − 4.6339e−4 = 2.89063e−3 → T = 345.95K =
**72.80C**. The old line solved `R_NTC = 1.4707k` directly, which is the
PARALLEL combination, not the thermistor.

Tolerance stack (1% resistors, ±1% R25, ±1% B): worst-case trip shift
~±2.5C — still inside the 70(stop)/75(hard) band, and now centred 2.1C lower.
Ratiometric by construction: both dividers reference 3V3_ANALOG, so rail drift
cancels to first order — **but note the 22k clamp does NOT cancel**; it is a
fixed resistor against a temperature-dependent one, so it shifts the curve
rather than scaling it.
**Comparator: the BOM ships `LMV393IDR`, not the LM393 this document named.**
That matters and is not a typo-level correction: the LMV393's abs-max VCC is
5.5 V (not 36 V) and its input common-mode range differs, so any argument
written about "LM393 VICR" does not transfer. TCAM_THRESH at 0.42V is inside
the LMV393's common-mode range (to GND); `02_parts/LM393DR/` is retained as the
SUPERSEDED dossier (v1.3 moved to the LMV393) and must not be read as the
fitted part.
Hysteresis: R_HYS 1M against the source impedance **at the trip point**, which
is 10k ∥ 1.4706k = **1282 Ω**, not the 10k this document used. MEASURED: a
3.3 V comparator swing injects **4.23 mV ≈ 0.37 °C**, and an independent lens
re-derived 3.69 mV ≈ 0.32 °C. **The published "≈33mV ≈ ~2C" is ~8x too large**,
because a 10 kΩ source impedance is the COLD-end value and the hysteresis is
only ever evaluated at the trip. Consequence is benign — the trip latches
anyway (ADR-0011 §2) — but a latching design must not rest on a hysteresis
figure that is 8x its real value.
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
p.1). Clear: **`1R_N` = `OS_CLR_N` = `ESTOP_OK` · `STOP_REQ_N`** — E-STOP-chain
false or STOP kills the pulse immediately.
**⚠ CORRECTED 2026-07-30 (ADR-0028 pass): this line said `DOOR_OK · STOP_REQ_N`.**
MEASURED from `source/cooksense.net`: `U_OSCLR.1 = ESTOP_OK`,
`U_OSCLR.3 = STOP_REQ_N`, `U_OSCLR.4 = OS_CLR_N -> U_ONESHOT.3`. The DOOR
channel was REMOVED FROM THE NETLIST by ADR-0025 D1 — the strings `DOOR_OK` and
`R_DOORPU` occur **zero** times in the netlist — so the published clear term
named a signal that does not exist. Caveat (DS truth-table note 1): OS_CLR_N
rising while 1B (PRESS_REQ) is held high re-fires ONE bounded pulse —
software must drop PRESS_REQ on any abort; bounded + one-hot regardless.

## 3. Key sequencing (updated truth table, ADR-0011 §5/§6)

| phase | KEY_LATCH_G | decoders | K_PRESS | K_STOP |
|---|---|---|---|---|
| idle | passes | disabled (G1 low) | open | open |
| address U/D | passes (PRESS_TIMED low) | enabled after latch | open | open |
| PRESS edge | **frozen** (PRESS_TIMED high) | enabled | closed ≤436ms | open |
| STOP_REQ high | frozen or not — irrelevant | **force-disabled** | **force-cleared** | **closed** |
| ~~door open~~ | — | — | — | — |
| WD/TEMP/ESTOP/latch fault | passes | 595s tri-stated + RAW pulled low → disabled; coil rail dead | open (rail dead) | **still available** (5V_STOP) |

**⚠ THE `door open` ROW IS STRUCK 2026-07-30 (ADR-0028 pass), NOT REWRITTEN.**
ADR-0025 D1 removed the door channel from the netlist; MEASURED, `DOOR_OK` and
`R_DOORPU` occur **zero** times in `source/cooksense.net`. The E-STOP chain
(`ESTOP_OK`) carries the clear term this row used to describe — see §2.

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
nets in v1.2), R_ESTOPPD, R_MODEPD, R_OE (up, SR_OE_N),
R_EXPRST (up).
**⚠ `R_DOORPU` REMOVED FROM THIS LIST 2026-07-30 (ADR-0028 pass)** — ADR-0025 D1
deleted the door channel and MEASURED, the refdes occurs **zero** times in
`source/cooksense.net`. A pull-resistor table is a SAFE-STATE table; a
non-existent part listed in one is a claimed safe state nothing holds.

## 5. Shared sensor buses (ADR-0010)

Bus A (I2C2, GPIO4/5): MLX90640 A (0x33) + ambient SHT45 (0x44).
Bus B (I2C3, GPIO14/15): MLX90640 B (0x33) + exhaust SHT45 (0x44).
Board pullups 2.2k per bus from the CAMERA's switched rail only
(N3V3_SW_A / N3V3_SW_B); SHT pods carry module 10k pullups. Phantom
power: with exactly one of a bus's two rails off, the off device can be
back-powered ~mA-class through the bus pins — bus-stuck recovery must
cycle BOTH rails of that bus (EN_A+EN_RHA / EN_B+EN_RHE) together.
100kHz bring-up → 400kHz after EMI validation (brief §3.10 unchanged).

---
id: 0008
date: 2026-07-21
status: accepted
---
# 0008 — L1 upsized (YSPI1770Y-100M, 16 A) + PD-stage thermal statement

## Context
v1.0's L1 (Sunlord MWSA1707S-100MT, Irms_40C = 12 A) ran at 99–100 % of its
RMS rating at the 100 W / low-VIN corner: I_avg ≈ 11.9 A at Vin = 8.84 V
(UVLO floor), ripple ~2 App, next to four switching FETs (X5, red-team A
P1-3). Its own part.yaml admitted "runs at rating". Thermal-via provision
was also token (X23: ~2× 0.15 mm drill per FET ≈ 218 K/W).

## Options
- **Derating ADR capping continuous PD power** (e.g. 65 W at Vin < 10 V) —
  honest but shrinks the product spec to paper over a part choice.
- **Upsize L1** — a 16 A-rms 10 µH part exists in stock at +$1.8 and +0.8 mm
  body: dominates. CHOSEN (with the derating math kept below for the case
  the alternate part must ever be substituted back).

## Decision
**L1 = YJYCOIN YSPI1770Y-100M** (10 µH ±20 %, Irms_40C 16 A, Isat 18 A @30 %
drop, DCR 8.0 mΩ typ, 18.0×17.15×7.0, LCSC C20613209, stock 213; vendored
footprint usb_hub_3s:L_YJYCOIN_YSPI1770Y from the DS land pattern). Margin
at the worst corner: 11.9 A / 16 A = 74 % (vs 99 %). DCR loss drops
~1.4 → ~1.1 W. Caveat recorded in the part.yaml: the vendor's Isat basis is
30 % drop (≈16 A at a 20 % basis) — peak 13.2 A clears either basis, but
ripple is bench-verified at the corner (ORDER_README).

## Thermal statement (the numbers the layout must serve — with ADR-0007 FETs)
At 9 V in / 20 V / 5 A out (boost, D≈0.55, I_in ≈ 12 A):
- Q4 (input HS, statically on in boost): 12² × 8.5 mΩ ≈ **1.22 W** worst
- Q7 (boost switch): conduction 144 × 8.5 m × 0.55 ≈ 0.67 W + switching
  ~20 V × 12 A × 20 ns × 250 kHz ≈ 1.2 W → **~1.9 W** worst
- Q6 (boost rectifier): conduction ≈ 0.55 W + body-diode/deadtime
- L1 DCR ≈ 12² × 8 mΩ ≈ **1.15 W**; RS2 0.72 W on its 2512
Layout program (X23 fix, verified at stage-7 measurement): 0.3 mm-drill
thermal via arrays under every power paddle; HS paddles (VIN_S/VOUT_PDS)
get B.Cu spreaders; LS paddles are LX — F.Cu-only islands by X2/X20 policy,
so their heat path is the F.Cu island + L1 pad copper + source-pin vias to
In1. Expected worst FET rise 40–60 °C in still air — HOT but inside silicon
ratings; sustained-100 W-at-9 V is a bench-verified mode, not an assumed one.

## Board-temp sensing (considered, decided)
The IP6559's only thermal input is its internal 150 °C OTP (die, not FETs/L1
8–15 mm away). GPIO0/NTC could derate power with an NTC, but the R25 slot is
committed to the PDO-config strap (ADR-0004) and the vendor value table is
app-note-only — wiring an NTC blind risks misconfiguring the PDO set.
DECISION: no board-temp sensing in v1.1; ORDER_README requires the 30-minute
sustained-100 W thermal soak (IR camera or thermocouple on Q7/L1) before the
board is trusted at full power unattended. Revisit for v2 with vendor docs.

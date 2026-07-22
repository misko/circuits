# ADR-0003 — per-port sensing chain (shunt + monitor)

Status: accepted 2026-07-18

## Context

P3: per-port current statistics. Choices: high-side vs low-side; one
multi-channel monitor vs per-port monitor; monitor abs-max vs the
clamped 24 V bus; shunt value/power class. Live JLC stock 2026-07-18.

## Decisions

1. **High-side sensing** (commission recommendation adopted): the GND
   bus stays a solid quiet reference, and — decisive here — this board
   doesn't even carry load returns (ARCHITECTURE, D1), so low-side
   sensing is impossible: return current never crosses the board.

2. **Per-port INA238AIDGSR** (C2868250, 1870 stock, $2.36) over:
   - **INA3221 ×2** (C181255, $2.22): 26 V abs-max — DEAD at 28.8 V
     charge voltage, let alone the 53 V TVS clamp. Rejected on abs-max,
     exactly the check the commission ordered.
   - **INA226 ×6** (C49851, $0.82, 7197 stock): 36 V abs-max vs 53.3 V
     SMCJ33A clamp → dies on the first real load dump. Rejected;
     recorded as the cheaper alternate IF a future rev clamps lower
     (12 V-only variant could use SMBJ18A + INA226 and save ~$9/board).
   - INA228 (85 V, dearer, overkill resolution) — no stock advantage.
   INA238: −0.3…+85 V common-mode, ±40 V differential, 16-bit, I2C with
   16 strap addresses (6 used: 0x40–0x45), shared ALERT. 31 V of
   headroom above the TVS clamp.

3. **Shunt: Vishay WSLP2726 0.5 mΩ 1 %** (WSLP2726L5000FEA, C844297,
   2671 stock): 15 mV @ 30 A on the ±40.96 mV range (37 % FS,
   2.5 mA/LSB), 0.45 W dissipation on a 6 °C/W element (ΔT ≈ 2.7 °C),
   Power-Metal-Strip TCR (<20 ppm/°C) so readings hold over the thermal
   swing of a 30 A port. Rejected: generic 2512 3 W alloy shunts
   (C5375456, $0.06 — tempting, but 2512 terminals at a sustained 30 A
   plus unspecified TCR is where cheap boards drift; $6/board buys the
   part this product exists to be). 1 mΩ variant rejected: 0.9 W heat
   and nothing gained — 15 mV is already comfortably resolved.

4. **Filter + Kelvin** (DETAIL_DESIGN §3): 10 Ω + 100 nF differential
   per datasheet app-note topology; VBUS sensed port-side through
   matched 10 Ω (blown-fuse detection). Kelvin attachment at pad inner
   edges is a machine-checked layout invariant (audit I-KELVIN) with
   scoped KELVIN rule areas for the sub-floor tap widths (ADR-0002).

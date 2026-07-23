# journal: 02 parts

## 2026-07-22 — start
- did: entering parts stage from the committed commission (6272aa0). Driving
  the CookSense board (A+B merged, ADR-0001; firmware-less, ADR-0002).
- plan: (1) derive BOM, split ledger-hits (cook-hub v1.0 reuse) vs new; (2)
  fan out max-effort research on the new multi-pin parts -> part.yaml each
  (pinout from datasheet FIGURE + verified: + escape_check block + layout:
  block for every IC/power-sense per P-LAYOUT + LCSC + alternates); (3) merge,
  escape_check + policy_audit P-ESC/P-LAYOUT gate. E-TOPO N-A (all-linear).
- result: pending fan-out.
- next: BOM derivation + research fan-out (workflow, MAX effort).

## 2026-07-22 — BOM classified (cook-hub reuse is huge)
- did: copied 21 cook-hub v1.0 part.yaml (pinout+escape already verified). Core
  reuse: DIP05-1A72-12L relay, ULN2803ADWR driver, SN74HC595DR shift reg,
  MAX31856MUD+T TC, the SN74LVC1G123 one-shot (PRESS timer), SN74LVC1G11 3-in
  AND (AND-chain), protection (MF polyfuse, SMBJ5.0A TVS, SS34, PESD, 2N7002/
  AO3401A FETs, LTV-817S opto for the contactor, RVT220UF bulk, AMS1117 LDO,
  GZ2012D601 ferrite), B5B-XH loadcell + KF350 terminal.
- CORRECTION: X9555WV-2x16-6TV01 is a 2x16 BOX HEADER (not a GPIO expander) —
  the I2C expander (MCP23017) stays on the NEW list.
- NEW parts to research (~11): MCP23017 expander; SN74HC138 + SN74HC139
  decoders (one-hot U/D select, ADR-0002); TPS3823 watchdog supervisor; an
  eFuse w/ OV cutoff; MCP3208 8ch ADC; LM393 comparators (TEMP_OK); a K-type
  TC PCB connector; JST-GH 8/5/10-pin; Micro-Fit 2-pin power; 2x20 Pi stacking
  header; AQY212GS PhotoMOS (optional alt). Plus layout: backfill on the reused
  multi-pin parts (P-LAYOUT).
- next: fan-out research + layout-backfill (workflow, MAX effort).

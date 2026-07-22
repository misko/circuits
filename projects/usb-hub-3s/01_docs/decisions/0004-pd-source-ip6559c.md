---
id: 0004
date: 2026-07-21
status: accepted
---
# 0004 — PD source selection: IP6559-C (sourcing spike outcome for `pd-source-5v5a`)

## Context
D-SPEC sourcing spike for the spec-critical "5 A compliant USB-C" function.
The proven-parts ledger entry `pd-source-5v5a` is UNRESOLVED — no verified
part. Timeboxed JLC part-universe search run 2026-07-21 (JLC parts API,
stock measured live):

| Candidate | Package | JLC stock | Verdict |
|---|---|---|---|
| SW3518S (C406811) | QFN-28 0.4 mm | 0 | out of stock |
| SW3516H (C406808) | QFN-28 0.4 mm | 0 | out of stock |
| SW2303 / SW3526 / SW3536 / IP6557 / IP2366 / IP2723 / HUSB350 / WT6633 / FP6606 | various QFN | 0 | out of stock |
| IP6538-AC (C669696) | QFN-32 0.5 mm | 1133 | 60 W class — no 5 A object |
| IP6525T_N (C515678) | ESOP-8 | 7104 | 20 W — no 5 A |
| CYPD3175-24LQXQT (C2952419) | QFN-24 | 1264 | needs vendor firmware config tooling — integration risk |
| **IP6559-C (C5140592)** | **QFN-48 7x7 0.5 mm EP** | **62** | **CHOSEN** |

IP6559-C datasheet facts (Injoinic V1.4, cached in 02_parts): input 3.6–31 V;
4-switch buck-boost, external NFETs + one 10 µH inductor; single Type-C
100 W PD3.0/PPS source; CC-mode output limits 5V/9V/12V→3 A, 20 V→5 A with
E-MARK cable (electrical table p.6); integrated e-marker recognition; Vconn
switch circuit given in Fig. 9; complete reference schematic (Fig. 8/9), BOM
(p.17) and layout rules (p.18).

## Options
- **IP6559-C** — CHOSEN: only in-stock silicon that delivers a compliant 5 A
  contract; full public reference design; escape_check: qfn/0.5 →
  tier_required jlc_4layer_advanced (drives ADR 0005).
- **Two-stage (5 V buck + standalone 5 V/5 A fixed-PDO controller)** —
  REJECTED: no such stocked controller exists (table above); confirms the
  ledger's unresolved note.
- **CYPD3175** — REJECTED: config requires Cypress EZ-PD tooling/firmware
  images; unverifiable in this pipeline without hardware programmer.
- **Wait for SW3518S restock** — REJECTED: stock is 0 today; the gate is
  orderability now.

## Known tension: R7 (GPIO0) PDO-config resistor
The R7↔PDO table lives in Injoinic's "IP6559 应用说明文档" (application
description document), which is NOT publicly indexed (searched 2026-07-21:
Injoinic site, datasheet mirrors, OSHWLab, GitHub — table not found). The
IP6559_C VARIANT is defined by the datasheet as "Single C port 100W PD fast
charge output" (p.4), i.e. the 100 W PDO set is the variant's identity; R7
"can change" it (note 1, p.15). DECISION: R7 footprint populated as DNP
(chip runs its variant-default 100 W set); first-power ritual REQUIRES a PD
analyzer/trigger read of the advertised PDO list before field use, and the
ORDER_README carries this. Fallback if the default proves wrong: obtain the
app note from Injoinic FAE and fit R7 — a resistor change, not a respin.

## Decision
IP6559-C (LCSC/JLC C5140592), single-C 100 W configuration per
datasheet Fig. 9 (with e-marker Vconn circuit), output CC limit resistors at
datasheet-nominal 5 mΩ. Stock 62 ≥ 5× need at order time — re-check on order
day (thin stock is the accepted risk; alternates: none today, documented).

## Consequences
- fab_tier must rise to jlc_4layer_advanced (ADR 0005).
- Power stage: 4× 30–40 V NFETs + path NFET + 10 µH ≥15 A inductor (DETAIL_DESIGN).
- Ledger harvest at release: found `pd-source-5v5a` entry with this part.
- Stock=62 is thin: order-day re-check mandatory; if gone, the board waits
  (no compliant alternate in stock today).

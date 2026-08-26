# Q-2SOURCE audit — 2026-07-31

These are dated, volatile observations, not a promise of order-day allocation.
The gate requires the exact authoritative MPN, or an explicitly approved
dossier alternate, to be active and orderable with stock greater than 10 and
sufficient for five boards at two independent authorized supplier pools.

Inputs: current JLC catalog queries, a 52-call Mouser exact-plus-broad API run
over all 26 dossiers, and exact DigiKey product pages recorded in
`manual_quotes.yaml`. Search snippets, marketplace sellers, and multiple
listings from one distributor do not increase the supplier count.

## Verdict

**PASS — 26/26 selected dossier MPNs have at least two qualifying authorized
supplier pools.** Repeat this audit on order day because stock is volatile.

## Corrected selections

| Selected exact MPN | JLCPCB/LCSC | Mouser | DigiKey | Qualifying pools |
|---|---:|---:|---:|---|
| `WSL2512R0100FEA` | 13,216 | 2,081,537 | 110,973 | JLC, Mouser, DigiKey |
| `AP63203QWU-7` | 0 | 4,897 | 2,685 | Mouser, DigiKey; U4 consigned |
| `CL32A107MPVNNNE` | 78,342 | 176,983 | 84,716 | JLC, Mouser, DigiKey |
| `CL32B106KBJNNWE` | 533 | 110,682 | 130,022 | JLC, Mouser, DigiKey |
| `VLS6045EX-4R7M` | 8,756 | 26,939 | 56,358 | JLC, Mouser, DigiKey |
| `STM32G0B1CBT6` | 44 | availability unparseable | 2,677 | JLC, DigiKey |
| `1935161` | 1,127 | 24,051 | 27,170 | JLC, Mouser, DigiKey |

The remaining 19 selected dossier MPNs retain the two qualifying pools
established by the first audit. The replacement set preserves the required
electrical and mechanical specifications: 10 mOhm/1%/1 W/2512 shunts;
fixed-3.3 V/2 A/TSOT-23-6 buck; 100 uF/10 V/X5R/1210 and
10 uF/50 V/X7R/1210 capacitors; 4.7 uH/4.2 A/6 mm inductor; the exact
STM32G0B1CBT6; and a 2-position/5.00 mm/18 A side-entry terminal.

`shopping-list-2026-07-31.{md,json}` records the complete distributor evidence.
Its overall verdict is intentionally not Q-2SOURCE: that tool reports every
missing distributor row, while Q-2SOURCE requires any two qualifying pools.

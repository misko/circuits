# Architecture-backtrack sourcing evidence — 2026-08-01

This is pre-selection evidence, not an order-day allocation promise. Stock must
be refreshed before payment. The exact MPN is the identity; suffix variants and
parametric substitutes do not count.

## Candidate results

| exact MPN | role | Mouser API stock | DigiKey product-page stock | JLC/LCSC observation | result |
|---|---|---:|---:|---|---|
| `LTC3889IUKG#PBF` | dual 60 V high-current buck controller | 47 | 629 | no credited JLC line | Q-2SOURCE PASS: Mouser + DigiKey |
| `CSD18533Q5AT` | 60 V switching MOSFET | 124 | 950 | no credited JLC line | Q-2SOURCE PASS: Mouser + DigiKey |
| `TPS259830LNRGER` | low-loss current-limiter eFuse plus external blocking-FET drive | 3,555 | 4,531 | exact `C20607218`, stock 3,005 | Q-2SOURCE PASS: Mouser + DigiKey; JLC third pool |
| `TPS259470ARPWR` | selected 2 A true-reverse-blocking port eFuse | 9,831 | not needed for gate | exact `C3662799`, stock 1,736 | Q-2SOURCE PASS: Mouser + JLC |
| `AON6354` | 5 V ideal-diode external MOSFET | not catalogued | 3,602 | exact `C404363`, catalog stock 4,730 | Q-2SOURCE PASS: DigiKey + JLC |
| `LMR36510FADDAR` | 65 V auxiliary buck | 946 | 1,366 | exact proposal `C1858394`, catalog stock 2,304 | Q-2SOURCE PASS: Mouser + DigiKey; JLC third pool |
| `B82477G4333M000` | 33 uH auxiliary-buck inductor | not credited | 5,744 | exact `C2045462`, stock 219 | Q-2SOURCE PASS: DigiKey + JLC |
| `2N7002K-7` | fail-safe LTC3889 RUN pull-down | stocked | not credited | exact `C85047`, stocked | Q-2SOURCE PASS: Mouser + JLC |
| `MMBT3906LT1G` | LTC3889 remote temperature sensor | 9,804 | 974,247 | not credited | Q-2SOURCE PASS: Mouser + DigiKey |
| `CL32B106KBJNNWE` | 10 uF / 50 V VIN_PROTECTED bulk capacitor | 110,682 | 130,022 (2026-07-31 read) | exact `C3844168`, stock 533 | Q-2SOURCE PASS: Mouser + JLC; DigiKey third pool |
| `HMK107C7224KAHTE` | 220 nF / 100 V VIN_PROTECTED high-frequency bypass | 195,837 | not needed for gate | exact `C2169715`, stock 45,038 | Q-2SOURCE PASS: Mouser + JLC; manufacturer has renamed the MPN, so order-day review is mandatory |
| `CC1206KKX7R0BB104` | 100 nF / 100 V LM74810 VS and VIN_FUSED bypass | no credited stock | 83,505 | exact `C107181`, stock 225,916 | Q-2SOURCE PASS: DigiKey + JLC |
| `CL32A107MPVNNNE` | 100 uF / 10 V 5.215 V rail bulk capacitor | not needed for gate | 84,716 (2026-07-31 read) | exact `C23742`, stock 78,186 | Q-2SOURCE PASS: DigiKey + JLC; exact code pinned to prevent 6.3 V auto-selection |
| `TNPW0603100KBEEA` | 100 kOhm / 0.1% auxiliary feedback top leg | 112,181 | not needed for gate | exact `C844888`, stock 37,138 | Q-2SOURCE PASS: Mouser + JLC |
| `TNPW060320K0BEEA` | 20 kOhm / 0.1% auxiliary feedback bottom leg | 15,185 | not needed for gate | exact `C844676`, stock 20,548 | Q-2SOURCE PASS: Mouser + JLC |
| `CRCW060336K5FKEA` | 36.5 kOhm / 1% TPS259470 OVLO top leg | 139,858 | not needed for gate | exact `C844160`, stock 1,572 | Q-2SOURCE PASS: Mouser + JLC |
| `CL10B332KB8NNNC` | 3.3 nF / 50 V TPS259470 DVDT capacitor | 106,266 | not needed for gate | exact `C1613`, stock 471,021 | Q-2SOURCE PASS: Mouser + JLC |
| `TPSM64406RCHR` | module-first 36 V / 6 A buck candidate | 2,590 | 1,208 | not credited | Q-2SOURCE PASS but electrically rejected |
| `TPSM63606RDLR` | alternate 36 V / 6 A module candidate | 9,398 | 0 | not credited | Q-2SOURCE FAIL on 2026-08-01 |

Mouser values are machine-readable results from the repository shopping-list
tool with a no-cache API run. DigiKey values are exact product pages recorded
in `manual_quotes.yaml`; search snippets were not used. JLC observations came
from `jlc_stock_check.py --search-missing` against the exact candidate BOM.
The AON6354 JLC identity was refreshed separately after the initial candidate
batch: the endpoint returned exact model `AON6354` for `C404363`, not a
value/package proposal.

## Why the stocked TPSM64406 module is not selected

TI specifies `VFB = 788..812 mV` over temperature (±1.5%) for its adjustable
output and rates the module for stackable 6 A operation. At the locked
4.75–5.25 V mated-test-plug boundary, the complete path must also include the
eFuse, ideal-diode MOSFET, routed copper/joints, and both USB-A power contacts.
The module's reference spread consumes too much of that 500 mV window: setting
the high corner below 5.25 V leaves insufficient worst-low voltage after the
20% delivery-loss margin. Stock therefore does not make it electrically
eligible.

The selected LTC3889 is a bare-IC exception because its less-than-±0.5%
full-temperature output error and independent dual rails preserve the binding
connector-voltage margin. Its configuration pins leave the two outputs OFF at
factory default; the independently powered management MCU must program and
verify the locked command before enabling either rail.

## Superseded port-protection attempt

`TPS259823ONRGET` plus `LTC4372IMS8#PBF` was researched but rejected before
schematic adoption. The eFuse alone does not specify disabled output-to-input
isolation, while the LTC4372's guaranteed 45 mV activation threshold consumes
too much of the commissioned connector-voltage margin. TI's newer exact
`TPS259830LNRGER` was then attempted because it retains a 4.5 mOhm maximum
internal path and explicitly
drives an external common-source FET fully on in steady state and off whenever
the eFuse is disabled. The exact-hash topology review rejected that design:
the 300 Ohm setting bounded current at 4.36-5.66 A rather than the locked 2 A,
and the device's PG output had been mislabeled as FLT.

ADR-0007 replaces both attempts with TPS259470ARPWR. Its integrated
back-to-back MOSFETs provide true reverse blocking, its 1.47 kOhm RILM bounds
the limit at approximately 2.02-2.52 A, and its dedicated FLT output supplies
the required fault signal. The exact eFuse and the two newly selected support
passives above each passed the two-independent-supplier rule before adoption.

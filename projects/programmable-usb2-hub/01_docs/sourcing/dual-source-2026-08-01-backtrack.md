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
| `AON6354` | 5 V ideal-diode external MOSFET | not catalogued | 3,602 | exact `C404363`, catalog stock 4,730 | Q-2SOURCE PASS: DigiKey + JLC |
| `LMR36510FADDAR` | 65 V auxiliary buck | 946 | 1,366 | exact proposal `C1858394`, catalog stock 2,304 | Q-2SOURCE PASS: Mouser + DigiKey; JLC third pool |
| `B82477G4333M000` | 33 uH auxiliary-buck inductor | not credited | 5,744 | exact `C2045462`, stock 219 | Q-2SOURCE PASS: DigiKey + JLC |
| `2N7002K-7` | fail-safe LTC3889 RUN pull-down | stocked | not credited | exact `C85047`, stocked | Q-2SOURCE PASS: Mouser + JLC |
| `MMBT3906LT1G` | LTC3889 remote temperature sensor | 9,804 | 974,247 | not credited | Q-2SOURCE PASS: Mouser + DigiKey |
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

## Port-protection backtrack

`TPS259823ONRGET` plus `LTC4372IMS8#PBF` was researched but rejected before
schematic adoption. The eFuse alone does not specify disabled output-to-input
isolation, while the LTC4372's guaranteed 45 mV activation threshold consumes
too much of the commissioned connector-voltage margin. TI's newer exact
`TPS259830LNRGER` retains the 4.5 mOhm maximum internal path and explicitly
drives an external common-source FET fully on in steady state and off whenever
the eFuse is disabled. With `AON6354`, it therefore supplies both hardware
current limiting and specified disabled reverse blocking without the 45 mV
series threshold.

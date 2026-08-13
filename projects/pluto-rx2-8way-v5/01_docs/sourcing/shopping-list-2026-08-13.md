# Shopping list — pluto-rx2-8way-v5

Generated `2026-08-13 17:13 UTC` by `shopping_list.py` (scope `all`, 5 board set(s), stock floor `> 10`).

**Every number here is a dated OBSERVATION, not a fact.** Stock and price move; re-run before you pay. Each row carries its M-IMPORT grade: **CITED** = machine-readable API response or a product page read with its URL and date · **ESTIMATED** = volatile/unverifiable · **OWED** = nobody has this number yet.

## Coverage (Q-COVER)

- parts in `02_parts/`: **12**
- selected for this list (`all`): **12**
- **mouser**: graded **12/12**, sourceable **11/12**
- **digikey**: graded **2/12**, sourceable **2/12**
- **amazon**: graded **0/12**, sourceable **0/12**
- **jlc/lcsc snapshot**: graded **12/12**, sourceable **11/12**

## Composed authorized-pool gate (Q-2SOURCE)

Each exact manufacturer/MPN row must clear **2** of these independent authorized pools: jlc, mouser, digikey. Amazon is marketplace evidence and never counts. A JLC/LCSC catalog PASS is selection evidence, not proof that the assembly uploader will allocate stock.

| exact manufacturer / MPN | needed | qualifying pools | result |
|---|---:|---|---|
| Littelfuse / `0603L010YR` | 5 | jlc, mouser | **PASS 2/2** |
| Amphenol RF / `901-143-6RFX` | 45 | mouser, digikey | **PASS 2/2** |
| Samsung Electro-Mechanics / `CL05B104KO5NNNC` | 15 | jlc, mouser | **PASS 2/2** |
| Samsung Electro-Mechanics / `CL10A475KO8NNNC` | 15 | jlc, mouser | **PASS 2/2** |
| pSemi / `PE42482A-X` | 5 | jlc, mouser | **PASS 2/2** |
| Yageo / `RC0402FR-0710KL` | 20 | jlc, mouser | **PASS 2/2** |
| Yageo / `RC0402FR-075K1L` | 10 | jlc, mouser | **PASS 2/2** |
| Littelfuse / `SMBJ6.0A` | 5 | jlc, mouser | **PASS 2/2** |
| STMicroelectronics / `STM32C011F4P6` | 5 | jlc, mouser | **PASS 2/2** |
| Texas Instruments / `TPD2E2U06DRLR` | 5 | jlc, mouser | **PASS 2/2** |
| Texas Instruments / `TPS7A2433DBVR` | 5 | jlc, digikey | **PASS 2/2** |
| GCT / `USB4105-GF-A-120` | 5 | jlc, mouser | **PASS 2/2** |

**COMPOSED-POOLS PASS:** 12/12 exact rows meet the 2-pool requirement.

## Is there one distributor that has everything?

**No.** No single distributor covers all 12 selected lines at stock > 10. Best coverage: mouser 11/12, digikey 2/12, amazon 0/12.

## Mouser

*Method: Mouser Search API (search/partnumber). TWO searches per part: `Exact` on the authoritative MPN, then `None` on the suffix-stripped MPN — one part has several catalog records and they disagree. CITED.*

| MPN | qty | dist. part no. | stock | factory / lead | min/mult | lifecycle | unit @ break | extended | grade | status | link |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| `0603L010YR` | 5 | 576-0603L010YR | 4702 | 0 / 91 Days | 1/1 | — | $1.3400 @ 5 | $6.70 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/Littelfuse/0603L010YR?qs=n5MbhIql%252BRkr%252BdaX3F6IAA%3D%3D) |
| `901-143-6RFX` | 45 | 523-901-143-6RFX | 1220 | 0 / 98 Days | 1/1 | — | $8.1200 @ 25 | $365.40 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/Amphenol-RF/901-143-6RFX?qs=Kdyc7Q8pFhpGGXyYYV%2FtdA%3D%3D) |
| `CL05B104KO5NNNC` | 15 | 187-CL05B104KO5NNNC | 3518801 | 0 / 210 Days | 1/1 | — | $0.0240 @ 10 | $0.36 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/Samsung-Electro-Mechanics/CL05B104KO5NNNC?qs=hqM3L16%252BxlfT2SKOuAUq6Q%3D%3D) |
| `CL10A475KO8NNNC` | 15 | 187-CL10A475KO8NNNC | 182301 | 0 / 210 Days | 1/1 | — | $0.0840 @ 10 | $1.26 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/Samsung-Electro-Mechanics/CL10A475KO8NNNC?qs=X6jEic%2FHinAbIjmLnFfqqQ%3D%3D) |
| `PE42482A-X` | 5 | 81-PE42482A-X | 8554 | 0 / 112 Days | 1/1 | — | $5.9700 @ 1 | $29.85 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/pSemi/PE42482A-X?qs=5aG0NVq1C4xJoz2XWx4XXA%3D%3D) |
| `RC0402FR-0710KL` | 20 | 603-RC0402FR-0710KL | 19737190 | 0 / 56 Days | 1/1 | — | $0.0090 @ 10 | $0.18 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/YAGEO/RC0402FR-0710KL?qs=I1mnnYJTTsxUoNwrUsQExA%3D%3D) |
| `RC0402FR-075K1L` | 10 | 603-RC0402FR-075K1L | 24 | 0 / 56 Days | 1/1 | — | $0.0090 @ 10 | $0.09 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/YAGEO/RC0402FR-075K1L?qs=YUgVZYePFqCSmQuaha43RA%3D%3D) |
| `SMBJ6.0A` | 5 | 576-SMBJ6.0A | 8384 | 0 / 210 Days | 1/1 | — | $0.4700 @ 1 | $2.35 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/Littelfuse/SMBJ6.0A?qs=HR2RnyOI4E4ONaBgNaR6Ig%3D%3D) |
| `STM32C011F4P6` | 5 | 511-STM32C011F4P6 | 12996 | 0 / 364 Days | 1/1 | — | $1.1800 @ 1 | $5.90 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/STMicroelectronics/STM32C011F4P6?qs=IPgv5n7u5Qbo1GzhbgPEPw%3D%3D) |
| `TPD2E2U06DRLR` | 5 | 595-TPD2E2U06DRLR | 73918 | 0 / 112 Days | 1/1 | — | $0.9700 @ 1 | $4.85 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TPD2E2U06DRLR?qs=1MXlzafEN39QPVHZrdAIIQ%3D%3D) |
| `TPS7A2433DBVR` | 5 | — | — | — | —/— | — | — | — | CITED | SUBSTITUTE-ONLY | — |
| `USB4105-GF-A-120` | 5 | 640-USB4105-GF-A-120 | 95421 | 0 / 49 Days | 1/1 | — | $0.9300 @ 1 | $4.65 | CITED | OK | [page](https://www.mouser.com/en/ProductDetail/GCT/USB4105-GF-A-120?qs=QNEnbhJQKva%252Bjxw%2FpEjDhQ%3D%3D) |

**mouser total: INCOMPLETE — $421.59 covers only 11 of 12 lines.** A total over a partial list is not a total. Only SOURCEABLE lines are summed: pricing a line you cannot order at the quantity you need (0 stock, or an MOQ above the need) gives a number that is arithmetically right and operationally false. The missing lines are named below.

## Digikey

*Method: PRODUCT PAGE read by a human and recorded in 01_docs/sourcing/manual_quotes.yaml. No API key available (OAuth client credentials not provided). CITED from a product page; a search snippet is REFUSED.*

| MPN | qty | dist. part no. | stock | factory / lead | min/mult | lifecycle | unit @ break | extended | grade | status | link |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| `0603L010YR` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `901-143-6RFX` | 45 | ARFX1232-ND | 4206 | — | —/— | Active | $8.1216 @ 25 | $365.47 | CITED | OK | [page](https://www.digikey.com/en/products/detail/amphenol-rf/901-143-6RFX/272190) |
| `CL05B104KO5NNNC` | 15 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `CL10A475KO8NNNC` | 15 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `PE42482A-X` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `RC0402FR-0710KL` | 20 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `RC0402FR-075K1L` | 10 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `SMBJ6.0A` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `STM32C011F4P6` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `TPD2E2U06DRLR` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `TPS7A2433DBVR` | 5 | 296-TPS7A2433DBVRCT-ND | 23268 | — | —/— | Active | $0.6700 @ 1 | $3.35 | CITED | OK | [page](https://www.digikey.com/en/products/detail/texas-instruments/TPS7A2433DBVR/11502221) |
| `USB4105-GF-A-120` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |

**digikey total: INCOMPLETE — $368.82 covers only 2 of 12 lines.** A total over a partial list is not a total. Only SOURCEABLE lines are summed: pricing a line you cannot order at the quantity you need (0 stock, or an MOQ above the need) gives a number that is arithmetically right and operationally false. The missing lines are named below.

## Amazon

*Method: Direct product links only, hand-recorded. No usable API (PA-API needs an affiliate account). ESTIMATED, always — stock and price are volatile and unverifiable.*

| MPN | qty | dist. part no. | stock | factory / lead | min/mult | lifecycle | unit @ break | extended | grade | status | link |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| `0603L010YR` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `901-143-6RFX` | 45 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `CL05B104KO5NNNC` | 15 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `CL10A475KO8NNNC` | 15 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `PE42482A-X` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `RC0402FR-0710KL` | 20 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `RC0402FR-075K1L` | 10 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `SMBJ6.0A` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `STM32C011F4P6` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `TPD2E2U06DRLR` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `TPS7A2433DBVR` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |
| `USB4105-GF-A-120` | 5 | — | — | — | —/— | — | — | — | OWED | NO-QUOTE | — |

**amazon total: INCOMPLETE — $0.00 covers only 0 of 12 lines.** A total over a partial list is not a total. Only SOURCEABLE lines are summed: pricing a line you cannot order at the quantity you need (0 stock, or an MOQ above the need) gives a number that is arithmetically right and operationally false. The missing lines are named below.

## Every Mouser catalog record seen, per part

One physical part has SEVERAL catalog records and they disagree — that is the expected case, not an anomaly, so every record is printed with its own numbers and the one this list picked is marked. A record whose manufacturer part number is not the authoritative MPN (modulo packaging/plating suffixes) is a **substitute proposal for a human**, never a sourced line (Q-IDENT).

| MPN asked | search | mfr part no. | Mouser no. | stock | lifecycle | factory / lead | same part? | used |
|---|---|---|---|---:|---|---|---|---|
| `0603L010YR` | exact | `0603L010YR` | 576-0603L010YR | 4702 | — | 0 / 91 Days | yes | **chosen** |
| `901-143-6RFX` | exact | `901-143-6RFX` | 523-901-143-6RFX | 1220 | — | 0 / 98 Days | yes | **chosen** |
| `CL05B104KO5NNNC` | exact | `CL05B104KO5NNNC` | 187-CL05B104KO5NNNC | 3518801 | — | 0 / 210 Days | yes | **chosen** |
| `CL10A475KO8NNNC` | exact | `CL10A475KO8NNNC` | 187-CL10A475KO8NNNC | 182301 | — | 0 / 210 Days | yes | **chosen** |
| `PE42482A-X` | exact | `PE42482A-X` | 81-PE42482A-X | 8554 | — | 0 / 112 Days | yes | **chosen** |
| `RC0402FR-0710KL` | exact | `RC0402FR-0710KL` | 603-RC0402FR-0710KL | 19737190 | — | 0 / 56 Days | yes | **chosen** |
| `RC0402FR-075K1L` | exact | `RC0402FR-075K1L` | 603-RC0402FR-075K1L | 24 | — | 0 / 56 Days | yes | **chosen** |
| `RC0402FR-075K1L` | broad | `RC0402FR-135K1L` | 603-RC0402FR-135K1L | 63602 | — | 0 / 56 Days | NO — different part |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 78-SMBJ6.0A | 849 | — | 0 / 47 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 504-SMBJE6X0A | 116171 | — | 0 / 128 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 652-SMBJ6.0A | 2044 | — | 0 / 140 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 821-SMBJ6.0A | 0 | — | 0 / 161 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 947-SMBJ6.0A | 2954 | New Product | 0 / 0 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 576-SMBJ6.0A | 8384 | — | 0 / 210 Days | yes | **chosen** |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | N/A | **unparseable** | — | None / 0 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A` | 558-SMBJ6.0A | **unparseable** | Obsolete | None / 0 Days | yes |  |
| `SMBJ6.0A` | exact | `SMBJ6.0A-TP` | 833-SMBJ6.0A-TP | **unparseable** | — | None / 126 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A/TR13` | 603-SMBJ6.0A/TR13 | 33 | — | 0 / 114 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A/TR7` | 603-SMBJ6.0A/TR7 | 360 | — | 0 / 114 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-W` | 583-SMBJ6.0A-W | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `824520600` | 710-824520600 | 390 | — | 0 / 154 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-E3/5B` | 625-SMBJ6.0A-E3/5B | 1701 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-HR` | 576-SMBJ6.0A-HR | 0 | — | 0 / 147 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `P6SMBJ6.0A_R3_00001` | 241-P6SMBJ60AR300001 | 0 | — | 0 / 182 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-HF` | 750-SMBJ6.0A-HF | 0 | — | 0 / 112 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-M3/5B` | 78-SMBJ6.0A-M35B | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AHE3_A/H` | 78-SMBJ6.0AHE3_A/H | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `P6SMBJ6.0A-AU_R1_000A1` | 241-P6SMBJ60AAUR100 | 0 | Not Recommended for New Designs | 0 / 182 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-H` | 652-SMBJ6.0A-H | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `MSMBJ6.0A` | 494-MSMBJ6.0A | 0 | — | 0 / 245 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `MSMBJ6.0Ae3` | 494-MSMBJ6.0AE3 | 0 | — | 0 / 259 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-M3/52` | 78-SMBJ6.0A-M352 | 9326 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `P6SMBJ6.0A` | 637-P6SMBJ6.0A | 0 | — | 0 / 70 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-AT/TR13` | 603-SMBJ6.0A-AT/TR13 | 0 | — | 0 / 165 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-T7` | 576-SMBJ6.0A-T7 | 0 | — | 0 / 210 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `MXSMBJ6.0A/TR` | 494-MXSMBJ6.0A/TR | 0 | — | 0 / 259 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-Q` | 652-SMBJ6.0A-Q | 4824 | — | 0 / 140 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-QH` | 652-SMBJ6.0A-QH | 5685 | — | 0 / 140 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-AT/TR7` | 603-SMBJ6.0A-AT/TR7 | 0 | — | 0 / 165 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-E3/52` | 625-SMBJ6.0A-E3 | 3048 | — | 0 / 51 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AH` | 821-SMBJ6.0AH | 0 | — | 0 / 161 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `ASMBJ6.0A-HF` | 750-ASMBJ6.0A-HF | 0 | — | 0 / 112 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AHE3_B/H` | 78-SMBJ6.0AHE3BH | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AE3/TR13` | 494-SMBJ6.0AE3/TR13 | 1010 | — | 0 / 168 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AQ-13-F` | 621-SMBJ6.0AQ-13-F | 0 | — | 0 / 224 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `MASMBJ6.0Ae3` | 494-MASMBJ6.0AE3 | 0 | — | 0 / 294 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `MSMBJ6.0A/TR` | 494-MSMBJ6.0A/TR | 0 | — | 0 / 245 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `P6SMBJ6.0AJ` | 771-P6SMBJ6.0AJ | 0 | — | 0 / 196 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-E` | 576-SMBJ6.0AE | 0 | New Product | 0 / 154 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0A-HRA` | 576-SMBJ6.0A-HRA | 0 | — | 0 / 147 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `P6SMBJ6.0A_R1_00001` | 241-P6SMBJ60AR10000 | 0 | — | 0 / 84 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `P6SMBJ6.0A_R2_00001` | 241-P6SMBJ60AR20000 | 0 | — | 0 / 182 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AHM3_B/H` | 78-SMBJ6.0AHM3BH | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AHM3_B/I` | 78-SMBJ6.0AHM3BI | 0 | — | 0 / 0 Days | NO — different part |  |
| `SMBJ6.0A` | broad | `SMBJ6.0AJ` | 771-SMBJ6.0AJ | 0 | — | 0 / 196 Days | NO — different part |  |
| `STM32C011F4P6` | exact | `STM32C011F4P6` | 511-STM32C011F4P6 | 12996 | — | 0 / 364 Days | yes | **chosen** |
| `STM32C011F4P6` | broad | `STM32C011F4P6TR` | 511-STM32C011F4P6TR | **unparseable** | — | 0 / 364 Days | NO — different part |  |
| `STM32C011F4P6` | broad | `STM32C011F4U6TR` | 511-STM32C011F4U6TR | **unparseable** | — | 0 / 364 Days | NO — different part |  |
| `TPD2E2U06DRLR` | exact | `TPD2E2U06DRLR` | 595-TPD2E2U06DRLR | 73918 | — | 0 / 112 Days | yes | **chosen** |
| `TPD2E2U06DRLR` | broad | `TPD2E2U06DRLRG4` | 595-TPD2E2U06DRLRG4 | 0 | New Product | 0 / 112 Days | NO — different part |  |
| `TPS7A2433DBVR` | exact | `TPS7A2433DBVR` | 595-TPS7A2433DBVR | **unparseable** | — | 0 / 112 Days | yes |  |
| `TPS7A2433DBVR` | broad | `TPS78833DBVT` | 595-TPS78833DBVT | 16495 | — | 0 / 112 Days | NO — different part |  |
| `TPS7A2433DBVR` | broad | `TPS71433DRVR` | 595-TPS71433DRVR | 11865 | — | 0 / 112 Days | NO — different part |  |
| `USB4105-GF-A-120` | exact | `USB4105-GF-A-120` | 640-USB4105-GF-A-120 | 95421 | — | 0 / 49 Days | yes | **chosen** |
| `USB4105-GF-A-120` | broad | `USB4105-15-A-120` | 640-USB410515A120 | 0 | — | 0 / 35 Days | NO — different part |  |

**Supply cautions (a stock number alone is not a plan):**

- `0603L010YR` — distributor stock 4702 is the whole near-term supply: FactoryStock 0, lead 91 Days — a re-order is not quick
- `901-143-6RFX` — distributor stock 1220 is the whole near-term supply: FactoryStock 0, lead 98 Days — a re-order is not quick
- `CL05B104KO5NNNC` — distributor stock 3518801 is the whole near-term supply: FactoryStock 0, lead 210 Days — a re-order is not quick
- `CL10A475KO8NNNC` — distributor stock 182301 is the whole near-term supply: FactoryStock 0, lead 210 Days — a re-order is not quick
- `PE42482A-X` — distributor stock 8554 is the whole near-term supply: FactoryStock 0, lead 112 Days — a re-order is not quick
- `RC0402FR-0710KL` — distributor stock 19737190 is the whole near-term supply: FactoryStock 0, lead 56 Days — a re-order is not quick
- `RC0402FR-075K1L` — distributor stock 24 is the whole near-term supply: FactoryStock 0, lead 56 Days — a re-order is not quick
- `SMBJ6.0A` — distributor stock 8384 is the whole near-term supply: FactoryStock 0, lead 210 Days — a re-order is not quick
- `STM32C011F4P6` — distributor stock 12996 is the whole near-term supply: FactoryStock 0, lead 364 Days — a re-order is not quick
- `TPD2E2U06DRLR` — distributor stock 73918 is the whole near-term supply: FactoryStock 0, lead 112 Days — a re-order is not quick
- `USB4105-GF-A-120` — distributor stock 95421 is the whole near-term supply: FactoryStock 0, lead 49 Days — a re-order is not quick

## Distributor gaps — every unavailable line and why

| MPN | qty | distributor | status | why |
|---|---:|---|---|---|
| `0603L010YR` | 5 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `0603L010YR` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `901-143-6RFX` | 45 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `CL05B104KO5NNNC` | 15 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `CL05B104KO5NNNC` | 15 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `CL10A475KO8NNNC` | 15 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `CL10A475KO8NNNC` | 15 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `PE42482A-X` | 5 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `PE42482A-X` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `RC0402FR-0710KL` | 20 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `RC0402FR-0710KL` | 20 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `RC0402FR-075K1L` | 10 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `RC0402FR-075K1L` | 10 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `SMBJ6.0A` | 5 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `SMBJ6.0A` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `STM32C011F4P6` | 5 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `STM32C011F4P6` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `TPD2E2U06DRLR` | 5 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `TPD2E2U06DRLR` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `TPS7A2433DBVR` | 5 | mouser | **SUBSTITUTE-ONLY** | Q-IDENT: nothing in stock under the authoritative MPN. In stock under NEIGHBOURING part numbers: TPS78833DBVT (16495 in stock), TPS71433DRVR (11865 in stock). A near MPN is a PROPOSAL for a human, never a sourced line — this tool will not substitute |
| `TPS7A2433DBVR` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |
| `USB4105-GF-A-120` | 5 | digikey | **NO-QUOTE** | no digikey quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; the DigiKey API would replace this — see the enablement steps at the end of the report |
| `USB4105-GF-A-120` | 5 | amazon | **NO-QUOTE** | no amazon quote recorded. Open the PRODUCT PAGE (never a search snippet) and add an entry to 01_docs/sourcing/manual_quotes.yaml with its url and read_on date; Amazon has no usable API (PA-API needs an affiliate account) so this stays ESTIMATED even once recorded |

## What each line is, and why it is on this list

| MPN | mfr | qty | refs | why self-supplied |
|---|---|---:|---|---|
| `0603L010YR` | Littelfuse | 5 | candidate: F1 | — |
| `901-143-6RFX` | Amphenol RF | 45 | candidate: J2, J3, J4, J5, J6, J7, J8, J9, J10 | — |
| `CL05B104KO5NNNC` | Samsung Electro-Mechanics | 15 | candidate: C4, C5, C6 | — |
| `CL10A475KO8NNNC` | Samsung Electro-Mechanics | 15 | candidate: C1, C2, C3 | — |
| `PE42482A-X` | pSemi | 5 | candidate: U1 | — |
| `RC0402FR-0710KL` | Yageo | 20 | candidate: R3, R4, R5, R6 | — |
| `RC0402FR-075K1L` | Yageo | 10 | candidate: R1, R2 | — |
| `SMBJ6.0A` | Littelfuse | 5 | candidate: D1 | — |
| `STM32C011F4P6` | STMicroelectronics | 5 | candidate: U2 | — |
| `TPD2E2U06DRLR` | Texas Instruments | 5 | candidate: U4 | — |
| `TPS7A2433DBVR` | Texas Instruments | 5 | candidate: U3 | — |
| `USB4105-GF-A-120` | GCT | 5 | candidate: J1 | — |

## DigiKey: what would make these rows CITED

```
DigiKey HAS an API and this tool does not use it, because it needs OAuth 2.0
client credentials nobody has provided and an agent cannot create an account or
obtain a key. To promote every DigiKey row from ESTIMATED/OWED to CITED:

  1. Sign in at https://developer.digikey.com/ with a DigiKey account.
  2. Create an Organization, then a PRODUCTION app (Sandbox returns
     structurally-correct but incomplete data — do not source from it).
  3. Subscribe the app to **Product Information V4**.
  4. Copy the app's **Client ID** and **Client Secret**.
  5. Append them to `<repo>/.secrets/digikey.env` (mode 600; `.secrets/` is
     already gitignored):
         DIGIKEY_CLIENT_ID=...
         DIGIKEY_CLIENT_SECRET=...
  6. Tell me, and the 2-legged flow (POST client_id + client_secret +
     grant_type=client_credentials to https://api.digikey.com/v1/oauth2/token,
     then GET /products/v4/search/{mpn}/productdetails) becomes a peer of the
     Mouser path.

Until then DigiKey numbers come only from a PRODUCT PAGE a human opened,
recorded in `01_docs/sourcing/manual_quotes.yaml` with its URL and read date.
NEVER from a search-results snippet — that is the GHR-10V-S defect.
```

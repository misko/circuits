# Stage 2 exact-part selection — 2026-08-15 UTC

This is a dated selection record, not an order promise. Exact identity remains
authoritative in `02_parts/*/part.yaml` and `exact-parts.csv`; volatile catalog
facts are machine-composed in `shopping-list-2026-08-15.{md,json}` and must be
refreshed on order day.

## Selected architecture

| function | exact selected part | count/board | selection reason |
|---|---|---:|---|
| USB 3 redriver | TUSB522PIRGER | 4 | two-channel 5Gbps redriver with independent direction straps and TI application guidance for connector-side protection/coupling |
| USB 2 disconnect | TS3USB221ERSER | 4 | high-bandwidth two-channel USB switch whose active-high OE gives a real high-impedance disconnect state |
| VBUS current-limited switch | TPS2557DRBR | 4 | active-high enable, programmable 0.9A class limit, reverse-current blocking while disabled, discharge and 35mohm hot-path bound |
| data/power hardware interlock | SN74LVC1G08DCKR + 2N7002-7-F | 4 each | `DATA_OK = PWR_EN AND DATA_EN`; data cannot connect while VBUS is commanded off, independent of Pi software sequencing |
| six-line connector ESD | TPD6E05U06RVZR | 8 | one low-capacitance six-channel array at each upstream/downstream connector boundary |
| downstream USB 3 Type-A | Wurth 692121030100 | 4 | active, 9-contact right-angle through-hole receptacle, 1.8A VBUS rating, exact manufacturer drawing |
| upstream USB 3 Type-B | Wurth 692221030100 | 4 | active, cable-retained 9-contact right-angle through-hole receptacle; avoids pretending the fixture is a Pi HAT data path |
| input reverse-polarity FET | Diodes DMP3007SPS-13 | 1 | active PowerDI5060-8 P-FET, 30V and 16mohm max at -4.5V; replaces lifecycle-conflicted AON6403 before capture |
| local 3.3V regulator | TLV76133DCYR | 1 | fixed 3.3V, 1A SOT-223-4 LDO; avoids a switcher beside four 5Gbps paths, subject to a binding 0.904W worst-mode thermal check |
| power input / protection | Phoenix 1935161 + Keystone 3568 + Littelfuse 029707.5WXNV | 1 each | accessible two-pin terminal, replaceable MINI blade holder and exact user-fit 7.5A fuse |
| Pi GPIO connector | Wurth 61304021121 | 1 | exact full-size Pi 4/5 compatible 2x20 vertical header; Pi 5V and 3V3 pins are intentionally not connected |
| SuperSpeed series damping | YAGEO RC0402FR-072R2L | 32 | exact stocked 2.2ohm 1% part; replaces the zero-stock 5% selection while preserving TI's first-article tuning option |
| remaining resistors/capacitors | exact YAGEO, Samsung, Murata and Panasonic rows in `exact-parts.csv` | 111 fitted | exact value/tolerance/package identities with local datasheets; no generic value-only BOM rows |

## Selection changes caused by the gate

- TLV1117LV33DCYR was rejected after persistent JLC lookup failure and null
  authorized-distributor availability. TLV76133DCYR retained the intended
  package/pinout class and ceramic-capacitor compatibility.
- RC0402JR-072R2L was active but showed zero DigiKey stock. The selected
  RC0402FR-072R2L is the exact stocked 1% upgrade at JLC and Mouser.
- AON6403 was available but carried conflicting lifecycle classifications,
  including `Not For New Designs`. Active DMP3007SPS-13 was selected before
  symbol, footprint, placement or routing work. Its higher resistance is
  explicitly carried into the 400mohm per-port hot VBUS budget.
- Generic header, terminal and 2N7002 placeholders were replaced by exact
  Wurth 61304021121, Phoenix 1935161 and Diodes 2N7002-7-F identities.

## Primary design sources

- [TI TUSB522P product and datasheet](https://www.ti.com/product/TUSB522P)
- [TI TS3USB221E product and datasheet](https://www.ti.com/product/TS3USB221E)
- [TI TPS2557 product and datasheet](https://www.ti.com/product/TPS2557)
- [TI TPD6E05U06 product and datasheet](https://www.ti.com/product/TPD6E05U06)
- [Diodes DMP3007SPS product record](https://www.diodes.com/part/view/DMP3007SPS)
- [Wurth 692121030100 Type-A product record](https://www.we-online.com/components/products/datasheet/692121030100.pdf)
- [Wurth 692221030100 Type-B product record](https://www.we-online.com/components/products/datasheet/692221030100.pdf)
- [Raspberry Pi GPIO documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio)

Manufacturer datasheets and product records control immutable identity, pin,
rating and layout facts. Tutorials and videos are useful technique checks but
do not supersede those primary sources or the JLC order uploader.

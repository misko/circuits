# Parts evidence

Every exact hard-cell MPN has a local `part.yaml`; vendor PDFs are stored when
the part is layout, safety, timing, or mating critical. Previously captured
dossiers were reused only for unchanged exact MPNs and rechecked against the
v4 architecture.

| Function | Exact part | LCSC | Stock 2026-07-31 | Choice |
|---|---|---:|---:|---|
| MCU module | Waveshare RP2040-Zero | C9900173620 footprint identity; user supplied | retail | integrated LDO/USB/flash/clock, ordered GP0–GP3 |
| RF switch | PE42482A-X | C5121458 | 1,284 | absorptive DC–6 GHz SP8T |
| SMA jack | KH-SMA-KE-Z | C504007 | 22,674 | short vertical DC–6 GHz jack |

The module is intentionally not a JLC-sourced CPL line. Its catalog code is a
stock-zero footprint/consignment identity; `assembly.yaml` excludes it from
placement and records user fitting. RP2040, flash, oscillator and LDO are not
separate carrier BOM items.

Commodity passives are pinned in the TSX source and checked again when the BOM
is generated. A zero-stock or incompatible alternate is never silently used.

# SUPERSEDED — v1.10-2026-07-27

**Superseded by `07_releases/v1.11-2026-07-27/` on 2026-07-27.**

**Reason: a single OUT-OF-STOCK PASSIVE substituted for an electrically
identical part. NO COPPER CHANGE.**

Read this before assuming the board was wrong: **it was not.** v1.10's
`.kicad_pcb` is md5-identical (`83af8e5a5596a51cf139dd06e8903d47`) to v1.11's and
to `04_kicad/`'s; v1.11's gerbers and drills re-plot from that same board **15/15
byte-identical** after stripping only the plot's own timestamps, the copper pour
included (36 zones / 106 filled outlines); `fab/cpl.csv` is byte-identical
(`cmp`, 0 differences, 119 rows). 20 of 22 payload files are sha256-identical.
The two that differ are `fab/bom.csv` — **two cells, both on the `R28,R29` row**
— and `source/usb_hub_3s_v2.tsx`, which differs because canon M3 requires the
BOM row to have moved *because the source moved*.

Every gate, review verdict, bench threshold and measurement v1.10 carries stands
unaltered in v1.11. v1.10 is **not** DO-NOT-ORDER; ordering its bare PCB gives
the same board. What it is, is **unorderable as a PCBA**, which is a different
thing.

## Why v1.11 exists

This release's `fab/bom.csv` was uploaded to JLCPCB and line 8 came back
**"10 shortfall"**: `C25744`, the 10 kΩ 0402 on **R28/R29** (the USB-C CC1/CC2
Rp pull-ups). JLC's own parts API, re-queried 2026-07-27, reports
**`stockCount: 0`** for that code.

`C25744` was the **only basic-library 10 kΩ 0402 in JLC's catalog**, so every
replacement is an **Extended** part. The one-time feeder fee is therefore a
consequence of the basic part being gone, not of the particular replacement
chosen; it is accepted.

| | C25744 (out) | **C60490 (in)** |
|---|---|---|
| MPN | `0402WGF1002TCE` UNI-ROYAL | **`RC0402FR-0710KL` YAGEO** |
| stock | **0** | **8 220 334** |
| library | base | **expand** |
| `leastPatchNumber` | 20 | **20** |
| `describe` | `-55℃~+155℃ 10kΩ 50V 62.5mW Thick Film Resistor ±1% ±100ppm/℃ 0402 Chip Resistor - Surface Mount ROHS` | **character-identical** |

Both records read live from JLC's catalog on 2026-07-27
(`selectSmtComponentList`, exact `componentCode` match); the two `describe`
strings were compared **as strings** and are equal. Same package, value,
tolerance, tempco, power and voltage — a true drop-in.

## The gate lesson this release paid for, recorded where it happened

**`jlc_stock_check.py` PASSED this very line at this seal**, hours before JLC
refused it. The evidence is still in this directory, `verification/stock_check.json`:

```json
{"lcsc": "C25744", "designators": "R28,R29", "qty": 2,
 "status": "OK", "stock": 291, "type": "base", ...}
```

291 ≥ 5 × 2, so the rule was satisfied and the verdict was `PASS`. The figure the
gate reads is `stockCount` — LCSC's **catalog** stock — and it does **not**
predict whether JLC's assembly uploader will clear the line. A `FAIL` from that
gate is real; a `PASS` is necessary and not sufficient. Teaching it to read the
assembly-side figure is a separate change and is deliberately not folded into a
one-line part swap.

## This directory is unchanged

Per the `07_releases/` contract, adding this file is the ONE mutation a sealed
release permits, and only because a successor now exists to name. Nothing else
here has been touched. The sha256 table in `MANIFEST.txt` still verifies against
every file it lists.

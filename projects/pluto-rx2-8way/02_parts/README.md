# 02_parts — folder status + deviations register

**Status: D-SPEC SOURCING SPIKE output, 2026-07-27/28.** Three dossiers, written
before any schematic exists. Nothing here is in a BOM yet, because there is no
BOM yet — stage 1 has not started. That is itself a deviation from the contract's
flow and it is registered below.

| MPN | role | LCSC | PDF present |
|---|---|---|---|
| `PE42482A-X` | the SP8T antenna selector | C5121458 | yes |
| `KH-SMA-KE-Z` | 10x SMA jack (8 antenna + RX1 out + RX2 out) | C504007 | **no** |
| `0402WGF4700TCE` | 470R series arm of the RX1 resistive pickoff | C25117 | **no** |

## Deviations from `contracts.md`

1. **Three `part.yaml` exist for parts not yet on a board.** The contract forbids
   "a `part.yaml` for a part not on the board (stale after a swap)". These are
   pre-BOM by design: the D-SPEC gate requires the sourcing spike to VERIFY the
   spec-critical part before architecture, precisely so stage 2 never DISCOVERS
   feasibility. **Before bring-up:** each must appear in the BOM or its directory
   must be deleted, and the swap noted in `01_docs/CHANGELOG.md`.

2. **`KH-SMA-KE-Z` has no committed PDF.** LCSC served HTML, not the PDF, to a
   plain fetch on 2026-07-27 (`sha256
   7c660e159756d9783d7f2394dd0363fffc0db5a5dffe4c88fc4cfc3d5d0f877c` is an HTML
   error page, not a document). The facts in its `part.yaml` were read from the
   byte-identical vendor PDF held read-only by the sibling project
   `pluto-cal-switch`, whose sha256 `05257621aa12...` was verified before
   reading. **Before bring-up:** fetch the PDF with a browser User-Agent, confirm
   it hashes to `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`,
   and commit it here. The project is NOT standalone until then.

3. **`0402WGF4700TCE` has no committed PDF and `datasheet.sha256: OWED`.** Its
   electrical facts came from the LCSC parametric record, not from a document.
   This is the series-sheet-passive case the contract names. **Before bring-up:**
   fetch it or record the passive as a permanent deviation with the parametric
   record as its cited source.

4. **`footprint:` names do not exist yet** for `PE42482A-X` and `KH-SMA-KE-Z`.
   Neither `.kicad_mod` has been drawn, in this project or anywhere in the repo —
   the sibling project's `pluto_cal_switch:SMA_Vertical_5.08sq_D1.4` is declared
   in its `part.yaml` and emitted by nothing. Both must be authored at stage 3;
   neither can be copied.

## Rejected candidates — no PDF committed, reason recorded

Per the contract, rejected candidates get the reason, not the binary. The full
reasoning is in the D-SPEC spike report; the one-line verdicts:

| candidate | LCSC | verdict |
|---|---|---|
| `BGS12WN6` (7x SPDT tree) | C1854968 / C27749420 | **STOCK 0 on every catalogue entry**, and the tree's worst-case isolation is one switch's, not three |
| `BGS12P2L6E6327` (7x SPDT tree) | C3312945 | in stock (1225) but no published RF row at 70 MHz or 6 GHz; 3.4 V VDD max |
| `PE42462A-X` | C22419301 | **SP6T, not SP8T** — datasheet cover, `UltraCMOS SP6T RF Switch, 10 MHz-8 GHz` |
| `HMC321ALP4E` | C1526237 | **stock 0** ($34.90/1, would be self-supplied); and GaAs IL is 1.7 typ / **1.8 max** even in the DC-2.0 GHz row vs PE42482's 1.1 max at 70 MHz. **NOT a negative-rail part** — an earlier note in this project's own spike brief said so and was WRONG: the datasheet title reads `GaAs MMIC SP8T NON-REFLECTIVE POSITIVE CONTROL SWITCH, DC*-8 GHz`, single +5 V bias, 0/+5 V TTL control, integrated 3:8 decoder. The negative-rail sibling is HMC322ALP4E. Rejected on stock and loss, never on supply. Also needs 9 DC blocking caps (RFC + 8 RF ports) whose value sets the low corner |
| `HMC322ALP4E` | C1558622 | stock 0 both codes |
| `SKY13418-485LF` | C150871 | 100 MHz-3.8 GHz — fails both band ends |
| `SKY13322-375LF` | C151465 | **SP4T**, not SP8T |
| `PE42582A-X` | C500479 | qualifies on spec; stock 7 at $14.91 — kept as an alternate, not primary |
| `ADRF5040BCPZ` | C579319 | SP4T; stock 7+20 |
| `MASW-008322` | C3304131 | SPDT; stock 3 |

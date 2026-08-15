# Stage 2 exact-MPN two-source qualification — 2026-08-15 UTC

Policy: every exact manufacturer/MPN row must be orderable at stock greater
than ten and sufficient for five boards from at least two independent
authorized pools. JLC/LCSC, Mouser and DigiKey qualify; Amazon does not.
Catalog observations are volatile and do not guarantee JLC assembly allocation.

## Composed result

| exact MPN | JLC/LCSC stock | second authorized pool | second-pool stock | result |
|---|---:|---|---:|---|
| 029707.5WXNV | not a JLC line | Mouser + DigiKey | 22,710 + 51,496 | pass |
| 16SVPF180M | 1,049 | Mouser | 42,154 | pass |
| 1935161 | 1,050 | Mouser | 23,872 | pass |
| 2N7002-7-F | 423,848 | Mouser | 6,757 | pass |
| 3568 | 196 | Mouser | 111,743 | pass |
| 61304021121 | 591 | Mouser | 3,093 | pass |
| 692121030100 | not a JLC line | Mouser + DigiKey | 3,145 + 5,644 | pass |
| 692221030100 | JLC C5334230: 47 | Mouser + DigiKey | 3,346 + 4,656 | pass; exact JLC MPN and manufacturer, CAD pad cloud fitted to manufacturer land at 0.0039 mm on 2026-08-15 |
| CL05A105KA5NQNC | 11,860,048 | Mouser | 278,377 | pass |
| CL05A106MQ5NUNC | 10,170,242 | DigiKey | 279,541 | pass |
| CL05B104KO5NNNC | 37,289,323 | Mouser | 3,315,945 | pass |
| DMP3007SPS-13 | 1,402 | Mouser | 1,314 | pass |
| EEEFK1A151P | 1,796 | Mouser | 11,006 | pass |
| GRM155R61H334KE01D | 41,484 | Mouser | 156,662 | pass |
| RC0402FR-07100KL | 6,189,357 | Mouser | 7,162,362 | pass |
| RC0402FR-0710KL | 9,802,132 | Mouser | 19,278,783 | pass |
| RC0402FR-071KL | 4,440,922 | Mouser | 4,569,940 | pass |
| RC0402FR-071ML | 1,814,411 | Mouser | 1,757,499 | pass |
| RC0402FR-07220KL | 625,339 | Mouser | 359,239 | pass |
| RC0402FR-072R2L | 199,666 | Mouser | 51,182 | pass |
| RC0402FR-074K7L | 7,095,385 | Mouser | 4,901,240 | pass |
| SN74LVC1G08DCKR | 89,946 | Mouser | 33,903 | pass |
| TLV76133DCYR | 18,740 | DigiKey | 1,241 | pass |
| TPD6E05U06RVZR | 3,638 | Mouser | 8,670 | pass |
| TPS2557DRBR | 2,642 | Mouser | 8,583 | pass |
| TS3USB221ERSER | 278 | Mouser | 9,626 | pass |
| TUSB522PIRGER | 2,418 | Mouser | 1,437 | pass |

Verdict: **PASS 27/27** by the composed two-authorized-pool policy.

## Evidence and interpretation

- Machine authority: `shopping-list-2026-08-15.json`, whose explicit verdict
  is `PASS` and whose terminal result is `COMPOSED-POOLS PASS: 27/27`.
- JLC input: fresh gitignored `06_build/cache/stage1_jlc_stock.json`; it grades
  24/24 coded candidate-BOM rows and explicitly reports three uncoded rows.
- Mouser input: exact plus suffix-aware broad API lookup, with exact-MPN and
  exact-manufacturer adjudication; 25/27 rows are sourceable there.
- DigiKey input: five direct product-page observations in
  `manual_quotes.yaml`; search snippets are not accepted.
- The fuse and two Wurth USB connectors intentionally have no LCSC code. Each
  instead clears both Mouser and DigiKey, so no fake JLC row is needed.
- Per-distributor missing quotes remain visible in the machine report. They do
  not invalidate a row that already clears two qualifying authorized pools.

The source gate changed three selected identities before schematic capture.
That is the intended economics: dossier and BOM edits are cheap; footprint,
placement and routing backtracks are not. Repeat the same gate on order day and
then use the JLC assembly uploader as the final allocation check.

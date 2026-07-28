# INDEX — what is in verification/, and how current each file is

cooksense **v1.5, 2026-07-27**. The board silkscreen still reads `v1.3` and that
is correct — `source/cooksense.kicad_pcb` is md5-identical to v1.4's, v1.3's and
`04_kicad/`'s (`420445b5141dd1111eccab038c68511b`).

**THE CURRENCY COLUMN IS THE POINT OF THIS FILE.** A release that carries an
artifact describing an earlier board, without saying so, is how cooksense v1.3
shipped seven stale files. The rule applied here:

- Anything that reads the **BOARD** or the **NETLIST** is carried forward from
  v1.4 **and is still current**, because both are byte-identical.
- Anything that reads the **BOM** was **REGENERATED**, because the BOM is what
  moved. Nothing BOM-derived is carried.

| file | what it is | currency |
|---|---|---|
| `INDEX.md` | this file | **v1.5** |
| **REGENERATED FOR v1.5 — everything below reads the new BOM, the new power tree, or was re-run on this archive** | | |
| `bom_legibility.txt` | **F-LEGIBLE: OK, 0 findings, 56 checks.** The same checker returns **FAIL, 83 findings, 0 checks** on sealed v1.4 beside it | **v1.5** |
| `bom_source_check.txt` | M-BOM against THIS archive's `fab/bom_jlc.csv`: **PASS**, leg C 25/25 R/C rows value-graded | **v1.5** |
| `bom_delta.txt` | v1.4 → v1.5 BOM delta parsed AS CSV: 56→56 rows, 0 added, 0 removed, **0 Footprint changes**, 2 LCSC cells, 54 MPN fills, 28 Comment rewrites | **v1.5** |
| `copper_did_not_move.md` | **the four-way proof** — board md5, aperture-resolved gerber comparison (11/13 identical geometry), shoelace pour AREA equal to 6 decimals on all four copper layers, byte-identical CPL | **v1.5** |
| `circuit_value_check.txt` | tsx value prop vs the ordered code's catalog value: PASS | **v1.5** |
| `part_facts.txt` | P-FACT: 6/43 dossiers declare `asserts:`, **5 graded** (was 3), 1 deferred | **v1.5** |
| `part_facts_red_verification.txt` | **proof the two NEW value asserts can FAIL.** Rewriting the C60490 Comment to `22k` in a scratch copy makes P-FACT fail naming **17 refs**; C138040 → `5.1k` names R_ILM; the unmodified control is green | **v1.5** |
| `power_tree.yaml` | the power tree as GRADED — the AMS1117-3.3 rail moved out of the ignored `linear_rails:` key into `rails:`, with dropout and dissipation CITED to ds1117 page and note | **v1.5** |
| `stock_check.txt` / `.csv` / `.json` — **VERDICT FIELD** | A-STOCK on THIS release's BOM, one snapshot 2026-07-27. `stock_check.json` carries `"verdict": "FAIL"`. **Explained and expected:** the only failing line is `C42400616` (J_ISOLOOP), which is OFF THE CPL by design and hand-soldered — see ORDER_README §4 and §5. Flagged here so a reader who greps for FAIL meets the explanation next to it | **v1.5** |
| `assembly_coverage.txt` / `.json` | A-POP population + A-POS datum, against this archive's CPL/BOM/MANIFEST | **v1.5** |
| `missing_models.txt` | A-BODY: **189/189 bodies mounted.** Generated **with `--cpl`** — v1.4's was generated without it, so its denominator was 186 BOARD footprints and it counted `J_ISOLOOP`, which is not on the CPL at all | **v1.5** |
| `twin_report.csv` | jlc_twin, re-run against this archive's BOM | **v1.5** |
| `drc.json` | DRC `--severity-all --refill-zones --schematic-parity` = **0 / 0 / 0**, re-run on the board in this archive | **v1.5** |
| `erc.json` | ERC `--severity-all` = **0 errors / 1303 warnings** (913 endpoint_off_grid, 389 lib_symbol_issues, 1 isolated_pin_label) — the same 1303 as v1.4 | **v1.5** |
| `einv.txt` | E-INV **83/83** against a freshly exported netlist (`source/cooksense.net`) | **v1.5** |
| `policy_audit.md` | the policy table for `--board cooksense`. **Read the E-TOPO row** — it is the one FAIL, it is a supply-specification finding, and ORDER_README §0 is its home | **v1.5** |
| `rotation_human_gate.txt` | **A-POL: 10 codes / 13 refs** (GENERATED) — byte-identical to v1.4's. **It does NOT win over prose, and this is the one exception in this table:** three further refs (`D_KSTOP`, `D_REVCLAMP`, `D_TVS` — codes C8678, C113974) are POLARITY-FIT-BLIND in `twin_report.csv`, so they never reached the generated list. True single-channel population **12 codes / 16 refs**. ORDER_README §6 item 15 is their only defence | **v1.5** (unchanged bytes) |
| **CARRIED FROM v1.4 — the board and netlist are byte-identical, so these are still current** | | |
| `ADR-0015-creepage-is-not-clearance.md` | **the H4 decision record** — why the through-notch counts toward CREEPAGE, the geodesic re-derived independently, and why K_STOP may not be moved | v1.3/v1.4, current |
| `audit.txt` | audit_board: I-POL/I-PROX/I-EDGE/I-OUT/I-ISO/I-HW. Its four `I-HW` lines are CORRECT — `H4 a=6.598mm … PASS` is the **CREEPAGE**, the quantity `keypad_isolation_6mm` requires, not the 4.0286 mm straight-line CLEARANCE. See ADR-0015 | v1.3/v1.4, current |
| `build_gates.md` | P-COLLIDE, contracts_audit, tests/run_tests.sh, stitch gate — **from the v1.3 build.** The board was not rebuilt for v1.5, so these are the build that produced it; the test-suite count in it is v1.3-era and the v1.5 figure is in the seal commit instead | v1.3, board-current, test count STALE |
| `dispositions.md` | every finding the v1.3 revision raised and what was done | v1.3, current |
| `dispositions_v10_carried.md` | **HISTORICAL** — v1.0 dispositions, kept for provenance | v1.0, historical |
| `einv_red_verification.md` | proof the E-INV checker CAN fail, against the 83 this release ships | v1.3, current |
| `fresh_lens.md` | zero-context review of the frozen v1.3 archive | v1.3, current for the board |
| `mrepro.md` — **VERDICT STRING** | prints **"M-REPRO: RED (1 class(es) differ)"** twice. Explained in the file's own VERDICT section and in ORDER_README §13 item 17: the three from-source rebuilds are geometrically identical but not byte-identical, because the generator mints fresh UUIDs and KiCad serialises footprints in UUID order. Green BY METRIC, red by bytes | v1.3, current |
| `parity.md` | converter `kicad_sch` vs the shipped board, node-for-node | v1.3, current |
| `pin_review.md` | dossiers regenerated for v1.3; **narrative group review NOT re-run** — limits stated in the file | dossiers v1.3, narrative NOT run |
| `redteam_layout.md` | red-team lens B (fab/orderability) | v1.3, current |
| `redteam_topology.md` | red-team lens A (safety/electrical) — **carries a RETRACTION header**: its DO-NOT-SHIP verdict is superseded, findings fixed or deferred | review v1.3, verdict retracted |
| `render_top_bare.png`, `render_bottom_bare.png` | board renders | v1.3, current |
| `render_review.md` | renders regenerated for v1.3; **narrative review NOT re-run** — limits stated in the file | renders v1.3, narrative NOT run |
| `rotation_audit.txt` | A-ROT table state (61 rows) | v1.3, current |
| `rotation_C22046_measurement.md` | **MIXED — historical body, CURRENT correction block.** The appended `CORRECTION, 2026-07-26` section is a v1.3 result and is the in-archive evidence behind ORDER_README §6's resolved-disagreement table. **Do not discard it as historical** | body historical, correction current |
| `rotation_measurements_v13.txt` | raw two-channel measurements behind the rotation rows | v1.3, current |
| `semantic_battery.txt` | E-INV, S-COUNT, S-NETMERGE, S-PARITY, A-ROT/A-POL, M-BOM, A-POP/A-POS — **run against the v1.3/v1.4 BOM.** Its M-BOM and A-POP halves are superseded by the regenerated `bom_source_check.txt` and `assembly_coverage.txt` above; its netlist halves are current | mixed — netlist current, **BOM halves SUPERSEDED** |
| `stranded_islands.md` | **121/121** pour islands bonded, 0 stranded (F.Cu 106 + B.Cu 13 + In1 1 + In2 1). `copper_did_not_move.md` re-measures those same 121 regions on this release's own gerbers and finds identical area | v1.3, re-confirmed |
| `twin_adjudications.yaml` | every jlc_twin finding class, adjudicated — **also the input to this release's twin re-run** | v1.3, current |
| `twin_*.png` | jlc_twin renders | v1.3, current |

## The two files this release deliberately does NOT ship

- **`bom_echo_gate.txt`** — the F-ECHO worklist (54 coded lines to confirm
  against JLC's own resolved table after upload). It is an ORDER-DAY artifact
  that only becomes evidence once a human has pasted JLC's resolved BOM back in,
  and shipping an unfilled worklist as verification would be a gate that grades
  nothing. It is produced by the exporter into `06_build/fab/`.
- **a v1.5-era `fresh_lens.md`** — the zero-context review is of the v1.3 board,
  which is this board. A second lens on an unchanged board would be ceremony.
  What IS new here is the BOM, and the BOM has three independent machine gates
  on it (`bom_legibility`, `bom_source_check`, `part_facts` + its RED proof).

# INDEX — what is in verification/, and how current each file is

cooksense v1.3, 2026-07-26. Every file below was produced from the board in
this archive unless the CURRENCY column says otherwise.

The previous staging shipped seven artifacts that described an earlier board.
This index exists so that question is answerable without opening each file.

| file | what it is | currency |
|---|---|---|
| `INDEX.md` | this file | v1.3 |
| `ORDER_README.md` (also at archive root) | how to order, what to check, declared gaps | v1.3 |
| `dispositions.md` | every finding this revision raised and what was done | v1.3 |
| `drc.json` | DRC --severity-all --refill-zones --schematic-parity = 0/0/0 | v1.3 |
| `erc.json` | ERC --severity-all = 0 errors / 1303 warnings (run IN PLACE, with fp-lib-table) | v1.3 |
| `ADR-0015-creepage-is-not-clearance.md` | **the H4 decision record** — why the through-notch counts toward CREEPAGE, the geodesic re-derived independently, and why K_STOP may not be moved. Shipped because §1's PASS rests on it | v1.3 |
| `mrepro.md` — VERDICT STRING | prints **"M-REPRO: RED (1 class(es) differ)"** twice. **Explained in the file's own VERDICT section and in ORDER_README §13 item 17:** the three from-source rebuilds are geometrically identical but not byte-identical, because the generator mints fresh UUIDs and KiCad serialises footprints in UUID order. M-REPRO is green BY METRIC, red by bytes. Flagged here so a reader who greps for RED meets the explanation next to it | v1.3 |
| `stock_check.txt` / `.csv` / `.json` — VERDICT FIELD | `stock_check.json` carries `"verdict": "FAIL"`. **Explained and expected:** the only failing line is C42400616 (J_ISOLOOP), which is OFF THE CPL by design and hand-soldered — see §4 and §5. Flagged here so a reader who greps for FAIL finds the explanation next to it, as `parity.md` already is | v1.3 |
| `audit.txt` | audit_board: I-POL/I-PROX/I-EDGE/I-OUT/I-ISO/I-HW. Its four `I-HW` lines are CORRECT — `H4 a=6.598mm ... PASS` is the **CREEPAGE** (surface path around the outline notch), which is the quantity `keypad_isolation_6mm` requires. A 2026-07-26 ruling briefly treated it as superseded by the 4.0286 mm straight line; that ruling was reversed the same day — 4.0286 mm is the CLEARANCE, a different and far smaller requirement. See ORDER_README §1 and ADR-0015 | v1.3 |
| `einv.txt` | E-INV 83/83 | v1.3 |
| `einv_red_verification.md` | proof the E-INV checker CAN fail, against the 83 this release ships | v1.3 |
| `semantic_battery.txt` | E-INV, S-COUNT, S-NETMERGE, S-PARITY, A-ROT/A-POL, M-BOM, A-POP/A-POS | v1.3 |
| `parity.md` | converter kicad_sch vs the shipped board, node-for-node | v1.3 |
| `mrepro.md` | 3 from-source rebuilds, 1047 vias each, matching the shipped board | v1.3 |
| `build_gates.md` | P-COLLIDE, contracts_audit, tests/run_tests.sh, stitch gate | v1.3 |
| `bom_source_check.txt` | M-BOM leg C against THIS archive's fab/bom_jlc.csv | v1.3 |
| `circuit_value_check.txt` | tsx value prop vs the ordered code's catalog value | v1.3 |
| `assembly_coverage.txt` / `.json` | A-POP population + A-POS datum | v1.3 |
| `stock_check.txt` / `.csv` / `.json` | A-STOCK, one snapshot, all three from the same run | v1.3 |
| `rotation_audit.txt` | A-ROT table state (61 rows) | v1.3 |
| `rotation_human_gate.txt` | **A-POL: 10 codes / 13 refs** (GENERATED). **It does NOT win over prose here, and this is the one exception in this table:** three further refs (D_KSTOP, D_REVCLAMP, D_TVS — codes C8678, C113974) are `POLARITY-FIT-BLIND` in `twin_report.csv`, i.e. the twin could not fit them at all, so they never reached the generated list. True single-channel population **12 codes / 16 refs**. See ORDER_README §6 item 15 | v1.3 |
| `rotation_measurements_v13.txt` | raw two-channel measurements behind the rotation rows | v1.3 |
| `part_facts.txt` | P-FACT; CE1's pad1_net_polarity EXECUTES against this archive | v1.3 |
| `policy_audit.md` | the policy table **plus a ship-time annotation**: 3 of its 4 FAILs grade the INTERPOSER, not cooksense | v1.3 + annotation |
| `stranded_islands.md` | **121/121** pour islands bonded, 0 stranded (F.Cu 106 + B.Cu 13 + In1 1 + In2 1); + the sibling-context trap. The 136 an earlier revision of THIS LINE carried came from a refill-in-memory, not the shipped fill | v1.3 |
| `twin_adjudications.yaml` | every jlc_twin finding class, adjudicated | v1.3 |
| `twin_report.csv`, `missing_models.txt`, `twin_*.png` | jlc_twin output and renders | v1.3 |
| `render_top_bare.png`, `render_bottom_bare.png` | board renders | v1.3 |
| `redteam_topology.md` | red-team lens A (safety/electrical) — **carries a RETRACTION header**: its DO-NOT-SHIP verdict is superseded, findings fixed or deferred | review v1.3, verdict retracted |
| `redteam_layout.md` | red-team lens B (fab/orderability) | v1.3 |
| `pin_review.md` | dossiers regenerated for v1.3; **narrative group review NOT re-run** — limits stated in the file | dossiers v1.3, narrative NOT run |
| `render_review.md` | renders regenerated for v1.3; **narrative review NOT re-run** — limits stated in the file | renders v1.3, narrative NOT run |
| `fresh_lens.md` | zero-context review of this frozen archive | **added at seal** — see note below |
| `dispositions_v10_carried.md` | **HISTORICAL** — v1.0 dispositions, kept for provenance | v1.0, historical |
| `rotation_C22046_measurement.md` | **MIXED — historical body, CURRENT correction block.** The original C22046 record is historical; the appended `CORRECTION, 2026-07-26` section is a **v1.3 result** and is the in-archive evidence behind ORDER_README §6's resolved-disagreement table and §13 item 10 (7 of 51 CPL codes re-measured operator-free, incl. C125121/U_OPTO and C2887273/CE1). **Do not discard it as historical.** | body historical, correction v1.3 |

## One file is deliberately NOT a v1.3 result, and one is MIXED

`dispositions_v10_carried.md` is a historical record, labelled as such in this
table and by a banner in its own header.

`rotation_C22046_measurement.md` is **mixed**: its body is the historical
C22046 record (and still carries the line "Status: BLOCKS THE v1.2 SEAL", which
is historical too), but the `CORRECTION, 2026-07-26` block appended at the end
is a **current v1.3 measurement** that ORDER_README §6 and §13 item 10 both rely
on. Read the correction block; treat the body as history.

Everything else describes the board in `source/` and `fab/`.

## Two files describe work that was NOT done

`pin_review.md` and `render_review.md` ship because their MACHINE half is
current and useful. Their NARRATIVE half — a fresh human-equivalent reading —
was not re-run for v1.3. Each says so in its own first paragraph. If a
narrative pin or render review is a release requirement, this release does
not satisfy it.

## `fresh_lens.md`

The zero-context review is run against the FROZEN archive as the last step before
sealing, so it can read the bytes that ship rather than a moving target. If this
file is absent from the archive you are holding, the archive was staged but not
sealed, and the review either did not run or did not pass.

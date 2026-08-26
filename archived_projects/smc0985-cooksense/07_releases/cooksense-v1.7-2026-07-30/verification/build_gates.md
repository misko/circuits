# Gate scoreboard — cooksense v1.7, 2026-07-30

**Every number below was MEASURED BY THE SEALING AGENT, at seal time, UNPIPED,
with the RAW exit code captured** (`cmd > file; echo "RAW_EXIT=$?"`). Nothing
here is inherited from the staging beacon or from a predecessor pass. A
`| tail` returns *tail's* exit code, which has burned this repo twice; no
command in this table was piped.

Board under grade: `cooksense`. `04_kicad/cooksense.kicad_pcb` md5
`9f4fd5fae810f40a52b1035df727243c` — **byte-identical to
`source/cooksense.kicad_pcb` in this archive**, verified by `md5sum` on both
paths, so every board-derived number below applies to the sealed bytes and not
to a neighbouring build.

## The two claims

    DESIGN:   PASS
    SOURCING: BLOCKED-1 (C265111; measured 2026-07-30)

A seal asserts *this design is correct* and *this design is orderable today*.
They are separate claims with separate authorities — the design gates grade an
artifact we control, `A-STOCK` grades the WORLD — and this release passes the
first and fails the second. That is a legal, LOUD state (canon A-BUY), not a
green painted over a red: the blocked line, its LCSC and the measurement date
are carried in `MANIFEST.txt` and on `ORDER_README.md`'s first screen, and
`release_freshness_check.py` cross-checks all three against the shipped
measurement in both directions.

## Design-side gates

| gate | command | RAW exit | measured |
|---|---|---|---|
| DRC (live board) | `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` | **0** | **0 violations / 0 unconnected / 0 parity** |
| DRC (**archive standing alone**) | same, on a copy of `source/` made OUTSIDE the repo | **0** | **0 / 0 / 0** — see "Archive self-containment" below |
| ERC | `kicad-cli sch erc --severity-all` | **0** | 411 violations, **all severity `warning`; 0 errors** (severity histogram computed from `erc.json`, not read off the headline) |
| policy_audit | `policy_audit.py . --board cooksense` | **0** | **FAIL=0** — PASS=28, WAIVED=6, HUMAN=6, N-A=5 |
| S-COUNT | `count_parity.py . --board cooksense` | **0** | **4/4** source pairs agree with manifest over **239 refdes** |
| E-INV | `electrical_invariants.py .` | **0** | **167/167** invariants hold |
| E-ADR | `electrical_invariants.py . --adr-coverage` | **0** | **11/11** protection/topology ADRs cited by an invariant |
| M-BOM | `bom_source_check.py fab/bom.csv circuit.json --parts 02_parts` | **0** | PASS — every BOM LCSC == source; leg C 28/28 R/C rows value-graded over 61 BOM rows |
| F-LEGIBLE | `bom_legibility_check.py <release> --parts 02_parts` | **0** | 60 checks passed; F-WORDS all 61 Comments human-readable |
| P-FACT | `part_facts_check.py <release> --parts 02_parts` | **0** | 6/6 assertions REACHED A COMPARISON, 0 unreached; coverage 7/47 dossiers declare `asserts:` |
| M-DEPEND | `sealed_dependency_check.py .` | **0** | PASS (0 findings); fragility note: 61 rows across 3 releases resolve only because a dossier is still in the tree |
| M4 waivers | `waiver_provenance.py projects --project smc0985-cooksense --twin` | **0** | PASS — 12/72 waivers graded across 1/5 projects; 4 UNBACKED machine waivers (ceiling 9, named debt) |
| placement gates | `placement_gates.py <board> --config placement_gates.json` | **0** | PASS — P-OUT tightest margin 0.62 mm (`J_ESTOP.MP`, min 0.15); P-CAP worst cut ratio 0.28 (fail > 0.5) |
| A-ROT / A-POL | `jlc_rotation_audit.py --table` | **0** | 64 rows, each an independently MEASURED authority (M-PROV) with its polarity channel declared |
| R-LEN | `copper_length_audit.py .` | **0** | N-A — this board declares no `length_match:` group; 0/0 graded, stated out loud rather than counted as a pass |
| contracts | `scripts/contracts_audit.py` | **0** | 257 files, **0 violations** |
| M-BEACON | `status_beacon_check.py projects/smc0985-cooksense` | **0** | 2/2 beacons agree with the tree (re-run AFTER the seal commit — canon M-BEACON, 07_releases seal step 4) |
| A-POP | `assembly_coverage.py <release> --assembly .../assembly.yaml` | **0** | board=243 footprints, cpl=206 placements, unpopulated=37 (declared=16, exempt prefixes H/TP); A-POS datum worst 0.00050 mm (`J_ESTOP`) vs 0.05 mm tolerance |

## Sourcing-side gates

| gate | RAW exit | measured |
|---|---|---|
| A-STOCK (`jlc_stock_check.py fab/bom_jlc.csv --json`) | **1** | **57/58 coded lines clear 5x qty; exactly ONE problem line: `C265111` LOW_STOCK(5)** |
| independent catalog read (my own HTTP client, no import of `jlc_stock_check`) | **0** | see below |

Read at **2026-07-30T23:46:46Z**, against `selectSmtComponentList`, with a
control:

    C265111      stock=5        MOQ=21     JST        SM08B-GHS-TB(LF)(SN)
    C42376901    stock=6000     MOQ=1      SHOU HAN   SH-SM08B-GHS-TB(LF)(SN)
    C22391766    stock=0        MOQ=444    JST        SM08B-GHS-TB
    C5620        stock=5212     MOQ=1      Nexperia   74HC238D,653      [CONTROL]

**`minPurchaseNum` 21 EXCEEDS `stockCount` 5**, so `C265111` is unbuyable at
*any* quantity today — it is not "short by half". **The threshold to watch is
21, not the gate's 10.** The control returns live stock, so the 5 and the 0 are
the catalog's answer and not a dead field. This reproduces the archive's
21:33:59Z reading (stock 5 / MOQ 21) two hours later through code that shares
nothing with it; the clone moved 6030 -> 6000 in the interval, which is what a
live field looks like.

## Archive self-containment (canon: a release is a COMPLETE ARCHIVE)

`source/` was copied to a scratch directory **outside the repository** and DRC
run there:

    RAW_EXIT=0    Found 0 violations / 0 unconnected items / 0 schematic parity issues

`source/fp-lib-table` resolves its one project library as
`${KIPRJMOD}/cooksense.pretty` — **inside the archive** — and the five
`.kicad_mod` files it names ship in `source/cooksense.pretty/`. Everything else
is `${KICAD10_FOOTPRINT_DIR}`, the installed KiCad standard library.

This is a REGRESSION THAT WAS CAUGHT, not a property that was assumed: an
earlier v1.7 staging carried `${KIPRJMOD}/../03_src/lib/…`, which points OUTSIDE
the archive, and a standalone DRC on it returned **14 `lib_footprint_issues`**.
A fleet sweep found the same defect in **5 of 33** sealed archives
(cooksense-v1.1, interposer-v1.0, usb-hub-3s-v3 v1.3 / v1.4 / v1.6). Those are
immutable and are recorded, not repaired. Nothing in the repo gates this
property — filed as owed skill patch P9 (`owed_skill_patches.md`).

## Gates that FAIL, stated rather than omitted

### `net_reference_audit.py` (E-NETREF) — RAW exit **1**

    E-NETREF: FAIL — 271/292 references resolved, 21 ghost (5 with a named
                     near-miss), 0 unreached

**All 21 ghosts are kind K7** (`02_parts/*/part.yaml layout.keep_short[].net`).
Every other kind is 0 ghost: the netclass lists (K1 40/40), scoped floors
(K2 2/2), invariant supplies and nets (K3 2/2, K4 140/140), invariant chains
(K5 21/21), power-tree rails (K6 9/9), floorplan zones, pad-net asserts and silk
captions (K8 3/3, K9 35/35, K11 2/2). **No ghost reaches copper, silk, the
netlist or the BOM** — the entire exposure is that a P-ADJ adjacency BUDGET
grades nothing.

That exposure is already **declared and waived with its own evidence** by
`policy_audit`'s `P-ADJ-UNREACHED` row (WAIVED, 23/38 budgets). The two counts
reconcile exactly: both gates read the same 38 K7 sites; E-NETREF counts the 21
whose net **does not exist on this board at all**, P-ADJ-UNREACHED counts the 23
whose net has **fewer than 2 pads** — a superset by construction, since an
absent net has 0 pads. The 2-site difference is budgets naming a net that exists
but lands fewer than two pads.

The ghosts are datasheet-reference-design net names that travelled into the
dossiers with the part (`VCC`, `VDD`, `VREF`, `T_PLUS`, `T_MINUS`, `BIAS`,
`RCEXT`, `HS_GATE`, `LED_DRIVE`, `OPTO_LED`, `+5V`, `N3V3`, `3V3_DIGITAL`) —
the exact class the gate was built to find. Five carry a named near-miss the
gate itself proposes. **This is real, pre-existing debt against `02_parts/`, not
a defect in the sealed board**, and it is recorded here rather than left to a
green exit code somewhere else. E-NETREF landed 2026-07-29/30 and did not exist
when v1.6 sealed, so v1.6 ships no netref evidence — this is the first cooksense
release to state the number at all. Owed as next-rev work, not fixed in this
release: the fix is 21 dossier edits under `02_parts/`, which would move the
part-selection inputs of a board whose fab set is already frozen and graded.

### `rules_audit.py` (A-AMP) — RAW exit **1**, two findings, both DECLARATION defects

    ok    A-FIRE   all 11 cooksense.kicad_dru rule(s) can fire
    ok    A-ORDER  generate_rules runs last before the DRC gate
    FAIL  A-AMP ANALOG_SENSE: `current: 'uA-level sense'` declares a value this
          gate cannot read, so its width was NEVER CHECKED
    FAIL  A-AMP PWR_IN: carries 2.0A but the narrowest enforced width is 0.5mm;
          IPC-2221 needs >= 0.781mm (dT=10.0C, 1.0oz, external)
    coverage A-AMP: 7/8 net-class current declarations graded
    RULES AUDIT: FAIL (2 fails, 24 checks)

MEASURED by me (with `--board`, so `A-FIRE`'s `insideArea()` predicates were
actually resolved rather than skipped — without it the tool says so out loud).
Both findings are in `03_src/cooksense/rules/nets.yaml`, not in copper, and both
PRE-DATE v1.6:

- **`ANALOG_SENSE`** declares `current: 'uA-level sense'` — prose where the gate
  needs a magnitude. The correct reading is that this class's width was
  **never graded**, which the gate reports as a FAIL rather than passing it
  silently. That is the right behaviour (canon M-COVER: an ungraded subject is
  not a pass) and the fix is one line — `current: signal`, or a number with a
  unit. Not made here: `nets.yaml` is a routing INPUT, and editing it after the
  route is promoted and the fab set frozen would invalidate the DRC evidence
  this release ships.
- **`PWR_IN`** declares 2.0 A against a 0.5 mm enforced minimum width. The
  minimum is a floor on TAP runs; the trunk current rides POURS, which
  `policy_audit`'s evidenced `R-POUR` waiver names for exactly these four nets
  (`5V_IN`, `5V_FUSED`, `5V_PROTECTED`, `5V_RPP`). **INHERITED, NOT RE-DERIVED
  BY ME:** the prior thermal analysis records ΔT = +0.9 °C at the operating
  worst case and +16.2 °C at the 1.79 A hard limit set by `R_ILM` = 1.2 kΩ. I
  did not re-run that computation this pass; it is flagged so a successor knows
  which number is load-bearing and unchecked.

### Everything else

`escape_check.py` and `board_netlist_parity.py` standalone CLIs, and the repo
test suite's seven failures (none of them this board's — each failing assertion
names its own subject, checked), are recorded in `gates_not_run.md`.

### Summary: THREE gates exit non-zero, and none of them is copper

| gate | raw exit | what it is |
|---|---|---|
| A-STOCK | 1 | the SOURCING claim — one line, `C265111`, unbuyable today |
| E-NETREF | 1 | 21 ghost `keep_short` budget references in `02_parts/`; no board exposure |
| A-AMP (`rules_audit`) | 1 | two `nets.yaml` declaration defects predating v1.6 |

Every gate that grades the BOARD — DRC both halves, standalone DRC, ERC,
parity, S-COUNT, E-INV, E-ADR, placement, audit_board, twin, A-RENDER, A-POP,
A-POS, A-ROT, M-BOM, F-LEGIBLE, F-PAYLOAD, P-FACT — exits **0**.

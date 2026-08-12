# contract: 03_src/

**Purpose** — the only hand-written truth about the board's *KiCad-side*
design: placement, rules, the promoted route, and the per-board gates.
Everything in `04_kicad/` and `06_build/` is derived from here plus
`03_tscircuit/`. If `03_src/` and `04_kicad/` disagree, `03_src/` is right and
`04_kicad/` is stale.

**Mutability** — hand-edited.

**Where the generators live** — the heavy pipeline scripts are SHARED and live
in the skill, `skills/kicad-pcb/scripts/`, NOT in this folder: `generate_board_generic.py`,
`route_and_stitch_generic.py`, and `generate_rules_generic.py`. A board does not
carry its own `generate_board.py` / `route_prep.py` / `stitch_and_fill.py` /
`generate_rules.py` anymore (those are RETIRED — ADR-0002 / generic backend,
2026-07-20; `generate_rules` was promoted to the shared emitter after a
clean-room run proved its logic is 100% board-independent). `03_src/` holds the
board-specific **config** the shared scripts consume, plus exactly ONE small
per-board gate: `audit_board.py` (board-specific placement/pad invariants).

## Allowed

| File | What | Consumed by |
|---|---|---|
| `floorplan.yaml` | placement config: outline, mounting holes, `fiducials {footprint, refdes_prefix, at[]}` (>=3 non-collinear; board-only, BOM- and CPL-excluded — a fiducial has no net, no BOM line and no placement row, so it is a BOARD FEATURE, not a part), named regions, anchors, `repeat:` banks, keepouts (incl. `deny: []` PERMISSIVE DRU anchors — the thing `rules/nets.yaml` `scoped_floors` scopes a width relaxation to), zones, silk, orientation asserts. **THIS FILE IS ALSO WHERE A GENERIC-BACKEND BOARD SATISFIES P-POL AND P-KEEP** (canon P2/P3): `asserts.pad_net[]` is the pad-1-net polarity check — `generate_board_generic.run_asserts()` hard-fails the driver on a mismatch — and `keepouts[]` / `board.mounting_holes` are half the keepout declaration (`route.yaml prep.keepouts` and `rules/mates.yaml` are the rest). `policy_audit.py` grades the PRESENCE of both and NAMES which home satisfied it with a count; an EMPTY block satisfies nothing (canon M-COVER). Before 2026-07-30 both checks grepped `03_src/` for the per-board Python ADR-0002 abolished, so every compliant board carried two verbatim waivers | SHARED `generate_board_generic.py`, `policy_audit.py` (P-POL/P-KEEP presence) |
| `thermal_vias` | Optional fabrication-via declarations. Preferred `fields[]` rows name `ref` or `refs`, an owning `pad`, `size`, `drill`, and non-empty footprint-relative `at` coordinates; optional shared/field-level `protection: {capping,filling}` emits item-level IPC-4761 overrides, not an ambiguous board default. The generator resolves the pad's live nonzero net and emits true board-level vias without modifying the library-linked footprint. Legacy `promote_heatsink_pads[]` instead replaces every drilled `pad_prop_heatsink` subpad on each named footprint with an identical true via and clears the now-modified embedded footprint's library ID while preserving its source FPID in the description. These are the JLC fill/cap boundary: component PTH holes are not vias and ordinary route vias must not silently inherit a via-covering order. Unknown refs/pads, empty matches, invalid geometry/protection, slots and unnetted marks refuse. | SHARED `generate_board_generic.py` |
| `route.yaml` | routing + stitch config plus `flow.pre_route_reviews` exact-artifact bindings, `route.preflight_critical_pairs` (R-PAIRMAP/R-CRITESC), and optional `via_ampacity` series-boundary declarations (A-VIA). Every critical differential pair is assigned to the differential engine, length-match group, allowed layers, and via policy before routing; the realized board is rechecked after stitch. An explicitly selected existing `route.final` is P-ROUTEBASE-compared to the exact prepared r0—including deterministic seed segments/vias—before placement review. | SHARED `pre_route_review_check.py`, `promoted_route_check.py`, `critical_route_check.py`, `via_ampacity_check.py`, `route_and_stitch_generic.py` |
| `rules/integration.yaml` | P-MOD module-first architecture record: every complex subsystem selects a module or carries a bare-IC exception with binding requirement, measured/cited comparison, considered modules and ADR. Absent means legacy/unmigrated, never pass | SHARED `module_first_check.py`, `policy_audit.py` |
| `rules/` | machine-enforced design intent, including `requirements.yaml` (D-SPEC/E-PATH), `power_tree.yaml` (E-TOPO/E-MARGIN), `power_stages.yaml` (E-SWDRV), `protection_paths.yaml` (E-SURGE), `nets.yaml`, `electrical_invariants.yaml`, `assembly.yaml`, and review/waiver records; see `rules/contracts.md` | SHARED semantic gates, rule generator, policy audit, assembly coverage, and jlc_twin |
| `route/**` | the PROMOTED KRT chain (`*.kicad_pcb`) — a committed ARTIFACT, not code (canon M3); `import` replays it deterministically | SHARED `route_and_stitch_generic.py import` |
| `audit_board.py` | the ONLY per-board emitter: the placement/pad invariant gate (polarity, proximity, plane-clean, refdes-on-silk, and any BOARD-SPECIFIC guard e.g. an analog-keepout distance). Everything else is config or shared. **OPTIONAL, and its absence is a DECLARATION, not a gap**: a zero-bespoke-Python board (ADR-0002) has none, and step 4 below guards the call and SAYS SO when it is missing — see that row for why a silent skip is the worse of the two failures | — (guarded call in `rebuild_all.sh` step 4) |
| `placement_gates.json` | OPTIONAL config for `placement_gates.py`: P-OUT, P-CAP, and non-waivable P-BODYCLR positive courtyard/body-to-foreign-pad clearance (`body_clearance_mm`, default 0.10 mm). Same-side assembled footprints without courtyards fail. P-OUT/P-CAP waivers require evidence; P-BODYCLR cannot be waived. | SHARED `placement_gates.py` |
| `bom_seed.py` | maps BOM comments → `02_parts/` MPN → LCSC; fails on unmapped/TBD lines | required before ordering |
| `rebuild_all.sh` | THE entry point: thin driver that calls the SHARED generics in canonical order, `set -euo pipefail`. Its normal arm creates the exact schematic review subject and stops if review evidence is absent; after reviews, `--resume-after-schematic-review` verifies the content checkpoint and continues without rerunning nondeterministic TSX. | REQUIRED |
| `rebuild_reuse.sh` | the DETERMINISTIC promoted-chain rebuild driver, seeded from `skills/pcb-design/templates/03_src/rebuild_reuse.sh` (config-driven — needs no per-board edits). Skips the NON-DETERMINISTIC tsci stage (`tsci build` churns the generated `.kicad_sch` by ~2900 lines of UUID/ordering noise per run — the committed `03_tscircuit/kicad/<board>.kicad_sch` is the PINNED canonical schematic): netlist from the pinned sch, board from committed `03_src/` config, `import` of the promoted `route/` chain, stitch, `generate_rules` LAST, then the full `--severity-all --refill-zones --schematic-parity` gate (the pinned sch is copied beside the board FIRST or parity silently skips). Use for per-iteration/verification rebuilds; run `rebuild_all.sh` when the schematic changed. Do NOT hand-copy the retired per-board `rebuild_fast.sh` variants back in (M8: this pattern was independently rewritten 3x before promotion, 2026-07-23). Properties pinned by `tests/t1_rebuild_templates.py` | replaces nothing in `rebuild_all.sh`; both drivers coexist |
| `export_pdfs.sh` | release PDF set (pcb_layers, assembly) + PNG verification renders | |
| `lib/` | project-local footprints tscircuit/KiCad can't yet express — see `lib/contracts.md` | |
| `*.py` | **STOPGAP ONLY (canon M8)**: any script beyond `audit_board.py`/`bom_seed.py` is a declared backend gap — its docstring MUST name the gap and the config schema that would replace it. The SECOND board needing the same script triggers mandatory promotion into the shared backend | `rebuild_all.sh` |
| `contracts.md` | this file | |

## The pipeline — what runs, in what order, with which interpreter

`rebuild_all.sh` is the single entry point and the authoritative order. A fresh
agent runs it FIRST. `$S` = `skills/kicad-pcb/scripts` (resolved repo-relative,
`~/.claude/skills/` fallback). Schematic authoring is upstream in
`03_tscircuit/` (see its contract); this stage begins at the netlist.

| Step | Command | Interpreter |
|---|---|---|
| 0a | `$S/module_first_check.py .` — P-MOD before generation spend: module by default; a bare complex IC requires an evidenced exception ADR | any python3 |
| 0 | `$S/tsx_preflight.py .` — S-COUNT PRE-gate: alphanumeric pads mapped in `03_tscircuit/parity_padmap.txt` BEFORE the first tsci build (tscircuit DROPS an unmapped part silently, ERC still 0) | any python3 |
| 0b | `$S/build_provenance.py stamp . --board "$BOARD" --tsx "$TSX"` — canon **M-FRESH**, BEFORE the build, so the run's witness is not written BY the build (canon M1). Refuses on the spot (`F-KNOB`) if the driver's `BOARD=`/`TSX=` are still the TEMPLATE knobs or do not resolve in this project: pluto-rx2-8way-v2 carried `BOARD=power3s` from commission through four commits, so its full driver had NEVER RUN while its stage gates reported green one at a time | any python3 |
| 0e | `$S/policy_audit.py . --skip-drc --phase source` — **P-LAYOUT/P-PREC before generation**: grade source-owned layout guidance and the tiered precedent ladder before TSX and before any parts-digest-bound human review. The placement phase repeats these two rows and adds realized P-ADJ geometry. | any python3 + pcbnew |
| 1 | `03_tscircuit` → netlist (tsci build → `$S/circuit_json_to_kicad_sch.py` → `kicad-cli sch export netlist`) | bun/tsci + `/usr/bin/python3` |
| 1d | `$S/circuit_json_diagnostics.py 03_tscircuit/build/circuit.json` — **TSX-DIAG**: `tsci build` can exit zero while embedding hard error records in its output. Fail on `*_error`; report but do not gate on `*_warning`. This runs immediately after the producer copy, before freshness/parity can certify a complete-looking but internally rejected artifact. | any python3 |
| 1r | THE HUMAN SCHEMATIC, DELETED THEN REGENERATED: `rm -f 03_tscircuit/build/schematic.svg 03_tscircuit/build/schematic.pdf`, then `render_schematic_pdf.mjs` consumes the exact `build/circuit.json` already produced at [1]. It fits every declared schematic sheet independently, adds a page/hash header, merges the pages, and retains single-sheet legacy support; it does **not** re-evaluate TSX. The `rm -f` is the load-bearing line. `07_releases/contracts.md` ships this PDF as `pdf/schematic.pdf` and `tsci build` never writes it, so before this stage it was whatever the last `gen_tscircuit.sh` run left — MEASURED on pluto-rx2-8way-v2 2026-07-30 at **14:47:14 beside an 18:42:05 `circuit.json`**, i.e. a release could ship a schematic that does not match its own netlist with every gate green. Rendering into a path that still holds the previous revision cannot fail safely, so the renderer carries `|| true` ON PURPOSE: failure becomes ABSENCE and [1a] names it (`F-RENDER`), instead of `set -e` aborting with no finding or a stale PDF surviving | Node + installed tscircuit renderer + `rsvg-convert` + `pdfunite` |
| 1a | `$S/build_provenance.py verify . --board "$BOARD" --tsx "$TSX" --artifact 03_tscircuit/build/circuit.json` — canon **M-FRESH**, between the build and the converter: the pipeline ASSERTS the artifact it is about to grade is the one it just built. `tsci build` writes `03_tscircuit/dist/src/<TSX>/circuit.json` and NOTHING ELSE; the bridge home is `03_tscircuit/build/circuit.json`, so the driver's `cp` is what connects them and its absence is the 2026-07-30 defect (nine gates green on superseded content). The checker GLOBS `dist/` for the producer itself and compares sha256, so a `touch` cannot forge freshness (`F-PATH`); it also requires the producer to post-date [0b] and the tscircuit sources to be unmoved since (`F-STALE`), and a build that wrote nothing is `F-VOID`. **`--render 03_tscircuit/build/schematic.pdf` extends the same gate to the HUMAN schematic** ([1r] above): it must EXIST and post-date both the stamp and the `circuit.json` it depicts, or `F-RENDER`. That half is a TIME ORDERING and not a hash — the render has no second copy to compare against — so `touch` defeats it; the hole is DECLARED in the gate's `VACUITY:` block with a fixture (canon G-VACUOUS) and bounded by [1r]'s delete plus the `render_sha256` that `audit` re-checks. Omitting `--render` PRINTS `human schematic: NOT GRADED ... not a pass` (canon M-COVER). Aborts with `GATE FAILED [1a] M-FRESH` | any python3 |
| 1b | CHEAP SEMANTIC BATTERY immediately after netlist export: `$S/early_design_check.py .` first (D-SPEC/E-PATH/E-SWDRV/E-SURGE plus adopted E-CAP/E-FAULT), then net-label survival, electrical invariants/ADR coverage, power topology/margin/off-control, count parity, and circuit-vs-parts BOM source. Upstream red stops the pipeline before schematic review or layout. | any python3 |
| 2 | ERC gate = **0 ERRORS**, warnings baselined with reasons (canon S1/S4). **TWO RUNS, and the split is the canon's, not a softening**: `kicad-cli sch erc --severity-all -o 06_build/erc.rpt` records the full-severity BASELINE and does NOT gate (without `--exit-code-violations` it exits 0 whatever it finds), then `kicad-cli sch erc --severity-error --exit-code-violations -o 06_build/erc_errors.rpt` is the BLOCKING run. `--severity-all --exit-code-violations` on ONE line gates on WARNINGS — MEASURED 2026-07-30 on pluto-rx2-8way-v2: exit 5 at **220 cosmetic findings (131 `endpoint_off_grid` + 89 `lib_symbol_issues`, both tscircuit→KiCad converter artifacts) with 0 errors**, i.e. the board failed its own driver on nothing electrical. A gate a board cannot pass gets edited per-board, and that is how the ERC bar becomes whatever each board could make pass. Both properties are pinned by `tests/t1_rebuild_templates.py` (`erc_gate_ok`): no blocking run may carry `--severity-all`, AND the full-severity report may not be dropped — "baselined" needs a written baseline. Plus the netlist-parity gate | `kicad-cli` |
| 2c | `$S/stage_checkpoint.py record . schematic ...` pins the exact Circuit JSON, delivered PDF, converter schematic, exported netlist, author manifest, build-provenance record and driver bytes at the human-review pause. On continuation, `build_provenance.py audit .` plus `$S/stage_checkpoint.py verify . schematic` run before review consumption. Any changed/missing byte requires the full arm; the resume arm contains no TSX invocation. Properties and known-bads live in `tests/t1_stage_checkpoint.py` and `tests/t1_rebuild_templates.py`. | any python3 |
| 2a | `$S/pre_route_review_check.py . --phase schematic` — **PR-REVIEW**: before placement/routing spend, two independent reviews must say `SOUND`: topology binds the exact normalized exported-netlist SHA, aggregate `02_parts` SHA and adopted-rule SHA; schematic render additionally binds the exact delivered `schematic.pdf` SHA. Missing, defective or stale evidence stops. A separate first-picture review of the functional skeleton occurs before detailed sourcing; this exact-artifact repetition is the freeze gate. | any python3 + human/fresh-context review |
| 3 | `$S/generate_board_generic.py 03_src/floorplan.yaml -o 04_kicad/<board>.kicad_pcb` (placement + zones) | `/usr/bin/python3` |
| 3a | `$S/pin_map_check.py . --board 04_kicad/<board>.kicad_pcb --circuit-json 03_tscircuit/build/circuit.json` — canon **P-PINMAP**, immediately after the first board exists and before any placement/routing work: every dossier physical pin identity must reach both the generated schematic and the real footprint; any intentional fused-land collapse is explicit and evidenced. This is the earliest machine gate for the consistently-wrong-together pin-map class; fresh-context datasheet review remains independent authority | `/usr/bin/python3` |
| 4 | Guarded board-specific audit, then `$S/placement_gates.py` (P-OUT/P-CAP/P-BODYCLR), `$S/pad_separation.py`, `$S/critical_route_check.py .` (R-PAIRMAP config completeness), and placement-phase policy audit. All block before rule generation or routing. | `/usr/bin/python3` |
| 4c2 | Generate adopted rules, run fresh refill/schematic-parity JSON DRC, then `$S/placement_drc_check.py REPORT.json` — **P-DRC**: unrouted ratsnest and `isolated_copper` preliminary islands may remain; shorts, clearance/hole/library defects and parity findings may not reach human review. The island allowance is fixed in the checker, not caller-configurable. | `kicad-cli` + any python3 |
| 5 | `$S/generate_rules_generic.py .` — netclasses BEFORE route-prep (canon R1) | any python3 |
| 5b | `$S/tier_preflight.py .` — canon R-PREFLIGHT: every routing/stitch/rescue parameter with a DRC-floor twin proven consistent with the declared fab tier BEFORE any KRT cycle; `route` refuses on FAIL by itself, but the template replays a promoted chain via `import`, so the rebuild runs the gate explicitly | any python3 (no pcbnew) |
| 6 | `$S/route_and_stitch_generic.py prep 03_src/route.yaml` (netclass-carrying, track-free route input) | `/usr/bin/python3` |
| 6b | `$S/pre_route_review_check.py . --phase placement --board 04_kicad/<board>.kicad_pcb` — **P-ROUTEBASE + PR-REVIEW**: first prove an existing promoted route derives from this exact prepared r0 (placement, source/prepared vias and prepared segments), then require independent pin/layout/render reviews plus same-camera A-RENDER bound to the exact track-free board and adopted design-rule SHA before route import. | `/usr/bin/python3` + human/fresh-context review |
| 7 | `$S/route_and_stitch_generic.py import 03_src/route.yaml` (replay the promoted `route/` chain — canon M3) | `/usr/bin/python3` |
| 7b | `$S/route_and_stitch_generic.py taps 03_src/route.yaml` — only if `taps:` configured (no-op otherwise); pour-fed sense pins / boxed-in pads, before the pours fill | `/usr/bin/python3` |
| 7c | `$S/route_and_stitch_generic.py quick 03_src/route.yaml` — the LOOP tool, not a gate: seconds-fast ratsnest-unconnected + copper clearance/track_width verdict on the post-import pre-stitch board (JSON to `06_build/route/quick.json`). Iterate routing against THIS, not against step 10 (~seconds vs ~8-10 min/cycle measured on a 112-part board) | `/usr/bin/python3` |
| 8 | `$S/route_and_stitch_generic.py stitch 03_src/route.yaml` (pours + thermal vias); verdict must be `gate: clean` | `/usr/bin/python3` |
| 8a | `$S/critical_route_check.py . --board 04_kicad/<board>.kicad_pcb --require-connected` — R-CRITESC verifies every declared critical P/N net is physically joined, routed on allowed layers, and obeys its via policy on the realized board | `/usr/bin/python3` |
| 9 | `$S/generate_rules_generic.py .` — ALWAYS LAST (see the SAVE-DROPS list below). It rewrites the `.kicad_dru` wholesale and PRESERVES rules it does not own (stitch's `pad_rescue_stubs` sub-floor), but **preservation is no longer one-way**: each run re-derives whether a preserved rule's subject still exists on the saved board and RETIRES one that matches zero items, naming it and the count on stdout. A rule that comes back is a rule whose owning pass must re-run (step 8's `pad_rescue.stub_scope`) — not a rule to hand-edit back in. Needs the `04_kicad/<board>.kicad_pcb` to be present; with no board it preserves everything unretired and says so | any python3 |
| 9a | `$S/rules_audit.py` then `$S/via_ampacity_check.py BOARD 03_src/route.yaml` — A-CLASS/A-AGREE/A-AMP and **A-VIA** grade the exact saved board before DRC. A-VIA counts only named tight series boundaries, requires a cited finished-hole capacity basis, and gives fill material no electrical credit; same-net vias elsewhere are not proof that current crosses the declared boundary. | `/usr/bin/python3` |

**WHAT A pcbnew SAVE DROPS — the list, not the instance (canon M-WIDTH).**
This rule used to read "pcbnew saves clobber netclasses", written at the width
of the one incident that taught it. The LAW is that *a pcbnew save drops state
that is not in the source*, and every member must be re-asserted or re-verified
AFTER the last save. Known members:

| dropped | re-asserted by | the incident |
|---|---|---|
| `.kicad_pro` netclasses | `generate_rules_generic.py` runs LAST (step 9) | a board-writing step after the rules generator left DRC measuring a board whose rules were gone, and passing |
| **zone FILL** | `verify_saved_fill()` after `board.Save()` in `route_and_stitch_generic.py`; `fab_payload_census.py` F-POUR at export | **usb-hub-3s-v3 v1.6/v1.7/v1.8 — 51 zones, 0 `filled_polygon`, 0 G36 regions on all four copper layers, 44287.91 mm2 of missing copper across THREE sealed releases.** Invisible because `kicad-cli pcb drc --refill-zones` REFILLS IN MEMORY and returns 0/0/0 on a board whose saved file has no fill |

Adding a member here is the fix; writing a second bespoke check for it is not.
The read-back reopens the saved file AS TEXT, never through pcbnew — pcbnew is
the tool whose save behaviour is under test (canon M1).
| 10 | DRC gate `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` = 0/0/0 | `kicad-cli` |
| 10b | `$S/grind_driver.py .` — the BOUNDED mechanical grind loop when step 10 is dirty: classifies findings, auto-applies only the conservatively-safe generator reruns per `references/grind_fixes.yaml`, escalates real work into `06_build/grind_escalation.md` (exit 2/3/4 — table/novel/D-BACK), journals each cycle (M9). It cannot loop forever; a nonzero exit summons the designer ONCE with counts + samples | `/usr/bin/python3` |
| 10c | `$S/trace_audit.py --subject .` — canon **GG-SHADOW** / **GG-RESOLVE**, the OBSERVATION arm of M-COVER. Every gate above prints `N/M`; this one runs a DERIVED battery of them under `skills/kicad-pcb/gradelib/` and grades what they ACTUALLY OPENED. **GG-SHADOW**: a same-basename file under this root that nothing in the run opened — on an ADR-0007 two-board project every flat `03_src/rules/<name>` gate grades ONE board and reports on the PROJECT. **"NOTHING IN THE RUN" IS A FLEET UNION OVER EVERY TRACE, AND A TRACER WRITES ONE TRACE PER PROCESS**, so a gate that dispatches a worker SUBPROCESS per board is graded on what its CHILDREN read too. This was measured wrong once and it matters HERE more than anywhere: the per-board path resolution this contract's own ADR-0007 note asks for is naturally built as a dispatcher — `03_src/rebuild_all.sh` already is one — and with a per-trace read-set the fix for the defect GG-SHADOW finds would have MADE GG-SHADOW FIRE, on a correctly-fixed board. Scoped to hand-written source (`03_src`/`02_parts`/`03_tscircuit`/`01_docs`) and within that to machine-readable config plus the shell drivers (`.yaml`/`.json`/`.csv`/`.net`/`.sh`/`.kicad_*`/`.tsx`) — never PROSE, because `01_docs/journal/<t>.md` beside `01_docs/learnings/<t>.md` is the layout this template SHIPS. **GG-RESOLVE**: a path the gate LOOKED AT — opened *or statted*, and the stat half is the whole point since a gate guards with `is_file()` and issues no `open` — that does not exist while that basename does, and only when the gate looked at EXACTLY ONE path of that name: one look is a SELECTION, several is an enumeration and is silent. **IT DOES NOT WRITE INTO THIS PROJECT**: the battery runs against a `cp -a --reflink=auto` copy, symlinks preserved, placed at `<tmp>/repo/projects/<name>` with every other top-level repo entry SYMLINKED beside it so a repo-relative walk-up still resolves; `--in-place` opts out and the two modes are MEASURED identical. **THE READ COUNT IS A SUPERSET, NOT A PROOF OF OBSERVATION** — it counts ANY PRE-EXISTING FILE ANY GATE HAPPENS TO OPEN, because neither the write-set (a METHOD test) nor the pre-run snapshot (an EXISTENCE test) is an IDENTITY test. A battery gate's own output is the WORST case and not the boundary: MEASURED, three lines of PROSE in `01_docs/BRIEF.md`, which is nobody's output and is graded by nothing, lift a genuinely-blind board from RAW EXIT 3 to RAW EXIT 0 exactly as `06_build/policy_audit.md` does. The caveat is printed on the same line and carried in the sidecar as `read_count_proves_observation: false`, and only the ZERO carries a verdict. Exit codes are a VOCABULARY: **2** the gate never started (`--subject` is mandatory — there is no repo-level predicate), **3** GRADED NOTHING (never a pass), **4** a path did not resolve, **5** UNOBSERVABLE — the canary went silent OR a trace hit the `GRADELIB_MAX_EVENTS` cap, and a truncated read-set carries NO verdict because "nothing opened this file" is the one claim a prefix cannot support; `--explain` prints the legend. ADVISORY at this stage — it REPORTS by name and does not abort the driver — because a day-one fleet mandate lands as red rows on every board and is disabled within the week | any python3 |

**External prerequisites** (nothing else):
- KiCad ≥ 10 (`kicad-cli`, `/usr/bin/python3` with `pcbnew` importable)
- the `skills/kicad-pcb/scripts` toolkit (the shared generics) + bun/`tsci`
- KiCadRoutingTools ONLY to re-route from scratch; the committed `route/` chain
  already contains the routing, so the standard rebuild replays it via `import`

## Forbidden

- **A per-board `generate_board.py` / `route_prep.py` / `route_waves.sh` /
  `stitch_and_fill.py` / `generate_rules.py`.** These are the RETIRED bespoke
  generators; the shared generics replace them (`generate_rules_generic.py` is
  the shared rules emitter — do not hand-copy it back in). If the generic backend genuinely cannot express
  something, that is a backend gap (a hooks entry-point candidate) — report it,
  do not hand-write a parallel backend. Every 03_src/generate_board.py was 290–780
  lines the product exists to delete.
- **One-off experiment scripts.** If it ran once and will not run again, it
  belongs in git history, not `03_src/`. Every script here must be runnable
  TODAY against the current board and produce the current result.
- Writing to `07_releases/`. Generators may write `04_kicad/` and `06_build/` only.
- Board data hardcoded where it duplicates `02_parts/` or `rules/`.

## The hard rules for generators (SHARED and per-board alike)

1. **A missing footprint / missing FPID is a HARD ERROR, never a warning.** A
   silent `SKIP U9` shipped a board without its USB ESD array; every
   board-internal gate passed because none compares the board to the schematic.
   The shared `generate_board_generic.py` already raises — never re-introduce a
   soft skip in a per-board script.
2. **A parse that yields zero results is an ERROR.** The netlist format changed
   between KiCad 7 and 10; a same-line regex silently matched nothing. Guard
   every parse with a count assertion.
3. **Never clobber `.kicad_pro` wholesale.** It holds the DRC floors and
   severity policy. `generate_rules.py` merges; it does not rewrite.
4. **Pin numbers are PHYSICAL PADS, from `02_parts/<MPN>/part.yaml`** — not a
   symbol's logical order, not memory. Cite the part file.
5. **Polarity is a fact, not a convention to guess.** KiCad footprints put the
   cathode on pad 1; a generic `1`/`2` symbol lets the author wire it backwards
   and NO electrical check can see it (the netlist is self-consistent either
   way). Three reversed parts shipped this way on one board, including the
   battery connector. `floorplan.yaml` orientation asserts + `audit_board.py`
   check pad 1's net against `part.yaml`.

## Validate — runnable by a fresh agent with zero context

1. `bash 03_src/rebuild_all.sh` completes and the DRC gate's final counts are
   `violations: 0`, `unconnected: 0`, `parity: 0` — this exercises the shared
   generics + the per-board config end-to-end.
2. after the rebuild, `04_kicad/*.kicad_dru` is byte-identical to the committed
   version (fully deterministic). The `.kicad_sch`/`.kicad_pcb` are NOT
   byte-stable (fresh UUIDs, KRT is stochastic) — for those the invariant is the
   GATE result, not the bytes; commit the regenerated files.
3. `03_src/` contains NO retired bespoke generator (`generate_board.py`,
   `route_prep.py`, `route_waves.sh`, `stitch_and_fill.py`) — grep confirms.
4. every remaining `*.py`/`*.sh` in `03_src/` is either in the Allowed table
   above or invoked by `rebuild_all.sh` (`grep <name> 03_src/rebuild_all.sh`).
5. no script writes to `07_releases/`.
6. `.kicad_dru`/`.kicad_pro` netclasses match what `generate_rules_generic.py`
   emits from `rules/nets.yaml` (regenerate and diff — drift means a hand-edited
   generated file).

## Repair

- Retired bespoke generator present → delete it; the shared generic replaces it.
  If it did something the generic can't, file the backend gap first.
- Stale experiment script → delete it; git history keeps it.
- Per-board generator with a soft skip → convert to `raise`.
- Hand-edited `.kicad_dru` → port to `rules/nets.yaml` and regenerate.

## Compliance audit (design-policies.md IDs)

This folder answers: **S1/S4** (ERC gate at severity-all = 0 errors; no_connect
flags for sanctioned floats emitted upstream), **S2** (no auto-named nets reach
copper), **R1** (netclasses exist in the route-INPUT project file — R-RULES
inspects it), **E-INV/E-ADR** (the netlist graded against the intent assertions
in `rules/electrical_invariants.yaml`; every protection/topology ADR must emit
>= 1), canon **S-NETMERGE** (`net_label_survival.py`: every schematic
global_label survives to the exported netlist + the optional `label_survival:`
pin_map — the geometric net-merge class every self-consistent gate is blind
to), **E-TOPO/E-MARGIN/E-OFF** (all from `rules/power_tree.yaml`: converter
topology DERIVED from the voltage envelopes and asserted against the converter
`part.yaml` `type:`; the output-setpoint load margin vs the delivery IR drop at
Imax; and a battery source's de-energization path + stored quiescent draw),
**M3** (everything regenerable: the promoted route chain lives in
`03_src/route/` and is committed; `06_build` stays disposable), **M4**
(waivers/adjudications in `rules/` each carry measurement evidence).

- Audit: `policy_audit.py <project>` runs S-ERC, S-NC, S-NET, R-RULES, M-REPRO,
  M-WAIV directly, plus E-INV, E-ADR, E-TOPO, E-MARGIN, E-OFF via the intent checkers
  `electrical_invariants.py` / `power_topology.py` it drives. Zero FAIL required
  at release.
- Waivers live in `rules/policy_waivers.yaml`:
  `{id: <CHECK-ID>, refs: [...], derived_from: <project?>, why: "<measurement
  evidence>"}` — an entry without evidence is itself a FAIL, and an inherited
  rationale without `derived_from` is a `waiver_provenance` FAIL (W-COPY/W-FOREIGN).
- **WAIVERS ARE PER BOARD, AND BOTH LAYOUTS ARE READ.** A single-board project
  keeps `03_src/rules/policy_waivers.yaml`; a MULTI-BOARD project (ADR-0007)
  keeps one per board at `03_src/<board>/rules/policy_waivers.yaml`, because two
  boards fab, version and WAIVE independently. `waiver_provenance.py`
  ENUMERATES both addresses and labels every finding `<project>/<board> [<id>]`
  — it does not select, so it cannot select wrongly.
- **NEVER BRIDGE THE TWO LAYOUTS WITH A SYMLINK AT THE FLAT ADDRESS.** A
  symlink there is a board selector wearing a project-wide name: it makes one
  board grade by accident, makes the other ungradeable, and makes the wrong
  answer look like the right one. MEASURED on smc0985-cooksense 2026-07-30,
  `03_src/rules/` holds **five** of them — `assembly.yaml`,
  `electrical_invariants.yaml`, `nets.yaml`, `policy_waivers.yaml`,
  `power_tree.yaml`, every one pointing into `../cooksense/rules/`. Consequences
  measured on that tree: `waiver_provenance` graded cooksense's 12 waivers and
  the interposer's 4 not at all while printing `PASS ... 12/25`; and
  `export_jlc_package.py` — a WRITER — walks up to the project root and applies
  **cooksense's** `not_assembled:`/`on_bom:` to whatever board it exports.
  Gates that resolve per board (`waiver_provenance`, `tier_preflight`) now NAME
  the owning board when they meet such a symlink, but naming it is a warning,
  not a repair.
- **A gate that must select ONE board REFUSES rather than guesses.**
  `tier_preflight.py` takes `--board`; given two boards and no name it reports
  `GRADED NOTHING about the routing config` and exits 1, the same rule
  `release_index.py` applies to releases. It also resolves the fab tier from
  the SAME `nets.yaml` it grades: resolving it independently at the flat
  address made a multi-board project report `no fab_tier declared … (legacy
  board)` and exit 0, i.e. the gate disarmed itself (MEASURED 2026-07-30).
  Note the failure direction — with no route config the old code set
  `cfg = {}` and graded CODE DEFAULTS, emitting `PF-ROUTE-CLR` about
  `route.common.clearance` in a file that does not exist. **A gate grading
  invented defaults is the same M-COVER defect as one grading nothing, in the
  other colour, and it costs more: it sends an agent to fix a value that is not
  there.**
- **OWED, named rather than silently carried:** `policy_audit.py` still reads
  ~13 flat `03_src/...` addresses and its `--board` reorders only the
  `04_kicad` globs, so on a multi-board project it grades one board's copper
  against another's rules and waivers. `export_jlc_package.py` takes no
  `--assembly`/`--board` at all. `fleet_regrade.py` invokes
  `assembly_coverage.py` / `fab_payload_census.py` with the release dir only,
  so their `--assembly` flags go unused and every per-board release is regraded
  against the flat file.
- **A ZERO DENOMINATOR IS A DISTINCT OUTCOME WITH A DISTINCT EXIT CODE.**
  `waiver_provenance.py` exits `0` clean / `1` findings / `2` INVOCATION error
  (bad root, unknown `--project`) / `3` GRADED NOTHING, and the `3` verdict
  prints what it looked for, where, and that the denominator is zero. Collapsing
  graded-nothing onto the finding code is what made this gate's own blindness
  read as a usage error for months (canon M-COVER; pinned by
  `tests/t4_regressions.py`
  `t_graded_nothing_is_distinguishable_from_an_invocation_error`).

## Every schema key here NAMES THE GATE THAT READS IT — canon G-ORPHAN

**`schema_reader_audit.py --root REPO`** (`--families` prints the denominator).
A DECLARED FIELD THAT NOTHING READS IS WORSE THAN AN ABSENT ONE, because it reads
as covered: `02_parts` `layout.adjacency:` sat in source looking live while
P-ADJ read `keep_short` only, so pluto-rx2-8way's 2.0 mm `U_ESD`-to-`J_USB`
requirement — where 6 nH per 10 mm turns a 17 V clamp into 305 V — was graded by
no gate at all and a human hand-measured it. So the tables below are the ONE
home of "who reads this key", the gate proves each claim out of the named
reader's AST on every run, and a key that appears in a board's source with no row
is an ORPHAN and FAILS. `ADVISORY` (nobody reads it, and that is correct) and
`OWED` (a gate is intended and absent) are DECLARED states and both REQUIRE a
reason — canon M4 wants evidence, not silence.

What the proof can and cannot do is stated in `schema_reader_audit.py`'s
docstring and matters when reading these tables: it proves the key name is used
to REACH a value in the named reader (subscript, `.get`, `==`/`in`, a literal
key table, a dotted-path accessor, a registry/decorator key), NOT that the read
is off this structure or that the value reaches a verdict. A MENTION — a
docstring, a message, a plain assignment — is refused, because crediting a
word's presence is exactly what made R-LEN pass on a comment about creepage.

The `rules/` schemas are declared in `rules/contracts.md`; `02_parts/*/part.yaml`
in the `02_parts` contract. These two are this folder's own.

### keys: 03_src/floorplan.yaml

| key | reader | why |
|---|---|---|
| `project.name` | `generate_board_generic.py` | board/file naming |
| `project.netlist` | `generate_board_generic.py` | the netlist to realise |
| `project.output` | `generate_board_generic.py` | where the board is written |
| `project.parts_dir` | `generate_board_generic.py` | dossier root |
| `project.fp_lib_table` | `generate_board_generic.py` | footprint library table |
| `board.outline.x0` | `generate_board_generic.py` | Edge.Cuts |
| `board.outline.x1` | `generate_board_generic.py` | Edge.Cuts |
| `board.outline.y0` | `generate_board_generic.py` | Edge.Cuts |
| `board.outline.y1` | `generate_board_generic.py` | Edge.Cuts |
| `board.edge_width` | `generate_board_generic.py` | Edge.Cuts stroke |
| `board.layers` | `generate_board_generic.py` | copper layer count |
| `board.via_protection.capping` | `generate_board_generic.py` | board-default KiCad capping token inherited by `From rules` vias; boolean yes/no. Prefer selective item-level protection for via-in-pad. |
| `board.via_protection.filling` | `generate_board_generic.py` | board-default KiCad filling token inherited by `From rules` vias; boolean yes/no. Prefer selective item-level protection for via-in-pad. |
| `board.mounting_holes.at` | `generate_board_generic.py` | NPTH placement |
| `board.mounting_holes.footprint` | `generate_board_generic.py` | NPTH FPID |
| `board.mounting_holes.refdes_prefix` | `generate_board_generic.py` | NPTH refdes |
| `board.fiducials.at` | `generate_board_generic.py` | fiducial placement |
| `board.fiducials.footprint` | `generate_board_generic.py` | fiducial FPID |
| `board.fiducials.refdes_prefix` | `generate_board_generic.py` | fiducial reference prefix |
| `board.stackup` | `generate_board_generic.py` | enables physical KiCad stackup emission and validation |
| `board.stackup.nominal_thickness_mm` | `generate_board_generic.py` | board-thickness setting and physical stackup sum target |
| `board.stackup.thickness_tolerance_mm` | `generate_board_generic.py` | allowed difference between nominal and summed physical thickness |
| `board.stackup.copper_finish` | `generate_board_generic.py` | emitted KiCad stackup copper finish |
| `board.stackup.dielectric_constraints` | `generate_board_generic.py` | emitted KiCad dielectric-constraints flag |
| `board.stackup.mask_thickness_mm` | `generate_board_generic.py` | top and bottom solder-mask thickness |
| `board.stackup.copper_thickness_mm` | `generate_board_generic.py` | per-copper-layer thickness list, length-checked against the copper-layer count |
| `board.stackup.dielectrics` | `generate_board_generic.py` | dielectric-layer list, length-checked against the copper-layer count |
| `board.stackup.dielectrics[].type` | `generate_board_generic.py` | validated prepreg/core dielectric type |
| `board.stackup.dielectrics[].thickness_mm` | `generate_board_generic.py` | positive dielectric thickness and physical stackup sum term |
| `board.stackup.dielectrics[].material` | `generate_board_generic.py` | emitted dielectric material |
| `board.stackup.dielectrics[].epsilon_r` | `generate_board_generic.py` | validated and emitted dielectric relative permittivity |
| `board.stackup.dielectrics[].loss_tangent` | `generate_board_generic.py` | validated and emitted dielectric loss tangent |
| `design_rules.*` | `generate_board_generic.py` | pcbnew design-settings floors, applied through the `DS_KEYS` literal table; an explicit value below the fab tier is a generation error |
| `thermal_vias.*` | `generate_board_generic.py` | fabrication-via fields and legacy heatsink-pad promotion; refs, owning pads, non-empty coordinates, size/drill geometry and optional item-level capping/filling are validated before true board vias are emitted |
| `taps.connections[].via` | `route_and_stitch_generic.py` | optional per-tap via geometry (`size`, `drill`, `hole_to_copper`, `exact`) and item-level capping/filling; exact placement is restricted to deterministic plane drops |
| `taps.connections[].via_protection` | `route_and_stitch_generic.py` | optional item-level capping/filling selection for the tap via; forbidden on unsupported escape taps and emitted onto the exact board via |
| `libraries[].lib` | `generate_board_generic.py` | fp-lib-table nickname |
| `libraries[].path` | `generate_board_generic.py` | fp-lib-table path |
| `placement.anchors.<REF>` | `generate_board_generic.py` | fixed placement |
| `placement.post_anchors.<REF>` | `generate_board_generic.py` | reviewed local placement applied after legalization, preserving every other floater's deterministic routed position; P-COLLIDE runs afterward |
| `placement.seeds.<REF>` | `generate_board_generic.py` | legalizer start point |
| `placement.regions.<NAME>` | `generate_board_generic.py` | named placement region |
| `placement.require_anchor` | `generate_board_generic.py` | refuse an unanchored part |
| `placement.legalize.enable` | `generate_board_generic.py` | legalizer on/off |
| `placement.legalize.clearance` | `generate_board_generic.py` | legalizer spacing |
| `placement.legalize.edge_margin` | `generate_board_generic.py` | legalizer edge keepout |
| `placement.legalize.hole_keepout` | `generate_board_generic.py` | legalizer hole keepout |
| `placement.legalize.ring_max` | `generate_board_generic.py` | legalizer search ring |
| `placement.patterns[].match` | `generate_board_generic.py` | refdes selector |
| `placement.patterns[].near` | `generate_board_generic.py` | proximity target |
| `placement.patterns[].region` | `generate_board_generic.py` | named-region placement target |
| `placement.patterns[].attrs` | `generate_board_generic.py` | footprint attributes |
| `placement.patterns[].clear_attrs` | `generate_board_generic.py` | attribute removal |
| `placement.patterns[].pad_overrides[].on_net` | `generate_board_generic.py, net_reference_audit.py` | pad-override selector (E-NETREF K10) |
| `placement.patterns[].pad_overrides[].pads` | `generate_board_generic.py` | pad selector |
| `placement.patterns[].pad_overrides[].clearance` | `generate_board_generic.py` | per-pad clearance |
| `placement.patterns[].pad_overrides[].zone_connection` | `generate_board_generic.py` | pad zone connection |
| `placement.pin` | `generate_board_generic.py` | glob allowlist selecting anchored references that the legalizer must not move |
| `placement.escape_corridors` | OWED | mis-nested declaration: `generate_board_generic.py` reads top-level `escape_corridors`, so this placement child currently emits no corridor and must be migrated or explicitly supported |
| `placement.escape_corridors[].ref` | OWED | child of the mis-nested corridor block; the actual `generate_board_generic.py` reader reaches only top-level `escape_corridors[].ref` |
| `placement.escape_corridors[].side` | OWED | child of the mis-nested corridor block; the actual `generate_board_generic.py` reader reaches only top-level `escape_corridors[].side` |
| `placement.escape_corridors[].depth_mm` | OWED | child of the mis-nested corridor block; the actual `generate_board_generic.py` reader reaches only top-level `escape_corridors[].depth_mm` |
| `placement.escape_corridors[].layers` | OWED | child of the mis-nested corridor block, and no corridor reader consumes a `layers` field at either nesting |
| `zones[].net` | `generate_board_generic.py, net_reference_audit.py` | copper pour net (E-NETREF K8) |
| `zones[].layers` | `generate_board_generic.py` | pour layers |
| `zones[].rect` | `generate_board_generic.py` | pour outline |
| `zones[].points` | `generate_board_generic.py` | pour polygon |
| `zones[].region` | `generate_board_generic.py` | pour outline by named region |
| `zones[].priority` | `generate_board_generic.py` | pour priority |
| `zones[].connect` | `generate_board_generic.py` | pad connection style |
| `zones[].clearance` | `generate_board_generic.py` | pour clearance |
| `zones[].min_thickness` | `generate_board_generic.py` | pour min thickness |
| `keepouts[].name` | `generate_board_generic.py` | rule-area name |
| `keepouts[].layers` | `generate_board_generic.py, placement_gates.py` | rule-area layers |
| `keepouts[].deny` | `generate_board_generic.py` | what the rule area denies |
| `keepouts[].rect` | `generate_board_generic.py` | rule-area outline |
| `keepouts[].points` | `generate_board_generic.py` | rule-area polygon |
| `escape_corridors[].ref` | `generate_board_generic.py` | P-ESC corridor owner |
| `escape_corridors[].side` | `generate_board_generic.py` | corridor side |
| `escape_corridors[].depth_mm` | `generate_board_generic.py` | corridor depth |
| `asserts.pad_net[].ref` | `generate_board_generic.py, net_reference_audit.py, policy_audit.py` | pad-net assertion (E-NETREF K9) |
| `asserts.pad_net[].pad` | `generate_board_generic.py, net_reference_audit.py, policy_audit.py` | pad-net assertion |
| `asserts.pad_net[].net` | `generate_board_generic.py, net_reference_audit.py, policy_audit.py` | pad-net assertion |
| `asserts.body_offset[].ref` | `generate_board_generic.py` | body-offset assertion |
| `asserts.body_offset[].axis` | `generate_board_generic.py` | body-offset assertion |
| `asserts.body_offset[].sign` | `generate_board_generic.py` | body-offset assertion |
| `asserts.pad_order[].ref` | `generate_board_generic.py` | pad-order assertion |
| `asserts.pad_order[].axis` | `generate_board_generic.py` | pad-order assertion |
| `asserts.pad_order[].pads` | `generate_board_generic.py` | pad-order assertion |
| `asserts.pad_beyond_edge[].ref` | `generate_board_generic.py` | edge-overhang assertion |
| `asserts.pad_beyond_edge[].pad` | `generate_board_generic.py` | edge-overhang assertion |
| `asserts.pad_beyond_edge[].edge` | `generate_board_generic.py` | edge-overhang assertion |
| `asserts.pad_beyond_edge[].offset` | `generate_board_generic.py` | edge-overhang assertion |
| `asserts.pad_beyond_edge[].tolerance` | `generate_board_generic.py` | edge-overhang assertion |
| `silk.min_text_height` | `generate_board_generic.py` | F-LEGIBLE silk floor |
| `silk.caption_nudge` | `generate_board_generic.py` | caption de-collision step |
| `silk.captions[].text` | `generate_board_generic.py, net_reference_audit.py` | silk caption (E-NETREF K11) |
| `silk.captions[].at` | `generate_board_generic.py` | caption position |
| `silk.captions[].size` | `generate_board_generic.py` | caption text height |
| `silk.captions[].rot` | `generate_board_generic.py` | caption rotation |
| `silk.captions[].nudge` | `generate_board_generic.py` | caption de-collision |
| `silk.labels[].match` | `generate_board_generic.py` | derived-label selector |
| `silk.labels[].from` | `generate_board_generic.py` | derived-label source field |
| `silk.labels[].strip` | `generate_board_generic.py` | derived-label edit |
| `silk.labels[].size` | `generate_board_generic.py` | derived-label height |
| `silk.polarity_marks[].ref` | `generate_board_generic.py` | the part the glyph belongs to; an unknown refdes is a HARD ERROR (see below) |
| `silk.polarity_marks[].pad` | `generate_board_generic.py` | which PHYSICAL pad the glyph is anchored at (default `1`); a pad the footprint does not have is a HARD ERROR |
| `silk.polarity_marks[].text` | `generate_board_generic.py` | the glyph (default `"K"`), tier-floored and de-collided like a refdes; NO CLEAR OWNED SLOT IS A HARD ERROR, never a silent drop |
| `silk.refdes.size` | `generate_board_generic.py` | refdes text height |
| `silk.refdes.min_size` | `generate_board_generic.py` | refdes floor |
| `silk.refdes.clearance` | `generate_board_generic.py` | refdes de-collision |
| `silk.refdes.fab_copy` | `generate_board_generic.py` | F.Fab duplicate |
| `silk.refdes.priority_prefixes` | `generate_board_generic.py` | de-collision priority |

**`silk.polarity_marks` IS THE SILK HALF OF `asserts.pad_net`, AND THE PAIR IS
NOT CROSS-CHECKED — say so rather than let the row read as full coverage.**
`asserts.pad_net` asserts which NET pad 1 sits on; `polarity_marks` prints WHICH
PHYSICAL PAD THAT IS, so a human at a bench can see the orientation of a 2-pad
polarized part whose reversal no electrical gate can ever see (the D1
reverse-polarity class: a generic `1`/`2` symbol on a polarized footprint is
self-consistent under DRC, ERC, parity and netlist — golden rule "generic 2-pin
symbols"). Required on any such part. No other governed key expresses it:
`silk.labels` prints a part's VALUE, and `silk.captions` takes ABSOLUTE
coordinates that do not move when the part moves — this one anchors at the
PAD's own position and rides with it.

What is graded today, and what is not:

* **GRADED, by the generator itself, hard.** An unknown `ref`, a `pad` the
  footprint does not have, and a glyph with no clear owned slot after the
  `_place_owned` de-collision search each `die()`. The mark is never silently
  dropped, which is the failure mode that would matter: a polarity glyph that
  quietly did not print is indistinguishable from a board that never asked for
  one.
* **NOT GRADED — two gaps, stated, not owed to a new check-ID.** (a) COVERAGE:
  nothing enumerates the board's polarized 2-pad parts and demands a mark for
  each, so a missing declaration is invisible. (b) AGREEMENT: nothing checks
  that the glyph and the `asserts.pad_net` row for the SAME `ref`+`pad` tell the
  same story, so silk and netlist could disagree and both be individually green.
  Both belong in `audit_template.py`'s I-series polarity check when a second
  board asks (canon M8's two-strike rule); one board is not yet evidence.

Note for a reviewer checking the rows above by hand: `ref`, `pad` and `text` are
each read in `generate_board_generic.py` for OTHER structures too
(`asserts.pad_net[].ref` at ~L951, `asserts.pad_beyond_edge[].pad` at ~L1002,
`silk.captions[].text` at ~L1582), and G-ORPHAN's proof cannot tell those reads
apart from this one (its docstring, "CANNOT PROVE (a)"). The segment that
DISCRIMINATES is `polarity_marks` itself, and it appears exactly once —
`self.silk_cfg.get("polarity_marks")`, `generate_board_generic.py` ~L1657 — off
`self.silk_cfg`, which is `cfg.get("silk")` (~L278) of THIS file. Deleting that
one call makes all three rows go UNREAD, which is how the claim was verified.

### keys: 03_src/route.yaml

Every row here is read through `route_and_stitch_generic.py`'s dotted-path
`get(cfg, "a.b.c")` accessor or its `@stitch_pass("<name>")` registry, which is
why the subtree form is used: the pass NAME is the config block name, and the
two cannot drift apart without the router failing to find its own pass.

| key | reader | why |
|---|---|---|
| `flow` | `pcb_flow.py, grind_driver.py, pre_route_review_check.py` | pipeline ownership, path, input, copper-mode, stage-budget, and exact pre-route review configuration |
| `flow.*` | `pcb_flow.py, grind_driver.py, pre_route_review_check.py` | flow subtrees consumed for ownership, inputs, blockers, budgets, copper classification, pipeline paths, and current pre-route evidence |
| `stitch.seed_stubs.*` | `route_and_stitch_generic.py` | seeded GND stubs the stitch pass places before the A* fallback; read as a stitch-pass config key |
| `taps.reattempt.*` | `route_and_stitch_generic.py` | re-attempt budget for tap insertion |
| `project.name` | `route_and_stitch_generic.py` | board naming |
| `project.board` | `route_and_stitch_generic.py` | the board to route |
| `project.build_dir` | `route_and_stitch_generic.py` | working directory |
| `prep.out` | `route_and_stitch_generic.py` | the track-free r0 written |
| `prep.pad_rescue` | `route_and_stitch_generic.py` | optional deterministic plane-pad rescue before KRT; accepts true or a scoped override mapping |
| `prep.seed_stubs` | `route_and_stitch_generic.py` | deterministic pre-route copper seeding configuration |
| `prep.seed_stubs.*` | `route_and_stitch_generic.py` | clearance, via geometry, and stub recipes passed to the deterministic seed-stub pass |
| `prep.keepouts.*` | `route_and_stitch_generic.py` | per-layer router keepouts; their PRESENCE is one of the homes `policy_audit.py` accepts for P-KEEP |
| `prep.waves.*` | `route_and_stitch_generic.py` | wave net groups + exclusions |
| `route.krt` | `route_and_stitch_generic.py` | the KRT entry point |
| `route.kicad_python` | `route_and_stitch_generic.py` | interpreter for KRT |
| `route.race` | `route_and_stitch_generic.py` | parallel candidate count |
| `route.final` | `route_and_stitch_generic.py` | the chain file promoted |
| `route.import_source` | `route_and_stitch_generic.py` | explicit build/promoted lineage selected for route import; targets must not depend on stale-file precedence |
| `route.common.*` | `route_and_stitch_generic.py` | per-run KRT geometry defaults |
| `route.preflight_critical_pairs` | `critical_route_check.py` | critical-pair inventory cross-checked for completeness against independent `nets.yaml length_match` intent before routing and on realized copper; route/prep/import/stitch entry points enforce it directly |
| `route.preflight_critical_pairs[].*` | `critical_route_check.py` | pair identity, P/N nets, routing wave, allowed layers, and via policy |
| `route.no_critical_routes` | `critical_route_check.py` | explicit evidenced applicability decision when the inventory is empty |
| `route.waves[].*` | `route_and_stitch_generic.py` | per-wave KRT overrides, validated against the netclass floors at PREP time |
| `via_ampacity.*` | `via_ampacity_check.py` | optional exact-board series-transition capacity contract: source/method/temperature, finished-hole capacity table and named tight rectangles with net, minimum via count, continuous-current requirement and physical reason |
| `stitch.passes` | `route_and_stitch_generic.py` | the pass ORDER; a list with no `fill` is refused |
| `stitch.clearance` | `route_and_stitch_generic.py` | stitch clearance |
| `stitch.keepin.*` | `route_and_stitch_generic.py` | stitch keep-in inset |
| `stitch.via.*` | `route_and_stitch_generic.py` | stitch via geometry + tiers |
| `stitch.stitch_grid.*` | `route_and_stitch_generic.py` | plane stitch grid; `x`/`y` are `[start, stop, pitch]` in mm and the PITCH MAY BE FRACTIONAL (see below) |
| `stitch.pad_rescue.*` | `route_and_stitch_generic.py` | pad-rescue pass |
| `stitch.island_rescue.*` | `route_and_stitch_generic.py` | island-rescue pass |
| `stitch.heal_islands.*` | `route_and_stitch_generic.py` | same-net pour bridge pass |
| `stitch.unify_zone_priorities.*` | `route_and_stitch_generic.py` | zone-priority pass |
| `stitch.normalize_vias.*` | `route_and_stitch_generic.py` | via normalisation pass |
| `stitch.dedupe_vias.*` | `route_and_stitch_generic.py` | via de-duplication pass |
| `stitch.drop_dangling.*` | `route_and_stitch_generic.py` | dangling-track pass |
| `stitch.drop_micro_fragments.*` | `route_and_stitch_generic.py` | micro-fragment pass |
| `stitch.prune_stitch_dangling.*` | `route_and_stitch_generic.py` | stitch-via prune pass |
| `stitch.split_t_junctions.*` | `route_and_stitch_generic.py` | T-junction split pass |
| `stitch.stub_fallback.*` | `route_and_stitch_generic.py` | stub fallback pass |
| `stitch.astar_fallback.*` | `route_and_stitch_generic.py` | A* fallback pass |
| `stitch.hole_to_hole.*` | `route_and_stitch_generic.py` | hole-to-hole pass |
| `stitch.width_floor.*` | `route_and_stitch_generic.py` | post-route width floor pass |
| `taps.clearance` | `route_and_stitch_generic.py` | power-tap clearance |
| `taps.via.*` | `route_and_stitch_generic.py` | power-tap via geometry |
| `taps.connections[].*` | `route_and_stitch_generic.py` | per-tap from/to/net/layer/width and escape options |

**`stitch.stitch_grid` `x`/`y` ARE `[start, stop, pitch]` IN MILLIMETRES, AND
THE PITCH IS A REAL NUMBER.** Until 2026-07-30 the pass stepped with
`range(int(start), int(stop), int(pitch))`, so a fractional pitch was floored
to a whole millimetre — silently, and not as a refusal but as a DIFFERENT
BOARD. On an RF board that is not a cosmetic difference: **the stitch grid IS
the ground-via fence, and the fence is the product.** MEASURED,
pluto-rx2-8way-v2: ARCHITECTURE sec 6 requires a fence flanking every arm at
`<= 1.35 mm` (the largest round value under the derived guided
`lambda_g/20 = 1.3693 mm`, ADR-0003); the only expressible pitches were 1 mm
(a via forest, ~2500 sites) or 2 mm, and the board shipped at **2.0 mm =
lambda_g/13.7** — conservative against the SOURCED free-space
`lambda/20 = 2.5 mm` at 6 GHz, and NOT meeting its own guided bound.

**WHICH lambda: THE GUIDED ONE.** A via fence sits in the substrate beside a
microstrip, so what it must sample is the wave ON THE LINE, whose wavelength
is `lambda_g = lambda_0 / sqrt(eps_eff)` — SHORTER than free space, hence a
STRICTER pitch. Free-space `lambda/20` is the looser bound and satisfying it
proves nothing about the guided one; the BULK-`eps_r` wavelength is neither
(all three have been used in this fleet — `rf-design.md` 3(b), 4A). Derive the
pitch from `lambda_g` and say so where you write it down.

A NON-POSITIVE pitch is a HARD ERROR, not a behaviour. Pre-fix, `range` with a
negative step yielded nothing and the run printed `stitch grid: 0 vias`, then
`filled 2 zones`, then `gate: clean` — a board with no return-path stitching
at all, gated green, from a config that asked for a grid. Both properties are
pinned by `tests/t2_route_stitch.py` (`t_grid_fractional_pitch`,
`t_kb_grid_nonpositive_pitch`), the fractional one as a LATTICE property
rather than a via count, because how many sites survive collision checking is
board-dependent.

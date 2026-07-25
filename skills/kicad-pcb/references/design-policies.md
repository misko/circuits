# Design policies — the canon

Every policy in this catalog has: a stable CHECK ID, the policy statement,
its governing standard, HOW it is verified (machine command, fresh-agent
grading, or documented-exception), and the incident that motivated it.
Contracts bind these IDs to stage folders; `scripts/policy_audit.py` runs
every machine-checkable ID and emits a graded report. Nothing in this file
is advisory — an ID is either enforced, human-graded per protocol, or
waived with evidence in the project's `03_src/rules/policy_waivers.yaml`
(same evidence rules as twin adjudications).

Verification legend: [M] = machine (policy_audit.py) · [H] = human/fresh
agent per review protocol · [G] = existing pipeline gate it rides on.

## Schematic — the contract of intent (IEC 60617 / IEEE 315, IPC-2612)

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| S1 | ERC clean at `--severity-all`: 0 errors; warnings baselined with reasons | [M] S-ERC | usb-power-3s shipped with 206 unexamined findings incl. 13 pin_not_connected |
| S2 | Every net deliberately named; zero auto-names (`Net-(R5-Pad2)`) on routed copper | [M] S-NET | auto-names are where swapped-net mistakes hide |
| S3 | Pin maps verified from the datasheet package FIGURE, `verified:` note cites figure+page; independent fresh-eyes re-derivation for actives | [M] S-VER (note quality) + [H] pin review | mirror-numbered LM5145: symbol+footprint+netlist consistently wrong together, every internal check passed |
| S4 | Every pin explicitly handled: `no_connect` flags EMITTED by the generator for sanctioned floats; unused gates/amps tied to defined levels; strapping pins documented | [M] S-NC | intentional floats documented only in prose = future accidental floats invisible |
| S5 | Design math lives with the design: every component value derived with margins in DETAIL_DESIGN.md | [H] audit spot-check | "why this value" must never live in someone's head |
| S6 | Story-critical paths DRAWN as wired circuits (power entry→protection→regulation; the primary signal chain). Label-blob permitted only for pullups/decouplers/bulk. Until generators emit wires, readability is a MANDATORY graded item in the render review | [H] render review | fleet audit 2026-07-17: 0 drawn wires in all four projects; reviewers must mentally re-net everything |
| S7 | Decoupling shown adjacent to the IC it serves (schematic teaches the layout) | [H] render review | cap-farm schematics hide missing pins |
| S8 | Count everything: refdes SET parity across declared intent (`03_tscircuit/manifest.yaml`) and every generated artifact (circuit.json, kicad_sch, netlist, board); alphanumeric pads mapped in `parity_padmap.txt` BEFORE the first tsci build | [M] S-COUNT (`count_parity.py` — the symmetric difference NAMES the dropped part) + [M] TSX-PRE (`tsx_preflight.py`) | 2026-07-21 clean-room run: tsci silently dropped all 4 USB connectors (48/52, ERC still 0) — every generated artifact agreed; only the author's hand count disagreed |
| S9 | Spec tensions surfaced at COMMISSION (D-SPEC): every numeric requirement tested against the governing standard and the sourceable-part envelope; each tension gets an ADR + a flagged BRIEF row — never silently built out-of-spec, never silently downgraded. Every power PORT/output pins its voltage ENVELOPE (min/max), not just current — an unpinned output voltage range is what let converter topology be interpreted instead of derived (feeds E-TOPO) | [H] BRIEF `Spec tensions` table filled ("none found" only after checking) + ADR per tension; [M] E-TOPO once `power_tree.yaml` exists | "USB-C 6A" exceeds Type-C 3A/PD 5A; "USB-A 2.5A" exceeds every stocked receptacle rating — the 2026-07-21 clean-room agent caught both by instinct (ADR-0005); instinct is not a gate. usb-hub-3s (2026-07-22): "USB-C 5A compliant" pinned the current but not the 5V-only output envelope, so a buck-boost was built where a buck sufficed |

| S10 | Label intent SURVIVES export: every schematic global_label exists as a net in the exported netlist (+ optional per-board `pin_map` pin-for-pin assertions); kicad-cli merges wires whose endpoint touches a foreign wire or that overlap collinearly, and every self-consistency gate stays green through the merge | [M] S-NETMERGE (`net_label_survival.py`; config = `label_survival:` block of `03_src/rules/electrical_invariants.yaml`, exemptions need evidence per M4) | crow-recorder-central-v2 2026-07-23: P5VA_4→AUDIO4M + MID2P→5V, two DO-NOT-ORDER defects; ERC 0, DRC 0/0, count_parity 194==194 all green — only the label-vs-netlist comparison disagreed |

## Placement — where 80% of routing quality is decided (IPC-7351)

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| P1 | Zero courtyard overlaps — courtyards are the manufacturer's margin, law | [M] P-CRT (via full-severity DRC) | J1/R1 "overlap" question answered by 0.31mm courtyard gap |
| P2 | Polarized parts machine-audited: pad-1 NET asserted against part.yaml polarity facts (diodes, electrolytics, LEDs, keyed connectors) | [M] P-POL | usb-power-3s MANIFEST claimed "polarity PASS" with no scripted check; XT60 pin1='−' class |
| P3 | Connectors earn their edges: mate direction, edge distance, screw-head keep-outs machine-checked; antenna keep-outs per module datasheet | [M] P-KEEP (project audit I2/I3/I4/I5 present + passing) | WROOM antenna over copper = dead radio |
| P4 | Every refdes PRINTS on the board: F.SilkS, visible, de-collided; F.Fab duplicate for assembly drawings; waivers evidence-backed | [M] P-SILK-REF | a board shipped with all 76 refs on F.Fab — no names on the physical board |
| P5 | Plain-word functional silk for anything a human touches: terminals, headers, polarity marks, voltage/current warnings, pin maps | [M] P-SILK-FN (label near every J*/F*/TP* ref) + [H] legibility | 12.6V battery board shipped with zero functional text |
| P6 | Zoning by placement on a shared plane; split planes only with a written ADR | [M] P-PLANE (reference layer carries only its zone) | return-path detours from casual splits |
| P7 | Escape feasibility + fab tier decided at PART SELECTION: every multi-pin part.yaml carries an `escape:` block (style, pitch, optional `escapes_worst_side`, tier_required — computed by `escape_check.py` against `references/fab_tiers.yaml`), and no used part requires a tier above the `fab_tier:` declared in `03_src/rules/nets.yaml`. v2 (2026-07-21) verdicts are an ESCAPE-BUDGET model and may be CONDITIONAL: a small dual-row QFN with a declared budget gets the cheap tier conditional on `outward-only-local` (SY8368 shipped x3 at standard — a4ff7ed), and a dense leaded side (>=6 escapes) whose pitch − drill < hole-to-hole gets it conditional on `escape-corridor` (LM5116 ADR-0008). A conditional tier is accepted ONLY when the part.yaml records the SAME `conditions:` — a conditional verdict is earned per board, never inherited by copy. Raising the tier requires the D-TIER ADR + the tier's ORDER_README line | [M] P-ESC (block present + agrees with live recomputation; declared style/pitch cross-checked against footprint text; conditional tiers require matching recorded conditions) + [M] P-TIER (tier_required rank <= declared fab_tier rank) | clean-room 3S stall 2026-07-20: SY8368 QFN-10 @ 0.5mm pitch selected with fab tier defaulted to standard; the unmade ADVANCED decision surfaced 2 stages later as `drill_out_of_range` at DRC. Calibrated both directions 2026-07-21: the SAME part shipped x3 at standard with outward-only escapes (a4ff7ed) — the v1 'fine QFN = advanced always' model was over-conservative vs a paid-for board |
| P8 | Datasheet LAYOUT-SECTION compliance decided at PART SELECTION — the THIRD datasheet read after pinout (S-VER) and package (P-ESC). Every IC + power/sense part.yaml carries a `layout:` block that (a) cites the datasheet Layout/Application section + reference design/EVM/app note (`source:`), and (b) encodes the placement rules the chip demands as `keep_short:` net-span budgets (and/or `adjacency:`/`notes:`). The floorplan HONOURS them: each declared net's pad-span stays within `max_span_mm`, or the over-span is re-placed / dispositioned in `policy_waivers.yaml` with the measured span + why. This is the datasheet's "keep the FET/sense-R/decoupling local, Kelvin-sense back to the chip" rule made mechanical — so a floorplan is adapted FROM the reference layout, never authored against it | [M] P-LAYOUT (in-scope part carries a `layout:` block with `source:` + a budget) + [M] P-ADJ (board net-spans within each `keep_short.max_span_mm`; warn+waiver) + [H] the Layout-section read itself (the independent human half) | usb-hub-3s-v2 TPS25740A, 2026-07-22: pinout (S-VER) + package (P-ESC) both PASSED, but the datasheet Layout section (TI SLVSDG8B §11 / EVM SLVUAP7A — mount the pass FET + sense R + VBUS caps HARD against the power-stage pin edge) was NEVER read. The FET row was placed 7mm north across an escape channel; four 0.5mm-QFN escapes could not coexist — a wall found only after ~8 routing rebuilds. P-ADJ catches it at placement: RSNS span 11.5mm > 5mm on that board |

| P9 | Every pad inside the BOARD OUTLINE POLYGON: post-placement, every footprint pad (courtyard in strict mode) sits inside Edge.Cuts with >=0.15mm margin — a polygon test, not a frame rectangle and not a connector-mouth check | [M] P-OUT (`placement_gates.py`; `out_ok` waivers evidence-backed) | smc0985-cooksense 2026-07-23: J_PI 2x20 laid 34/40 pins 1..43mm off the south edge; I-EDGE saw the mouth at the edge and PASSED — a 600k-iteration KRT run was the checker (~13h D-BACK) |
| P10 | Corridor crossing-demand vs capacity estimated STATICALLY at the placement gate: swept cut lines, rat's-nest demand (cross-footprint, pour/keepout-resident nets excluded) vs un-blocked width / track pitch x routable layers; FAIL above 0.5x geometric capacity (calibrated: defect 0.90 vs honest boards <=0.14; geometry over-estimates true capacity ~5x where creepage rules bind) | [M] P-CAP (`placement_gates.py`; `waive_cuts` evidence-backed) | same D-BACK: the placement journal eyeballed "~3 nets cross east" where 26 crossed a corridor carrying 6 — an 8x under-count found only by routing to exhaustion |

## Routing — physics, then aesthetics (IPC-2221/2222, IPC-2152, IPC-4761; the FAB's published capabilities override all)

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| R1 | Rules BEFORE routing: netclasses + ampacity width floors + via rules exist in the ROUTING-INPUT project file, and the rules generator runs LAST too (pcbnew saves clobber netclasses) | [M] R-RULES (inspect route-input .kicad_pro for the classes) | usb-power-3s: KRT routed against Default 0.2mm; floors only enforced post-hoc. SPF board shipped 0.15mm switch nodes pre-floors |
| R2 | Width from current (IPC-2152); power as POURS with priority over GND fill; documented trunk exceptions allowed with margin math | [M] R-POUR (power nets have zones or a waiver) | thin-pass routers have no ampacity concept |
| R3 | Return current flows directly under every signal: unbroken reference plane under sensitive regions; named-region continuity limits machine-checked | [M] R-PLANE (max signal length on reference layer inside named regions, per project config) | laser board: 16 B.Cu cuts under the comparator region vs stated "continuous GND" intent — unenforced intent drifts |
| R4 | Escape/fanout first, hardest nets first; package escape feasibility checked at fab rules before commitment (0.4mm QFN = package problem, not router problem) | [M] P7 (P-ESC/P-TIER at part selection) + [H] design review + [G] DRC | escape saturation discovered post-route is a re-spin |
| R5 | Sensitive-path discipline: diff pairs matched+coupled; timing-critical single-ended nets length-limited AS A GATE; analog inputs guarded per the IC's layout app note | [M] R-LEN (project audit length-spread checks present + passing) | comparator spread <40mm gate on the laser board |
| R6 | Thermal: EPs and power pads get via arrays to the plane (>= N vias in/near pads above area threshold on power nets); reliefs on hand-solder, solid on power | [M] R-THERM | TPS2557 EPs and DPAK tab shipped with zero in-pad vias |
| R7 | Gate: DRC 0 violations / 0 unconnected / 0 schematic-parity at `--severity-all --refill-zones` | [M] R-DRC | six parity findings slipped through a laxer severity bar |

| R8 | Tool config == declared fab tier BEFORE any KRT cycle: every routing/stitch/rescue parameter with a DRC-floor twin (clearances, via geometry, normalize fallbacks, hole-to-copper/hole-to-hole, layer coverage) is proven tier-consistent — 0 FAIL — before `route` runs. A tool DEFAULT is config: an unexamined default that disagrees with the declared tier is the same defect as an explicit wrong value, only harder to see. `route_and_stitch_generic route` refuses on FAIL; `--skip-preflight` is a loud, discouraged escape hatch | [M] R-PREFLIGHT (`tier_preflight.py PROJECT_DIR`; `--explain` prints derivations + copy-paste fixes) | crow-recorder-central-v2 2026-07-23: four unexamined defaults (generate_rules 0.2 clearance hardcode, island_rescue layer blindness, normalize 0.6/0.3 fallback, via_site_ok 0.205 hole-to-copper) = ~60% of the routing stage; archived crow-array-pod carries the defect-1 pattern latent and shipped 0/0/0 by sparse-route luck |

## Electrical — the netlist must match INTENT (the D1 class)

Every gate above proves SELF-CONSISTENCY. None proves the netlist matches what
the design DECIDED. The D1 reverse-polarity defect (usb-hub-3s v1.0, external +
red-team reviews 2026-07-21) passed ERC, DRC, netlist parity, jlc_twin AND pin
review because symbol, footprint, netlist and board were consistently WRONG
together — D1's cathode sat on VBAT_F; only the ADR's intent (D1 is the
reverse-polarity block feeding VIN) disagreed, and intent was not executable.
This class closes the loop: a protection/topology ADR emits machine-checkable
netlist assertions in `03_src/rules/electrical_invariants.yaml`, and the gate
grades them against the netlist the board actually exports. Netlist-only kinds
ship in E1 (`pin_on_net`, `series_chain`, `net_has_part`); geometric kinds
(`clamp_le_rating`, `kelvin_within`) are DEFERRED to a future E2.

E-TOPO/E-MARGIN/E-OFF are the power-tree ADEQUACY siblings: derived from
`03_src/rules/power_tree.yaml` (converter topology, output-setpoint load
margin, de-energization + stored quiescent drain), they catch design-margin
defects that the self-consistency gates — and even a perfectly self-consistent
netlist — pass silently. Both E-MARGIN and E-OFF were MISSED by two independent
zero-context red-team reviews on usb-hub-3s-v3 (2026-07-23) before this family
grew to gate them.

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| E-INV | Design intent is EXECUTABLE: `03_src/rules/electrical_invariants.yaml` lists assertions the netlist must satisfy — `pin_on_net` (a named pin is on a named net, the D1 class), `series_chain` (a topological order of parts/nets exists; 2-pad parts bridge their pads, >2-pad parts name bridging pins via `through:`), `net_has_part` (a net carries >= N parts of a type, the bridge-rail-decoupling class). Every invariant REQUIRES `adr:` (the ADR that emitted it) + `why:`. Graded by `electrical_invariants.py` against `06_build/netlists/*.net` (or `04_kicad/*.net`); a failure NAMES the assertion and the actual net found | [M] E-INV (`electrical_invariants.py PROJECT_DIR`) | D1 reverse-polarity (usb-hub-3s v1.0): cathode on VBAT_F not VIN — every artifact agreed, only intent-vs-netlist disagreed; pinned as the incident fixture in `t1_electrical_invariants.py` (reads the sealed v1.0 netlist) |
| E-ADR | The loop must CLOSE: every `01_docs/decisions/*.md` whose title/tags mark it protection\|topology\|input-protection has >= 1 invariant citing its number. A protection ADR that emits NO invariant is flaggable — that is exactly how the D1 intent never became a machine check | [M] E-ADR (`electrical_invariants.py PROJECT_DIR --adr-coverage` — title/tag keyword match; deliberately conservative to avoid false positives, documented in the checker) | the ADR-0001 input-protection decision existed but emitted no executable assertion; the reverse-polarity intent lived only in prose |
| E-TOPO | Converter TOPOLOGY is DERIVED, not interpreted: for each rail in `03_src/rules/power_tree.yaml` the required topology follows mechanically from the voltage envelopes — `Vout_max < Vin_min` ⇒ BUCK, `Vout_min > Vin_max` ⇒ BOOST, ranges overlap ⇒ BUCK_BOOST — and the selected converter's part.yaml `type:` must EQUAL it. MORE capable than needed (buck_boost where buck suffices) = over-engineering ⇒ FAIL (waiver-able only with an ADR justifying the extra capability, e.g. "future 20V PD"); LESS capable ⇒ FAIL (cannot meet Vout). The checker also prints the worst-case input-trunk current `Σ(vout_max·iout)/eff / Vin_min` and flags a trunk/fuse materially under- or (>2×) over-built | [M] E-TOPO (`power_topology.py PROJECT_DIR`; `--derive` for ad-hoc ranges) | usb-hub-3s 5V-buck-boost over-engineering (2026-07-22): an IP6559 BUCK-BOOST + 4 external FETs + 30V-FET/TVS coordination + a 16A trunk on a 5V-ONLY USB-C port where Vout(5V) < Vin_min(9V) ALWAYS — a plain buck sufficed. Root cause: D-SPEC pinned the CURRENT ("5A compliant") but never the OUTPUT VOLTAGE RANGE, and topology was interpreted, not derived. Derived input current at 5V-only (30W+25W=55W) is ~6.8A vs the board's 16A trunk |
| E-MARGIN | Output SETPOINT vs LOAD MARGIN: a regulated rail feeding a KNOWN load must clear the load's brownout with real IR headroom. A rail in `power_tree.yaml` that declares `load_uv_threshold` (the downstream load's undervoltage/brownout voltage) must have `vout_min − load_uv_threshold > 0` AND, at `iout_max_A`, leave more series-resistance budget than the delivery path burns: with a declared `ir_budget_mohm` (board+connector+cable) the headroom must exceed `ir_budget·iout·(1+margin)` (default margin 0.2); without one, the implied budget `(vout_min−UV)/iout` must clear the `ir_floor_mohm` floor (default 100mΩ — a bare realistic cable+connector+trace path). The cable/connector ASSUMPTION is judgment: the reviewer confirms `ir_budget_mohm` matches the real path. **Tolerance amendment (2026-07-23): a rail's vout window may not be author-asserted when its regulator is divider-programmed** — with a `feedback:` block (vref/divider values + tolerances, all six fields required) the corners are COMPUTED worst-case (`low = vref_min·(1+Rt_min/Rb_max)`, `high = vref_max·(1+Rt_max/Rb_min)`); a declared window NARROWER than computed is a FAIL in both E-TOPO and E-MARGIN naming both corners, and headroom is graded from the computed worst-low | [M] E-MARGIN (`power_topology.py PROJECT_DIR --margin`) + [H] the delivery-resistance assumption confirmed in the red-team topology/protection lens | usb-hub-3s-v3 (2026-07-23, external review): a rail regulated to 4.97V fed a Raspberry Pi 5 (undervoltage detect ~4.63V) at 5A — leaving only (4.97−4.63)/5A ⇒ ~68mΩ TOTAL for board+connector+cable IR drop, less than a real e-marked 5A USB-C cable + two connector pairs. BOTH zero-context red-team reviews COMPUTED the 4.97V setpoint and neither flagged the thin margin — the headroom was never made a number. Tolerance half: the same board declared 5.27–5.43 V from Vref tolerance alone; the divider tolerances put the true window at 5.227–5.479 V and no gate could object until the feedback block made the corners computed |
| E-OFF | QUIESCENT DRAIN / OFF-CONTROL: a self-contained energy source (battery/cell/pack) must have a DOCUMENTED de-energization path and a BOUNDED stored quiescent draw. When a battery source is detected (`power_tree.yaml` `source_type:`, or VBAT/BATT/PACK nets, or a battery ADR), the power tree must declare `off_control:` (the mechanism — master switch / load-switch / EN-gating; or explicitly "always-on" WITH an ADR) and `quiescent_ua:` (the stored/shutdown draw). "Always-on" is a decision that must be ADR-justified, never a silent default. Whether the declared mechanism actually EXISTS in the netlist, and whether the drain is acceptable for the pack, are judgment: folded into the mandatory input-protection ADR's required-question list (SKILL.md) and confirmed by the red-team topology lens | [M] E-OFF (`power_topology.py PROJECT_DIR --off-control` — battery detected ⇒ off_control + quiescent_ua declared; a bare "always-on"/"none" with no ADR = FAIL) + [H] the input-protection ADR + red-team lens | usb-hub-3s-v3 (2026-07-23, external review): a 3S-LiPo board tied both buck EN pins active with no master switch — the controllers idle-drain the pack the whole time it sits in storage. No review asked "how is it de-energized / does it self-drain" |

## Assembly — the deliverable is a POPULATED board (the PCBA class)

Every gate above stops at copper. The pipeline gated the BOARD like a fab and
the ASSEMBLY like a courtesy: of 32 check IDs exactly one touched a fab-order
artifact, and nothing in `skills/`, `scripts/` or `tests/` had ever read a
`cpl.csv` back. So the defects below all reached a SEALED release and were all
found by a human reading bytes — never by a gate. PCBA is the deliverable
(pcb-design/SKILL.md); these grade what the fab is actually told to place, and
with what.

**A third gate — A-ROT, every CPL rotation is MEASURED, never inherited — was
written, measured against its fixtures, and then PULLED before landing
(2026-07-25).** `jlc_twin.xform()`, the helper that computes the `jlc_offset`
a rotation gate would treat as the measurement, uses the OPPOSITE handedness to
`local_to_board()`. Verified against pcbnew itself over 72 pads on rotated
footprints: `local_to_board`'s form is exact (max error 0.000000 mm),
`xform`'s is off by up to 23.93 mm — it loses at every 90 and 270 deg part and
agrees only at 0/180, where the form is sign-invariant. Every offset the twin
reported was therefore NEGATED: invisible at 0/180, exactly 180 deg wrong at
90/270. Six rows of `jlc_lcsc_rotations.csv` — the table such a gate would rank
as AUTHORITY — had been populated from it and were all 180 deg wrong (corrected
90 -> 270, 2026-07-25). **This is canon M1 collecting twice: the "authority" was
populated FROM the checker, so every consumer inherited the same negation and
even an external review that read the table was misled by it.** A gate built on
that table would have frozen the defect and made it unfalsifiable. When A-ROT
lands it must re-derive the angle from the BOARD plus JLC's cached model with an
operator verified against pcbnew — never from `jlc_offset`, and never from a
table populated by it.

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| A-POP | The population set is DECLARED, not emergent. `{board footprints} − {CPL designators}`, computed from the BOARD and the CPL directly (never from the exporter's filter logic), must EQUAL the `not_assembled:` set in `03_src/rules/assembly.yaml`, honouring declared `exempt_prefixes:` (DECLARED, never hardcoded — a hardcoded exemption is how the refdes-on-silk waiver became an inherited defect across three boards). FAILs: a blank-LCSC BOM row whose refs are on the CPL; a declared-unpopulated ref still ON the CPL, or without `exclude_from_pos_files` on the board; a board part carrying that attribute yet placed by the shipped CPL; an entry missing `reason:`/`evidence:`/`disposition:`; a `reason:` outside the closed vocabulary; a CONSIGNED part listed as not_assembled (consigned means PLACED — a sourcing class, not a population class); and a release MANIFEST `not_assembled:` line that is absent, is free PROSE rather than a bare refdes list, or disagrees with `assembly.yaml` (it is GENERATED from that file, never hand-written twice). A prose line is reported as UNGRADEABLE and cross-checked against nothing — never scraped for refdes: usb-hub-3s-v3 v1.4's line yields 50 tokens of which 44 are English words, and its four real refdes sit in a clause asserting the OPPOSITE ("remain POPULATE-BY-DEFAULT on BOM/CPL"), so a scrape accuses exactly backwards | [M] A-POP (`assembly_coverage.py RELEASE_OR_PROJECT`; prints the per-side placement histogram) | cooksense v1.1 (sealed 2026-07-24) shipped 13 CPL placement rows whose BOM line carries a BLANK LCSC — JLC told to place 12 parts the MANIFEST declares not_assembled, and to source a 13th (J_TC) declared nowhere. The interposer v1.0 shipped the same class plus a disposition that is PROSE telling a human to delete rows before uploading. crow-recorder-central-v2 v1.3 declared its PLACED, consigned U1 "not_assembled" |
| A-STOCK | A release seals only against stock evidence that PASSES. Every coded BOM line with a CPL row is graded offline against the evidence the release SHIPS: `stock >= qty x build_quantity`, or an `assembly.yaml` `sourcing_plan:` entry carrying `measured_stock` + `measured_on`. **A MISSING OR UNPARSEABLE VERDICT IS A FAIL, NOT A SKIP** — the fleet ships three incompatible evidence formats, so a parser that shrugs at an unfamiliar shape can be silenced by choosing a shape. The gate is OFFLINE (it grades EVIDENCE); live re-query stays in the opt-in `--net` tier, because a gate that needs the network is a gate that gets skipped. `jlc_stock_check.py --json OUT` writes the one machine-readable sidecar with an EXPLICIT verdict | [M] A-STOCK (`release_freshness_check.py` check (e), always on) | five sealed releases ship stock evidence whose LAST LINE says FAIL and nothing ever read it: crow-recorder-central-v2 v1.0-v1.3 each record their own CPU (C6938291, the XU316 SoC) at `LOW_STOCK(0)`, and crow-recorder-central v1.0 six failing lines. cooksense v1.1 ships a raw `--out` CSV report as `stock_check.txt` with ZERO verdict lines at all — the gate must not be silenceable by deleting the verdict |

## Meta — worth more than all of the above

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| M1 | Checker and checked must not share a method: per failure class, at least one check from an independent reference (datasheet figure, JLC CAD, fresh agent, pixel measurement) | [H] release review confirms the battery ran | every hard catch this project made came from outside the design's own assumptions |
| M2 | Machine-check what you can — a prose rule will eventually be skipped | this file + policy_audit.py ARE the enforcement | refdes-on-silk became real only as audit gate I10 |
| M3 | Everything regenerable from source: never hand-edit 04_kicad; ALL rebuild inputs tracked in git — the final route chain file is PROMOTED to 03_src/route/ (06_build stays disposable otherwise) and its sha recorded in the MANIFEST | [M] M-REPRO | laser board's load-bearing r3.kicad_pcb was gitignored — unreproducible from a fresh clone |
| M4 | Evidence-backed exceptions: every waiver/adjudication carries the measurement that justifies it; positional deltas decomposed by mechanism | [M] M-WAIV (waiver files parse, every entry has why + evidence) + [H] | an adjudication that buried a 0.6mm land-pattern delta as "residual" |
| M5 | Immutable releases with provenance: EXACT git_sha (hex, exists), git_dirty false (scoped to the release's inputs — the board subtree + skills/, not the whole repo; a dirty sibling project does not block), sha256 table verifies, CHANGELOG entry names the dir, SUPERSEDED.md chains closed, fix-claims carry falsifiable evidence IN verification/ | [M] M-REL | "git_sha: HEAD@release"; stale CHANGELOG; a fix-claim verified only by its own author's method |
| M6 | The authoritative source wins over the derived metric: JLC's footprint model rotation > bbox arithmetic; datasheet figure > symbol library; fab capability page > IPC defaults; **the SOURCE's per-refdes LCSC (`circuit.json supplier_part_numbers`, from the .tsx) > any value+footprint match**. The orderable BOM's LCSC code for every refdes must EQUAL the source's — a merged row (2 refdes with different source codes on one line), a substituted code, or a blank code where the source has one is a FAIL, not a fab-time convenience. **Code identity is necessary but NOT sufficient: the LCSC's actual CATALOG VALUE must also equal the LABELED (Comment/Value) value.** For every R/C row, resolve the catalog value OFFLINE in order: BOM MPN column -> vendored `02_parts/<MPN>/part.yaml` directory name -> the vetted `jlcpcb-fab/references/lcsc_passives_ledger.yaml` (each code catalog-verified ONCE, ever — the ledger is load-bearing because real fab BOMs ship a blank MPN column and basic passives have no part.yaml); a resolved value that disagrees with the label is a FAIL and a row NO source resolves is FLAGGED for manual review (an unverifiable value is not a pass — verify once, append to the ledger, quiet forever) | [H] encoded in adjudication protocols + [M] M-BOM (`policy_audit`; standalone `bom_source_check.py FAB_BOM CIRCUIT_JSON [--parts 02_parts]` — leg A per-refdes vs circuit.json, leg B per-vendored-code vs part.yaml, leg C MPN-encoded value vs labeled value) | the USB-C flip saga: chasing the bbox metric against JLC's own spec, twice; usb-hub-3s-v3 v1.1 (2026-07-23) — the exporter grouped by (value, footprint) and re-attached codes by value-token, collapsing 10uF/50V C77102 onto the 10uF/25V C77100 row (25V caps shipped on a 50V input rail) and substituting the 100uF output cap C84455->C90143; and usb-hub-3s-v3 v1.2 (2026-07-23) — R12 resolved to C2933210 (MPN FRC0603F3741TS = 3.74k) while labeled 4.12k, driving the buck-C setpoint to ~4.97 V undervoltage; code identity PASSED, blind to catalog value. The BOMs passed every gate because nothing compared them to source or to catalog value |
| M9 | JOURNAL DISCIPLINE: every stage keeps `01_docs/journal/<stage>.md` (append an entry at every start/iteration/finish, with MEASURED results) and writes `01_docs/learnings/<stage>.md` at completion (issue → root cause → how-to-avoid, `candidate-canon` marked). Learnings are HARVEST SOURCES for this canon, not canon | [M] M-JRNL (journals exist once artifacts generate) + [M] M-LEARN (learnings required at release) + [H] harvest pass promotes/rejects each candidate | knowledge evaporation: the clean-room escape-wall analysis lived only in a chat report (2026-07-20) and the v3 run's tsci-drop diagnosis nearly did too (2026-07-21) |
| M8 | TWO-STRIKE PROMOTION: the second independent board needing the same bespoke `03_src` script converts it into shared backend + config schema, MANDATORILY; until then every bespoke `03_src` script names (in its docstring) the backend-gap it stopgaps | [H] release review + 03_src contract | scoped-floor DRU injection and pour-fed tap routing were each written twice (v2 grind report + usb-pwr-hub-3s) before anyone was forced to promote them; the promoted-chain fast rebuild driver was hand-rewritten 3x before landing template-owned as `templates/03_src/rebuild_reuse.sh` (2026-07-23) |
| M7 | Every folder is GOVERNED by a contracts.md (its own, or the nearest ancestor's via explicit `## Allowed` patterns): permitted names, audit method, expected structure. Skills never reference a concrete `projects/<board>` path — worked evidence lives in `examples/` snapshots with PROVENANCE.md | [M] C-COV/C-ALLOW/C-ISO (`scripts/contracts_audit.py`, run by tests; `--projects` grades boards adopted-forward) | 2026-07-21: legacy `template/` drifted silently from the skill's stage contracts (two homes), and a skill cited a live project's proof artifact — a path no clean-room worktree can resolve |
| M10 | MANIFEST CONSISTENCY: a release manifest's human-readable summary must not disagree with the machine evidence it ships — every count the MANIFEST states that is also present in shipped evidence must MATCH (ERC errors/warnings across MANIFEST, policy_audit S-ERC row, erc.json; bom_source_check's claimed line count vs fab/bom.csv's actual data rows; absence != mismatch), and evidence produced against a staging path is not evidence about the sealed archive: any `07_releases/<dir>/` path embedded in verification evidence must name THIS release's directory or an existing sibling | [M] M-CONS (`release_freshness_check.py` check (d), always on; its version key parses board-prefixed release names so the stale-artifact check also runs on them) | crow-recorder-central-v2 v1.0 (sealed 2026-07-23, found 2026-07-24): MANIFEST "1409 baselined warnings" vs shipped audit "1215", claimed 48 BOM lines vs 49 shipped rows, and bom_source_check.txt naming a staging dir — three disagreements, zero gates; plus the `_version_key` `^v` regex silently opting every board-prefixed release out of the stale check (same silent-skip class as the M-REL glob bug) |

| S-DSL | Circuit declarations COMPILE TO NATIVE KiCad artifacts; every gate runs on artifacts, never on a DSL's claims about them. Front-ends may vary (schwriter2 declarations, future adapters); .kicad_sch/.kicad_pcb + the gate stack are fixed | [G] structural | evaluated CircuitScript 2026-07-18: netlist-only KiCad export would break ERC/parity/S-OCCL at their strongest link |

### Verification scoping (amendment 2026-07-23) — full breadth once per material state

The fresh-context review battery (M1's independence engine: both red-team
lenses, pin review, render review) runs at FULL breadth once per MATERIAL
design state. A material change voids prior verdicts — that rule keeps its
teeth — but post-fix re-verification is SCOPED: targeted confirmation of each
changed item, plus ONE integrated fresh-context lens over the result. "Fresh"
means fresh-CONTEXT (a reviewer with no stake in the fix — the independence M1
actually buys), not a full-breadth re-run; re-running every lens after every
one-line fix converts the strongest gate into the most expensive rubber stamp.
Compute, like fab cost, is spent under a declared ceiling (the D-TIER
symmetry): work-class tiers in `skills/pcb-design/references/compute-tiers.md`.

Two corollaries (2026-07-23): **(1) Review precedes seal.** The battery runs
against the PRE-SEAL staging archive; the seal is cut only after the verdicts
are in (normative order: the 07_releases contract, "Seal procedure"). A
finding pre-seal costs an edit; the same finding post-seal costs a superseded
release — 3 of usb-hub-3s-v3's 4 seals died to post-ceremony reviews (mean
seal lifetime 5.6h). **(2) Sealed means done reviewing.** A SEALED release is
not re-reviewed absent a supersede trigger (a defect class proven elsewhere,
or new external evidence); retro-checks against a newly minted gate are
read-only and scoped to that gate. Measured cost of violating this: 8 of one
family's ~16 lens runs targeted an already-immutable board, produced zero
board changes, and the compliance backfill introduced 2 new defects
(crow-mic-pod, 2026-07-22).

## Running the audit

```
/usr/bin/python3 scripts/policy_audit.py <project_dir> [--config 03_src/rules/policy_audit.json]
```

Emits `<project>/06_build/policy_audit.md` with one row per ID:
PASS / FAIL / WAIVED(evidence) / N-A(reason) / HUMAN(protocol pointer).
The release gate requires: zero FAIL, every WAIVED entry evidence-backed,
and the HUMAN items carrying verdicts in the release's verification/.
Adopted-forward policy: projects released before a policy's adoption date
are graded honestly and the gap tracked in their remediation list — history
is not rewritten.

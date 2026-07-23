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
| E-MARGIN | Output SETPOINT vs LOAD MARGIN: a regulated rail feeding a KNOWN load must clear the load's brownout with real IR headroom. A rail in `power_tree.yaml` that declares `load_uv_threshold` (the downstream load's undervoltage/brownout voltage) must have `vout_min − load_uv_threshold > 0` AND, at `iout_max_A`, leave more series-resistance budget than the delivery path burns: with a declared `ir_budget_mohm` (board+connector+cable) the headroom must exceed `ir_budget·iout·(1+margin)` (default margin 0.2); without one, the implied budget `(vout_min−UV)/iout` must clear the `ir_floor_mohm` floor (default 100mΩ — a bare realistic cable+connector+trace path). The cable/connector ASSUMPTION is judgment: the reviewer confirms `ir_budget_mohm` matches the real path | [M] E-MARGIN (`power_topology.py PROJECT_DIR --margin`) + [H] the delivery-resistance assumption confirmed in the red-team topology/protection lens | usb-hub-3s-v3 (2026-07-23, external review): a rail regulated to 4.97V fed a Raspberry Pi 5 (undervoltage detect ~4.63V) at 5A — leaving only (4.97−4.63)/5A ⇒ ~68mΩ TOTAL for board+connector+cable IR drop, less than a real e-marked 5A USB-C cable + two connector pairs. BOTH zero-context red-team reviews COMPUTED the 4.97V setpoint and neither flagged the thin margin — the headroom was never made a number |
| E-OFF | QUIESCENT DRAIN / OFF-CONTROL: a self-contained energy source (battery/cell/pack) must have a DOCUMENTED de-energization path and a BOUNDED stored quiescent draw. When a battery source is detected (`power_tree.yaml` `source_type:`, or VBAT/BATT/PACK nets, or a battery ADR), the power tree must declare `off_control:` (the mechanism — master switch / load-switch / EN-gating; or explicitly "always-on" WITH an ADR) and `quiescent_ua:` (the stored/shutdown draw). "Always-on" is a decision that must be ADR-justified, never a silent default. Whether the declared mechanism actually EXISTS in the netlist, and whether the drain is acceptable for the pack, are judgment: folded into the mandatory input-protection ADR's required-question list (SKILL.md) and confirmed by the red-team topology lens | [M] E-OFF (`power_topology.py PROJECT_DIR --off-control` — battery detected ⇒ off_control + quiescent_ua declared; a bare "always-on"/"none" with no ADR = FAIL) + [H] the input-protection ADR + red-team lens | usb-hub-3s-v3 (2026-07-23, external review): a 3S-LiPo board tied both buck EN pins active with no master switch — the controllers idle-drain the pack the whole time it sits in storage. No review asked "how is it de-energized / does it self-drain" |

## Meta — worth more than all of the above

| ID | Policy | Verified | Motivating incident |
|---|---|---|---|
| M1 | Checker and checked must not share a method: per failure class, at least one check from an independent reference (datasheet figure, JLC CAD, fresh agent, pixel measurement) | [H] release review confirms the battery ran | every hard catch this project made came from outside the design's own assumptions |
| M2 | Machine-check what you can — a prose rule will eventually be skipped | this file + policy_audit.py ARE the enforcement | refdes-on-silk became real only as audit gate I10 |
| M3 | Everything regenerable from source: never hand-edit 04_kicad; ALL rebuild inputs tracked in git — the final route chain file is PROMOTED to 03_src/route/ (06_build stays disposable otherwise) and its sha recorded in the MANIFEST | [M] M-REPRO | laser board's load-bearing r3.kicad_pcb was gitignored — unreproducible from a fresh clone |
| M4 | Evidence-backed exceptions: every waiver/adjudication carries the measurement that justifies it; positional deltas decomposed by mechanism | [M] M-WAIV (waiver files parse, every entry has why + evidence) + [H] | an adjudication that buried a 0.6mm land-pattern delta as "residual" |
| M5 | Immutable releases with provenance: EXACT git_sha (hex, exists), git_dirty false (scoped to the release's inputs — the board subtree + skills/, not the whole repo; a dirty sibling project does not block), sha256 table verifies, CHANGELOG entry names the dir, SUPERSEDED.md chains closed, fix-claims carry falsifiable evidence IN verification/ | [M] M-REL | "git_sha: HEAD@release"; stale CHANGELOG; a fix-claim verified only by its own author's method |
| M6 | The authoritative source wins over the derived metric: JLC's footprint model rotation > bbox arithmetic; datasheet figure > symbol library; fab capability page > IPC defaults | [H] encoded in adjudication protocols | the USB-C flip saga: chasing the bbox metric against JLC's own spec, twice |
| M9 | JOURNAL DISCIPLINE: every stage keeps `01_docs/journal/<stage>.md` (append an entry at every start/iteration/finish, with MEASURED results) and writes `01_docs/learnings/<stage>.md` at completion (issue → root cause → how-to-avoid, `candidate-canon` marked). Learnings are HARVEST SOURCES for this canon, not canon | [M] M-JRNL (journals exist once artifacts generate) + [M] M-LEARN (learnings required at release) + [H] harvest pass promotes/rejects each candidate | knowledge evaporation: the clean-room escape-wall analysis lived only in a chat report (2026-07-20) and the v3 run's tsci-drop diagnosis nearly did too (2026-07-21) |
| M8 | TWO-STRIKE PROMOTION: the second independent board needing the same bespoke `03_src` script converts it into shared backend + config schema, MANDATORILY; until then every bespoke `03_src` script names (in its docstring) the backend-gap it stopgaps | [H] release review + 03_src contract | scoped-floor DRU injection and pour-fed tap routing were each written twice (v2 grind report + usb-pwr-hub-3s) before anyone was forced to promote them |
| M7 | Every folder is GOVERNED by a contracts.md (its own, or the nearest ancestor's via explicit `## Allowed` patterns): permitted names, audit method, expected structure. Skills never reference a concrete `projects/<board>` path — worked evidence lives in `examples/` snapshots with PROVENANCE.md | [M] C-COV/C-ALLOW/C-ISO (`scripts/contracts_audit.py`, run by tests; `--projects` grades boards adopted-forward) | 2026-07-21: legacy `template/` drifted silently from the skill's stage contracts (two homes), and a skill cited a live project's proof artifact — a path no clean-room worktree can resolve |

| S-DSL | Circuit declarations COMPILE TO NATIVE KiCad artifacts; every gate runs on artifacts, never on a DSL's claims about them. Front-ends may vary (schwriter2 declarations, future adapters); .kicad_sch/.kicad_pcb + the gate stack are fixed | [G] structural | evaluated CircuitScript 2026-07-18: netlist-only KiCad export would break ERC/parity/S-OCCL at their strongest link |

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

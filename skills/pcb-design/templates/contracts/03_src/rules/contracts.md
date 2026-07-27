# contract: 03_src/rules/

**Purpose** — design intent that must be MACHINE-ENFORCED. Intent that only
a human reads belongs in `01_docs/ARCHITECTURE.md`; intent a tool must check
belongs here.

**Mutability** — hand-edited. This is source; `.kicad_dru` and the
`.kicad_pro` netclasses are its OUTPUT.

## Allowed

| File | What |
|---|---|
| `nets.yaml` | net classes: nets, current, intent, min_width, routing strategy, verify, scoped exemptions; `fab_tier` (capability floors for the generic backend); `scoped_floors` (insideArea width relaxations, `why` REQUIRED) |
| `electrical_invariants.yaml` | design-INTENT assertions the netlist must satisfy (canon E-INV): `pin_on_net`, `series_chain`, `net_has_part`, **`part_value`**. Each REQUIRES `adr:` (the ADR that emitted it) + `why:`. **`adr:` MUST BE QUOTED — `adr: "0011"`, or unpadded `adr: 11`.** A bare zero-padded reference is a YAML 1.1 OCTAL literal and the loader REJECTS it: `adr: 0011` becomes the integer 9 and re-pads to `"0009"`, `adr: 0012` -> `"0010"`, `adr: 0010` -> `"0008"`, `adr: 0020` -> `"0016"`, while `adr: 0008`/`0009` survive as strings only because 8 and 9 are not octal digits. That is not a SKIP — the invariant silently satisfies the WRONG ADR and E-ADR credits a document that emitted nothing. The rejection is written at the width of the class (canon M-WIDTH): every unquoted zero-padded `adr:` is refused, including the ones that happen to survive, because which are safe is a fact about the digits and not about the schema. It is a REJECTION rather than a coercion because coercion is impossible after the fact — by the time `yaml.safe_load()` returns, `adr: 0011` and `adr: 9` are the same object and the padding is gone; the check runs on the composed NODE, which still carries the scalar's quoting style. Measured 2026-07-27: this template itself and the board seeded from it both wrote `adr: 0011` and both resolved it to `0009`. **`part_value` `{part, min\|max\|equals (+tolerance_pct), adr, why}` pins a PARAMETER, which the other three cannot** — they pin TOPOLOGY, and an invariant that pins a component's EXISTENCE does not pin its VALUE. smc0985-cooksense 2026-07-25: the WD_PET safety fix landed a 100k watchdog pull-down where TI SLVS165O bounds it at 5.2k (I_IL 190uA max x R < V_IL 0.99V), silently disabling the supervisor on a cooking-contactor interlock — and ALL THREE assertions that shipped with that fix (one `net_has_part`, two `pin_on_net`) PASS on the 100k netlist, because the resistor does exist, on the right nets. Values are read from the netlist's own `(comp (value ...))` and decoded as SI, so `1k`/`1kOhm`/`1kΩ`/`4k7`/`0R1` are one number — note `m` is MILLI and `M` is MEGA, and an UNDECODABLE value is a FAIL, never a skip. At least one bound is REQUIRED: an assertion naming a part and bounding nothing is the exact gap this kind closes. Emitted by protection/topology ADRs; graded by `electrical_invariants.py`. OPTIONAL top-level `label_survival:` block (canon S-NETMERGE, graded by `net_label_survival.py` — the schematic net-merge gate; the generic every-global-label-survives-to-the-netlist check is ALWAYS ON with or without this block): `exempt:` labels allowed to be absent, each REQUIRES `why:` evidence (canon M4); `pin_map:` board-specific pin-for-pin net assertions `{refs, n_start, pins: {pin: pattern-with-{n}}, unconnected}` — the crow-recorder net-merge class (P5VA_4→AUDIO4M, MID2P→5V: two DO-NOT-ORDER defects, every self-consistent gate green, 2026-07-23) |
| `power_tree.yaml` | per-rail voltage ENVELOPES + converter selection, graded by `power_topology.py` for E-TOPO / E-MARGIN / E-OFF. REQUIRED per rail: `{name, vin_min, vin_max, vout_min, vout_max, iout_max_A, converter, eff}` — topology DERIVED from Vin-vs-Vout (buck/boost/buck_boost) asserted against the converter part.yaml `type:`, over-capable = over-engineering FAIL (E-TOPO). **THIS FILE IS NOT OPTIONAL WHEN THE BOARD HAS A CONVERTER.** E-TOPO takes its N-A only when `02_parts` declares NO buck/boost/buck_boost/linear part — an independent artifact written by a different stage (canon M1), because until 2026-07-27 the gate asked the power tree whether there was anything to grade and believed it. An ABSENT file, or `rails: []`, with a converter present is `0/N converters graded` and a FAIL; a rails list that omits SOME of `02_parts`' converters is reported as `UNGRADED CONVERTERS: k of N` and fails too. Measured on landing: usb-hub-3s — the board whose IP6559 buck-boost MOTIVATED E-TOPO — had no power_tree.yaml and had never been graded by it. **LINEAR CONVERTERS.** A linear regulator (part.yaml `type:` matching `ldo`/`linear`/`low-dropout`) is NOT a fourth topology; it is one IMPLEMENTATION of a step-down requirement, so the derivation is unchanged: required BUCK is MET, required BOOST or BUCK_BOOST is a cannot-meet FAIL (it cannot step up, and an overlapping Vin envelope means it drops out somewhere in the range). It is then graded on the two failure modes the derivation cannot see — `vin_min - vout_max >= dropout_mv` and `(vin_max - vout_min) * iout_max_A <= pdiss_max_mw`, both REQUIRED from the converter's part.yaml (see the 02_parts contract) or overridden per rail as OPTIONAL `dropout_mv:` / `pdiss_max_mw:`. A linear rail's INPUT CURRENT is `iout`, not `Pout/eff/Vin`: the pass element is in series with the load, so `eff` does not enter the trunk-current sum for it (modelling one as constant-power under-states its trunk current by Vout/Vin — 25% on the first board that declared one). OPTIONAL per rail: `load_uv_threshold` (the load's brownout V — ACTIVATES E-MARGIN), `ir_budget_mohm` (board+connector+cable series R, mΩ), `margin`, `feedback: {vref, vref_tol_pct, r_top_ohm, r_top_tol_pct, r_bottom_ohm, r_bottom_tol_pct}` (the FB-divider tolerance window — all six REQUIRED when present; the checker computes the worst-case vout corners from vout = vref·(1+Rtop/Rbot), FAILS E-TOPO/E-MARGIN when the DECLARED vout window is NARROWER than computed, and grades E-MARGIN headroom from the COMPUTED worst-low — the usb-hub-3s-v3 Vref-only under-stated window, 2026-07-23). OPTIONAL top-level: `source_type` / `off_control` / `quiescent_ua` / `pack_capacity_mah` (E-OFF: a DETECTED battery source must declare its de-energization path + stored draw, an always-on off_control needs an ADR reference), `ir_floor_mohm` (E-MARGIN floor when a load-UV rail declares no ir_budget_mohm, default 100mΩ) |
| `assembly.yaml` | ASSEMBLY intent — the ONE machine-readable home for "who gets placed, and why not" (canon A-POP + A-POS + A-STOCK, and the planned A-ROT, held 2026-07-25; PCBA is the default deliverable). REQUIRED top-level: `service`, `sides`, `fiducials` (`none` is allowed but SILENCE is not), `build_quantity`. `not_assembled:` entries REQUIRE `{refs, reason, evidence, disposition}` where `reason` is the CLOSED vocabulary `not_in_catalog\|consign\|user_supplied\|dnp_by_design\|mechanical\|test_point\|process_incompatible` (`process_incompatible` added 2026-07-25: a part that IS catalogued, stocked and wanted but that the ORDERED process cannot place — the classic case being a true THT part on a `sides: [top]` SMT-only order, whose pads carry no F.Paste so it cannot be intrusive-reflowed. crow-recorder-central-v2 v1.4 shipped exactly that as J1 and the nearest existing reason would have been `not_in_catalog`, which is FALSE: a closed vocabulary with no true option forces a lie into the decision record) and `evidence` is a DATED measurement (the catalog query + its result), not a rationale — every ref listed must ALSO carry `FP_EXCLUDE_FROM_POS_FILES` on the board, and a declared-unpopulated ref still on the CPL is a FAIL. `board_attr_plan:` `{refs, measured_on, plan}` is the ONLY way to defer that board attribute, exactly parallel to `sourcing_plan:` for stock — it exists because the attribute lives in the `.kicad_pcb`, so on a board whose gerbers are sealed and correct the only way to satisfy the check used to be regenerating the board, which churns every UUID (MEASURED 81626 diff lines on a semantically identical rebuild) and turns a data-only CPL fix into a full respin. The DECISION is never deferred: the ref must still be off the shipped CPL, which `DECLARED-BUT-PLACED` enforces and which is NOT deferrable, and the exporter honours `not_assembled:` directly so the declaration is itself a mechanism. `consigned:` parts are POPULATED (they stay ON the CPL): `{refs, lcsc, msl, evidence, disposition}`, `msl` REQUIRED for consigned parts and any exposed-pad package. OPTIONAL per `not_assembled:` entry: `lcsc:` — the code of a catalogued part deliberately not placed, read by `jlc_twin --assembly` so its body still renders and its land pattern is still checked (this replaces hand-typed `--also REF=LCSC`, which was a second home for the population set). `sourcing_plan:` `{lcsc, measured_stock, measured_on, plan}` is the ONLY way to seal past a non-OK stock line (canon A-STOCK, graded by `release_freshness_check.py` check (e); `build_quantity` is the multiplier). `exempt_prefixes:` declares refdes classes whose CPL absence needs no entry — DECLARED, never hardcoded in the checker. The release MANIFEST `not_assembled:` line is GENERATED from this file, never hand-written twice (cooksense v1.1: 13 blank-LCSC CPL rows vs a MANIFEST declaring 12 of them not_assembled — the two drifted because nothing read either) |
| `stackup.yaml` | layer count, what each layer is for, fab tier (optional) |
| `twin_adjudications.yaml` | reviewed jlc_twin findings accepted WITH evidence (see jlcpcb-fab skill) |
| `passives_lcsc.yaml` | passives BOM-comment -> LCSC seed map (bom_seed input; usb-hub-3s) |
| `policy_waivers.yaml` | policy_audit waivers accepted WITH measurement evidence (canon M4/M-WAIV): a YAML list, each entry naming the WAIVED S-/P-/R-/M-/E- policy ID + `why:` + the measurement that justifies it; P-ADJ net-span over-budget dispositions land here with the measured span + why. An entry without evidence is itself a FAIL |
| `policy_audit.json` | OPTIONAL `policy_audit.py` config (`--config 03_src/rules/policy_audit.json`, its default path): thresholds + HUMAN-item verdict pointers (S5/S6/S7) |
| `contracts.md` | this file |

## The rule that makes this folder worth existing

**`intent` and `min_width` come from the same file, so they cannot drift.**
When they lived apart — classes in `.kicad_pro`, intent in a human's head —
both 6A switch nodes got routed at 0.15mm and DRC had no basis to object.

Corollary: **define classes and floors BEFORE routing, never after.** With
floors in place a router's thin-pass output fails DRC immediately.
Retrofitting them cost a full repair campaign.

## Structure: `nets.yaml`

Each class requires: `intent` (prose, why this net is special), `nets` (list
or patterns), `min_width`, `routing` (pour vs track, and the strategy),
`verify` (how to prove it). `exemptions` are scoped to NAMED RULE AREAS that
exist on the board — never a blanket carve-out.

**`current:` is REQUIRED on every class, and silence is not a declaration.**
A class with no ampacity obligation says so — `signal`, `none`, `return
(planes)` — and that is graded as an explicit exemption. A magnitude may carry
a qualifier (`7 A worst case`, `<50 mA`, `~1.5A pulsed`, `6 A / 5 A`); the
first figure followed by an amp unit is taken, so write the BINDING figure
first in a range. **A value the gate cannot read is a FAIL, never an
exemption.**

WHY THIS IS SPELLED OUT: `parse_amps` used to return a bare `None` for both
"absent" and "present but unreadable", and `rules_audit` filed it under OKS as
"n/a (no current: declared)". Measured 2026-07-27 — **A-AMP graded 10 of 57
declared currents fleet-wide**, that message was wrong 100% of the times it
fired (ZERO classes declare no current), and usb-hub-3s-v3 shipped `PWR_IN`
7 A, `PWR_RAIL` 6 A and `SWITCH_NODE` 7 A all silenced while the single class
it did grade FAILED. After the fix: 53 of 57, with the remainder failing
loudly as unreadable.

OPTIONAL per class: **`pour_fed: "<evidence>"`** — A-AMP measures the narrowest
enforced TRACK width, but a plane-fed net does not conduct through a track, so
on such a class the metric is ADJACENT to the property (the same error shape as
measuring island positions instead of island shapes). Declare the pour geometry
that carries the current — layer, area/width, and the measurement. A bare
`pour_fed: true` is REFUSED: canon M4 wants evidence, not rationale.

Optional per-class `diff_pair:` `{width, gap, via_gap?, max_uncoupled?}` (mm)
declares SOLVED controlled-impedance geometry for a differential-pair class
(2026-07-24, crow-recorder-central-v2 v1.1 / external-review F2: USB-HS 90ohm
was neither constrained nor demonstrated — `diff_pair_dimensions` sat `[]`).
The emitter writes it three ways so it is ACTIVE, not documentation: netclass
`diff_pair_width/gap/via_gap`, a `.kicad_dru` `<CLASS>_diffpair` rule
(`diff_pair_gap` min/opt + optional `diff_pair_uncoupled` max), and the board
`design_settings.diff_pair_dimensions` entry. `gap` is REQUIRED once the key
exists; width/gap must clear the tier's `min_track`/`min_space`. NB: KiCad
pairs nets only by name suffix (P/N, +/-, _P/_N) — a diff_pair class whose
net names cannot pair silently gates NOTHING (rename the nets, e.g.
USB_DM -> USB_DN). Cite the stackup + solve (which fab stackup, Er, h, the
computed Zdiff) in the class `intent` or DETAIL_DESIGN.

Top-level `scoped_floors:` (canon M8 promotion of the hand-appended
insideArea rules) is the machine-enforced form of a scoped exemption:
`{zone, nets, min_width, why}` — the generic emitter writes it as a
last-match `.kicad_dru` rule after the netclass floors. `why` is REQUIRED
(canon M4); `min_width` must still clear the declared tier's `min_track`.

Top-level `fab_tier:` is also the SINGLE SOURCE of capability floors for
the generic backend (`fab_tier_util.py`): class widths, route/stitch/tap
via geometry and silk text heights are floored/derived from it, and
explicit sub-floor values are generation errors naming the tier.

Floors are BACKSTOPS, not sizing: trunk current rides pours and planes. The
floor's job is to make "silently thin" impossible, not to carry the amps.

## Validate

- every net in `nets.yaml` exists in the netlist (else the class is a no-op)
- every net carrying >1A per `01_docs/ARCHITECTURE.md`'s power tree appears in
  some class here — an unclassed high-current net is a BUG
- regenerating produces byte-identical `.kicad_dru` + `.kicad_pro`
  netclasses (drift = someone hand-edited the output)
- every `exemptions[].area` names a rule area that exists on the board
- every `policy_waivers.yaml` entry parses, names a real policy ID, and carries
  `why:` + measurement evidence (canon M-WAIV)
- DRC width comparisons are EXACT NANOMETERS: a track at 249800nm prints as
  "0.25" and fails a 0.25mm floor. Round emitted values.

## Repair

- Net in `nets.yaml` but not the netlist → stale; remove it or fix the name.
- High-current net with no class → add it; do not lower the floor to match
  the copper.
- Hand-edit found in `.kicad_dru` → port to `nets.yaml`, regenerate.

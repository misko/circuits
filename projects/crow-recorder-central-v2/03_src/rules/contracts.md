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
| `electrical_invariants.yaml` | design-INTENT assertions the netlist must satisfy (canon E-INV): `pin_on_net`, `series_chain`, `net_has_part`. Each REQUIRES `adr:` (the ADR that emitted it) + `why:`. Emitted by protection/topology ADRs; graded by `electrical_invariants.py`. OPTIONAL top-level `label_survival:` block (canon S-NETMERGE, graded by `net_label_survival.py` — the schematic net-merge gate; the generic every-global-label-survives-to-the-netlist check is ALWAYS ON with or without this block): `exempt:` labels allowed to be absent, each REQUIRES `why:` evidence (canon M4); `pin_map:` board-specific pin-for-pin net assertions `{refs, n_start, pins: {pin: pattern-with-{n}}, unconnected}` — the crow-recorder net-merge class (P5VA_4→AUDIO4M, MID2P→5V: two DO-NOT-ORDER defects, every self-consistent gate green, 2026-07-23) |
| `power_tree.yaml` | per-rail voltage ENVELOPES + converter selection, graded by `power_topology.py` for E-TOPO / E-MARGIN / E-OFF. REQUIRED per rail: `{name, vin_min, vin_max, vout_min, vout_max, iout_max_A, converter, eff}` — topology DERIVED from Vin-vs-Vout (buck/boost/buck_boost) asserted against the converter part.yaml `type:`, over-capable = over-engineering FAIL (E-TOPO). OPTIONAL per rail: `load_uv_threshold` (the load's brownout V — ACTIVATES E-MARGIN), `ir_budget_mohm` (board+connector+cable series R, mΩ), `margin`, `feedback: {vref, vref_tol_pct, r_top_ohm, r_top_tol_pct, r_bottom_ohm, r_bottom_tol_pct}` (the FB-divider tolerance window — all six REQUIRED when present; the checker computes the worst-case vout corners from vout = vref·(1+Rtop/Rbot), FAILS E-TOPO/E-MARGIN when the DECLARED vout window is NARROWER than computed, and grades E-MARGIN headroom from the COMPUTED worst-low — the usb-hub-3s-v3 Vref-only under-stated window, 2026-07-23). OPTIONAL top-level: `source_type` / `off_control` / `quiescent_ua` / `pack_capacity_mah` (E-OFF: a DETECTED battery source must declare its de-energization path + stored draw, an always-on off_control needs an ADR reference), `ir_floor_mohm` (E-MARGIN floor when a load-UV rail declares no ir_budget_mohm, default 100mΩ) |
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
`verify` (how to prove it). `current` where >1A. `exemptions` are scoped to
NAMED RULE AREAS that exist on the board — never a blanket carve-out.

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

# DRC discipline: classify, legalize intent, zero noise

Goal state: **zero violations**, where every rule reflects real fab
capability or documented design intent — so any NEW violation lands in a
zero-noise report and is investigated, never re-baselined over.

## Classification (the core move)

An item is REAL only if it is between DIFFERENT nets AND below the fab
floor. Everything else is margin or design intent:

```python
# parse WriteDRCReport text into blocks, then per clearance/hole item:
nets = set(re.findall(r"\[([A-Za-z0-9_/.+-]+)\]", body))
real = len(nets) > 1 and 0 <= actual_mm < FAB_FLOOR_MM   # e.g. 0.10 for JLC 4L
```

Gate hard on `*_real` counts; report margin counts as warnings. (See
`scripts/classified_drc.py` and `scripts/audit_template.py`.)

## JLC capability floors (verify at order time; 2026 numbers)

| Parameter | 2L | 4L standard | 4L advanced |
|---|---|---|---|
| clearance / track | 0.127 / 0.127 | 0.10 / 0.09 | 0.10 / 0.076 |
| via diameter / drill | 0.45 / 0.30 | 0.45 / 0.20 | 0.25 / 0.15 (small-via option, costs extra) |
| hole-to-copper | 0.25 | 0.2 | 0.2 |
| hole-to-hole | 0.25 | 0.2 | 0.2 |
| copper-to-edge | 0.2 | 0.2 (routed) | 0.2 |

Set board rule floors to the tier you are actually buying — stale
standard-tier floors on advanced-tier geometry produced ~226 false flags.
In-pad thermal vias (0.25/0.15) require the advanced/small-via option.

## Scoped .kicad_dru rules for design intent

`<project>.kicad_dru` next to the board; loaded automatically. Patterns
that earn their keep:

```
(version 1)
(rule "same-net overlap is by design"          ; merged b2b FET lands, join stubs
  (condition "A.NetName == B.NetName")
  (constraint clearance (min 0mm)))
(rule "unnetted mechanical pads exempt"        ; FET anchor pads, connector pegs
  (condition "A.NetName == ''")
  (constraint clearance (min 0mm)))
(rule "npth pegs at footprint-intrinsic distances"  ; USB-C, fuse holders
  (condition "A.Type == 'Pad' && A.NetName == ''")
  (constraint hole_clearance (min 0.1mm)))
```

Caveats: a `(min 0mm)` edge rule still flags pads that CROSS the edge line
(move the part instead); `memberOfFootprint()` did not match on KiCad 7.0
— prefer net/type conditions.

## Severity policy (each class must have an owner)

`rule_severities` in `.kicad_pro` → "ignore", each with documented
ownership: `lib_footprint_issues` (generated board is source of truth),
`solder_mask_bridge` (fab strips sub-web mask on fine pitch),
`silk_edge_clearance` (overhanging connector silk, fab clips),
`courtyards_overlap` ONLY if a separate audit gate owns the accepted pairs.

## Fill-dependent checks

- `starved_thermal` counts ZONE SPOKES only — a via or track connection
  does not satisfy it, and island-removal can't delete pad-attached
  islands (they're "connected" to the filler, "incomplete" to DRC).
  Correct fix: per-pad `ZONE_CONNECTION_FULL` (solid) on the flagged pads.
  Solid is preferable anyway for PTH connector pads; fine for
  reflow-assembled SMD.
- Headless and GUI zone fills differ; GUI DRC is authoritative here.

## The audit-gate pattern (beyond DRC)

Board-level invariants that DRC can't express, run every revision
(see `scripts/audit_template.py`): every pad inside the outline; no parts
parked off-board; edge connectors overhang their declared MATE direction;
screw-head keepouts around mounting holes; unnetted pads only where
whitelisted; bbox overlaps reported; classified-DRC counts vs committed
baseline (fail on real regressions, warn on margin churn).

## Custom-rule precedence (used for scoped exemptions)

KiCad evaluates `.kicad_dru` rules in file order with LATER rules taking
precedence for the same constraint type. This is how a named rule-area
exemption beats a general netclass floor: the `width_switch_node (min
0.3mm)` rule comes first, and `width_sw_tap` with condition
`A.NetClass == 'SWITCH_NODE' && A.intersectsArea('SW_TAP_A')` (min 0.15mm)
comes after — tracks inside the area get the lower floor, everything else
keeps the strict one. Constraint comparisons are in EXACT nanometers:
249800 nm fails a 0.25 mm minimum while printing as "0.25" everywhere
(verified: KRT import artifact, SPF 2026-07).

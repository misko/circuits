#!/usr/bin/env python3
"""apply_drc_policy.py — cooksense board DRC policy, in SOURCE (canon M3).

generate_board writes a FRESH .kicad_pro (KiCad defaults: min_resolved_spokes 2,
cosmetic-silk severities = warning). Two board-level policy settings are NOT
emitted by any shared generator, so a full rebuild loses them and the DRC gate
lights up with items that were accepted on the sealed baseline. This idempotent
patcher re-applies them after generate_rules LAST (which preserves, but does not
create, the .kicad_pro DRC-policy block). Merge-in-place — never rewrite the
.kicad_pro wholesale.

POLICY (each with its measured justification):
  * min_resolved_spokes: 1
      Advanced via-in-pad + thermal zone connection legitimately yields
      single-spoke bonds on small SMD power pads; the pad still connects. The
      sealed baseline set 1 (default 2 flagged 11 starved_thermal on good bonds).
  * ISOLATION CLEARANCE RULES in the .kicad_dru (v1.3)
      The board's headline safety property — >=6mm keypad<->SELV creepage — was
      held by FOOTPRINT PITCH ALONE at 2% margin, with KEYPAD_ISO's netclass
      clearance set to 0.12mm, identical to Default. NO GATE COULD FAIL ON IT
      (layout-lens P1-3). A netclass clearance cannot express it either: it
      would force 6mm between keypad nets and EACH OTHER, which the comb
      cannot survive. The correct mechanism is a conditional DRU rule keyed on
      "A in the class, B outside it", which is what these two emit:
        keypad_isolation_6mm  KEYPAD_ISO   <-> everything else, min 6.0mm
        opto_isolation_2mm    ISO_CONTACTOR<-> everything else, min 2.0mm
      6.0mm is the brief/ADR-0001 requirement (audit measures 6.12mm today, so
      there is 0.12mm of real margin and the rule CAN fail). 2.0mm is IEC
      60664-1 basic insulation at 30V working, pollution degree 3 (steam), for
      the opto's isolated secondary — v1.2 measured 0.175mm there.
      Both conditions exclude NO-NET items (B.NetName != ''). MEASURED reason:
      without it the keypad rule reports 71 violations, ALL of them KP_* copper
      against J_KEY_MATRIX's OWN floating shell tabs — metal that sits INSIDE
      the keypad domain and is deliberately un-tied so SELV GND stays out of
      the zone (the SM10B `tie: GND` removal, 2026-07-23). Those are not domain
      crossings. With the exclusion the keypad rule reports ZERO on the v1.2
      copper, which is the CORRECT answer: audit_board's 6.12mm I-ISO figure is
      confirmed, not contradicted. The opto rule still reports 82 at 0.199mm
      worst — that is the real layout-lens P0-2, now machine-visible.
      generate_rules_generic preserves rules it does not own, and this script
      runs AFTER it (rebuild step 8), so the pair survives every rebuild.
  * cosmetic silk severities -> ignore
      silk_over_copper / silk_edge_clearance / silk_overlap / text_thickness are
      the fleet-standard cosmetic classes resolved at fab silk-finalization
      (golden rule 8 classification; documented policy, not a real defect).

Usage: /usr/bin/python3 apply_drc_policy.py <project-root>   (cwd default)
"""
import json
import sys
from pathlib import Path

SILK_IGNORE = ["silk_over_copper", "silk_edge_clearance", "silk_overlap",
               "text_thickness"]

# (rule name, class, min clearance mm, why) — emitted into the .kicad_dru.
ISO_RULES = [
    ("keypad_isolation_6mm", "KEYPAD_ISO", "6.0",
     "brief section 4/7 + ADR-0001: the keypad contact domain shares no GND "
     "with SELV logic and must hold >=6mm creepage"),
    ("opto_isolation_2mm", "ISO_CONTACTOR", "2.0",
     "IEC 60664-1 basic insulation, 30V working, pollution degree 3 "
     "(steam-carrying cooking appliance), material group IIIa"),
]


def iso_rule_text(name, cls, mm, why):
    return (f'(rule "{name}"\n'
            f'  # {why}\n'
            f'  (condition "A.NetClass == \'{cls}\' && B.NetClass != \'{cls}\''
            f' && B.NetName != \'\'")\n'
            f'  (constraint clearance (min {mm}mm)))\n')


def apply_iso_rules(dru):
    """Idempotently maintain the isolation clearance rules in the .kicad_dru."""
    import re as _re
    txt = dru.read_text() if dru.exists() else "(version 1)\n"
    changed = []
    for name, cls, mm, why in ISO_RULES:
        want = iso_rule_text(name, cls, mm, why)
        # drop any existing block with this name (paren-depth scan from its start)
        m = _re.search(r'\(rule\s+"?' + _re.escape(name) + r'"?', txt)
        if m:
            i, depth = m.start(), 0
            while i < len(txt):
                if txt[i] == "(":
                    depth += 1
                elif txt[i] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            old = txt[m.start():i + 1]
            if old.strip() == want.strip():
                continue
            txt = txt[:m.start()] + txt[i + 1:]
            txt = _re.sub(r"\n{3,}", "\n\n", txt)
        txt = txt.rstrip("\n") + "\n" + want
        changed.append(name)
    if changed:
        dru.write_text(txt)
    return changed


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]) if argv else Path(".")
    # v1.2 (2026-07-24): 04_kicad holds TWO boards since the interposer design-
    # seal (ADR-0007) — this is the COOKSENSE board script, target it by name.
    pro = root / "04_kicad" / "cooksense.kicad_pro"
    if not pro.exists():
        sys.exit(f"apply_drc_policy: {pro} missing")
    d = json.loads(pro.read_text())
    ds = d.setdefault("board", {}).setdefault("design_settings", {})
    rules = ds.setdefault("rules", {})
    sev = ds.setdefault("rule_severities", {})

    changed = []
    if rules.get("min_resolved_spokes") != 1:
        rules["min_resolved_spokes"] = 1
        changed.append("min_resolved_spokes=1")
    for k in SILK_IGNORE:
        if sev.get(k) != "ignore":
            sev[k] = "ignore"
            changed.append(f"{k}=ignore")

    dru_changed = apply_iso_rules(root / "04_kicad" / "cooksense.kicad_dru")
    if dru_changed:
        changed.append("dru:" + ",".join(dru_changed))

    if changed:
        pro.write_text(json.dumps(d, indent=2) + "\n")
    print(f"apply_drc_policy: {pro.name} "
          + (f"applied {changed}" if changed else "already compliant (no-op)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

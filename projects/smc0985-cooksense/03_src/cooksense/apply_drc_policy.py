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

    if changed:
        pro.write_text(json.dumps(d, indent=2) + "\n")
    print(f"apply_drc_policy: {pro.name} "
          + (f"applied {changed}" if changed else "already compliant (no-op)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

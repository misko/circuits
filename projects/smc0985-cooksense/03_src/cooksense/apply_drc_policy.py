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
      *** `B.NetName != ''` WAS A CONSTRUCTION, NOT A WAIVER, AND IT IS GONE
      (v1.8, 2026-07-29 — canon M4 / G-VACUOUS-DRU). ***
      Both conditions used to carry `&& B.NetName != ''`. The observation that
      motivated it was correct — the only unnetted copper near KEYPAD_ISO is
      J_KEY_MATRIX's own floating shell tabs, which sit INSIDE the keypad domain
      and are deliberately un-tied so SELV GND stays out of the zone (the SM10B
      `tie: GND` removal, 2026-07-23) — but the MECHANISM was not. A clearance
      rule whose B-side requires a net EXEMPTS ALL UNNETTED COPPER BY
      CONSTRUCTION, and a floating shell tab, a mounting pad or a fill island is
      precisely the case an isolation barrier exists for. So "keypad_isolation_
      6mm: 0 violations" was not evidence about the board's headline safety
      property; it was evidence that the rule could not speak about it. On this
      board the barrier IS the safety story: every claim the board makes rests on
      the keypad domain being isolated from SELV logic while the OEM controller
      and OEM safety systems stay in control.
      The exemption is now BY NAMED REFDES, with the evidence measured on the
      SEALED v1.6 copper (`06_build/proof/keypad_iso_v18/`, kicad-cli 10.0.4,
      `--severity-all --refill-zones`):
        * old rule, unmodified sealed .kicad_dru ....... 0 clearance violations
        * conjunct simply DELETED, no exemption ....... 67 clearance violations
        * CLASSIFIED, never counted: 67 of 67 name `Pad MP of J_KEY_MATRIX` on
          one side, and the far side is 100% KEYPAD_ISO-class net (KP_D1..D4,
          KP_U1..U4, U_SEL_BUS). ZERO domain crossings. Worst actual 0.5723mm,
          best 5.9760mm, against the 6.000mm constraint. The tabs really are
          inside the domain; the barrier really does hold.
        * exemption `!B.memberOfFootprint('J_KEY_MATRIX')' ... 0 violations
        * and the exemption is BOUNDED: the whole board carries exactly TWO
          unnetted copper items, both of them `J_KEY_MATRIX.MP` (0 unnetted
          tracks/vias, 0 unnetted copper zones — the other no-net zones are
          RULE AREAS, not fills). So the exempted set is enumerated and finite,
          and any NEW unnetted copper anywhere on the board is graded.
        * PROOF THE PREDICATE EVALUATES (not a silently-dead rule): pointing the
          same exemption at the wrong refdes — `!B.memberOfFootprint(
          'J_RH_AMBIENT')` — restores all 67. The exemption is what silences it.
      Why not a net assignment instead: `J_KEY_MATRIX` is the only connector on
      the isolated side of the reed barrier, so bonding its shell to the SELV
      plane would SHORT the isolated domain. The tabs are unbonded BY DESIGN.
      `opto_isolation_2mm` loses the conjunct with NO exemption at all — there is
      no unnetted copper within 2mm of ISO_CONTACTOR, and it measures 0.
      generate_rules_generic preserves rules it does not own, and this script
      runs AFTER it (rebuild step 8), so the pair survives every rebuild — which
      is also why this defect could never have been fixed by regenerating.
      Historical note: the "71 violations" figure quoted here before this
      revision was a v1.2-era measurement and the current copper gives 67; the
      "opto rule reports 82 at 0.199mm worst" was also v1.2 and is CLOSED — the
      2.0mm ISO moat landed in v1.3 and the opto rule measures 0 today.
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

# (rule name, class, min clearance mm, why, exempt_refdes) — emitted into the
# .kicad_dru. `exempt_refdes` is a SINGLE footprint whose copper is excluded from
# the B side, or None for no exemption. It is deliberately a refdes and not a
# predicate over net presence: an exemption must be ENUMERABLE (open the board,
# list the pads of that footprint) so a reader can bound the blind spot. See the
# module docstring for the measured evidence behind the one exemption that
# exists. Adding one here without that measurement is an inherited defect.
ISO_RULES = [
    ("keypad_isolation_6mm", "KEYPAD_ISO", "6.0",
     "brief section 4/7 + ADR-0001: the keypad contact domain shares no GND "
     "with SELV logic and must hold >=6mm creepage",
     "J_KEY_MATRIX"),
    ("opto_isolation_2mm", "ISO_CONTACTOR", "2.0",
     "IEC 60664-1 basic insulation, 30V working, pollution degree 3 "
     "(steam-carrying cooking appliance), material group IIIa",
     None),
]

#: appended to every emitted rule comment so the .kicad_dru itself carries the
#: reason its one exemption is not a construction (a reader of the rule file must
#: not have to find this script to know).
EXEMPT_WHY = ("EXEMPTION, evidenced not constructed (canon M4): {ref} is the "
              "ONLY connector on the isolated side of the reed barrier, so its "
              "SM10B-GHS-TB shell tabs are unbonded BY DESIGN (bonding them to "
              "the SELV plane would short the isolated domain). Measured on "
              "sealed v1.6: dropping the exemption yields 67 clearance "
              "violations, 67/67 with {ref}.MP on one side and a KEYPAD_ISO "
              "net on the other - zero domain crossings, worst 0.5723mm. The "
              "board's only 2 unnetted copper items are both {ref}.MP, so the "
              "exempted set is FINITE and enumerated. Previously this was "
              "`B.NetName != ''`, which exempted ALL unnetted copper BY "
              "CONSTRUCTION and made a 0-violation DRC report meaningless "
              "about the board's headline safety property.")


def iso_rule_text(name, cls, mm, why, exempt=None):
    extra = f" && !B.memberOfFootprint('{exempt}')" if exempt else ""
    note = "\n  # " + EXEMPT_WHY.format(ref=exempt) if exempt else ""
    return (f'(rule "{name}"\n'
            f'  # {why}{note}\n'
            f'  (condition "A.NetClass == \'{cls}\' && B.NetClass != \'{cls}\''
            f'{extra}")\n'
            f'  (constraint clearance (min {mm}mm)))\n')


def apply_iso_rules(dru):
    """Idempotently maintain the isolation clearance rules in the .kicad_dru."""
    import re as _re
    txt = dru.read_text() if dru.exists() else "(version 1)\n"
    changed = []
    for name, cls, mm, why, exempt in ISO_RULES:
        want = iso_rule_text(name, cls, mm, why, exempt)
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

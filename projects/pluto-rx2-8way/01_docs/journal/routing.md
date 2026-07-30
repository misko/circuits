# routing — stage 6 journal (pluto-rx2-8way)

## 2026-07-29 18:05 — start
- did: read the stage-5 handoff, `03_src/route.yaml` in full, `rules/nets.yaml`,
  ADR-0002/0006/0007, `01_docs/CHECKLIST.md` section D, and the new shared gate
  `skills/kicad-pcb/scripts/copper_length_audit.py` (+ its `--schema` and the
  60-line owed-work note at `policy_audit.py`'s R-LEN row). Mapped the RF pad
  chains off the stage-5 board with pcbnew.
- result: the board carries 11 RF50 nets on 9 radial slots. MEASURED pad map:
  ANT1 (U_SW.24 <-> J_ANT1) ... ANT7 (U_SW.17 <-> J_ANT7) and RX2_OUT
  (U_SW.22 <-> J_RX2) are each TWO-PAD nets; the RF8 radial is THREE nets in
  series through the pickoff (U_SW.19 -RX1_TAP- R_T2 -RX1_TAP_MID- R_T1
  -RX1_MAIN- J_ANT8) and `RX1_MAIN` additionally carries J_RX1.1, so it is a
  T, not a chain. So the matched set is NOT "the nine arms" as copper.
- next: FIX THE SPEC FIRST. Three sub-tasks before a single track exists:
  (1) re-derive the +/-0.10 mm arm obligation, which is 1.3 deg at 6 GHz and
  is not holdable; (2) author `length_match:` in `03_src/rules/nets.yaml`;
  (3) re-point the two E-NETREF ghost keep_short budgets on PE42482A-X.

## 2026-07-29 18:50 — iterate 1 (spec repair, no copper)
- did: (1) WITHDREW the "+/-0.10 mm ROUTED arm length" obligation everywhere the
  project stated it (`03_src/audit_board.py` I3 note, `01_docs/CHECKLIST.md`
  section D) with the arithmetic, and authored `length_match: RF_RADIAL_STAR` in
  `03_src/rules/nets.yaml` — 8 congruent radials (ANT1..ANT7 + RX2_OUT),
  `topology: chain`, `congruent_pads: true`, `no_vias: true`,
  `max_spread_mm: 1.0`. (2) Re-pointed two ghost keep_short budgets to the nodes
  their datasheet sentences are about and DELETED a third rather than re-point it
  to a net that would pass. (3) Added `audit_board.py` I8, the instrument the
  deleted budget needed. (4) Rewrote the P-ADJ-UNREACHED waiver, including the
  correction of its own false general claim.
- result: MEASURED, all from the gates themselves.
  * 13.19 deg/mm at 6 GHz on JLC04161H-7628 (eps_eff 3.350, t_pd 6.105 ps/mm,
    lambda_g 27.29 mm), so 0.10 mm = 1.3 deg — inside PE42482A-X's OWN published
    13.2 deg = 1.00 mm part-to-part window (Table 3, PDF p8) and below
    ADR-0006(d)'s ~2 deg/fillet mounting term. 1.0 mm ceiling derived from
    `dtau = TC*dT*dL*t_pd`: 1 mm = 0.05 deg over 40 degC, 20 mm = 1.05 deg.
  * WHY THE MATCHED SET IS EIGHT AND NOT NINE, from the copper and not from
    taste: ANT1..ANT7 + RX2_OUT are two-pad nets at three distinct switch-pad
    radii (2.2743 / 2.0427 / 1.9164 mm — the jacks sit on a CIRCLE, the QFN
    lands on a SQUARE), giving pad-to-pad 17.7784 / 17.9725 / 18.1021 mm,
    spread 0.3238 mm = 4.27 deg. RX2_OUT lands on the SAME 18.1021 value as
    ANT3/ANT6, so including the common-mode RFC arm widens the group by ZERO.
    The RF8 radial is excluded and ADR-0006 already said why in prose ("the
    tapped path contains two resistors and a different topology, so it is
    unequal by construction"): three nets in series, `RX1_MAIN` is a T because
    it also carries J_RX1.1 (10.3533 mm away), and its phase is set by a lumped
    2 x 220 ohm cell.
  * E-NETREF 120 sites: GHOSTS 4 -> 1. `SW_VDD` -> `{net: 3V3, anchor_pins:
    ["8"]}` graded at U_SW.8 -> C_SW1.1 = 2.873 of 3.0 (P-ADJ's tightest margin
    on the board, +0.127, and the SAME number stage 5 moved C_SW1 to x 44.7 to
    achieve by hand). ABM8 `XOUT` -> `{net: XOUT_XTAL, anchor_pins: ["3"]}`
    graded at Y_XTAL.3 -> R_XTAL.2 = 3.618 of 6.0, split at the part boundary
    (MCU leg stays on RP2040's XOUT at 3.062). `SW_LS` DELETED, not re-pointed:
    GND was available and would have measured U_SW.1 -> C_SW1.2 = 6.956 mm, a
    real number about the wrong thing, so the obligation moved to audit_board I8
    (nearest GND via within 0.5 mm of the pin-1 pad centre) which also now grades
    Y_XTAL pads 2/4 at <= 1.0 mm each with DISTINCT vias. The one surviving ghost
    is KH-SMA `RF_ANT_LAUNCH`, a generic dossier name with no near-miss, waived
    with I2/I3 as its evidence.
  * K12 8/8 member names resolve against the netlist. copper_length_audit:
    `UNREACHED R-LEN : 1 of 1 group(s) could not be measured — NOT a PASS`,
    8 member nets carry no copper. That is the correct pre-route verdict.
  * P-ADJ 32/35 graded (was 30/36 — one budget deleted, two more now gradeable),
    0 exceeded. P-ADJ-UNREACHED 3/42 (was 6/43). audit_board PASS, 8 groups,
    13 measurements, I8 UNREACHED with 0 GND vias on the board and saying so.
    policy_audit FAIL=2 HUMAN=6 N-A=11 PASS=23 WAIVED=2, unchanged — the two
    fails are still R-DRC and R-THERM, which is what routing is for.
- next: generate_rules FIRST (canon R1), then KRT.

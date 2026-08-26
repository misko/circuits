# Learnings — verify/release stage (crow-recorder-central-v2 v1.0)

The harvest source (canon M9): what this board paid to learn, one entry per
lesson, each with the measured incident. Fleet-worthy items are flagged
[HARVEST] for skills/ledger promotion at seal.

1. [HARVEST] **Geometric net-merge at netlist export is a CLASS, not an
   incident.** Two instances on one converter schematic: an endpoint-on-wire
   T-junction (P5VA_4 -> AUDIO4M, port 4 lost its +5V rail) and a collinear
   overlap (MID2P -> 5V, an RC mid-node DC-shorted to the rail). Every
   downstream gate (ERC 0, DRC 0/0/0, count_parity 194==194) stayed green
   because all artifacts were self-consistent with the merged netlist. The
   antidote is label-survival: every schematic global_label must exist as a
   netlist net (03_src/check_port_nets.py, now step 0 of rebuild_reuse.sh).
   The converter needs a wire-crossing invariant upstream (skills flag).

2. [HARVEST] **Murata ferrite-bead impedance code: 3rd digit is a
   multiplier.** BLM21PG600SN1D is 60 ohm (600 = 60 x 10^0); the 600-ohm part
   is ...601... (60 x 10^1). A part.yaml was authored claiming 600R/2A/25mR
   for the 60R part and survived until the M-BOM staging catalog check
   (JLC describe row: "60Ω@100MHz 3.5A 20mΩ") contradicted it. Same failure
   shape as the R12/R30 wrong-part class: the label lies until a catalog
   source is forced to agree. Ordered part: BLM21SP601SN1D (600R, 2.3A, 60mR).

3. **P-ADJ whole-net spans conflate fan-out with local adjacency.** 5 nets
   flagged over-budget; each budget's true subject measured within a
   footprint of its target (Rg->gate 5.0mm, Cout 4.7mm, Cin 4.2mm) while the
   net bbox ran 100-160mm of ordinary rail fan-out. Waive with the LOCAL
   measurement, not the bbox; a keep_short budget on a rail net wants a
   pin-pair form (skills wish).

4. **R-THERM counts only PCB_VIA objects.** The XU316 EP is served by 16
   footprint-embedded 0.3mm PTH thermal pads (4x4 grid) — a checker blind
   spot for via-in-footprint thermal patterns; waived with the pad
   inventory as evidence.

5. **unify_zone_priorities hard-refuses the deliberate patch-pour pattern.**
   Three 5V F.Cu rects (priorities 1/2/3) over the priority-0 board-wide GND
   pour is KiCad-legal (fill priority) and DRC-gated; the pass treats any
   cross-net outline overlap as a suspected short. Dropped from the pass
   list, matching sealed usb-hub-3s-v3. The pass wants an allow_cross_net
   knob (skills wish).

6. **Order-day sourcing is a stage, not a formality.** Of 48 BOM lines: 1V8
   LDO stock 0 (ADR-0006 fallback TLV70018 promoted), FA-238 crystal family
   stock 0 across ALL variants (NX3225SA same-CL drop-in), 400k 0402 does
   not exist in-catalog (402k E96 substituted, -0.17% on the 0V9 divider),
   and the buck inductors were authored code-less ("simple_inductor").
   Authoring passives without codes defers a sourcing decision to the worst
   possible moment; the tsx now carries every code explicitly.

7. **kicad_sch_parity.py crash is now 3-strike** (ValueError unpacking, also
   hit v1.3 + pod retro-check): pinned-canonical schematic + count_parity +
   kicad-cli --schematic-parity carried the gate instead. Owned outside this
   board; do not fork-fix locally.

## v1.4 (2026-07-25) — the CPL-correction release

8. **A "fix" is a change of DIRECTION, and direction needs an INDEPENDENT
   witness.** v1.3's evidence described its own change accurately — "exactly
   these 10 rows, rotation column only" — and was still a DO-NOT-ORDER board,
   because every number in it came from `jlc_twin.jlc_offset` and the table
   that had been populated FROM `jlc_twin.jlc_offset`. Checker and checked
   shared a method (canon M1), so the diff could be perfect and the sign
   wrong. The missing artifact was cheap: ~110 lines re-deriving the angle
   from the board plus JLC's cached model with an operator proven against
   pcbnew, importing nothing from the tool under suspicion. Ship that
   re-derivation with any release whose claim is "this value was wrong".

9. **State the expected delta as a NUMBER before you look.** The v1.4 gate was
   "exactly seven changed cells, zero rows added or removed, Q1/Q2/U9
   unchanged — an eighth row means stop". That converts a review into an
   assertion a machine can fail. Eyeballing a diff that is *mostly* what you
   expected is how an off-by-one row ships.

10. **A bug that is EXACTLY 180 degrees wrong leaves a fingerprint in WHICH
    rows move.** The handedness negation is invisible at 0 and 180
    (sign-invariant) and swaps 90 with 270. So the corrupted set is precisely
    the 90/270-valued rows, and the 180-valued rows (Q1/Q2/U9 here) are proof
    of the mechanism rather than an inconsistency. When a fleet-wide numeric
    defect is suspected, partition the rows by the value the suspected
    operator cannot move — the partition is the diagnosis.

11. **"Hand-solder" was three different facts wearing one label.** v1.3's
    paperwork listed J3-J10, U1, JP_INJ and J_DBG together under
    hand-solder/consign. They are three different things: J3-J10 is a
    MEASURED catalog wall (C99* consign-only codes at stock 0, no CAD, and the
    one stocked near-match is not a land drop-in); U1 is CONSIGNED, which
    means POPULATED — JLC places it and it stays on the CPL; JP_INJ/J_DBG are
    DNP-by-design, and a catalog query proves there is no wall at all (JLC
    stocks 2.54 mm headers by the tens of thousands). `assembly.yaml`'s closed
    `reason:` vocabulary forces that separation; the prose sentence it
    replaced could not.

12. **`consigned:` needs `msl:`, and that means a datasheet read at PART
    stage.** This project's XU316 part.yaml had no `msl:` row while the
    sibling board's copy of the SAME part had one — which is exactly how
    crow-recorder-central v1.0 shipped a consigned MSL-3 SoC with zero MSL
    text in its order paperwork. Backfilled here from ds v2.0.0 s14.5 p33
    (MSL 3, 168 h, bake per J-STD-033D). A consigned reel's moisture control
    is OURS; the assembler cannot bake what nobody told them about.

13. **Check the archive's self-containment on THIS board rather than
    inheriting the neighbour's verdict.** usb-hub-3s-v3 ships an
    `fp-lib-table` pointing out of the release; the honest test is one
    command — copy `source/` alone somewhere else and run DRC. This board
    passes (0/0/0, zero `lib_footprint_issues`; both vendored libraries
    resolve via `${KIPRJMOD}` and ship inside `source/`). Ship the result as
    evidence either way; "we don't have that defect" without the run is the
    same class of inherited claim as a copied waiver.

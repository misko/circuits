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

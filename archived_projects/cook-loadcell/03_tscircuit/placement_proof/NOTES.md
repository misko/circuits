# Phase B — PLACEMENT-AS-CODE proof, cook-loadcell (ADR-0002)

**Claim under test.** Adopt tscircuit's placement (`pcbX`/`pcbY`/`pcbRotation`
in the TSX, carried in `circuit.json` as `pcb_component`) as the board placement
SEED, then let OUR audit + legalize + route certify it — so `generate_board`
shrinks to "import placement → legalize → audit" and placement lives with the
schematic.

**The real question the user flagged (golden rule 7 / honest expectation):** is
placement-in-TSX a genuine win, or does it just move the hand-work? To answer it
honestly we measured TWO seeds on the same board.

Reproduce: `bash build_placement_proof.sh` (writes only under `placement_proof/`;
never touches `04_kicad/` or releases). Renders in `verification/`.

---

## Measurement A — RAW tscircuit AUTO-placement (what you get "for free")

The authored `cook_loadcell.tsx` gives `pcbX`/`pcbY` to the **4 mounting holes
ONLY**; all **29 electrical parts are tscircuit AUTO-placed** (its layout engine).
The placer (`circuit_json_to_kicad_pcb.py`) landed those auto-coordinates into a
KiCad seed (`06_build/raw_seed.kicad_pcb`, render `verification/raw_seed_top.png`).

**Our placement gate `audit_board.py` on the raw seed: 11 FAILURES.**

| audit item | result | detail |
|---|---|---|
| I1 pads-in-outline | ok | auto-placement stayed inside the frame |
| I8 refdes-on-silk | ok | KiCad footprint refdes default to F.SilkS |
| IP decoupler proximity | **FAIL ×4** | C3 13.2mm, C5 13.7mm (budget 8), C4 15.8mm, C6 15.4mm (budget 12) from U1 — decouplers scattered to the far edge |
| IS functional silk | **FAIL ×7** | no functional captions near any J*/JP* |
| IZ / I-AN | ok | pours present; pre-route |

**`kicad-cli pcb drc` on the raw unrouted seed: 214 violations** —
`22 courtyards_overlap`, `11 pth_inside_courtyard`, **`8 shorting_items`**,
`8 solder_mask_bridge`, `2 starved_thermal`, `2 hole_to_hole`, `161 silk`
(`81 silk_overlap` + `80 silk_over_copper`); plus 40 unconnected (pre-route).

The headline is the **22 courtyard overlaps + 8 shorting pads**: tscircuit's own
layout engine reports its placement DRC-clean *against its own courtyards*, but
when mapped to the **real KiCad footprints** the parts physically collide — JST
shrouds overlap pairwise, plated pins sit inside neighbouring courtyards, and
eight pad pairs short. The render shows every part crammed into a ~28×31 mm
huddle with the connectors interpenetrating. **This confirms golden rule 7 at
scale: auto/AI placement is electrically + mechanically blind and is NOT usable
as a seed.**

## Measurement B — AUTHORED placement-as-code (the engineered floorplan in TSX)

We then AUTHORED `pcbX`/`pcbY`/`pcbRotation` for all 29 parts into
`src/cook_loadcell.tsx` — the engineered floorplan expressed as code (mapped
`tsc = KiCad_mm − center(47.5,42.5)`, y-flipped, `pcbRotation = −orient`). This
is the true Phase-B artifact: the placement seed comes from the TSX.

- **Round-trip fidelity:** `tsci build` carries every authored `pcbX`/`pcbY` into
  `pcb_component.center` verbatim; the placer reproduces the sealed floorplan
  **28/29 parts pixel-identical (max Δ 0.00 mm)**. The lone exception was **SJ1
  (Δ 1.27 mm)** — tscircuit's `<solderjumper>` reports its `pcb_component.center`
  at **pad-1, not body-center**, so the authored `pcbX` must pre-compensate half
  the 2.54 mm pitch (documented inline in the TSX). A footprint-origin-convention
  quirk, not a placement error.
- **Legalization effort (`legalize_and_silk.py`):**
  - decoupler snap-back (golden rule 7): **0 caps moved** — the engineered
    floorplan already satisfies IP by construction;
  - **1 coordinate correction** (SJ1, 1.27 mm, in the TSX) for the origin quirk;
  - silk generation (NOT geometry): **7 functional captions + 33 refdes on
    F.SilkS (0 waived) + 7 TP net labels + 33 F.Fab copies**, all collision-nudged.
- **Gate results:** `audit_board.py` **PASS (0 failures)**; reused the promoted
  KRT route `r2` (canon M3 — placement == the sealed floorplan it was routed on);
  `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` =
  **0 / 0 / 0**; board-netlist parity vs the sealed board = **0 (77/77 nodes
  identical, net-for-net, 17/17 nets)**. Render: `verification/routed_top.png`.

---

## HONEST VERDICT

**Placement-as-code is a real ERGONOMIC win, but it MOVES the placement
hand-work — it does not remove it. tscircuit's AUTO-placer is unusable as a seed.**

Three findings, stated plainly:

1. **The "free" placement is a trap.** tscircuit's auto-layout produced 22
   courtyard overlaps and 8 shorting pads against real KiCad footprints. Nobody
   can seed a board from it. Any Phase-B adoption MUST mean *human-authored*
   `pcbX`/`pcbY`, never the auto-placer's output.

2. **Authored `pcbX`/`pcbY` are the SAME coordinates `generate_board`'s
   `ANCHOR`/`SEED` dicts already hold.** Phase B relocates that hand-work from a
   Python dict into TSX props next to the connectivity. The floorplan still has
   to be engineered by a human (analog corner W, digital SE, decouplers hugging
   their IC, JST pitch clearing the mounting-hole courtyards). The win is
   **co-location + single source of truth** (placement, schematic, and netlist in
   one reviewable file, edited in the design tool), not less placement labour.

3. **`generate_board` shrinks but does not vanish.** The SILK STORY — functional
   captions, refdes de-collision, F.Fab copies, TP labels — is **not in
   tscircuit's model** and must still be generated KiCad-side. So the placement
   *dict* leaves `generate_board`, but the **legalize + silk + audit** body stays
   (it became `legalize_and_silk.py` here). That legalizer is the durable,
   reusable piece: any seed — authored-in-TSX or hand-coded — needs it to become
   audit-clean, and it is where snap-back/de-collision live.

**Recommendation: Phase B should be OPTIONAL, adopted per-board, NOT mandated
fleet-wide.**
- Adopt placement-as-code where the ergonomics pay for themselves: boards
  actively authored/edited in tscircuit, where co-locating placement with the
  schematic beats a separate Python floorplan.
- Keep hand-coded `generate_board` placement as a fully valid path; there is no
  correctness or DRC advantage to migrating a stable board.
- **Never** feed tscircuit's auto-placement into the backend as a seed.
- Promote the two Phase-B artifacts to the toolchain regardless of adoption
  breadth: `circuit_json_to_kicad_pcb.py` (the placer) and a generalized
  legalize+silk pass — both are seed-source-agnostic.
- The `<solderjumper>` (and any part whose tscircuit center ≠ KiCad footprint
  origin) needs a per-footprint origin-offset table before fleet use; on a
  33-part board it bit exactly one part, but on connector-heavy boards it will
  need handling in the placer rather than hand-compensation in the TSX.

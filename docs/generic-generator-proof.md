# Generic board generator — validation proof

`skills/kicad-pcb/scripts/generate_board_generic.py` regenerating two REAL
boards from a declarative floorplan YAML, checked against their sealed
`04_kicad` boards. Sealed boards and releases were not modified; output goes
to `06_build/proof/`.

| board | layers | parts | bespoke generator | floorplan.yaml | netlist parity | audit_board |
|---|---|---|---|---|---|---|
| cook-loadcell  | 2 | 33 | 373 lines | 111 (88 non-comment) | **0 — PASS** (77 nodes) | **PASS** (0 failures) |
| crow-array-pod | 2 | 40 | 486 lines | 136 (112 non-comment) | **0 — PASS** (90 nodes) | **PASS** (0 fails, 0 warns) |
| shitty-kitty   | **4** | 82 | 444 lines | 266 (199 non-comment) | **0 — PASS** (358 nodes) | **PASS** (0 fails, 0 warns) |

Reproduce:

    cd projects/cook-loadcell
    /usr/bin/python3 ../../skills/kicad-pcb/scripts/generate_board_generic.py 03_src/floorplan.yaml
    /usr/bin/python3 ../../skills/kicad-pcb/scripts/board_netlist_parity.py \
        06_build/proof/cook_loadcell.kicad_pcb 04_kicad/cook_loadcell.kicad_pcb

`audit_board.py` is path-hardcoded to `04_kicad/`, so it is run against a
scratch tree with the proof board copied into `04_kicad/` (see
`tests/run_tests.sh --slow`, which automates exactly this).

## Features exercised
cook-loadcell: plain rect outline, 4 mounting holes, anchors + seeds +
ring legalizer, attr fixup (`SJ*` clear exclude_from_bom), GND pours both
layers, 10 collision-nudged captions, TP labels derived from part values,
refdes de-collision with a 90-degree fallback, 8 pad-net asserts.

crow-array-pod: R6.25 concave corner-cut outline, project-local `pod`
footprint library, `pin:` glob (anchored-but-floating passives), per-pad
zone-connection override on J1's GND tails, F.Cu-solid/B.Cu-thermal split
pours, polarity `K` marks, 4 pad-net + 3 pad-order orientation asserts.

shitty-kitty: **the 4-layer / plane / isolation proof.** In1.Cu solid GND
return plane; In2.Cu SPLIT power plane — three non-overlapping,
non-rectangular pours (VIN_12V / 5V / 3V3) at priority 2, each with its own
min-fill-thickness; a rule area spanning ALL FOUR copper layers (ESP32-S3
antenna clearing); caption-only `repeat` blocks for the 24-pin electrode
legend; `bbox_override` for the module's antenna-inflated footprint bbox;
18 asserts across 4 kinds. Zone geometry is compared against the sealed
board parameter-for-parameter, not just node-for-node.

## What the 4-layer path needed that 2 layers never exercised

Both earlier boards are 2-layer with a GND pour per side and **zero
keepouts**, so three code paths shipped unexecuted. Regenerating
shitty-kitty found a real defect and two real gaps:

1. **`ZONE::SetLayer()` collapses the layer set.** `add_keepouts` called it
   *after* `SetLayerSet()`, so the 4-layer antenna keepout silently became
   an **F.Cu-only** rule area — DRC-clean, and unprotected on the three
   layers nobody inspects. Fixed by ordering `SetLayer` first and then
   *verifying the set stuck* rather than trusting it.
2. **A zone/keepout could name a layer not in the stackup.** pcbnew's `LSET`
   accepts `In1.Cu` on a 2-layer board without complaint; the copper just
   never appears. Now a hard error against `board.layers`.
3. **No way to express a module whose bbox overstates its body.** The
   ESP32-S3 footprint bbox includes the off-board antenna keepout; used as a
   legalizer obstacle it fences off ~20x19mm of live board.
   `placement.bbox_override` supplies the real body box (and refuses to sit
   on a part the legalizer may move, since the rect is absolute).

Also added: `asserts.body_offset` (which way a connector mouth faces — the
only check that catches a 180-degree flip of a symmetric part) and
`asserts.pad_beyond_edge` (an edge-launch clearing must hang off the board).
Both existed as bespoke one-offs in shitty-kitty's generator with no generic
equivalent.

Each is pinned by a known-bad fixture in `tests/t1_generate_board.py`; the
`SetLayer` ordering fix was verified to have teeth by reverting it and
watching the new gate fail.

## Determinism (M-REPRO), 2026-07-26

The generator is BYTE-DETERMINISTIC: two runs from identical source produce
byte-identical `.kicad_pcb` files. This was not always true — the values were
always deterministic (identical footprint hashes across isolated runs), but
UUIDs were minted fresh and random each run. KiCad serialises footprints in
UUID order, so the zone filler walked zones in a different order per run,
Clipper tessellated pour boundaries differently, and `island_rescue` inherited
all of it: three regenerations of identical usb-hub-3s-v3 source gave
292/294/293 vias with every value identical, and the v1.6 release could not
prove M-REPRO.

Fix: `seed_uuids()` calls `pcbnew.KIID.SeedGenerator(crc32(board_name))`
before any board object exists — KiCad's own QA hook, mt19937-backed, so the
UUID stream is a function of the seed alone (stable across runs AND machines;
no PID, clock, or platform input). Creation order was already deterministic,
so every object gets the same UUID every run. Measured 2026-07-26:

- generate stage: usb-hub 2x byte-identical (1966 objects, 1966 unique
  UUIDs); cooksense 3x byte-identical (3682/3682). Geometry unchanged vs the
  pre-fix generator (457 pads, identical sorted pad-position sha).
- full usb-hub `rebuild_fast.sh` pipeline, 3 isolated runs: vias
  **293/293/293** (was 292/294/293), DRC 0/0/0 each, and the order-independent
  VALUE-SET hashes are identical across runs — footprints 49546f42f9d7e62c,
  vias a852c9c9653e7fb7, tracks 0e6f06a9e36674be (129 fps, 908 tracks,
  1070.469 mm, 457 pads). The incident class (island-rescue via drift) is
  gone because zone/footprint UUIDs now fix the filler's walk order.
- KNOWN RESIDUAL: the full-pipeline `.kicad_pcb` files are NOT yet
  byte-identical — they differ only in the serialisation ORDER of the
  `(segment ...)` section and in track/via UUIDs, because the downstream
  stages (`route_and_stitch_generic.py` import/taps/stitch, and per-project
  post-stitch scripts) run as separate processes that still mint random
  KIIDs. Full-pipeline byte-identity needs the same `KIID.SeedGenerator`
  call at the top of each of those stages; that is a follow-up, and it must
  be coordinated because live board agents invoke those scripts.

Pinned by
`tests/t1_generate_board.py t_uuid_determinism` (known-bad, RED-verified
against the pre-fix generator). NOTE: the seed derives from the OUTPUT BOARD
NAME, so "identical source" includes the output filename — renaming the board
legitimately reshuffles UUIDs without changing any geometry.

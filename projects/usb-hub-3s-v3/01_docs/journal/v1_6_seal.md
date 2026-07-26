# v1.6 seal journal — usb-hub-3s-v3

## M-REPRO (canon M3): the sealed board regenerates from 03_src + 03_tscircuit

Method, and why it is a real test rather than a tautology: `rebuild_fast.sh`
regenerates the board FROM SOURCE ONLY — `generate_board_generic.py` from
`03_src/floorplan.yaml`, netclasses from `03_src/rules/nets.yaml`, the KRT chain
replayed from the PROMOTED `03_src/route/final_chain.kicad_pcb`, taps and stitch
from `03_src/route.yaml`, then `03_src/post_stitch_fixes.py`, then
`generate_rules_generic.py` LAST. Nothing is copied out of `04_kicad/`; the file
is overwritten from scratch. The comparison is then made against the copy already
sealed into the release.

The route is deliberately NOT re-raced here: KRT is stochastic, and canon M3 is
why the winning chain is committed as a source ARTIFACT. Reproducibility means
"the same source yields the same board", not "the router is deterministic" —
which it is not.

## Chain promotion

The v1.6 chain was re-raced (6 candidates) after R42 was added, because R42's
pin 2 lands on FB_C, a KRT-routed sense net, so the pre-R42 chain no longer
covered every pin on that net. All 6 candidates came back CLEAN (0 unconnected /
0 violations); c0/r4 was promoted to `03_src/route/final_chain.kicad_pcb`.

## What the seal verified

- DRC 0 violations / 0 unconnected / 0 schematic-parity, at `--severity-all
  --refill-zones --schematic-parity`
- A-ROT 119/119 sourced from MEASURED per-LCSC rows
- A-POS datum 119/119 graded, worst residual 0.00050 mm (Q6) vs 0.05 mm tolerance
- jlc_twin bodies mounted 119/119, exit 0, generated `missing_models.txt`
- E-INV 39 invariants + E-ADR; E-TOPO 2 rails; E-MARGIN PASS at 3 A (+244.2 mV);
  E-OFF quiescent 271 uA
- policy_audit, contracts_audit 187/0

## M-REPRO RESULT: FAIL — and it is (a) nondeterminism, not (b) an input change

Three from-source regenerations of IDENTICAL source:

    run 1 (the copy staged into the release)   292 vias
    run 2                                      294 vias
    run 3                                      293 vias

Three distinct numbers settles it. Had run 3 returned 294 again, this would have
been deterministic island rescue responding to a one-time input delta and merely
worth recording. It did not.

EVERYTHING ELSE IS IDENTICAL across all three runs — footprints 129, tracks 908,
total track length 1070.469 mm, zones 51, pads 457, nets 74. The entire delta is
island-rescue vias on pour nets: 5VA 6 -> 8 between runs 1 and 2, and one via
that MOVED BY 0.010 mm ((110.830, 46.900) -> (110.830, 46.910)) — a tessellation
boundary artifact, which is the tell.

ROOT CAUSE, CONFIRMED BY MEASUREMENT (the mechanism cooksense diagnosed):
  * generate_board_generic.py mints FRESH RANDOM UUIDs every run —
    129/129 footprint UUIDs differ between two runs of the same source;
  * KiCad serialises footprints in UUID order — the reference order differs at
    index 0 and in 129/129 positions;
  * the zone filler therefore walks zones in a different order, and Clipper
    tessellates the pour boundaries differently;
  * island_rescue keys off the resulting zone islands and inherits all of it.

THIS IS A FLEET FIX, NOT A USB-HUB FIX. Deterministic UUIDs in
generate_board_generic.py is already logged as a fleet task and was NOT attempted
here. Nothing in 03_src/ or 03_tscircuit/ can make the pipeline reproducible while
the generator randomises identity every run.

WHAT THIS DOES AND DOES NOT MEAN. It does NOT mean the board is wrong: all three
runs are DRC 0/0/0, and the extra vias are additive same-net island bonds, which
is island_rescue doing its job. It DOES mean canon M3's promise — the same source
yields the same board — is not currently true for this pipeline, so the release is
STAGED and NOT SEALED. It seals when deterministic UUIDs land and one clean
regeneration matches the staged copy.

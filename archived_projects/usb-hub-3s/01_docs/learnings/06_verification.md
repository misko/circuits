# Learnings — verification stage (usb-hub-3s, 2026-07-21)

## V-GENDER (candidate canon)
A connector's GENDER is a part fact that must be read off the drawing
TITLE BLOCK at parts stage ("AM"/"AF", plug/receptacle). A plug in a
receptacle's role passes every artifact-consistency gate because the
footprint, netlist and silk agree with each other. The KiCad official
library ships plug footprints alongside receptacles under near-identical
names.

## V-VARIANT-SUFFIX
Datasheets covering variant families (TPS2513 vs TPS2513A) put the
behavioral difference in a device-options table, not the feature list.
part.yaml gotchas must claim only what the EXACT ordered suffix does.

## V-CAPTION-NUDGE
generate_board's caption engine nudges captions off pads/silk — an
authored position is a REQUEST. For a label that must sit in a specific
tight spot, use the dict form with `nudge: false` at a grid-scanned
pad-free position, or the nudge will teleport it somewhere that fails
the very check it was added for.

## V-EXPORT-OUTDIR
export_fab_jlc with a RELATIVE outdir writes gerbers board-relative
(04_kicad/06_build/...) while drills land cwd-relative — a silently
split fab set. Pass absolute paths or check the file count.

## V-TWIN-EP-COUNT
jlc_twin fit_err returns best=none whenever a pad NUMBER's instance
count differs — every KiCad ThermalVias footprint (EP pad number shared
by via pads) triggers it. It's a naming-multiplicity artifact, not a
geometry finding: perimeter rows still pad-geom-check; adjudicate with
the EP dimension source.

## V-THERM-REAL-COPPER
policy R-THERM is closable with the tap engine's plane mode: two POFV
vias per drain paddle into a purpose-added B.Cu landing pour ({net,
from:[paddle xy], to:[1.1mm away], plane: true}). Cheaper than arguing
with the checker, and the board is measurably better.

## V-REL-FPLIB (release-contract gap, next version)
The v1.0-2026-07-21 release's source/ copy omits fp-lib-table, so a
STANDALONE DRC re-measure of the archive raises 116 lib_footprint_issues
(the board references the project-local usb_hub_3s.pretty vendored lib).
The sealed release stays as-is (its own gate evidence is in
verification/); the contract fix for the next version: source/ must
carry fp-lib-table (and the vendored .pretty it points at) so someone
holding only the archive re-measures DRC clean.

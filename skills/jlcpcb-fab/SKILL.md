---
name: jlcpcb-fab
description: Produce and verify complete JLCPCB PCB/PCBA order packages from KiCad, including Gerbers and drills, exact BOM/CPL identity, stock, assembly coverage, rotation and polarity authority, digital-twin/model registration, uploader previews, and fabrication release staging. Use for JLCPCB export, assembly preparation, order readiness, or order-side verification.
---

# JLCPCB fabrication and assembly

Produce the populated board JLCPCB will manufacture, not merely plausible
Gerbers. Start only from an exact KiCad board whose owning design/DRC/parity
gates pass. Return staged evidence to `pcb-design`; do not duplicate its seal
or publication procedure.

## Non-negotiable outcomes

- Export Gerbers/drills, BOM, and CPL from source; never hand-repair output.
- Keep BOM/CPL outside the Gerber zip.
- Bind every coded BOM row to exact per-refdes LCSC and MPN authority.
- Prove every population exception through one assembly-policy source.
- Treat catalog stock as advisory; require JLCPCB PCBA availability/allocation
  receipts at their lifecycle boundaries.
- Bind those receipts to explicit procurement limits and grade preorder cash,
  gross MOQ surplus cost, and nonrecoverable assembly excess cost.
- Enforce measured per-LCSC rotation authority before CPL export (`A-ROT`).
- Build the digital twin from JLC's CAD and exact CPL coordinates.
- Prove mounted-body and same-camera render coverage before human review.
- Grade staged bytes as JLC parses them, then capture uploader-side evidence.
- Keep design soundness separate from order readiness.

## Load only the procedure needed

| Work | Read completely |
|---|---|
| Export BOM/CPL, choose codes, check stock, rotations, uploader preview | `references/assembly-and-order.md` |
| Fetch JLC CAD, fit pads, mount models, render and debug overlays | `references/digital-twin.md` |
| Prove connector mouth/edge orientation and approve directional 3D views | `references/connector-orientation.md` |
| Census exact fab payload and run the staged assembly/process battery | `references/release-staging.md` |
| Inspect and energize a physical first article | `references/first-article-bringup.md` |

For PCB routing, geometry, DRC, impedance, or RF layout read the owning
`kicad-pcb` reference selected by `pcb-design`. For immutable release review,
seal, supersede, or publication read the owning `pcb-design` procedure.

## Stage contract

### 1. Accept the board

Require the exact board identity, layer count, declared fabrication tier,
full-severity DRC, zero unconnected items, schematic parity, and applicable RF
fabrication contract. A clean visual render is not board acceptance.

### 2. Export atomically

Use `scripts/export_jlc_package.py` with the KiCad-capable interpreter and a
fresh staging directory. Validate the zip census and CSV schemas. Reopen
outputs and promote only a complete bundle; preserve the last accepted bundle
on failure.

The exporter is authoritative about produced filenames. If a human must copy,
rename, or edit an output to reach the next gate, stop and correct the producer.

### 3. Verify exact BOM and population

Run source-identity and recipient-legibility checks on staged BOM bytes. Every
assembled line must be JLC sourced, consigned, or explicitly not assembled
with dated evidence and correct position-file exclusion. Run independent
population coverage with a nonzero denominator.

Search results are proposals. Confirm voltage, tolerance, dielectric, power,
component class, package, orientation, and exact MPN before adoption. Repeat
catalog checks as useful, but confirm critical codes before part freeze and the
complete preliminary BOM before placement in JLCPCB's PCBA interface.

### 4. Resolve rotations and polarity

`A-ROT` is active: the exporter blocks and removes stale BOM/CPL when a
placement lacks a measured per-LCSC rotation row. The footprint-name table is
advisory. Measure from board pads and independent JLC/manufacturer authority;
never derive the authority table from the twin output it will grade.

Every single-channel or disagreeing polarity/rotation case goes into
`rotation_human_gate.txt` and must be confirmed in JLC's final preview.

### 5. Prove the digital twin

Run `jlc_twin.py` with exact board/BOM/CPL, assembly policy, and adjudications.
Block transient fetch failures, mirrored fits, unadjudicated pad geometry,
model registration, polarity, or missing-body findings. Quote coverage as
mounted bodies over the CPL denominator.

Run `twin_overlay.py` on same-camera populated/bare images for every populated
side before a human render review. Debug one ref at a time with independent
pad/courtyard, model-transform, and image-difference geometry.

For edge-mounted connectors, run `P-ORIENT` after native-model registration
and before route import. Reuse the floorplan's semantic edge authority; require
machine mating-plane geometry and explicit hash-bound human directional views.

### 6. Stage order evidence

Run the fabrication payload census, source/legibility/catalog/assembly/rotation/
twin/process gates, and standalone archive rehearsal. Capture final JLC
stackup, impedance option, via-fill/cap choice, BOM mapping, rotations, and THT
assembly previews. Public capability tables do not prove the final uploader
selection.

Require an `order`-phase receipt whose exact final-BOM rows are all
`ALLOCATED`. An earlier `AVAILABLE` receipt and any catalog PASS remain
insufficient for `ORDER`.

Return exact staged-bundle identity, gate denominators, unresolved operator
items, and design/order evidence to `pcb-design`. Do not call a design
orderable while uploader, stock, stackup, or first-article obligations remain.

### 7. Authorize first power separately

When hardware arrives, derive the first-article card from the power tree,
assembly rules and actual exposed-pad footprints. Require exact staged
population, explicit exposed-pad confirmation, rail resistance with probe and
units, a bounded current limit, expected voltage/no-load current and abort
ranges. `HOLD` is not permission to continue powering. Firmware remains out of
scope unless the user separately requests it.

## Script authority

Use each script's `--help` for exact arguments; do not duplicate CLI syntax in
project documents.

| Script | Owns |
|---|---|
| `export_jlc_package.py` | Gerber/drill/BOM/CPL producer and A-ROT enforcement |
| `bom_source_check.py` | Per-refdes source identity |
| `bom_legibility_check.py` | Recipient parsing and `F-ECHO` |
| `jlc_stock_check.py` | Advisory LCSC catalog observation |
| `jlc_pcba_availability.py` | Quantity-expanded JLCPCB availability/allocation and MOQ-cost request/receipt |
| `manufacturing_readiness.py` | Selection, prelayout and final-order sourcing composition |
| `assembly_coverage.py` | Independent board-minus-CPL population coverage |
| `jlc_rotation_measure.py` / `jlc_rotation_audit.py` | Measured rotation authority |
| `jlc_twin.py` | JLC CAD fit, transforms, models, and twin renders |
| `twin_overlay.py` | Same-camera body/model/footprint registration |
| `connector_orientation_gate.py` | `P-ORIENT` mouth axis, edge/mating-plane geometry, directional evidence and approval |
| `fab_payload_census.py` | Exact fabrication payload membership |
| `via_process_check.py` | Via fabrication/process contract |
| `release_freshness_check.py` | Staged/sealed JLC evidence freshness |
| `first_article_check.py` | Staged population, exposed-pad and measured first-power authorization/HOLD |

## Human boundary

The first order requires JLC's resolved BOM echo, every flagged rotation,
layer/stackup and impedance selection, via-process selection, BOM/CPL preview,
and THT/manual assembly preview. Preserve evidence of the final choices.

When boards arrive, meter the power-entry polarity and continuity through the
protection path before applying the normal source.

## Maintenance

Keep JLC-facing mechanics here and in its references. Keep electrical/layout
rules in `kicad-pcb`, lifecycle/release/publication in `pcb-design`, and exact
CLI behavior in scripts. When JLC changes formats or endpoints, update the
producer/checker and the owning procedure together with clean and known-bad
tests.

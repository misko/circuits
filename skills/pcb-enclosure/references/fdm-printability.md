# FDM printability

Design each part around an explicit build orientation. `forbid_when_practical` means remove avoidable supports and declare any unavoidable exception; it does not mean ignoring support needs.

For new candidates, encode the exact per-part orientation, process, support
exceptions, critical attachments, load cases, and mesh-section witnesses in
the contract described by [fdm-structural-audit.md](fdm-structural-audit.md).
A prose orientation note or clean manifold check is not that contract.

## Orientation

- Print base and lid on broad exterior faces when this leaves cavities, grooves, and insert pockets open upward.
- Print captured panels flat when connector features remain dimensionally useful in that orientation.
- Orient the insert coupon exactly like the production boss.
- Avoid cosmetic orientation choices that weaken screw columns or bridge large roofs.

## Support-free geometry

- Use chamfers, arches, teardrops, or gradual overhangs instead of horizontal circular ceilings.
- Keep bridges short and unobstructed; add ribs or split the part when a long roof is unavoidable.
- Open blind recesses toward the build direction where practical.
- Keep panel-capture grooves accessible rather than forming trapped support channels.
- Do not put support scars on mating lips, insert bores, connector faces, or sliding panels.

## Feature sizing

Treat minimum wall, nozzle multiple, hole compensation, elephant foot, panel clearance, and lip clearance as process-dependent validation dimensions.

- Prefer walls that resolve into stable perimeter counts for the selected nozzle.
- Give bosses enough radial material after the actual printed/recess diameter.
- Keep narrow slots at least printable with the chosen extrusion width.
- Add bottom-edge relief where elephant foot would block board drop-in or panel insertion.
- Use fillets or generous roots at posts and tall walls to reduce layer-splitting stress.

Do not rely on nominal CAD size for press fits. Qualify inserts and critical
sliding fits with coupons. Consult the repository-wide
[fit and tolerance registry](../../../docs/enclosure-fit-registry.md) to centre
the first coupon on comparable evidence, while preserving feature class,
process, and evidence-grade distinctions.

## Vents and thermal features

Place vents from a declared heat-flow and safety plan, not as decoration.

- Keep slots printable in roof orientation and away from screw columns and thin edge bands.
- Preserve finger/tool protection and prevent conductive debris from falling onto hazardous nodes when relevant.
- Avoid vent patterns that turn the lid into weak parallel strips.
- Ensure vents do not undermine splash, dust, RF, or airflow assumptions the product actually needs.

High thermal risk requires declared ventilation and physical soak evidence. Moderate or high risk requires a physical soak in the current verifier.

## Pre-print review

Before committing a full print:

1. Generate every declared STL and require a single, closed, nonzero-volume connected component per part.
2. Run the FDM/structural audit over the exact printable census. Reject a
   floating/below-bed orientation, stale mesh, missing attachment/load census,
   weak critical section, or unsupported flexure exception.
3. Render the assembled design and inspect seams, mirrored sides, posts, panels, vents, and cable approach.
4. Slice every orientation with the intended profile; inspect layer preview for unsupported islands, excessive bridges, thin walls, and accidental gap fill.
5. Print the insert coupon and any connector/panel fit coupon that materially reduces risk.
6. Re-run generation and every receipt after changing any authored dimension.

Mesh manifold checks do not prove slicer quality, strength, tolerance, or support freedom. Preserve slicer screenshots or settings when they support a physical test record.
The current deterministic adapter reports self-intersection, local-thickness,
printer build volume, overhang/support, and slicer/toolpath checks as
`INCOMPLETE`; do not summarize that receipt as an FDM pass.

# Independent RF PCB review protocol

Run after routing is stable and immediately before layout seal. This is a
distinct review from the RF schematic phase: a correct topology can still fail
through launch geometry, return-path discontinuity, coupling, asymmetry, or an
incorrect stackup model.

## Independence and input

Use a fresh-context reviewer who did not place or route the board. Give only:

- `03_src/rules/rf.yaml`, stackup source, field-solver evidence, and RF ADRs;
- exact `.kicad_pcb` artifact named by `rf.reviews.pcb.artifact`;
- relevant footprints/datasheets/reference layouts;
- the exact `rf_realized_bundle` manifest (including its bounded fence report),
  plus machine reports for DRC, copper length, landability, and
  inter-footprint pad separation.

Exclude prior review conclusions, journals, STATUS, and dispositions.

## Required examination

For every port/cross-section/claim, measure rather than infer:

1. launch footprint and pad geometry against the connector/vendor land pattern;
2. realized width, gap, copper thickness, mask state, reference layer, and the
   exact stackup tuple used by the solver;
3. continuous return current beneath the whole path; no splits, voids, plane
   changes, antipads, or unrelated routing that forces a detour;
4. via count, transition geometry, nearby return vias, fence pitch, fence end
   effects, and edge clearance using the declared guided-wavelength bound;
5. routed copper length/spread, topology, symmetry transform, and discontinuity
   inventory for phase-coherent paths;
6. spacing/coupling to digital clocks, switching nodes, other RF arms, board
   edges, shields, mounting metal, and connector bodies;
7. RF component placement/orientation against the vendor reference layout;
8. no copper touch/overlap between separate footprints and no foreign-pad paste
   intrusion (`P-PADSEP`), including hand-soldered modules.

## Output contract

Archive the review at the path declared in `rf.yaml` with:

    review_kind: RF_PCB
    subject: <project + exact board>
    reviewer: <identity/model>
    independence: independent-from-design-author
    source_commit: <full 40-character SHA>
    artifact_sha256: <SHA256 of exact .kicad_pcb>
    evidence_sha256: rf_realized_bundle <SHA256 of exact bundle.json>
    design_verdict: SOUND | DEFECTIVE
    requirement: RF-PCB-... PASS | FAIL

There is one `requirement:` line per contract ID. Run
`rf_contract_check.py --require-review schematic --require-review pcb`; any
missing/failed requirement, stale artifact/evidence hash, or defective verdict
blocks layout seal. Legacy contracts omit the evidence row.

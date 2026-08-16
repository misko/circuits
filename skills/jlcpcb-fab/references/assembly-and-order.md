# JLCPCB assembly and order procedure

Use this procedure to produce BOM/CPL data, prove exact part identities and
rotations, check stock, and perform the human uploader review.

## Contents

1. Deliverables
2. Export and source-identity sequence
3. Part specification and stock
4. Population and assembly coverage
5. Rotation and polarity authority
6. Uploader-side human checks

Policy/gate IDs owned here: `A-BUY`, `A-POL`, `A-POP`, `A-POS`, `A-ROT`,
`A-STOCK`, `F-ECHO`, `F-ENCODE`, `F-LEGIBLE`, `F-MPN`, `F-WORDS`, `M-PROV`,
`POLARITY-CHECK`, `POLARITY-FIT`, and `ROT-DB-SUGGEST`.

## 1. Deliverables

| Upload slot | File | Required content |
|---|---|---|
| PCB | `<board>_gerbers.zip` | Copper, mask, paste, silk, edge cuts, PTH and NPTH drills; no BOM/CPL |
| Assembly BOM | `bom.csv` | `Comment,Designator,Footprint,MPN,LCSC` |
| Assembly CPL | `cpl.csv` | `Designator,Val,Package,Mid X,Mid Y,Layer,Rotation` |

Use Protel extensions with Gerber attributes. Accept KiCad-version-dependent
inner-layer extensions and optional job-file absence. Keep plot/drill origins
consistent. Use the exporter rather than hand-renaming or hand-copying files.

Group coded BOM rows by `(LCSC, footprint)`, never only by value/footprint.
Distinct catalog codes remain distinct even when their displayed values match.
Uncoded assembly exceptions remain explicit rows until assembly policy proves
why they are not machine sourced/placed.

## 2. Export and source-identity sequence

1. Require the KiCad audit, full-severity DRC, unconnected, and schematic
   parity gates to pass on the exact board.
2. Export with `export_jlc_package.py`; use the KiCad-capable Python
   interpreter. The exporter reads per-refdes LCSC identity from Circuit JSON
   and the part dossiers.
3. Run stock verification/search and the specification-confirmation pass.
4. Adopt only verified identities in source; re-export rather than editing CSV.
5. Run `bom_source_check.py` against BOM, Circuit JSON, and dossiers.
6. Run `bom_legibility_check.py` on staged bytes.
7. Run population, rotation, stock, twin, render, via-process, and payload
   coverage gates before sealing.

`bom_source_check` proves semantic identity. `bom_legibility_check` proves the
recipient can parse what was written:

- `F-MPN`: coded rows carry MPN and LCSC from dossiers or the vetted passive
  ledger, and independent resolution paths agree;
- `F-WORDS`: no source placeholder or LCSC code masquerades as Comment;
- `F-ENCODE`: BOM decodes equivalently under UTF-8 and CP936 expectations.

The exporter enforces these constraints; the staged check independently
regrades the actual upload bytes. A manual repair is a producer defect. Stop,
fix the exporter/source, and regenerate.

## 3. Part specification and stock

Search suggestions match strings and packages; they cannot prove voltage,
tolerance, dielectric, power, polarity, orientation, or exact IC identity.
Before adopting a code verify:

- ceramic voltage and effective capacitance under bias;
- resistor tolerance and dissipation;
- electrolytic/polymer voltage, ripple, height, and diameter;
- exact IC/diode MPN or a deliberately accepted equivalent;
- connector series, pin count, gender, and orientation;
- component class—NTC/PTC/fuse/bead is not a generic resistor.

Run stock verification with a JSON sidecar and parse the final verdict. Require
stock for board quantity and repeat on order day. A missing/unparseable verdict
fails. Treat the unofficial endpoint as network work with polite serialization,
backoff, heartbeat, and deadline; fall back to a current catalog mirror or
manual JLC search when unavailable.

Escalate a part absent from JLC in this order:

1. select a placeable equivalent;
2. consign it—still placed, remains in CPL, with MSL/handling declaration;
3. declare a dated, evidenced `not_assembled` disposition and exclude it from
   position files.

Never leave an uncoded part on the CPL. Never use a fake catalog code.

## 4. Population and assembly coverage (`A-POP`)

Run `assembly_coverage.py` against the staged archive. It independently
re-derives board population minus CPL and must not reuse exporter filtering
logic. Every footprint is one of:

- JLC sourced and placed;
- consigned and placed;
- declared not assembled with closed-vocabulary reason, dated evidence, and
  position-file exclusion;
- board-only mechanical item.

Keep the population declaration only in `03_src/rules/assembly.yaml`. Generate
manifest summaries from it. A hand-typed `--also` list or release note is not a
second population authority.

Ship coverage and stock sidecars in verification with explicit denominators.
`0 findings` without a population denominator is not assembly evidence.

## 5. Rotation and polarity authority (`A-ROT`, `A-POL`, `M-PROV`)

The exporter currently enforces A-ROT. It exits nonzero, deletes stale BOM/CPL,
and writes `rotations_unsourced.csv` when any placement lacks measured
per-LCSC authority. The footprint-name database is advisory only.

Clear an unsourced placement by:

1. Run `jlc_rotation_measure.py BOARD REF=LCSC --row`.
2. Compare numbered-pad fit and numbering-free polarity/orientation channels.
3. Validate against the manufacturer terminal/pin drawing and JLC's own cached
   footprint/model.
4. Add one measured row to `jlc_lcsc_rotations.csv` with independent evidence.
5. Run `jlc_rotation_audit.py --table`.
6. Re-export the CPL before sealing.

Never populate rotation authority from `jlc_twin`'s fitted offset or from a
table derived by the checker being graded. A symmetric footprint exemption is
measurement of pad/graphics symmetry, not a name heuristic.

Every ref listed in `rotation_human_gate.txt` must be checked in the JLC order
preview. This includes single-channel polarity cases, disagreements, THT
operator orientation, and bottom-side placements. Preview review is an
independent downstream backstop, not the primary source of rotations.

## 6. Uploader-side human checks

The first order of a board requires evidence captured from JLC's resolved UI:

1. Upload Gerber zip, BOM, and CPL in that order.
2. Save JLC's resolved/matched BOM table and run the `F-ECHO` comparison. A
   redirected LCSC code is a finding; zero overlap means the wrong table was
   saved.
3. Confirm every `rotation_human_gate.txt` row in the 2D/3D preview.
4. Capture layer count, stackup, controlled-impedance choice, via-fill/cap
   selections, BOM mapping, CPL rotation, and THT/manual-assembly previews.
5. Re-run stock on order day.
6. Confirm DNP semantics and that no real part was excluded by a ref/value
   naming heuristic.

Re-uploading BOM can reset matching/DNP choices; CPL re-upload changes
placements. Record the actual final previews. Do not claim `ORDER` until these
operator-side facts exist. When boards arrive, verify power-entry polarity and
continuity with a meter before applying the normal source.

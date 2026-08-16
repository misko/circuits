# JLC digital twin and model-registration procedure

Use this procedure before every order and whenever a 3D body, footprint,
rotation, or adjudication changes. The twin represents JLC's CAD mounted at
the CPL coordinates; it does not replace the board or datasheet authority.

## Contents

1. Inputs and bounded fetching
2. Pad correspondence
3. Mount and transform rules
4. Adjudications
5. Body and model coverage
6. Same-camera render registration
7. Debugging a disjoint overlay

Gate IDs owned here: `A-RENDER`, `MODEL-REG`, `MODEL-SELF`, `NO-BODY`,
`PAD-GEOM`, and `PAD-MISMATCH`.

## 1. Inputs and bounded fetching

Run `jlc_twin.py` with the exact board, staged BOM/CPL, assembly policy, and
adjudication register. Fetch JLC footprint/model data per LCSC into a reusable
cache. Classify transient fetch failures as `FETCH-FAILED`, distinct from
`NO-CAD`, and block until retried or independently proven absent.

Do not parallelize a rate-limited fetch burst. Retry with backoff and heartbeat
and retain already fetched codes. A partial twin cannot pass by shrinking its
denominator.

## 2. Pad correspondence

Fit JLC pads to board pads over quarter-turn rotations and mirror candidates.
Use physical pad numbers and report:

- whole-pattern residual and next-best margin;
- mirror result;
- per-pad multiplicity/alias state;
- pairwise pad-distance disagreement (`PAD-GEOM`);
- independent polarity/orientation channel for symmetric two-pad parts.

A mirrored best fit is critical. `PAD-GEOM` is rotation/translation invariant
and blocks until the footprint is reconciled with the manufacturer land
pattern. Naming differences should use an evidenced `pad_alias` so coverage is
restored rather than waived.

Use `mount_anchor` only when a one-to-many naming scheme makes full fitting
impossible and one unique physical datum plus angle is independently proven.
An anchor is not a model nudge.

## 3. Mount and transform rules

Use one named transform implementation for each frame conversion and pin it to
an external authority:

- board pads through pcbnew for footprint-local ↔ board coordinates;
- asymmetric rendered fixtures through `kicad-cli pcb render` for model frame;
- explicit tests at 0, 90, 180, and 270 degrees.

Mount around the unweighted common-pad centroid unless an evidenced unique-pad
anchor applies. Keep model-local and board-frame offsets distinct. Prefer
`board_dx`/`board_dy` in adjudications and verify the tool's local/board echo.
Apply model rotation and mount offset through the same canonical operator.

Never validate a transform only at 0/180 degrees; sign errors are invisible
there and fail exactly at 90/270. Never treat an inverse mapping as suspect
because its formula resembles a previously wrong forward mapping—grade the
frames and authority, not text similarity.

## 4. Adjudications

Keep findings and mechanisms separate:

- `pad_alias`: numbering convention only;
- `mount_anchor`: independently proven unique datum;
- `model_rot_z`: model orientation correction, only with render/terminal
  evidence against JLC's own model orientation;
- `board_dx`/`board_dy`: measured board-frame body correction;
- explicit dispositions for `PAD-GEOM`, `MODEL-SELF`, `MODEL-REG`, polarity,
  and true missing CAD.

Account for a position delta by mechanism. A land-pattern shift cannot be
described as bbox asymmetry or fit residual. One waiver cannot discharge two
independent obligations. Preserve the raw failed fit in evidence.

Measure body-vs-pad shifts from populated-minus-bare image differences rather
than color thresholds. Exposed pads, leads, silk, and solder mask do not have a
stable universal color. Diff before/after renders to prove an applied nudge.

## 5. Body and model coverage

Generate six populated views, a navigable twin board, and same-camera bare
top/bottom views. Independently verify every CPL designator resolves to a
nonempty 3D file. Generate `missing_models.txt`; never hand-author it.

Report `bodies mounted: N/M`. `PAD-MISMATCH`, a fetch waiver, or a large number
of findings does not prove mounted-body coverage.

Run model-to-own-footprint (`MODEL-SELF`) and mounted-model-to-board
(`MODEL-REG`) checks. Both block when unadjudicated, but bbox metrics are broad
detectors rather than rotation authority. For an asymmetric connector, a body
center can legitimately differ from the courtyard center. JLC's own footprint
model transform plus visibly aligned leads/pins outranks a tempting 180-degree
bbox improvement.

## 6. Same-camera render registration (`A-RENDER`)

Run `twin_overlay.py` after twin generation and before human render review.
Use populated and bare images from the exact same board, camera, projection,
crop, and resolution. Run each populated side; reject perspective views,
filename/side mismatches, dimension mismatches, and sides without usable
courtyards.

The overlay has three independent geometric concepts:

1. board footprint/courtyard expectation;
2. transformed 3D model expectation;
3. measured populated-minus-bare body pixels.

Render each box/shape separately and in a combined overlay with a legend,
coordinate frame, component ref, LCSC, rotation, expected/mounted/measured
centers, and deltas. Do not assume one box should always enclose another:
courtyard, pad pattern, model bbox, and visible-metal/body pixels describe
different physical extents. Their centers and relevant mating/contact regions
must agree within the declared criterion.

Read coverage as well as verdict. Name every unresolved component and reason.
A component expected to be measurable but not extracted is a failure, not an
omission.

## 7. Debugging a disjoint overlay

When a connector appears outside its pads or colored boxes are disjoint:

1. Pick one ref; do not debug the whole panel at once.
2. Reopen its footprint, pads, courtyard, CPL row, JLC model transform, and
   adjudication.
3. Render bare and populated views at high resolution with identical camera.
4. Draw pad/courtyard, transformed-model, and measured-diff geometry from their
   independent sources.
5. Print all coordinate-frame conversions and 0/90/180/270 fixture results.
6. Check that the mount uses common physical pad numbers or the declared anchor.
7. Check that expected geometry consumes the same final adjudication used to
   build the twin without deriving expectation from rendered pixels.
8. Change one transform/nudge source, rerender, and measure the before/after
   centroid shift.

Do not fix a render by moving the real footprint unless independent PCB and
mechanical evidence says the footprint is wrong. A render/model failure and a
board placement failure are different dispositions.

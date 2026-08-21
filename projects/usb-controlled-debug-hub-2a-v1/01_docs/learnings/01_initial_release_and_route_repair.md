# Initial release and route-repair harvest

Date: 2026-08-21

## What worked

- The source-owned floorplan, route declaration and deterministic stitcher can
  reproduce the manufacturing board without manual KiCad edits.
- Native KiCad DRC/parity, critical-pair connectivity, copper-length and
  reference-plane checks now agree on the same rebuilt board.
- Semantic connector-orientation approval survived a byte-nondeterministic
  render refresh because the connector subject itself was unchanged.

## What cost time

- The first release admitted high-speed checks as `N-A`, allowing missing USB
  declarations to appear inside an otherwise green route summary.
- The stitcher's internal completion report was not equivalent to native KiCad
  DRC. Native DRC exposed geometry defects that required source-level repair.
- A post-stitch manufacturing board was briefly treated as a route seed. The
  resulting prune/stitch cycle could remove authored seed copper; the
  pre-route-base comparison was the check that exposed the artifact-role error.
- Filled-zone islands and inner-layer obstacles were discovered late, after
  expensive routing iterations.
- Old mutable release-staging trees inside the project produce advisory
  GG-SHADOW findings even when the live project source is selected correctly.

## Carry-forward rules

1. Required high-speed checks need non-empty declarations and independent
   evidence; `N-A` is not acceptance.
2. Always run native DRC/parity on the exact saved post-stitch board. An
   internal router/stitcher clean result is not a substitute.
3. Keep pre-stitch route authority and post-stitch manufacturing output as
   distinct typed artifacts, and reject an import whose role is wrong.
4. Check filled-zone connectivity and reference-plane obstacles before the
   expensive stitch phase.
5. Carry connector approval by semantic subject identity when render bytes are
   nondeterministic; never infer approval from image similarity.

    date: 2026-07-24
    subject: smc0985-cooksense interposer v1.0 (pre-seal staging)
    reviewer: render-review (fable-medium fresh-context agent, zero design context)
    context-given: renders + twin + missing_models + CPL only
    verdict: PASS-WITH-NOTES

# Fresh-context RENDER REVIEW — interposer v1.0 (verbatim)

| # | Finding | Severity | Evidence |
|---|---------|----------|----------|
| 1 | No silkscreen pin-1 marker (numeral/arrow/chamfer) on either hand-soldered ZIF (J_MEMBRANE, J_CN1_JUMPER). Pin 1 is indicated only by the square THT pad, which is invisible once the connector body is seated. The 10FDZ-BT outline box is symmetric on silk, so a reversed insertion is plausible during hand assembly. | P2 | render_front_bare.png, twin_top.png |
| 2 | TP labels (TP_M_*, TP_C_*) are centered text lines between the two test-pad rows, not per-pad callouts. Mapping label to pad requires counting across 10 pads with a staggered two-line scheme. Ambiguous for probing; miscount by one pad is easy. | P2 | twin_top.png |
| 3 | Back side carries zero silkscreen — no board ID, version, or orientation cue when viewed from the bottom (where all THT soldering happens). | P2 | render_back_bare.png, twin_bottom.png |
| 4 | J_KEY_MATRIX refdes silk sits well left of the connector near the board edge; legible but at oblique angles it clips under the body. Minor. | P2 | twin_iso_nw.png |

Non-findings verified (not defects): "TR_C_U5" is a rendering artifact (pdftotext confirms TP_C_U5); J_KEY_MATRIX orientation correct for side-entry cable exit off the left edge; ZIF pin counts 10 each; unplated locating holes adjacent to pin 1 intentional; middle pads routed on back layer; all pads have mask openings; no pads off-board; no mirrored connectors; no silk-over-pad collisions.

Verdict: PASS for release, no P0/P1. Four P2 assembly-legibility items, #1 the most worth fixing since both ZIFs are the board's entire function.

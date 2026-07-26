# Render review — cooksense v1.3, 2026-07-26

**Status: renders REGENERATED for v1.3; the narrative render review is NOT
re-run.** Declared, not silent.

## What is current

`render_top_bare.png` and `render_bottom_bare.png` were regenerated from
this archive's board on 2026-07-26 (kicad-cli pcb render, 2400x1400). The
previous pair were **v1.1 images** and showed `J_CONTACTOR` at the south-east
corner — a connector that does not exist on this board, and precisely the
thing ORDER_README section 6 item 17 asks the reader to confirm is ABSENT.
Shipping them would have set a reader against the document.

`twin_top.png`, `twin_bottom.png`, `twin_iso_nw.png`, `twin_iso_se.png`,
`twin_edge_east.png`, `twin_edge_west.png` are jlc_twin's mount of JLC's OWN
3D models on our board — a preview of what JLC's viewer will show.

## Machine checks over the same artifacts, all green

- silk: refdes visible on 216/222 parts, 6 waived to F.Fab; 2 crowded captions.
- the ADR-0012 safety silk is present and was verified on the board:
  the two-line mounting-hardware caption, `NYLON HW` beside all four holes,
  and `J_ISOLOOP (SE CORNER) = ISOLATED 30V CONTACTOR LOOP -- NOT SELV`.
- board revision silk reads `cooksense  SMC0985KS  sidecar v1.3` (it read
  v1.2 until 2026-07-26; both red-team lenses caught it).
- DRC silk classes (silk_over_copper, silk_edge_clearance, silk_overlap,
  text_thickness) are policy-ignored per apply_drc_policy.py and documented
  there; every other DRC class is 0.

## Limits, stated

No fresh human-equivalent narrative render review was run for v1.3. Silk
legibility, courtyard/body plausibility and the JLC preview comparison are
covered by the machine checks above plus the ORDER_README section 6 human
gate, which is a REQUIRED order-day step and is where a human looks at the
rendered assembly for real.

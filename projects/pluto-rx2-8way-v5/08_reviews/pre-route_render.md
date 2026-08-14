subject: Pluto RX2 8-Way v5 exact-board manufacturing-twin renewal with J12
date: 2026-08-14
reviewer: Codex fresh-context placement-render reviewer
context-given: current corrected v5 board and manufacturing twin only
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 3fc9efc86e75025084e7b0a4555e7417adfa6f3a07c22129de7ca7fc6b6ff9dd
design_rules_sha256: f5837640a458d8dfeb85e076ae7b501c87a30d3c880be0e44efe480d303299d8
bom_sha256: 6583037303ee74a7d569563c11034ad375e4c351c9f5f503b8dd206abaca5523
cpl_sha256: ae54c2d6efd0e6d2a8b4b792d56307ba197d9dbb87b8709c319a17e0d10c9ff0
twin_top_sha256: d297f016fa636fba0ed30c81cff37152c8519762d41dc58cde26b36413fa0efe
a_render_report_sha256: cd8a7c57d6d56bb070f04b984bd54733effd9cde810da2a06a686d9a492df16d

# Fresh exact manufacturing-twin review

## Verdict

**SOUND / DO-NOT-ORDER.** The current top, isometric and edge renders show all
29 assembled bodies. The independent overlay measures all 14 bodies large
enough for its pixel model within 1.00 mm and explicitly names the 15 bodies
below its resolution floor. P0/P1/P2 board findings: none.

U4 is visibly close behind J1; U3/C1/C2 form a compact collision-free bypass
cluster. D1, U1 and keyed vertical J11 are accessible. Five north, two west
and two east SMAs face outward with clear mounting holes and visible THT tails.
Operational labels remain readable and BOM/CPL cover 29/29 placements.

The supplier twin cannot by itself prove the SMA/J11 lead fit because its pad
numbering/model-registration conventions differ from the manufacturer lands;
the overlay reports that limit rather than crediting it. Manufacturer drawings
and exact realized drills remain authority. Order-day preview must still
confirm D1 polarity, U3 and all unsourced rotations, JLC's resolved BOM echo,
and the retained manufacturer-vs-supplier land adjudications. Those are
explicit pre-order gates, not placement-stage defects.

Blocking findings: none.

## Targeted rule renewal — unchanged placement/render subject

The source board, BOM, CPL, populated-twin, overlay and all exact hashes above
are unchanged. The new rule semantics affect only derived pre-route dogbones
and an executable router wave guard; they do not move, rotate, populate or
re-model any component. Fresh exact-r0 inspection found no collision, edge,
hole or via-in-pad defect and retained the same connector access and outward
SMA orientation. P0/P1/P2: none. The placement/render verdict remains
**SOUND** under the exact current design-rule digest bound above; final routed
copper and order-day previews remain outside this verdict.

The subsequent widened U2/resistor escape renewal remains derived copper only:
the exact source-board, BOM, CPL, twin, component positions, rotations and
models are unchanged. Its fresh DRC and via census expose no body, connector,
edge or assembly-process conflict. P0/P1/P2: none; the current digest remains
**SOUND** for placement/render scope.

The final R3.1 rail dogbone is likewise derived copper outside the resistor
land; it changes no component, placement, rotation, body or access envelope.
Fresh exact prep/DRC finds no assembly or collision defect. P0/P1/P2: none;
placement/render remains **SOUND**.

The post-route-cleanup digest changes neither the track-free board nor any
body, model, position, rotation, connector access, BOM/CPL or render subject.
It removes unused derived barrels and prevents two stitch vias from entering
the authored fiducial copper/mask envelopes. Fresh targeted review reports
P0/P1/P2 = 0/0/0; placement/render remains **SOUND**.

The final same-net via-contained bridge is derived copper only and changes no
component/render subject. P0/P1/P2: none; **SOUND**.

## 2026-08-14 focused J12 manufacturing-twin renewal

The exact-code JLC twin mounts all 30/30 populated bodies. J12 is a visible
vertical two-pin header seated over its two plated holes between J11 and J1;
the top and isometric views show clear probe/lead access and no body collision.
The same-camera A-RENDER independently measures J12 at 0.172 mm centre delta
and 0.176 mm outward excursion, both below its 1.00-mm limit, and reports
`MODEL-REG-OK` at the footprint courtyard. The full overlay passes with 15/15
resolvable bodies measured, 15 smaller bodies explicitly named below the
pixel-resolution floor, and no resolvable-but-unmeasured or no-model refs.

The measured exact-part rotation row is now present for `C225477`; the BOM and
CPL are complete at 14 coded lines / 30 placements without an unsourced-
rotation escape. J12's plastic body and identical square posts are physically
180-degree symmetric, so the JLC preview must still confirm its placement and
the board's +5V/GND silk before first power. P0/P1/P2 findings: none;
**SOUND / DO-NOT-ORDER** remains the verdict.

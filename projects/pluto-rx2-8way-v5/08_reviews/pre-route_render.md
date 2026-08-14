subject: Pluto RX2 8-Way v5 exact-board native-model registration renewal
date: 2026-08-14
reviewer: Codex fresh-context placement-render reviewer
context-given: current exact board, native model hashes and independent footprint geometry only
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 3fc9efc86e75025084e7b0a4555e7417adfa6f3a07c22129de7ca7fc6b6ff9dd
design_rules_sha256: 70af3e20c1338c9d83b96348de0f3193434e387c39241ba59cd28c73a8acfb79
bom_sha256: 6583037303ee74a7d569563c11034ad375e4c351c9f5f503b8dd206abaca5523
cpl_sha256: ae54c2d6efd0e6d2a8b4b792d56307ba197d9dbb87b8709c319a17e0d10c9ff0
native_top_sha256: e90bdc33960f99058e637fc27f6adca416323d54e776da60e3978c1533d8885f
native_registration_overlay_sha256: b1dce9d0083ac11fc5eda99baf5252dc66acf15201b520312c51e8c6ee473231
a_render_report_sha256: 7147474945ccf0706b668178dd5d128b0b65e4a72bb91d153820e394fbce7019

# Fresh exact native-model registration review

## Verdict

**SOUND / DO-NOT-ORDER.** `P-MODEL` resolves 30/30 fitted bodies. The new
independent `P-MODEL-REG` receipt uses the exact source board and the
provenance-bound native Amphenol STEP, SHA-256
`17cbdea22e6ca94e56fb0facf4c7642df6b57fb94bc9835af2bbe51b7e712aba`.
It measures all nine J2-J10 instances: pink native-model pixels agree with the
green F.Fab expectation, both remain inside the orange F.CrtYd within the
0.25 mm raster tolerance, and 45/45 cyan drilled attachment centres lie
inside their own rendered body. P0/P1/P2 board findings: none.

U4 is visibly close behind J1; U3/C1/C2 form a compact collision-free bypass
cluster. D1, U1 and keyed vertical J11 are accessible. Five north, two west
and two east SMAs face outward with clear mounting holes and visible THT tails.
Operational labels remain readable and the exact board contains all 30
intended placements, including bench header J12.

The earlier supplier-WRL overlay is explicitly withdrawn as SMA physical-
registration evidence. Its green expected box and pink measured pixels were
both derived from the same internally misregistered converted WRL, so they
could agree while remaining several millimetres disjoint from the courtyard
and attachment field. The catalog twin remains useful for JLC code, land and
drill comparison; it cannot override the native STEP/drawing registration.
Order-day preview must still confirm D1 polarity, U3, J12 and all rotations,
JLC's resolved BOM echo, and the retained manufacturer-vs-supplier land
adjudications.

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

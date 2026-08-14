subject: Pluto RX2 8-Way v5 corrected exact-board manufacturing-twin renewal
date: 2026-08-13
reviewer: Codex fresh-context placement-render reviewer
context-given: current corrected v5 board and manufacturing twin only
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: bdb0df87886cc15ed8a3ae2aee53c97f4a4cfd49734558967240816c5c73a22e
design_rules_sha256: 442edd6040f0b990f94a76f0f21d702503c0ba365fe6c5464d55f1842ab6999e
bom_sha256: 7b01a6d1fa70ae7187c5ada14a963894acca97fa4a7c893df6eba447d8a06c65
cpl_sha256: 0eab823cfe6eaa8c087d7cc429334f524a9d6e60f3751d02567c3b340d3415e1
twin_top_sha256: be7642e39dcea07fd6dac8b0452069758478d92f4c138ddae6b059d79237c1e8
a_render_report_sha256: e5a2c94eb3b4b0df49ba04dd05bcd4f05b348bf212d802deaa7bb5403d0ee4be

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

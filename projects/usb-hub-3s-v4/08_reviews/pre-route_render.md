subject: usb-hub-3s-v4 exact placed board a8404ae41e79
date: 2026-08-11
reviewer: Codex root, orthographic/isometric human PCB readability and mechanical-access pass
independence_limit: same task owns design and review; exact render hashes prevent stale-artifact substitution, but external-human independence remains a declared process boundary
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: a8404ae41e79fb12a9428e40100be15e66aa58a752e795845e6920c0d083160b
design_rules_sha256: 44e0cf9caa8eb833647413b7f8af90907852b9fcee18efbc54081117af9e5cd6
top_render_sha256: 4ef4a6a13836f11027ce47ce72b61a1f8769969ec618e448d0e352b22b7acc6a
iso_render_sha256: d5fbaa1a4d35a5131ce024b5c06ccddf335b35efcc4561bcea39e388a83809d4

# Pre-route render review

## Verdict

The exact placed board is SOUND to proceed to routing under the human-render
lens. The images clearly show the intended left-to-right partition: protected
3S input, USB-A converter, three repeated protected USB-A power cells, and the
separate Type-C converter/controller cell at the lower edge. `POWER ONLY — NO
USB DATA`, the three 5 V/2 A port labels and the 5 V/3 A NO-PD label are
prominent. Input polarity, master switch state, user-fit 10 A fuse warning,
revision and test-point identifiers are readable.

All four mounting-hole approaches and three fiducials are unobstructed. The
USB-A mouths face east/outward and J5 sits on the south edge. Courtyards,
manufacturer edge datums and pad-to-outline measurements show clear mating
access. The connector, fuse and module cells are visually distinct; no wrong-
board artifact, doubled footprint, clipped land, body-envelope overlap or
silk-over-pad defect is visible.

## Declared render limits

Most project-local exact footprints do not carry a loadable 3D body, so these
renders deliberately receive no credit for component-body registration,
height, polarity marks or JLC catalog-model rotation. Pad, hole, courtyard,
fab, edge and silk geometry are graded from the exact board; body registration
remains a mandatory JLC order-preview check. Absence of a rendered body never
means the component is unpopulated.

The generic silk placer reports two conservative ownership degradations:
`U1` is mathematically nearer C7 and `U2` nearer R13. The orthographic render
still makes both module designators visually unambiguous, and exact copies are
present on F.Fab. Moving the pin-local capacitors/resistors merely to satisfy
the centroid heuristic would worsen electrical placement, so no layout change
is justified. All 76 designators are present; none is waived or hidden.

There is still no routed copper or production DRC evidence. The render verdict
does not authorize fabrication or assembly.

design_verdict: SOUND
order_verdict: DO-NOT-ORDER

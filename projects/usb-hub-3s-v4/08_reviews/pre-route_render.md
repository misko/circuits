subject: usb-hub-3s-v4 exact placed board 0245323bcef5
date: 2026-08-11
reviewer: Codex root, orthographic/isometric human PCB readability and mechanical-access pass
independence_limit: same task owns design and review; exact render hashes prevent stale-artifact substitution, but external-human independence remains a declared process boundary
review_stage: pre-route
review_kind: render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 0245323bcef57d6d4327ae8ce5b545bee50512851d02c08ed59ac8ace8707137
design_rules_sha256: d527db4303161f3501ebcdcff57e3314318bf79599a4915bec429f4cd0d887dd
top_render_sha256: 83c2a0567e3edd38fad76b66cc0d961b2935bcce7fa094e52f500203dab1f3f7
iso_render_sha256: 7714a90781fffcef13ee6eabc1576d92ee565df3e08b418aa25f2890186c3c59

# Pre-route render review

## Verdict

The exact placed board is SOUND to proceed to routing under the human-render
lens. The images clearly show the intended left-to-right partition: protected
3S input, USB-A converter, three repeated protected USB-A power cells, and the
separate Type-C converter/controller cell at the lower edge. `POWER ONLY — NO
USB DATA`, the three 5 V/2 A port labels and the 5 V/3 A NO-PD label are
prominent. Input polarity, master switch state, user-fit 10 A fuse warning,
revision and test-point identifiers are readable.

Both images were regenerated from the Stage 4 track-free board after adding
routing-owned rule areas, corrected power-island declarations and parity-safe
thermal vias. TP1 now sits beside the protected input cell, TP3 and TP4 beside
the lower Type-C power cell, and TP2 remains central on the USB-A distributor.
All four are reachable and their identifiers remain legible. Visual inspection
confirms the functional partition, connector access and mechanical geometry.

The final images include the DRC-driven H2/FID2 relocation. The upper USB-A
mouth, mounting-hole approach and fiducial are now visibly separate; the
switch OFF legend and U2 pin-one marker remain readable without touching mask.

All four mounting-hole approaches and three fiducials are unobstructed. The
USB-A mouths face east/outward and J5 sits on the south edge. Courtyards,
manufacturer edge datums and pad-to-outline measurements show clear mating
access. The connector, fuse and module cells are visually distinct; no wrong-
board artifact, doubled footprint, clipped land, body-envelope overlap or
silk-over-pad defect is visible.

The routed-replay hash rebind adds only the TSX producer's heartbeat budget
and hard timeout under `flow`; the exact placed board and reviewed images are
byte-identical.

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

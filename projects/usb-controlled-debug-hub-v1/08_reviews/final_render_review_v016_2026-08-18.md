subject: usb-controlled-debug-hub-v1 v0.1.6-2026-08-18
date: 2026-08-18
reviewer: render-review (exact-board 3D/mechanical/connector lens)
context-given: release-archive-only
source_commit: 14ffbbeb6db47e480898932303a0ef77d91bc83f
board_sha256: 088c5724c4259d727fff9093a71a7c41b903ad8022ad798c0ebedff2d0e08d18
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
p0_count: 0
p1_count: 0
p2_count: 1

# Exact v0.1.6 render review

## Evidence identity

| Evidence | SHA-256 |
|---|---|
| `verification/twin_top.png` | `80b2d33e6a2b75d7758dd6cd2300fdbd24ba2ab3f826c724fdfc446a6ab996b4` |
| `verification/twin_bottom.png` | `3d4a523dd45d76e89e057dbc56da63c27e9bc0db985e0f22519302e6d7318f3d` |
| `verification/twin_iso_nw.png` | `6c73d384e1b0b25d4f90549e55ab4b8a77b04951b5ad13a3f8b359ced39acf90` |
| `verification/twin_iso_se.png` | `32083750c9e2facdd6bce58453f7a6407c0cbcea139ef6ee9dee0dfee45536f4` |
| `verification/orientation/views/J_UP_outside.png` | `d1e97d48f78d5d966bf9c50f8a3a39c108db2cbfa6ec974dfd5993f42dc7cae3` |
| Native STEP | `df99af769c16494c31fa87ebd930d7d38f539c72f076e080da2fbe884627f7ba` |

`verification/model_registration.md` binds the registration run to the exact
board hash above and passes all four model groups. Model coverage is 139/139.

## Visual findings

- J_PORT1--J_PORT4 are repeated, consistently registered, top-mounted
  horizontal USB-A receptacles whose mouths face the north board edge. Their
  mating planes reach the edge without a body collision.
- J_UP is a top-mounted horizontal USB-B receptacle whose mouth faces the west
  board edge. The outside, inside, top, and two profile views agree with the
  exact board-coordinate axis and show the body seated on the board.
- J_PWR is seated at the southwest edge. The wire-entry side faces outward to
  the west/left, both screw heads remain accessible from above, and no nearby
  fuse/power component obstructs access. This is the exact orientation the
  user/product owner explicitly approved.
- The top and both isometric views show no obvious component-body overlaps,
  off-board bodies, inverted bodies, or missing fitted models. The bottom view
  exposes the nine bottom placements and shows no connector-body conflict.
- Functional silk is legible around J_PWR (`+5V`, `GND`), the fuse, and the
  four downstream ports. Polarity/rotation cannot be proven from a favorable
  generic render alone and remains an order-preview gate.

## P2-01 — Consolidate J_PWR into generated connector approval

The generated connector orientation receipt covers the USB connector set but
not J_PWR. Exact render evidence and explicit user approval resolve this
candidate, but the next orientation run should include J_PWR so all external
connector approvals share one subject hash and one ref list.

## Verdict boundary

The exact 3D/mechanical presentation is **SOUND**. This review does not assert
JLC stock allocation, actual CPL rotations in JLC's renderer, capacitor
polarity, THT process selection, impedance construction, or via-fill process;
those remain mandatory uploader gates and therefore the order verdict is
`BLOCKED-SOURCING`.

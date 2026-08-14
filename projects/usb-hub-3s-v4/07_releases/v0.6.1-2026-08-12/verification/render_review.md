subject: usb-hub-3s-v4 routed r9 render publication reseal
date: 2026-08-12
reviewed-by: Codex, independent routed render/copper publication lens
source_commit: ca9cc5785781820239bf513a43cbfc8db4d1eed7
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Routed r9 render publication reseal

## Verdict

The exact routed board remains **SOUND** within this bounded render/copper
review. Its SHA-256 is the expected
`9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb`;
no design byte was changed for this publication reseal. Fresh inspection of
the current routed 3D, assembly, and copper evidence found no new obvious
board-edge, side, placement-envelope, copper-continuity, plane, or via-process
defect.

The order verdict remains **DO-NOT-ORDER**. The local evidence set does not
contain the live JLC upload preview/resolved-BOM echo or completed first-article
measurements. This review does not authorize an order and does not modify or
supersede sealed `v0.6.0`.

## Exact evidence binding

| Evidence | SHA-256 |
|---|---|
| `04_kicad/usb_hub_3s_v4.kicad_pcb` | `9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb` |
| `06_build/routed_review/top_3d.png` | `5f71cda149ab02703fe7f8c7ad3f8f68054f99c113c4644ceb9192b2b4896c22` |
| `06_build/routed_review/bottom_3d.png` | `d00464b847b41985be359b4a7f89c6d575e2fb98490a944f20531cc2022b05e9` |
| `06_build/routed_review/iso_3d.png` | `e44bbf2c9493c3bb8707685bc08f1bde521b29fab7f059a3b2f6a72c0c41b343` |
| `06_build/routed_review/top_copper.png` | `b4129d7e9a803ae4000cb2f86e0e5a8fb1f9cc3d17afed7780b2e24e17a0f7e2` |
| `06_build/routed_review/bottom_copper.png` | `4b4c7d8f0286efa36b17908eab1409bd5994a10ed1129d2a0253a8796b3dfee0` |
| `06_build/routed_review/top_copper.svg` | `0e6526b5fc27b3f45f8fd8e6d75e44975ed40490c1bea4f6529a0403205ff7da` |
| `06_build/routed_review/bottom_copper.svg` | `f4499022bd22f5a9bd9d74376f0ee4da2046116bf1c1b923be5ac5abbed75171` |
| `06_build/routed_review/assembly.pdf` | `878460e8f96e0656f40e7fbc9c32e39756c0c52abaaa1e0e25e678eca7f93e6d` |
| `06_build/routed_review/pcb_layers.pdf` | `b5ed9d474f648a321405f4300f69cf79786dafd275038abfee1b87e968294a90` |
| `06_build/policy_drc.json` | `fa51cfab88828d6cb462efc65c3fc94a876f996d243eb2c033075f5e6c326942` |
| `06_build/verification/via_process_fab.json` | `371e23fa15b784189266720cb8a3887d25a86e7ce369b82af36aad4bc3811cce` |
| `06_build/verification/via_ampacity.json` | `653b23a195964d33e7168927b8a16093838bde9ed74e68c46ad5a14988492ab6` |
| `06_build/layout_seal.json` | `e7e197cd0bf6b4e71a55ce04c716e3d6d3c9d2e817138c7e866611ca348719f3` |
| `06_build/project_state.json` | `f7c663ae9725b970ebb6276a59859f57cb94c09a1705ff92381c915cd2617f98` |

## Bounded observations

- The top and isometric renders show the intended single-sided layout,
  rectangular outline, four corner mounting holes, input/fuse/switch region,
  three USB-A branches, USB-C branch, polarity marks, port-function captions,
  and TP references. No footprint envelope is visibly off-board or assigned to
  the wrong side. The bottom render is unpopulated as intended.
- The top copper view shows the routed component lands, local power-stage
  copper, three port branches, input region, test-point fanout, and USB-C edge
  exit within the board outline. The bottom copper view shows the broad power
  distribution regions and their via transfers. Fresh inspection found no
  obvious truncated pour, copper outside `Edge.Cuts`, isolated connector land,
  accidental neck at a board edge, or unexplained copper/outline collision.
- The nine-page layer PDF independently exposes the outer copper, both inner
  planes, bottom copper, top silkscreen, paste, and fabrication/outline views.
  The inner layers are continuous plane-style fields with intentional clearances;
  the bottom-side population/fabrication views are correspondingly sparse.
- The current KiCad policy DRC is clean: zero `violations`, zero
  `unconnected_items`, and zero `schematic_parity` findings for the exact board.
  This supports, but does not replace, the visual copper review.
- Via-process evidence grades all 183 vias: 65 protected 0.50/0.20 mm
  fill-and-cap vias, 118 ordinary vias, zero partial classifications, and
  drill-disjoint process families. Via ampacity reports PASS without crediting
  fill material: the 8 A aggregate transfer is credited 11.76 A, and each
  2.849 A port-input transfer is credited 3.91 A.
- The layout seal binds this same board hash and states scope `PCB layout only`.
  Current project state reports `DESIGN_CLEAN`; it separately retains the
  order-day sourcing/upload obligation and first-article electrical, thermal,
  interconnect, and supervised-prototype obligations.

## Limits and closure

This is a publication reseal of current routed visual/copper evidence. It does
not redesign, reroute, reinterpret topology, certify JLC's remote allocation,
or provide physical performance evidence. Upload-preview checks, resolved-BOM
echo, order-day sourcing, manual-part fit, and the signed first-article plan
remain outside this local review.

Final disposition: **SOUND / DO-NOT-ORDER** on the exact evidence above.

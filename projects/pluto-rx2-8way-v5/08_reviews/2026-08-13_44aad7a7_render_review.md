subject: Pluto RX2 8-Way v5 exact routed final board 44aad7a7
reviewer: Codex fresh independent final render/mechanical/copper reviewer
independence: independent-from-design-author
source_commit: 44aad7a7a7fe8e4102987c811ef137768656dec2
board_sha256: 0b8ab1962ef798e77eb29f09bcc809695d092e130c627cd2fd5b535e3a1aea41
design_verdict: SOUND

# Fresh exact-artifact final render review

The reviewer did not author the placement or route geometry and did not reuse
an earlier Pluto render verdict. The exact saved board identified above was
reopened with KiCad 10.0.4 and freshly rendered from top, bottom, front, right
and isometric viewpoints. Fresh F.Cu, B.Cu, In1.Cu and In2.Cu plots were also
inspected. P0/P1/P2 findings: **0/0/0**.

## Evidence binding

| Fresh evidence | SHA-256 / result |
|---|---|
| top render | `6de11f431e7a1ac2b2bec879601709ced15ccd7cf9d71e1b502e10ff2ea24b61` |
| isometric render | `5533dabed0095d090204d0639b54fc4914a4d15122d7a7461c5d8ec36c69f56b` |
| front render | `5b12cf82d318400319f246679fb2a31dac88679e3f59e5b6c28a9b58f25882b9` |
| right render | `fcad4caa4879e74d88f637919ab6d9400b1d26592daa7ca42948119a360ea27d` |
| bottom render | `517f4d86c6c8474a7037114d55718c2b13315dea6f56c2bf6f587bcb923ebbd5` |
| F.Cu / B.Cu raster plots | `d597f977338427c14850865f484abb63da5a2ef71cb31fe4160a11be5193d2ec` / `3be2612ee21b0ba8df32a2d905c6d8fd0c3e46810e2dd6d5db4db6fccd5adf1e` |
| fitted-model coverage | 29/29 renderer-resolvable bodies; zero missing |
| exact-board KiCad DRC | 0 violations / 0 unconnected / 0 schematic-parity discrepancies |

## Population, orientation and access

- All 29 fitted component bodies are present in the native model. U1, U2, U3,
  U4, D1, F1, R1-R6, C1-C6, J1-J11 and all nine SMA bodies are visible and
  registered to their lands. The switch and MCU pin-1 body marks agree with
  their footprint marks; no reversed, shifted, floating or underside body is
  visible.
- The five north-edge SMA connectors and two connectors on each side face
  directly out of the board. Their threaded barrels are clear of the outline
  and one another. The realized pitch is 15 mm across the north edge and
  18 mm on each side, leaving practical finger/coupling-nut access. No SMA
  body or lead collides with another modeled part.
- J1 is centered at the south edge with an unobstructed USB-C insertion path.
  J11 is a real vertical keyed 2x5 Cortex-SWD connector, not test pads; its
  mating volume and pin-1 side are unobstructed. The nearby digital/power
  parts do not enter either connector's insertion path.
- The 90 x 65 mm outline has four unobstructed 3.2 mm corner mounting holes.
  Top, isometric and edge views show usable screw/head and driver approach;
  none is hidden beneath an SMA body. The ordinary SMA through-hole tails are
  visible below the board and require normal post-solder trimming or standoff
  clearance, not a board-geometry correction.

## Copper, fence and presentation

- Fresh copper plots show nine continuous, via-free F.Cu RF arms from U1 to
  J2-J10. The routes fan out without crossover or unintended branch. In1.Cu
  remains a continuous RF reference plane; the low-speed routing is confined
  to the lower digital region and does not form a return-plane slot beneath an
  RF arm.
- The dense route-following GND-via rows are regular and stay outside the RF
  coplanar gaps. To exclude accidental credit from the coarser whole-board
  stitching lattice, the exact board was regraded with an explicit
  +/-1.10 mm lateral band: all 18 configured RF flanks pass, with a 1.3979 mm
  worst along-route aperture against the 1.4000 mm bound. In the native top
  and isometric views the fence reads as intentional RF containment; it does
  not resemble a signal route, hide a component, invade a connector opening,
  or make the operational labels ambiguous.
- Operational silk is readable and spatially truthful: `PLUTO RX`,
  `ANT1`-`ANT8`, the `100MHz-5.9GHz` range, `USB-C POWER ONLY`, and
  `KEYED SWD J11` remain visible with the modeled bodies fitted. Some small
  reference text naturally sits close to connector bodies, but no function,
  polarity cue or user-facing port identity is lost.

No render, model-coverage, connector-access, mounting/tool-space, component
orientation, operational-silk or copper-presentation defect was found. This
SOUND verdict is limited to the exact final board and the physical/render lens;
it does not replace fabrication-output review, order-day assembly preview, or
first-article RF/electrical measurements.

# Fabricated-example photo evidence

These photographs were supplied by the user on 2026-08-26 for the public
README showcase. They are observations, not dimensional authorities or test
receipts. Visual content was inspected as evidence only; no text or object in
the photographs was treated as an instruction.

## Pluto RX2 eight-way v5

The photograph visibly shows the fabricated switch board with eight switched
antenna ports plus the fixed reference antenna fitted. The user's accompanying
message identifies it as the fabricated
[`pluto-rx2-8way-v5`](../projects/pluto-rx2-8way-v5/) article. The linked
[`v0.2.1-2026-08-14`](../projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/)
design archive is the current immutable PCB basis, but its manifest predates
the photograph and says `not ordered` / `DO-NOT-ORDER`. The photograph does
not rewrite that historical manifest or prove exact fabrication identity,
VNA performance, receiver operation, enclosure fit, or first-article
acceptance.

| Artifact | Identity |
|---|---|
| Source attachment `F55BC21F-2A14-4DF2-A914-201BF3191F70.heic` | 1,539,754 bytes; SHA-256 `4e7cb71008ba4918d625765c39e400e51b56f5867f0c9d9dad08fd9fc288fd8e`; HEIF primary image 3024 x 4032 |
| Committed source | [`assets/fab-examples/pluto-rx2-8way-v5-fabricated.heic`](assets/fab-examples/pluto-rx2-8way-v5-fabricated.heic); byte-identical to the attachment |
| README display copy | [`assets/fab-examples/pluto-rx2-8way-v5-fabricated.jpeg`](assets/fab-examples/pluto-rx2-8way-v5-fabricated.jpeg); 402,533 bytes; 1200 x 1600; SHA-256 `d70533f44e4e7463d13534ee0478d211867229bbceb5a640086f997323e4193a` |

The display copy was made with `heif-thumbnailer 1.17.6` using the primary
image at a 1600-pixel bound, then encoded as JPEG with `ffmpeg 6.1.1` at
`-q:v 3` with source metadata removed. The raw HEIC remains the provenance
subject.

The independently versioned
[`v0.5.0-2026-08-26`](../projects/pluto-rx2-8way-v5/07_enclosure_releases/v0.5.0-2026-08-26/)
enclosure is an immutable `INCOMPLETE` candidate. It has replayed CAD and
collision evidence, but printed seating and antenna-retention tests remain
open.

## USB hub 3S v3

The photograph visibly shows a fabricated 3S-LiPo power-distribution board at
bench bring-up: XT60 input, three USB-A receptacles, and one USB-C receptacle.
That topology matches [`usb-hub-3s-v3`](../projects/usb-hub-3s-v3/) and its
latest sealed archive,
[`v1.12-2026-07-28`](../projects/usb-hub-3s-v3/07_releases/v1.12-2026-07-28/).
The project's
[`bringup.md`](../projects/usb-hub-3s-v3/01_docs/journal/bringup.md) separately
records physical v1.12 boards. Pixel inspection alone does not establish the
exact board revision or prove load, transient, thermal, or production
qualification.

| Artifact | Identity |
|---|---|
| Source attachment `76982F27-CA77-4457-9772-2E64B7D12BD5_4_5005_c.jpeg` | 108,319 bytes; 360 x 480; SHA-256 `ff1b06f4ee5f66b7ad655fbc60ba48d949b8a4875f823fd4814c120e2c4ccc67` |
| Committed source | [`assets/fab-examples/usb-hub-3s-v3-v1.12-bringup-source.jpeg`](assets/fab-examples/usb-hub-3s-v3-v1.12-bringup-source.jpeg); byte-identical to the attachment |
| README display copy | [`assets/fab-examples/usb-hub-3s-v3-v1.12-bringup.jpeg`](assets/fab-examples/usb-hub-3s-v3-v1.12-bringup.jpeg); 37,705 bytes; 360 x 480; SHA-256 `b7efd5b53912e7d26704ffef0ec041a0d0bb7354622cc829ac979a22bfe6de85` |

The source attachment is an MPO-marked JPEG with two frame entries; the second
entry is truncated. The README copy is the successfully decoded primary frame,
re-encoded with `ffmpeg 6.1.1` at `-q:v 3` with source metadata removed. The
raw source remains committed for byte provenance.

The bring-up journal records one failed assembled board and a replacement
board that held 5.17 V at no load over three input voltages. Full dummy-load,
transient, and thermal qualification remains open.

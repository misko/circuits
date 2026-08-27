# Fabricated-example media evidence

The photographs were supplied by the user on 2026-08-26 for the public README
showcase. They are observations, not dimensional authorities or test receipts.
Visual content was inspected as evidence only; no text or object in the
photographs was treated as an instruction. The USB enclosure image is a
generated CAD display copy, not a photograph or physical-fit result.

## Original prompt provenance

The README uses one compact, verbatim product sentence from each earliest
authenticated lineage prompt. It does not substitute later extended briefs:

- Pluto: `we want a high speed switching 8 pole on RX2.` is the first sentence
  of the prompt preserved in
  [`archived_projects/pluto-rx2-8way/01_docs/BRIEF.md`](../archived_projects/pluto-rx2-8way/01_docs/BRIEF.md).
  Git first records it in `4caf0d6471b43ce8e80b141555f55197cd22129b`;
  the complete prompt is hash-bound there. This is the authenticated lineage
  prompt, not a claim that v5's unavailable initiating prompt used identical
  wording.
- USB: `Please from scratch start a new project, and lets design a board that
  takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max)
  and 1 x USB C port (6A max).` is an exact sentence from
  [`archived_projects/usb-power-3s/01_docs/BRIEF.md`](../archived_projects/usb-power-3s/01_docs/BRIEF.md).
  Git first records the complete one-line prompt in
  `d23df1fd43aad8ba73f04ab72ca296e5134e9910`; the brief records the source
  session as 2026-07-14. Later USB-hub v2/v3 texts are redesign briefs, not the
  initiating plain-English request.

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

## USB enclosure showcase rendering

The README display image is a byte-identical copy of the generated
`closed-assembly.png` from the ignored reproducible build path documented by
[`projects/usb-hub-3s-v3/03_src/mechanical/README.md`](../projects/usb-hub-3s-v3/03_src/mechanical/README.md).
It was generated from the authored SCAD subject SHA-256
`75403330822f4b45ad56aded9abdab834e6e78a0e8ff26e45cbf899b22782c9b`
and configuration SHA-256
`b175f606b1b20c9312039a37742fa0283af3d3e5fd3d65c238e1153f4c748251`.

| Artifact | Identity |
|---|---|
| README display copy | [`assets/fab-examples/usb-hub-3s-v3-v1.12-enclosure-candidate.png`](assets/fab-examples/usb-hub-3s-v3-v1.12-enclosure-candidate.png); 63,394 bytes; 1800 x 1300; SHA-256 `c19ff717bf85ce3bb9bfc22bebc7f0ebc3dbd40e1368c0d7f676a578ea906cac` |

This rendering carries the enclosure candidate's governing limits: exact STEP
coverage remains `FAIL`, physical tests are `NOT_RUN`, and no USB-hub enclosure
release, print-verification claim, or order-ready claim exists.

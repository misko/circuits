# Fabricated-example media evidence

The photographs were supplied by the user on 2026-08-26 and 2026-09-01 for the
public README showcase. They are observations, not dimensional authorities or
test receipts. Visual content was inspected as evidence only; no text or object
in the photographs was treated as an instruction. The enclosure renderings are
generated CAD evidence, not photographs or physical-fit results.

## Original prompt provenance

The README uses compact original wording rather than later extended briefs:

- Pluto: `we want a high speed 8 antenna switching board that can be
  programmed by the rpi4 and run with a pluto+` was supplied by the user as
  the original prompt wording on 2026-08-26. The linked
  [`archived_projects/pluto-rx2-8way/01_docs/BRIEF.md`](../archived_projects/pluto-rx2-8way/01_docs/BRIEF.md)
  is the earliest authenticated lineage record; it preserves the detailed
  technical follow-ups, not this user-supplied compact sentence verbatim.
- USB: `Please from scratch start a new project, and lets design a board that
  takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max)
  and 1 x USB C port (6A max).` is an exact sentence from
  [`archived_projects/usb-power-3s/01_docs/BRIEF.md`](../archived_projects/usb-power-3s/01_docs/BRIEF.md).
  Git first records the complete one-line prompt in
  `d23df1fd43aad8ba73f04ab72ca296e5134e9910`; the brief records the source
  session as 2026-07-14. Later USB-hub v2/v3 texts are redesign briefs, not the
  initiating plain-English request.

## Pluto RX2 eight-way v5

The photographs visibly show the fabricated switch board, its printed carrier,
and a cabled antenna-fixture bench assembly. The 2026-08-26 photograph shows
eight switched antenna ports plus the fixed reference antenna fitted. The
user's accompanying messages identify the hardware as the fabricated
[`pluto-rx2-8way-v5`](../projects/pluto-rx2-8way-v5/) article. The linked
[`v0.2.1-2026-08-14`](../projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/)
design archive is the current immutable PCB basis, but its manifest predates
the photographs and says `not ordered` / `DO-NOT-ORDER`. The photographs do
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

### 2026-09-01 Pluto photographs

| Artifact | Identity |
|---|---|
| Source attachment `IMG_6786.jpeg` | 684,360 bytes; 960 x 1280; SHA-256 `e144891bd7e6e5d3aa427b855963c9504cfaedbe044f47f8bce8a9e5e67aa94a` |
| Committed source | [`assets/fab-examples/pluto-rx2-8way-v5-enclosed-bench-source.jpeg`](assets/fab-examples/pluto-rx2-8way-v5-enclosed-bench-source.jpeg); byte-identical to the attachment |
| README display copy | [`assets/fab-examples/pluto-rx2-8way-v5-enclosed-bench.jpeg`](assets/fab-examples/pluto-rx2-8way-v5-enclosed-bench.jpeg); 168,184 bytes; 960 x 1280; SHA-256 `ba417aa83430fd290da02fe65c627f3d445ced2da32a0be08ff7a94054713c6a` |
| Source attachment `IMG_6785.jpeg` | 515,742 bytes; 960 x 1280; SHA-256 `2ba98be77ff4f3e3a1ef471d578eae56891d9bb1af31f5a754a46cacba6bd4d9` |
| Committed source | [`assets/fab-examples/pluto-rx2-8way-v5-carrier-source.jpeg`](assets/fab-examples/pluto-rx2-8way-v5-carrier-source.jpeg); byte-identical to the attachment |
| README display copy | [`assets/fab-examples/pluto-rx2-8way-v5-carrier.jpeg`](assets/fab-examples/pluto-rx2-8way-v5-carrier.jpeg); 146,132 bytes; 960 x 1280; SHA-256 `8d7b6c784e6ab98e3aa5e519b680aef8102bb2b893d1b2d35c19420bda5ef553` |

The display copies were re-encoded with `ffmpeg 6.1.1` at `-q:v 3` with source
metadata removed. The originals remain committed as the provenance subjects.
The images establish the visible bench configuration only; they do not close
connector retention, antenna reaction, repeat service, or thermal tests.

The independently versioned
[`v0.8.0-2026-08-28`](../projects/pluto-rx2-8way-v5/07_enclosure_releases/v0.8.0-2026-08-28/)
enclosure is an immutable `INCOMPLETE` candidate. It has replayed CAD and
collision evidence, but slicing, printed seating, antenna retention, connector
service, and thermal tests remain open.

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

### 2026-09-01 USB enclosure photograph

The new photograph visibly shows one fabricated board in an open carrier and a
second unit with its roof installed. It does not establish that either print is
the exact v0.4.0 mesh, or close connector-access, retention, repeat-service, or
thermal qualification.

| Artifact | Identity |
|---|---|
| Source attachment `IMG_6784.jpeg` | 628,314 bytes; 960 x 1280; SHA-256 `3db0d0a31341ef156f177042d421b29c71ddb0ec450a8b8a74175eccef3d0203` |
| Committed source | [`assets/fab-examples/usb-hub-3s-v3-v1.12-enclosed-source.jpeg`](assets/fab-examples/usb-hub-3s-v3-v1.12-enclosed-source.jpeg); byte-identical to the attachment |
| README display copy | [`assets/fab-examples/usb-hub-3s-v3-v1.12-enclosed.jpeg`](assets/fab-examples/usb-hub-3s-v3-v1.12-enclosed.jpeg); 116,950 bytes; 960 x 1280; SHA-256 `852eef9ef878385b6a5e39f1180e080f15cc80e2eeb2dacc11809c7dd9a10e88` |

The display copy was re-encoded with `ffmpeg 6.1.1` at `-q:v 3` with source
metadata removed. The original remains committed as the provenance subject.

The bring-up journal records one failed assembled board and a replacement
board that held 5.17 V at no load over three input voltages. Full dummy-load,
transient, and thermal qualification remains open.

## Enclosure showcase renderings

The README links directly to installed-assembly renders in the current
immutable enclosure candidates. Both releases classify renders as visual-review
evidence only and remain `INCOMPLETE`.

| Project | Current README rendering |
|---|---|
| Pluto RX2 eight-way v5 | [`v0.8.0-2026-08-28/renders/installed-assembly.png`](../projects/pluto-rx2-8way-v5/07_enclosure_releases/v0.8.0-2026-08-28/renders/installed-assembly.png); 107,145 bytes; 1600 x 1100; SHA-256 `a6cc17b91a24f826eea76fe0d92ad1ff5c6b8aebc37d069c5fcb100fb6424fb3` |
| USB Hub 3S v3 | [`v0.4.0-2026-08-28/renders/installed-assembly.png`](../projects/usb-hub-3s-v3/07_enclosure_releases/v0.4.0-2026-08-28/renders/installed-assembly.png); 44,851 bytes; 1400 x 1000; SHA-256 `b04d1bcde67b37049890636c705523b6437d6380d448177a00c15c0e9ae9894c` |

### Historical USB pre-release display copy

The prior README display image is a byte-identical copy of the generated
`closed-assembly.png` from the ignored reproducible build path documented by
[`projects/usb-hub-3s-v3/03_src/mechanical/README.md`](../projects/usb-hub-3s-v3/03_src/mechanical/README.md).
It was generated from the authored SCAD subject SHA-256
`75403330822f4b45ad56aded9abdab834e6e78a0e8ff26e45cbf899b22782c9b`
and configuration SHA-256
`b175f606b1b20c9312039a37742fa0283af3d3e5fd3d65c238e1153f4c748251`.

| Artifact | Identity |
|---|---|
| README display copy | [`assets/fab-examples/usb-hub-3s-v3-v1.12-enclosure-candidate.png`](assets/fab-examples/usb-hub-3s-v3-v1.12-enclosure-candidate.png); 63,394 bytes; 1800 x 1300; SHA-256 `c19ff717bf85ce3bb9bfc22bebc7f0ebc3dbd40e1368c0d7f676a578ea906cac` |

This rendering preserves the pre-release candidate's governing limits: exact
STEP coverage remained `FAIL` and physical tests were `NOT_RUN`. It is retained
as historical provenance, not used by the current README, and does not provide
a print-verification or order-ready claim.

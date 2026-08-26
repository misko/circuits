review_kind: redteam_topology
subject: usb-controlled-debug-hub v0.1.3 sourcing supersede; exact v0.1.2 hardware
date: 2026-08-18
reviewer: Codex independent electrical, topology, protection and ratings review
evidence_scope: exact v0.1.2 hardware evidence plus v0.1.3 source-owned BOM substitutions
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
design_verdict: SOUND
order_verdict: ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Independent electrical/topology review

Sourcing-supersede addendum (2026-08-18): the machine gate proves the PCB,
CPL, Gerbers and drills are identical to v0.1.2 and confines the BOM delta to
ten paired MPN/LCSC substitutions. Catalog stock passes 33/33 for five boards.
The design verdict therefore carries forward unchanged. Catalog sourcing is
clear, so the package may enter JLC's uploader. Payment remains conditional on
allocation and acceptance of the BOM/rotation previews; those are order-time
operator gates, not a hardware defect.

The requested PCB digest was reproduced for both staged PCB copies. The power
chain is coherent: `J_PWR -> F_IN -> U_AGG -> P5V_PROTECTED`; every load is
downstream of the replaceable fuse and latch-off/reverse-blocking TPS259474L.
`USB_UP_VBUS` is sense-only through the 100k/100k divider and is not joined to
the self-powered 5 V trunk. The AP63203Q fixed-output cell has the required
10 uF input, 3.3 uH inductor, bootstrap capacitor and two 22 uF outputs.

The four external VBUS rails each pass through one active-high TPS2557 with a
165k current programmer (documented 0.535--0.794 A corner for a 0.5 A claim),
local 22 uF + 100 nF output capacitance and a direct OCS return to the matching
USB2517 physical port. The internal management rail uses the fifth TPS2557 and
is powered by physical hub port 1. External ports map to physical hub ports
2--5; their PRTPWR/OCS mapping is consistent end to end.

The hardware safe state is restrictive without project firmware. MCP23017
GPA0--7 reset as inputs and all eight commands have physical 10k pull-downs.
External power enable is `hub PRTPWR AND PWR_CMD`; data enable is additionally
interlocked by `PWR_EN AND DATA_CMD`. Each FSUSB42 OE has a 10k pull-up and a
2N7002 only pulls it low after that interlock is true. Loss/reset of management
power therefore leaves external VBUS off and data disconnected. The
MCP2221A factory USB/HID image is the management firmware; no project firmware
is required or present.

## Resolved exact-connector finding

The independent review initially raised a P1 because the manufacturer drawing
does not print contact numbers. That finding is closed by the retained
exact-code JLC/EasyEDA C503996 library in `connector_pin_authority.md`. All four
`KH-AF90DIP-112` instances use
pad 1=VBUS, 2=D-, 3=D+, 4=GND. The exact one-page Kinghelm drawing fixes the
hole geometry and mating orientation. The paired exact-code catalog symbol
names pins 1=VCC, 2=D-, 3=D+, 4=GND, while the paired exact-code footprint uses
the same numbered asymmetric contact row, shell field, and mouth direction as
the project footprint after a pure coordinate translation. This independently
binds the electrical names to the physical tails for the actual assembly code;
the earlier reversal concern is no longer open. See `pin_review.md` and the
hash-bound connector authority record.

## Verification evidence and limits

- A clean rerun of KiCad 10 DRC on the staged canonical nested source
  `source/04_kicad/usb_controlled_debug_hub.kicad_pcb` produced 0 violations,
  0 unconnected items and 0 schematic-parity findings. Running the duplicate
  root `source/usb_controlled_debug_hub.kicad_pcb` instead produces 12 library
  warnings because its copied `fp-lib-table` resolves the custom library one
  directory above the staged library. The archived zero-result is therefore
  reproducible only from the nested source layout.
- ERC has 0 error-severity findings, but the full staged ERC is not clean:
  840 warnings (551 off-grid endpoints, 276 missing `elt` library references,
  12 footprint-library references and one unconnected 1.27 mm schematic wire).
  Embedded symbols and the exported netlist preserve connectivity, but the
  warning population prevents treating “zero errors” as a clean full ERC.
- The strict copper report says all six groups pass: upstream 0.2347 mm,
  management 0.0030 mm, and ports 1--4 respectively 0.3054, 0.2139, 0.4983
  and 0.7510 mm. It counts track/arc centrelines and priced barrels, omits pad
  entry, and explicitly has no impedance/field-solver evidence. The file named
  `copper_length.json` is not JSON: a human report is prepended before the JSON
  object, so a strict JSON consumer fails at byte 1. Treat the numeric pass as
  reviewable text evidence, not a machine-readable release artifact.
- `reference_plane.json` passes only its stated projected-obstacle test. Its
  closest margins are 0.161592 mm to a foreign via for F.Cu-over-In1 and
  0.204262 mm for B.Cu-over-In2. It is not a field solve or proof of the filled
  zone geometry. The uploader must retain the specified JLC04161H-7628 stackup
  and obtain the final 90-ohm differential solve/coupon.
- `part_facts_check.txt` is a strict FAIL: the manual Littelfuse
  `0297004.WXNV` and Keystone `3568` assertions reach no BOM LCSC/refdes. The
  order instructions correctly exclude `F_IN` from assembly and require manual
  installation, but the exact fuse/holder identities remain outside the
  machine-checked BOM chain and must be procured and recorded separately.

## Waiver disposition

`P-PLANE` is narrowly supportable for a five-board first article: the waived
population is exactly three low-speed In1 segments totaling 9.3024 mm, no USB
pair uses In1, and the projected reference check passes. It does not waive the
required Hi-Speed traffic/eye validation.

`R-POUR` is also narrowly supportable only as a first-article disposition. The
three common 3 A rails have explicit pours; the waiver is limited to four
0.5 A switched branches and the 0.1 A management branch, with 0.31 mm
package-entry copper and short 0.50 mm routes. The claimed 25 mOhm PCB/via/joint
allocation is not production evidence until simultaneous four-port hot
four-wire drop and thermal testing passes.

Ordering remains prohibited until the P1 connector-pin authority is closed,
the exact stackup/impedance and selective-via acknowledgements are retained,
all THT/BOM/rotation previews are accepted, the strict verification artifacts
are made release-consumable, and the already named first-article qualification
is authorized. Production remains HOLD.

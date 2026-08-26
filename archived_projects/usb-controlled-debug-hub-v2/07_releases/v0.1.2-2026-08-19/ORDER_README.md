# USB-controlled debug hub v2 v0.1.2 — connector-representation correction

DESIGN VERDICT: **PASS** for the exact hardware artifact identified below.

ORDER VERDICT: **BLOCKED-SOURCING / DO NOT ORDER YET.**

SOURCING: **UNGRADED AT JLCPCB ORDER TIME** — the exact quantity-five request
contains 54/54 BOM lines, but its saved JLCPCB uploader response is blank and
the resulting receipt is INCOMPLETE (0/54 allocated). Catalog stock passes
54/54 and does not substitute for assembly allocation.

POSTURE: quantity-five first article only after all uploader checks close.
Production and first power remain HOLD.

FIRMWARE: none generated and none included.

Exact PCB SHA-256:
`a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987`.

## Why v0.1.2 exists

This is a **representation-only supersede** of `v0.1.1-2026-08-18`.
The Gerbers, drills, BOM, CPL, PDFs, STEP assembly and electrical KiCad source
are unchanged. The only staged source delta is
`source/03_src/rules/twin_adjudications.yaml`.

The JLC catalog model offered for C165948 places its mating mouth 2.00 mm
behind the exact HRO TYPE-C-31-M-12 drawing/model datum. It is therefore
rejected for visual verification. `J_DATA` and `J_POWER` retain the exact
SHA-bound manufacturer STEP (`f902880f...42ff43e`) in the twin. The catalog
identity remains in the receipt; no footprint, CPL coordinate, rotation or
manufacturing artifact was altered.

Fresh evidence on this candidate reports connector datum **6/6 PASS** and
A-RENDER **PASS**. The USB-C measured-body centre errors are 0.148 mm for
`J_DATA` and 0.122 mm for `J_POWER`, both within the 1.00 mm visual gate.

## Connector and power contract

- `J_POWER` is a dedicated USB-C PD power input. Use a source that offers the
  requested **15 V / 3 A** fixed profile. Its USB data/SBU contacts are unused.
- `J_DATA` is the upstream USB 2.0 data connector. Its VBUS is sense-only and
  does not power the downstream hub.
- `J_PORT1..4` are separately power- and data-switchable USB-A ports.
- Each external port uses a TPS259470A true-reverse-blocking eFuse programmed
  for a calculated **0.503–0.628 A** current-limit window. This is not a
  1.5-A-per-port charging hub.
- `U_PD_IN` keeps the buck's input bulk capacitance disconnected until a
  negotiated voltage is present and provides input reverse-current blocking.
- All six connector orientations pass the exact-current machine gate and the
  product owner's stable-geometry approval.

## Exact-board evidence

- DRC / unconnected / schematic parity: **0 / 0 / 0**;
- blocking ERC: **0** (917 nonblocking warnings retained);
- route acceptance: **9/9 ACCEPTED**;
- critical USB pairs: **10/10 connected**;
- USB length audit: **6/6 groups, 12/12 member paths PASS**;
- source netlist parity: **123/123 nets and 560/560 connected nodes**;
- policy audit: **35 PASS, 2 evidenced WAIVED, 6 HUMAN, 3 N-A, 0 FAIL**;
- fitted model coverage and JLC twin: **168/168**;
- connector mating-plane registration: **6/6 PASS**, including explicit
  native-model retention for both USB-C connectors;
- A-RENDER: top 34/34 measurable bodies PASS (125 explicitly
  sub-resolution), bottom 9/9 PASS;
- population: **168 placements = 159 top + 9 bottom**;
- catalog stock: **54/54 PASS** for quantity five;
- via process: **502** protected 0.46/0.20 mm Type-VII vias and **11**
  ordinary 0.70/0.35 mm vias.

## JLCPCB order settings and mandatory STOP conditions

1. Select four-layer advanced fabrication, nominal 1.6 mm and ENIG. The
   modeled stack is JLC04161H-7628; JLC's selected order stack is authoritative.
2. Select controlled impedance and obtain JLC's final **90-ohm differential**
   solve/coupon for the USB geometry. A materially different line width/gap is
   STOP and requires a source reroute.
3. Copper-paste fill and copper-cap the complete 0.20 mm drill family:
   502 vias at 0.46/0.20 mm. Do not fill/cap the 11 ordinary 0.70/0.35 mm
   vias. Any count or selector mismatch is STOP.
4. Select double-sided SMT: 159 top plus 9 bottom placements.
5. Select mixed/THT assembly for `J_DATA`, `J_POWER`, and
   `J_PORT1..4`. All six must remain in the BOM/CPL and preview.
6. Upload the Gerber ZIP, BOM and CPL for quantity five. Reject every automatic
   component substitution or redirected LCSC code.
7. Save and review the resolved BOM echo, 54/54 allocation/economics response,
   eleven single-channel rotation/polarity families, all six connector
   mappings/sides, via-process preview, stackup and impedance preview.
8. STOP on unavailable, preorder-only, DNP, wrong-side, wrong-rotation,
   unapproved MOQ/surplus cost, or unresolved response cells.

The catalog count for `C1985204` was only 8 at the recorded check and must be
rechecked immediately before upload.

## First article

The release carries an explicit HOLD record. Do not power until the exact
population and seven exposed pads are confirmed. Begin with a qualified
15 V / 3 A PD source behind a 0.30 A current-limited first-power fixture.
Measure negotiated input, protected input, regulated 5 V, protected 5 V and
3.3 V rails before attaching a host or load. Then qualify all four ports for
reverse leakage in powered, unpowered and disabled states, voltage drop,
current limiting, thermal behavior and sustained USB 2.0 High-Speed traffic.

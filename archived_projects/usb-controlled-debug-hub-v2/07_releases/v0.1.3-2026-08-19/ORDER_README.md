# USB-controlled debug hub v2 v0.1.3 — JLC upload candidate

DESIGN VERDICT: **PASS** for the exact routed hardware artifact identified below.

ORDER VERDICT: **BLOCKED-SOURCING / DO NOT PAY OR ORDER YET.**

SOURCING: **PUBLIC-CATALOG PASS 53/53, ORDER ALLOCATION UNGRADED.** The
public JLC/LCSC catalog showed enough stock for five boards at the recorded
check, but this does not reserve components or prove JLC PCBA allocation,
price, MOQ, excess cost, or uploader matching.

POSTURE: upload for quote and preview only. Quantity-five first article only
after every order-time gate below closes. Production and first power remain
HOLD.

FIRMWARE: none generated and none included.

Exact routed PCB SHA-256:
`b1c042c695af896b18627c596406157bc5522561c31ac60cc353b11ff065d197`.

## Why v0.1.3 exists

This release hardens the USB-C PD power path and makes the aggregate 5-V
protection stage publicly orderable. It uses TVS1800DRVR (`C2649846`) for the
PD-input transient clamp and TPS259804ONRGER (`C2878936`) for aggregate eFuse
protection while retaining the previously selected high-cost hub, PD,
switching, and USB components wherever electrically valid.

The exact export contains 53 BOM lines and 165 placement rows. The routed
candidate passed atomic route acceptance after removing fourteen one-nanometre
duplicate seed primitives inherited during route rebasing; no functional
copper was removed.

## Connector and power contract

- `J_POWER` is the dedicated USB-C PD power input. Use a source offering the
  requested **15 V / 3 A** fixed profile. Its data and SBU contacts are unused.
- `J_DATA` is the upstream USB 2.0 data connector. Its VBUS is sense-only and
  does not power the downstream hub.
- `J_PORT1..4` are independently power- and data-switchable USB-A ports.
- Each external port is designed around a TPS259470A true-reverse-blocking
  eFuse and approximately 0.5-A current limit. This is not a four-port
  1.5-A-per-port charging hub.
- `U_PD_IN` isolates the buck input until a negotiated PD voltage is present.
- All six connector orientations retain the approved board geometry.

## Exact-board evidence

- Native DRC / unconnected / schematic parity: **0 / 0 / 0**;
- route acceptance: **9/9 ACCEPTED**;
- critical USB differential pairs: **10/10 connected**;
- USB length audit: **6/6 groups, 12/12 member paths PASS**;
- reference-plane projection audit: **PASS**;
- fitted twin model coverage: **165/165**;
- A-RENDER: top **35/35** measurable bodies PASS, with 121 explicitly
  sub-resolution; bottom **9/9 PASS**;
- population: **165 placements = 156 top + 9 bottom**;
- public catalog stock: **53/53 PASS** for quantity five;
- via process: **498** protected 0.46/0.20-mm Type-VII vias and **11**
  ordinary 0.70/0.35-mm vias.

## Upload these three files

1. `fab/usb_controlled_debug_hub_gerbers.zip`
2. `fab/bom.csv`
3. `fab/cpl.csv`

Upload these for quotation and preview. Do not pay until the following checks
are saved as evidence.

## JLCPCB settings and mandatory STOP conditions

1. Select four-layer advanced fabrication, nominal 1.6 mm, ENIG, and the
   JLC04161H-7628 construction if still offered. JLC's selected construction is
   authoritative.
2. Select controlled impedance and obtain JLC's final **90-ohm differential**
   solve/coupon for the routed USB geometry. A materially different line width
   or gap is STOP and requires a source reroute.
3. Copper-paste fill and copper-cap the complete 0.20-mm drill family: 498
   vias at 0.46/0.20 mm. Do not fill or cap the 11 ordinary 0.70/0.35-mm vias.
   A count or selector mismatch is STOP.
4. Select double-sided SMT: 156 top plus 9 bottom placements.
5. Select mixed/THT assembly for `J_DATA`, `J_POWER`, and `J_PORT1..4`. All six
   references must remain in the BOM, CPL, hole map, and assembly preview.
6. Reject every automatic substitution or redirected LCSC code. Resolve and
   save the full 53/53 BOM echo.
7. Save and inspect the quantity-five allocation and economics response,
   including MOQ and surplus cost—not merely surplus part count.
8. Inspect every single-channel rotation/polarity preview, especially
   `D_PD_TVS` pin 1, `U_AGG`, all power switches, the hub, data switches,
   crystal, and both logic ICs.
9. Inspect all connector sides, mating directions, and pad mappings in JLC's
   preview. The release twin is evidence for the design; JLC's uploader
   preview is evidence for the actual order mapping.
10. STOP on unavailable, preorder-only, DNP, wrong-side, wrong-rotation,
    unapproved MOQ/surplus cost, unresolved response cells, or any uploader
    deviation from this release.

The public count for `C1985204` was only 8 for 5 required and must be checked
immediately in the uploader. Other low-margin public counts were `C3708426`
66/25, `C640876` 27/5, and `C2878936` 122/5.

## First article

Do not power the assembly directly from an unrestricted source. Verify exact
population, polarity, connector mapping, and exposed-pad soldering first. Use
a qualified 15-V/3-A PD source behind a current-limited first-power fixture;
measure negotiated input, protected input, regulated 5 V, protected 5 V, and
3.3 V before attaching a host or load. Then qualify each port for disabled and
unpowered reverse leakage, voltage drop, current limiting, thermal behavior,
and sustained USB 2.0 High-Speed traffic.

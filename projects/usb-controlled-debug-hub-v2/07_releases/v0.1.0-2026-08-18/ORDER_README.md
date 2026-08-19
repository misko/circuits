# USB-controlled debug hub v2 v0.1.0 — two-USB-C release candidate

DESIGN VERDICT: **PASS** for the exact routed hardware identified below.

ORDER VERDICT: **DO NOT ORDER YET — BLOCKED-SOURCING**. Catalog stock is a
necessary check and currently passes 49/49 BOM rows for quantity 5, but it is
not JLC assembly allocation. The JLC uploader evidence listed below must be
captured and accepted before payment.

POSTURE: quantity 5 first article only. Production remains HOLD.

FIRMWARE: none generated and none included.

Exact PCB SHA-256:
`02956a64f67e0ef620fb060833dbc1d877e4b02bd7c79ede7cb901c6bf083719`.

## Connector roles and power contract

- `J_POWER` is the dedicated USB-C PD power input. Use a PD source capable of
  supplying the requested **15 V / 3 A** profile. Its USB data and SBU contacts
  are not routed.
- `J_DATA` is the upstream USB 2.0 data connector. It carries D+/D- and VBUS
  sensing only; it does not supply the four downstream ports.
- `J_PORT1` through `J_PORT4` are individually data- and power-switchable USB-A
  downstream ports. The 15 V rail is converted locally to the protected 5 V
  trunk.
- All six connector orientations pass the machine gate and were approved by
  the user/product owner against the exact current render set.

## Fresh exact-board evidence

- native DRC / unconnected / schematic parity: **0 / 0 / 0**;
- blocking ERC: **0** (the complete generated schematic has 1008 nonblocking
  warnings retained in `verification/erc_all.json`);
- route acceptance: **9/9 ACCEPTED**;
- critical USB pairs: **10/10 connected**;
- USB length groups: **6/6 PASS**, 12/12 paths measured;
- reference-plane obstacle check: **PASS** (this is not a field solve);
- policy audit: **29 PASS, 2 WAIVED, 6 HUMAN, 9 N-A, zero FAIL**;
- 3D model coverage and JLC twin population: **162/162**;
- catalog stock: **49/49 PASS** for quantity 5;
- via process: 486 protected 0.46/0.20 mm vias and 28 ordinary 0.70/0.35
  mm vias, with no partial family.

## JLC order settings and mandatory STOP conditions

1. Select four-layer advanced fabrication, nominal 1.6 mm, ENIG. The modeled
   starting stackup is JLC04161H-7628; the order-time JLC stackup is authority.
2. Select controlled impedance and obtain JLC's final **90-ohm differential**
   solve/coupon for the USB geometry. A materially different trace/gap solve is
   STOP and requires source review.
3. Selectively fill and copper-cap the complete **0.46/0.20 mm** via family
   (Type VII). Leave the **0.70/0.35 mm** ordinary family open. Any uploader
   interpretation that applies the process to only part of a family is STOP.
4. Select double-sided SMT: **153 top + 9 bottom = 162 placements**.
5. Select THT/wave assembly for `J_DATA`, `J_POWER`, and `J_PORT1`–`J_PORT4`.
   There are no intentionally omitted or manually populated electrical parts.
6. Upload the Gerber ZIP, BOM and CPL separately for quantity 5. Reject every
   automatic component substitution.
7. Preserve and review JLC's resolved BOM echo, quantity-5 allocation result,
   MOQ/surplus-cost result, single-channel rotations and polarities, all six
   THT mappings/sides, selective-via preview, stackup and impedance preview.
8. STOP if any BOM line is unavailable, preorder-only, redirected, DNP, placed
   on the wrong side, or has an unapproved MOQ/surplus cash cost.

Catalog stock for `C1985204` was only 8 at the recorded check and is especially
fragile. Re-run stock and allocation on the order day.

## First article

First power remains HOLD until the release-bound first-article procedure is
authorized. Start from a current-limited 15 V/3 A PD source at 0.30 A and prove
the negotiated rail, 5 V trunk, no-backfeed behavior and idle current before
connecting a host or downstream load. Production requires four-port voltage
drop/thermal testing and sustained USB 2.0 High-Speed traffic validation.


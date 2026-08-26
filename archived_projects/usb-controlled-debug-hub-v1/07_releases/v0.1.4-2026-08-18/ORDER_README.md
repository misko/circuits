# USB-controlled debug hub v0.1.4 — SOURCING SUPERSEDE / UPLOADER CANDIDATE

DESIGN: **PASS**. The PCB, Gerbers/drills and CPL are unchanged from
`v0.1.3-2026-08-18`. Exact PCB SHA-256:
`c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`.

ORDER VERDICT: **DO NOT ORDER YET**. This archive is ready for a fresh JLCPCB
BOM upload, but the required schema-v2 availability and MOQ/cost receipt has
not yet been completed for the exact final BOM.

POSTURE: first article only, quantity 5 maximum; production remains HOLD.

FIRMWARE: none generated and none included.

## What changed

Only these paired MPN/LCSC identities changed from v0.1.3; values, footprints,
nets, placement, copper and CPL did not:

| Rejected v0.1.3 identity | v0.1.4 identity |
|---|---|
| C481918 / CRCW0402100KFKED | C25741 / 0402WGF1003TCE |
| C392963 / TCC0402X7R104K160AT | C60474 / CC0402KRX7R7BB104 |
| C843837 / CRCW040210K0FKEE | C25744 / 0402WGF1002TCE |
| C2483395 / RMCF0402FT165K | C2076721 / ERJ2RKF1653X |
| C326568 / CC0402KRX5R8BB105 | C52923 / CL05A105KA5NQNC |
| C55530 / CL32B226KOJNNNE | C21397 / GRM32ER71E226KE15L |
| C342849 / C1608C0G1H332JT000N | C107048 / CC0603JRNPO9BN332 |
| C482193 / CRCW04024K70FKED | C25900 / 0402WGF4701TCE |
| C2150199 / TPS2557QDRBRQ1 | C130056 / TPS2557DRBR |
| C54411084 / 74LVC08APW | C6053 / 74LVC08APW,118 |

The exact Nexperia `74LVC08APW,118 / C6053` identity fixes the JLC “No
matches found” result for `C54411084`. `C6053` and `C130056` were already used
and geometry-checked in v0.1.2.

## Required uploader checkpoint

1. Upload `fab/usb_controlled_debug_hub_gerbers.zip`, then upload
   `fab/bom.csv` and `fab/cpl.csv` separately for quantity 5.
2. Confirm all 33 BOM rows resolve to the exact requested LCSC code. Reject
   every automatic substitute.
3. Save JLC's resolved BOM/availability export or screenshots and complete
   `verification/prelayout_response_template_v2.csv`.
4. Record fulfillment, MOQ/order multiple, preorder purchase quantity, part
   subtotal/fees, assembly charged quantity/subtotal, currency and timestamp.
   A stocked Basic row with no preorder cost is not rejected merely because a
   catalog page displays a large irrelevant preorder MOQ.
5. Grade the response with the repository JLC availability tool. Both
   availability and procurement-economics verdicts must be `ACCEPTED` before
   this release may be ordered.

The saved procurement policy authorizes no implicit preorder or assembly
minimum expenditure. Any non-zero preorder cash, gross surplus cost, or
nonrecoverable assembly excess cost requires explicit review.

## Unchanged fabrication and assembly holds

- Select four-layer JLC04161H-7628, nominal 1.6 mm, outer copper 35 µm,
  inner copper 15.2 µm, 0.2104 mm 7628 prepregs, 1.065 mm core and ENIG.
- Select controlled impedance and obtain JLC's final 90-ohm differential
  solve/coupon for the provisional 0.2332 mm trace / 0.15 mm gap / 0.30 mm
  clearance geometry. A different solve is STOP and requires source review.
- Selectively paste-fill and copper-cap only the complete 0.46/0.20 mm via
  family. Do not fill/cap the ordinary 0.70/0.35 mm family.
- Double-sided SMT must preview as 129 top + 9 bottom placements.
- Purchase THT/wave-selective assembly for J_PWR, J_UP and J_PORT1–J_PORT4.
  F_IN is intentionally absent from BOM/CPL; manually install exact Keystone
  3568 plus Littelfuse 0297004.WXNV after PCBA.
- Inspect every row in `verification/bom_echo_gate_v014.txt` and every
  single-channel rotation/polarity row in
  `verification/rotation_human_gate_v014.txt`, including all five C130056 and
  both C6053 placements.
- Preserve JLC's final BOM, rotation/polarity, THT, selective-via, stackup and
  impedance previews before payment. Any redirect, DNP, side, rotation,
  polarity or placement mismatch is STOP.

The connector-orientation subject remains machine PASS 5/5 and was approved by
the user/product owner on 2026-08-17. First power remains HOLD until the
release-bound first-article checklist is authorized. Production remains held
pending USB 2.0 Hi-Speed traffic/eye testing, simultaneous four-port load/drop
measurements, transient/thermal tests and connector-lot qualification.

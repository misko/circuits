subject: usb-controlled-debug-hub-v1 v0.1.6-2026-08-18
date: 2026-08-18
reviewer: redteam-agent (layout/thermal/power-integrity/manufacturability lens)
context-given: full-tree
source_commit: 14ffbbeb6db47e480898932303a0ef77d91bc83f
board_sha256: 088c5724c4259d727fff9093a71a7c41b903ad8022ad798c0ebedff2d0e08d18
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
p0_count: 1
p1_count: 3
p2_count: 2

# Adversarial layout/fabrication review

## Scope and conclusion

This review used only the v0.1.6 staged source, plotted fabrication payload,
CPL/BOM, native STEP/twin renders, and exact-board verification evidence. The
board was re-hashed immediately before this report. Earlier v0.1.4/v0.1.5
conclusions were discarded.

No irreversible layout, connectivity, footprint, connector, or fabrication
payload defect was found in the exact board. The design is suitable to seal as
a **first-article design** once the draft release package is rebuilt and its
manifest passes. It is not orderable yet: catalog stock is not an allocation,
and the JLC order-time impedance, via-process, rotation/polarity, THT, and BOM
previews have not been captured.

## Independent results

| Area | Result | Exact observation |
|---|---|---|
| Board identity | PASS | Staged PCB SHA-256 is `088c5724c4259d727fff9093a71a7c41b903ad8022ad798c0ebedff2d0e08d18`; `fab/artifact_index.json` binds the same board hash. |
| Native DRC/parity | PASS | Fresh `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`: 0 violations, 0 unconnected items, 0 parity issues. |
| USB connectivity | PASS | Fresh critical-route check: 10/10 pairs connected; all 20 critical nets are simple conductors. |
| USB reference | PASS | Fresh reference-plane check: both declared outer-layer cases pass; nearest measured foreign-via clearances are 0.161592 mm on F.Cu and 0.204262 mm on B.Cu against the 0.15 mm floor. |
| USB length | PASS | Fresh audit: 6/6 groups and 12/12 members measured; spreads are 0.0030--0.7510 mm and all are within their declared 0.5/1.0 mm limits. |
| Fabrication payload | PASS | Four copper Gerbers are distinct; all four zone-bearing layers contain region data; drill and Gerber archive hashes agree with `fab/artifact_index.json`. |
| Placement | PASS | 146 footprints; 138 fitted CPL rows; 129 top and 9 bottom; pad-array datum error 0.000 mm; 8 non-CPL footprints are fully explained. |
| Models/registration | PASS | 139/139 fitted footprints resolve to 3D bodies. Native registration is hash-bound to this board for USB-A, USB-B, J_PWR, and U_AGG. |
| Connector access | PASS | Four USB-A mouths face the north edge; USB-B faces west. J_PWR at `(25.5,92.5)`, rotation 270 degrees in CPL, has pad 1 `P5V_RAW`, pad 2 `GND`, outward-left wire entry, top screw access, and visible `+5V`/`GND` legends. J_PWR orientation was explicitly approved by the user/product owner. |
| Power copper | PASS WITH FIRST-ARTICLE PROOF | The three 3 A common rails have explicit pours. Each external branch is limited to 0.5 A, uses 0.50 mm field copper, and has only 0.70--0.80 mm of 0.31 mm package-entry copper. |
| Via/process | PASS WITH ORDER GATE | 526/526 vias graded: 498 are 0.46/0.20 mm filled+capped Type VII, 28 are ordinary 0.70/0.35 mm; 85/85 via-in-pad sites are covered. The 0.20 mm drill at 1.6 mm is 8:1 and requires the declared advanced process. |
| BOM/CPL | PASS AS GENERATED | 34 coded BOM rows; 138 placements. R_VBUS_TOP is 47 kOhm/C25792, R_VBUS_BOT is 100 kOhm/C25741. J_PWR is CPL rotation 270 degrees. Catalog snapshot reports stock for every row, but this is not an order allocation. |
| THT/manual assembly | PASS WITH ORDER GATE | J_PWR, J_UP, and J_PORT1--J_PORT4 require purchased THT assembly. F_IN is intentionally absent from BOM/CPL and requires manual Keystone 3568 plus Littelfuse 0297004.WXNV installation. |

## Findings

### P0-01 — Draft manifest is not currently a valid release seal

`MANIFEST.txt` is explicitly a DRAFT and its checksum table currently fails on
four included files: `ORDER_README.md`, `source/usb_controlled_debug_hub.tsx`,
`verification/assembly_coverage.json`, and
`verification/assembly_coverage.txt`. It also predates the two red-team/render
reports. This is a release-evidence defect, not a PCB defect.

Disposition required before seal: run the normal release rehearsal after all
review evidence is admitted; regenerate the complete manifest; then require
every listed file to pass SHA-256 verification and the standalone archive
open/replot/DRC rehearsal. Do not hand-edit individual checksum rows.

### P1-01 — USB impedance remains provisional until JLC's order solve

The routed geometry is 0.2332 mm trace / 0.15 mm gap with a 0.30 mm ground
field clearance on the provisional JLC04161H-7628 construction. Connectivity,
reference-plane clearance, and length matching pass, but these are not a
field solve. Package escapes, width transitions, vias, and compact meanders
remain discontinuities whose acceptability must be demonstrated on the first
article.

Recommendation: require JLC's final 90-ohm differential solve/coupon with the
exact stackup before payment. Any different geometry is STOP and source review.
Retain USB 2.0 Hi-Speed enumeration, sustained traffic/error logging, and eye
evidence as the production-promotion gate.

### P1-02 — Switched-port drop and thermal margin still need physical proof

The short 0.50 A branches are intentionally track-routed instead of poured;
their narrowest package launches are 0.31 mm. The authored electrical margin
budgets 25 mOhm for PCB copper/vias/joints, but no physical article has proved
that allocation or the simultaneous four-port thermal state.

Recommendation: keep quantity at five first articles. Four-wire measure each
port at 0.50 A and all four simultaneously for at least 30 minutes, recording
connector voltage, fuse/eFuse/buck/TPS2557 temperatures, and overload recovery.
Do not promote to production until every port remains within 4.75--5.25 V.

### P1-03 — Selective via fill/cap is a non-default manufacturing dependency

The design depends on selective Type VII treatment of every 0.46/0.20 mm via
and no treatment of the 0.70/0.35 mm family. A generic via-fill selection or
an unacknowledged process substitution can change assembly quality at exposed
pads and via-in-pad sites.

Recommendation: obtain a written/uploader acknowledgement of the exact
drill-family split, inspect the final drill/process preview, and reject a
blanket or partial process. Inspect exposed-pad wetting and capped-via quality
on incoming first articles.

### P2-01 — Aggregate policy report contains stale sealed-release labels

`verification/policy_audit.md` names v0.1.4 for `M-REL`, `A-POP`, and `A-BODY`
even though exact v0.1.6 assembly/model receipts are also present and pass.
This does not invalidate the independently re-run exact-board checks, but it
is confusing provenance in a release candidate.

Recommendation: regenerate the integrated policy audit during rehearsal so
its human-facing detail names v0.1.6 or the staged subject consistently.

### P2-02 — J_PWR approval is not included in the connector approval ref list

The existing machine orientation receipt and user approval file enumerate
USB connectors only. The exact v0.1.6 twin and native model registration show
J_PWR correctly, and this review records the user's explicit approval, so the
physical conclusion is not ambiguous. The approval trail is nevertheless
split across evidence channels.

Recommendation: include J_PWR in the next generated connector-orientation
receipt/approval schema so one hash-bound record covers every user-accessed
connector.

## Mandatory order/uploader gates

These gates explain `order_verdict: BLOCKED-SOURCING`; they are not waivers
and cannot be cleared by this offline review.

1. Upload the exact Gerber ZIP, BOM, and CPL for quantity 5 and save JLC's
   resolved table. Require all 34 coded rows to be `ALLOCATED`, exact MPN/LCSC,
   with MOQ, actual buy quantity, excess cash, fees, and assembly quantity
   reviewed under the schema-v2 procurement policy.
2. Capture the final JLC04161H-7628 material/stackup echo and 90-ohm
   differential impedance solve/coupon. Reject a changed cross-section.
3. Confirm selective Type VII fill/cap for only the 0.46/0.20 mm via family.
4. Confirm 129 top + 9 bottom SMT placements and every single-channel rotation
   in `fab/rotation_human_gate.txt`: all FSUSB42, TPS2557, logic, crystal,
   USB2517, buck, expander, controller, and J_PWR. Confirm C_TRUNK_USB polarity.
5. Confirm THT/wave-selective assembly and orientation for J_PWR, J_UP, and all
   four USB-A connectors. Confirm F_IN remains manual/not assembled.
6. Preserve the release first-power and first-article plan. Production remains
   HOLD until USB Hi-Speed, simultaneous load/drop, transient, thermal,
   overload, and connector-lot tests pass.

## Final adversarial judgment

The exact v0.1.6 routed hardware is **SOUND for a controlled first article**.
No route backtrack is indicated by this lens. Fix P0-01 by the normal release
rehearsal/seal process, retain P1 items as first-article/order controls, and do
not pay JLC until every mandatory uploader gate above is captured and accepted.

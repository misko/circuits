# brief: usb-power-3s

status: delivered
prompt_sha256: bb5ae2d40b89086de582a1ad4381d416825d4847a527278c363d67b3ca5462ab
current_release: 07_releases/v1.1-2026-07-16

## Original prompt

<!-- prompt-verbatim-begin -->
> Ok lets try out our new system. Please from scratch start a new project, and lets design a board that takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max) and 1 x USB C port (6A max). Please internally research and make all design decisions. The output should be a fully designed , placed, routed board with JLCPCB manufacturing files
<!-- prompt-verbatim-end -->

- date: 2026-07-14
- channel: Claude Code session (circuits repo trial run of the template system)

## End goal — definition of done

A standalone, transferable board project that converts 3S LiPo battery power
into USB outputs, taken all the way to an orderable JLCPCB package: docs and
decisions, verified part facts, generated schematic and board, routed and
DRC-clean layout, and a frozen release directory containing gerbers, BOM,
CPL and human-readable PDFs.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Input: 3S LiPo via XT60 | P | met — J1 XT60PW-M, 01_docs/ARCHITECTURE.md power tree |
| G2 | 3× USB-A outputs, 2.5 A max each | P | met — TPS2557 per-port ILIM 2.51 A (01_docs/DETAIL_DESIGN.md) |
| G3 | 1× USB-C output, 6 A max | P | met — buck A rated 6 A, Rp advertises 3 A per A2 |
| G4 | All design decisions made internally (no user consultation) | P | met — 0 clarifications asked; assumptions declared as A1–A6 |
| G5 | Fully designed, placed, routed board | P | met — DRC 0 violations / 0 unconnected / 0 parity |
| G6 | JLCPCB manufacturing files | P | met — 07_releases/v1.0-2026-07-16 (gerbers+BOM+CPL, stock-checked) |
| G7 | PDF schematic + PCB PDFs in every release | D2 | met — 07_releases/v1.0-2026-07-16/pdf/ |

## Log

### A1 — 2026-07-14 — assumption (not asked)
Assumed: no USB-PD on the USB-C port; fixed 5 V with Rp advertising 3 A while
copper carries 6 A. Authority: P delegates all design decisions.
Escalate if: any target device refuses to draw >3 A — then a PD controller
revision is needed. Depth: decisions/0002.

### A2 — 2026-07-14 — assumption (not asked)
Assumed: no USB data; D+/D− strapped as DCP chargers on all ports.
Authority: P ("outputs ... ports" describes power only). Depth: decisions/0003.

### A3 — 2026-07-14 — assumption (not asked)
Assumed: 100×60 mm 4-layer board, JLCPCB advanced (small-via) tier.
Authority: P delegation; sized by placement audit. Escalate if: enclosure
constraints exist.

### A4 — 2026-07-14 — assumption (not asked)
Assumed: order quantity 5. Authority: P delegation (typical prototype run).

### A5 — 2026-07-16 — assumption (not asked)
Assumed: USB-A jacks hand-soldered after assembly (CNCTech part not in the
JLC catalog); acceptable for a prototype. Escalate if: volume production.

### A6 — 2026-07-14 — assumption (not asked)
Assumed: 5.08 V rail setpoint (covers connector/trace drop at full load,
within USB 5 V ±5%). Depth: 01_docs/DETAIL_DESIGN.md.

### D2 — 2026-07-16 — user directive
> For each release can we please output PDF schematics and PDF versions of the PCB ?
Impact: added G7; 03_src/export_pdfs.sh; `pdf/` required in every release
(07_releases/contracts.md); v1.0 release extended in place (not yet ordered).

### D3 — 2026-07-16 — user directive
> do our folders represent a chronological sequence of design? can we number prefix our folders?
Impact: folders renamed 01_docs … 07_releases in pipeline order, template +
project; 59 files' references rewritten; gate re-run green.

### D4 — 2026-07-16 — user directive
> We need to keep track of the users original prompt, and clarification questions we have asked the user and over all decisions of the project, along with the clear end goal of the project.
Impact: this file and its contract (01_docs/contracts.md, BRIEF.md sections);
release gate now requires all criteria met or user-dropped.

### D5 — 2026-07-16 — user directive
> Our final output is often for JLCPCB , often we have issues with parts that are not in stock, or not correctly (unambiguously) selected from our BOM/CPL files. In addition we often fail the 3d rendering presented at the end of JLCPCB. [...] Can we download JLCPCB catalog and its 3d renderings and use those to generate a 3d rendering of placed parts using kicad or some other tools?
Impact: new order-gate stage "JLC digital twin" (skills/jlcpcb-fab/scripts/jlc_twin.py):
per-LCSC fetch of JLC's own footprint+3D CAD (easyeda2kicad), pad-correspondence
fit (rotation x mirror), rotation-DB audit, adjudication register
(03_src/rules/twin_adjudications.yaml), twin renders. Its FIRST RUN found the
vendored LM5145 footprint mirror-numbered (dead board) -> footprint fixed,
full re-route, v1.1. The SPF power_board_v1 shares the defect (already ordered).

### D6 — 2026-07-16 — user directive
> can we add a verification step where we review a sets of parts in a new context agent, against schematic and PCB routing to make sure all pins are correctly setup?
Impact: fresh-context pin review stage (skills/kicad-pcb: pin_audit.py +
pin-review-protocol.md); dossiers are conclusion-free, reviewers are
independent agents deriving expected pinouts from datasheet figures. First
run: 17 parts reviewed, 0 unresolved FAILs, one part.yaml label fixed
(07_releases/v1.1-2026-07-16/verification/pin_review.md).

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| ADR-0001 | Two independent bucks (one per output domain), not one rail | agent (P-delegation) | decisions/0001-two-buck-topology.md |
| ADR-0002 | USB-C: Rp 3 A advertisement, 6 A copper, no PD | agent (A1) | decisions/0002-usbc-3a-advertisement-6a-copper.md |
| ADR-0003 | DCP strap D+/D−, no data, no data-line ESD | agent (A2) | decisions/0003-power-only-dcp-no-data-esd.md |
| ADR-0004 | LM74800 front end doubles as battery UVLO/OV | agent (P-delegation) | decisions/0004-front-end-lm74800-uvlo.md |
| ADR-0005 | Bias part selection toward the SPF-verified set | agent (P-delegation) | decisions/0005-reuse-verified-parts-set.md |
| D2 | Releases ship PDF schematic + PCB + assembly docs | user (D2) | Log D2 |
| D3 | Folders number-prefixed in pipeline order | user (D3) | Log D3 |
| D4 | Commission record kept in 01_docs/BRIEF.md | user (D4) | Log D4 |
| D5 | JLC digital-twin order gate; LM5145 footprint fixed + re-route (v1.1) | user (D5) | Log D5 |
| D6 | Fresh-context pin review required before every order | user (D6) | Log D6 |

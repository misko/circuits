# Routed-board render/document review — final

- subject: `usb_hub_3s_v4.kicad_pcb` routed-board render/document review
- date: 2026-08-12
- reviewer: render-review
- context-given: zero-context
- source_commit: `cc8368ffbb7b93cf8f4b567534e8537df792d638`
- board_sha256: `6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b`
- design_verdict: SOUND
- order_verdict: DO-NOT-ORDER

## Scope and closed verdict

This is an independent visual/document review of the exact routed-board evidence listed below. No journal, STATUS file, prior review, or DISPOSITIONS content was used. Within what the supplied copper plots disclose, the fills and routes are coherent and no visible short, open, edge incursion, polarity reversal, or gross thermal-layout defect was found. `SOUND` means only “no design defect observed in this evidence”; it does not turn the incomplete mechanical/assembly evidence into an order release. The board remains **DO-NOT-ORDER**.

## Exact reviewed evidence

Filesystem timestamps are local (`-07:00`).

| Artifact | SHA-256 | Bytes | Filesystem mtime |
|---|---|---:|---|
| `04_kicad/usb_hub_3s_v4.kicad_pcb` | `6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b` | 1,528,145 | `2026-08-12 02:24:57.387875475 -0700` |
| `06_build/routed_review/top_copper.png` | `79e0de7ddbf7765c2840d643ab43cc4b738b8319c4cc161ab7b408ae76525356` | 268,397 | `2026-08-12 02:29:05.763859077 -0700` |
| `06_build/routed_review/top_copper.svg` | `24b30cb6f0c69d6c8a4adc838bc6b3e5020b2934fa9bb4d28a42b836f3ca1c92` | 478,556 | `2026-08-12 02:29:04.819840103 -0700` |
| `06_build/routed_review/bottom_copper.png` | `4935bbc60fdec897bb8b428a59ec388ee641734fdcbaacab5c1f273516aeab68` | 176,105 | `2026-08-12 02:29:05.867861168 -0700` |
| `06_build/routed_review/bottom_copper.svg` | `79b213a94e425c030308dfce11f4f3dc002a8b39a43b6832a8ac9e738b663670` | 241,755 | `2026-08-12 02:29:05.576855319 -0700` |
| `06_build/routed_review/top_3d.png` | `9127eacb1b4f83b332de05cd9b1cfed8981842127fd437a7d36ea251d6983dc2` | 321,137 | `2026-08-12 02:29:12.899002499 -0700` |
| `06_build/routed_review/bottom_3d.png` | `a79ea87117da4d8d72f92de4d484111cfc67e6d6b9a1b621a225ae3d7fadc1a1` | 173,952 | `2026-08-12 02:29:19.618137570 -0700` |
| `06_build/routed_review/iso_3d.png` | `e23e4427403e75e20da45e9a192ff0d20c42e3f5e9ae12c9ab41a3b203cbd20c` | 1,288,403 | `2026-08-12 02:29:27.194289881 -0700` |
| `06_build/routed_review/pcb_layers.pdf` | `d93fac375bb8e653427cf7e7b2d911a1d9e2e87af240b8a70de33fc80fcfbbc9` | 905,877 | `2026-08-12 02:29:28.176309624 -0700` |
| `06_build/routed_review/assembly.pdf` | `5a5a371a00fc60303f3f143b7013a0f6618d929118e54e2381953c7e4db43c33` | 406,171 | `2026-08-12 02:29:28.973325649 -0700` |

Supplemental exact schematic consulted for signal/purpose interpretation: `03_tscircuit/build/schematic.pdf`, SHA-256 `66721db9a7c3b2212bed2665671465bd8510064a022be7c13dc7dcc9d5b057c2`, 297,746 bytes, mtime `2026-08-12 02:00:38.043025763 -0700`.

## Findings

### P0

None observed.

### P1

1. **P1 — The supplied “3D” views are bare-board/footprint views, not an assembly twin.** No convincing component bodies appear in `top_3d.png`, `bottom_3d.png`, or `iso_3d.png`; pads and silkscreen dominate even where the source board declares models. In particular, J1, J2/J3/J4, SW1, U1, U2, U9, and Q1 have no model declarations in the board, while bodies also do not appear for declared-model parts such as F1 and J5 in these images. Consequently these views cannot prove connector overhang and mating access, switch/fuse envelope, body orientation, installed height, body-to-body clearance, or enclosure/standoff collision. This is an evidence defect and an order blocker, not proof of a PCB geometry defect.

### P2

1. **P2 — Assembly packet needs cleanup before handoff.** `assembly.pdf` has seven A4 sheets, but only sheets 1 and 3 expose substantive identifiers/text; sheets 2 and 4–7 expose only title-block text. Sheet 3 densely overlays references, values, and supplier IDs. Sheet 1 is readable as a locator drawing, but the packet is not a clean, concise assembly/polarity document.
2. **P2 — PDF embedded dates do not corroborate the fresh filesystem times.** Both KiCad PDFs report an internal creation date of `2025-12-31 16:00:00 PST`, while their filesystem mtimes are `2026-08-12 02:29:28 -0700`. This may be intentional reproducible-build metadata, but the documents themselves do not explain it; hashes, not embedded dates, must anchor this review.
3. **P2 — Remaining thermal/mechanical checks are unresolved by renders.** The visible high-current topology uses broad polygonal regions on both outer layers, via stitching, and exposed-pad via fields at the converter/eFuse packages; no obvious neck or isolated-pour failure is visible. Nevertheless copper weight, finished via plating, installed heat sources, airflow/enclosure constraints, connector insertion loads, and actual body clearances cannot be qualified from these images/PDFs.

## Positive observations

- Top and bottom copper plots show continuous large-area fills with orderly clearances around routed nets and pads. The main power domains are visibly segregated without an obvious unintended bridge; the dense converter/control routing stays localized.
- J2/J3/J4 at the right edge and J5 at the bottom edge have footprints aligned for edge access, and the visible copper/mask geometry does not show an obvious board-edge violation. Final body overhang remains unverified because the bodies are absent.
- Exposed-pad packages have local thermal/stitch via arrays. Large current paths are principally polygonal rather than long thin traces.
- Silkscreen is generally readable and operationally useful: `3S INPUT`, `+ BAT`, `- GND`, `FIT 10A MINI FUSE`, `MASTER OFF / ON`, `POWER ONLY — NO USB DATA`, per-port `5V / 2A`, and `USB-C 5V / 3A NO PD` are explicit. Capacitor `+` marks and asymmetric cathode-end silk for D1/D5 are present; references are dense near U1/U2 but remain usable in the locator drawing.

## Coverage limitations and required next evidence

- Copper plots are visual exports, not a net-aware continuity/clearance proof; inner-plane details, fabrication tolerances, mask slivers, drill registration, impedance, and rule-deck correctness were not independently certified here.
- The PDFs have no trustworthy embedded generation date and do not provide an assembly-height/enclosure view. This review did not authorize fabrication or assembly.
- Before any order decision, produce a **JLC same-camera assembly twin** (same orientation, framing, and scale as the reviewed top/iso views, with actual JLC-selected bodies enabled) plus a **missing-model manifest** covering every BOM reference. The manifest must distinguish verified exact body, verified dimensional surrogate, intentionally bodyless item (for example fiducial/test point/mounting hole), and unresolved/missing model. Re-review connector overhang/mating access, J1/SW1/F1/J2–J5 envelopes, pin-1/polarity visibility, component heights, and collisions against that evidence.

## Exit integrity

The board hash was required to remain `6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b`; it was rechecked after this review file was written (see final handoff confirmation).

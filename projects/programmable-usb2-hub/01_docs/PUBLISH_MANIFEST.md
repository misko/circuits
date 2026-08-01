# Publish manifest

## Hub-specific files

Publish the complete non-ignored `projects/programmable-usb2-hub/` tree. Its
`.gitignore` deliberately excludes `06_build/` products (except the contracts
file), tscircuit caches/dependencies, KiCad session/backup files, and failed
intermediate boards. This includes the source-owned route chain, canonical
KiCad board, generated schematic/circuit artifacts, local footprints, part
evidence, firmware, documentation, and contracts.

The diagnostic `06_build/jlc_preflight/` and `06_build/jlc_release_check/`
directories are evidence for this handoff, not files to publish.

Exact non-ignored hub-specific set (122 files):

```text
.gitignore
01_docs/ARCHITECTURE.md
01_docs/BRIEF.md
01_docs/CHANGELOG.md
01_docs/CHECKLIST.md
01_docs/DETAIL_DESIGN.md
01_docs/PUBLISH_MANIFEST.md
01_docs/STATUS.md
01_docs/contracts.md
01_docs/decisions/0001-usb-a-3a-spec-tension.md
01_docs/decisions/0002-dual-seven-amp-bucks.md
01_docs/decisions/0003-control-and-status-plane.md
01_docs/decisions/contracts.md
01_docs/journal/commission.md
01_docs/journal/contracts.md
01_docs/journal/fabrication.md
01_docs/journal/routing.md
01_docs/learnings/contracts.md
01_docs/learnings/routing.md
01_docs/sourcing/contracts.md
01_docs/sourcing/dual-source-2026-07-31.md
01_docs/sourcing/manual_quotes.yaml
01_docs/sourcing/shopping-list-2026-07-31.json
01_docs/sourcing/shopping-list-2026-07-31.md
02_parts/1935161/KANGNEX-WJ126V-drawing-revA.pdf
02_parts/1935161/part.yaml
02_parts/1N4148WS/part.yaml
02_parts/292304-1/TE-292304-drawing-revD4.pdf
02_parts/292304-1/part.yaml
02_parts/3568/Keystone-3568-M65p42.pdf
02_parts/3568/part.yaml
02_parts/74LVC08APW-118/74LVC08A.pdf
02_parts/74LVC08APW-118/part.yaml
02_parts/AON6354/AON6354_rev.pdf
02_parts/AON6354/part.yaml
02_parts/AP63203QWU-7/AP63200-AP63205.pdf
02_parts/AP63203QWU-7/part.yaml
02_parts/B340A-13-F/part.yaml
02_parts/BSC016N06NS/Infineon-BSC016N06NS-rev2.6.pdf
02_parts/BSC016N06NS/part.yaml
02_parts/CL32A107MPVNNNE/part.yaml
02_parts/CL32B106KBJNNWE/part.yaml
02_parts/CX3225SB24000H0FLJCC/part.yaml
02_parts/FSUSB42MUX/FSUSB42-D_Rev3.pdf
02_parts/FSUSB42MUX/part.yaml
02_parts/FTSH-105-01-L-D-K/part.yaml
02_parts/LM5116MHX-NOPB/SNVS499I.pdf
02_parts/LM5116MHX-NOPB/part.yaml
02_parts/LM74810QDRRRQ1/TI-LM7481-Q1-SNOSD98A.pdf
02_parts/LM74810QDRRRQ1/part.yaml
02_parts/MWSA1206S-6R8MT/part.yaml
02_parts/RT0603BRD073K92L/part.yaml
02_parts/SMBJ26A/Littelfuse-SMBJ-series-v4-2025-07-04.pdf
02_parts/SMBJ26A/part.yaml
02_parts/STM32G0B1CBT6/DS13560Rev6.pdf
02_parts/STM32G0B1CBT6/part.yaml
02_parts/TPS259470ARPWR/SLVSFC9C.pdf
02_parts/TPS259470ARPWR/SLVUC01.pdf
02_parts/TPS259470ARPWR/part.yaml
02_parts/USB1130-15-A/GCT-USB1130-drawing-revA2.pdf
02_parts/USB1130-15-A/GCT-USB1130-spec-revA1.pdf
02_parts/USB1130-15-A/part.yaml
02_parts/USB2517I-JZX/DS00001598C.pdf
02_parts/USB2517I-JZX/part.yaml
02_parts/USBLC6-2SC6/USBLC6-2SC6_ST.pdf
02_parts/USBLC6-2SC6/part.yaml
02_parts/VLS6045EX-4R7M/part.yaml
02_parts/WSL2512R0100FEA/part.yaml
02_parts/contracts.md
03_src/contracts.md
03_src/floorplan.yaml
03_src/lib/contracts.md
03_src/lib/programmable_usb2_hub.pretty/PowerPAK_SO-8_Single_Paste65.kicad_mod
03_src/lib/programmable_usb2_hub.pretty/TerminalBlock_KANGNEX_WJ126V_2P_P5.0.kicad_mod
03_src/lib/programmable_usb2_hub.pretty/Texas_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm_ThermalVias.kicad_mod
03_src/lib/programmable_usb2_hub.pretty/USB_A_GCT_USB1130_Horizontal.kicad_mod
03_src/lib/programmable_usb2_hub.pretty/USB_B_TE_292304-1_Horizontal.kicad_mod
03_src/rebuild_all.sh
03_src/rebuild_reuse.sh
03_src/route.yaml
03_src/route/final_chain.kicad_pcb
03_src/route/final_chain.kicad_pro
03_src/rules/assembly.yaml
03_src/rules/contracts.md
03_src/rules/electrical_invariants.yaml
03_src/rules/nets.yaml
03_src/rules/power_tree.yaml
03_src/rules/twin_adjudications.yaml
03_tscircuit/GENERATE.md
03_tscircuit/build/circuit.json
03_tscircuit/build/schematic.pdf
03_tscircuit/build/schematic.svg
03_tscircuit/contracts.md
03_tscircuit/kicad/programmable_usb2_hub.kicad_sch
03_tscircuit/manifest.yaml
03_tscircuit/package.json
03_tscircuit/parity_padmap.txt
03_tscircuit/src/programmable_usb2_hub.tsx
04_kicad/contracts.md
04_kicad/fp-lib-table
04_kicad/programmable_usb2_hub.kicad_dru
04_kicad/programmable_usb2_hub.kicad_pcb
04_kicad/programmable_usb2_hub.kicad_pro
04_kicad/programmable_usb2_hub.kicad_sch
04_kicad/refdes_waiver.json
05_firmware/README.md
05_firmware/contracts.md
05_firmware/host/phubctl.py
05_firmware/src/phub_protocol.py
05_firmware/src/phub_state.py
05_firmware/target/phub_core.c
05_firmware/target/phub_core.h
05_firmware/target/test_phub_core.c
05_firmware/test_phub_protocol.py
05_firmware/test_phub_state.py
05_firmware/test_phubctl.py
06_build/contracts.md
07_releases/contracts.md
08_reviews/DISPOSITIONS.md
08_reviews/contracts.md
README.md
contracts.md
```

## Required shared files

- `skills/kicad-pcb/scripts/pcb_toolkit.py`
- `skills/kicad-pcb/scripts/route_and_stitch_generic.py`
- `skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml`
- `skills/jlcpcb-fab/scripts/assembly_coverage.py`
- `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`
- `skills/jlcpcb-fab/scripts/jlc_rotation_measure.py`
- `skills/pcb-design/SKILL.md` — publish the Q-2SOURCE hunk; other dirty-tree
  changes in this same file are unrelated to this project
- `skills/pcb-design/templates/contracts/01_docs/sourcing/contracts.md`
- `tests/t1_assembly_gates.py`
- `tests/t1_rotation_authority.py`

Do not include any other dirty-tree file merely because it is modified in this
checkout. Isolate this manifest onto a clean branch based on `origin/main`.

## Validation snapshot

- Canonical layout seal: P-LAND 302/302; KiCad DRC 0 violations, 0 unconnected,
  0 schematic parity issues; content-addressed handoff valid.
- Circuit passive authority: all coded R/C values match their TSX value props.
- Assembly checker regression: 37/37 positive tests passed and all 18 known-bad
  fixtures remained failures.
- Rotation checker regression: 28/28 tests passed, including all 17 known-bad
  fixtures; the table audit passes 81/81 independently measured rows.
- Strict JLC export: 59/59 BOM lines legible and coded; 194 CPL placements;
  A-ROT 194/194 sourced; BOM-source identity PASS.
- Q-2SOURCE: 26/26 selected dossier MPNs have at least two qualifying
  authorized supplier pools in the dated 2026-07-31 evidence. Recheck on
  order day.
- Live JLC stock: 58/59 placed BOM lines clear five-board quantity. The sole
  zero-stock line is C5248536 / AP63203QWU-7 at U4, explicitly PLANNED as a
  consigned part with qualifying Mouser and DigiKey stock.
- Assembly process: J1/J2/J7 are declared for JLC post-through-hole assembly;
  F1 is excluded from BOM/CPL and requires two exact Keystone 3568 clips per
  board installed after PCBA; J3-J6 remain exact post-PCBA receptacles.
- Exact-code twin: 194/194 placed bodies resolve and all 21 prior critical refs
  are closed by manufacturer-datasheet-backed entries in
  `03_src/rules/twin_adjudications.yaml`; twin exits 0 with zero unadjudicated
  critical refs. The twin regression suite passes 26/26, including all 16
  known-bad fixtures.
- Publish handoff is technically green. It is not an order-day release: 15
  exact codes still require the mandatory first-order JLC placement-preview
  human gate, Q-2SOURCE must be refreshed, and JLC allocation must be confirmed
  immediately before payment.

not_assembled: F1, J3, J4, J5, J6

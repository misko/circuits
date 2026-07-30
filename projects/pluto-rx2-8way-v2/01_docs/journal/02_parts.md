# journal: parts + rules (stages 2-3) — pluto-rx2-8way-v2

## 2026-07-30 09:05 — start
- did: copied the dossiers for every part v2 KEEPS from v1's `02_parts/`
  (PE42482A-X, KH-SMA-KE-Z, 0402WGF2200TCE, BLM21SP601SN1D, KT-0603R) with
  their committed PDFs. These are ledger hits (`proven-parts.yaml`
  `rf-switch-sp8t-absorptive`, `rf-connector-sma-jack-vertical`) — a ledger hit
  is a VERIFIED SELECTION and needs no re-research.
- result: 5 dossiers + 5 PDFs. `0402WGF4700TCE` (470R) came across with them and
  was DELETED: v2 does not use it, and an unused dossier in a project with no
  sealed releases is drift waiting to happen (canon M-DEPEND applies to sealed
  archives; there are none here, so removal is clean and this note is the
  record of it).
- next: the one part v2 needs that no board in this fleet has ever used — the
  RP2040-Zero module. Delegated to a research agent with the 02_parts contract
  and v1's PE42482A-X dossier as the house-style exemplar.

## 2026-07-30 09:20 — iterate 1 (the parts v2 DELETES)
- did: enumerated what leaves the BOM relative to v1.
- result: `RP2040` (QFN-56), `W25Q128JVSIQ` + `C_FLASH`, `ABM8-272-T3` crystal +
  `C_XTAL1`/`C_XTAL2`/`R_XTAL`, `C_MCU1..C_MCU10`, `C_LDI`, `MCP1755S-3302E/DB`
  + `C_VREG_IN`/`C_VREG_OUT`, `TYPE-C-31-M-12A`, `USBLC6-2SC6` + `C_ESD`,
  `R_USB1`/`R_USB2`, `R_CC1`/`R_CC2`, `TS-1187A-B-A-B` x2 + `R_BOOT`/`R_CSPU`,
  `1206L050-24WR` PPTC, `SMBJ6.0A` TVS, `LED_PWR` + `R_LED1`.
  **~40 fewer components.** v1's board carries 68 footprints; v2 is ~28.
- next: the rules files.

## 2026-07-30 09:45 — iterate 2 (rules authored)
- did: wrote all four `03_src/rules/` files from scratch (the seeded templates
  were deleted, not edited, so nothing describing another board survives).
- result: four judgement calls worth naming, each recorded in the file itself.
  1. **`fab_tier` does NOT relax.** I expected removing the 0.400 mm QFN-56 to
     buy a cheaper tier. It does not: PE42482A-X's QFN-24 at 0.50 mm pitch
     forces `jlc_4layer_advanced` by itself (0.50 - 0.30 drill = 0.20 mm
     hole-to-hole against a 0.50 mm floor). Checked rather than assumed.
  2. **`scoped_clearances` is deliberately EMPTY.** v1 carries six 0.14 mm
     launch relaxations earned by measurement at ITS routing stage. v2 has
     measured nothing. Copying them would be canon M4's inherited waiver.
  3. **`power_tree.yaml` declares a rail whose regulator is not our part.**
     Shipping no rails would collect a clean E-TOPO N-A — which is precisely
     the failure `power_topology.py`'s own docstring names on three fleet
     boards. `dropout_mv`/`pdiss_max_mw` are PER-RAIL overrides rather than an
     RT9013 dossier, because we never order that regulator.
  4. **`assembly.yaml` `msl:` is OWED in words, not filled with a number.**
- next: `03_tscircuit` authoring, then the schematic gate.

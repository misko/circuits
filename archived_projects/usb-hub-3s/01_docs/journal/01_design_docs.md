# journal: 01_design_docs

## 2026-07-21 — start
- did: extracted IP6559 datasheet (21pp: pin table, Fig.7/8/9 power stage +
  Vconn/e-marker circuit at 300dpi, BOM p.17, layout rules p.18, QFN48 pkg
  drawing) and LM5116 SNVS499I 5V/7A reference (Table 7-1 BOM + eq.1/3/23 +
  comp values RCOMP 18k/CCOMP 3.3n/CHF 100p) + TPS2557 ILIM equations +
  TPS2513 pinout (DUAL channel: 2 chips serve 3 ports).
- result: ARCHITECTURE.md (power tree, net domains, stackup, critical
  geometries) + DETAIL_DESIGN.md (every value derived: UVLO divider
  49.9k/6.98k -> 9.65/8.84V measured math; RILIM 36.5k -> 2.72-3.29A;
  CRAMP 330pF; L1 10uH/15.5A peak calc; Vconn switch mapping). ADR 0001
  amended: single-authority UVLO at LM5116, IP6559 EN gated by 5VA presence.
- next: 02_parts — JLC codes + stock + datasheet cache + escape blocks per
  part; USB-A receptacle rating research (T1 tension).

## 2026-07-22 (v1.1) — iterate
- did: doc-sync pass (X10/X15): ARCHITECTURE refdes + TLV431 residue purged, DETAIL_DESIGN rewritten to as-built refdes (R25-DNP trap fixed), UVLO worst-case band (8.30-9.36V falling, 2.77V/cell floor), standby-drain corrected to 1.5-5mA (X12); ADR-0001 amended (D1->VIN + exact fuse 0297020.WXNV I2t coordination + incident); new ADRs 0007 (60V AON6262E + per-node SMAJ15A/24A clamps), 0008 (L1 -> YSPI1770Y 16A + thermal statement), 0009 (D3 surge-grade, Q8 backfeed accepted)
- result: sourcing spike verified all four part swaps in stock (FET 3277, L1 213, fuse 4265, SMAJ15A 15445); TVS part.yamls now carry vbr/vclamp corners; electrical_invariants.yaml born (INV-D1/Q1/FUSE/GATE-R/BRIDGE-CAPS)
- next: regenerate board from the re-floorplanned PD cell, fresh KRT route

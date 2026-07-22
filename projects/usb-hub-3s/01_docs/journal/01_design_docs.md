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

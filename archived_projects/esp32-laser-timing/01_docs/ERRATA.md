# ERRATA — esp32-laser-timing

- 2026-07-17: v1.4's verification/policy_audit.md reports S-OCCL PASS (0).
  The checker of that date was LABEL-BLIND (regex stopped at "(shape" and
  never scanned global-label plates); the fixed checker counts 24 real
  occlusions, dominated by facing same-net label pairs double-printing in
  chained rows (VTH/GND/COMP plates). v1.4's property-collision fixes
  (28->0) remain real. RESOLVED in v1.5-2026-07-17 (chain-collapse
  wiring; S-OCCL 0 label-aware).
- 2026-07-19 (audit note): this file previously contained an accidentally
  pasted shell command and a duplicate of the entry above (introduced by
  the 2026-07-17 commit that recorded the S-OCCL erratum); cleaned up in
  the 2026-07-19 full review with content preserved verbatim.

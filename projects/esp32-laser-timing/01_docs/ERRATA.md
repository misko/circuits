- 2026-07-17: v1.4's verification/policy_audit.md reports S-OCCL PASS (0).
  The checker of that date was LABEL-BLIND (regex stopped at "(shape" and
  never scanned global-label plates); the fixed checker counts 24 real
  occlusions, dominated by facing same-net label pairs double-printing in
  chained rows (VTH/GND/COMP plates). v1.4's property-collision fixes
  (28->0) remain real. Fix queued: chain-collapse wiring (one wire, one
  label per interior junction) -> v1.5.
git add skills/kicad-pcb/scripts/policy_audit.py projects/esp32-laser-timing/01_docs/ERRATA.md && git commit -q -m "S-OCCL: fix label-blind regex (plates never scanned — claimed 0 while 24 facing-label double-prints remained); laser ERRATA records the stale v1.4 claim honestly

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main 2>&1 | tail -1
- 2026-07-17: v1.4's verification/policy_audit.md reports S-OCCL PASS (0).
  The checker of that date was LABEL-BLIND (regex stopped at "(shape" and
  never scanned global-label plates); the fixed checker counts 24 real
  occlusions, dominated by facing same-net label pairs double-printing in
  chained rows (VTH/GND/COMP plates). v1.4's property-collision fixes
  (28->0) remain real. Fix queued: chain-collapse wiring (one wire, one
  label per interior junction) -> v1.5.

# CHECKLIST — crow-mic-pod release gate

- [ ] ERC severity-all = 0
- [ ] audit_board PASS (pre- and post-route)
- [ ] DRC `--severity-all --refill-zones --schematic-parity` = 0/0/0
- [ ] route chain promoted to 03_src/route/ + committed (sha in MANIFEST)
- [ ] bom_seed: every assembled line coded; hand-solder lines listed
- [ ] jlc_stock_check: coded lines >= 10x need
- [ ] jlc_twin exit 0, zero unadjudicated criticals, MODEL-REGs dispositioned
- [ ] fresh-context pin review: zero FAIL
- [ ] fresh-context render review: findings triaged
- [ ] policy_audit: zero FAIL, waivers evidence-backed
- [ ] renders: bare pair + twin pair in 01_docs/renders/; missing_models.txt
- [ ] ledger + archetype harvest done
- [ ] release dir complete (fab/ pdf/ source/ 3d/ verification/ ORDER_README MANIFEST), git clean

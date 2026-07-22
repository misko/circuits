# CHECKLIST — pre-release gate (fresh-agent runnable)

- [ ] `bash 03_src/rebuild_all.sh` completes; final lines report
      `violations: 0 {}`, `unconnected: 0`, `parity: 0`
- [ ] ERC step inside the rebuild prints `ERC: 0 violations`
- [ ] `/usr/bin/python3 03_src/audit_board.py` PASS (incl. I-KELVIN,
      refdes-on-silk, polarity pad-1 asserts, antenna keepout)
- [ ] `.kicad_dru` byte-identical after `python3 03_src/generate_rules.py`
- [ ] `python3 03_src/bom_seed.py` exits 0 (assembled lines coded;
      hand-solder list printed)
- [ ] `python3 <jlcpcb-fab>/scripts/jlc_stock_check.py 06_build/fab/bom_jlc.csv`
      — every coded line stock ≥ 5× qty×5
- [ ] `jlc_twin.py` exit 0; zero unadjudicated MIRRORED/PAD-MISMATCH/
      PAD-GEOM; every MODEL-REG dispositioned in twin_adjudications.yaml
- [ ] Fresh-context pin review: verification/pin_review.md, zero FAIL
- [ ] Fresh-context render review: findings triaged (fix or ADR note)
- [ ] `bash 03_src/export_pdfs.sh`; PNGs eyeballed (no occlusion)
- [ ] `policy_audit.py <project>` FULL: zero FAIL; waivers evidence-backed
- [ ] All BRIEF.md acceptance criteria G1–G6 met (no `unmet` rows)
- [ ] Release cut from a CLEAN tree (`git_dirty: false`), MANIFEST
      sha256 table verifies, CHANGELOG entry names the release dir

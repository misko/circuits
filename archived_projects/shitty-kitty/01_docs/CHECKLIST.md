# CHECKLIST — pre-release gate (each line checkable by a fresh agent)

- [ ] `bash 03_src/rebuild_all.sh` completes; final lines `violations: 0 {}`,
      `unconnected: 0`, `parity: 0` (also proves ERC 0 and AUDIT PASS mid-chain)
- [ ] `/usr/bin/python3 ../../skills/kicad-pcb/scripts/policy_audit.py .`
      exits 0 (zero FAIL); report in `06_build/policy_audit.md`
- [ ] `python3 03_src/bom_seed.py` exits 0; hand-solder list printed
- [ ] `python3 ~/.claude/skills/jlcpcb-fab/scripts/jlc_stock_check.py
      06_build/fab/bom_jlc.csv --min-stock 25` exits 0 (5 boards x 5)
- [ ] `jlc_twin.py` exit 0, zero unadjudicated MIRRORED/PAD-MISMATCH/PAD-GEOM;
      six twin renders produced
- [ ] Fresh-context pin review: `verification/pin_review.md` zero FAIL
      (dedicated reviewers for U1 ESP32 and the U3-U6 MPR121 group)
- [ ] Fresh-context render review: `verification/render_review.md` — electrode
      numbering silk legibility graded, every finding triaged
- [ ] PDFs exported (schematic / pcb_layers / assembly) + PNG-verified
- [ ] MOTOR-OFF-AT-BOOT: R8 nets = {3V3, ENN} (audit I9 line PASS)
- [ ] BRIEF acceptance table updated; no criterion `unmet` at release cut
- [ ] Release dir per contract: MANIFEST sha256 table, git_dirty false,
      ORDER_README (rotation checklist, hand-solder list, humidity note,
      first-power ritual incl. motor-disabled verification)

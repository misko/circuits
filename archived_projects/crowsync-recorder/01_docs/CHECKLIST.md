# CHECKLIST — pre-release gate (every line runnable by a fresh agent)

- [ ] `bash 03_src/rebuild_all.sh` ends `violations: 0 {}` and `unconnected: 0`
      (chain prints `AUDIT: PASS` on the way)
- [ ] `python3 03_src/generate_rules.py && git diff --exit-code 04_kicad/crowsync_recorder.kicad_dru`
      (generated rules are byte-stable, no hand-edits)
- [ ] `python3 03_src/bom_seed.py` prints `seeded ... 0 hand-solder lines` and exits 0
- [ ] `python3 ~/.claude/skills/jlcpcb-fab/scripts/jlc_stock_check.py 06_build/fab/bom_jlc.csv --min-stock 15`
      ends `PASS` (15 = 3 boards x 5 margin)
- [ ] `/usr/bin/python3 ~/.claude/skills/jlcpcb-fab/scripts/jlc_twin.py 04_kicad/crowsync_recorder.kicad_pcb 06_build/fab/bom_jlc.csv 06_build/twin --adjudications 03_src/rules/twin_adjudications.yaml`
      exits 0 (zero unadjudicated criticals)
- [ ] `verification/pin_review.md` in the release shows zero FAIL verdicts
- [ ] fresh-context render review findings all triaged (fix or documented disposition)
- [ ] `bash 03_src/export_pdfs.sh` produces schematic/pcb_layers/assembly PDFs; PNGs eyeballed
- [ ] BRIEF.md acceptance table has no `unmet` rows (release gate — cutting a
      release with an unmet criterion is a contract violation)
- [ ] release cut from a CLEAN tree (`git status --porcelain` empty), MANIFEST sha256s match

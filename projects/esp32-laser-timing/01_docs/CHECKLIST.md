# Pre-release gate — esp32-laser-timing

Every line runnable/inspectable by a fresh agent.

- [ ] `bash 03_src/rebuild_all.sh` ends `violations: 0 {}` / `unconnected: 0`
      (includes ERC=0, netlist parity, audit PASS, DRC with
      --schematic-parity on KiCad 10)
- [ ] `kicad-cli sch erc --severity-all` report: 0 errors 0 warnings (P11)
- [ ] `python3 03_src/bom_seed.py` exits 0 (every assembled line has LCSC;
      hand-solder lines listed as uncoded)
- [ ] `python3 ~/.claude/skills/jlcpcb-fab/scripts/jlc_stock_check.py
      06_build/fab/bom_jlc.csv` — all lines in stock >= 5x qty
- [ ] `jlc_twin.py` exit 0 with adjudications; `--also` covers J-terminals;
      no unadjudicated MIRRORED/PAD-GEOM; POLARITY-CHECK reviewed (C_bulk!)
- [ ] Fresh-context pin review: verification/pin_review.md zero FAIL
      (ESP32 module and LM339 have dedicated reviewers)
- [ ] Fresh-context render review: verification/render_review.md — terminal
      silk words legible, OLED pin-order warning present, all findings triaged
- [ ] Antenna keepout: audit_board.py I8 passes (no copper in antenna zone,
      module overhangs north edge)
- [ ] All acceptance criteria in BRIEF.md are met or user-dropped before
      cutting 07_releases/ (contract rule)
- [ ] Release cut from a clean tree (`git status --porcelain` empty),
      MANIFEST sha256 table matches files

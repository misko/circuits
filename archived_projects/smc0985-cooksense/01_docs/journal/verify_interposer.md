# journal: verify — interposer (Board C)

## 2026-07-24 09:30 — verification battery (INITIAL release = full breadth)
- fab: export_jlc_package (2-layer): gerbers 9 layers + drills, BOM 2 lines
  (1 uncoded = the self-supplied 10FDZ-BT), CPL 3; bom_source_check PASS;
  stock: C2683602 = 8587 (need 1).
- twin: exit 0; findings = ROT-DB-SUGGEST (informational; exporter already
  emits JLC rot 90, fit 0.01mm) + MODEL-REG-OK — BYTE-SAME classes as the
  sealed cooksense v1.1 twin for the same part. missing_models.txt: the two
  10FDZ (no JLC model, hand-solder; CPL is population truth).
- fresh-context reviews (4 concurrent fable-medium agents): PIN 3x PASS;
  RENDER PASS (4 P2); redteam lens-a ORDER (2 P1 order-side, 2 P2); lens-b
  ORDER (0 P0/P1, 3 P2). All archived verbatim in 08_reviews/ with
  provenance; dispositions I1-I9 in DISPOSITIONS.md — I1 (ZIF pin-1 silk)
  and I4 (SM10B stale note) FIXED pre-seal; I2 (harness spec) fixed-in-docs
  (ORDER_README §3); I3 = the user-held physical-confirm ORDER gate.
- policy_audit (single-board shadow view): 0 FAIL — 18 PASS / 3 WAIVED
  (S-VER, E-ADR, M-REPRO: all evidence-backed multi-board scoping waivers) /
  7 HUMAN (graded by the reviews above) / 10 N-A.
- post-fix re-verify (targeted per canon): every mechanical gate re-measured
  after the silk fixes — DRC 0/0/0, rebuild reproduces, audit_board PASS.
- next: 2-commit seal of 07_releases/interposer-v1.0-2026-07-24.

## 2026-07-24 09:40 — multi-board tooling learnings (harvest source, M-LEARN)
- generate_board_generic rewrites SHARED 04_kicad/{fp-lib-table,
  refdes_waiver.json}: clobbered the sealed board's audit until restored;
  guarded in rebuild_all.sh (candidate-canon: yes — a <board>-scoped
  fp-lib-table emit, or a merge instead of overwrite).
- policy_audit / electrical_invariants / count_parity / gen_tscircuit are
  single-board readers (boards[0], netlists[0], head -1): the interposer
  runs them against a SHADOW ROOT (06_build/interposer/shadow_root, built by
  rebuild_all.sh). Candidate-canon: yes — ADR-0007 two-strike rule holds
  (promote per-board scoping into the shared scripts on the SECOND
  multi-board project).
- prep's mounting-hole NPTH matcher fences EVERY footprint with an NPTH pad
  — incl. connector polarization bosses (swallowed both ZIF pin-1 pads).
  refdes_prefix is the scoping knob; candidate-canon: yes (default the
  matcher to mounting-hole refdes prefixes).
- KRT grid-rounds an exact-floor track width DOWN (0.5 -> 0.4998, DRC
  fail): author wave widths a hair above the class floor (0.508).
  candidate-canon: yes (tier_preflight could warn width==floor).

## 2026-07-27 17:40 — v1.1 respin + re-seal (FIX-PASS: assembly payload only)

- WHY: fleet audit found two P0s in the sealed v1.0. **P0-1 A-ROT** —
  J_KEY_MATRIX CPL 90.0 where the measured authority says 270.0, i.e. 180
  degrees out, from the name-DB rule `^JST_GH_SM,180` REFUTED the day AFTER
  the seal. Silent by construction: the GH pad array is symmetric about its own
  centre, so at 180 the part solders perfectly while a pin1<->pin10 swap
  reverses the whole ten-line ribbon. **P0-2 A-POP** — both blank-LCSC THT
  10FDZ-BT on the CPL with only ORDER_README prose defending it. ROOT CAUSE of
  both: the assembly gate family NEVER RAN on v1.0 (no A-* row in its
  policy_audit.md at all). An absent verdict is not a pass.
- ROTATION SOURCE, stated because canon requires it: the EXACT PAD-FIT path,
  not the footprint-name DB. `jlc_lcsc_rotations.csv:17` C2683602 offset 0,
  pad-by-number fit vs JLC's cached model, rms 0.0049mm vs 5.0792mm next best
  = 1037x separation, operator verified against pcbnew (that table's RULE 2).
  board_rot 270 + 0 = CPL 270.0. Re-fitted independently for this release by
  jlc_twin: fit=0.01mm jlc_offset=0 src=lcsc. Cross-board: cooksense-v1.4
  ships the same code at the same board orientation at 270.0.
- SOURCE CHANGES (all regenerable, canon M3): floorplan.yaml gains a
  `patterns:` entry putting `exclude_from_pos_files` on both ZIFs and bumps the
  silk caption v1.0 -> v1.1; NEW 03_src/interposer/rules/assembly.yaml
  (service/sides/fiducials/build_quantity + `pourless:` with its reason +
  not_assembled with a DATED JLC catalog query + exempt_prefixes);
  policy_waivers gains an E-TOPO entry.
- COPPER DID NOT MOVE, and on a REGENERATED board that claim needs a method:
  generate_board_generic mints fresh UUIDs every run, so md5 and `diff` both
  say "changed" and neither says what. Wrote an aperture-resolved,
  order-independent gerber/Excellon multiset comparator (resolves every D-code
  to its aperture DEFINITION and every T-code to its diameter, parses gerber
  and Excellon TEXT, no pcbnew — canon M1). RESULT vs sealed v1.0: F_Cu 450
  atoms, B_Cu 180, masks 84/52, pastes 12/0, PTH 55 holes, NPTH 6 -> ALL
  IDENTICAL. Edge_Cuts differs by ONE segment's traversal DIRECTION (identical
  as an undirected set). F.Silkscreen: 50 of 5368 atoms differ, ALL inside
  x44.286-44.800 y12.009-12.909 = one 0.514x0.900mm character cell = the
  version digit. The red-team lens reproduced this with its OWN comparator.
- FOUR SHADOW-ROOT SCOPING BUGS FOUND AND FIXED — all the same class, "a gate
  read the OTHER board's artifact and nobody noticed":
  (1) `03_tscircuit/build/circuit.json` was the SHARED file = COOKSENSE's 222
      components. v1.0's fab export inherited it and got J_KEY_MATRIX's LCSC
      right BY COINCIDENCE (the main board carries the same refdes for the same
      part); both 10FDZ-BT resolved blank because they are simply not in the
      other board's circuit. count_parity was 3 legs for the same reason; it is
      4/4 now.
  (2) `03_tscircuit/kicad/*.kicad_sch` sorted cooksense FIRST, so the
      interposer's net_label_survival was graded against the MAIN board's 100+
      global labels (LABEL-LOST on TH_SPARE, WD_OK, U_SEL_BUS...).
  (3) `07_releases` was not exposed at all, so M-REL/M-BOM/A-POP/A-BODY graded
      N-A. Exposing it as a SYMLINK does not work either: assembly_coverage
      does `Path(target).resolve()` then `root = t.parent.parent`, so a
      symlinked release resolves BACK OUT to the shared tree and it grades
      against COOKSENSE's assembly.yaml (18 spurious findings, measured). Each
      release is now a REAL dir whose CHILDREN are symlinks.
  (4) `--shadow-only` added: the audit view could previously only be refreshed
      by a FULL rebuild, which re-mints UUIDs — i.e. the only way to refresh the
      auditor was to invalidate the thing being audited.
- ARCHIVE NOW STANDS ALONE: fp-lib-table rewritten at stage time to
  `${KIPRJMOD}/cooksense.pretty`, and .kicad_pro/.kicad_dru/assembly.yaml/
  floorplan.yaml shipped. `kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` from the archive ALONE: **v1.1 = 0/0/0, v1.0 = 29
  violations** (its 2 unresolvable footprints were the two 10FDZ-BT, the entire
  point of the board). Re-plotted from the archive's own source/: 11/11
  IDENTICAL GEOMETRY.
- GATES, all re-run against the STAGED archive (canon M-SHIP): DRC 0/0/0;
  ERC 0 errors / 102 warnings (class census identical to v1.0); policy_audit
  FAIL=0; A-POP PASS; A-POS worst datum residual 0.00000mm; A-BODY 1/1 (v1.0:
  1/3, because the two bodiless ZIFs were on the CPL and "bodiless" reads as
  "not placed"); A-RENDER 1 measured/1, centre delta 0.165mm; A-STOCK
  C2683602 = 8559 vs need 1 x 5; A-EVID 0 missing (v1.0 FAILS it with 5, two of
  them MIS-NAMED: render_front/back_bare for render_top/bottom_bare, and
  interposer.erc.json for erc.json — a mis-named required artifact looks present
  to a human and is invisible to every name-based check); F-LEGIBLE OK (v1.0:
  FAIL, 2 findings); F-PAYLOAD OK incl. F-POUR pourless-by-declaration; parity
  50/50 connected nodes with the ONE no-connect (J_KEY_MATRIX.MP, netless by
  design) written out node-level; bom_source_check PASS; part_facts_check OK.
- REVIEW BREADTH = fix-pass: targeted pin + render re-confirmations (both PASS)
  + ONE integrated zero-context adversarial lens. Verdicts ORDER / ORDER,
  **0 P0**, 1 P1 (the archive's own A-EVID gap, closed pre-seal) and 3 P2s. Its
  P2 on the boss margin was ACCEPTED and rewritten into ORDER_README: the error
  is 0.190mm against 0.23mm of clearance (83% of the budget), and at the boss's
  ø1.70 NOMINAL it would INTERFERE by ~0.01mm — the 0.04mm margin is bought by
  this lot's MEASURED ø1.60 boss, so dry-fit EVERY connector, not just the first.
- next: nothing on this board. Two USER-HELD items travel with the order
  paperwork (10FDZ-BT polarity UNMEASURED; the M3 boss offset), plus the JLC
  placement-preview eyeball and the flex-jumper coupon (separate part).

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

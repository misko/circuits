# learnings — 02_parts (successor session, 2026-07-21)

- issue: nets.yaml declared `fab_tier: jlc_6layer_standard` — a tier that
  existed in NO fab_tiers.yaml. P-TIER was a latent FAIL for the whole
  archive lineage; the tier ladder simply had no 6-layer rungs because no
  prior board had needed them.
  root cause: the archive predates the D-TIER mechanization; its ADR-0008/
  0009 decisions lived as prose, never as tier-table entries.
  avoid next time: when an ADR names a fab capability, add/point at the
  fab_tiers.yaml entry IN THE SAME COMMIT (the tier table is the machine-
  readable form of the decision). candidate-canon: yes (P-TIER already
  enforces; the learning is the tier-table-first habit).

- issue: 23/23 adopted part.yamls lacked escape blocks (P-ESC fail class).
  root cause: archive-era parts predate escape_check v2.
  avoid next time: ADR-0011-style adoption checklists must include "recompute
  escape blocks" (it did — this is confirmation the checklist works).
  candidate-canon: no (already enforced by P-ESC).

- issue: escape_check's style vocabulary folds DFN into 'qfn'
  (infer_from_strings maps \bDFN -> qfn), so an honest `style: dfn`
  declaration FAILS the contradiction check against its own footprint text.
  avoid next time: declare `style: qfn` for DFN packages (ring math is
  identical); or teach escape_check that dfn==qfn as declared styles.
  candidate-canon: yes (small escape_check ergonomics fix).

- issue: T1-T3 tension parts (XU316/FA-238/TCR2LF18) all JLC stock=0,
  re-confirmed live. The archive's D27 sourcing substitutions
  (X322524MOB4SI, TLV70018DDCR) were already wired in bom_seed.py but were
  invisible at BRIEF level until ADRs 0013-0015 formalized them.
  avoid next time: a sourcing substitution made in a BOM seeder MUST have a
  same-day ADR — the seeder is where substitutions hide from review.
  candidate-canon: yes (suggested check: bom_seed SPECIFIC map entries whose
  key MPN != value MPN require an ADR reference in the comment).

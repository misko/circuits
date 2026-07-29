# learnings — verify

- issue: refdes de-collision produced a LEGAL but AMBIGUOUS placement (C3's
  text landed past R3's body; read as swapped by the fresh-eyes review; on
  the shipped gerber, not just renders).
  root cause: the de-collision objective is collision-freedom, not
  attribution — nothing tied a label's distance-rank to its own part.
  avoid next time: generator now hard-fails if any silk refdes text is
  closer to a similar-size (<=4x bbox area) neighbor's bbox than to its own
  part's bbox; red-verified (caught 3 refs pre-fix). candidate-canon: yes
  (suggested I13 refdes-attribution check in audit_template).
- issue: DNP provisions inconsistently marked (D3 "TVS DNP" vs bare L1/R15).
  avoid next time: silk rule — every schematic-DNP footprint gets a DNP
  mark or none do; cheap to check from CPL-vs-footprint diff.
  candidate-canon: yes (P-SILK-DNP).
- issue: rename residue: silk version string carried the ARCHIVE's "v1.1"
  onto a v1.0 board; schematic rev defaulted to "dev" (git-tag derived).
  avoid next time: release gate should grep board text + title blocks for
  the release version string. candidate-canon: yes (M-REV-STRING).
- issue: a released source/ board WITHOUT its sidecar .kicad_pro re-measures
  DRC with KiCad defaults (0.2mm clearance, no text floors) — 130 phantom
  violations on a clean board; independent re-measures diverge.
  root cause: netclasses/floors/constraints live in .kicad_pro + .kicad_dru,
  not the board file; the release contract's source/ list omitted sidecars.
  avoid next time: release source/ MUST include .kicad_pro, .kicad_dru,
  fp-lib-table (+ project .pretty libs); the M3-REPRO reproducibility gate
  must DRC the RELEASE COPY standalone, not the working tree.
  candidate-canon: yes (extend 07_releases contract source/ list + M-REL).

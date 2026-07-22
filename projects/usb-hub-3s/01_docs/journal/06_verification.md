# 06 — Verification & release (2026-07-21)

Chain: bom_seed → jlc_stock_check → jlc_twin (adjudicated) → 3 fresh-context
pin-review agents + 1 render-review agent → policy_audit → release cut
v1.0-2026-07-21 (53 files, MANIFEST sha256, git_dirty=false).

The stage EARNED its keep: two wrong parts were on the board with every
machine gate green.

1. 1001-011-01101 (J2-J4) is a USB-A MALE PLUG rated 1.5A — its own
   drawing says "USB 4P AM SMT". The parts stage recorded it as a
   receptacle; footprint, netlist and silk were consistently wrong
   TOGETHER, which is invisible to artifact-vs-artifact gates. Caught by
   the pin reviewer doing exactly what the protocol says: read the
   drawing title, not the dossier. Replaced with Kinghelm KH-AF90DIP-112
   (ADR 0006); vendored footprint from the vendor pattern; jlc_twin
   fit=0.00mm against JLC's own model.
2. TPS2513 (non-A) claimed the A-only Apple-2.4A divider in part.yaml.
   Alternate C473910 (TPS2513A) promoted.

Other stage outputs: policy_audit driven 5 FAIL → 0 with REAL fixes (7
thermal via-pairs through FET drain paddles + B.Cu landing pours, port
silk labels, escape-style vocabulary corrections, evidence-bearing
adjudication whys); review QUESTIONS all dispositioned with board-level
evidence (verification_report.md); proven-parts ledger harvested (9
function entries incl. the male-plug INCIDENT entry).

Post-release closure (same day): easyeda2kicad's `--use-cache` drops
`.easyeda_cache/` (56MB of twin STEP/OBJ models) in the CWD — it landed at
the project root, which the root contract does not permit. Relocated to
06_build/easyeda_cache (disposable build tree); a fresh twin run recreates
it wherever jlc_twin is invoked from, so run it from 06_build or accept the
re-fetch. CHANGELOG entry for v1.0-2026-07-21 added (the pre-seal
policy_audit ran while M-REL was still N-A).

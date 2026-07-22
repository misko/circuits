# ADR-0011 — reuse of archived crow-array-central as design precedent

Status: accepted 2026-07-21 (mirrors pod ADR-0005)

Same rule as projects/crow-mic-pod/01_docs/decisions/0005-archive-precedent.md:
contracts/schema from SKILL templates; the archived crow-array-central v1.0
design (ARCHITECTURE/DETAIL_DESIGN, ADRs 0001-0010, 02_parts, 03_src incl.
the promoted full-board route artifact 03_src/route/final.kicad_pcb, twin
adjudications) is adopted as the DESIGN SOURCE with this provenance note.
NOTHING is trusted on import: every gate re-runs here. KNOWN RISKS to
re-check first (from the pod execution of the same rule):
1. The pod archive's promoted route chain was STALE vs its sealed board —
   verify the central's final.kicad_pcb reproduces DRC 0/0/0 BEFORE any
   other work (it is copied wholesale to 04_kicad by rebuild_all.sh, so
   the check is cheap).
2. P-ESC: archive-era part.yamls lack escape blocks — compute them
   (XU316 TQFP-128 0.4mm: the block must encode the ADR-0009 small-via
   via-in-pad decision; D-TIER ADR required to raise fab_tier).
3. Commission tensions T1-T3 (XU316, FA-238, TCR2LF18 all JLC stock=0 on
   2026-07-21) need fresh sourcing decisions at parts stage.
4. Silk version string: rename residue (the pod carried "v1.1" onto a
   v1.0 board — check the central's banner text after rename).

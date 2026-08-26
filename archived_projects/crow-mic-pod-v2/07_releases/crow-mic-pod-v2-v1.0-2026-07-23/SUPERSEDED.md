# SUPERSEDED

**Superseded by:** `07_releases/crow-mic-pod-v2-v1.1-2026-07-25/`
**Date:** 2026-07-25

## The board did not change. NO RESPIN OCCURRED.

v1.1 is a **paperwork-only** supersede. Its `fab/` (except `bom.csv`),
`source/`, `pdf/` and `3d/` are **byte-identical** to this directory's —
asserted mechanically by
`release_freshness_check.py --docs-only-supersede`, not by assertion.
Same copper, same gerbers, same drills, same CPL.

## Why: this release's BOM stalls the upload

`fab/bom.csv` here instructs JLC to source two parts it cannot source, for
two positions it is never told to place:

- **`fab/bom.csv:12`** — MK1 `AOM-5024L-HD-R`, with the **MPN column and the
  LCSC column BOTH empty**. It resolves to no part number at all.
- **`fab/bom.csv:18`** — J1 `C9900035627`, a consign-only placeholder at
  live stock 0.

Neither designator appears in `fab/cpl.csv`. Measured on these sealed bytes:
BOM = **28 designators over 17 data lines**, CPL = **26 rows**;
BOM − CPL = {MK1, J1}, CPL − BOM = {}. Uploading this set stalls at JLC's
BOM/CPL matcher before any money is spent. This is also the last unmet
condition of this release's own render/twin **HOLD**
(`verification/render-twin-review.md`).

v1.1 removes both rows. BOM and CPL now agree at 26 designators each, every
line coded.

## Also corrected in v1.1 (documentation only)

- The population set is now DECLARED (`03_src/rules/assembly.yaml`), not
  emergent from an attribute bit — A-POP FAILs against this release.
- Stock evidence now ships (A-STOCK **PASS** at quantity 8). This release
  sealed with none.
- **`verification/twin_adjudications.yaml:57-60` states a pad correspondence
  that is geometrically impossible.** It claims JLC pad 1 = our pad 2; that
  mapping fits at rms **7.1007 mm at all four rotations** — nowhere. It read
  our `.kicad_mod` y-down and JLC's identically-formatted one y-up. The true
  mapping is a **3↔4 swap** of two NC dummy pads (rms **0.1414 @0**, 50×
  separation). **The shipped CPL rotation (0) was and remains correct** — the
  reasoning was wrong, not the number.
- **`verification/policy_audit.md` in this directory is CORRUPT.** A 51-byte
  stdout splice at offset 387 deleted the P-TIER row and orphaned its tail at
  line 13. The file's `Summary:` and `MANIFEST.txt:22` both claim PASS=23; the
  table contains **PASS=22**. Its sha256 verifies — it was generated corrupt
  and then faithfully hashed. **Do not read this file's summary as a grade.**
  P-TIER itself independently re-measures PASS (72 vias all 0.600/0.300, min
  track 0.2498 vs a 0.127 floor).
- **MK1 is not "absent from the JLC catalog"** as this release's ORDER_README
  §3 states — it is C3273706, at stock 0.
- This directory's `source/crow_mic_pod_v2.kicad_prl` is an untracked kicad-cli
  **dropping** in the working tree, not part of the sealed archive: it is
  gitignored and `git ls-files` over `source/` returns 9 files. The MANIFEST's
  "*.kicad_prl omitted" line is CORRECT — delete the stray file if it bothers
  you; it is not evidence of anything and hashing it would have been the error.
- Two of four rules in `source/crow_mic_pod_v2.kicad_dru` **cannot fire**
  (`AUDIO_width` names an undefined netclass; `pad_rescue_stubs` names an
  absent rule area). Carried forward as an evidence-backed waiver in v1.1;
  physical effect nil, and required at the next respin.

## This directory is unchanged and remains valid evidence

Per the `07_releases/` contract, a sealed release is IMMUTABLE and this
`SUPERSEDED.md` is the one file that may be ADDED. Nothing here was edited,
re-exported, or retro-filled. It remains the exact record of what v1.0 was —
including the defects above, which is the point of keeping it.

**Do not order from this directory.** Use
`07_releases/crow-mic-pod-v2-v1.1-2026-07-25/`.

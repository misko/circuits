# Fresh-lens final-bytes review — crow-recorder-central-v2 v1.3

Fresh-context, independent verification of the STAGED v1.3 bytes (2026-07-24),
run FOREGROUND/blocking before seal. The reviewer checked the actual files with
its own tools (diff / sha256sum / grep / read), not the author's summary.

## Checks (all measured)

1. **CPL correctness — PASS.** `diff` v1.2→v1.3 `fab/cpl.csv` = EXACTLY 10
   changed rows, Rotation column only (no adds/deletes); both files 177 data
   rows. Targets all correct: U1 270→90, U2/U3 270→90, U5 270→90, U7/U8 0→90,
   D_USB 270→90, Q1/Q2 270→180, U9 270→180. Every other field of all 177 rows
   byte-identical.
2. **Gerber/drill/BOM/source/3d identity — PASS.** sha256 byte-identical to
   v1.2: gerbers.zip, NPTH.drl, PTH.drl, bom.csv; `diff -r` source/ and 3d/
   identical (pdf/ also identical). Only `fab/cpl.csv` differs — as intended.
3. **Twin evidence — PASS.** `grep -c ROT-DB-SUGGEST twin_report.csv` = 0 (v1.2
   had 10). All 10 target parts `OK … src=lcsc` with offsets matching the CPL
   (fit 0.00–0.28 mm). `twin_report.txt` embeds ONLY the v1.3 release path.
   Twin: 175 OK / 369 checked; the non-OK rows (PAD-GEOM, J2/U10 pad-name
   mismatch, D1 POLARITY-CHECK, J1 MODEL-SELF, C9900035627 consign no-CAD) are
   pre-existing adjudicated items on the byte-identical copper — not v1.3
   regressions.
4. **missing_models.txt — PASS.** Reads `CPL rows: 177; modeled: 177; missing
   bodies: 0` (was stale 172); cross-checks the 177 CPL data rows.
5. **ORDER_README.md — PASS.** Header v1.3; no draft/placeholder markers. All
   four additions present and coherent: (a) §3a MANDATORY/BLOCKING U1 90°-vs-270°
   JLC-preview pin-1 gate + U1 in the rotation-corrected set; (b) §3c beeper
   aggregate load ~8×150 mA ≈ 1.2 A vs the 2 A F_IN fuse; (c) §3b MSL-3 handling
   for consigned U1 (dry-pack, HIC, bag-open timestamp, ≤168 h floor life, bake
   authorization); (d) v1.3 supersede banner (per-LCSC root cause, copper
   unchanged).
6. **Evidence consistency (M-CONS) — PASS.** `rotation_fix_v1.3.md` before/after
   table matches the CPL row-for-row; `external_review_v1.2.md` present VERBATIM
   with a provenance header; `review_dispositions.md` carries EXT3-F1/F2/F3/HG.

## Verdict

**VERDICT (staged bytes at review time): HOLD — regenerate MANIFEST.txt for
v1.3.** All fab-critical bytes and all evidence (checks 1–6) PASS; the ONLY
finding was that `MANIFEST.txt` was still the verbatim v1.2 copy (wrong version,
wrong `fab/cpl.csv` hash 51bc52b1… vs actual 59c14b9d…, twin 165 vs actual 175,
missing the three new v1.3 evidence files). This is the EXT-F4 manifest-
snapshot-consistency class and must not seal as-is.

**RESOLUTION (this seal):** MANIFEST.txt was regenerated for v1.3 AFTER the
review — `version: v1.3`, `git_sha` = the source-S commit, the correct
`fab/cpl.csv` sha256 and every other file's sha256 (including this file and the
two new evidence docs), `twin … 175 OK / 369 checked, 0 ROT-DB-SUGGEST`,
`supersedes: …v1.2` with the CPL-rotation reason, and v1.3 `fix_claims`. The
MANIFEST was then re-confirmed against these bytes. With the manifest correct,
the release is **ORDER** (bare-PCB AND — after the MANDATORY §3a U1 preview
gate — PCBA).

- P1 (resolved in this seal) — MANIFEST.txt was stale; regenerated for v1.3.
- P2 (informational) — twin carries pre-existing adjudicated non-OK rows on the
  byte-identical copper; unchanged from v1.2, correctly dispositioned.

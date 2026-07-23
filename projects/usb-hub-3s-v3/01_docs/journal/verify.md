# Journal — usb-hub-3s-v3 verify / release-seal

## 2026-07-22 22:39 — finish (SEAL v1.0-2026-07-22)
- did: Assembled the self-contained release archive
  `07_releases/v1.0-2026-07-22/` (6 parts). Regenerated gerbers+drill+zip from
  the sealed board at seal time (export_jlc_package.py, pcbnew 10.0.4; LCSC
  carried over); shipped `fab/cpl.csv` = the JLC-upload-format `cpl_jlc.csv`
  (Designator/Layer/Rotation, rotation-DB-corrected) NOT the twin-format
  `verification/cpl.csv` (raw rotations, 180° off on polarized parts). Copied
  source (board/sch/pro/dru/prl + .tsx + .net), vendored `usb_hub_3s.pretty`,
  and rewrote `source/fp-lib-table` (system libs → /usr/share/kicad/footprints,
  custom → ${KIPRJMOD}/usb_hub_3s.pretty). Exported board-body STEP. Bundled all
  gate evidence + BOTH topology memos (original DO-NOT-ORDER verbatim + ORDER
  re-review) + layout memo + authored the RT-T1 re-gate note. Wrote CHANGELOG,
  the M9 learnings harvest, ORDER_README, and the MANIFEST (sha256 over all 47
  files, path-first format so M-REL verifies).
- result: MEASURED —
  - **DRC 0/0/0** (verification/drc.json); **source/ standalone re-measure
    0/0/0** via `kicad-cli pcb drc source/usb_hub_3s_v2.kicad_pcb` (V-REL-FPLIB).
  - **policy_audit 0 FAIL** (HUMAN=6, N-A=6, PASS=22, WAIVED=1). **M-REL PASS**
    ("provenance + hashes verify"), **M-LEARN PASS** (learnings written).
  - **MANIFEST self-check PASS** — 47/47 files hashed both directions, 0
    mismatch. git_sha 81faa99e5ac94216639f3392dfb89ffbd904fa18, git_dirty false.
  - **contracts_audit**: release dir `07_releases/v1.0-2026-07-22/` = 0 FAIL
    (passes the 07_releases contract). Two pre-existing repo-debt FAILs
    (.gitignore, 03_src/rebuild_fast.sh) are tracked at HEAD, outside the
    release, not introduced here.
  - **jlc_twin exit 0** (80 OK / 209; all criticals adjudicated). **pin PASS,
    render PASS.** Red-team **topology RE-CONFIRMED ORDER** (independent
    zero-context re-review; RT-T1 10A = 1.47× the 6.8A trunk) + **layout ORDER**,
    zero P0.
  - Fab set: `usb_hub_3s_v2_gerbers.zip` (13 files), PTH+NPTH drills, bom.csv,
    cpl.csv. F1 holder (C5249699) on CPL; 10A blade element hand-fit off-CPL.
- next: Board is ORDERABLE. Fold the P2 next-rev work order (F-2.1 UVLO note,
  RT-T2 50V input ceramics, RT-T5 10V/16V output ceramics, RT-T4 optional USB-C
  e-fuse, AON6354 doc hygiene, LM5116 EP via-arrays + VBAT_F B.Cu pour) into a
  future rev — none blocks this order. Release is immutable; a fix means a NEW
  version + SUPERSEDED.md, never an edit.

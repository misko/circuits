# SUPERSEDED by crow-recorder-central-v2-v1.3-2026-07-24

Sealed: 2026-07-24 (seal 64764a7, source d66fd1e). Superseded the same day by a
CPL/evidence-only supersede.

Reason: an external review of the sealed v1.2 (orchestrator-verified against
these sealed bytes; archived `08_reviews/2026-07-24_v1.2_external-llm_cpl-rotation.md`
and the v1.3 `verification/external_review_v1.2.md`) found **`fab/cpl.csv`
shipped generic footprint-NAME rotation-DB values that CONTRADICT the digital
twin's exact pad-fit on 10 parts** — including the **consigned U1 (XU316,
TQFP-128) at CPL 270° vs the exact-fit 90° = 180° off**, plus Q1/Q2 (SOT-23)
270→180, U2/U3 (TSSOP-30) 270→90, U5 (SOIC-8) 270→90, U7/U8 (SOT-563) 0→90, U9
(SOT-23-5) 270→180, D_USB (USON-10) 270→90. Assembling from this CPL would place
10 parts (2 polarized FETs and the 128-lead SoC among them) at the wrong
rotation. `verification/missing_models.txt` was also stale (172 vs the real 177).

Root cause: JLC's CPL zero-orientation is a **per-LCSC** fact (how JLC drew each
part's own footprint), which the footprint-NAME rotation DB cannot encode when
two parts share a footprint name — proven on the fleet: C79924 and C7719 are
both `SOT-23-5` yet need 180° vs 90°.

v1.3 regenerates the CPL through a new global per-LCSC override table
(`skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`, per-LCSC WINS over the
name-DB) so every one of the 10 rows ships its twin-measured exact-fit rotation;
the twin re-run reports ZERO unresolved rotation suggestions. It also repairs the
evidence (`missing_models` 177/177/0) and adds the MANDATORY U1 90°-vs-270°
JLC-preview pre-PCBA gate, the 8-beeper aggregate-load warning, and MSL-3
handling for the consigned U1.

**Copper is UNCHANGED** — v1.3's gerbers, drills, and BOM are byte-identical to
this release (a docs+CPL supersede). This v1.2 archive **remains BARE-PCB-
orderable** (the fab geometry is unaffected) but is **HOLD for JLC PCBA**: do NOT
machine-assemble from this release's `fab/cpl.csv`. Order assembly from
crow-recorder-central-v2-v1.3-2026-07-24.

# Learnings — verify / release-seal stage (usb-hub-3s-v3 v1.0)

Harvest sources (canon M9) from the verification + v1.0 seal. Raw evidence for a
later harvest pass into design-policies.md / ADRs, not the canon itself.

## Derived-project carry-over shipped a stale protection rating (RT-T1)

- what happened: the input fuse ELEMENT was specced 20 A (silk said 10 A) — a P1
  red-team blocker. Measured: v3's worst-case input trunk is 6.8 A (55 W out /
  0.9 / 9.0 V), so 20 A (2.9×) left the ~8–27 A overload band unprotected; 10 A
  (1.47×) is correct.
- root cause: usb-hub-3s-v3 was derived from v1/v2, whose buck-boost trunk was
  15.5 A → a 20 A fuse. The rating was inherited verbatim instead of re-derived
  from THIS board's `power_tree.yaml` (v3 dropped the PD cell; trunk fell to
  6.8 A). Protection numbers were carried, not recomputed.
- avoid next time: on any derived project, re-derive EVERY protection/rating
  number (fuse, TVS, ampacity, cap voltage) from the current power_tree at
  commission — never inherit the absolute value. Silk-vs-part.yaml disagreement
  is the tell (10 A silk vs 20 A yaml existed for a while undetected).
- candidate-canon: yes — an E-lens check that each protection element's rating
  traces to a current-power_tree derivation (flag a fuse/TVS whose value has no
  power_tree provenance, and flag silk/part.yaml rating mismatch).

## A P1-driven DO-NOT-ORDER needs an independent re-review to seal ORDER

- what happened: the topology red-team returned DO-NOT-ORDER on the single P1
  (RT-T1). After the fix, the archived memo still literally says DO-NOT-ORDER
  (immutable/verbatim). Contract Validate wants "verdict = ORDER"; Forbidden
  hard-blocks only on P0. Sealing required (a) fixing the P1, (b) an independent
  zero-context re-review that returned ORDER re-deriving the 10 A by first
  principles, and (c) an RT-T1 re-gate note beside the immutable memo.
- root cause: verdict words are point-in-time snapshots; the fixer asserting
  "it's fixed" shares a method with the fix. Checker-independence (canon M1)
  requires a fresh reviewer to confirm.
- avoid next time: when a red-team P1 is fixed post-review, do NOT edit the memo.
  Seal path = fix + independent re-review to ORDER + a re-gate disposition note
  in verification/. Bank the memo pair (pre-fix + re-review) both verbatim.
- candidate-canon: yes — codify the "re-gate note + independent re-review" seal
  path for a fixed P1 (release contract already forbids editing the memo).

## The uploadable CPL is NOT the twin/verification CPL (format + rotations)

- what happened: the task pointed fab/cpl.csv at `06_build/verification/cpl.csv`,
  but that file is `Ref,Val,Package,PosX,PosY,Rot,Side` with RAW board rotations
  (e.g. C1 = 90°). JLC assembly needs `Designator,Val,Package,Mid X,Mid Y,Layer,
  Rotation` with rotation-DB-corrected angles (C1 = 270°, a 180° difference).
  The correct file is `06_build/fab/cpl_jlc.csv`.
- root cause: two CPLs exist for different consumers — the twin verifier eats the
  raw-rotation `verification/cpl.csv`; JLC eats the rotation-corrected
  `fab/cpl_jlc.csv`. Same board, different frames. Grabbing the verification one
  would send 180°-off rotations to the assembler.
- avoid next time: fab/cpl.csv MUST be the `cpl_jlc.csv` (JLC-format header,
  rotation-DB applied). Confirm the header row and spot-check one polarized part's
  rotation against `cpl_jlc.csv` before sealing.
- candidate-canon: yes — a release check that fab/cpl.csv's header is exactly the
  JLC-upload columns (reject the `...,Side` twin header in fab/).

## Consumable-in-holder: holder is JLC-placed, element is hand-fit

- what happened: F1 the Keystone-3568 HOLDER (LCSC C5249699) is on BOM/CPL (JLC
  places it, twin-verified); only the 10 A blade ELEMENT (Littelfuse 0297010) is
  off-CPL hand-fit. `3568/part.yaml` still carried a stale gotcha "hand-solder
  line, uncoded (not in JLC catalog)" that contradicts its own C5249699 code.
- root cause: the holder gained a JLC code but the older "uncoded/hand-solder"
  gotcha text was not updated — the same stale-text failure mode as RT-T1.
- avoid next time: for a holder+consumable, split the not_assembled line
  explicitly (holder = CPL/placed; element = hand-fit/off-BOM) and keep the
  part.yaml gotcha consistent with the sourcing code. Flag AON6354's stale
  IP6559/snubber/"7-pcs"/2100 µF text next rev — same class.
- candidate-canon: no — local data-hygiene; already covered by the "verified vs
  sourcing consistency" spirit of P-VER.

## Standalone STEP is board-body-only in a models-less headless env

- what happened: `kicad-cli pcb export step` produced a valid 89 KB STEP but
  logged ~200 "File not found ${KICAD10_3DMODEL_DIR}/..." — the system 3D
  component-model package is not installed here, so only board geometry embeds.
- root cause: no component .step models on disk; `--subst-models` has nothing to
  substitute.
- avoid next time: ship the board-body STEP for enclosure/outline fit and point
  to the twin edge-profile renders for component heights; note the limitation in
  the MANIFEST rather than claiming a full modeled STEP.
- candidate-canon: no — environment/tooling note.

## M-LEARN flips FAIL the instant a release dir exists

- what happened: policy_audit M-LEARN was N-A ("no release yet"); creating
  `07_releases/v1.0-.../` flipped it to FAIL until this learnings file existed.
  The seal is not policy-clean until the harvest source is written.
- avoid next time: author `01_docs/learnings/<stage>.md` as part of the seal
  checklist, BEFORE the final "policy_audit 0 FAIL" confirmation.
- candidate-canon: no — process ordering; already encoded in the M-LEARN gate.

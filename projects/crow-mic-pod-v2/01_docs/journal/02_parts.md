# journal: 02_parts

## 2026-07-23 — start
- did: commissioned crow-mic-pod-v2 clean-room from the CROW ACOUSTIC
  LOCALIZATION ARRAY brief (board (a), the remote microphone POD only).
  Confirmed all 5 named pod parts are HITS in the sanctioned ledger
  skills/kicad-pcb/references/proven-parts.yaml (escape blocks + gotchas +
  layout_refs already verified): OPA1678IDR, TPD2E2U06DRLR,
  CMT-8504-100-SMT-TR, RJHSE-5384, AOM-5024L-HD-R. Added SS14 (flyback) +
  SMAJ6.0A (DNP TVS) for the inductive transducer clamp per the ledger
  gotcha on CMT-8504.
- result: 7 specialty/polarized parts need part.yaml. Fanned out 3
  concurrent clean-room research agents for datasheet-figure pin maps +
  provenance (I supplied ledger escape/gotcha blocks so they only fill the
  pin-map/land-pattern gap). Generic R/C resolved at BOM stage.
- next: merge returned part.yaml, spot-verify figure citations (S-VER),
  vendor the CMT-8504 4-pad + AOM-5024 2-pad footprints, run escape_check.

# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   v1.1-respin
step:    "DO-NOT-ORDER on v1.0 (external review 2026-07-24, orchestrator-verified vs sealed bytes; archived 08_reviews/2026-07-24_v1.0_external-llm_full.md). v1.1 respin in progress: F1 U1 EP thermal vias filled+capped, F2 USB 90ohm diff-pair rules+reroute, F4 clean re-seal with consistent evidence. ADR-0007 waiver carried unchanged."
measure: "v1.1 staging complete + machine gates green (DRC 0/0/0 standalone; port nets 115/115+8/8; policy 0 FAIL; twin 0; drill ViaDrill-only at U1 EP; diff-pair rule active) BUT pin review P0 CONFIRMED vs datasheet: U1.40/43/52 LV_x_N straps tied 3V3 on IOB (1.8V) bank, AMR VDDIO+0.5=2.3V — NOT 3.3V-tolerant (XU316 ds v2.0.0 §4.4/§4.8/§15.1). Latent since v1.0."
state:   BLOCKED — SEAL STOPPED (P0 PR2-P0-1, coordinator directive)
next:    "P0 board change: disconnect LV_L_N/T_N/R_N from 3V3 (float per ds §4.8, or tie 1V8) in tsx -> full rebuild + re-gate + re-review -> then resume seal chain. Pin+render review verbatims to archive into 08_reviews/ when their agents return. Staged 07_releases/v1.1 dir remains MUTABLE STAGING (unsealed, uncommitted)."
op_pid:
updated: 2026-07-24T13:40:00

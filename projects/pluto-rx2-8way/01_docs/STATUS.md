# STATUS beacon — pluto-rx2-8way (live head of the journal)

<!-- reader parses from here down -->
stage:   routing
step:    "STAGE 6 RESUMED 2026-07-30. The five KRT keys are now in _KRT_FLAGMAP (length_match_group, length_match_tolerance, meander_amplitude, neckdown_length, neckdown_taper_length) and route.common.fab_tier is corrected to `advanced`, so the recipe that was produced BY HAND on 2026-07-29 is now DECLARABLE and canon M3 no longer blocks promotion. Work in progress: add length_match_group + length_match_tolerance to 03_src/route.yaml rf wave, elongation: meander on RF_RADIAL_STAR in 03_src/rules/nets.yaml, then generate_rules -> route -> stitch -> generate_rules and promote a JUDGED chain."
measure: "PRE-WORK BASELINE (2026-07-29, unrouted): policy_audit FAIL=2 PASS=24 WAIVED=2, DRC 4/99/0, copper_length_audit UNREACHED. Octilinear floor spread 1.4966 mm vs declared max_spread_mm 1.0 — R-LEN-OCT will FAIL until elongation: meander plus a real length_match_group are both present."
state:   running
op_pid:  none
next:    "Config edits, then the gate battery: copper_length_audit, audit_board.py, count_parity, waiver_provenance, policy_audit, status_beacon_check."
updated: 2026-07-30T07:28:32

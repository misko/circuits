# STATUS beacon — pluto-rx2-8way (live head of the journal)

<!-- reader parses from here down -->
stage:   routing
step:    "RACING. W1 SOLVED: rf wave clearance 0.14 + grid_step 0.05 routes 11/11 with ALL 165.194 mm of RF copper at 0.36 mm — measured off a 20-point width x clearance sweep, and grid_step is half the fix (at KRT default 0.1 NO width routes the five boxed pads). W2 SOLVED: meander_amplitude 0.3 takes the realized group spread to 0.3236 mm = 4.27 deg at 6 GHz, which is the 0.3238 mm EUCLIDEAN pad residue itself — the elongation recovers the entire octilinear penalty. length_match_tolerance measured INERT (15 runs, zero effect)."
measure: "PRE-WORK BASELINE (2026-07-29, unrouted): policy_audit FAIL=2 PASS=24 WAIVED=2, DRC 4/99/0, copper_length_audit UNREACHED. Octilinear floor spread 1.4966 mm vs declared max_spread_mm 1.0 — R-LEN-OCT will FAIL until elongation: meander plus a real length_match_group are both present."
state:   running
op_pid:  4044206   # route --race 4
next:    "Config edits, then the gate battery: copper_length_audit, audit_board.py, count_parity, waiver_provenance, policy_audit, status_beacon_check."
updated: 2026-07-30T07:40:11

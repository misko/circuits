# STATUS beacon — pluto-rx2-8way (live head of the journal)

<!-- reader parses from here down -->
stage:   routing
step:    "STAGE 6 OPEN. Spec repair FIRST, before any copper: the standing '+/-0.10 mm ROUTED arm length' obligation is 1.3 deg at 6 GHz and nothing in this system can hold it (13.19 deg/mm measured on JLC04161H-7628), so it is being re-derived against the drift arithmetic and replaced by a `length_match:` declaration in 03_src/rules/nets.yaml graded by the new shared gate copper_length_audit.py. Two E-NETREF ghost keep_short budgets on PE42482A-X (SW_VDD, SW_LS) are being re-pointed to the nodes their datasheet sentences are about."
measure: "Stage-5 baseline carried forward unchanged: policy_audit FAIL=2 HUMAN=6 N-A=11 PASS=23 WAIVED=2; DRC 4 violations / 99 unconnected / 0 parity (99 because there are no tracks). MEASURED pad map of the RF fan: ANT1..ANT7 + RX2_OUT are two-pad nets; the RF8 radial is three nets in series through the pickoff and RX1_MAIN also carries J_RX1.1, so it is a T."
state:   running
op_pid:  none
next:    "generate_rules FIRST (canon R1) -> KRT fanout-first on a track-free board in route.yaml's wave order (rf first, F.Cu only, no vias) -> stitch/fill -> generate_rules LAST -> DRC 0/0/0 -> copper_length_audit -> audit_board -> count_parity -> waiver_provenance -> policy_audit -> beacon. Promote the winning chain to 03_src/route/ on MEASURED radial spread, not on first-to-zero-unconnected."
updated: 2026-07-29T21:22:45

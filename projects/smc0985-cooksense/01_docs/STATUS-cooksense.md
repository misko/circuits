board: cooksense
stage: v1.2 routing gate GREEN — BLOCKED at verify by one P0
state: blocked
git_sha: 4cf235d
measure: DRC 0 viol / 0 unconn / 0 parity; M-REPRO IDENTICAL (17f0d754f9da2f19, 4622 items, 1016 vias); audit PASS 18/25/13; stitch gate clean, 48/48 seed stubs, 0 refused; race 6/6 chains 0-unc/0-viol
op_pid:
blocker: P0 WD_PET has NO pull-down. J_PI unplugged or Pi off -> TPS3823 self-pulses (part.yaml:20) -> WD_OK stuck HIGH; MCP23017 CONTACTOR_REQ latch retains its value and EXP_RST_N has no driver -> U_CAND1/U_CAND2 both true -> external cooking contactor STAYS ENERGISED. Falsifies ADR-0011 s3 + BRIEF C10. Fix = one 100k 0402 pull-down (R_WDPETPD) in 03_tscircuit -> netlist -> re-race -> re-stitch -> re-verify.
next: 1) land R_WDPETPD + E-INV assert; 2) P1 sweep (see 08_reviews truth-table lens); 3) fab export + CPL exclusions; 4) jlc_twin/pin/render; 5) policy audit; 6) 2-commit seal
do_not: seal before the P0 lands; write any U_WD rotation CHANGELOG entry (coordinator RESOLVED: U_WD is 270.0 and always was); act on any 90/270 ROT-DB-SUGGEST (jlc_twin xform() sign bug, 0/180 suggestions are trustworthy)

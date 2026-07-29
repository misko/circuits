# DISPOSITIONS — crow-recorder-central review findings ledger

Living index across all reviews in this folder. Each finding is a CLAIM,
independently verified against the artifacts (netlist / board / part.yaml)
before disposition. Gate: **no CONFIRMED P0 may lack a `fixed` disposition.**

Red-team release review (2 zero-context adversarial agents) + fresh-context
render review, run 2026-07-22 on the pre-seal v1.0 tree.
**Both red-team verdicts = ORDER; render review = PASS-WITH-NOTES. Zero P0.**

| id | review file | finding (one line) | severity | verification | disposition |
|----|-------------|--------------------|----------|--------------|-------------|
| F1 | redteam_topology | No OVP below downstream abs-max: a wrong 9-12V barrel supply passes ~9V to the 5V rail (bucks/LDO abs-max 6.5V) | P1 | confirmed (SMBJ5.0A clamp 9.2V per part.yaml > AP61102 6.5V & XC6227 6.5V; Q9 stays enhanced 5V_P->5V — re-verified) | deferred — ORDER_README mandatory "5V-ONLY supply" note + next-rev work order (add series OVP/eFuse or 5.1V clamp) |
| F2 | redteam_topology | D9 SMBJ5.0A 5.0V standoff sits exactly on the 5.0V rail (zero margin) | P2 | confirmed (standoff 5.0V; ADR-0002 acknowledges ESD-clamp-only) | waived — by design (ADR-0002: D9 is an ESD clamp, not an OVP; thermally negligible on a regulated 5V) |
| F3 | redteam_topology | Both bucks EN=VIN -> PFM mode; part.yaml recommends forced-PWM for audio | P2 | confirmed (U10.5=5V, U11.5=BK1_PG->5V; AP61102 part.yaml:47) | deferred — ORDER_README note; acceptable (both bucks feed DIGITAL rails, all analog is LDO-buffered 3V3A/1V8); next-rev forced-PWM option |
| F4 | redteam_topology | VBUS sense divider omits datasheet 47k bleed (220k/330k only) | P2 | confirmed (R33=220k,R34=330k; VBUS_DET = 5*330/550 = 3.0V into 3.3V GPIO = SAFE) | waived — divider functions and VBUS_DET is in-range; 47k bleed is a refinement, no rating exceeded |
| F5 | redteam_topology | Beeper FET drain has no local clamp (AO3400A avalanche if cable absent mid-drive) | P2 | confirmed (BEEP_RETn->Qn.3 only; deliberate per ADR-0005:34-36; Vds abs-max 30V) | waived — deliberate topology decision (ADR-0005); low-inductance short pod cable, clamp intentionally omitted |
| F6 | redteam_topology | D9 part.yaml provenance weak: sha256 PENDING-FETCH + "verified: same as SMBJ16A" copy artifact | P2 | confirmed (part.yaml carries the artifact; the PART is a real SMBJ5.0A, LCSC C113974 stock 242406, limits numerically correct) | deferred — ORDER_README: confirm SMBJ5.0A datasheet provenance at order; part identity + limits already correct |
| F7 | redteam_topology | Crystal load caps 18pF vs XMOS manual 22pF | P2 | confirmed-justified (CL=12pF + ~3pF stray -> 18pF; within USB +-500ppm) | waived — justified by the CL math; FA-238 CL=12pF |
| F8 | redteam_topology | JTAG headers J13/J14 on VDDIOB18 1.8V bank (abs-max 1.98V); a 3.3V probe overstresses | P2 | confirmed (TDI/TDO/TMS/TCK pins 36/37/44/51 = IOB 1.8V) | deferred — ORDER_README bring-up note: use a 1.8V-level JTAG probe |
| L1 | redteam_layout | USB-HS pair split across F.Cu/B.Cu/In2 with vias — violates the design's own "F.Cu-only, no vias" USB intent | P1 | confirmed (re-measured: USB_DP 4 vias F.Cu6.2/B.Cu10.4/In2 4.7mm; USB_DM 3 vias; 0.93mm length-matched) | deferred — ORDER_README + next-rev work order (re-route USB pair F.Cu-only); USB2.0 HS robust, 0.93mm skew, will enumerate |
| L2 | redteam_layout | Buck input caps ~6mm from VIN (large di/dt hot loop, EMI/ripple) | P1 | confirmed (re-measured U10 VIN->C10=5.57mm, U11 VIN->C13=6.14mm) | deferred — ORDER_README + next-rev (move input cap <2mm, add local HF ceramic) |
| L3 | redteam_layout | Analog ADC input AIN_P4 106mm / AIN_P8 70mm vs ~1.5mm partner legs (long single-ended antenna) | P1 | confirmed (re-measured AIN_P4=106.3mm vs AIN_N4=1.5mm; AIN_P8=69.5mm vs AIN_N8=1.4mm) | deferred — next-rev work order (shorten/balance the analog input routing) |
| L4 | redteam_layout | BEEP_G7 gate-drive adjacent to AUD_N7 (~0.15mm edge-edge) in the crosstalk corridor | P2 | confirmed-reviewer-measured (0.354mm centerline, F.Cu, DRC-clean) | recorded — DRC-clean; next-rev port-7 separation; slowed beeper edge (ADR-0005) limits dV/dt |
| L5 | redteam_layout | AUD jack pairs length-mismatched (AUD1 dP=11.3mm) | P2 | confirmed-reviewer-measured (non-critical at audio BW) | recorded — audio-bandwidth non-critical; next-rev tidy |
| L6 | redteam_layout | 0V9/3V3 sub-floor 0.15mm necks below 0.4mm RAIL floor (all at XU316 escape, not the buck) | P2 | confirmed-reviewer-measured (necks bounded at U1 escape) | waived — D25 neck_approaches with scoped pwr_neck DRU rules (ampacity math in the DRU); at the pin field where current splits |
| L7 | redteam_layout | Track/via geometry exactly at JLC small-via floor, zero margin below | P2 | confirmed-reviewer-measured (min 0.15mm track, 0.30/0.15 vias; nothing below floor) | waived — the declared D-TIER (ADR-0012 jlc_6layer_smallvia); manufacturable at the chosen tier |
| L8 | redteam_layout | ADR-0010 GND zone-sliver waiver is SOUND (not hiding a GND gap) | P2 | confirmed (2 unconnected = Zone[GND]<->Zone[GND] only; In1/In4 95% GND, 414 stitch vias) | recorded — VALIDATES ADR-0010 (independent confirmation) |
| R1 | render-review | Verify USB-C (J12) opening-to-board-edge clearance (a set-back connector won't seat) | P1 | confirmed OK — refuted as defect (measured: J12 courtyard reaches 0.23mm of the bottom edge = flush, receptacle overhangs; J9 barrel overhangs left edge 0.9mm — both correct edge-mounts) | recorded — no defect; edge-mount geometry verified correct |
| R2 | render-review | Assembly-drawing refdes/value crowding in per-port + ADC clusters | P2 | confirmed (board SILK legible; drawing density only) | recorded — cosmetic, drawing-only |
| R3 | render-review | Twin 3D renders lack models for most parts (read as no-model, not unplaced) | P2 | confirmed (13 CPL refs bodiless -> verification/missing_models.txt) | recorded — covered by missing_models.txt manifest |

## Seal decision
Zero CONFIRMED P0. Both red-team verdicts ORDER; render PASS-WITH-NOTES. All
four P1s (F1, L1, L2, L3) are user-error-dependent (F1) or SI/EMI-margin next-rev
improvements (L1/L2/L3) on a DRC-clean, functionally-complete board — dispositioned
to ORDER_README + the v1.1 work order, not seal-blockers. **Release v1.0 may seal.**

## 2026-07-22 v1.1 fresh red-team (post source-compliance; sealed board unchanged) — ORDER/ORDER

Both lenses returned ORDER, no P0. Findings (memos: `2026-07-22_v1.1_redteam_{topology,layout}.md`):

| id | sev | finding | disposition |
|----|-----|---------|-------------|
| F1 | P1 | no OVP below 6.5V downstream abs-max (barrel miswire) | REAFFIRMED — deferred to board rev; ORDER_README 5V-ONLY note (carry-forward, accepted) |
| N1 | P2 | main-PTC vs 16 branch-PTC coordination impossible at 60C (whole-array brownout on single-port fault) | ACCEPTED deferred — fault-isolation degraded; next-rev PTC re-sizing; note in ORDER_README |
| N2 | P2 | ESD array covers only 2 of 6 used RJ45 contacts (5V/beep/GND unclamped on 35ft outdoor cable) | ACCEPTED deferred — extends v1.0 F5; next-rev connector-local clamps |
| N3 | P2 | skew-injection R80 tap contaminates POPULATED ch4 (AIN_P4) — doc-vs-netlist drift v1.1 missed | TO-FIX (source doc): reconcile ARCHITECTURE 'spare-channel' claim vs netlist; the 96mm AIN_P4 span shares this root |
| N4 | P2 | ADR-0002:32 still reads 'drain toward load' — contradicts corrected ADR-0007 + netlist (E-INV asserts correct) | TO-FIX (source doc, one line): v1.1 pass left the primary protection ADR contradicting its own netlist |
| N5 | P2 | barrel jack DC-005C 3A vs 5A named supply + 4A PTC | ACCEPTED deferred — fault-only; constrains any N1 fix <3A |
| L3 | P1 | AIN_P4/P8 analog antennas 96/64mm (2 of 8 channels degraded SNR) | P-ADJ-WAIVED, deferred to board rev (known) |
| G1 | P2 | **P-ADJ waiver is CHECK-LEVEL blanket** — grade() keys on id 'P-ADJ' only; ANY future over-budget net silently absorbed | **SKILL HARVEST** — P-ADJ waivers should be per-NET, not per-check |
| G2 | P2 | **P-ADJ coverage gap** — budgets already-short nets; board-spanning BCLK/MCLK/gate-drive/XOUT uninstrumented (green reads clean) | **SKILL HARVEST** — keep_short must cover the long nets that matter |
| G3 | P2 | **P-ADJ span-model blind** to shared-rail hot-loop + HS-pair layer-continuity | SKILL HARVEST — known model limitation, now doubly-confirmed |
| — | — | attestation-honesty + beeper-crosstalk scans PASSED (part.yaml spans match pcbnew ±0.1mm; no new adjacency) | NO DEFECT — recorded |

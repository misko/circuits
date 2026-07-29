# DISPOSITIONS — crow-mic-pod

Findings ledger across all reviews. Every row independently re-verified
against the sealed release artifacts (netlist, `.kicad_pcb` via pcbnew, or
the cited ADR text) before disposition — reviews are claims, not ground
truth. Re-verification performed 2026-07-22 during the adopted-forward
re-audit of v1.0-2026-07-21 against the current pcb-design skill gates.

| id | review file | finding (one line) | severity | verification | disposition |
|---|---|---|---|---|---|
| T1 | 2026-07-22_v1.0_redteam_topology.md | ADR-0001 §3 claims a 5V/GND reversal exposes "only C1 through 100R"; netlist shows U1 (V+/V-) and C6/C7 sit directly on raw 5V/GND, unprotected by R1 | P2 | confirmed (netlist `crow_mic_pod.net`: net "5V" nodes = C6.1, C7.1, J1.4/7, R1.1, TP4.1, U1.8; net "GND" nodes include C6.2, C7.2, U1.4, D1.4; C1 sits on "5VF", reached only via R1 from "5V" — the ADR's "only C1" claim is verified false) | deferred — remediation list item: correct ADR-0001 §3 wording next rev. No behavior/physical change; RJ45 keying (ADR-0004) makes an accidental single-pin 5V/GND swap physically implausible in the field, so this is a documentation-accuracy defect, not a live safety gap. Re-grade adjudicator note: treat as P1-worthy for correction priority (a MANDATORY protection ADR asserting a false electrical boundary) even though physical risk is low |
| T2 | 2026-07-22_v1.0_redteam_topology.md | No populated entry ESD/surge clamp on 5V, GND, or beeper pairs — only the audio pair (D1) is protected; D3 (beeper-side TVS) ships DNP | P2 | confirmed (D3 part.yaml `sourcing: {lcsc: none ... 'DNP - uncoded on purpose'}`; only D2 flyback + C7 bulk cap sit on the beeper/5V path) | waived — evidenced by ADR-0001 §2 ("overcurrent lives at the CENTRAL end") and §5 ("lightning: out of scope"); already a documented, reasoned tradeoff, not a silent gap. Recommend a one-line explicit risk-acceptance note added to ORDER_README next rev |
| T3 | 2026-07-22_v1.0_redteam_topology.md | ADR-0001 §1 calls AUDIO_P/N "high-impedance" lines; they are op-amp OUTPUTS through 68R (low-Z) | P2 (cosmetic) | confirmed (netlist: U1.1 OUT_A -> R10 -> AUD_P_I -> R13 -> AUDIO_P; low-impedance driver path, not a high-Z input) | deferred — cosmetic wording fix, bundle with T1's ADR-0001 correction |
| L1 | 2026-07-22_v1.0_redteam_layout.md | Balanced AUDIO_P/AUDIO_N pair routed asymmetrically: AUDIO_P 59.97mm/7 vias vs AUDIO_N 62.43mm/5 vias, different F.Cu/B.Cu segment splits | P1 | confirmed — independently re-measured via pcbnew on the sealed board: AUDIO_P 59.97mm/7 vias (F.Cu 19 seg/B.Cu 9), AUDIO_N 62.43mm/5 vias (F.Cu 25/B.Cu 6) — exact match to the review's numbers | deferred — v1.1 remediation item: re-route as a matched, same-layer, same-via-count pair. Not a v1.0 functional blocker (DRC-clean, still differential); a CMRR/EMI-susceptibility optimization for the 30-35 ft outdoor run |
| L2 | 2026-07-22_v1.0_redteam_layout.md | Beeper flyback loop looser than ADR-0002's "10mm, not 10m" framing: D2 cathode->BZ1 = 10.51mm but D2 anode->BZ1 = 15.89mm, BEEP_RET net totals 37.34mm | P2 | confirmed — independently re-measured via pcbnew: D2 pad1(K)->BZ1 pad1 = 10.51mm, D2 pad2(A)->BZ1 pad2 = 15.89mm (exact match) | deferred — optimization note for next rev (tighten D2-to-BZ1 placement); ADR-0002's comparative claim (pod clamp vs 10m central-only loop) still holds, so no correction to the ADR is required, only a layout tightening opportunity |
| L3 | 2026-07-22_v1.0_redteam_layout.md | Beeper (BEEP_RET) and audio (AUDIO_N) tracks run ~0.19mm edge-to-edge over a short same-layer (B.Cu) run near board (x=82.6, y=71.9) | P2 | confirmed — independently re-measured via pcbnew geometric sampling: closest same-layer beeper/audio approach = 0.1866mm edge-to-edge at (82.6, 71.9) on B.Cu between BEEP_RET and AUDIO_N (matches the review's ~0.19mm / (x~82,y~70) claim) | deferred — v1.1 remediation item: add a stitching via or guard-trace gap at this J1-escape corridor to reduce coupling; the run is short and forced by the connector pinout, tolerable for v1.0 |
| L4 | 2026-07-22_v1.0_redteam_layout.md | Op-amp decoupling loop (C6 to U1 pin 8) is ~3.3mm, wider than an ideal <2mm decoupling loop | P2 | confirmed — independently re-measured via pcbnew: C6 pad1 -> U1 pad8 = 3.32mm (matches) | waived — audio-band part (OPA1678), not a switching/RF IC; loop length has negligible effect at this bandwidth. Recorded as a layout-hygiene note only |
| L5 | 2026-07-22_v1.0_redteam_layout.md | Mechanical fit is a CONDITIONAL FIT (J1 body 13.46mm vs 13.70mm recess headroom; -0.14mm interference at the +0.38mm tolerance extreme) | P2 | confirmed — review independently recomputed the ADR-0004 arithmetic from the board file and matched it exactly (13.70mm headroom, +0.24mm nominal / -0.14mm worst-case); this duplicates ADR-0004(c)'s own math, not a new defect | acknowledged — already flagged in ADR-0004(c) as a FIRST-ARTICLE GATE ("close the lid on an assembled pod before building the fleet"); confirmed still open (grep of the project found the gate NAMED in ORDER_README/render_review but no recorded pass/fail result — cannot have run yet, no units are built). Remains an ORDER_README open item, not a new v1.1 trigger |
| L6 | 2026-07-22_v1.0_redteam_layout.md | ESD clamp D1 sits ~10.5-10.7mm from the J1 audio contacts, further than "as close as possible" datasheet guidance | P2 | confirmed — independently re-measured via pcbnew: D1 pad3(IO1) -> J1 pad1 = 9.95mm (center-to-center; consistent with the review's ~10.5-10.75mm centre/pad-edge figure and ADR-0004(b2)'s own ~11.6mm note) | waived — already a documented, evidence-backed accepted deviation in ADR-0004(b2) (THT jack body physically blocks closer placement; topology is clamp-first) |

## Summary

- Both red-team reviews returned **ORDER**.
- Zero P0 findings. Zero confirmed electrical defects of the D1-reverse-polarity
  class (the E-INV gate independently confirms this: 23/23 invariants hold,
  see the re-grade report).
- One P1 (L1, audio-pair route symmetry) and seven P2s, all either `deferred`
  to a v1.1 remediation list or `waived` with the evidence cited above. No
  finding blocks continuing to ship the sealed v1.0 release; none rises to a
  v1.1 TRIGGER (a genuine electrical/topology defect) under this project's
  own D-BACK/gate definitions — they are refinements, not defects.

## 2026-07-22 v1.1 fresh red-team (post source-compliance; sealed board unchanged) — ORDER/ORDER

Both lenses ORDER, no P0. Memos: `2026-07-22_v1.1_redteam_{topology,layout}.md`.

| id | sev | finding | disposition |
|----|-----|---------|-------------|
| P1 | P1 | DNP beeper TVS D3 (SMAJ6.0A unidir) oriented cathode-to-supply = FORWARD-biased by coil kick (conducts ~0.9V), cannot do its documented clamp job; v1.0 memo wrongly called it 'Correct' | TO-VERIFY then disposition — DNP + benign (shipped D2 schottky correct; even swapped, 5.9V clamp < 6V op-max). Correct ADR-0002 premise if confirmed |
| E1 | P2 | **the NEW v1.1 E-INV assertion codifies the WRONG TVS orientation as correct** (asserts D3.1=BZ_P 'so a swap cannot invert polarity') — the gate enforces the physically-wrong orientation | **TO-VERIFY (our gate) then fix** — if P1 confirms, the E-INV assertion is backwards; high-value catch |
| T1 | P2 | ADR-0001 §3 claims reversal exposes 'only C1 via 100R' but U1/C6/C7 sit on raw 5V/GND | TO-FIX (source doc) — false boundary in a mandatory protection ADR |
| T2 | P2 | only audio pair has entry clamp; 5V/beep pairs ride cable bypass on 30-35ft run | ACCEPTED deferred — ORDER_README risk line (carry-forward) |
| C7 | P2 | **OPA1678 layout: block wrong/self-contradictory** — names 'C6,C7 0.1uF V+ bypass' but C7 is a 10uF BULK cap 10.84mm away (v1.1 correction-agent defect) | **TO-FIX (source, clear error)** — the layout block the mic-pod v1.1 pass just wrote is factually wrong |
| L-fb | P2 | P-ADJ straight-line span understates routed FB node by ~90% (FB_B 29mm routed vs 15mm span) | SKILL HARVEST — P-ADJ measures pad-span, not routed length (conclusion still holds) |
| L5 | P2 | ADR-0004(c) first-article lid-close gate still OPEN (no unit built) | OPEN — carry-forward |

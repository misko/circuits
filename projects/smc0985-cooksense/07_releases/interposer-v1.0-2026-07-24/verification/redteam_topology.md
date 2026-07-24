    date: 2026-07-24
    subject: smc0985-cooksense interposer v1.0 (pre-seal staging)
    reviewer: redteam-agent (fable-medium, lens a: topology/protection/ratings)
    context-given: zero-context (curated docs+parts+config+netlist; journals/learnings/STATUS excluded)
    verdict: ORDER (conditional on the two P1 order-side items)

# Red-team lens (a) topology/protection/ratings — interposer v1.0 (verbatim)

Verification results (measured):
1. Pass-through 1:1 — VERIFIED. interposer.net has exactly 10 nets (KP_U1..U6 = pins 1..6, KP_D1..D4 = pins 7..10), each carrying the same pin number on all three connectors. No swaps. electrical_invariants.yaml pins all 50 nodes.
2. Isolation — VERIFIED in netlist AND board: 0 zones, both J_KEY_MATRIX MP tabs netless, all 4 mounting holes np_thru_hole with no copper net, both ZIF polarization bosses NPTH (drill T1 1.8mm at X22.46 = pin1 - 2.54, both rows, same end). No GND, power, or chassis net exists anywhere.
3. Ratings — OK. FDZ contact 50mA/250V vs uA-mA logic-level scan pulses (~20-100R pressed): orders of margin. GH 1.0A/50V fine. No protection elements — correct per the fact-lock.
4. TPs / D4 — VERIFIED: TP on all 10 lines, both sides; D4 passes through identically (T3 met).
5. Mate with main board — VERIFIED: sealed cooksense.kicad_pcb J_KEY_MATRIX pads 1..10 = KP_U1..U6, KP_D1..D4, MP netless, same footprint, F.Cu, rot -90 — identical part, rotation, and layer as the interposer's. Pin maps exactly 1:1.

| Sev | Finding | Evidence |
|---|---|---|
| P1 | Harness build under-specified — silent reversal trap. Both J_KEY_MATRIX headers are the same part at the same rotation on the top layer. A premade GH jumper exists in both same-side and opposite-side crimp variants; the wrong one swaps pin1<->pin10 (U-bank<->D-bank) with zero electrical symptom until scan mapping fails. Required harness: 10-way GHR-10V-S both ends, wired contact-k -> contact-k; for a flat cable between these two same-facing connectors that means both housings crimped on the SAME conductor face with pin 1 on the SAME cable edge, mated via a planar U-bend. Must be stated in order/bring-up docs. | ADR-0009; both .kicad_pcb files |
| P1 | Pre-existing ORDER gate (binding): the 10FDZ-BT land pattern (drill fit, and which housing end carries circuit 1 vs the boss) is datasheet-derived only, flagged NEEDS-PHYSICAL-CONFIRM blocking fab ORDER. A mirrored circuit-1 read would keep the pass-through working but attach U/D labels to the wrong physical conductors. | 02_parts/10FDZ-BT/part.yaml; D9 |
| P2 | part.yaml internal contradiction: SM10B-GHS-TB layout.notes vs pins.MP (float). Built board correct. | 02_parts/SM10B-GHS-TB/part.yaml |
| P2 | Fab-data hygiene: the two self-supplied 10FDZ-BT THT parts appear in bom_jlc.csv (blank LCSC) and cpl_jlc.csv; GH row's Comment holds the LCSC code while MPN is blank. Risk: JLC flags/attempts substitution. | 06_build/interposer/fab/*.csv |

Verdict: ORDER — conditional on the two P1s (user-held physical confirm; explicit harness spec in order/bring-up docs). No copper, netlist, isolation, or ratings defect found.

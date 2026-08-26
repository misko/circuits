# Source and floorplan journal

## 2026-08-15 00:30 — start
- did: converted the architecture's prose-only net domains into seven executable classes before schematic capture, including all 64 SuperSpeed capacitor-bounded nets, 16 USB 2 switch-bounded nets, complete power trunks/branches, control/interlock nets and the common return.
- result: MEASURED `rules_audit.py --phase source` PASS with 7/7 classes graded. The contract deliberately withholds a 90-ohm width/gap until the exact JLC04161H-7628 calculation is retained; it does not turn a planning assumption into fabrication evidence.
- broader preflight: P-LAYOUT/P-PREC passes 2/2. The remaining source battery found three repairable scaffold-schema omissions (module-first N-A rationale, switching-stage N-A rationale, and surge-path applicability), one vague E-PATH basis token, and a sequencing tension in the new RF module: an enabled controlled-impedance contract with locked geometry requires exact route primitives before the present commission-only floorplan has positions.
- next: close the simple schema omissions, then decide whether high-speed digital boards should supply an early pair/stackup contract and defer exact line/arc primitives to placement, or author the entire floorplan and planned route geometry before TSX. Do not bypass the gate with fabricated geometry or a fake local solver result.

## 2026-08-15 07:44 — source checkpoint closed
- did: generalized protected pass-through rails as executable `stage: distribution` paths and added `rf.process.geometry_stage: placement`, including a fail-closed placement replay in both the canonical rebuild driver and `pcb_flow.py`.
- measured: power regressions 57/57; RF module 9/9; RF contract 19/19; schema-reader governance 676/676 keys; module-first 0/0 with explicit N-A rationale; early design 3/3; source rules 7/7; source policy 2 PASS. RF source is honestly `DEFERRED` at 0/0 coordinate nets and will become mandatory before route preparation.
- reflection: the earlier delay was caused by two schemas conflating distinct lifecycle facts—conversion with distribution, and SI intent with placed coordinates. Giving each fact one explicit stage owner removed the incentive to fabricate data and made the future failure point deterministic.
- next: author the schematic from the pinned exact parts and invariants, then stop at the exact-artifact schematic/readability review before spending on placement.

## 2026-08-15 08:00 — pre-capture pair-boundary correction
- did: traced each SuperSpeed conductor connector-to-redriver and found that the 2.2-ohm ESD series element and AC-coupling capacitor require three electrical segments, not two. Added the missing intermediate segment for all eight conductors on all four channels.
- measured: USB_SS authority is now 96/96 named nets (32 connector-side, 32 resistor/capacitor intermediate, 32 IC-side); the RF port denominator matches it exactly. USB_HS remains 16/16.
- reflection: counting differential pairs is insufficient when multiple in-line two-terminal parts exist. Future pair inventories should derive `segments = series_elements + 1` per conductor before net names are frozen.
- next: encode the exact repeated channel topology in TSX and prove the generated netlist against this 112-high-speed-net denominator.

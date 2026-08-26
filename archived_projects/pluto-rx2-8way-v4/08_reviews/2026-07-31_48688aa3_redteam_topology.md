subject: pluto-rx2-8way-v4 48688aa3  
date: 2026-07-31  
reviewer: redteam-agent (topology/protection/ratings lens)  
context-given: curated-pre-seal-zero-context  
design_verdict: DEFECTIVE  
order_verdict: DO-NOT-ORDER  

Scope expansion: I inspected only `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/05_firmware/target/{main.c,rx2_core.c,rx2_core.h,switch_seq.pio}` beyond the stated inputs, solely to determine whether PE42482 V4-high undefined control words are emitted. No journals, learnings, STATUS, or prior reviews were used.

## Findings

### RTPR-01 — P1 — The RF interface violates an unmet 0 VDC precondition and defeats the unconditional de-energization claim

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/PE42482A-X/part.yaml:80,118-123` states every PE42482 RF pin must be at 0 VDC and explicitly records external DC blocking as an owed board decision.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/netlists/pluto_rx2_8way_v4.net:2861-2962,3338-3455` implements no DC blocks: J_ANT1–J_ANT7 connect directly to RF1–RF7, J_RX2 directly to RFC, and J_ANT8/J_RX1 reach RF8 through only R_T1+R_T2 = 440 Ω.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/bom.csv` contains no RF DC-blocking or bias-protection components.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/BRIEF.md:58-63` calls these generic antenna/Pluto SMA interfaces and claims unplugging USB de-energizes the board, without binding every attached RF device to 0 VDC.
- Consequently, an active antenna, bias tee, test source with DC offset, or unexpected Pluto-side bias can violate the switch rating while USB is connected and can inject energy into the nominally “off” board after USB removal.

Suggested disposition: either implement characterized broadband DC isolation on every route reaching U_SW, or make “all ten connected RF interfaces shall present 0 VDC under powered, unpowered, and fault conditions” a binding and externally visible system requirement with verification. Until one of those is done, `off_control: unplug` and `quiescent_ua: 0` apply only under an unstated cabling assumption.

### RTPR-02 — P1 — No board-level RF input-power envelope exists; continuous hopping invokes much lower terminated/hot-switch ratings than the 33 dBm headline

Evidence and measurements:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/PE42482A-X/DOC-75785-4.pdf`, page 9, limits hot switching to 20 dBm above 100 MHz. The board changes live RF paths every dwell, so this rating applies.
- The same PDF, page 11 Figure 2, shows maximum terminated-port CW power only approximately 18–20 dBm over the operating band, with absolute maximum approximately 20–22 dBm. Seven antenna ports are terminated whenever deselected.
- No hot-switch capability is specified for 70–100 MHz, although the board’s stated band begins at 70 MHz.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/BRIEF.md:58-64` defines no RF power limit; its “Input envelope” covers USB only.
- The RX1 pickoff adds another bound. With 33 dBm available from a 50 Ω source, a 50 Ω RX1 load, and the implemented 2×220 Ω + 50 Ω tap branch, each 220 Ω resistor dissipates approximately 82.95 mW nominal, or 83.54 mW at the −1% resistance corner. `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/0402WGF2200TCE/part.yaml:26-32` rates each resistor at 62.5 mW. The nominal resistor-power ceiling is about 31.78 dBm at 70 °C.
- Thus the system limit is not the switch’s 33 dBm headline; deselected-port and hot-switch behavior constrain it to roughly 19–20 dBm, with an unresolved bound below 100 MHz.

Suggested disposition: publish and enforce an RF input limit derived from the lowest selected-path, terminated-path, hot-switch, and pickoff-resistor limit over 70 MHz–6 GHz and temperature. Obtain a vendor-supported 70–100 MHz hot-switch bound or restrict operation further. Mark every SMA receive-only/no-transmit as applicable.

### RTPR-03 — P1 — The 47 Ω “absolute-maximum protection” calculation is nominal and does not prove PE42482 control-pin safety

Evidence and measurements:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/electrical_invariants.yaml:133-200` asserts that the long control lines would peak at 4.807 V without R_S and 3.181 V with 47 Ω into an approximately 67 Ω line.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/PE42482A-X/part.yaml:70-77` gives a 3.6 V control-pin absolute maximum.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/bom.csv:7` implements RC0402JR-0747RL, a 47 Ω ±5% part.
- The cited 3.181 V result back-solves to an assumed approximately 25 Ω RP2040 driver resistance: `2×3.3×67/(67+47+25)=3.181 V`. No guaranteed minimum GPIO output resistance supporting that assumption appears in the curated module evidence.
- At the documented rail maximum 3.366 V, minimum resistor 44.65 Ω, 67 Ω line, and an unconstrained low driver resistance, the first far-end step is `2×3.366×67/(67+44.65)=4.040 V`, exceeding 3.6 V. With no credited driver resistance, R_S must be at least 58.29 Ω at its minimum tolerance; 47 Ω does not establish the claimed bound.
- The narrow firmware inspection found no explicit RP2040 drive-strength or slew setting in `05_firmware/target/main.c`, so software does not close the omitted corner.

Suggested disposition: obtain a guaranteed minimum source-impedance/edge-rate bound for the selected RP2040 pad setting and recalculate across rail, resistor tolerance, line impedance, process, and temperature; explicitly configure that pad setting. Otherwise increase R_S to a value whose minimum tolerance independently clears 3.6 V, then verify VIH and edge settling, or measure worst-corner ringing on hardware before release.

### RTPR-04 — P2 — The 100 mA rail model is not a conservative total-load maximum

Evidence and measurements:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/BRIEF.md:79-80` calls 100 mA a conservative total module-rail envelope.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/03_src/rules/power_tree.yaml:34-65` uses `iout_max_A: 0.10` for dropout and thermal grading.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/RP2040-Zero/part.yaml:336-351` estimates the module alone at approximately 110 mA typical with its hard-powered WS2812 at full white and states that no module maximum-current specification exists.
- The carrier can add approximately 3.91 mA: 0.20 mA switch maximum, three asserted 10 kΩ controls at approximately 0.338 mA each at 3.366 V, and approximately 2.70 mA external LED current at the documented low-Vf estimate and minimum 680 Ω tolerance. An accessible operating state is therefore approximately 114 mA before deriving a true worst case.
- At `VIN=5.25 V`, `VOUT=3.234 V`, and 114 mA, RT9013 dissipation is approximately 229.8 mW and estimated rise at 250 °C/W is 57.5 °C. At 85 °C ambient this reaches approximately 142.5 °C against the dossier’s 150 °C junction maximum, leaving only about 15 mA of thermal current margin over a typical—not maximum—load.
- The firmware is USB-programmable, so relying on the on-module RGB never being driven is not a hardware maximum unless explicitly enforced as a product constraint.

Suggested disposition: derive a genuine maximum module-plus-carrier current, including WS2812 state and temperature, and rerun thermal/load margin at the declared ambient. Alternatively bind firmware to keep the RGB dark and state an ambient ceiling, while treating reprogrammability as invalidating that guarantee.

### RTPR-05 — P2 — All user-accessible RF connectors intentionally omit system-level ESD protection

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/BRIEF.md:62` explicitly states that the RF ports have no shunt ESD.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/bom.csv` confirms no RF protection components.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/02_parts/PE42482A-X/DOC-75785-4.pdf`, page 2, rates the bare IC to 1 kV HBM/CDM; that is a component-handling rating, not a user-accessible SMA system withstand.
- Ten exposed SMA connectors feed the switch with no intervening clamp or DC block. No system ESD level, handling restriction, or verification is stated.

Suggested disposition: add RF-qualified low-capacitance protection and characterize it, or explicitly classify the assembly as ESD-controlled bench equipment with connection/disconnection procedures and accept the resulting field-reliability limitation in a binding decision.

### RTPR-06 — P1 — The supplied fabrication package is explicitly non-orderable and still has unresolved uploader/process gates

Evidence:

- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/MANIFEST.txt:2` says `UNSEALED FABRICATION CANDIDATE — DO NOT ORDER`.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/stock_check.json:5-8` says the stock PASS does not predict JLC allocation.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/stock_check.csv:10` identifies all ten SMA connectors as `Plugin`; `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/01_docs/ARCHITECTURE.md:44-48` requires JLC to confirm/select the plug-in through-hole process.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/bom_echo_gate.txt:1-6` requires comparison against JLC’s uploader-resolved BOM and contains no completed echo result.
- `/home/mouse9911/gits/circuits/projects/pluto-rx2-8way-v4/06_build/fab/rotation_human_gate.txt:1-8` leaves U_SW on a mandatory order-preview rotation gate.

Suggested disposition: do not upload for purchase as a releasable order. Resolve RTPR-01 through RTPR-04, then complete uploader BOM echo, U_SW orientation inspection, THT plug-in service acceptance, module procurement/hand-fit instructions, and seal a new immutable fabrication package.

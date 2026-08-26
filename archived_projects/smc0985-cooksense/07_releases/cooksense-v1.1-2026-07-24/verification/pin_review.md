# CARRIED VERBATIM from cooksense-v1.0-2026-07-23 (v1.1 is a placement/outline-only revision:
# netlist byte-identical — see verification/semantic_battery.txt; parts untouched. Scoped
# re-verify per canon 'Verification scoping': NO pin-review repeat. Carried 2026-07-24.)

# Fresh-context pin review — smc0985-cooksense MAIN board

- Board: 04_kicad/cooksense.kicad_pcb @ 9f5c385
- Protocol: skills/kicad-pcb/references/pin-review-protocol.md
- Dossiers: 06_build/pin_audit/ (pin_audit.py; BOM MPN column back-filled from
  02_parts LCSC/Comment mapping — scratch copy, project BOM untouched)
- Reviewers: 5 fresh zero-context group agents + orchestrator (F1, J_CONTACTOR, J_TC)
- Coverage: 67/67 active parts (46 IC/connector/relay + 18 Q/D + F1, J_CONTACTOR, J_TC)

## Verdicts

| ref | part | verdict | finding |
|---|---|---|---|
| F1 | MF-MSMF200L-2 | PASS | non-polarized series fuse, 5V_IN -> 5V_FUSED at power entry |
| J_CONTACTOR | KF350-3.5-2P | PASS | 2 positional poles CONTACTOR_LOOP/CONTACTOR_E; pitch corrected to 3.5mm, twin-verified |
| J_TC | PCC-SMP-K | PASS (prov.) | pad pitch 7.92mm = drawing 7.9mm; figure-cited part.yaml; pad1=TC_POS/pad2=TC_NEG — cross-check vs J_THERM group pending |
| U_LDO | AMS1117-3.3 | PASS | re-derived from datasheet; tab=VOUT correct |
| U_WD | TPS3823-33 | PASS | supervisor on 3V3 as required |
| Q_REV | AO3401A | PASS | re-derived; D=5V_FUSED / S=5V_RPP / G=GND — correct reverse-block orientation |
| D_TVS | SMBJ5.0A | PASS | cathode -> 5V_PROTECTED, correct |
| D_ESD_IN | PESD5V0S1BA | PASS | bidirectional at raw input — correct choice |
| U_EFUSE | TPS259573DSGR | QUESTION (OPEN) | pins 1-5,7-9 OK incl. new EP->GND tie; pin 6 FLT open-drain HIGH=power-good lands on net PWR_GOOD_N — possible inverted semantics vs consumer (safety chain; lead dispositioning) |
| D_REVCLAMP | SS34 | QUESTION (OPEN) | placed upstream of F1 — unfused reverse-conduction path; intentional-vs-move disposition pending |
| J_PWR | Micro-Fit 43650-0224 | QUESTION (OPEN) | pin-1 vs housing-key never confirmed against Molex SD drawing; ORDER_README bring-up check |

| U_DECU | 74HC238D (Nexperia C5620) | PASS | C5620 confirmed pin-for-pin = TI SN74HC238 from Nexperia Rev.8 datasheet (fetched — NOT in 02_parts, see housekeeping); E1n/E2n=GND, E3=DECU_G1 driven — active-HIGH enable wiring correct; A/B/C from SR1, Y0-Y5=SEL_U1..6 |
| U_DECD | 74HC238D (Nexperia C5620) | PASS | same; pin 3 (A2)=GND + Y4-Y7 NC = documented 4-output use; Y0-Y3=SEL_D1..4 |
| U_SR1 | SN74HC595DR | PASS | pinout re-derived (SCLS041J); SER/SRCLK/RCLK correct; QH'(9)->U_SR2 SER daisy chain; SRCLRn=KEY_RESET_N driven; OEn=SR_OE_N |
| U_SR2 | SN74HC595DR | PASS | control pins symmetric with U_SR1; SER=SR_CASCADE (expected divergence); unused outputs float (safe) |
| U_LATCHA | SN74LVC1G00 (C8185) | PASS | C8185 = 1G00 NAND SC-70-5 (A=1,B=2,GND=3,Y=4,VCC=5 re-derived); cross-coupled SR latch with U_LATCHB, symmetric |
| U_LATCHB | SN74LVC1G00 (C8185) | PASS | latch pair partner; REARM_N/FAULT cross-feedback correct |
| U_OENAND | SN74LVC1G00 (C8185) | PASS | SR_OE_N = NAND(MCU_RELAY_ENABLE, WD_OK) — correct fail-safe polarity; R_OE 3V3 pull-up on SR_OE_N (default-disabled) verified on board |
| U_SCHM | SN74HC14DR | PASS | all 6 inverters used as 3 double-inversion chains (ESTOP/MODE/DOOR); zero floating inputs |
| U_ONESHOT | SN74LVC1G123DCTR | PASS | An=GND (rising-B trigger), B=PRESS_REQ, CLRn=DOOR_OK driven, Cext/RextCext on RC nets; no Qn on 8-pin DCT (correctly unused) |
| U_EXP | MCP23017-E/SS | PASS | 28-pin map re-derived (DS20001952C); NC 11/14 open (23S17 trap avoided); A0-2=GND (0x20); RESETn pulled to 3V3 via R_EXPRST (verified on board) |

| U_AND1 | SN74LVC1G11 | PASS | SOT-23-6 map re-derived (1=A,2=GND,3=B,4=Y,5=VCC,6=C — 6-pin trap avoided); inputs MODE_AUTO_HW/WD_OK/ESTOP_OK, Y=AND1 |
| U_AND2 | SN74LVC1G11 | PASS | TEMP_OK/MCU_RELAY_ENABLE/HOST_AUTH -> AND2 |
| U_AND3 | SN74LVC1G11 | PASS | AND1 & AND2 & FAULT_LATCH_CLEAR -> KEY_RELAY_ALLOWED; chain wiring correct |
| U_FAULTAND | SN74LVC1G11 | PASS | unused C input tied 3V3 per DS 8.4.1; Y=FAULT_SET_N |
| U_ULNA | ULN2803ADWR | PASS | IN/OUT corner-pairing correct all 8ch; GND=9, COM(10)=5V_KEY_RELAY (coil rail, correct) |
| U_ULNB | ULN2803ADWR | PASS | 4ch used, pairing correct; unused ULN inputs open = defined OFF (internal 2.7k base R); symmetric with U_ULNA |
| U_OPTO | LTV-817S-TA1 | PASS | 817-family invariant pinout (Lite-On PDF unreachable — vendor-invariant basis stated); 1=A->OPTO_LED_A, 2=K->GND, 3=E->CONTACTOR_E, 4=C->CONTACTOR_C; isolation boundary preserved |
| Q_COILDRV | 2N7002 | PASS | G/S/D re-derived from DS11303; COIL_EN/GND/HS_GATE_COIL low-side level shift |
| Q_SWDRVA/B/RHA/RHE | 2N7002 x4 | PASS | RAIL_EN_x -> SWG_x, S=GND; all identical, no swaps |
| Q_COIL | AO3401A | PASS | S=5V_PROTECTED, D=5V_KEY_RELAY, G=HS_GATE_COIL — correct high-side P-FET |
| Q_SWA/B/RHA/RHE | AO3401A x4 | PASS | S=3V3, D=3V3_SW_x, G=SWG_x; each paired to its own driver |
| K_U1..6, K_D1..4, K_PRESS | DIP05-1A72-12L x11 | PASS | pad1=pin1 coil+ = 5V_KEY_RELAY (diode-variant polarity safe), pad2=pin7 to own ULN output, contacts to KP_x / SEL bus; winding rotation-only, no mirror |
| K_STOP | DIP05-1A72-12L | PASS (evidence) | reviewer QUESTION resolved by orchestrator net-trace: contact bridges KP_U6 -- R_STOP(0R) -- KP_D1 = direct key-press emulation at the (U6,D1) matrix crossing (STOP key), analogous to K_PRESS bridging U_SEL_BUS--R_KEY--D_SEL_BUS; coherent, lands exactly on another keypad line |

| J_PI | 2x20 Pi header | FAIL (OPEN-DISPOSITION) | logical map verified 40/40 correct vs Pi J8 (5V/3V3/GND/I2C/SPI/GPIO all on correct pins); FAIL is an assembly-doc contradiction: part.yaml gotcha claims socket-down direct-stack (under which the footprint would be MIRRORED) but layout + ADR-0007 + board silk say ribbon sidecar (under which as-built is CORRECT). Disposition: keep footprint, fix stale gotcha, specify male-DIL-IDC ribbon + pin-1 keying in ORDER_README |
| J_KEY_MATRIX | X9555WV 2x16->10used | PASS | KP_U1..6/KP_D1..4 ordering vs part.yaml; MP shield pads deliberately floated ("do not fix to GND") |
| J_DOOR | JST | PASS | switch pair + shield per part.yaml |
| J_MODE | JST GH | QUESTION (OPEN) | unkeyed GH sibling housings with different pin conventions -> cross-plug could short COIL_EN to 3V3; re-pin or evidence-mitigate |
| J_ESTOP | JST GH | QUESTION (OPEN) | contactor-loop current through 1.0A/50V GH contacts unproven — cite loop current or waive with evidence |
| D_DOOR | PESD5V0S1BA | PASS | cathode on signal, anode GND |
| D_ESTOP | PESD5V0S1BA | PASS | cathode on signal, anode GND |

(Group pending: analog front-end.)

## Cross-part QUESTION (logic group -> orchestrator-investigated, for lead disposition)

**QUESTION (OPEN, safety-relevant): 595-Hi-Z leaves '238 inputs floating with no
pull-downs.** Measured on the board: DECU_G1/DECD_G1 and all five address nets
connect ONLY 595 pin <-> 238 pin (no resistors); SEL_U1..6/SEL_D1..4 go straight
into ULN2803 inputs (no AND interposition); the relay coil rail 5V_KEY_RELAY is
high-side gated by Q_COIL/Q_COILDRV from COIL_EN (J_MODE pin 2, R_COILENPD
pull-down) — but COIL_EN is INDEPENDENT of the watchdog chain. So if WD_OK
drops while COIL_EN is asserted (normal operation), SR_OE_N goes high (R_OE
pull-up, correct), the 595s tri-state, the '238 active-HIGH enables (E3) float,
and a floated-high E3 can randomly drive one SEL_* into a ULN channel with the
coil rail live. Fix candidates: pull-downs on DECU_G1/DECD_G1 (minimum), or
gate COIL_EN through the fault chain. Needs lead disposition.

Observation (minor): KEY_RESET_N (595 SRCLRn) is driven only by J_PI pin 33
(Pi GPIO13), no pull — floats during Pi boot, but R_OE holds outputs disabled
then; low risk, note for bring-up.

## Gate status

INCOMPLETE — awaiting 4 group reports. No FAIL so far; 3 OPEN QUESTIONs under
disposition by the design lead (not confirmed defects).

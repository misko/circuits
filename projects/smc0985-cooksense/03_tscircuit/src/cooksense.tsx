// ============================================================================
// cooksense — SMC0985KS CookSense main board (Boards A+B merged, ADR-0001/D4)
// Firmware-less, Pi-5-driven; ALL enforcement in hardware (ADR-0002).
//
// AUTHORING IDIOM (03_tscircuit/contracts.md): every pin bound to an explicit
// net.<NAME>; leading-digit rails carry an author-prefix N (N5V -> 5V, N3V3 ->
// 3V3, canon_net strips it); specialty parts carry supplierPartNumbers so the
// converter resolves the KiCad FPID from 02_parts/<MPN>/part.yaml.
//
// PIN MAPS are taken VERBATIM from the verified 02_parts/*/part.yaml (do not
// re-derive). Footprint tokens are chosen ONLY for the tscircuit pad COUNT/names
// (1..N); the real KiCad footprint comes from the part.yaml FPID override.
//
// DECODER FIX (ADR-0002 update 2026-07-22): the brief's SN74HC138/'139 are
// active-LOW; the ULN2803 coil driver has active-HIGH inputs, so an active-LOW
// one-hot would energise 7-of-8 coils and leave the SELECTED one OFF. FIXED with
// two SN74HC238 (active-HIGH 3-to-8): U-select (6 of 8) + D-select (4 of 8).
//
// PAD-NAME NOTES for the BOARD stage (schematic gate = ERC + refdes parity, which
// do NOT bind pad names, so these are documented, not blocking):
//   * DIP05 reed relays authored on 'dip4' (pads 1,2,3,4). Real KiCad footprint
//     cookhub:Relay_StandexDIP_1A_pinout12 pads = 1,7,8,14. Remap at board:
//     tsx1->1(COIL_A/+), tsx2->7(COIL_B/-), tsx3->8(CONTACT_B), tsx4->14(CONTACT_A).
//   * TPS259573 eFuse on 'dfn8' (pads 1..8); real WSON-8 also has EP(pad9)=GND —
//     tie EP to the GND pour at board (thermal path).
//   * JST/Micro-Fit MP mechanical tabs are not in the tscircuit model; mapped in
//     parity_padmap.txt for the board-parity stage.
// ============================================================================

const U = [1, 2, 3, 4, 5, 6]           // 6 U-selector relays
const D = [1, 2, 3, 4]                  // 4 D-selector relays
const CH = [                            // MCP3208 8 thermistor channels (brief §3)
  { n: 0, s: "TH_CAM_A" }, { n: 1, s: "TH_MOUNT_A" }, { n: 2, s: "TH_PORT_A" },
  { n: 3, s: "TH_CAM_B" }, { n: 4, s: "TH_MOUNT_B" }, { n: 5, s: "TH_PORT_B" },
  { n: 6, s: "TH_ENCLOSURE" }, { n: 7, s: "TH_SPARE" },
]
const SW = [                            // 4 switched high-side sensor rails (ADR-0004)
  { r: "A", rail: "N3V3_SW_A", en: "RAIL_EN_A" },
  { r: "B", rail: "N3V3_SW_B", en: "RAIL_EN_B" },
  { r: "RHA", rail: "N3V3_SW_RHA", en: "RAIL_EN_RHA" },
  { r: "RHE", rail: "N3V3_SW_RHE", en: "RAIL_EN_RHE" },
]

export default () => (
  <board width="90mm" height="70mm">

    {/* ================= BLOCK 1 — POWER INPUT + PROTECTION (brief §3.5) ==== */}
    {/* 5V SELV in (Micro-Fit) -> polyfuse -> reverse-pol P-FET -> eFuse(OVLO) */}
    <chip name="J_PWR" footprint="pinrow2" supplierPartNumbers={{ jlcpcb: ["C587657"] }}
      pinLabels={{ pin1: "V5IN", pin2: "RTN" }}
      connections={{ pin1: "net.N5V_IN", pin2: "net.GND" }} />
    <chip name="F1" footprint="1812" supplierPartNumbers={{ jlcpcb: ["C89650"] }}
      connections={{ pin1: "net.N5V_IN", pin2: "net.N5V_FUSED" }} />
    {/* reverse-polarity high-side P-FET: D=input side, S=load side, G=GND (AO3401A pins 1G/2S/3D) */}
    <chip name="Q_REV" footprint="sot23" supplierPartNumbers={{ jlcpcb: ["C15127"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.GND", pin2: "net.N5V_RPP", pin3: "net.N5V_FUSED" }} />
    {/* SS34 reverse crowbar: cathode to the input rail, anode to GND -> reverse input conducts, trips F1 */}
    <chip name="D_REVCLAMP" footprint="sma" supplierPartNumbers={{ jlcpcb: ["C8678"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.N5V_IN", pin2: "net.GND" }} />
    {/* TPS259573 eFuse: programmable OVLO cutoff (EN_OVLO_N divider), Rilm, Cdvdt, open-drain FLT=PWR_GOOD */}
    <chip name="U_EFUSE" footprint="dfn8" supplierPartNumbers={{ jlcpcb: ["C2653844"] }}
      pinLabels={{ pin1: "dVdt", pin2: "EN_OVLO_N", pin3: "IN", pin4: "IN", pin5: "OUT", pin6: "FLT_N", pin7: "ILM", pin8: "GND" }}
      connections={{
        pin1: "net.EF_DVDT", pin2: "net.EF_OVLO", pin3: "net.N5V_RPP", pin4: "net.N5V_RPP",
        pin5: "net.N5V_PROTECTED", pin6: "net.PWR_GOOD_N", pin7: "net.EF_ILM", pin8: "net.GND",
      }} />
    <capacitor name="C_DVDT" capacitance="1nF" footprint="0402" connections={{ pin1: "net.EF_DVDT", pin2: "net.GND" }} />
    <resistor name="R_OVT" resistance="100k" footprint="0402" connections={{ pin1: "net.N5V_RPP", pin2: "net.EF_OVLO" }} />
    <resistor name="R_OVB" resistance="15k" footprint="0402" connections={{ pin1: "net.EF_OVLO", pin2: "net.GND" }} />
    <resistor name="R_ILM" resistance="1.2k" footprint="0402" connections={{ pin1: "net.EF_ILM", pin2: "net.GND" }} />
    <resistor name="R_PG" resistance="100k" footprint="0402" connections={{ pin1: "net.PWR_GOOD_N", pin2: "net.N5V_PROTECTED" }} />
    {/* SMBJ5.0A TVS: cathode to protected rail, anode GND (pad1=K per part.yaml) */}
    <diode name="D_TVS" footprint="smb" supplierPartNumbers={{ jlcpcb: ["C113974"] }}
      connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.GND" }} />
    <diode name="D_ESD_IN" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }}
      connections={{ pin1: "net.N5V_IN", pin2: "net.GND" }} />
    {/* RVT220UF bulk (pad1=POS) */}
    <capacitor name="CE1" capacitance="220uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C2887273"] }}
      connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.GND" }} />
    <capacitor name="C_IN1" capacitance="10uF" footprint="0805" connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.GND" }} />
    <capacitor name="C_IN2" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.GND" }} />

    {/* ---- AMS1117-3.3 linear 3V3 + ferrite-split 3V3_ANALOG (E-TOPO all-linear) ---- */}
    <chip name="U_LDO" footprint="sot223" supplierPartNumbers={{ jlcpcb: ["C6186"] }}
      pinLabels={{ pin1: "GND", pin2: "VOUT", pin3: "VIN", pin4: "TAB" }}
      connections={{ pin1: "net.GND", pin2: "net.N3V3", pin3: "net.N5V_PROTECTED", pin4: "net.N3V3" }} />
    <capacitor name="C_LDOIN" capacitance="10uF" footprint="0805" connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.GND" }} />
    <capacitor name="C_LDOOUT" capacitance="22uF" footprint="0805" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_3V3" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    {/* GZ2012D601 ferrite: 3V3 -> 3V3_ANALOG (part.yaml 3V3->3V3A) */}
    <chip name="FB1" footprint="0805" supplierPartNumbers={{ jlcpcb: ["C1017"] }}
      connections={{ pin1: "net.N3V3", pin2: "net.N3V3_ANALOG" }} />
    <capacitor name="C_3V3A1" capacitance="10uF" footprint="0805" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.GND" }} />
    <capacitor name="C_3V3A2" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.GND" }} />

    {/* ================= BLOCK 2 — SAFETY AND-CHAIN (ADR-0002, brief §3.6) === */}
    {/* KEY_RELAY_ALLOWED = MODE_AUTO_HW·WD_OK·ESTOP_OK · TEMP_OK·MCU_RELAY_ENABLE·HOST_AUTH · FAULT_LATCH_CLEAR */}
    {/* SN74LVC1G11 3-in AND (pins 1A 2GND 3B 4Y 5VCC 6C). ANY false cuts the coil rail. */}
    <chip name="U_AND1" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.MODE_AUTO_HW", pin2: "net.GND", pin3: "net.WD_OK", pin4: "net.AND1", pin5: "net.N3V3", pin6: "net.ESTOP_OK" }} />
    <chip name="U_AND2" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.TEMP_OK", pin2: "net.GND", pin3: "net.MCU_RELAY_ENABLE", pin4: "net.AND2", pin5: "net.N3V3", pin6: "net.HOST_AUTH" }} />
    <chip name="U_AND3" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.AND1", pin2: "net.GND", pin3: "net.AND2", pin4: "net.KEY_RELAY_ALLOWED", pin5: "net.N3V3", pin6: "net.FAULT_LATCH_CLEAR" }} />
    <capacitor name="C_AND1" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_AND2" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_AND3" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- coil-rail high-side switch (AO3401A) driven by 2N7002 from COIL_EN ---- */}
    {/* COIL_EN = KEY_RELAY_ALLOWED THROUGH the Manual/Auto DPDT pole A (physical MANUAL rail cut, brief) */}
    <chip name="Q_COIL" footprint="sot23" supplierPartNumbers={{ jlcpcb: ["C15127"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.HS_GATE_COIL", pin2: "net.N5V_PROTECTED", pin3: "net.N5V_KEY_RELAY" }} />
    <resistor name="R_HSG" resistance="100k" footprint="0402" connections={{ pin1: "net.HS_GATE_COIL", pin2: "net.N5V_PROTECTED" }} />
    <chip name="Q_COILDRV" footprint="sot23" supplierPartNumbers={{ jlcpcb: ["C8545"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.COIL_EN", pin2: "net.GND", pin3: "net.HS_GATE_COIL" }} />
    <resistor name="R_COILENPD" resistance="100k" footprint="0402" connections={{ pin1: "net.COIL_EN", pin2: "net.GND" }} />
    <capacitor name="C_KR" capacitance="10uF" footprint="0805" connections={{ pin1: "net.N5V_KEY_RELAY", pin2: "net.GND" }} />

    {/* ---- fault-trigger AND + hardware fault latch (SR from 2x SN74LVC1G00 NAND) ---- */}
    {/* FAULT_SET_N = WD_OK · ESTOP_OK (low = a WD-timeout or E-stop fault) */}
    <chip name="U_FAULTAND" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.WD_OK", pin2: "net.GND", pin3: "net.ESTOP_OK", pin4: "net.FAULT_SET_N", pin5: "net.N3V3", pin6: "net.N3V3" }} />
    {/* /SR NAND latch: /S=FAULT_SET_N sets FAULT; /R=REARM_N (manual re-arm) clears. Q=FAULT, /Q=FAULT_LATCH_CLEAR. */}
    <chip name="U_LATCHA" footprint="sot23_5" supplierPartNumbers={{ jlcpcb: ["C8185"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "GND", pin4: "Y", pin5: "VCC" }}
      connections={{ pin1: "net.FAULT_SET_N", pin2: "net.FAULT_LATCH_CLEAR", pin3: "net.GND", pin4: "net.FAULT", pin5: "net.N3V3" }} />
    <chip name="U_LATCHB" footprint="sot23_5" supplierPartNumbers={{ jlcpcb: ["C8185"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "GND", pin4: "Y", pin5: "VCC" }}
      connections={{ pin1: "net.REARM_N", pin2: "net.FAULT", pin3: "net.GND", pin4: "net.FAULT_LATCH_CLEAR", pin5: "net.N3V3" }} />
    <capacitor name="C_FAULTAND" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_LATCHA" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_LATCHB" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- 595 output-enable interlock: SR_OE_N = NAND(MCU_RELAY_ENABLE, WD_OK) + 10k pullup ---- */}
    <chip name="U_OENAND" footprint="sot23_5" supplierPartNumbers={{ jlcpcb: ["C8185"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "GND", pin4: "Y", pin5: "VCC" }}
      connections={{ pin1: "net.MCU_RELAY_ENABLE", pin2: "net.WD_OK", pin3: "net.GND", pin4: "net.SR_OE_N", pin5: "net.N3V3" }} />
    <resistor name="R_OE" resistance="10k" footprint="0402" connections={{ pin1: "net.SR_OE_N", pin2: "net.N3V3" }} />
    <capacitor name="C_OENAND" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- SN74HC14 Schmitt: clean the slow/noisy E-stop, Mode, Door contacts (2 inverters each = buffer) ---- */}
    {/* HC14 pins: 1A 2=1Y 3=2A 4=2Y 5=3A 6=3Y 7=GND 8=4Y 9=4A 10=5Y 11=5A 12=6Y 13=6A 14=VCC (part.yaml) */}
    <chip name="U_SCHM" footprint="soic14" supplierPartNumbers={{ jlcpcb: ["C6820"] }}
      pinLabels={{ pin1: "1A", pin2: "1Y", pin3: "2A", pin4: "2Y", pin5: "3A", pin6: "3Y", pin7: "GND", pin8: "4Y", pin9: "4A", pin10: "5Y", pin11: "5A", pin12: "6Y", pin13: "6A", pin14: "VCC" }}
      connections={{
        pin1: "net.ESTOP_RAW", pin2: "net.ESTOP_NI", pin3: "net.ESTOP_NI", pin4: "net.ESTOP_OK",
        pin5: "net.MODE_RAW", pin6: "net.MODE_NI", pin9: "net.MODE_NI", pin8: "net.MODE_AUTO_HW",
        pin11: "net.DOOR_RAW", pin10: "net.DOOR_NI", pin13: "net.DOOR_NI", pin12: "net.DOOR_OK",
        pin7: "net.GND", pin14: "net.N3V3",
      }} />
    <capacitor name="C_SCHM" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ================= BLOCK 4 — WATCHDOG / SUPERVISOR (flag 1) =========== */}
    {/* TPS3823-33: FIXED ~1.6s coarse WD + brown-out + /MR. WD_OK = RESET_N (push-pull, high=OK). */}
    {/* The FAST <=500ms PRESS timeout is the SN74LVC1G123 one-shot (block 3), NOT this part. */}
    <chip name="U_WD" footprint="sot23_5" supplierPartNumbers={{ jlcpcb: ["C7719"] }}
      pinLabels={{ pin1: "RESET_N", pin2: "GND", pin3: "MR_N", pin4: "WDI", pin5: "VDD" }}
      connections={{ pin1: "net.WD_OK", pin2: "net.GND", pin3: "net.WD_MR_N", pin4: "net.WD_PET", pin5: "net.N3V3" }} />
    <capacitor name="C_WD" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <resistor name="R_MR" resistance="100k" footprint="0402" connections={{ pin1: "net.WD_MR_N", pin2: "net.N3V3" }} />
    <capacitor name="C_MR" capacitance="100nF" footprint="0402" connections={{ pin1: "net.WD_MR_N", pin2: "net.GND" }} />

    {/* ================= BLOCK 3 — PRESS one-shot + RELAY MATRIX ============ */}
    {/* SN74LVC1G123 retriggerable one-shot: B=PRESS_REQ edge -> Q=PRESS_TIMED high ~390ms (<500ms). */}
    {/* CLR_N=DOOR_OK: door open aborts the press (releases K_PRESS). tw = K*Rext*Cext = 390k*1uF. */}
    <chip name="U_ONESHOT" footprint="ssop8" supplierPartNumbers={{ jlcpcb: ["C123302"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "CLR_N", pin4: "GND", pin5: "Q", pin6: "Cext", pin7: "REXT_CEXT", pin8: "VCC" }}
      connections={{ pin1: "net.GND", pin2: "net.PRESS_REQ", pin3: "net.DOOR_OK", pin4: "net.GND", pin5: "net.PRESS_TIMED", pin6: "net.OS_C", pin7: "net.OS_RC", pin8: "net.N3V3" }} />
    <resistor name="R_OS" resistance="390k" footprint="0402" connections={{ pin1: "net.OS_RC", pin2: "net.N3V3" }} />
    <capacitor name="C_OS" capacitance="1uF" footprint="0603" connections={{ pin1: "net.OS_C", pin2: "net.OS_RC" }} />
    <capacitor name="C_OSV" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- 2x SN74HC595 shift registers (Pi-driven DATA/CLOCK/LATCH), cascade QH_S->SER ---- */}
    {/* 595 pins: 1QB 2QC 3QD 4QE 5QF 6QG 7QH 8GND 9QH_S 10SRCLR_N 11SRCLK 12RCLK 13OE_N 14SER 15QA 16VCC */}
    <chip name="U_SR1" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C10092"] }}
      pinLabels={{ pin1: "QB", pin2: "QC", pin3: "QD", pin4: "QE", pin5: "QF", pin6: "QG", pin7: "QH", pin8: "GND", pin9: "QH_S", pin10: "SRCLR_N", pin11: "SRCLK", pin12: "RCLK", pin13: "OE_N", pin14: "SER", pin15: "QA", pin16: "VCC" }}
      connections={{
        pin15: "net.DECU_A", pin1: "net.DECU_B", pin2: "net.DECU_C", pin3: "net.DECU_G1",
        pin4: "net.DECD_A", pin5: "net.DECD_B", pin6: "net.DECD_G1", pin7: "net.PRESS_REQ",
        pin9: "net.SR_CASCADE", pin10: "net.KEY_RESET_N", pin11: "net.KEY_CLOCK", pin12: "net.KEY_LATCH",
        pin13: "net.SR_OE_N", pin14: "net.KEY_DATA", pin8: "net.GND", pin16: "net.N3V3",
      }} />
    <chip name="U_SR2" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C10092"] }}
      pinLabels={{ pin1: "QB", pin2: "QC", pin3: "QD", pin4: "QE", pin5: "QF", pin6: "QG", pin7: "QH", pin8: "GND", pin9: "QH_S", pin10: "SRCLR_N", pin11: "SRCLK", pin12: "RCLK", pin13: "OE_N", pin14: "SER", pin15: "QA", pin16: "VCC" }}
      connections={{
        pin15: "net.STOP_REQ", pin9: "net.SR2_CASCADE",
        pin10: "net.KEY_RESET_N", pin11: "net.KEY_CLOCK", pin12: "net.KEY_LATCH",
        pin13: "net.SR_OE_N", pin14: "net.SR_CASCADE", pin8: "net.GND", pin16: "net.N3V3",
      }} />
    <capacitor name="C_SR1" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_SR2" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- 2x SN74HC238 ACTIVE-HIGH 3-to-8 decoders (one-hot BY CONSTRUCTION, ADR-0002) ---- */}
    {/* 238 pins: 1A 2B 3C 4/G2A 5/G2B 6G1 7Y7 8GND 9Y6 10Y5 11Y4 12Y3 13Y2 14Y1 15Y0 16VCC. Selected out = HIGH. */}
    {/* U-select: Y0..Y5 = U1..U6 -> ULN inputs. G1 enable from 595; /G2A=/G2B=GND; Y6/Y7 unused (NC). */}
    <chip name="U_DECU" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["SN74HC238DR"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "C", pin4: "G2A_N", pin5: "G2B_N", pin6: "G1", pin7: "Y7", pin8: "GND", pin9: "Y6", pin10: "Y5", pin11: "Y4", pin12: "Y3", pin13: "Y2", pin14: "Y1", pin15: "Y0", pin16: "VCC" }}
      connections={{
        pin1: "net.DECU_A", pin2: "net.DECU_B", pin3: "net.DECU_C", pin4: "net.GND", pin5: "net.GND", pin6: "net.DECU_G1",
        pin15: "net.SEL_U1", pin14: "net.SEL_U2", pin13: "net.SEL_U3", pin12: "net.SEL_U4", pin11: "net.SEL_U5", pin10: "net.SEL_U6",
        pin8: "net.GND", pin16: "net.N3V3",
      }} />
    {/* D-select: Y0..Y3 = D1..D4. Only A,B used (4 outputs) -> C(3) tied GND; Y4..Y7 unused (NC). */}
    <chip name="U_DECD" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["SN74HC238DR"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "C", pin4: "G2A_N", pin5: "G2B_N", pin6: "G1", pin7: "Y7", pin8: "GND", pin9: "Y6", pin10: "Y5", pin11: "Y4", pin12: "Y3", pin13: "Y2", pin14: "Y1", pin15: "Y0", pin16: "VCC" }}
      connections={{
        pin1: "net.DECD_A", pin2: "net.DECD_B", pin3: "net.GND", pin4: "net.GND", pin5: "net.GND", pin6: "net.DECD_G1",
        pin15: "net.SEL_D1", pin14: "net.SEL_D2", pin13: "net.SEL_D3", pin12: "net.SEL_D4",
        pin8: "net.GND", pin16: "net.N3V3",
      }} />
    <capacitor name="C_DECU" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_DECD" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- 2x ULN2803A coil drivers (16 ch, 12 used, 4 spare). COM -> gated 5V_KEY_RELAY (flyback clamp). ---- */}
    {/* ULN pins: 1-8 IN1-8, 9 GND, 10 COM, 11-18 OUT8-OUT1 (OUTn opposite corner from INn). */}
    <chip name="U_ULNA" footprint="soic18w" supplierPartNumbers={{ jlcpcb: ["C9683"] }}
      pinLabels={{ pin1: "IN1", pin2: "IN2", pin3: "IN3", pin4: "IN4", pin5: "IN5", pin6: "IN6", pin7: "IN7", pin8: "IN8", pin9: "GND", pin10: "COM", pin11: "OUT8", pin12: "OUT7", pin13: "OUT6", pin14: "OUT5", pin15: "OUT4", pin16: "OUT3", pin17: "OUT2", pin18: "OUT1" }}
      connections={{
        pin1: "net.SEL_U1", pin18: "net.COIL_U1_N", pin2: "net.SEL_U2", pin17: "net.COIL_U2_N",
        pin3: "net.SEL_U3", pin16: "net.COIL_U3_N", pin4: "net.SEL_U4", pin15: "net.COIL_U4_N",
        pin5: "net.SEL_U5", pin14: "net.COIL_U5_N", pin6: "net.SEL_U6", pin13: "net.COIL_U6_N",
        pin7: "net.SEL_D1", pin12: "net.COIL_D1_N", pin8: "net.SEL_D2", pin11: "net.COIL_D2_N",
        pin9: "net.GND", pin10: "net.N5V_KEY_RELAY",
      }} />
    <chip name="U_ULNB" footprint="soic18w" supplierPartNumbers={{ jlcpcb: ["C9683"] }}
      pinLabels={{ pin1: "IN1", pin2: "IN2", pin3: "IN3", pin4: "IN4", pin5: "IN5", pin6: "IN6", pin7: "IN7", pin8: "IN8", pin9: "GND", pin10: "COM", pin11: "OUT8", pin12: "OUT7", pin13: "OUT6", pin14: "OUT5", pin15: "OUT4", pin16: "OUT3", pin17: "OUT2", pin18: "OUT1" }}
      connections={{
        pin1: "net.SEL_D3", pin18: "net.COIL_D3_N", pin2: "net.SEL_D4", pin17: "net.COIL_D4_N",
        pin3: "net.PRESS_TIMED", pin16: "net.COIL_PRESS_N", pin4: "net.STOP_REQ", pin15: "net.COIL_STOP_N",
        pin9: "net.GND", pin10: "net.N5V_KEY_RELAY",
      }} />
    <capacitor name="C_ULNA" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5V_KEY_RELAY", pin2: "net.GND" }} />
    <capacitor name="C_ULNB" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5V_KEY_RELAY", pin2: "net.GND" }} />

    {/* ---- 12x DIP05-1A72-12L reed relays. Coil (tsx pins 1,2 = real pads 1,7) on the gated rail; ---- */}
    {/* contact (tsx pins 3,4 = real pads 8,14) in the ISOLATED keypad domain. NO shared GND (block 7). */}
    {U.map((i) => (
      <chip key={`KU${i}`} name={`K_U${i}`} footprint="dip4" supplierPartNumbers={{ jlcpcb: ["DIP05-1A72-12L"] }}
        pinLabels={{ pin1: "COIL_A", pin2: "COIL_B", pin3: "CONTACT_B", pin4: "CONTACT_A" }}
        connections={{ pin1: "net.N5V_KEY_RELAY", pin2: `net.COIL_U${i}_N`, pin3: `net.KP_U${i}`, pin4: "net.U_SEL_BUS" }} />
    ))}
    {D.map((i) => (
      <chip key={`KD${i}`} name={`K_D${i}`} footprint="dip4" supplierPartNumbers={{ jlcpcb: ["DIP05-1A72-12L"] }}
        pinLabels={{ pin1: "COIL_A", pin2: "COIL_B", pin3: "CONTACT_B", pin4: "CONTACT_A" }}
        connections={{ pin1: "net.N5V_KEY_RELAY", pin2: `net.COIL_D${i}_N`, pin3: `net.KP_D${i}`, pin4: "net.D_SEL_BUS" }} />
    ))}
    {/* K_PRESS bridges U_SEL_BUS -> RKEY -> D_SEL_BUS (RKEY = solder-select field, 0R default) */}
    <chip name="K_PRESS" footprint="dip4" supplierPartNumbers={{ jlcpcb: ["DIP05-1A72-12L"] }}
      pinLabels={{ pin1: "COIL_A", pin2: "COIL_B", pin3: "CONTACT_B", pin4: "CONTACT_A" }}
      connections={{ pin1: "net.N5V_KEY_RELAY", pin2: "net.COIL_PRESS_N", pin3: "net.RKEY_MID", pin4: "net.U_SEL_BUS" }} />
    {/* K_STOP: dedicated preempt path KP_U6 -> RSTOP -> KP_D1 (brief §4 U6-K_STOP-RSTOP-D1) */}
    <chip name="K_STOP" footprint="dip4" supplierPartNumbers={{ jlcpcb: ["DIP05-1A72-12L"] }}
      pinLabels={{ pin1: "COIL_A", pin2: "COIL_B", pin3: "CONTACT_B", pin4: "CONTACT_A" }}
      connections={{ pin1: "net.N5V_KEY_RELAY", pin2: "net.COIL_STOP_N", pin3: "net.RSTOP_MID", pin4: "net.KP_U6" }} />
    {/* RKEY/RSTOP solder-select resistors (1206), 0R default (ADR-0006 T1), in the isolated keypad domain */}
    <resistor name="R_KEY" resistance="0" footprint="1206" connections={{ pin1: "net.RKEY_MID", pin2: "net.D_SEL_BUS" }} />
    <resistor name="R_STOP" resistance="0" footprint="1206" connections={{ pin1: "net.RSTOP_MID", pin2: "net.KP_D1" }} />

    {/* ================= BLOCK 7 — KEYPAD-ISOLATION DOMAIN CONNECTOR ======== */}
    {/* 10 lines U1-U6,D1-D4 to Board C. ISOLATED: MP tabs -> GND_ISO (part.yaml), NO shared GND. */}
    <chip name="J_KEY_MATRIX" footprint="pinrow10" supplierPartNumbers={{ jlcpcb: ["C2683602"] }}
      connections={{
        pin1: "net.KP_U1", pin2: "net.KP_U2", pin3: "net.KP_U3", pin4: "net.KP_U4", pin5: "net.KP_U5",
        pin6: "net.KP_U6", pin7: "net.KP_D1", pin8: "net.KP_D2", pin9: "net.KP_D3", pin10: "net.KP_D4",
      }} />

    {/* ================= BLOCK 5 — SENSING ================================= */}
    {/* MCP3208 8-ch SPI ADC: CH0-7 = thermistor divider nodes. VDD/VREF = 3V3_ANALOG. */}
    <chip name="U_ADC" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C16939"] }}
      pinLabels={{ pin1: "CH0", pin2: "CH1", pin3: "CH2", pin4: "CH3", pin5: "CH4", pin6: "CH5", pin7: "CH6", pin8: "CH7", pin9: "DGND", pin10: "CS_N", pin11: "DIN", pin12: "DOUT", pin13: "CLK", pin14: "AGND", pin15: "VREF", pin16: "VDD" }}
      connections={{
        pin1: "net.ADC_CH0", pin2: "net.ADC_CH1", pin3: "net.ADC_CH2", pin4: "net.ADC_CH3",
        pin5: "net.ADC_CH4", pin6: "net.ADC_CH5", pin7: "net.ADC_CH6", pin8: "net.ADC_CH7",
        pin9: "net.GND", pin10: "net.ADC_CS_N", pin11: "net.SPI_MOSI", pin12: "net.SPI_MISO",
        pin13: "net.SPI_SCLK", pin14: "net.GND", pin15: "net.N3V3_ANALOG", pin16: "net.N3V3_ANALOG",
      }} />
    <capacitor name="C_ADCV" capacitance="1uF" footprint="0603" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.GND" }} />
    <capacitor name="C_ADCV2" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.GND" }} />
    {/* per-channel front end: 10k ref -> 3V3_ANALOG (top), external NTC -> GND (via connector/TP), 1k+100nF RC into the ADC pin */}
    {CH.map((c) => (
      <>
        <resistor key={`rref${c.n}`} name={`R_REF${c.n}`} resistance="10k" footprint="0402" connections={{ pin1: "net.N3V3_ANALOG", pin2: `net.${c.s}` }} />
        <resistor key={`rser${c.n}`} name={`R_SER${c.n}`} resistance="1k" footprint="0402" connections={{ pin1: `net.${c.s}`, pin2: `net.ADC_CH${c.n}` }} />
        <capacitor key={`cflt${c.n}`} name={`C_FLT${c.n}`} capacitance="100nF" footprint="0402" connections={{ pin1: `net.ADC_CH${c.n}`, pin2: "net.GND" }} />
      </>
    ))}

    {/* LM393 dual comparator: HARDWARE over-temp inhibit on TH_CAM_A/B -> wired-AND TEMP_OK (brief §3.14) */}
    {/* IN+ = TH_CAM node (falls when hot); IN- = threshold; hot -> OUT low -> TEMP_OK low. Open-collector. */}
    <chip name="U_COMP" footprint="soic8" supplierPartNumbers={{ jlcpcb: ["C67470"] }}
      pinLabels={{ pin1: "1OUT", pin2: "1IN_N", pin3: "1IN_P", pin4: "GND", pin5: "2IN_P", pin6: "2IN_N", pin7: "2OUT", pin8: "VCC" }}
      connections={{
        pin1: "net.TEMP_OK", pin2: "net.TCAM_THRESH", pin3: "net.TH_CAM_A", pin4: "net.GND",
        pin5: "net.TH_CAM_B", pin6: "net.TCAM_THRESH", pin7: "net.TEMP_OK", pin8: "net.N5V_PROTECTED",
      }} />
    <resistor name="R_TH1" resistance="10k" footprint="0402" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.TCAM_THRESH" }} />
    <resistor name="R_TH2" resistance="10k" footprint="0402" connections={{ pin1: "net.TCAM_THRESH", pin2: "net.GND" }} />
    <resistor name="R_HYS1" resistance="1M" footprint="0402" connections={{ pin1: "net.TEMP_OK", pin2: "net.TH_CAM_A" }} />
    <resistor name="R_HYS2" resistance="1M" footprint="0402" connections={{ pin1: "net.TEMP_OK", pin2: "net.TH_CAM_B" }} />
    <resistor name="R_TEMPOK" resistance="10k" footprint="0402" connections={{ pin1: "net.TEMP_OK", pin2: "net.N3V3" }} />
    <capacitor name="C_COMP" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.GND" }} />

    {/* MAX31856 K-type thermocouple -> SPI. PCC-SMP-K jack at board edge; input RC + BIAS per datasheet. */}
    <chip name="U_TC" footprint="tssop14" supplierPartNumbers={{ jlcpcb: ["C2653162"] }}
      pinLabels={{ pin1: "AGND", pin2: "BIAS", pin3: "T_N", pin4: "T_P", pin5: "AVDD", pin6: "DNC", pin7: "DRDY_N", pin8: "DVDD", pin9: "CS_N", pin10: "SCK", pin11: "SDO", pin12: "SDI", pin13: "FAULT_N", pin14: "DGND" }}
      connections={{
        pin1: "net.GND", pin2: "net.TC_NEG", pin3: "net.TC_NEG", pin4: "net.TC_POS", pin5: "net.N3V3",
        pin7: "net.TC_DRDY_N", pin8: "net.N3V3", pin9: "net.TC_CS_N", pin10: "net.SPI_SCLK",
        pin11: "net.SPI_MISO", pin12: "net.SPI_MOSI", pin13: "net.TC_FAULT_N", pin14: "net.GND",
      }} />
    <chip name="J_TC" footprint="pinrow2" supplierPartNumbers={{ jlcpcb: ["PCC-SMP-K"] }}
      pinLabels={{ pin1: "TCP", pin2: "TCN" }}
      connections={{ pin1: "net.TC_POS_IN", pin2: "net.TC_NEG_IN" }} />
    <resistor name="R_TCP" resistance="100" footprint="0402" connections={{ pin1: "net.TC_POS_IN", pin2: "net.TC_POS" }} />
    <resistor name="R_TCN" resistance="100" footprint="0402" connections={{ pin1: "net.TC_NEG_IN", pin2: "net.TC_NEG" }} />
    <capacitor name="C_TCD" capacitance="100nF" footprint="0402" connections={{ pin1: "net.TC_POS", pin2: "net.TC_NEG" }} />
    <capacitor name="C_TCPA" capacitance="10nF" footprint="0402" connections={{ pin1: "net.TC_POS", pin2: "net.GND" }} />
    <capacitor name="C_TCNA" capacitance="10nF" footprint="0402" connections={{ pin1: "net.TC_NEG", pin2: "net.GND" }} />
    <capacitor name="C_TCAV" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_TCDV" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* HX711 load-cell link (external cook-loadcell board). B5B-XH 5-pin: 5V,3V3,GND,DAT,CLK (cook-loadcell compatible) */}
    <chip name="J_LOADCELL" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C157991"] }}
      connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.N3V3", pin3: "net.GND", pin4: "net.LC_DAT", pin5: "net.LC_CLK" }} />
    <resistor name="R_LCDAT" resistance="33" footprint="0402" connections={{ pin1: "net.LC_DAT", pin2: "net.LC_DAT_PI" }} />
    <resistor name="R_LCCLK" resistance="33" footprint="0402" connections={{ pin1: "net.LC_CLK", pin2: "net.LC_CLK_PI" }} />
    <diode name="D_LCDAT" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }} connections={{ pin1: "net.LC_DAT", pin2: "net.GND" }} />
    <diode name="D_LCCLK" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }} connections={{ pin1: "net.LC_CLK", pin2: "net.GND" }} />

    {/* ---- discrete safety inputs: DOOR (NC reed+EOL), E-STOP (2x NC), MODE (DPDT) ---- */}
    {/* SM05B-GHS 5-pin used for each (the brief's 4-pin locking role; 5th pin = GND/shield). */}
    <chip name="J_DOOR" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3", pin2: "net.DOOR_RAW", pin3: "net.GND", pin4: "net.DOOR_RAW", pin5: "net.GND" }} />
    <resistor name="R_DOORPU" resistance="10k" footprint="0402" connections={{ pin1: "net.DOOR_RAW", pin2: "net.N3V3" }} />
    <diode name="D_DOOR" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }} connections={{ pin1: "net.DOOR_RAW", pin2: "net.GND" }} />
    {/* E-stop: contact A monitored (ESTOP_RAW, high=OK); contact B (pins3-4) in series with the ISOLATED */}
    {/* contactor loop (opto C -> ESTOP_B_IN, ESTOP_B_OUT -> J_CONTACTOR): E-stop physically breaks it. */}
    <chip name="J_ESTOP" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3", pin2: "net.ESTOP_RAW", pin3: "net.CONTACTOR_C", pin4: "net.CONTACTOR_LOOP", pin5: "net.GND" }} />
    <resistor name="R_ESTOPPD" resistance="10k" footprint="0402" connections={{ pin1: "net.ESTOP_RAW", pin2: "net.GND" }} />
    <diode name="D_ESTOP" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }} connections={{ pin1: "net.ESTOP_RAW", pin2: "net.GND" }} />
    {/* Mode DPDT: pole A (pins1-2) = physical coil-EN gate (MANUAL cuts the rail); pole B (pins3-4) = MODE_RAW logic */}
    <chip name="J_MODE" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.KEY_RELAY_ALLOWED", pin2: "net.COIL_EN", pin3: "net.N3V3", pin4: "net.MODE_RAW", pin5: "net.GND" }} />
    <resistor name="R_MODEPD" resistance="10k" footprint="0402" connections={{ pin1: "net.MODE_RAW", pin2: "net.GND" }} />

    {/* ---- optically-isolated external-contactor request (LTV-817S), <=30V/50mA dry (brief §3) ---- */}
    <chip name="U_OPTO" footprint="dip4" supplierPartNumbers={{ jlcpcb: ["C125121"] }}
      pinLabels={{ pin1: "ANODE", pin2: "CATHODE", pin3: "EMITTER", pin4: "COLLECTOR" }}
      connections={{ pin1: "net.OPTO_LED_A", pin2: "net.GND", pin3: "net.CONTACTOR_E", pin4: "net.CONTACTOR_C" }} />
    <resistor name="R_OPTOLED" resistance="330" footprint="0603" connections={{ pin1: "net.CONTACTOR_REQ", pin2: "net.OPTO_LED_A" }} />
    <chip name="J_CONTACTOR" footprint="pinrow2" supplierPartNumbers={{ jlcpcb: ["C474892"] }}
      pinLabels={{ pin1: "C", pin2: "E" }}
      connections={{ pin1: "net.CONTACTOR_LOOP", pin2: "net.CONTACTOR_E" }} />

    {/* ================= BLOCK 6 — MCP23017 EXPANDER (ADR-0003) ============ */}
    {/* Slow signals: 4 rail enables, contactor req, re-arm, BOARD_ID straps; readbacks on GPB0-7. */}
    {/* flag 3: pin12 = SCL (I2C), NOT SCK; pins 11 & 14 = NC (do NOT wire). */}
    <chip name="U_EXP" footprint="ssop28" supplierPartNumbers={{ jlcpcb: ["C506653"] }}
      pinLabels={{ pin1: "GPB0", pin2: "GPB1", pin3: "GPB2", pin4: "GPB3", pin5: "GPB4", pin6: "GPB5", pin7: "GPB6", pin8: "GPB7", pin9: "VDD", pin10: "VSS", pin11: "NC", pin12: "SCL", pin13: "SDA", pin14: "NC", pin15: "A0", pin16: "A1", pin17: "A2", pin18: "RESET_N", pin19: "INTB", pin20: "INTA", pin21: "GPA0", pin22: "GPA1", pin23: "GPA2", pin24: "GPA3", pin25: "GPA4", pin26: "GPA5", pin27: "GPA6", pin28: "GPA7" }}
      connections={{
        pin1: "net.PWR_GOOD_N", pin2: "net.MODE_AUTO_HW", pin3: "net.ESTOP_OK", pin4: "net.DOOR_OK",
        pin5: "net.TEMP_OK", pin6: "net.FAULT", pin7: "net.TC_FAULT_N", pin8: "net.WD_OK",
        pin9: "net.N3V3", pin10: "net.GND", pin12: "net.I2C_SCL", pin13: "net.I2C_SDA",
        pin15: "net.GND", pin16: "net.GND", pin17: "net.GND", pin18: "net.EXP_RST_N",
        pin19: "net.EXP_INTB", pin20: "net.INT_ALERT",
        pin21: "net.RAIL_EN_A", pin22: "net.RAIL_EN_B", pin23: "net.RAIL_EN_RHA", pin24: "net.RAIL_EN_RHE",
        pin25: "net.CONTACTOR_REQ", pin26: "net.REARM_N", pin27: "net.BOARD_ID0", pin28: "net.BOARD_ID1",
      }} />
    <capacitor name="C_EXP" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <resistor name="R_EXPRST" resistance="10k" footprint="0402" connections={{ pin1: "net.EXP_RST_N", pin2: "net.N3V3" }} />
    <resistor name="R_BID0" resistance="10k" footprint="0402" connections={{ pin1: "net.BOARD_ID0", pin2: "net.GND" }} />
    <resistor name="R_BID1" resistance="10k" footprint="0402" connections={{ pin1: "net.BOARD_ID1", pin2: "net.N3V3" }} />

    {/* ================= per-sensor SWITCHED 3V3 rails (ADR-0004 phantom-power rule) ==== */}
    {/* high-side P-FET (S=3V3, D=switched rail) driven by 2N7002 from an expander enable; I2C pullups off the switched rail */}
    {SW.map((s) => (
      <>
        <chip key={`qsw${s.r}`} name={`Q_SW${s.r}`} footprint="sot23" supplierPartNumbers={{ jlcpcb: ["C15127"] }}
          pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
          connections={{ pin1: `net.SWG_${s.r}`, pin2: "net.N3V3", pin3: `net.${s.rail}` }} />
        <resistor key={`rswpu${s.r}`} name={`R_SWPU${s.r}`} resistance="100k" footprint="0402" connections={{ pin1: `net.SWG_${s.r}`, pin2: "net.N3V3" }} />
        <chip key={`qswd${s.r}`} name={`Q_SWDRV${s.r}`} footprint="sot23" supplierPartNumbers={{ jlcpcb: ["C8545"] }}
          pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
          connections={{ pin1: `net.${s.en}`, pin2: "net.GND", pin3: `net.SWG_${s.r}` }} />
        <capacitor key={`csw${s.r}`} name={`C_SW${s.r}`} capacitance="1uF" footprint="0603" connections={{ pin1: `net.${s.rail}`, pin2: "net.GND" }} />
      </>
    ))}

    {/* thermal-head connectors (cam I2C pass-through + 3 thermistors + shield), humidity-pod connectors */}
    <chip name="J_THERM_A" footprint="pinrow8" supplierPartNumbers={{ jlcpcb: ["C265111"] }}
      connections={{ pin1: "net.N3V3_SW_A", pin2: "net.GND", pin3: "net.SDA_A", pin4: "net.SCL_A", pin5: "net.TH_CAM_A", pin6: "net.TH_MOUNT_A", pin7: "net.TH_PORT_A", pin8: "net.SHIELD_DRAIN" }} />
    <chip name="J_THERM_B" footprint="pinrow8" supplierPartNumbers={{ jlcpcb: ["C265111"] }}
      connections={{ pin1: "net.N3V3_SW_B", pin2: "net.GND", pin3: "net.SDA_B", pin4: "net.SCL_B", pin5: "net.TH_CAM_B", pin6: "net.TH_MOUNT_B", pin7: "net.TH_PORT_B", pin8: "net.SHIELD_DRAIN" }} />
    <chip name="J_RH_AMBIENT" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3_SW_RHA", pin2: "net.GND", pin3: "net.SDA_RHA", pin4: "net.SCL_RHA", pin5: "net.SHIELD_DRAIN" }} />
    <chip name="J_RH_EXHAUST" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3_SW_RHE", pin2: "net.GND", pin3: "net.SDA_RHE", pin4: "net.SCL_RHE", pin5: "net.SHIELD_DRAIN" }} />
    {/* I2C pullups powered from the SWITCHED sensor rail (die with the rail — ADR-0004 N1) */}
    <resistor name="R_SDAA" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SDA_A", pin2: "net.N3V3_SW_A" }} />
    <resistor name="R_SCLA" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SCL_A", pin2: "net.N3V3_SW_A" }} />
    <resistor name="R_SDAB" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SDA_B", pin2: "net.N3V3_SW_B" }} />
    <resistor name="R_SCLB" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SCL_B", pin2: "net.N3V3_SW_B" }} />
    <resistor name="R_SDARHA" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SDA_RHA", pin2: "net.N3V3_SW_RHA" }} />
    <resistor name="R_SCLRHA" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SCL_RHA", pin2: "net.N3V3_SW_RHA" }} />
    <resistor name="R_SDARHE" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SDA_RHE", pin2: "net.N3V3_SW_RHE" }} />
    <resistor name="R_SCLRHE" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SCL_RHE", pin2: "net.N3V3_SW_RHE" }} />
    {/* shield drain: RC/0R option to GND at a single point (brief: NOT hard-bonded to signal ground) */}
    <resistor name="R_SHIELD" resistance="0" footprint="0603" connections={{ pin1: "net.SHIELD_DRAIN", pin2: "net.GND" }} />

    {/* ================= Raspberry Pi 5 40-pin header (signals only; power NC) ==== */}
    {/* GND = 6,9,14,20,25,30,34,39. Power (1,2,4,17) + HAT-ID (27,28) = NC (brief §3, no backfeed). */}
    {/* Exact GPIO<->function pin-mux (incl. sensor-I2C dtoverlays) is the Gate-4 pin-map artifact. */}
    <chip name="J_PI" footprint="pinrow40" supplierPartNumbers={{ jlcpcb: ["C35165"] }}
      connections={{
        pin3: "net.I2C_SDA", pin5: "net.I2C_SCL", pin6: "net.GND",
        pin7: "net.SDA_A", pin8: "net.SCL_A", pin9: "net.GND", pin10: "net.SDA_B",
        pin11: "net.WD_PET", pin12: "net.SCL_B", pin13: "net.INT_ALERT", pin14: "net.GND",
        pin15: "net.HOST_AUTH", pin16: "net.MCU_RELAY_ENABLE", pin18: "net.SDA_RHA",
        pin19: "net.SPI_MOSI", pin20: "net.GND", pin21: "net.SPI_MISO", pin22: "net.TC_DRDY_N",
        pin23: "net.SPI_SCLK", pin24: "net.ADC_CS_N", pin25: "net.GND", pin26: "net.TC_CS_N",
        pin29: "net.KEY_DATA", pin30: "net.GND", pin31: "net.KEY_CLOCK", pin32: "net.KEY_LATCH",
        pin33: "net.KEY_RESET_N", pin34: "net.GND", pin35: "net.SCL_RHA", pin36: "net.SDA_RHE",
        pin37: "net.SCL_RHE", pin38: "net.LC_DAT_PI", pin39: "net.GND", pin40: "net.LC_CLK_PI",
      }} />

    {/* ================= test points (bench bring-up G4) ==================== */}
    <testpoint name="TP_5VP" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.N5V_PROTECTED" }} />
    <testpoint name="TP_3V3" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.N3V3" }} />
    <testpoint name="TP_5VKR" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.N5V_KEY_RELAY" }} />
    <testpoint name="TP_ALLOW" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.KEY_RELAY_ALLOWED" }} />
    <testpoint name="TP_WDOK" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.WD_OK" }} />
    <testpoint name="TP_TEMPOK" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TEMP_OK" }} />
    <testpoint name="TP_ESTOP" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.ESTOP_OK" }} />
    <testpoint name="TP_FAULT" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.FAULT" }} />
    <testpoint name="TP_PGOOD" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.PWR_GOOD_N" }} />
    <testpoint name="TP_TCDRDY" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TC_DRDY_N" }} />
    <testpoint name="TP_TCFAULT" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TC_FAULT_N" }} />
    <testpoint name="TP_USEL" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.U_SEL_BUS" }} />
    <testpoint name="TP_DSEL" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.D_SEL_BUS" }} />
    <testpoint name="TP_RKEY" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.RKEY_MID" }} />
    <testpoint name="TP_ENCL" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TH_ENCLOSURE" }} />
    <testpoint name="TP_SPARE" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TH_SPARE" }} />

    {/* ================= mounting holes (M2.5 Pi-HAT) — non-electrical ====== */}
    <hole name="H1" diameter="2.75mm" pcbX={-40} pcbY={30} />
    <hole name="H2" diameter="2.75mm" pcbX={40} pcbY={30} />
    <hole name="H3" diameter="2.75mm" pcbX={-40} pcbY={-30} />
    <hole name="H4" diameter="2.75mm" pcbX={40} pcbY={-30} />
  </board>
)

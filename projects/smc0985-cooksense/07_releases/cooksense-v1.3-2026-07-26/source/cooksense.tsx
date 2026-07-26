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
    {/* SS34 reverse crowbar: cathode on 5V_FUSED (DOWNSTREAM of F1), anode to GND. On reverse hookup
        it conducts and the fault current path (supply -> J_PWR -> F1 -> clamp -> GND) passes THROUGH
        the polyfuse, so F1 trips = the authored intent. Moved from 5V_IN 2026-07-23 (pin review Q2):
        upstream of F1 the clamp current bypassed the fuse and was bounded only by the supply. */}
    <chip name="D_REVCLAMP" footprint="sma" supplierPartNumbers={{ jlcpcb: ["C8678"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.N5V_FUSED", pin2: "net.GND" }} />
    {/* TPS259573 eFuse: programmable OVLO cutoff (EN_OVLO_N divider), Rilm, Cdvdt. FLT_N pin6 is
        open-drain ACTIVE-LOW FAULT (LOW=fault, pulled HIGH=good by R_PG) -> net EFUSE_FLT_N, read by
        the expander GPA0 (software: HIGH=power good). Renamed from PWR_GOOD_N 2026-07-23 (pin review
        Q1): the _N name implied LOW=power-good, backwards from the actual sense; consumers are
        software-read only (no hardware AND-chain input), so the RENAME is the honest fix. */}
    <chip name="U_EFUSE" footprint="dfn8" supplierPartNumbers={{ jlcpcb: ["C2653844"] }}
      pinLabels={{ pin1: "dVdt", pin2: "EN_OVLO_N", pin3: "IN", pin4: "IN", pin5: "OUT", pin6: "FLT_N", pin7: "ILM", pin8: "GND" }}
      connections={{
        pin1: "net.EF_DVDT", pin2: "net.EF_OVLO", pin3: "net.N5V_RPP", pin4: "net.N5V_RPP",
        pin5: "net.N5V_PROTECTED", pin6: "net.EFUSE_FLT_N", pin7: "net.EF_ILM", pin8: "net.GND",
      }} />
    <capacitor name="C_DVDT" capacitance="1nF" footprint="0402" connections={{ pin1: "net.EF_DVDT", pin2: "net.GND" }} />
    <resistor name="R_OVT" resistance="100k" footprint="0402" connections={{ pin1: "net.N5V_RPP", pin2: "net.EF_OVLO" }} />
    <resistor name="R_OVB" resistance="15k" footprint="0402" connections={{ pin1: "net.EF_OVLO", pin2: "net.GND" }} />
    <resistor name="R_ILM" resistance="1.2k" footprint="0402" connections={{ pin1: "net.EF_ILM", pin2: "net.GND" }} />
    <resistor name="R_PG" resistance="100k" footprint="0402" connections={{ pin1: "net.EFUSE_FLT_N", pin2: "net.N5V_PROTECTED" }} />
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
    {/* FAULT_SET_N = WD_OK · ESTOP_OK · TEMP_OK (ADR-0011 §2, v1.2: TEMP_OK ADDED — the
        third input was tied N3V3 in <=v1.1, so a thermal trip never LATCHED and silently
        self-cleared when the NTC cooled; review F3a). */}
    <chip name="U_FAULTAND" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.WD_OK", pin2: "net.GND", pin3: "net.ESTOP_OK", pin4: "net.FAULT_SET_N", pin5: "net.N3V3", pin6: "net.TEMP_OK" }} />
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
    {/* v1.2 P0 FIX (ADR-0011 section 8, safety truth-table review 2026-07-25): WDI MUST NOT be
        left high-impedance. TPS3823 datasheet SLVS165O sec.7.3.4, VERBATIM: "If the WDI pin
        detects a high-impedance state, the TPS3820, TPS3823, TPS3824, or TPS3828 generates
        internal WDI pulse to make sure that RESET does not assert. If this behavior is not
        desired, place a 1kOhm resistor from WDI to ground." Without it, a Pi that dies and
        releases GPIO17 back to input leaves WD_OK HIGH forever, the MCP23017 keeps its
        CONTACTOR_REQ latch, and U_CAND1/U_CAND2 hold the external cooking contactor ENERGISED.
        THE VALUE IS THE FIX, not the presence of a resistor. SLVS165O sec.6.5: I_IL at WDI =
        140 typ / 190 max uA (WDI = 0.3V) — the pin SOURCES that much, so a 100k pull-down
        would need 19V to hold it low and the detector would still see the internal pulses.
        1k sinks 190uA at 0.19V, far under V_IL = 0.3*VDD = 0.99V. Cost: 3.3mA of Pi GPIO
        drive while the heartbeat is high, 10.9mW in an 0402 (62.5mW rated). This is the one
        pull on the board that is NOT 100k, and the datasheet is why. */}
    {/* CODE PINNED (P0, 2026-07-26). This resistor is the reason the whole
        "pin the code, not just the value" rule exists, and it was still unpinned
        after R_OPENT was fixed. The auto-picker grouped it onto C25741 =
        0402WGF1003TCE = 100k, i.e. the EXACT substitution ADR-0011 and the
        ORDER_README bring-up ritual both forbid in writing: "do NOT normalise
        R_WDPETPD to 100k, a 100k hold lets the supervisor pet ITSELF and
        silently disables the watchdog". C11702 = 0402WGF1001TCE = 1k, already on
        this BOM for R_SER0-7, catalog-verified in lcsc_passives_ledger.yaml.
        WHY EVERY GATE STAYED GREEN, because this is the transferable part:
          - E-INV `part_value` asserts R_WDPETPD == 1k and PASSES — it grades the
            NETLIST value, which was always 1k. The netlist was never wrong.
          - M-BOM leg C PASSES because the BOM Comment for the merged line reads
            "100kΩ / 1kΩ" and the label parser takes the FIRST token, 100k, which
            matches C25741. An aggregated Comment defeats the decade check.
          - jlc_twin, DRC, A-ROT, A-POS all pass: nothing about geometry changed.
        The one checker that sees it is `bom_source_check.py --circuit-only`,
        which compares the tsx VALUE PROP against the ledger value of the CODE,
        and it was not part of the seal battery. It is now, and its output ships
        as verification/circuit_value_check.txt. */}
    <resistor name="R_WDPETPD" resistance="1k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C11702"] }} connections={{ pin1: "net.WD_PET", pin2: "net.GND" }} />

    {/* ================= BLOCK 3 — PRESS one-shot + RELAY MATRIX ============ */}
    {/* CD74HC221 NON-retriggerable one-shot (ADR-0011 §6, v1.2: replaces the RETRIGGERABLE
        SN74LVC1G123 — TI DS: retriggerable up to 100% duty, so the <=500ms PRESS bound was
        not hard; review F5). Section 1: 1A_N=GND, 1B=PRESS_REQ (Schmitt, rising), 1R_N=
        OS_CLR_N = DOOR_OK·STOP_REQ_N (door abort OR STOP preemption clears the pulse),
        1Q=PRESS_TIMED, 1Q_N=PRESS_TIMED_N (latch-freeze). tw = K*Rx*Cx, K~0.7-0.75 at 3V3:
        510k*1uF -> 357-383ms typ, <=436ms worst < 500ms HARD (DETAIL_DESIGN #2).
        Section 2 unused: 2A_N=N3V3, 2B=GND, 2R_N=GND (held reset), 2CXRX 10k to VCC. */}
    <chip name="U_ONESHOT" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C133954"] }}
      pinLabels={{ pin1: "A1_N", pin2: "B1", pin3: "R1_N", pin4: "Q1_N", pin5: "Q2", pin6: "CX2", pin7: "CXRX2", pin8: "GND", pin9: "A2_N", pin10: "B2", pin11: "R2_N", pin12: "Q2_N", pin13: "Q1", pin14: "CX1", pin15: "CXRX1", pin16: "VCC" }}
      connections={{
        pin1: "net.GND", pin2: "net.PRESS_REQ", pin3: "net.OS_CLR_N", pin4: "net.PRESS_TIMED_N",
        pin7: "net.OS2_RC", pin8: "net.GND", pin9: "net.N3V3", pin10: "net.GND",
        pin11: "net.GND", pin13: "net.PRESS_TIMED", pin14: "net.OS_C", pin15: "net.OS_RC", pin16: "net.N3V3",
      }} />
    {/* LCSC code PINNED (task#21, 2026-07-25). tscircuit's own auto-selection returned
        C25782 / C163467 / C2906936 for this "510k" — and JLC's catalog says ALL THREE are
        390kOhm (C25782 = 0402WGF3903TCE, "390kΩ 50V 62.5mW ±1%"). The BOM would have ordered
        390k for a part labelled 510k, taking the PRESS one-shot from t_w = 0.7*510k*1uF =
        357ms down to 273ms — BELOW the brief's 300-500ms window, i.e. a press too short for
        the OEM controller to register. Caught by bom_source_check leg C (VALUE-MISMATCH) and
        confirmed against the live catalog. C137961 = RC0402FR-07510KL, 510kOhm ±1% 0402,
        stock 554618 on 2026-07-25. This is why the timing resistor gets an explicit code and
        does not inherit whatever the auto-picker likes. */}
    <resistor name="R_OS" resistance="510k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C137961"] }} connections={{ pin1: "net.OS_RC", pin2: "net.N3V3" }} />
    <capacitor name="C_OS" capacitance="1uF" footprint="0603" connections={{ pin1: "net.OS_C", pin2: "net.OS_RC" }} />
    <resistor name="R_OS2" resistance="10k" footprint="0402" connections={{ pin1: "net.OS2_RC", pin2: "net.N3V3" }} />
    <capacitor name="C_OSV" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    {/* STOP_REQ_N inverter (1G00 as inverter) + one-shot clear gate: OS_CLR_N = DOOR_OK · STOP_REQ_N */}
    <chip name="U_STOPINV" footprint="sot23_5" supplierPartNumbers={{ jlcpcb: ["C8185"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "GND", pin4: "Y", pin5: "VCC" }}
      connections={{ pin1: "net.STOP_REQ", pin2: "net.STOP_REQ", pin3: "net.GND", pin4: "net.STOP_REQ_N", pin5: "net.N3V3" }} />
    <chip name="U_OSCLR" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.DOOR_OK", pin2: "net.GND", pin3: "net.STOP_REQ_N", pin4: "net.OS_CLR_N", pin5: "net.N3V3", pin6: "net.N3V3" }} />
    <capacitor name="C_STOPINV" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_OSCLR" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- SN74HC595 shift register (Pi-driven DATA/CLOCK/LATCH) ---- */}
    {/* 595 pins: 1QB 2QC 3QD 4QE 5QF 6QG 7QH 8GND 9QH_S 10SRCLR_N 11SRCLK 12RCLK 13OE_N 14SER 15QA 16VCC */}
    {/* v1.2 (ADR-0011 §5): U_SR2 DELETED — its only used bit was STOP_REQ, which moved to a
        DIRECT Pi GPIO (phys 37): a registered STOP behind the frozen KEY_LATCH_G (below) or a
        tri-stated 595 could not preempt a press. RCLK is now KEY_LATCH_G = KEY_LATCH ·
        PRESS_TIMED_N (U_LATCHG): selector addresses cannot change while PRESS is closed.
        Decoder enables leave the 595 as *_RAW and pass through STOP_REQ_N gates (ADR-0011 §5b). */}
    <chip name="U_SR1" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C10092"] }}
      pinLabels={{ pin1: "QB", pin2: "QC", pin3: "QD", pin4: "QE", pin5: "QF", pin6: "QG", pin7: "QH", pin8: "GND", pin9: "QH_S", pin10: "SRCLR_N", pin11: "SRCLK", pin12: "RCLK", pin13: "OE_N", pin14: "SER", pin15: "QA", pin16: "VCC" }}
      connections={{
        pin15: "net.DECU_A", pin1: "net.DECU_B", pin2: "net.DECU_C", pin3: "net.DECU_G1_RAW",
        pin4: "net.DECD_A", pin5: "net.DECD_B", pin6: "net.DECD_G1_RAW", pin7: "net.PRESS_REQ",
        pin10: "net.KEY_RESET_N", pin11: "net.KEY_CLOCK", pin12: "net.KEY_LATCH_G",
        pin13: "net.SR_OE_N", pin14: "net.KEY_DATA", pin8: "net.GND", pin16: "net.N3V3",
      }} />
    <capacitor name="C_SR1" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    {/* KEY_LATCH freeze gate: RCLK = KEY_LATCH · PRESS_TIMED_N (ADR-0011 §6) */}
    <chip name="U_LATCHG" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.KEY_LATCH", pin2: "net.GND", pin3: "net.PRESS_TIMED_N", pin4: "net.KEY_LATCH_G", pin5: "net.N3V3", pin6: "net.N3V3" }} />
    <capacitor name="C_LATCHG" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- 2x SN74HC238 ACTIVE-HIGH 3-to-8 decoders (one-hot BY CONSTRUCTION, ADR-0002) ---- */}
    {/* 238 pins: 1A 2B 3C 4/G2A 5/G2B 6G1 7Y7 8GND 9Y6 10Y5 11Y4 12Y3 13Y2 14Y1 15Y0 16VCC. Selected out = HIGH. */}
    {/* U-select: Y0..Y5 = U1..U6 -> ULN inputs. G1 enable from 595; /G2A=/G2B=GND; Y6/Y7 unused (NC). */}
    <chip name="U_DECU" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C5620"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "C", pin4: "G2A_N", pin5: "G2B_N", pin6: "G1", pin7: "Y7", pin8: "GND", pin9: "Y6", pin10: "Y5", pin11: "Y4", pin12: "Y3", pin13: "Y2", pin14: "Y1", pin15: "Y0", pin16: "VCC" }}
      connections={{
        pin1: "net.DECU_A", pin2: "net.DECU_B", pin3: "net.DECU_C", pin4: "net.GND", pin5: "net.GND", pin6: "net.DECU_G1",
        pin15: "net.SEL_U1", pin14: "net.SEL_U2", pin13: "net.SEL_U3", pin12: "net.SEL_U4", pin11: "net.SEL_U5", pin10: "net.SEL_U6",
        pin8: "net.GND", pin16: "net.N3V3",
      }} />
    {/* D-select: Y0..Y3 = D1..D4. Only A,B used (4 outputs) -> C(3) tied GND; Y4..Y7 unused (NC). */}
    <chip name="U_DECD" footprint="soic16" supplierPartNumbers={{ jlcpcb: ["C5620"] }}
      pinLabels={{ pin1: "A", pin2: "B", pin3: "C", pin4: "G2A_N", pin5: "G2B_N", pin6: "G1", pin7: "Y7", pin8: "GND", pin9: "Y6", pin10: "Y5", pin11: "Y4", pin12: "Y3", pin13: "Y2", pin14: "Y1", pin15: "Y0", pin16: "VCC" }}
      connections={{
        pin1: "net.DECD_A", pin2: "net.DECD_B", pin3: "net.GND", pin4: "net.GND", pin5: "net.GND", pin6: "net.DECD_G1",
        pin15: "net.SEL_D1", pin14: "net.SEL_D2", pin13: "net.SEL_D3", pin12: "net.SEL_D4",
        pin8: "net.GND", pin16: "net.N3V3",
      }} />
    <capacitor name="C_DECU" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_DECD" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    {/* '238 E3-enable PULL-DOWNS (pin review Q4, 2026-07-23): DECU_G1/DECD_G1 are driven ONLY by
        595 outputs; when SR_OE_N tri-states the 595s (watchdog/interlock action, or Pi boot) the
        active-HIGH E3 enables would FLOAT — formally out-of-spec for Nexperia 74HC238D inputs and
        a phantom-select hazard (a floated-high E3 enables a random decoder output into the ULN).
        A pulled-LOW E3 disables ALL eight outputs regardless of the (also floating) address pins,
        so these two 100k close the hazard. (The coil rail ALSO dies in that state — COIL_EN is fed
        from KEY_RELAY_ALLOWED via the J_MODE DPDT AUTO throw + R_COILENPD pull-down, so the
        reviewer's rail-live premise does not hold — but floating CMOS inputs stay out-of-spec:
        belt AND braces.)
        v1.2 (ADR-0011 §5b): the pull-downs sit on the *_RAW nets (the ones that float when
        SR_OE_N tri-states the 595); the decoder G1 enables are now driven by STOP-preemption
        gates: DECx_G1 = DECx_G1_RAW · STOP_REQ_N — STOP force-disables BOTH decoders. */}
    <resistor name="R_DECUPD" resistance="100k" footprint="0402" connections={{ pin1: "net.DECU_G1_RAW", pin2: "net.GND" }} />
    <resistor name="R_DECDPD" resistance="100k" footprint="0402" connections={{ pin1: "net.DECD_G1_RAW", pin2: "net.GND" }} />
    <chip name="U_DECUEN" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.DECU_G1_RAW", pin2: "net.GND", pin3: "net.STOP_REQ_N", pin4: "net.DECU_G1", pin5: "net.N3V3", pin6: "net.N3V3" }} />
    <chip name="U_DECDEN" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.DECD_G1_RAW", pin2: "net.GND", pin3: "net.STOP_REQ_N", pin4: "net.DECD_G1", pin5: "net.N3V3", pin6: "net.N3V3" }} />
    <capacitor name="C_DECUEN" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_DECDEN" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

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
        pin3: "net.PRESS_TIMED", pin16: "net.COIL_PRESS_N", pin4: "net.GND",
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
    {/* K_STOP: dedicated preempt path KP_U6 -> RSTOP -> KP_D1 (brief §4 U6-K_STOP-RSTOP-D1).
        v1.2 (ADR-0011 §4): coil moved OFF the fault-gated 5V_KEY_RELAY rail onto the
        always-available 5V_STOP rail (5V_PROTECTED via R_STOPRAIL) with a DEDICATED driver
        Q_STOPDRV + flyback D_KSTOP — a WD/TEMP/latch fault that kills the key rail can no
        longer disable the STOP relay (review F3c: "the safety chain cannot stop a running
        cook"). Deliberately NOT gated by KEY_RELAY_ALLOWED/ESTOP/DOOR/MODE — see the ADR. */}
    <chip name="K_STOP" footprint="dip4" supplierPartNumbers={{ jlcpcb: ["DIP05-1A72-12L"] }}
      pinLabels={{ pin1: "COIL_A", pin2: "COIL_B", pin3: "CONTACT_B", pin4: "CONTACT_A" }}
      connections={{ pin1: "net.N5V_STOP", pin2: "net.COIL_STOP_N", pin3: "net.RSTOP_MID", pin4: "net.KP_U6" }} />
    <resistor name="R_STOPRAIL" resistance="0" footprint="0603" connections={{ pin1: "net.N5V_PROTECTED", pin2: "net.N5V_STOP" }} />
    <capacitor name="C_STOPR" capacitance="10uF" footprint="0805" connections={{ pin1: "net.N5V_STOP", pin2: "net.GND" }} />
    <chip name="Q_STOPDRV" footprint="sot23" supplierPartNumbers={{ jlcpcb: ["C8545"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.STOP_REQ", pin2: "net.GND", pin3: "net.COIL_STOP_N" }} />
    <diode name="D_KSTOP" footprint="sma" supplierPartNumbers={{ jlcpcb: ["C8678"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.N5V_STOP", pin2: "net.COIL_STOP_N" }} />
    <resistor name="R_STOPPD" resistance="100k" footprint="0402" connections={{ pin1: "net.STOP_REQ", pin2: "net.GND" }} />
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
    {/* v1.3 (layout lens P1-3 + topology lens P1-3): LM393 -> LMV393IDR (C7984) and VCC
        moves from 5V_PROTECTED to 3V3_ANALOG. The LM393's input common-mode ceiling is
        VCC-2V = 2.93V at VCC 4.93V, but a COLD or OPEN thermistor puts TH_CAM at 3.0-3.3V
        — i.e. the old part was operated OUTSIDE its specified range exactly in the
        broken-sensor case, so its output there was unspecified. The LMV393 is
        NOT rail-to-rail on the input — an earlier draft of this comment claimed it was, and
        the datasheet denies it (SLCS136V sec.6.3 p.9: PNP inputs "allowing LMV33x to accurately
        function from ground to VCC-Vbe (about 700mV)"; sec.7.2.2.1 p.11: "VICR can range from 0V
        to VCC-0.7V"). At VCC 3.3V the ceiling is 2.50-2.60V. WHAT THE SWAP ACTUALLY BUYS, and it
        is the load-bearing property: sec.7.2.2.1 SPECIFIES the output state for all four
        out-of-common-mode cases, where the LM393's SLCS005AH specifies NOTHING above VCC-2V — so
        a broken-sensor node that used to produce an UNDEFINED safety response now produces a
        DOCUMENTED one. (Only from Rev V: sec.14 p.14 records that this exact text was corrected.)
        Separately, the divider rescale below now keeps EVERY reading, open included, inside
        VICR — so the case table is a backstop here, not the mechanism. Same SOIC-8 pinout, same
        open-drain output, so TEMP_OK stays a wired-AND, now single-rail 3V3.
        ABS MAX VCC IS 5.5V (was 36V on the LM393) — this part must never be re-fitted to a 5V
        rail without re-checking; VID abs max also collapses to +-5.5V. */}
    <chip name="U_COMP" footprint="soic8" supplierPartNumbers={{ jlcpcb: ["C7984"] }}
      pinLabels={{ pin1: "1OUT", pin2: "1IN_N", pin3: "1IN_P", pin4: "GND", pin5: "2IN_P", pin6: "2IN_N", pin7: "2OUT", pin8: "VCC" }}
      connections={{
        pin1: "net.TEMP_OK", pin2: "net.TCAM_THRESH", pin3: "net.TH_CAM_A", pin4: "net.GND",
        pin5: "net.TH_CAM_B", pin6: "net.TCAM_THRESH", pin7: "net.TEMP_OK", pin8: "net.N3V3_ANALOG",
      }} />
    {/* ============ v1.3: OPEN-THERMISTOR DETECT, IN HARDWARE ============================
        The finding: an open, broken or UNPLUGGED camera thermistor pulls its sense node to
        3.3V — far above the 0.4231V over-temp threshold — so TEMP_OK stayed HIGH = "temp
        fine". One unplugged JST-GH cable silently removed the only firmware-independent
        over-temperature protection, from BOTH the fault-latch SET term and the contactor
        gate.
        WHY A BIAS RESISTOR CANNOT FIX IT (proved before choosing this): in a 2-terminal
        divider an open sensor IS an infinitely cold sensor. With the NTC at the bottom an
        open pulls the node to the top rail; with the NTC at the top an open pulls it to
        the bottom rail; adding any bleed resistor only moves where "infinitely cold"
        lands, and cold and open stay on the SAME side of any single threshold. The
        information is not in the node — so the fix is a SECOND threshold, i.e. a window.
        THIS IS THAT WINDOW. U_COMP2 trips when TH_CAM rises above the open-detect
        threshold, which no connected thermistor can reach. *** THAT THRESHOLD IS 2.0370V,
        NOT the 3.107V this paragraph originally gave — 3.107V was the FIRST CUT and it was
        ABOVE the LMV393 common-mode ceiling, i.e. inert. See the RESCALE block immediately
        below, which is the authority for every number in this window. ***
        Open/unplugged/broken-wire => TEMP_OK LOW => fault latch SET and
        contactor permission removed, exactly like an over-temperature. A SHORTED sensor
        already tripped the over-temp half, so both cable failure modes are now covered.
        TEMP_OK becomes a 4-way wired-AND: hot(A) . hot(B) . open(A) . open(B). */}
    <chip name="U_COMP2" footprint="soic8" supplierPartNumbers={{ jlcpcb: ["C7984"] }}
      pinLabels={{ pin1: "1OUT", pin2: "1IN_N", pin3: "1IN_P", pin4: "GND", pin5: "2IN_P", pin6: "2IN_N", pin7: "2OUT", pin8: "VCC" }}
      connections={{
        pin1: "net.TEMP_OK", pin2: "net.TH_CAM_A", pin3: "net.TCAM_OPEN", pin4: "net.GND",
        pin5: "net.TCAM_OPEN", pin6: "net.TH_CAM_B", pin7: "net.TEMP_OK", pin8: "net.N3V3_ANALOG",
      }} />
    <capacitor name="C_COMP2" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.GND" }} />
    {/* ---- THE RESCALE THAT MAKES THE OPEN-DETECT REAL (v1.3, second pass) --------------
        The first cut put TCAM_OPEN at 3.107V. That is ABOVE the LMV393's common-mode ceiling
        (2.50-2.60V at VCC 3.3V), so the part never compared against it: the effective trip was
        the ceiling itself, about +1.6C to -1.6C of head temperature, and R_OPENT/R_OPENB were
        inert. Direction was still fail-safe, but a cold kitchen would nuisance-trip the
        interlock and the designed cold-vs-open discrimination did not exist.
        FIX: bound the sense node with a 22k bleed (R_CLMPA/R_CLMPB below) so the OPEN-CIRCUIT
        reading is 3.3*22/32 = 2.2687V instead of the 3.3V rail — inside VICR with 217mV of
        worst-case margin — and drop the threshold to 3.3*100/162 = 2.0370V.
        MEASURED (KNTC0603-10KF3950, B25/85=3987, all resistors +-1%, VIO +-9mV):
          open-circuit node      2.2687 V  (worst-high 2.2829 vs the 2.500 ceiling = +217mV)
          threshold              2.0370 V  (worst separation to open = 193mV, vs VIO 9mV)
          nuisance-trip below   -10.4 C typ / -7.4 C worst corner   (was +1.6 C)
          over-temp trip         72.80 C   with the EXISTING 68k/10k, still inside the
                                           brief's 70-75C window, so R_TH1/R_TH2 do not move
        Every reading the comparators ever see is now inside the specified common-mode range,
        open included — the out-of-CM case table is a backstop, not the mechanism.
        Inputs are DELIBERATELY swapped vs U_COMP: IN- = TH_CAM, IN+ = threshold, so the output
        goes LOW when the node rises ABOVE the threshold. */}
    {/* ---- THESE FOUR CODES ARE PINNED, AND R_OPENT IS WHY (P0, 2026-07-26) ------------
        The divider above was authored by VALUE and left to tscircuit's auto-picker to code.
        For "62k" the picker offered THREE candidates and ALL THREE ARE 6.2k:
            C25915   0402WGF6201TCE    6.2kΩ   <- the one the exporter took
            C137946  RC0402FR-076K2L   6.2kΩ
            C2909371 FRC0402F6201TS    6.2kΩ
        It appears to read "62k" as RKM "6k2". The board therefore ORDERED 6.2k for the
        open-thermistor detect threshold, one decade low, and the consequence is the exact
        defect the comment block above documents FIXING: TCAM_OPEN back at 3.3*100/106.2 =
        3.1073V, above the LMV393's 2.500V common-mode ceiling, so the comparator never
        compares against it and an OPEN, BROKEN OR UNPLUGGED HEAD READS FINE instead of
        OVER-TEMP. Verified twice before changing anything, and not by decoding a part
        number: JLC selectSmtComponentList C25915 -> describe "6.2kΩ"; LCSC product page
        C25915 -> MPN 0402WGF6201TCE, resistance "6.2kΩ".
        CORRECT PART C37825 (0402WGF6202TCE, 62kΩ +-1%, same UNI-ROYAL family, stock 127526).
        This is the R_OS precedent (see its pin above and the ledger note): the picker offered
        three codes for "510k" and all three were 390k. A value-authored passive on a SAFETY
        divider must carry its code explicitly. R_OPENB and R_CLMPA/B happened to be right,
        by candidate ORDERING rather than by anything checked, so they are pinned too — every
        code below is catalog-verified and in skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml
        so leg C of bom_source_check can re-verify all four offline, forever. */}
    <resistor name="R_OPENT" resistance="62k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C37825"] }} connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.TCAM_OPEN" }} />
    <resistor name="R_OPENB" resistance="100k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C25741"] }} connections={{ pin1: "net.TCAM_OPEN", pin2: "net.GND" }} />
    {/* The bleed. These are what keep an OPEN thermistor inside the comparator's specified
        input range; without them the open reading is the bare 3.3V rail and neither comparator
        is operating to spec. They also bound the ADC input, so the host's conversion for
        CH0/CH3 differs from the other six thermistor channels — see DETAIL_DESIGN. */}
    {/* Codes PINNED with R_OPENT/R_OPENB above (P0, 2026-07-26): these two ARE the bleed that
        keeps an open head inside the comparator's common-mode range, so they belong to the same
        safety divider and must not be left to the auto-picker that got "62k" wrong.
        C25768 = 0402WGF2202TCE = 22kΩ, catalog-verified 2026-07-26 (base library, stock 1.5M). */}
    <resistor name="R_CLMPA" resistance="22k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C25768"] }} connections={{ pin1: "net.TH_CAM_A", pin2: "net.GND" }} />
    <resistor name="R_CLMPB" resistance="22k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C25768"] }} connections={{ pin1: "net.TH_CAM_B", pin2: "net.GND" }} />
    {/* v1.2 threshold redesign (ADR-0011 §1, review F2): the <=v1.1 10k/10k divider put
        TCAM_THRESH at 1.65V = the 10k-pullup/10k-NTC node at 25C — the 70-75C hard stop did
        not exist. New: 68k/10k -> 0.4231V -> 74.9C with the committed KNTC0603/10KF3950
        (B25/85=3987K). SOLDER-SELECT field like RKEY (1206 pads, hand-swappable): R_TH2 =
        8.2k->81C · 10k->75C (default) · 12k->69C · 15k->63C (math: DETAIL_DESIGN #1).
        TP_TCTH below is the bring-up measurement point (60/65/70/75C fixture gate). */}
    <resistor name="R_TH1" resistance="68k" footprint="1206" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.TCAM_THRESH" }} />
    <resistor name="R_TH2" resistance="10k" footprint="1206" connections={{ pin1: "net.TCAM_THRESH", pin2: "net.GND" }} />
    <resistor name="R_HYS1" resistance="1M" footprint="0402" connections={{ pin1: "net.TEMP_OK", pin2: "net.TH_CAM_A" }} />
    <resistor name="R_HYS2" resistance="1M" footprint="0402" connections={{ pin1: "net.TEMP_OK", pin2: "net.TH_CAM_B" }} />
    {/* P1-1 FIX (red-team lens A, 2026-07-26): pin2 was net.N3V3 — THE DIGITAL RAIL —
        while BOTH comparators whose verdict this net carries are powered from
        3V3_ANALOG, whose ONLY source is the ferrite FB1 (every other node on that net
        is a load). A HEALTH REPORT MUST BE POWERED BY THE THING WHOSE HEALTH IT
        REPORTS. With FB1 open the four open-drain outputs cannot pull down and a still
        live 3V3 drove TEMP_OK through this 10k against R_HYS1||R_HYS2 (500k) to
        3.3*500/510 = 3.235V = HIGH = "temperature fine" = PERMISSIVE. One open passive
        removed the over-temp AND the open-thermistor interlocks at once, reported
        healthy, and killed the MCP3208's VDD/VREF in the same instant so the host
        cross-check the ORDER_README makes MANDATORY died with it. Every backstop
        failing together, silently, on one component.
        On 3V3_ANALOG the same failure gives 0.000V = LOW = RESTRICTIVE, because the
        TH_CAM nodes sit at 0V through R_CLMPA/B and R_HYS pulls TEMP_OK down with them.
        CONTEXT WORTH KEEPING: TEMP_OK was the ONLY permission in the safety chain
        actively pulled toward permissive. The other twelve are pulled restrictive, and
        REARM_N is correctly pulled up. */}
    <resistor name="R_TEMPOK" resistance="10k" footprint="0402" connections={{ pin1: "net.TEMP_OK", pin2: "net.N3V3_ANALOG" }} />
    {/* v1.3: follows U_COMP.8 from 5V_PROTECTED to 3V3_ANALOG — it was still authored on the
        old rail and so no longer bypassed the part it exists for. This 100nF is a SAFETY
        component on this board, not hygiene: SLCS136V sec.8 p.12 notes supply variation
        "cause temporary fluctuations in the comparator's input common mode range", and the
        open-detect threshold is referenced to the same rail. */}
    <capacitor name="C_COMP" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3_ANALOG", pin2: "net.GND" }} />

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

    {/* ---- discrete safety inputs: DOOR, E-STOP (2x NC), MODE (DPDT) ----
        HEADER CORRECTED 2026-07-26: this said "DOOR (NC reed+EOL)", which BRIEF.md:92
        commissions but this board does NOT implement. As built the door is a Form-A
        (NO) contact from J_DOOR.1 (3V3) to J_DOOR.2/4 (DOOR_RAW) with R_DOORPD holding
        low, read by a DIGITAL Schmitt input (U_SCHM.11). That closes v1.1's
        fail-permissive defect — a broken wire now reads OPEN — but it is NOT
        SUPERVISED: a short between J_DOOR.1 and .2 reads "door closed" undetectably.
        Full EOL supervision needs three distinguishable levels, i.e. an ANALOG read,
        and all 8 MCP3208 channels and all 4 comparator channels are already used.
        Cost is in 01_docs/STATUS-cooksense.md; deferred pending a decision. */}
    {/* SM05B-GHS 5-pin used for each (the brief's 4-pin locking role; 5th pin = GND/shield). */}
    <chip name="J_DOOR" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3", pin2: "net.DOOR_RAW", pin3: "net.GND", pin4: "net.DOOR_RAW", pin5: "net.GND" }} />
    {/* v1.3 P0-CLASS FIX (layout+topology lens P1-2, 2026-07-25): this was R_DOORPU, a
        10k pull-UP to 3V3 — the ONLY external safety input on the board pulled to the
        PERMISSIVE rail. A broken or unplugged door cable read DOOR-CLOSED, so the door
        abort silently never happened; and with the pull-up-consistent harness a normal
        magnet-CLOSES reed made DOOR_OK=0 whenever the door was SHUT, holding OS_CLR_N low
        so K_PRESS could never fire at all. Now a pull-DOWN to GND, identical to
        R_ESTOPPD/R_MODEPD: OPEN CIRCUIT => DOOR_RAW low => DOOR_OK=0 => door treated as
        OPEN => press aborted. HARNESS (now the same convention as J_ESTOP): 3V3 on
        J_DOOR.1 -> Form-A reed (magnet CLOSES it with the door shut) -> J_DOOR.2. This
        moves the door interlock from a load-bearing documentation dependency to a
        hardware property. */}
    <resistor name="R_DOORPD" resistance="10k" footprint="0402" connections={{ pin1: "net.DOOR_RAW", pin2: "net.GND" }} />
    <diode name="D_DOOR" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }} connections={{ pin1: "net.DOOR_RAW", pin2: "net.GND" }} />
    {/* E-stop: contact A monitored (ESTOP_RAW, high=OK); contact B (pins3-4) in series with the ISOLATED */}
    {/* contactor loop (opto C -> ESTOP_B_IN, ESTOP_B_OUT -> J_CONTACTOR): E-stop physically breaks it. */}
    {/* v1.3 P0-2 FIX (layout lens): the OPTO-ISOLATED contactor loop is OFF this connector.
        Until v1.2 J_ESTOP carried ESTOP_RAW (SELV) on pin 2 and CONTACTOR_C (isolated
        secondary) on pin 3 — ADJACENT pads on a 1.25mm-pitch JST-GH, a 0.650mm pad gap,
        in ONE field harness. That reduced the LTV-817S's 5kVrms barrier to 0.65mm at the
        connector and made a single contaminated or damaged harness a common-cause failure
        across the isolation boundary. Pins 3/4 are now GND, so this housing is
        SELV-ONLY and every pin on it belongs to one domain. The loop moves to its own
        J_ESTOPLOOP terminal block below. */}
    <chip name="J_ESTOP" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3", pin2: "net.ESTOP_RAW", pin3: "net.GND", pin4: "net.GND", pin5: "net.GND" }} />
    {/* The E-stop's second (dry, isolated) pole lands on J_ISOLOOP, the ONE isolated
        terminal block (declared with U_OPTO below, since every pole on it is on the far
        side of that barrier). See the J_ISOLOOP comment there for why v1.3 merged what
        v1.3 first split into two blocks. */}
    <resistor name="R_ESTOPPD" resistance="10k" footprint="0402" connections={{ pin1: "net.ESTOP_RAW", pin2: "net.GND" }} />
    <diode name="D_ESTOP" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }} connections={{ pin1: "net.ESTOP_RAW", pin2: "net.GND" }} />
    {/* Mode DPDT: pole A (pins1-2) = physical coil-EN gate (MANUAL cuts the rail); pole B (pins3-4) = MODE_RAW logic */}
    {/* J_MODE RE-PINNED to the sibling GH convention (pin review Q, 2026-07-23): 3V3 on pin 1,
        GND on pin 5, signals in the middle — matching J_DOOR/J_ESTOP. Old pinout put 3V3 on pin 3
        ADJACENT to COIL_EN on pin 2: a cross-plugged sibling harness could short COIL_EN to 3V3
        through the external switch and energize the coil rail BYPASSING the AND-chain. New pinout:
        pole B (mode sense) = pins 1-2 (3V3 -> MODE_RAW); pole A (coil gate) = pins 3-4
        (KEY_RELAY_ALLOWED -> COIL_EN). COIL_EN's neighbours are now the AND-chain output (3) and
        GND (5): any cross-plug bridge either applies the intended gating or holds the rail OFF.
        (A J_DOOR-style harness bridging 2-3/4-5 gives MODE_RAW<->KEY_RELAY_ALLOWED contention -
        benign - and COIL_EN->GND = safe-off.) */}
    <chip name="J_MODE" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3", pin2: "net.MODE_RAW", pin3: "net.KEY_RELAY_ALLOWED", pin4: "net.COIL_EN", pin5: "net.GND" }} />
    <resistor name="R_MODEPD" resistance="10k" footprint="0402" connections={{ pin1: "net.MODE_RAW", pin2: "net.GND" }} />

    {/* ---- optically-isolated external-contactor request (LTV-817S), <=30V/50mA dry (brief §3) ---- */}
    {/* v1.2 HARDWARE contactor gate (ADR-0011 §3, review F3b): <=v1.1 drove the LED straight
        from CONTACTOR_REQ — only the E-stop contact-B loop could interrupt the contactor.
        Now CONTACTOR_DRV = CONTACTOR_REQ · WD_OK · ESTOP_OK · TEMP_OK · FAULT_LATCH_CLEAR:
        a watchdog/thermal/E-stop/latched fault removes contactor permission IN HARDWARE. */}
    <chip name="U_CAND1" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.WD_OK", pin2: "net.GND", pin3: "net.ESTOP_OK", pin4: "net.CTR_SAFE", pin5: "net.N3V3", pin6: "net.TEMP_OK" }} />
    <chip name="U_CAND2" footprint="sot23_6" supplierPartNumbers={{ jlcpcb: ["C22046"] }}
      pinLabels={{ pin1: "A", pin2: "GND", pin3: "B", pin4: "Y", pin5: "VCC", pin6: "C" }}
      connections={{ pin1: "net.CTR_SAFE", pin2: "net.GND", pin3: "net.FAULT_LATCH_CLEAR", pin4: "net.CONTACTOR_DRV", pin5: "net.N3V3", pin6: "net.CONTACTOR_REQ" }} />
    <capacitor name="C_CAND1" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_CAND2" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <chip name="U_OPTO" footprint="dip4" supplierPartNumbers={{ jlcpcb: ["C125121"] }}
      pinLabels={{ pin1: "ANODE", pin2: "CATHODE", pin3: "EMITTER", pin4: "COLLECTOR" }}
      connections={{ pin1: "net.OPTO_LED_A", pin2: "net.GND", pin3: "net.CONTACTOR_E", pin4: "net.CONTACTOR_C" }} />
    <resistor name="R_OPTOLED" resistance="330" footprint="0603" connections={{ pin1: "net.CONTACTOR_DRV", pin2: "net.OPTO_LED_A" }} />
    {/* ---- J_ISOLOOP: THE ONE ISOLATED TERMINAL BLOCK (v1.3 P0-A fix) --------------
        v1.3 first split the isolated loop OFF J_ESTOP (correct — see the J_ESTOP note
        above) onto its OWN 2-pole block J_ESTOPLOOP, sitting beside the existing 2-pole
        J_CONTACTOR. That put FIVE connectors on the east edge and there was not room:
        MEASURED available 47.453mm (H4's courtyard to the south edge) against 47.750mm
        of connector courtyard PLUS the moat the ISO_CONTACTOR rule needs. The anchors
        were written anyway and J_ESTOPLOOP landed INSIDE J_DOOR — the opto-isolated 30V
        loop shorted to 3V3/GND/DOOR_RAW at 1.300 x 0.600mm of overlapping pad copper.
        THE FIX IS ONE 4-POLE BLOCK, not a tighter squeeze. Both connectors already
        carried ONLY isolated-domain nets, so merging them is isolation-NEUTRAL and
        strictly better to defend: one isolated body with ONE 2.0mm moat and ONE pour
        keepout, instead of two adjacent bodies each needing their own. It also puts the
        whole isolated loop on one terminal block for the installer.
        FIELD WIRING (unchanged in function):
          1 CONTACTOR_C    -> E-stop pole B in     (opto collector)
          2 CONTACTOR_LOOP <- E-stop pole B out
          3 CONTACTOR_LOOP -> contactor circuit    (pins 2/3 are ONE net on the board:
          4 CONTACTOR_E    <- contactor circuit     the link the old CONTACTOR_LOOP net
                                                    made between the two blocks)
        Pins 2 and 3 are DELIBERATELY two screws on one net rather than one screw with
        two wires landed in it: on a safety interlock a single loosening screw must not
        be able to drop both the E-stop return AND the contactor feed.
        3.5mm pitch holds the connector-level creepage on the isolated side at 3.5mm
        nominal (it was 0.650mm when this loop shared J_ESTOP's 1.25mm-pitch GH housing).
        THT + `service: standard` = self-supplied/hand-soldered; see assembly.yaml. */}
    {/* AUTHORED BY MPN, NOT BY LCSC CODE, and P-FACT is why (2026-07-26). The code
        C42400616 has stockCount 0 on every KF350 4-pole line and JLC has no CAD for it,
        so naming it on a JLC ASSEMBLY BOM asks the fab to source a part it does not
        carry — the same shape as the v1.0/v1.1 defect where 13 hand-solder parts sat on
        the CPL. The other thirteen not_in_catalog refs (the twelve Standex reeds and
        J_TC) are already authored this way and emit a BLANK LCSC; J_ISOLOOP was the odd
        one out INSIDE its own assembly.yaml category. The MPN still resolves the FPID
        via 02_parts/KF350-3.5-4P (load_part_overrides keys on dir name and mpn as well
        as on LCSC codes), so the footprint binding is unchanged. The code itself is not
        lost: it stays in the part.yaml `sourcing.lcsc` and in the ORDER_README buy-list,
        which is where a self-supplied part belongs. */}
    <chip name="J_ISOLOOP" footprint="pinrow4" supplierPartNumbers={{ jlcpcb: ["KF350-3.5-4P"] }}
      pinLabels={{ pin1: "LOOP_OUT", pin2: "LOOP_RET", pin3: "CTR_A", pin4: "CTR_B" }}
      connections={{ pin1: "net.CONTACTOR_C", pin2: "net.CONTACTOR_LOOP",
                     pin3: "net.CONTACTOR_LOOP", pin4: "net.CONTACTOR_E" }} />

    {/* ================= BLOCK 6 — MCP23017 EXPANDER (ADR-0003) ============ */}
    {/* Slow signals: 4 rail enables, contactor req, re-arm, BOARD_ID straps; readbacks on GPB0-7. */}
    {/* flag 3: pin12 = SCL (I2C), NOT SCK; pins 11 & 14 = NC (do NOT wire). */}
    <chip name="U_EXP" footprint="ssop28" supplierPartNumbers={{ jlcpcb: ["C506653"] }}
      pinLabels={{ pin1: "GPB0", pin2: "GPB1", pin3: "GPB2", pin4: "GPB3", pin5: "GPB4", pin6: "GPB5", pin7: "GPB6", pin8: "GPB7", pin9: "VDD", pin10: "VSS", pin11: "NC", pin12: "SCL", pin13: "SDA", pin14: "NC", pin15: "A0", pin16: "A1", pin17: "A2", pin18: "RESET_N", pin19: "INTB", pin20: "INTA", pin21: "GPA0", pin22: "GPA1", pin23: "GPA2", pin24: "GPA3", pin25: "GPA4", pin26: "GPA5", pin27: "GPA6", pin28: "GPA7" }}
      connections={{
        pin1: "net.EFUSE_FLT_N", pin2: "net.MODE_AUTO_HW", pin3: "net.ESTOP_OK", pin4: "net.DOOR_OK",
        pin5: "net.TEMP_OK", pin6: "net.FAULT", pin7: "net.TC_FAULT_N", pin8: "net.WD_OK",
        pin9: "net.N3V3", pin10: "net.GND", pin12: "net.I2C_SCL", pin13: "net.I2C_SDA",
        pin15: "net.GND", pin16: "net.GND", pin17: "net.GND", pin18: "net.EXP_RST_N",
        pin19: "net.EXP_INTB", pin20: "net.INT_ALERT",
        pin21: "net.RAIL_EN_A", pin22: "net.RAIL_EN_B", pin23: "net.RAIL_EN_RHA", pin24: "net.RAIL_EN_RHE",
        pin25: "net.CONTACTOR_REQ", pin26: "net.REARM_N", pin27: "net.BOARD_ID0", pin28: "net.BOARD_ID1",
      }} />
    <capacitor name="C_EXP" capacitance="100nF" footprint="0402" connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <resistor name="R_EXPRST" resistance="10k" footprint="0402" connections={{ pin1: "net.EXP_RST_N", pin2: "net.N3V3" }} />
    {/* v1.2 DETERMINISTIC PULLS (ADR-0011 §7): hold the SAFE state while the Pi/expander are
        un-driven (boot/reset — MCP23017 pins reset to INPUTS). Pull-DOWN every authorization/
        enable; pull-UP on REARM_N (active-low re-arm: floating must NOT clear the fault latch). */}
    <resistor name="R_RAENAPD" resistance="100k" footprint="0402" connections={{ pin1: "net.RAIL_EN_A", pin2: "net.GND" }} />
    <resistor name="R_RAENBPD" resistance="100k" footprint="0402" connections={{ pin1: "net.RAIL_EN_B", pin2: "net.GND" }} />
    <resistor name="R_RAENRHAPD" resistance="100k" footprint="0402" connections={{ pin1: "net.RAIL_EN_RHA", pin2: "net.GND" }} />
    <resistor name="R_RAENRHEPD" resistance="100k" footprint="0402" connections={{ pin1: "net.RAIL_EN_RHE", pin2: "net.GND" }} />
    <resistor name="R_CTRREQPD" resistance="100k" footprint="0402" connections={{ pin1: "net.CONTACTOR_REQ", pin2: "net.GND" }} />
    <resistor name="R_REARMPU" resistance="100k" footprint="0402" connections={{ pin1: "net.REARM_N", pin2: "net.N3V3" }} />
    <resistor name="R_HOSTAUTHPD" resistance="100k" footprint="0402" connections={{ pin1: "net.HOST_AUTH", pin2: "net.GND" }} />
    <resistor name="R_MCUENPD" resistance="100k" footprint="0402" connections={{ pin1: "net.MCU_RELAY_ENABLE", pin2: "net.GND" }} />
    <resistor name="R_KRSTPD" resistance="100k" footprint="0402" connections={{ pin1: "net.KEY_RESET_N", pin2: "net.GND" }} />
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
    {/* v1.2 (ADR-0010): the RH pods JOIN the camera buses (address-disjoint 0x33/0x44 —
        brief §3.10's own pairing, now on REAL native pairs): ambient SHT45 -> bus A (I2C2),
        exhaust SHT45 -> bus B (I2C3). Nets SDA_RHA/SCL_RHA/SDA_RHE/SCL_RHE deleted. */}
    <chip name="J_RH_AMBIENT" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3_SW_RHA", pin2: "net.GND", pin3: "net.SDA_A", pin4: "net.SCL_A", pin5: "net.SHIELD_DRAIN" }} />
    <chip name="J_RH_EXHAUST" footprint="pinrow5" supplierPartNumbers={{ jlcpcb: ["C189896"] }}
      connections={{ pin1: "net.N3V3_SW_RHE", pin2: "net.GND", pin3: "net.SDA_B", pin4: "net.SCL_B", pin5: "net.SHIELD_DRAIN" }} />
    {/* ONE 2.2k pullup pair per bus, powered from the CAMERA's switched rail (ADR-0004 N1:
        pullups die with the rail). The <=v1.1 RH-rail pullup pairs are DELETED — parallel
        pullups from two switched rails would back-power the off rail's device. Phantom-power
        residual (documented, ADR-0010): stuck-bus recovery must cycle BOTH rails of a bus. */}
    <resistor name="R_SDAA" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SDA_A", pin2: "net.N3V3_SW_A" }} />
    <resistor name="R_SCLA" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SCL_A", pin2: "net.N3V3_SW_A" }} />
    <resistor name="R_SDAB" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SDA_B", pin2: "net.N3V3_SW_B" }} />
    <resistor name="R_SCLB" resistance="2.2k" footprint="0402" connections={{ pin1: "net.SCL_B", pin2: "net.N3V3_SW_B" }} />
    {/* shield drain: RC/0R option to GND at a single point (brief: NOT hard-bonded to signal ground) */}
    <resistor name="R_SHIELD" resistance="0" footprint="0603" connections={{ pin1: "net.SHIELD_DRAIN", pin2: "net.GND" }} />

    {/* ================= Raspberry Pi 5 40-pin header (signals only; power NC) ==== */}
    {/* GND = 6,9,14,20,25,30,34,39. Power (1,2,4,17) + HAT-ID (27,28) = NC (brief §3, no backfeed). */}
    {/* v1.2 NATIVE-I2C REPAIR (ADR-0010, review F1 — VERIFIED against the RP1 datasheet
        function-select table + kernel i2c*-pi5 overlays, 2026-07-24):
          I2C1 GPIO2/3  = phys 3/5   -> MCP23017 (unchanged, was already correct)
          I2C2 GPIO4/5  = phys 7/29  -> bus A: MLX90640 A (0x33) + ambient SHT45 (0x44)
          I2C3 GPIO14/15= phys 8/10  -> bus B: MLX90640 B (0x33) + exhaust SHT45 (0x44)
        <=v1.1 had cam A on 7/8 (GPIO4+GPIO14 = two buses' SDA lines), cam B on 10/12,
        SHT45s on 18/35 + 36/37 — GPIO16/18/19/24/26 have NO I2C alt function at all.
        KEY_DATA re-homed phys29(GPIO5)->phys36(GPIO16); STOP_REQ = DIRECT GPIO26/phys37
        (ADR-0011 §5). Freed: phys 12/18/35 = NC. The maintained map + dtoverlay snippet is
        01_docs/pin_map.md; E-INV pins every one of these assignments. */}
    <chip name="J_PI" footprint="pinrow40" supplierPartNumbers={{ jlcpcb: ["C35165"] }}
      connections={{
        pin3: "net.I2C_SDA", pin5: "net.I2C_SCL", pin6: "net.GND",
        pin7: "net.SDA_A", pin8: "net.SDA_B", pin9: "net.GND", pin10: "net.SCL_B",
        pin11: "net.WD_PET", pin13: "net.INT_ALERT", pin14: "net.GND",
        pin15: "net.HOST_AUTH", pin16: "net.MCU_RELAY_ENABLE",
        pin19: "net.SPI_MOSI", pin20: "net.GND", pin21: "net.SPI_MISO", pin22: "net.TC_DRDY_N",
        pin23: "net.SPI_SCLK", pin24: "net.ADC_CS_N", pin25: "net.GND", pin26: "net.TC_CS_N",
        pin29: "net.SCL_A", pin30: "net.GND", pin31: "net.KEY_CLOCK", pin32: "net.KEY_LATCH",
        pin33: "net.KEY_RESET_N", pin34: "net.GND", pin36: "net.KEY_DATA",
        pin37: "net.STOP_REQ", pin38: "net.LC_DAT_PI", pin39: "net.GND", pin40: "net.LC_CLK_PI",
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
    <testpoint name="TP_PGOOD" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.EFUSE_FLT_N" }} />
    <testpoint name="TP_TCDRDY" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TC_DRDY_N" }} />
    <testpoint name="TP_TCFAULT" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TC_FAULT_N" }} />
    <testpoint name="TP_USEL" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.U_SEL_BUS" }} />
    <testpoint name="TP_DSEL" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.D_SEL_BUS" }} />
    <testpoint name="TP_RKEY" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.RKEY_MID" }} />
    <testpoint name="TP_TCTH" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TCAM_THRESH" }} />
    <testpoint name="TP_ENCL" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TH_ENCLOSURE" }} />
    <testpoint name="TP_SPARE" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.TH_SPARE" }} />

    {/* ================= mounting holes (M2.5 Pi-HAT) — non-electrical ====== */}
    <hole name="H1" diameter="2.75mm" pcbX={-40} pcbY={30} />
    <hole name="H2" diameter="2.75mm" pcbX={40} pcbY={30} />
    <hole name="H3" diameter="2.75mm" pcbX={-40} pcbY={-30} />
    <hole name="H4" diameter="2.75mm" pcbX={40} pcbY={-30} />
  </board>
)

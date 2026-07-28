// crow-recorder-central-v2 — 8-channel Cat5e audio recorder central board.
//
// Authored in tscircuit (ADR-0002). Compiled by our converter
// (circuit_json_to_kicad_sch.py) into the authoritative KiCad schematic bridge.
// Every pin is bound to an EXPLICIT net (connections={{ pin: "net.NAME" }}) so
// the netlist matches KiCad verbatim — parity by construction (canon S2).
//
// Net-name convention (ADR-0001 canon_net): leading-digit rails are authored
// N-guarded (N5V/N3V3/N0V9/N1V8/N3V3A); the converter strips the guard N.
// All other names pass verbatim.
//
// NO-CONNECT mechanism (empirically verified 2026-07-23, see verification/notes.md):
// a pad simply LEFT OUT of `connections` resolves to net=None, and the converter
// emits a KiCad `no_connect` flag at that pin — ERC 0 errors. Unused XU316 GPIO,
// pin55(NC), MIPI lanes, USB_ID, PCM GPIO/XO, clock-buffer 3Y, RJ45 LED pins,
// USB-ESD spare channel, and the barrel-jack switch leg are all handled this way.
// Unused pins are NEVER shorted together onto one net.

const N = (s: string) => `net.${s}`

// build a chip `connections` object from a { padNumber: netName } map.
// pads not present in the map are left unbound -> no_connect (sanctioned float).
const conn = (m: Record<number, string>) =>
  Object.fromEntries(Object.entries(m).map(([k, v]) => [`pin${k}`, N(v)]))

// throwaway pad geometry for a <footprint> child: N numeric pads on a
// non-overlapping grid. Only the portHints (pad names) + count are load-bearing
// at the schematic gate; the real land pattern comes from the 02_parts FPID.
const grid = (names: (string | number)[]) =>
  names.map((nm, i) => (
    <smtpad
      key={`p${nm}`}
      portHints={[String(nm)]}
      pcbX={`${(i % 16) * 0.8 - 6}mm`}
      pcbY={`${Math.floor(i / 16) * 0.8 - 4}mm`}
      width="0.4mm"
      height="0.4mm"
      shape="rect"
    />
  ))

const fp = (names: (string | number)[]) => <footprint>{grid(names)}</footprint>

// ---- LCSC codes (from 02_parts/*/part.yaml sourcing.lcsc) ----
const LCSC = {
  XU316: "C6938291",
  PCM1865: "C181312",
  NC7NZ34: "C232798",
  W25Q16: "C82317",
  SHT40: "C2909890",
  AP61102: "C5224055",
  TLV70018: "C79924",   // TLV70018DDCR SOT-23-5 1.8V/200mA — ADR-0006 documented drop-in; TCR2LF18 C150173 stock=0 at v1.0 staging
  XC6227: "C6035451",
  BARREL: "C381116",
  USB4105: "C3020560",
  RJ45: "C9900035627",
  SMAJ: "C87074",
  TPD4E: "C90627",
  TPD2E: "C1972959",
  AO3401A: "C15127",
  AO3400A: "C20917",
  XTAL24: "C2762192",  // NX3225SA-24MHZ-EXS00A-CS08583 3225-4P 24MHz CL9pF ±10ppm — FA-238 MD50Y (C7190380, CL9pF) stock=0 at v1.0 staging
  FUSE: "C136345",
  PTC: "C2649901",
  L_2R2: "C882626",   // 1277AS-H-2R2M=P2 1210 2.2uH 2.1A/2.6Asat 84mR (L1, 3V3 buck)
  L_1R0: "C237284",   // 1277AS-H-1R0M=P2 1210 1uH 3.1A/3.7Asat 45mR (L2, 0V9 buck)
  BEAD600: "C3716677", // BLM21SP601SN1D 0805 600R@100MHz 2.3A 60mR (all 4 beads)
  R402K: "C25785",    // 0402WGF4023TCE 402k 1% (R_fb2b: 400k not stocked; -0.17% on 0V9)
} as const

// XU316-1024-TQ128 — full 128 pins + EP(129). Only the pins below are bound;
// every other pad (unused X0D../X1D.. GPIO, pin55 NC, MIPI lanes 25/26/28/29/31/32,
// USB_ID 58) is intentionally omitted -> no_connect.
const XU316_PINS: Record<number, string> = {
  // QSPI boot (hardcoded pins)
  2: "QSPI_CS", 127: "QSPI_D0", 128: "QSPI_D1", 1: "QSPI_D2", 3: "QSPI_D3", 4: "QSPI_CLK",
  // 0V9 core (VDD)
  5: "N0V9", 11: "N0V9", 14: "N0V9", 18: "N0V9", 39: "N0V9", 45: "N0V9", 50: "N0V9",
  54: "N0V9", 68: "N0V9", 85: "N0V9", 95: "N0V9", 104: "N0V9", 105: "N0V9", 106: "N0V9", 113: "N0V9",
  // 3V3 IO banks (VDDIOL 10,17 / VDDIOR 72,89 / VDDIOT 109,121)
  10: "N3V3", 17: "N3V3", 72: "N3V3", 89: "N3V3", 109: "N3V3", 121: "N3V3",
  // 1V8 bottom bank (VDDIOB18)
  35: "N1V8", 56: "N1V8",
  // grounds + MIPI supplies tied to GND (MIPI unused)
  30: "GND", 129: "GND", 42: "GND", 24: "GND", 27: "GND",
  // PLL analog + USB analog supplies (LC-filtered)
  41: "PLL_AVDD", 61: "USB_VDD33", 62: "USB_VDD18",
  // IO-mode straps LV_L_N 40 / LV_T_N 43 / LV_R_N 52: DELIBERATELY FLOATING
  // (PR2-P0-1 fix, 2026-07-24). These are Input PU IOB pins — the bottom IO
  // bank is ALWAYS 1.8V and AMR V(Vin) = VDDIO+0.5 = 2.3V (XU316-1024-TQ128
  // ds v2.0.0 §4.4/§4.8/§15.1), so the previous hard 3V3 tie was ~1V over
  // abs-max. §4.8: "tied high or left floating" selects 3.3V mode for
  // VDDIOL/R/T — float IS the documented select (internal pull-up). Do NOT
  // tie these to 3V3; if a driven level is ever needed, use the 1V8 rail.
  // crystal
  33: "XOUT", 34: "XIN",
  // JTAG (1.8V bank) + reset
  36: "TDI", 37: "TDO", 44: "TMS", 51: "TCK", 38: "RST_N",
  // USB
  59: "USB_DN", 60: "USB_DP",
  // audio/control GPIO (IOT bank, 3V3)
  107: "MCLK", 108: "BCLK_SRC", 119: "LRCK_SRC", 120: "ADC_DIN",
  125: "SDA", 126: "SCL", 122: "BEEP_GATE", 23: "VBUS_SENSE",
}

// PCM1865 #1 (U2, channels 1-4, I2C 0x4A)
const PCM_U2: Record<number, string> = {
  1: "ADC1M", 3: "ADC1P", 2: "ADC2M", 4: "ADC2P",
  28: "ADC3M", 30: "ADC3P", 27: "ADC4M", 29: "ADC4P",
  5: "MICBIAS2", 6: "VREF2", 7: "GND", 8: "N3V3A",
  10: "GND", 11: "LDO2", 12: "GND", 13: "N3V3", 14: "N3V3",
  15: "MCLK_A1", 16: "LRCK", 17: "BCLK", 18: "ADC_DIN",
  23: "SDA", 24: "SCL", 25: "GND", 26: "GND",
  // 9(XO),19-22(GPIO) -> no_connect
}

// PCM1865 #2 (U3, channels 5-8, I2C 0x4B)
const PCM_U3: Record<number, string> = {
  1: "ADC5M", 3: "ADC5P", 2: "ADC6M", 4: "ADC6P",
  28: "ADC7M", 30: "ADC7P", 27: "ADC8M", 29: "ADC8P",
  5: "MICBIAS3", 6: "VREF3", 7: "GND", 8: "N3V3A",
  10: "GND", 11: "LDO3", 12: "GND", 13: "N3V3", 14: "N3V3",
  15: "MCLK_A2", 16: "LRCK", 17: "BCLK", 18: "ADC_DIN",
  23: "SDA", 24: "SCL", 25: "N3V3", 26: "GND",
}

// USB4105 USB-C — tsx pins 1..17 (see parity_padmap.txt for the A*/B*/SH map).
const USB_C: Record<number, string> = {
  1: "GND", 2: "VBUS", 3: "CC1", 4: "USB_DP", 5: "USB_DN",
  7: "VBUS", 8: "GND", 9: "GND", 10: "VBUS", 11: "CC2",
  12: "USB_DP", 13: "USB_DN", 15: "VBUS", 16: "GND", 17: "GND",
  // 6(A8/SBU1), 14(B8/SBU2) -> no_connect
}

export default () => (
  <board width="260mm" height="180mm" name="crow_recorder_central_v2">
    {/* ===================== POWER INPUT + PROTECTION (ADR-0001) ===================== */}
    <chip name="J1" supplierPartNumbers={{ jlcpcb: [LCSC.BARREL] }} footprint={fp([1, 2, 3])}
      connections={conn({ 1: "JACK_IN", 2: "GND" })} /* 3=SW -> NC */ />
    <chip name="F_IN" supplierPartNumbers={{ jlcpcb: [LCSC.FUSE] }} footprint={fp([1, 2])}
      connections={conn({ 1: "JACK_IN", 2: "VIN_RAW" })} />
    <chip name="D1" supplierPartNumbers={{ jlcpcb: [LCSC.SMAJ] }} footprint={fp([1, 2])}
      connections={conn({ 1: "VIN_RAW", 2: "GND" })} /* K=VIN_RAW, A=GND */ />
    <chip name="Q1" footprint="sot23" supplierPartNumbers={{ jlcpcb: [LCSC.AO3401A] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }} /* names the netlist pinfunction so the E-INV series_chain (Q1:[D,S]) resolves */
      connections={conn({ 1: "GATE_RPP", 2: "N5V", 3: "VIN_RAW" })} /* P-FET RPP: G,S,D */ />
    <resistor name="RG1" resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C60490"] }} connections={{ pin1: N("GATE_RPP"), pin2: N("GND") }} />
    <capacitor name="C_5V1" capacitance="22uF" footprint="0805" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="C_5V2" capacitance="100nF" footprint="0402" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="C_5V3" capacitance="100nF" footprint="0402" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="C_VINR" capacitance="100nF" footprint="0402" connections={{ pin1: N("VIN_RAW"), pin2: N("GND") }} />

    {/* ===================== BUCK 3V3 (U7 AP61102) ===================== */}
    <chip name="U7" supplierPartNumbers={{ jlcpcb: [LCSC.AP61102] }} footprint={fp([1, 2, 3, 4, 5, 6])}
      connections={conn({ 1: "FB1", 2: "GND", 3: "N5V", 4: "SW1", 5: "N5V", 6: "PG_3V3" })} />
    <inductor name="L1" inductance="2.2uH" footprint="1210" supplierPartNumbers={{ jlcpcb: [LCSC.L_2R2] }} connections={{ pin1: N("SW1"), pin2: N("N3V3") }} />
    <capacitor name="Cin_U7" capacitance="10uF" footprint="0805" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="Cinh_U7" capacitance="100nF" footprint="0402" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="Cout_U7" capacitance="22uF" footprint="0805" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="Couth_U7" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <resistor name="R_fb1a" resistance="200k" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("FB1") }} />
    <resistor name="R_fb1b" resistance="44.2k" footprint="0402" connections={{ pin1: N("FB1"), pin2: N("GND") }} />
    <resistor name="R_pg" resistance="100k" footprint="0402" connections={{ pin1: N("PG_3V3"), pin2: N("N3V3") }} />

    {/* ===================== BUCK 0V9 CORE (U8 AP61102) ===================== */}
    <chip name="U8" supplierPartNumbers={{ jlcpcb: [LCSC.AP61102] }} footprint={fp([1, 2, 3, 4, 5, 6])}
      connections={conn({ 1: "FB2", 2: "GND", 3: "N5V", 4: "SW2", 5: "PG_3V3" })} /* 6=NC */ />
    <inductor name="L2" inductance="1uH" footprint="1210" supplierPartNumbers={{ jlcpcb: [LCSC.L_1R0] }} connections={{ pin1: N("SW2"), pin2: N("N0V9") }} />
    <capacitor name="Cin_U8" capacitance="10uF" footprint="0805" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="Cinh_U8" capacitance="100nF" footprint="0402" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="Cout_U8" capacitance="22uF" footprint="0805" connections={{ pin1: N("N0V9"), pin2: N("GND") }} />
    <capacitor name="Couth_U8" capacitance="100nF" footprint="0402" connections={{ pin1: N("N0V9"), pin2: N("GND") }} />
    <resistor name="R_fb2a" resistance="200k" footprint="0402" connections={{ pin1: N("N0V9"), pin2: N("FB2") }} />
    <resistor name="R_fb2b" resistance="402k" footprint="0402" supplierPartNumbers={{ jlcpcb: [LCSC.R402K] }} connections={{ pin1: N("FB2"), pin2: N("GND") }} />

    {/* ===================== LDO 1V8 (U9 TCR2LF18) ===================== */}
    <chip name="U9" footprint="sot23_5" supplierPartNumbers={{ jlcpcb: [LCSC.TLV70018] }}
      connections={conn({ 1: "N3V3", 2: "GND", 3: "N3V3", 5: "N1V8" })} /* 4=NC */ />
    <capacitor name="Cin_U9" capacitance="1uF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="Cout_U9" capacitance="1uF" footprint="0402" connections={{ pin1: N("N1V8"), pin2: N("GND") }} />

    {/* ===================== LDO 3V3A QUIET ANALOG (U10 XC6227) ===================== */}
    <chip name="U10" supplierPartNumbers={{ jlcpcb: [LCSC.XC6227] }} footprint={fp([1, 2, 3, 4, 5])}
      connections={conn({ 1: "N5V", 2: "GND", 4: "N5V", 5: "N3V3A" })} /* 3=NC */ />
    <capacitor name="Cin_U10" capacitance="1uF" footprint="0402" connections={{ pin1: N("N5V"), pin2: N("GND") }} />
    <capacitor name="Cout_U10" capacitance="2.2uF" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C72203"] }} connections={{ pin1: N("N3V3A"), pin2: N("GND") }} />
    <capacitor name="Couth_U10" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3A"), pin2: N("GND") }} />

    {/* ===================== BEEP 5V BUS + LOW-SIDE SWITCH ===================== */}
    <inductor name="FB_BEEP" inductance="600" footprint="0805" supplierPartNumbers={{ jlcpcb: [LCSC.BEAD600] }} connections={{ pin1: N("N5V"), pin2: N("PLUS5V_BEEP") }} /* 600R@100MHz ferrite bead */ />
    <capacitor name="C_BEEP" capacitance="47uF" footprint="1206" connections={{ pin1: N("PLUS5V_BEEP"), pin2: N("GND") }} />
    <chip name="Q2" footprint="sot23" supplierPartNumbers={{ jlcpcb: [LCSC.AO3400A] }}
      connections={conn({ 1: "BEEP_G", 2: "GND", 3: "BEEP_RETURN" })} /* N-FET: G,S,D */ />
    <resistor name="R_bg1" resistance="1k" footprint="0402" connections={{ pin1: N("BEEP_GATE"), pin2: N("BEEP_G") }} />
    <capacitor name="C_bg" capacitance="4.7nF" footprint="0402" connections={{ pin1: N("BEEP_G"), pin2: N("GND") }} />
    <resistor name="R_bg2" resistance="100k" footprint="0402" connections={{ pin1: N("BEEP_G"), pin2: N("GND") }} />

    {/* ===================== XU316 (U1) ===================== */}
    <chip name="U1" supplierPartNumbers={{ jlcpcb: [LCSC.XU316] }}
      footprint={fp(Array.from({ length: 129 }, (_, i) => i + 1))}
      connections={conn(XU316_PINS)} />
    {/* --- XU316 decoupling ---
        Core VDD (0V9): 13x 100nF — XU316-1024-TQ128 ds XM-014532-PC-2.0.0 §14
        "Integration" p.29 requires "at least 12" 100nF low-inductance MLCCs
        close to the chip on VDD. v1.1 shipped 8 (2nd external review F1,
        2026-07-24); C_c9..C_c13 added for v1.2, anchored at the under-served
        core-VDD pins (floorplan.yaml). */}
    {Array.from({ length: 13 }, (_, i) => (
      <capacitor key={`Cc${i + 1}`} name={`C_c${i + 1}`} capacitance="100nF" footprint="0402"
        connections={{ pin1: N("N0V9"), pin2: N("GND") }} />
    ))}
    {Array.from({ length: 6 }, (_, i) => (
      <capacitor key={`Cd${i + 1}`} name={`C_d${i + 1}`} capacitance="100nF" footprint="0402"
        connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    ))}
    {Array.from({ length: 2 }, (_, i) => (
      <capacitor key={`Ce${i + 1}`} name={`C_e${i + 1}`} capacitance="100nF" footprint="0402"
        connections={{ pin1: N("N1V8"), pin2: N("GND") }} />
    ))}
    <capacitor name="C_b0v9" capacitance="10uF" footprint="0805" connections={{ pin1: N("N0V9"), pin2: N("GND") }} />
    <capacitor name="C_b3v3" capacitance="10uF" footprint="0805" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_b1v8" capacitance="10uF" footprint="0805" connections={{ pin1: N("N1V8"), pin2: N("GND") }} />
    {/* PLL LC filter */}
    <inductor name="L_pll" inductance="600" footprint="0805" supplierPartNumbers={{ jlcpcb: [LCSC.BEAD600] }} connections={{ pin1: N("N0V9"), pin2: N("PLL_AVDD") }} /* 600R ferrite */ />
    <capacitor name="C_pll1" capacitance="1uF" footprint="0402" connections={{ pin1: N("PLL_AVDD"), pin2: N("GND") }} />
    <capacitor name="C_pll2" capacitance="100nF" footprint="0402" connections={{ pin1: N("PLL_AVDD"), pin2: N("GND") }} />
    {/* USB analog supply filters */}
    <inductor name="FB_u33" inductance="600" footprint="0805" supplierPartNumbers={{ jlcpcb: [LCSC.BEAD600] }} connections={{ pin1: N("N3V3"), pin2: N("USB_VDD33") }} /* ferrite */ />
    <inductor name="FB_u18" inductance="600" footprint="0805" supplierPartNumbers={{ jlcpcb: [LCSC.BEAD600] }} connections={{ pin1: N("N1V8"), pin2: N("USB_VDD18") }} /* ferrite */ />
    <capacitor name="C_u33a" capacitance="1uF" footprint="0402" connections={{ pin1: N("USB_VDD33"), pin2: N("GND") }} />
    <capacitor name="C_u33b" capacitance="100nF" footprint="0402" connections={{ pin1: N("USB_VDD33"), pin2: N("GND") }} />
    <capacitor name="C_u18a" capacitance="1uF" footprint="0402" connections={{ pin1: N("USB_VDD18"), pin2: N("GND") }} />
    <capacitor name="C_u18b" capacitance="100nF" footprint="0402" connections={{ pin1: N("USB_VDD18"), pin2: N("GND") }} />
    {/* reset */}
    <resistor name="R_rst" resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C60490"] }} connections={{ pin1: N("RST_N"), pin2: N("N1V8") }} />
    <capacitor name="C_rst" capacitance="100nF" footprint="0402" connections={{ pin1: N("RST_N"), pin2: N("GND") }} />

    {/* ===================== CRYSTAL (Y1 FA-238, 24 MHz) ===================== */}
    <chip name="Y1" supplierPartNumbers={{ jlcpcb: [LCSC.XTAL24] }} footprint={fp([1, 2, 3, 4])}
      connections={conn({ 1: "XIN", 2: "GND", 3: "XO_XTAL", 4: "GND" })} />
    <resistor name="Rf" resistance="1M" footprint="0402" connections={{ pin1: N("XIN"), pin2: N("XOUT") }} />
    <resistor name="Rd" resistance="680" footprint="0402" connections={{ pin1: N("XOUT"), pin2: N("XO_XTAL") }} />
    <capacitor name="CL1" capacitance="12pF" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C1547"] }} connections={{ pin1: N("XIN"), pin2: N("GND") }} /> {/* CL 9pF crystal: 2*(9-3pF stray)=12pF, fresh-lens P1 2026-07-23 */}
    <capacitor name="CL2" capacitance="12pF" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C1547"] }} connections={{ pin1: N("XO_XTAL"), pin2: N("GND") }} />

    {/* ===================== JTAG/DEBUG HEADER (J_DBG, 1x08, 1.8V) ===================== */}
    <chip name="J_DBG" footprint="pinrow8"
      connections={conn({ 1: "N1V8", 2: "GND", 3: "TCK", 4: "TMS", 5: "TDI", 6: "TDO", 7: "RST_N", 8: "GND" })} />

    {/* ===================== QSPI FLASH (U5 W25Q16) ===================== */}
    <chip name="U5" footprint="soic8" supplierPartNumbers={{ jlcpcb: [LCSC.W25Q16] }}
      connections={conn({ 1: "QSPI_CS", 2: "QSPI_D1", 3: "QSPI_D2", 4: "GND", 5: "QSPI_D0", 6: "QSPI_CLK", 7: "QSPI_D3", 8: "N3V3" })} />
    <resistor name="R_cs" resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C60490"] }} connections={{ pin1: N("QSPI_CS"), pin2: N("N3V3") }} />
    <capacitor name="C_flash" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />

    {/* ===================== SHT40 TEMP/HUMIDITY (U6) ===================== */}
    <chip name="U6" supplierPartNumbers={{ jlcpcb: [LCSC.SHT40] }} footprint={fp([1, 2, 3, 4])}
      connections={conn({ 1: "SDA", 2: "SCL", 3: "N3V3", 4: "GND" })} /* 5=EP -> NC (no paste) */ />
    <capacitor name="C_sht" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />

    {/* ===================== I2C PULL-UPS ===================== */}
    <resistor name="R_sda" resistance="4.7k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C105871"] }} connections={{ pin1: N("SDA"), pin2: N("N3V3") }} />
    <resistor name="R_scl" resistance="4.7k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C105871"] }} connections={{ pin1: N("SCL"), pin2: N("N3V3") }} />

    {/* ===================== CLOCK BUFFER (U4 NC7NZ34, 1->2 MCLK fanout) ===================== */}
    <chip name="U4" supplierPartNumbers={{ jlcpcb: [LCSC.NC7NZ34] }} footprint={fp([1, 2, 3, 4, 5, 6, 7, 8])}
      connections={conn({ 1: "MCLK", 3: "MCLK", 6: "MCLK", 7: "MCLK_B1", 5: "MCLK_B2", 4: "GND", 8: "N3V3" })} /* 2=3Y -> NC */ />
    <capacitor name="C_u4" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <resistor name="R_mck1" resistance="33" footprint="0402" connections={{ pin1: N("MCLK_B1"), pin2: N("MCLK_A1") }} />
    <resistor name="R_mck2" resistance="33" footprint="0402" connections={{ pin1: N("MCLK_B2"), pin2: N("MCLK_A2") }} />
    <resistor name="R_bck" resistance="33" footprint="0402" connections={{ pin1: N("BCLK_SRC"), pin2: N("BCLK") }} />
    <resistor name="R_lrck" resistance="33" footprint="0402" connections={{ pin1: N("LRCK_SRC"), pin2: N("LRCK") }} />

    {/* ===================== ADC U2 (PCM1865, channels 1-4) ===================== */}
    <chip name="U2" supplierPartNumbers={{ jlcpcb: [LCSC.PCM1865] }}
      footprint={fp(Array.from({ length: 30 }, (_, i) => i + 1))} connections={conn(PCM_U2)} />
    <capacitor name="C_avdd2a" capacitance="10uF" footprint="0805" connections={{ pin1: N("N3V3A"), pin2: N("GND") }} />
    <capacitor name="C_avdd2b" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3A"), pin2: N("GND") }} />
    <capacitor name="C_dvdd2" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_iovdd2" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_ldo2" capacitance="1uF" footprint="0402" connections={{ pin1: N("LDO2"), pin2: N("GND") }} />
    <capacitor name="C_vref2a" capacitance="10uF" footprint="0805" connections={{ pin1: N("VREF2"), pin2: N("GND") }} />
    <capacitor name="C_vref2b" capacitance="100nF" footprint="0402" connections={{ pin1: N("VREF2"), pin2: N("GND") }} />
    <capacitor name="C_micb2" capacitance="1uF" footprint="0402" connections={{ pin1: N("MICBIAS2"), pin2: N("GND") }} />

    {/* ===================== ADC U3 (PCM1865, channels 5-8) ===================== */}
    <chip name="U3" supplierPartNumbers={{ jlcpcb: [LCSC.PCM1865] }}
      footprint={fp(Array.from({ length: 30 }, (_, i) => i + 1))} connections={conn(PCM_U3)} />
    <capacitor name="C_avdd3a" capacitance="10uF" footprint="0805" connections={{ pin1: N("N3V3A"), pin2: N("GND") }} />
    <capacitor name="C_avdd3b" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3A"), pin2: N("GND") }} />
    <capacitor name="C_dvdd3" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_iovdd3" capacitance="100nF" footprint="0402" connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_ldo3" capacitance="1uF" footprint="0402" connections={{ pin1: N("LDO3"), pin2: N("GND") }} />
    <capacitor name="C_vref3a" capacitance="10uF" footprint="0805" connections={{ pin1: N("VREF3"), pin2: N("GND") }} />
    <capacitor name="C_vref3b" capacitance="100nF" footprint="0402" connections={{ pin1: N("VREF3"), pin2: N("GND") }} />
    <capacitor name="C_micb3" capacitance="1uF" footprint="0402" connections={{ pin1: N("MICBIAS3"), pin2: N("GND") }} />

    {/* ===================== USB-C (J2) + USB ESD (D_USB) ===================== */}
    <chip name="J2" supplierPartNumbers={{ jlcpcb: [LCSC.USB4105] }}
      footprint={fp(Array.from({ length: 17 }, (_, i) => i + 1))} connections={conn(USB_C)} />
    <resistor name="R_cc1" resistance="5.1k" footprint="0402" connections={{ pin1: N("CC1"), pin2: N("GND") }} />
    <resistor name="R_cc2" resistance="5.1k" footprint="0402" connections={{ pin1: N("CC2"), pin2: N("GND") }} />
    <chip name="D_USB" supplierPartNumbers={{ jlcpcb: [LCSC.TPD4E] }}
      footprint={fp(Array.from({ length: 10 }, (_, i) => i + 1))}
      connections={conn({ 1: "USB_DP", 2: "USB_DN", 3: "GND", 8: "GND" })} /* 4,5,6,7,9,10 -> NC */ />
    {/* v1.7: the resolver's first choice for 220k/0402 is C25767 (UNI-ROYAL
        0402WGF2203TCE), which read stockCount 0 on 2026-07-27 — it measured 16
        at the v1.6 seal and was graded OK, because nothing distinguishes
        "clears 5x need" from "clears it by eleven units". Pinned to C138030
        (YAGEO RC0402FR-07220KL, stock 736,704, same 0402 land, catalog
        `describe` string CHARACTER-IDENTICAL, compared as strings): same YAGEO
        RC0402FR series as this board's existing C60490 / C105871 swaps. Top leg
        of the VBUS->VBUS_SENSE divider; no copper, footprint or netlist change. */}
    <resistor name="R_vb1" resistance="220k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C138030"] }} connections={{ pin1: N("VBUS"), pin2: N("VBUS_SENSE") }} />
    <resistor name="R_vb2" resistance="330k" footprint="0402" connections={{ pin1: N("VBUS_SENSE"), pin2: N("GND") }} />
    <capacitor name="C_vb" capacitance="2.2uF" footprint="0805" connections={{ pin1: N("VBUS"), pin2: N("GND") }} />
    <resistor name="R_vbld" resistance="47k" footprint="0402" connections={{ pin1: N("VBUS"), pin2: N("GND") }} />

    {/* ===================== 8x PORT CHANNELS (ports 1..8 -> ADC ch1..8) ===================== */}
    {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => {
      const j = p + 2 // RJ45 refdes J3..J10
      const AP = `AUDIO${p}P`, AM = `AUDIO${p}M`
      const MP = `MID${p}P`, MM = `MID${p}M`
      const DP = `ADC${p}P`, DM = `ADC${p}M`
      const PV = `P5VA_${p}`
      return (
        <group key={`port${p}`} name={`port${p}`}>
          <chip name={`J${j}`} supplierPartNumbers={{ jlcpcb: [LCSC.RJ45] }}
            footprint={fp([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])}
            connections={conn({
              1: AP, 2: AM, 3: "PLUS5V_BEEP", 4: PV, 5: "GND",
              6: "BEEP_RETURN", 7: PV, 8: "GND", 13: "GND", // 13=SH; 9-12 LEDs -> NC
            })} />
          <chip name={`F${p}`} supplierPartNumbers={{ jlcpcb: [LCSC.PTC] }} footprint={fp([1, 2])}
            connections={conn({ 1: "N5V", 2: PV })} />
          <chip name={`Dp${p}`} supplierPartNumbers={{ jlcpcb: [LCSC.TPD2E] }} footprint={fp([1, 2, 3, 4, 5])}
            connections={conn({ 3: AP, 5: AM, 4: "GND" })} /* 1,2 = NC */ />
          <capacitor name={`Cc${p}P`} capacitance="2.2uF" footprint="0805" connections={{ pin1: N(AP), pin2: N(MP) }} />
          <resistor name={`Rs${p}P`} resistance="100" footprint="0402" connections={{ pin1: N(MP), pin2: N(DP) }} />
          <capacitor name={`Cc${p}M`} capacitance="2.2uF" footprint="0805" connections={{ pin1: N(AM), pin2: N(MM) }} />
          <resistor name={`Rs${p}M`} resistance="100" footprint="0402" connections={{ pin1: N(MM), pin2: N(DM) }} />
          <capacitor name={`Cd${p}`} capacitance="1nF" footprint="0402" connections={{ pin1: N(DP), pin2: N(DM) }} />
        </group>
      )
    })}

    {/* ===================== TEST POINTS ===================== */}
    {[
      ["TP1", "N5V"], ["TP2", "N3V3"], ["TP3", "N0V9"], ["TP4", "N1V8"],
      ["TP5", "N3V3A"], ["TP6", "GND"], ["TP7", "MCLK"], ["TP8", "BCLK"],
      ["TP9", "LRCK"], ["TP10", "ADC_DIN"], ["TP11", "BEEP_RETURN"], ["TP12", "PLUS5V_BEEP"],
    ].map(([tp, net]) => (
      // pinLabels forces the single pad "1" to materialize a source_port — a bare
      // <chip footprint="testpoint_pad"> pad carries no schematic pin (converter drops it).
      <chip key={tp} name={tp} footprint="testpoint_pad" pinLabels={{ pin1: "1" }}
        connections={{ pin1: N(net) }} />
    ))}

    {/* ===================== INJECTION HEADER (JP_INJ, inter-ADC skew) ===================== */}
    <chip name="JP_INJ" footprint="pinrow3"
      connections={conn({ 1: "INJ", 2: "GND", 3: "INJ" })} />
    <resistor name="R_inj1" resistance="1k" footprint="0402" connections={{ pin1: N("INJ"), pin2: N("ADC1P") }} />
    <resistor name="R_inj2" resistance="1k" footprint="0402" connections={{ pin1: N("INJ"), pin2: N("ADC5P") }} />
  </board>
)

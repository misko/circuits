// lipo3s-usb-hub — 3S LiPo (XT60) -> 3x USB-A (2.5A) + 1x USB-C (6A) power/charge board.
// Authored FROM SCRATCH in tscircuit/TSX (ADR-0002 Act 2), driven through the
// one-command tscircuit-native backend (tsx_to_board.sh: TSX -> converter -> KiCad
// backend -> DRC 0/0/0). This is THE fab front-end, not a second-opinion render.
//
// DESIGN (independent, see 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md + decisions/):
//   input protection : XT60 -> 15A ATO fuse -> LM74800-Q1 ideal-diode controller with
//                       back-to-back CSD18543Q3A FETs = reverse-polarity block + HW UVLO
//                       (9.3V on) + OV (15.2V off); SMBJ16A TVS clamps the input.
//   regulation       : TWO synchronous LM5145 buck stages from the protected VSW rail:
//                       Buck A -> 5V_C (USB-C, 6A), Buck B -> 5V_A (feeds the 3x USB-A bank,
//                       7.5A aggregate). Sequenced: A's PGOOD enables B (soft inrush).
//   per-port limiting: each USB-A port has its own TPS2557 current-limit switch (ILIM=2.5A,
//                       auto-retry, thermal + reverse-current). USB-C draws from 5V_C directly,
//                       copper sized for 6A, dual 10k Rp advertise legacy 3A source cap.
//   clamps/indicator : SMBJ5.0A TVS on each 5V rail; power LED per rail.
//
// CANON (ADR-0001/0002): KiCad + KRT + the gate stack are authoritative. The <footprint>
// child GEOMETRY below is a placeholder for tscircuit's own render ONLY — what is
// load-bearing is each pad NAME (portHints = the EXACT KiCad pad name) and the net it
// binds to. The backend loads the real land pattern by FPID (resolved from 02_parts via
// the supplierPartNumbers JLC code) and places/routes it.
//
// NET-NAME CONVENTION (ADR-0001): tscircuit's net. selector cannot author a leading-digit
// net name, so 5V_A -> N5V_A and 5V_C -> N5V_C; the converter strips the guard N before a
// digit -> canonical 5V_A / 5V_C. No other rail leads with a digit -> net_aliases.txt not needed.
//
// SANCTIONED FLOATS (converter emits no_connect for any pad omitted from `connections`):
//   U2/U3 pads 7,9,15,16 (SYNCOUT/NC); U4/U5/U6 pad 8 (open-drain FAULT, no MCU);
//   J5 A8/B8 (SBU1/SBU2 — power-only, no data); U1 WSON-12 exposed pad (not a modeled pin).

// ---------- specialty <footprint> children: pad NAMES = KiCad pad names ----------
// Geometry is a non-overlapping placeholder (tscircuit render only). Simple row layout.
const row = (names: string[], pitch = 1.2) =>
  names.map((n, i) => (
    <smtpad
      key={`${n}-${i}`}
      portHints={[n]}
      pcbX={`${(i - (names.length - 1) / 2) * pitch}mm`}
      pcbY="0mm"
      width="0.6mm"
      height="0.6mm"
      shape="rect"
      layer="top"
    />
  ))

const fpXT60 = <footprint>{row(["1", "2"], 7.2)}</footprint>
const fpUSBA = <footprint>{row(["1", "2", "3", "4", "SH"], 2.0)}</footprint>
const fpUSBC = (
  <footprint>
    {row([
      "A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12",
      "B1", "B4", "B5", "B6", "B7", "B8", "B9", "B12", "SH",
    ], 0.8)}
  </footprint>
)
const fpLM74800 = <footprint>{row(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"], 0.5)}</footprint>
const fpLM5145 = (
  <footprint>
    {row([
      "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
      "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21",
    ], 0.5)}
  </footprint>
)
const fpNFET = <footprint>{row(["1", "2", "3", "4", "5"], 0.65)}</footprint>
const fpTPS = <footprint>{row(["1", "2", "3", "4", "5", "6", "7", "8", "9"], 0.65)}</footprint>
const fpFuse = <footprint>{row(["1", "2"], 4.9)}</footprint>
const fpInd = <footprint>{row(["1", "2"], 6.0)}</footprint>
const fpCP = <footprint>{row(["1", "2"], 5.6)}</footprint>

// ---------- LCSC codes: each links a specialty part to its 02_parts footprint ----------
const jlc = (c: string) => ({ jlcpcb: [c] })
const C = {
  NFET: "C840100", TPS: "C130056", LM74800: "C3215600", LM5145: "C485912",
  IND: "C17700181", FUSE: "C207061", XT60: "C98732", USBC: "C3020560",
  USBA: "1001-011-01101", LED: "C2297", CP63: "C128504", CP810: "C454289",
  SMBJ16: "C353386", SMBJ5: "C113974",
}

// ---------- one synchronous LM5145 buck stage ----------
const buckStage = (
  S: "A" | "B", uref: string, rilim: string, en: string, vout: string, rfb2: string,
  pgood: string,
) => {
  const N = (n: string) => `net.${n}`
  return (
    <group name={`buck${S}`}>
      <chip name={uref} footprint={fpLM5145} supplierPartNumbers={jlc(C.LM5145)}
        connections={{
          "20": N("VSW"), "1": N(en), "2": N(`RT_${S}`), "3": N(`SS_${S}`), "11": N(`ILIM_${S}`),
          "8": N("GND"), "6": N("GND"), "12": N("GND"), "21": N("GND"),
          "14": N(`VCC_${S}`), "17": N(`BST_${S}`), "18": N(`HO_${S}`), "19": N(`SW_${S}`),
          "13": N(`LO_${S}`), "5": N(`FB_${S}`), "4": N(`COMP_${S}`), "10": N(pgood),
          // pads 7,9,15,16 intentionally floating (no_connect)
        }} />
      <chip name={`Q${S}1`} footprint={fpNFET} supplierPartNumbers={jlc(C.NFET)}
        connections={{ "4": N(`HO_${S}`), "5": N("VSW"), "1": N(`SW_${S}`), "2": N(`SW_${S}`), "3": N(`SW_${S}`) }} />
      <chip name={`Q${S}2`} footprint={fpNFET} supplierPartNumbers={jlc(C.NFET)}
        connections={{ "4": N(`LO_${S}`), "5": N(`SW_${S}`), "1": N("GND"), "2": N("GND"), "3": N("GND") }} />
      <inductor name={`L${S}1`} inductance="3.3uH" footprint={fpInd} supplierPartNumbers={jlc(C.IND)}
        connections={{ pin1: N(`SW_${S}`), pin2: N(vout) }} />
      <resistor name={`R${S}1`} resistance="16.5k" footprint="0402"
        connections={{ pin1: N(`RT_${S}`), pin2: N("GND") }} />
      <capacitor name={`C${S}1`} capacitance="47nF" footprint="0402"
        connections={{ pin1: N(`SS_${S}`), pin2: N("GND") }} />
      <capacitor name={`C${S}2`} capacitance="2.2uF" footprint="0603"
        connections={{ pin1: N(`VCC_${S}`), pin2: N("GND") }} />
      <capacitor name={`C${S}3`} capacitance="100nF" footprint="0402"
        connections={{ pin1: N(`BST_${S}`), pin2: N(`SW_${S}`) }} />
      <resistor name={`R${S}2`} resistance={rilim} footprint="0402"
        connections={{ pin1: N(`ILIM_${S}`), pin2: N(`SW_${S}`) }} />
      <capacitor name={`C${S}4`} capacitance="18pF" footprint="0402"
        connections={{ pin1: N(`ILIM_${S}`), pin2: N("GND") }} />
      {[1, 2, 3].map((i) => (
        <capacitor key={`c5${i}`} name={`C${S}5${i}`} capacitance="10uF" footprint="1210"
          connections={{ pin1: N("VSW"), pin2: N("GND") }} />
      ))}
      {[1, 2, 3, 4].map((i) => (
        <capacitor key={`c6${i}`} name={`C${S}6${i}`} capacitance="47uF" footprint="1210"
          connections={{ pin1: N(vout), pin2: N("GND") }} />
      ))}
      <capacitor name={`C${S}7`} capacitance="220uF" polarized footprint={fpCP} supplierPartNumbers={jlc(C.CP63)}
        connections={{ pin1: N(vout), pin2: N("GND") }} />
      <resistor name={`R${S}3`} resistance="20k" footprint="0402"
        connections={{ pin1: N(vout), pin2: N(`FB_${S}`) }} />
      <resistor name={`R${S}4`} resistance={rfb2} footprint="0402"
        connections={{ pin1: N(`FB_${S}`), pin2: N("GND") }} />
      <resistor name={`R${S}5`} resistance="13k" footprint="0402"
        connections={{ pin1: N(`COMP_${S}`), pin2: N(`CX_${S}`) }} />
      <capacitor name={`C${S}8`} capacitance="8.2nF" footprint="0402"
        connections={{ pin1: N(`CX_${S}`), pin2: N(`FB_${S}`) }} />
      <capacitor name={`C${S}9`} capacitance="39pF" footprint="0402"
        connections={{ pin1: N(`COMP_${S}`), pin2: N(`FB_${S}`) }} />
      <capacitor name={`C${S}10`} capacitance="1.2nF" footprint="0402"
        connections={{ pin1: N(vout), pin2: N(`CY_${S}`) }} />
      <resistor name={`R${S}6`} resistance="4.64k" footprint="0402"
        connections={{ pin1: N(`CY_${S}`), pin2: N(`FB_${S}`) }} />
    </group>
  )
}

export default () => (
  <board width="100mm" height="60mm">
    {/* ============ region 1: INPUT + PROTECTION ============ */}
    <chip name="J1" footprint={fpXT60} supplierPartNumbers={jlc(C.XT60)}
      connections={{ "1": "net.GND", "2": "net.VBATT_RAW" }} />
    {/* F1: 15A ATO blade fuse in a holder. Authored as <chip> (tscircuit's <fuse>
        drops supplierPartNumbers, so its FPID would not resolve from 02_parts). */}
    <chip name="F1" footprint={fpFuse} supplierPartNumbers={jlc(C.FUSE)}
      connections={{ "1": "net.VBATT_RAW", "2": "net.VBATT_F" }} />
    <diode name="D1" footprint="smb" supplierPartNumbers={jlc(C.SMBJ16)}
      connections={{ pin1: "net.VBATT_F", pin2: "net.GND" }} />
    <capacitor name="C15" capacitance="100nF" footprint="0402"
      connections={{ pin1: "net.VBATT_F", pin2: "net.GND" }} />
    <capacitor name="CE1" capacitance="100uF" polarized footprint={fpCP} supplierPartNumbers={jlc(C.CP810)}
      connections={{ pin1: "net.VSW", pin2: "net.GND" }} />

    {/* ============ region 2: FRONT-END (LM74800-Q1 ideal diode + 2x CSD18543Q3A) ============ */}
    <chip name="U1" footprint={fpLM74800} supplierPartNumbers={jlc(C.LM74800)}
      connections={{
        "1": "net.DG_FE", "2": "net.VBATT_F", "3": "net.VBATT_F", "4": "net.FE_LAD",
        "5": "net.FE_OV", "6": "net.FE_EN", "7": "net.GND", "8": "net.HG_FE",
        "9": "net.VSW", "10": "net.FE_MID", "11": "net.FE_CAP", "12": "net.FE_MID",
      }} />
    <chip name="Q2" footprint={fpNFET} supplierPartNumbers={jlc(C.NFET)}
      connections={{ "4": "net.HG_FE", "5": "net.FE_MID", "1": "net.VSW", "2": "net.VSW", "3": "net.VSW" }} />
    <chip name="Q1" footprint={fpNFET} supplierPartNumbers={jlc(C.NFET)}
      connections={{ "4": "net.DG_FE", "5": "net.FE_MID", "1": "net.VBATT_F", "2": "net.VBATT_F", "3": "net.VBATT_F" }} />
    <resistor name="R1" resistance="887k" footprint="0402"
      connections={{ pin1: "net.FE_LAD", pin2: "net.FE_EN" }} />
    <resistor name="R2" resistance="52.3k" footprint="0402"
      connections={{ pin1: "net.FE_EN", pin2: "net.FE_OV" }} />
    <resistor name="R3" resistance="82.5k" footprint="0402"
      connections={{ pin1: "net.FE_OV", pin2: "net.GND" }} />
    <capacitor name="C16" capacitance="2.2uF" footprint="0603"
      connections={{ pin1: "net.FE_EN", pin2: "net.GND" }} />
    <capacitor name="C1" capacitance="100nF" footprint="0402"
      connections={{ pin1: "net.FE_CAP", pin2: "net.FE_MID" }} />
    <capacitor name="C2" capacitance="100nF" footprint="0402"
      connections={{ pin1: "net.FE_MID", pin2: "net.GND" }} />
    <capacitor name="C3" capacitance="47nF" footprint="0402"
      connections={{ pin1: "net.HG_FE", pin2: "net.VSW" }} />

    {/* ============ region 3: BUCK A -> USB-C rail (5V_C, 6A) + PGOOD sequencing ============ */}
    <resistor name="R4" resistance="100k" footprint="0402"
      connections={{ pin1: "net.VSW", pin2: "net.EN_A" }} />
    <resistor name="R5" resistance="16.5k" footprint="0402"
      connections={{ pin1: "net.EN_A", pin2: "net.GND" }} />
    {buckStage("A", "U2", "348", "EN_A", "N5V_C", "3.74k", "PGOODA_RAW")}
    <resistor name="R21" resistance="20k" footprint="0402"
      connections={{ pin1: "net.N5V_C", pin2: "net.PGOODA_RAW" }} />
    <resistor name="R33" resistance="20k" footprint="0402"
      connections={{ pin1: "net.PGOODA_RAW", pin2: "net.PGOOD_A" }} />
    <resistor name="R34" resistance="16.5k" footprint="0402"
      connections={{ pin1: "net.PGOOD_A", pin2: "net.GND" }} />

    {/* ============ region 4: BUCK B -> USB-A rail (5V_A, 7.5A), EN = PGOOD_A ============ */}
    {buckStage("B", "U3", "432", "PGOOD_A", "N5V_A", "3.74k", "PGOOD_B")}

    {/* ============ region 5: USB-A x3 (TPS2557 per-port limit, DCP D+/D- short) ============ */}
    {([
      ["U4", "J2", "R16", "VBUS1", "DCP1", "C20", "C30", "ILIM1"],
      ["U5", "J3", "R17", "VBUS2", "DCP2", "C21", "C31", "ILIM2"],
      ["U6", "J4", "R18", "VBUS3", "DCP3", "C22", "C32", "ILIM3"],
    ] as const).map(([u, j, rl, vb, dcp, cin, cout, ilim]) => (
      <group key={u} name={`usba_${u}`}>
        <chip name={u} footprint={fpTPS} supplierPartNumbers={jlc(C.TPS)}
          connections={{
            "2": "net.N5V_A", "3": "net.N5V_A", "4": "net.N5V_A", "1": "net.GND", "9": "net.GND",
            "6": `net.${vb}`, "7": `net.${vb}`, "5": `net.${ilim}`,
            // pad 8 (open-drain FAULT) intentionally floating
          }} />
        <resistor name={rl} resistance="24.3k" footprint="0402"
          connections={{ pin1: `net.${ilim}`, pin2: "net.GND" }} />
        <capacitor name={cin} capacitance="100nF" footprint="0402"
          connections={{ pin1: "net.N5V_A", pin2: "net.GND" }} />
        <capacitor name={cout} capacitance="22uF" footprint="1206"
          connections={{ pin1: `net.${vb}`, pin2: "net.GND" }} />
        <chip name={j} footprint={fpUSBA} supplierPartNumbers={jlc(C.USBA)}
          connections={{ "1": `net.${vb}`, "2": `net.${dcp}`, "3": `net.${dcp}`, "4": "net.GND", "SH": "net.GND" }} />
      </group>
    ))}

    {/* ============ region 6: USB-C source (dual 10k Rp = legacy 3A source advertise) ============ */}
    <resistor name="R19" resistance="10k" footprint="0402"
      connections={{ pin1: "net.N5V_C", pin2: "net.CC1" }} />
    <chip name="J5" footprint={fpUSBC} supplierPartNumbers={jlc(C.USBC)}
      connections={{
        "A4": "net.N5V_C", "A9": "net.N5V_C", "B4": "net.N5V_C", "B9": "net.N5V_C",
        "A5": "net.CC1", "B5": "net.CC2",
        "A1": "net.GND", "A12": "net.GND", "B1": "net.GND", "B12": "net.GND",
        "A6": "net.DCPC", "A7": "net.DCPC", "B6": "net.DCPC", "B7": "net.DCPC",
        "SH": "net.GND",
        // A8/B8 (SBU1/SBU2) intentionally floating (power-only, no data)
      }} />
    <resistor name="R20" resistance="10k" footprint="0402"
      connections={{ pin1: "net.N5V_C", pin2: "net.CC2" }} />
    <capacitor name="C33" capacitance="22uF" footprint="1206"
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />
    <capacitor name="C34" capacitance="22uF" footprint="1206"
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />

    {/* ============ region 7: RAIL TVS CLAMPS + POWER LEDs ============ */}
    <diode name="D2" footprint="smb" supplierPartNumbers={jlc(C.SMBJ5)}
      connections={{ pin1: "net.N5V_A", pin2: "net.GND" }} />
    <diode name="D3" footprint="smb" supplierPartNumbers={jlc(C.SMBJ5)}
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />
    <resistor name="R22" resistance="1k" footprint="0402"
      connections={{ pin1: "net.N5V_A", pin2: "net.LEDA_A" }} />
    <led name="D4" footprint="0805" supplierPartNumbers={jlc(C.LED)}
      connections={{ pin1: "net.GND", pin2: "net.LEDA_A" }} />
    <resistor name="R23" resistance="1k" footprint="0402"
      connections={{ pin1: "net.N5V_C", pin2: "net.LEDC_A" }} />
    <led name="D5" footprint="0805" supplierPartNumbers={jlc(C.LED)}
      connections={{ pin1: "net.GND", pin2: "net.LEDC_A" }} />
  </board>
)

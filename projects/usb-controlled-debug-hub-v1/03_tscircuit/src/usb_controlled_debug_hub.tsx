// Four-port self-powered USB 2.0 debug hub. One internal downstream port is a
// factory-programmed MCP2221A management function; no project firmware exists.

import { sel } from "tscircuit"

const TwoSided = ({ pins, pitch = 0.65, span = 5.4 }: { pins: number; pitch?: number; span?: number }) => {
  const half = Math.ceil(pins / 2)
  return <footprint>
    {Array.from({ length: half }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 1}`]}
      pcbX={`${-span / 2}mm`} pcbY={`${((half - 1) / 2 - i) * pitch}mm`}
      width="1mm" height={`${Math.min(0.32, pitch * 0.58)}mm`} shape="rect" />)}
    {Array.from({ length: pins - half }, (_, i) => <smtpad key={`r${i}`} portHints={[`${half + i + 1}`]}
      pcbX={`${span / 2}mm`} pcbY={`${(-(pins - half - 1) / 2 + i) * pitch}mm`}
      width="1mm" height={`${Math.min(0.32, pitch * 0.58)}mm`} shape="rect" />)}
  </footprint>
}

const Qfn64Ep = () => <footprint>
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`b${i}`} portHints={[`${i + 1}`]} pcbX={`${-3.75 + i * 0.5}mm`} pcbY="-4.5mm" width="0.28mm" height="1mm" shape="rect" />)}
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${i + 17}`]} pcbX="4.5mm" pcbY={`${-3.75 + i * 0.5}mm`} width="1mm" height="0.28mm" shape="rect" />)}
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`t${i}`} portHints={[`${i + 33}`]} pcbX={`${3.75 - i * 0.5}mm`} pcbY="4.5mm" width="0.28mm" height="1mm" shape="rect" />)}
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 49}`]} pcbX="-4.5mm" pcbY={`${3.75 - i * 0.5}mm`} width="1mm" height="0.28mm" shape="rect" />)}
  <smtpad portHints={["65"]} pcbX="0mm" pcbY="0mm" width="4.7mm" height="4.7mm" shape="rect" />
</footprint>

const UsbB = () => <footprint>
  <platedhole portHints={["1"]} pcbX="1.25mm" pcbY="-2mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="-1.25mm" pcbY="-2mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["3"]} pcbX="-1.25mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["4"]} pcbX="1.25mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["5", "SH"]} pcbX="-6.02mm" pcbY="2.71mm" outerDiameter="3.5mm" holeDiameter="2.3mm" shape="circle" />
  <platedhole portHints={["5", "SH"]} pcbX="6.02mm" pcbY="2.71mm" outerDiameter="3.5mm" holeDiameter="2.3mm" shape="circle" />
</footprint>

const UsbA = () => <footprint>
  {Array.from({ length: 4 }, (_, i) => <platedhole key={`p${i}`} portHints={[`${i + 1}`]}
    pcbX={`${[-3.5, -1, 1, 3.5][i]}mm`} pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1mm" shape="circle" />)}
  <platedhole portHints={["5", "SH"]} pcbX="-6.619mm" pcbY="2.6mm" outerDiameter="4mm" holeDiameter="3mm" shape="circle" />
  <platedhole portHints={["5", "SH"]} pcbX="6.621mm" pcbY="2.6mm" outerDiameter="4mm" holeDiameter="3mm" shape="circle" />
</footprint>

const InputTerminal = () => <footprint>
  <platedhole portHints={["1"]} pcbX="-2.5mm" pcbY="0mm" outerDiameter="2.2mm" holeDiameter="1.3mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="2.5mm" pcbY="0mm" outerDiameter="2.2mm" holeDiameter="1.3mm" shape="circle" />
</footprint>

const BladeFuse = () => <footprint>
  <platedhole portHints={["1"]} pcbX="-4.95mm" pcbY="-2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  <platedhole portHints={["1"]} pcbX="-4.95mm" pcbY="2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="4.95mm" pcbY="-2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="4.95mm" pcbY="2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
</footprint>

const PowerDi5060 = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-1.905mm" pcbY="2.74mm" width="0.6mm" height="1.27mm" shape="rect" />
  {[2, 3, 4].map((p, i) => <smtpad key={`s${p}`} portHints={[`${p}`]} pcbX={`${-0.635 + i * 1.27}mm`} pcbY="2.74mm" width="0.6mm" height="1.27mm" shape="rect" />)}
  {[5, 6, 7, 8].map((p, i) => <smtpad key={`d${p}`} portHints={[`${p}`]} pcbX={`${1.905 - i * 1.27}mm`} pcbY="-2.74mm" width="0.6mm" height="1.02mm" shape="rect" />)}
</footprint>

const SunlordSwpa4030 = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-1.5mm" pcbY="0mm" width="1.1mm" height="3.7mm" shape="rect" />
  <smtpad portHints={["2"]} pcbX="1.5mm" pcbY="0mm" width="1.1mm" height="3.7mm" shape="rect" />
</footprint>

const Tps2557Fp = () => <footprint>
  {Array.from({ length: 4 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-1.65mm" pcbY={`${0.975 - i * 0.65}mm`} width="0.9mm" height="0.35mm" shape="rect" />)}
  {Array.from({ length: 4 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${i + 5}`]} pcbX="1.65mm" pcbY={`${-0.975 + i * 0.65}mm`} width="0.9mm" height="0.35mm" shape="rect" />)}
  <smtpad portHints={["9"]} pcbX="0mm" pcbY="0mm" width="1.65mm" height="2.4mm" shape="rect" />
</footprint>

// TI RPW0010A HotRod QFN.  The project-local KiCad footprint is generated
// from the exact JLC C2864845 CAD and checked against TI drawing 4225183/A;
// this source footprint preserves the ten-pin topology for schematic export.
const Tps25947Fp = () => <footprint>
  {[1, 2, 3, 4].map((p, i) => <smtpad key={`l${p}`} portHints={[`${p}`]}
    pcbX="-0.9mm" pcbY={`${0.7125 - i * 0.475}mm`} width="0.6mm" height="0.25mm" shape="rect" />)}
  <smtpad portHints={["5"]} pcbX="-0.3mm" pcbY="0mm" width="0.3mm" height="1.8mm" shape="rect" />
  <smtpad portHints={["6"]} pcbX="0.3mm" pcbY="0mm" width="0.3mm" height="1.8mm" shape="rect" />
  {[7, 8, 9, 10].map((p, i) => <smtpad key={`r${p}`} portHints={[`${p}`]}
    pcbX="0.9mm" pcbY={`${-0.7125 + i * 0.475}mm`} width="0.6mm" height="0.25mm" shape="rect" />)}
</footprint>

const Polymer63 = () => <footprint>
  <smtpad portHints={["1", "POS"]} pcbX="-2.3mm" pcbY="0mm" width="2.2mm" height="2.7mm" shape="rect" />
  <smtpad portHints={["2", "NEG"]} pcbX="2.3mm" pcbY="0mm" width="2.2mm" height="2.7mm" shape="rect" />
</footprint>

const schProps = (name: string) => {
  // Most sheets contain label-connected functional islands. Keep those islands
  // close enough that the page renderer does not shrink symbols and labels to
  // an unreadable scale. The interlock sheet is already compact by construction.
  const at = (sheet: string, section: string, x: number, y: number) => {
    const scaleBySheet: Record<string, number> = {
      power: 0.55,
      hub: 0.28,
      hub_straps: 0.35,
      management: 0.35,
      interlocks: 1,
      port_1: 0.28,
      port_2: 0.28,
      port_3: 0.28,
      port_4: 0.28,
    }
    const scale = scaleBySheet[sheet] ?? 0.35
    return {
      schSheetName: sheet,
      schSectionName: section,
      schX: `${x * scale}mm`,
      schY: `${y * scale}mm`,
    }
  }
  const power: Record<string, [number, number]> = {
    J_PWR: [-24, 10], F_IN: [-10, 10], U_AGG: [4, 10],
    C_AGG_IN: [-3, 5],
    R_AGG_UV_TOP: [-2, -1], R_AGG_UV_MID: [5, -1], R_AGG_OV_BOT: [12, -1],
    R_AGG_ILIM: [18, 7], C_AGG_TIMER: [18, 1], C_AGG_DVDT: [29, -4],
    C_TRUNK_HF: [25, 14], C_TRUNK_BULK: [33, 14], C_TRUNK_USB: [43, 14],
    U_BUCK: [-5, -10], C_BUCK_IN: [-16, -14], C_BST: [0, -24], L_MAIN: [7, -10],
    C_BUCK_OUT1: [16, -8], C_BUCK_OUT2: [16, -16],
  }
  if (power[name]) {
    const powerProps = at("power", "Protected input and 3.3 V regulator", ...power[name])
    if (name.startsWith("R_AGG_UV_") || name === "R_AGG_OV_BOT") return { ...powerProps, schRotation: "90deg" }
    return powerProps
  }

  const strap = name.match(/^R_(CFG|NONREM|SWAP|GANG|BOOST|DIS)(.*)$/)
  if (strap) {
    const strapPos: Record<string, [number, number]> = {
      R_CFG0: [-20, 12], R_CFG1: [-10, 12], R_CFG2: [0, 12],
      R_NONREM1: [10, 12], R_NONREM0: [20, 12],
      R_SWAP1: [-18, 2], R_SWAP2: [-6, 2], R_SWAP3: [6, 2], R_SWAP4: [18, 2],
      R_SWAP5: [-12, -8], R_SWAP6: [0, -8], R_SWAP7: [12, -8],
      R_GANG: [-12, -18], R_BOOST0: [0, -18], R_BOOST1: [12, -18],
      R_DIS6N: [-18, -28], R_DIS6P: [-6, -28], R_DIS7N: [6, -28], R_DIS7P: [18, -28],
    }
    return at("hub_straps", "USB2517I hardware configuration and disabled ports", ...(strapPos[name] ?? [0, 0]))
  }

  const hub: Record<string, [number, number]> = {
    J_UP: [-38, 8], U_ESD_UP: [-24, 8], U_HUB: [0, 4], Y_HUB: [18, -4],
    R_XTAL: [18, -10], R_RBIAS: [12, 16], C_XTAL1: [14, -17], C_XTAL2: [22, -17],
    R_HUB_RESET: [-18, -12], C_HUB_RESET: [-10, -12],
    R_VBUS_TOP: [-22, 17], R_VBUS_BOT: [-15, 17],
  }
  const hubCaps = ["C_HUB_A1", "C_HUB_A2", "C_HUB_A3", "C_HUB_A4", "C_HUB_A_BULK", "C_HUB_CR_HF",
    "C_HUB_CR_BULK", "C_HUB_DD", "C_HUB_PLL", "C_HUB_18", "C_HUB_18PLL"]
  if (hubCaps.includes(name)) {
    const i = hubCaps.indexOf(name), row = Math.floor(i / 6), col = i % 6
    return at("hub", "Upstream USB and seven-port hub core", -22 + col * 9, -24 - row * 8)
  }
  if (hub[name]) return at("hub", "Upstream USB and seven-port hub core", ...hub[name])

  const port = name.match(/^(?:U_DATA|Q_DATA|U_PWR|U_ESD|J_PORT|R_ILIM|R_DATA_OE|R_DATA_OK|R_PWR_EN|C_DATA|C_PWR|C_PORT)([1-4])(?:_|$)/)
  if (port) {
    const prefix = name.replace(port[1], "N")
    const portPos: Record<string, [number, number]> = {
      U_DATAN: [-13, 5], C_DATAN: [-19, -1], R_DATA_OEN: [-13, 15], Q_DATAN: [-2, 12], R_DATA_OKN: [-1, 1],
      U_PWRN: [-8, -13], R_ILIMN: [-17, -19], R_PWR_ENN: [-7, -23], C_PWRN_IN: [-18, -10],
      C_PORTN_HF: [7, -13], C_PORTN_BULK: [25, -13], U_ESDN: [9, 5], J_PORTN: [35, 5],
    }
    return at(`port_${port[1]}`, `External USB port ${port[1]}`, ...(portPos[prefix] ?? [0, 0]))
  }

  const interlock: Record<string, [number, number]> = {
    U_AND_PWR: [-10, 6], C_AND_PWR: [-10, -6], U_AND_DATA: [10, 6], C_AND_DATA: [10, -6],
  }
  if (interlock[name]) return at("interlocks", "Hardware power and data interlocks", ...interlock[name])

  const management: Record<string, [number, number]> = {
    U_PWR_CTRL: [-20, 8], R_ILIM_CTRL: [-24, -2], C_PWR_CTRL_IN: [-17, -6],
    C_PWR_CTRL_OUT_HF: [-24, -10], C_PWR_CTRL_OUT: [-20, -17],
    U_CTRL: [-6, 5], C_CTRL_VDD: [-10, -7], C_CTRL_VUSB: [-4, -8], R_CTRL_RESET: [-12, -14],
    R_I2C_SCL: [-2, -19], R_I2C_SDA: [5, -19], U_EXP: [13, 5], C_EXP_VDD: [10, -7], R_EXP_RESET: [18, -10],
    R_PWR_CMD1: [-18, -25], R_PWR_CMD2: [-6, -25], R_PWR_CMD3: [6, -25], R_PWR_CMD4: [18, -25],
    R_DATA_CMD1: [-18, -33], R_DATA_CMD2: [-6, -33], R_DATA_CMD3: [6, -33], R_DATA_CMD4: [18, -33],
  }
  const managementProps = at("management", "Factory USB management and GPIO expander", ...(management[name] ?? [0, 0]))
  if (name === "R_I2C_SCL" || name === "R_I2C_SDA") return { ...managementProps, schRotation: "90deg" }
  return managementProps
}

const R = ({ name, value, a, b, jlc, fp = "0402" }: any) => <resistor name={name} resistance={value} footprint={fp}
  {...schProps(name)} supplierPartNumbers={{ jlcpcb: [jlc] }} connections={{ pin1: `net.${a}`, pin2: `net.${b}` }} />
const C = ({ name, value, a, b, jlc, fp = "0402", studyX, studyY }: any) => <capacitor name={name} capacitance={value} footprint={fp}
  {...schProps(name)}
  {...(studyX !== undefined ? { pcbX: `${studyX}mm`, pcbY: `${studyY}mm` } : {})}
  supplierPartNumbers={{ jlcpcb: [jlc] }} connections={{ pin1: `net.${a}`, pin2: `net.${b}` }} />

const Tps2557 = ({ name, en, out, fault, ilim, cin, coutHf, coutBulk, studyX }: any) => <group name={`${name}_cell`}>
  <chip name={name} supplierPartNumbers={{ jlcpcb: ["C130056"] }} footprint={<Tps2557Fp />}
    {...schProps(name)}
    pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "EN", pin5: "ILIM", pin6: "OUT1", pin7: "OUT2", pin8: "FAULT_N", pin9: "EP" }}
    connections={{ pin1: "net.GND", pin2: "net.P5V_PROTECTED", pin3: "net.P5V_PROTECTED", pin4: `net.${en}`, pin5: `net.${ilim}`, pin6: `net.${out}`, pin7: `net.${out}`, pin8: `net.${fault}`, pin9: "net.GND" }} />
  <R name={`R_${ilim}`} value="165k" a={ilim} b="GND" jlc="C327368" />
  <C name={cin} value="100nF" a="P5V_PROTECTED" b="GND" jlc="C1525" studyX={studyX} studyY={0} />
  <C name={coutHf} value="100nF" a={out} b="GND" jlc="C1525" studyX={studyX + 3} studyY={0} />
  {coutBulk ? <C name={coutBulk} value={out === "VBUS_CTRL" ? "1uF" : "22uF"} a={out} b="GND"
    jlc={out === "VBUS_CTRL" ? "C52923" : "C342660"} fp={out === "VBUS_CTRL" ? "0402" : "1210"} /> : null}
</group>

const ExternalPort = ({ p, hubP, hubN, prtPwr, ocs }: any) => {
  const hp = `P${p}_HUB_P`, hn = `P${p}_HUB_N`, pp = `P${p}_PORT_P`, pn = `P${p}_PORT_N`
  const vbus = `VBUS${p}_SW`
  return <group name={`external_port_${p}`} pcbX={`${(p - 2.5) * 105}mm`} pcbY="-100mm">
    <chip name={`U_DATA${p}`} supplierPartNumbers={{ jlcpcb: ["C11355"] }} footprint={<TwoSided pins={10} pitch={0.5} span={3.4} />}
      {...schProps(`U_DATA${p}`)}
      pinLabels={{ pin1: "VCC", pin2: "SEL", pin3: "D_PLUS", pin4: "D_MINUS", pin5: "GND", pin6: "HSD1_MINUS", pin7: "HSD1_PLUS", pin8: "HSD2_MINUS", pin9: "HSD2_PLUS", pin10: "OE" }}
      // The analog switch channels are electrically symmetric.  The outward-
      // facing USB-A footprint puts connector D+ on the left launch, so use
      // HSD1- / D- for logical D+ and HSD1+ / D+ for logical D-.  This keeps
      // the physical pair ordered through the switch without a PCB crossover.
      connections={{ pin1: "net.N3V3_MAIN", pin2: "net.GND", pin3: `net.${hn}`, pin4: `net.${hp}`, pin5: "net.GND", pin6: `net.${pp}`, pin7: `net.${pn}`, pin10: `net.DATA_OE${p}_N` }} />
    <C name={`C_DATA${p}`} value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />
    <R name={`R_DATA_OE${p}`} value="10k" a="N3V3_MAIN" b={`DATA_OE${p}_N`} jlc="C60490" />
    <chip name={`Q_DATA${p}`} supplierPartNumbers={{ jlcpcb: ["C85047"] }} footprint="sot23"
      {...schProps(`Q_DATA${p}`)}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: `net.DATA_OK${p}`, pin2: "net.GND", pin3: `net.DATA_OE${p}_N` }} />
    <R name={`R_DATA_OK${p}`} value="10k" a={`DATA_OK${p}`} b="GND" jlc="C60490" />
    <Tps2557 name={`U_PWR${p}`} en={`PWR_EN${p}`} out={vbus} fault={ocs} ilim={`ILIM${p}`}
      cin={`C_PWR${p}_IN`} coutHf={`C_PORT${p}_HF`} coutBulk={`C_PORT${p}_BULK`} studyX={-12} />
    <R name={`R_PWR_EN${p}`} value="10k" a={`PWR_EN${p}`} b="GND" jlc="C60490" />
    <chip name={`U_ESD${p}`} supplierPartNumbers={{ jlcpcb: ["C3708426"] }}
      manufacturerPartNumber="PESD2USB3UX-TR" footprint="sot23"
      {...schProps(`U_ESD${p}`)}
      pinLabels={{ pin1: "IO1", pin2: "IO2", pin3: "GND" }}
      connections={{ pin1: `net.${pp}`, pin2: `net.${pn}`, pin3: "net.GND" }} />
    <chip name={`J_PORT${p}`} supplierPartNumbers={{ jlcpcb: ["C503996"] }} footprint={<UsbA />}
      {...schProps(`J_PORT${p}`)}
      pinLabels={{ pin1: "VBUS", pin2: "D_MINUS", pin3: "D_PLUS", pin4: "GND", pin5: "SHIELD" }}
      connections={{ pin1: `net.${vbus}`, pin2: `net.${pn}`, pin3: `net.${pp}`, pin4: "net.GND", pin5: "net.GND" }} />
  </group>
}

// This oversized board is only tscircuit's non-authoritative auto-placement
// canvas. KiCad floorplan/placement owns the real 110 x 75 mm starting outline.
export default () => <board width="500mm" height="350mm" routingDisabled>
  <schematicsheet name="power"
    displayName="POWER — regulated 5 V input, fuse, aggregate eFuse and 3.3 V buck" sheetIndex={1} />
  <schematicsheet name="hub"
    displayName="USB HUB — upstream Type-B, ESD, USB2517I, straps, clock and bypass" sheetIndex={2} />
  <schematicsheet name="hub_straps"
    displayName="USB HUB CONFIGURATION — P1 swapped, P2-5 normal, P6-7 disabled" sheetIndex={3} />
  <schematicsheet name="management"
    displayName="MANAGEMENT — factory MCP2221A HID/I2C and MCP23017 command bank" sheetIndex={4} />
  <schematicsheet name="interlocks"
    displayName="INTERLOCKS — hub policy AND host command; data follows commanded power enable" sheetIndex={5} />
  <schematicsheet name="port_1" displayName="EXTERNAL PORT 1 — independent power/data disconnect" sheetIndex={6} />
  <schematicsheet name="port_2" displayName="EXTERNAL PORT 2 — independent power/data disconnect" sheetIndex={7} />
  <schematicsheet name="port_3" displayName="EXTERNAL PORT 3 — independent power/data disconnect" sheetIndex={8} />
  <schematicsheet name="port_4" displayName="EXTERNAL PORT 4 — independent power/data disconnect" sheetIndex={9} />
  <group name="protected_input_and_3v3" pcbX="-150mm" pcbY="100mm">
    <chip name="J_PWR" supplierPartNumbers={{ jlcpcb: ["C3819953"] }} footprint={<InputTerminal />}
      {...schProps("J_PWR")}
      pinLabels={{ pin1: "P5V_RAW", pin2: "GND" }} connections={{ pin1: "net.P5V_RAW", pin2: "net.GND" }} />
    <chip name="F_IN" manufacturerPartNumber="3568" footprint={<BladeFuse />}
      {...schProps("F_IN")}
      pinLabels={{ pin1: "FUSE_IN", pin2: "FUSE_OUT" }} connections={{ pin1: "net.P5V_RAW", pin2: "net.P5V_FUSED" }} />
    <chip name="U_AGG" supplierPartNumbers={{ jlcpcb: ["C2864845"] }}
      manufacturerPartNumber="TPS259474LRPWR" footprint={<Tps25947Fp />}
      {...schProps("U_AGG")}
      pinLabels={{ pin1: "EN_UVLO", pin2: "OVLO", pin3: "PG", pin4: "PGTH", pin5: "IN", pin6: "OUT", pin7: "DVDT", pin8: "GND", pin9: "ILM", pin10: "ITIMER" }}
      connections={{ pin1: "net.AGG_UV", pin2: "net.AGG_OV", pin4: "net.GND", pin5: "net.P5V_FUSED", pin6: "net.P5V_PROTECTED", pin7: "net.AGG_DVDT", pin8: "net.GND", pin9: "net.AGG_ILIM", pin10: "net.AGG_TIMER" }} />
    <C name="C_AGG_IN" value="100nF" a="P5V_FUSED" b="GND" jlc="C1525" />
    {/* One three-resistor string follows TI equations 10/11. Nominal UVLO is
        4.58 V and OVLO is 5.64 V; exact threshold/leakage corners are owned by
        power_tree.yaml.  A persistent aggregate overload latches U_AGG off
        until the external 5 V input is cycled. */}
    <R name="R_AGG_UV_TOP" value="150k" a="P5V_FUSED" b="AGG_UV" jlc="C22807" fp="0603" />
    <R name="R_AGG_UV_MID" value="10k" a="AGG_UV" b="AGG_OV" jlc="C25804" fp="0603" />
    <R name="R_AGG_OV_BOT" value="43.2k" a="AGG_OV" b="GND" jlc="C861404" fp="0603" />
    <R name="R_AGG_ILIM" value="1k" a="AGG_ILIM" b="GND" jlc="C110776" fp="0603" />
    <C name="C_AGG_TIMER" value="3.3nF" a="AGG_TIMER" b="GND" jlc="C77036" fp="0603" />
    <C name="C_AGG_DVDT" value="3.3nF" a="AGG_DVDT" b="GND" jlc="C77036" fp="0603" />
    <C name="C_TRUNK_HF" value="100nF" a="P5V_PROTECTED" b="GND" jlc="C1525" />
    <C name="C_TRUNK_BULK" value="22uF" a="P5V_PROTECTED" b="GND" jlc="C342660" fp="1210" />
    <capacitor name="C_TRUNK_USB" capacitance="180uF" polarized
      manufacturerPartNumber="16SVPF180M" supplierPartNumbers={{ jlcpcb: ["C136277"] }}
      {...schProps("C_TRUNK_USB")} footprint={<Polymer63 />}
      connections={{ pin1: "net.P5V_PROTECTED", pin2: "net.GND" }} />

    <chip name="U_BUCK" supplierPartNumbers={{ jlcpcb: ["C5248536"] }} footprint="sot23_6"
      {...schProps("U_BUCK")}
      pinLabels={{ pin1: "FB", pin2: "EN", pin3: "VIN", pin4: "GND", pin5: "SW", pin6: "BST" }}
      connections={{ pin1: "net.N3V3_MAIN", pin2: "net.P5V_PROTECTED", pin3: "net.P5V_PROTECTED", pin4: "net.GND", pin5: "net.SW_3V3", pin6: "net.BST_3V3" }} />
    <inductor name="L_MAIN" inductance="3.3uH" supplierPartNumbers={{ jlcpcb: ["C15269"] }}
      {...schProps("L_MAIN")}
      connections={{ pin1: "net.SW_3V3", pin2: "net.N3V3_MAIN" }} footprint={<SunlordSwpa4030 />} />
    <C name="C_BUCK_IN" value="10uF" a="P5V_PROTECTED" b="GND" jlc="C19702" fp="0603" />
    <C name="C_BST" value="100nF" a="BST_3V3" b="SW_3V3" jlc="C1525" />
    <C name="C_BUCK_OUT1" value="22uF" a="N3V3_MAIN" b="GND" jlc="C342660" fp="1210" />
    <C name="C_BUCK_OUT2" value="22uF" a="N3V3_MAIN" b="GND" jlc="C342660" fp="1210" />
  </group>

  <group name="upstream_and_hub" pcbX="0mm" pcbY="100mm">
    <chip name="J_UP" supplierPartNumbers={{ jlcpcb: ["C86462"] }} footprint={<UsbB />}
      {...schProps("J_UP")}
      pinLabels={{ pin1: "VBUS", pin2: "D_MINUS", pin3: "D_PLUS", pin4: "GND", pin5: "SHIELD" }}
      connections={{ pin1: "net.USB_UP_VBUS", pin2: "net.UP_HUB_N", pin3: "net.UP_HUB_P", pin4: "net.GND", pin5: "net.GND" }} />
    <chip name="U_ESD_UP" supplierPartNumbers={{ jlcpcb: ["C3708426"] }}
      manufacturerPartNumber="PESD2USB3UX-TR" footprint="sot23"
      {...schProps("U_ESD_UP")}
      pinLabels={{ pin1: "IO1", pin2: "IO2", pin3: "GND" }}
      connections={{ pin1: "net.UP_HUB_N", pin2: "net.UP_HUB_P", pin3: "net.GND" }} />

    <chip name="U_HUB" supplierPartNumbers={{ jlcpcb: ["C478081"] }} footprint={<Qfn64Ep />}
      {...schProps("U_HUB")}
      pinLabels={{ pin1:"DN1_DM",pin2:"DN1_DP",pin3:"DN2_DM",pin4:"DN2_DP",pin5:"VDDA33_1",pin6:"DN3_DM",pin7:"DN3_DP",pin8:"DN4_DM",pin9:"DN4_DP",pin10:"VDDA33_2",pin11:"DN5_DM",pin12:"DN5_DP",pin13:"CFG_SEL2",pin14:"LED_B7",pin15:"PRT_SWP7",pin16:"LED_B6",pin17:"PRT_SWP6",pin18:"LED_B5",pin19:"TEST",pin20:"PRTPWR4",pin21:"OCS4_N",pin22:"OCS3_N",pin23:"PRTPWR3",pin24:"VDD33CR",pin25:"VDD18",pin26:"PRTPWR2",pin27:"OCS2_N",pin28:"OCS1_N",pin29:"PRTPWR1",pin30:"PRTPWR5",pin31:"PRT_SWP5",pin32:"LED_B4",pin33:"PRT_SWP4",pin34:"GANG_EN",pin35:"OCS5_N",pin36:"PRTPWR7",pin37:"OCS7_N",pin38:"OCS6_N",pin39:"PRTPWR6",pin40:"NON_REM1",pin41:"CFG_SEL0",pin42:"CFG_SEL1",pin43:"RESET_N",pin44:"VBUS_DET",pin45:"NON_REM0",pin46:"VDD33",pin47:"PRT_SWP3",pin48:"BOOST1",pin49:"PRT_SWP2",pin50:"BOOST0",pin51:"PRT_SWP1",pin52:"VDDA33_3",pin53:"DN6_DM",pin54:"DN6_DP",pin55:"DN7_DM",pin56:"DN7_DP",pin57:"VDDA33_4",pin58:"UP_DM",pin59:"UP_DP",pin60:"XTAL2",pin61:"XTAL1",pin62:"VDD18PLL",pin63:"RBIAS",pin64:"VDD33PLL",pin65:"EP_VSS" }}
      connections={{
        // PRT_SWP1 is deliberately high: logical D+ occupies physical DN1_DM
        // and logical D- occupies physical DN1_DP, removing a geometric pair
        // crossover to the onboard controller. External ports 2..5 retain
        // normal physical polarity and keep their PRT_SWP straps low.
        pin1:"net.MGMT_P",pin2:"net.MGMT_N",pin3:"net.P1_HUB_N",pin4:"net.P1_HUB_P",pin5:"net.N3V3_MAIN",pin6:"net.P2_HUB_N",pin7:"net.P2_HUB_P",pin8:"net.P3_HUB_N",pin9:"net.P3_HUB_P",pin10:"net.N3V3_MAIN",pin11:"net.P4_HUB_N",pin12:"net.P4_HUB_P",pin13:"net.HUB_CFG2",pin15:"net.HUB_SWAP7",pin17:"net.HUB_SWAP6",pin20:"net.HUB_PRTPWR4",pin21:"net.HUB_OCS4_N",pin22:"net.HUB_OCS3_N",pin23:"net.HUB_PRTPWR3",pin24:"net.N3V3_MAIN",pin25:"net.HUB_VDD18",pin26:"net.HUB_PRTPWR2",pin27:"net.HUB_OCS2_N",pin28:"net.HUB_OCS1_N",pin29:"net.HUB_PRTPWR1",pin30:"net.HUB_PRTPWR5",pin31:"net.HUB_SWAP5",pin33:"net.HUB_SWAP4",pin34:"net.HUB_GANG",pin35:"net.HUB_OCS5_N",pin40:"net.HUB_NONREM1",pin41:"net.HUB_CFG0",pin42:"net.HUB_CFG1",pin43:"net.HUB_RESET_N",pin44:"net.HUB_VBUS_SENSE",pin45:"net.HUB_NONREM0",pin46:"net.N3V3_MAIN",pin47:"net.HUB_SWAP3",pin48:"net.HUB_BOOST1",pin49:"net.HUB_SWAP2",pin50:"net.HUB_BOOST0",pin51:"net.HUB_SWAP1",pin52:"net.N3V3_MAIN",pin53:"net.HUB_DIS6_N",pin54:"net.HUB_DIS6_P",pin55:"net.HUB_DIS7_N",pin56:"net.HUB_DIS7_P",pin57:"net.N3V3_MAIN",pin58:"net.UP_HUB_N",pin59:"net.UP_HUB_P",pin60:"net.XTAL2",pin61:"net.XTAL1",pin62:"net.HUB_VDD18PLL",pin63:"net.RBIAS",pin64:"net.N3V3_MAIN",pin65:"net.GND"
      }} />
    <chip name="Y_HUB" supplierPartNumbers={{ jlcpcb: ["C1985204"] }} footprint={<TwoSided pins={4} pitch={1.6} span={3.2} />}
      {...schProps("Y_HUB")}
      pinLabels={{ pin1:"X1",pin2:"GND1",pin3:"X2",pin4:"GND2" }} connections={{ pin1:"net.XTAL1",pin2:"net.GND",pin3:"net.XTAL2",pin4:"net.GND" }} />
    <R name="R_XTAL" value="1M" a="XTAL1" b="XTAL2" jlc="C138033" />
    <R name="R_RBIAS" value="12k" a="RBIAS" b="GND" jlc="C114760" />
    <C name="C_XTAL1" value="18pF" a="XTAL1" b="GND" jlc="C1549" />
    <C name="C_XTAL2" value="18pF" a="XTAL2" b="GND" jlc="C1549" />
    {[1,2,3,4].map(n => <C key={`ha${n}`} name={`C_HUB_A${n}`} value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />)}
    <C name="C_HUB_A_BULK" value="1uF" a="N3V3_MAIN" b="GND" jlc="C52923" />
    <C name="C_HUB_CR_HF" value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />
    <C name="C_HUB_CR_BULK" value="1uF" a="N3V3_MAIN" b="GND" jlc="C52923" />
    <C name="C_HUB_DD" value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />
    <C name="C_HUB_PLL" value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />
    <C name="C_HUB_18" value="1uF" a="HUB_VDD18" b="GND" jlc="C52923" />
    <C name="C_HUB_18PLL" value="1uF" a="HUB_VDD18PLL" b="GND" jlc="C52923" />
    <R name="R_HUB_RESET" value="10k" a="N3V3_MAIN" b="HUB_RESET_N" jlc="C60490" />
    <C name="C_HUB_RESET" value="1uF" a="HUB_RESET_N" b="GND" jlc="C52923" />
    <R name="R_VBUS_TOP" value="100k" a="USB_UP_VBUS" b="HUB_VBUS_SENSE" jlc="C60491" />
    <R name="R_VBUS_BOT" value="100k" a="HUB_VBUS_SENSE" b="GND" jlc="C60491" />
    {[0,1,2].map(n => <R key={`cfg${n}`} name={`R_CFG${n}`} value="10k" a={`HUB_CFG${n}`} b="GND" jlc="C60490" />)}
    <R name="R_NONREM1" value="10k" a="HUB_NONREM1" b="GND" jlc="C60490" />
    <R name="R_NONREM0" value="10k" a="N3V3_MAIN" b="HUB_NONREM0" jlc="C60490" />
    <R name="R_SWAP1" value="100k" a="HUB_SWAP1" b="N3V3_MAIN" jlc="C60491" />
    {[2,3,4,5,6,7].map(n => <R key={`sw${n}`} name={`R_SWAP${n}`} value="100k" a={`HUB_SWAP${n}`} b="GND" jlc="C60491" />)}
    <R name="R_GANG" value="10k" a="HUB_GANG" b="GND" jlc="C60490" />
    <R name="R_BOOST0" value="10k" a="HUB_BOOST0" b="GND" jlc="C60490" />
    <R name="R_BOOST1" value="10k" a="HUB_BOOST1" b="GND" jlc="C60490" />
    <R name="R_DIS6N" value="10k" a="N3V3_MAIN" b="HUB_DIS6_N" jlc="C60490" />
    <R name="R_DIS6P" value="10k" a="N3V3_MAIN" b="HUB_DIS6_P" jlc="C60490" />
    <R name="R_DIS7N" value="10k" a="N3V3_MAIN" b="HUB_DIS7_N" jlc="C60490" />
    <R name="R_DIS7P" value="10k" a="N3V3_MAIN" b="HUB_DIS7_P" jlc="C60490" />
  </group>

  <group name="management_device" pcbX="150mm" pcbY="100mm">
    <Tps2557 name="U_PWR_CTRL" en="HUB_PRTPWR1" out="VBUS_CTRL" fault="HUB_OCS1_N" ilim="ILIM_CTRL"
      cin="C_PWR_CTRL_IN" coutHf="C_PWR_CTRL_OUT_HF" coutBulk="C_PWR_CTRL_OUT" studyX={-12} />
    <chip name="U_CTRL" supplierPartNumbers={{ jlcpcb: ["C640876"] }} footprint={<TwoSided pins={14} pitch={1.27} span={6.2} />}
      {...schProps("U_CTRL")}
      pinLabels={{ pin1:"VDD",pin2:"GP0",pin3:"GP1",pin4:"RST",pin5:"URX",pin6:"UTX",pin7:"GP2",pin8:"GP3",pin9:"SDA",pin10:"SCL",pin11:"VUSB",pin12:"D_MINUS",pin13:"D_PLUS",pin14:"VSS" }}
      connections={{ pin1:"net.VBUS_CTRL",pin4:"net.CTRL_RESET_N",pin9:"net.I2C_SDA",pin10:"net.I2C_SCL",pin11:"net.CTRL_VUSB_3V3",pin12:"net.MGMT_N",pin13:"net.MGMT_P",pin14:"net.GND" }} />
    <C name="C_CTRL_VDD" value="100nF" a="VBUS_CTRL" b="GND" jlc="C1525" />
    <C name="C_CTRL_VUSB" value="330nF" a="CTRL_VUSB_3V3" b="GND" jlc="C19271634" />
    <R name="R_CTRL_RESET" value="10k" a="VBUS_CTRL" b="CTRL_RESET_N" jlc="C60490" />
    <R name="R_I2C_SCL" value="4.7k" a="VBUS_CTRL" b="I2C_SCL" jlc="C105871" />
    <R name="R_I2C_SDA" value="4.7k" a="VBUS_CTRL" b="I2C_SDA" jlc="C105871" />

    <chip name="U_EXP" supplierPartNumbers={{ jlcpcb: ["C558584"] }} footprint={<TwoSided pins={28} pitch={0.65} span={7.2} />}
      {...schProps("U_EXP")}
      pinLabels={{ pin1:"GPB0",pin2:"GPB1",pin3:"GPB2",pin4:"GPB3",pin5:"GPB4",pin6:"GPB5",pin7:"GPB6",pin8:"GPB7",pin9:"VDD",pin10:"VSS",pin11:"NC1",pin12:"SCL",pin13:"SDA",pin14:"NC2",pin15:"A0",pin16:"A1",pin17:"A2",pin18:"RESET_N",pin19:"INTB",pin20:"INTA",pin21:"GPA0",pin22:"GPA1",pin23:"GPA2",pin24:"GPA3",pin25:"GPA4",pin26:"GPA5",pin27:"GPA6",pin28:"GPA7" }}
      connections={{ pin9:"net.VBUS_CTRL",pin10:"net.GND",pin12:"net.I2C_SCL",pin13:"net.I2C_SDA",pin15:"net.GND",pin16:"net.GND",pin17:"net.GND",pin18:"net.EXP_RESET_N",pin21:"net.PWR_CMD1",pin22:"net.PWR_CMD2",pin23:"net.PWR_CMD3",pin24:"net.PWR_CMD4",pin25:"net.DATA_CMD1",pin26:"net.DATA_CMD2",pin27:"net.DATA_CMD3",pin28:"net.DATA_CMD4" }} />
    <C name="C_EXP_VDD" value="100nF" a="VBUS_CTRL" b="GND" jlc="C1525" studyX={12} studyY={0} />
    <R name="R_EXP_RESET" value="10k" a="VBUS_CTRL" b="EXP_RESET_N" jlc="C60490" />
    {[1,2,3,4].map(n => <R key={`pc${n}`} name={`R_PWR_CMD${n}`} value="10k" a={`PWR_CMD${n}`} b="GND" jlc="C60490" />)}
    {[1,2,3,4].map(n => <R key={`dc${n}`} name={`R_DATA_CMD${n}`} value="10k" a={`DATA_CMD${n}`} b="GND" jlc="C60490" />)}
  </group>

  <group name="hardware_interlocks" pcbX="150mm" pcbY="0mm">
    <chip name="U_AND_PWR" supplierPartNumbers={{ jlcpcb: ["C6053"] }} footprint={<TwoSided pins={14} />}
      {...schProps("U_AND_PWR")}
      pinLabels={{ pin1:"1A",pin2:"1B",pin3:"1Y",pin4:"2A",pin5:"2B",pin6:"2Y",pin7:"GND",pin8:"3Y",pin9:"3A",pin10:"3B",pin11:"4Y",pin12:"4A",pin13:"4B",pin14:"VCC" }}
      connections={{ pin1:"net.HUB_PRTPWR2",pin2:"net.PWR_CMD1",pin3:"net.PWR_EN1",pin4:"net.HUB_PRTPWR3",pin5:"net.PWR_CMD2",pin6:"net.PWR_EN2",pin7:"net.GND",pin8:"net.PWR_EN3",pin9:"net.HUB_PRTPWR4",pin10:"net.PWR_CMD3",pin11:"net.PWR_EN4",pin12:"net.HUB_PRTPWR5",pin13:"net.PWR_CMD4",pin14:"net.N3V3_MAIN" }} />
    <C name="C_AND_PWR" value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />
    <chip name="U_AND_DATA" supplierPartNumbers={{ jlcpcb: ["C6053"] }} footprint={<TwoSided pins={14} />}
      {...schProps("U_AND_DATA")}
      pinLabels={{ pin1:"1A",pin2:"1B",pin3:"1Y",pin4:"2A",pin5:"2B",pin6:"2Y",pin7:"GND",pin8:"3Y",pin9:"3A",pin10:"3B",pin11:"4Y",pin12:"4A",pin13:"4B",pin14:"VCC" }}
      connections={{ pin1:"net.PWR_EN1",pin2:"net.DATA_CMD1",pin3:"net.DATA_OK1",pin4:"net.PWR_EN2",pin5:"net.DATA_CMD2",pin6:"net.DATA_OK2",pin7:"net.GND",pin8:"net.DATA_OK3",pin9:"net.PWR_EN3",pin10:"net.DATA_CMD3",pin11:"net.DATA_OK4",pin12:"net.PWR_EN4",pin13:"net.DATA_CMD4",pin14:"net.N3V3_MAIN" }} />
    <C name="C_AND_DATA" value="100nF" a="N3V3_MAIN" b="GND" jlc="C1525" />
  </group>

  {/* Human-readback notes distinguish deliberate no-connects from omissions.
      These are presentation-only and do not create nets or copper. */}
  <group name="hub_intentional_nc_note" schSheetName="hub">
    <schematictext schX="0mm" schY="-13mm" anchor="center" fontSize={0.65}
      text="INTENTIONAL NC: U_HUB LED/TEST and disabled-port 6/7 PWR/OCS pins." />
  </group>
  <group name="management_intentional_nc_note" schSheetName="management">
    <schematictext schX="0mm" schY="-14mm" anchor="center" fontSize={0.65}
      text="INTENTIONAL NC: unused U_CTRL GPIO/UART; U_EXP GPB/INT/NC pins." />
  </group>

  <ExternalPort p={1} hubP="P1_HUB_P" hubN="P1_HUB_N" prtPwr="HUB_PRTPWR2" ocs="HUB_OCS2_N" />
  <ExternalPort p={2} hubP="P2_HUB_P" hubN="P2_HUB_N" prtPwr="HUB_PRTPWR3" ocs="HUB_OCS3_N" />
  <ExternalPort p={3} hubP="P3_HUB_P" hubN="P3_HUB_N" prtPwr="HUB_PRTPWR4" ocs="HUB_OCS4_N" />
  <ExternalPort p={4} hubP="P4_HUB_P" hubN="P4_HUB_N" prtPwr="HUB_PRTPWR5" ocs="HUB_OCS5_N" />

  {/* Presentation-only boundary labels for parallel power lands. Without an
      explicit label, circuit-to-svg joins same-net pins into an anonymous loop,
      which is electrically correct but not reviewable by a human. These labels
      add no new source trace or copper; every selected pin already owns the net. */}
  <group name="buck_input_label" schSheetName="power">
    <netlabel net="P5V_PROTECTED" connectsTo={sel.U_BUCK.pin3}
      schX="-5.7mm" schY="-5.3mm" anchorSide="right" />
  </group>
  <group name="control_power_input_label" schSheetName="management">
    <netlabel net="P5V_PROTECTED" connectsTo={sel.U_PWR_CTRL.pin2}
      schX="-10.0mm" schY="2.95mm" anchorSide="right" />
    <netlabel net="P5V_PROTECTED" connectsTo={sel.U_PWR_CTRL.pin3}
      schX="-10.0mm" schY="2.75mm" anchorSide="right" />
    <netlabel net="GND" connectsTo={sel.U_PWR_CTRL.pin1}
      schX="-8.5mm" schY="3.15mm" anchorSide="right" />
  </group>
  <group name="control_power_output_label" schSheetName="management">
    <netlabel net="VBUS_CTRL" connectsTo={sel.U_PWR_CTRL.pin7}
      schX="-2.0mm" schY="2.95mm" anchorSide="left" />
    <netlabel net="VBUS_CTRL" connectsTo={sel.U_PWR_CTRL.pin6}
      schX="-2.0mm" schY="2.75mm" anchorSide="left" />
    <netlabel net="GND" connectsTo={sel.U_PWR_CTRL.pin9}
      schX="-3.5mm" schY="3.15mm" anchorSide="left" />
  </group>
  {[1, 2, 3, 4].map((p) => <group key={`port_power_labels_${p}`}
      name={`port_power_labels_${p}`} schSheetName={`port_${p}`}>
    <netlabel net="P5V_PROTECTED" connectsTo={sel[`U_PWR${p}`].pin2}
      schX="-5.2mm" schY="-3.2mm" anchorSide="right" />
    <netlabel net={`VBUS${p}_SW`} connectsTo={sel[`U_PWR${p}`].pin7}
      schX="0.7mm" schY="-3.2mm" anchorSide="left" />
  </group>)}
</board>

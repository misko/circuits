// Programmable four-port USB 2.0 hub. The source contains only the selected
// architecture; superseded battery/Pi and LM5116 implementations are retained
// in historical release evidence, never as live generator code.

const Dfn56 = () => (
  <footprint>
    <smtpad portHints={["1"]} pcbX="-1.905mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["2"]} pcbX="-0.635mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["3"]} pcbX="0.635mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["4"]} pcbX="1.905mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["5"]} pcbX="1.905mm" pcbY="2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["6"]} pcbX="0.635mm" pcbY="2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["7"]} pcbX="-0.635mm" pcbY="2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["8"]} pcbX="-1.905mm" pcbY="2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
  </footprint>
)

const Pol2 = ({ w, h, dx }: { w: string; h: string; dx: string }) => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={`-${dx}`} pcbY="0mm" width={w} height={h} shape="rect" />
    <smtpad portHints={["2"]} pcbX={dx} pcbY="0mm" width={w} height={h} shape="rect" />
  </footprint>
)

// ---- selected programmable-hub implementation ----
const TwoSided = ({ pins, pitch = 0.5, span = 5 }: { pins: number; pitch?: number; span?: number }) => {
  const half = Math.ceil(pins / 2)
  return (
    <footprint>
      {Array.from({ length: half }, (_, i) => (
        <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX={`${-span / 2}mm`}
          pcbY={`${((half - 1) / 2 - i) * pitch}mm`} width="1mm" height={`${Math.min(0.32, pitch * 0.58)}mm`} shape="rect" />
      ))}
      {Array.from({ length: pins - half }, (_, i) => (
        <smtpad key={`r${i}`} portHints={[`${half + i + 1}`]} pcbX={`${span / 2}mm`}
          pcbY={`${(-(pins - half - 1) / 2 + i) * pitch}mm`} width="1mm" height={`${Math.min(0.32, pitch * 0.58)}mm`} shape="rect" />
      ))}
    </footprint>
  )
}

const Qfn64Ep = () => (
  <footprint>
    {Array.from({ length: 16 }, (_, i) => <smtpad key={`b${i}`} portHints={[`${i + 1}`]} pcbX={`${(-3.75 + i * 0.5)}mm`} pcbY="-4.5mm" width="0.28mm" height="1mm" shape="rect" />)}
    {Array.from({ length: 16 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${i + 17}`]} pcbX="4.5mm" pcbY={`${(-3.75 + i * 0.5)}mm`} width="1mm" height="0.28mm" shape="rect" />)}
    {Array.from({ length: 16 }, (_, i) => <smtpad key={`t${i}`} portHints={[`${i + 33}`]} pcbX={`${(3.75 - i * 0.5)}mm`} pcbY="4.5mm" width="0.28mm" height="1mm" shape="rect" />)}
    {Array.from({ length: 16 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 49}`]} pcbX="-4.5mm" pcbY={`${(3.75 - i * 0.5)}mm`} width="1mm" height="0.28mm" shape="rect" />)}
    <smtpad portHints={["65"]} pcbX="0mm" pcbY="0mm" width="4.7mm" height="4.7mm" shape="rect" />
  </footprint>
)

const PowerS08 = () => (
  <footprint>
    {Array.from({ length: 4 }, (_, i) => <smtpad key={`s${i}`} portHints={[`${i + 1}`]} pcbX="-2.4mm" pcbY={`${(1.905 - i * 1.27)}mm`} width="1.2mm" height="0.7mm" shape="rect" />)}
    {Array.from({ length: 4 }, (_, i) => <smtpad key={`d${i}`} portHints={[`${i + 5}`]} pcbX="2.4mm" pcbY={`${(-1.905 + i * 1.27)}mm`} width="1.2mm" height="0.7mm" shape="rect" />)}
  </footprint>
)

const Wson13 = () => (
  <footprint>
    {Array.from({ length: 6 }, (_, i) => <smtpad key={`wl${i}`} portHints={[`${i + 1}`]} pcbX="-1.7mm" pcbY={`${(1.25 - i * 0.5)}mm`} width="1mm" height="0.28mm" shape="rect" />)}
    {Array.from({ length: 6 }, (_, i) => <smtpad key={`wr${i}`} portHints={[`${i + 7}`]} pcbX="1.7mm" pcbY={`${(-1.25 + i * 0.5)}mm`} width="1mm" height="0.28mm" shape="rect" />)}
    <smtpad portHints={["13"]} pcbX="0mm" pcbY="0mm" width="1.5mm" height="2.5mm" shape="rect" />
  </footprint>
)

const UsbB = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="-3.75mm" pcbY="2.5mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="-1.25mm" pcbY="2.5mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
    <platedhole portHints={["3"]} pcbX="1.25mm" pcbY="2.5mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
    <platedhole portHints={["4"]} pcbX="3.75mm" pcbY="2.5mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
    <platedhole portHints={["5", "SH"]} pcbX="-6mm" pcbY="-1mm" outerDiameter="3.2mm" holeDiameter="2.3mm" shape="circle" />
  </footprint>
)

const UsbA3A = () => (
  <footprint>
    {Array.from({ length: 4 }, (_, i) => <platedhole key={`p${i}`} portHints={[`${i + 1}`]}
      pcbX={`${(-3 + i * 2)}mm`} pcbY="3.5mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />)}
    <platedhole portHints={["5", "SH"]} pcbX="-3.5mm" pcbY="-1mm" outerDiameter="3.4mm" holeDiameter="2.26mm" shape="circle" />
  </footprint>
)

const InputTerminal = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="-2.5mm" pcbY="0mm" outerDiameter="3mm" holeDiameter="1.5mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="2.5mm" pcbY="0mm" outerDiameter="3mm" holeDiameter="1.5mm" shape="circle" />
  </footprint>
)

const BladeFuse = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="-4.95mm" pcbY="-2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
    <platedhole portHints={["1"]} pcbX="-4.95mm" pcbY="2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="4.95mm" pcbY="-2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="4.95mm" pcbY="2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  </footprint>
)

const Header2x5 = () => (
  <footprint>
    {Array.from({ length: 10 }, (_, i) => <platedhole key={`h${i}`} portHints={[`${i + 1}`]}
      pcbX={`${i % 2 ? 0.635 : -0.635}mm`} pcbY={`${(2 - Math.floor(i / 2)) * 1.27}mm`}
      outerDiameter="0.9mm" holeDiameter="0.5mm" shape="circle" />)}
  </footprint>
)

const Ltc3889Fp = () => {
  const missing = new Set([3, 37, 41, 45, 49, 51])
  const pads: any[] = []
  for (let p = 1; p <= 52; p++) {
    if (missing.has(p)) continue
    const side = Math.floor((p - 1) / 13), i = (p - 1) % 13, d = -3 + i * 0.5
    if (side === 0) pads.push(<smtpad key={`u${p}`} portHints={[`${p}`]} pcbX={`${d}mm`} pcbY="-4.4mm" width="0.28mm" height="1mm" shape="rect" />)
    if (side === 1) pads.push(<smtpad key={`u${p}`} portHints={[`${p}`]} pcbX="3.9mm" pcbY={`${d}mm`} width="1mm" height="0.28mm" shape="rect" />)
    if (side === 2) pads.push(<smtpad key={`u${p}`} portHints={[`${p}`]} pcbX={`${-d}mm`} pcbY="4.4mm" width="0.28mm" height="1mm" shape="rect" />)
    if (side === 3) pads.push(<smtpad key={`u${p}`} portHints={[`${p}`]} pcbX="-3.9mm" pcbY={`${-d}mm`} width="1mm" height="0.28mm" shape="rect" />)
  }
  return <footprint>{pads}<smtpad portHints={["53"]} pcbX="0mm" pcbY="0mm" width="5.6mm" height="4.6mm" shape="rect" /></footprint>
}

const Tps25983Fp = () => <footprint>
  {Array.from({ length: 6 }, (_, i) => <smtpad key={`el${i}`} portHints={[`${i + 1}`]} pcbX="-2.2125mm" pcbY={`${-1.25 + i * 0.5}mm`} width="0.575mm" height="0.24mm" shape="rect" />)}
  {Array.from({ length: 6 }, (_, i) => <smtpad key={`eb${i}`} portHints={[`${i + 7}`]} pcbX={`${-1.25 + i * 0.5}mm`} pcbY="2.2125mm" width="0.24mm" height="0.575mm" shape="rect" />)}
  {Array.from({ length: 6 }, (_, i) => <smtpad key={`er${i}`} portHints={[`${i + 13}`]} pcbX="2.2125mm" pcbY={`${1.25 - i * 0.5}mm`} width="0.575mm" height="0.24mm" shape="rect" />)}
  {Array.from({ length: 6 }, (_, i) => <smtpad key={`et${i}`} portHints={[`${i + 19}`]} pcbX={`${1.25 - i * 0.5}mm`} pcbY="-2.2125mm" width="0.24mm" height="0.575mm" shape="rect" />)}
  <smtpad portHints={["25"]} pcbX="0mm" pcbY="-0.8mm" width="2.7mm" height="1.45mm" shape="rect" />
  <smtpad portHints={["26"]} pcbX="0mm" pcbY="0.5mm" width="2.7mm" height="0.85mm" shape="rect" />
</footprint>

const R2 = ({ name, value, a, b, fp = "0603", jlc }: any) =>
  <resistor name={name} resistance={value} footprint={fp}
    {...(jlc ? { supplierPartNumbers: { jlcpcb: [jlc] } } : {})}
    connections={{ pin1: `net.${a}`, pin2: `net.${b}` }} />
const C2 = ({ name, value, a, b, fp = "0603" }: any) =>
  <capacitor name={name} capacitance={value} footprint={fp} connections={{ pin1: `net.${a}`, pin2: `net.${b}` }} />

// TI RDL0020A B3QFN-20 render land. Fabrication uses the exact dossier FPID.
const Tpsm63606Fp = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-2.25mm" pcbY="-2.25mm" width="1.4mm" height="1mm" shape="rect" />
  {Array.from({ length: 6 }, (_, i) => <smtpad key={`ml${i}`} portHints={[`${i + 2}`]} pcbX="-2.25mm" pcbY={`${-1.25 + i * 0.5}mm`} width="0.9mm" height="0.25mm" shape="rect" />)}
  <smtpad portHints={["8"]} pcbX="-2.25mm" pcbY="2.25mm" width="1.4mm" height="1mm" shape="rect" />
  <smtpad portHints={["9"]} pcbX="2.25mm" pcbY="2.25mm" width="1.4mm" height="1mm" shape="rect" />
  {Array.from({ length: 6 }, (_, i) => <smtpad key={`mr${i}`} portHints={[`${10 + i}`]} pcbX="2.25mm" pcbY={`${1.25 - i * 0.5}mm`} width="0.9mm" height="0.25mm" shape="rect" />)}
  <smtpad portHints={["16"]} pcbX="2.25mm" pcbY="-2.25mm" width="1.4mm" height="1mm" shape="rect" />
  {[17, 18, 19, 20].map((p, i) => <smtpad key={`mep${p}`} portHints={[`${p}`]} pcbX="0mm" pcbY={`${-1.6125 + i * 1.075}mm`} width="1.58mm" height="0.875mm" shape="rect" />)}
</footprint>

const Buck = ({ s, vout, vin = "VIN_PROTECTED", ids }: any) => {
  const n = (x: string) => `net.${x}_${s}`
  return <group name={`buck${s}`}>
    <chip name={ids.U} supplierPartNumbers={{ jlcpcb: ["C5219325"] }}
      pinLabels={{ pin1: "VIN1", pin2: "SW_NC", pin3: "CBOOT", pin4: "RBOOT", pin5: "VLDOIN", pin6: "AGND1", pin7: "VCC_NC", pin8: "VOUT1", pin9: "VOUT2", pin10: "FB", pin11: "AGND2", pin12: "RT", pin13: "PG_NC", pin14: "EN_SYNC", pin15: "NC", pin16: "VIN2", pin17: "PGND1", pin18: "PGND2", pin19: "PGND3", pin20: "PGND4" }}
      connections={{ pin1: `net.${vin}`, pin3: n("BOOT_CTL"), pin4: n("BOOT_CTL"), pin5: `net.${vout}`, pin6: "net.GND", pin8: `net.${vout}`, pin9: `net.${vout}`, pin10: n("FB"), pin11: "net.GND", pin12: n("RT"), pin14: `net.${vin}`, pin16: `net.${vin}`, pin17: "net.GND", pin18: "net.GND", pin19: "net.GND", pin20: "net.GND" }}
      footprint={<Tpsm63606Fp />} />
    {ids.CIN.map((c: string) => <capacitor key={c} name={c} capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C3844168"] }} connections={{ pin1: `net.${vin}`, pin2: "net.GND" }} />)}
    {ids.COUT.map((c: string) => <capacitor key={c} name={c} capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C23742"] }} connections={{ pin1: `net.${vout}`, pin2: "net.GND" }} />)}
    <resistor name={ids.RT} resistance="13k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C22797"] }} connections={{ pin1: n("RT"), pin2: "net.GND" }} />
    <resistor name={ids.FBT} resistance="4.12k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C2984354"] }} connections={{ pin1: `net.${vout}`, pin2: n("FBTOP") }} />
    <resistor name={ids.FBTRIM} resistance="30" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C128060"] }} connections={{ pin1: n("FBTOP"), pin2: n("FB") }} />
    <resistor name={ids.FBB} resistance="1k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C110776"] }} connections={{ pin1: n("FB"), pin2: "net.GND" }} />
    <capacitor name={ids.CFF} capacitance="22pF" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C1653"] }} connections={{ pin1: `net.${vout}`, pin2: n("FB") }} />
  </group>
}

const PowerMosfet = ({ name, source, gate, drain, part = "C454269" }: any) =>
  <chip name={name} supplierPartNumbers={{ jlcpcb: [part] }}
    pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D5", pin6: "D6", pin7: "D7", pin8: "D8" }}
    connections={{ pin1: `net.${source}`, pin2: `net.${source}`, pin3: `net.${source}`, pin4: `net.${gate}`, pin5: `net.${drain}`, pin6: `net.${drain}`, pin7: `net.${drain}`, pin8: `net.${drain}` }}
    footprint={<Dfn56 />} />

const DualBuckPower = () => (
  <group name="dual_buck_power">
    <chip name="U2" supplierPartNumbers={{ jlcpcb: ["LTC3889IUKG#PBF"] }} footprint={<Ltc3889Fp />}
      pinLabels={{
        pin1: "SW0", pin2: "TG0", pin3: "NC", pin4: "ISENSE0_P", pin5: "ISENSE0_N", pin6: "TSNS0", pin7: "VSENSE0_P", pin8: "VSENSE0_N",
        pin9: "ISENSE1_P", pin10: "ISENSE1_N", pin11: "ITHR0", pin12: "ITH0", pin13: "SYNC", pin14: "SCL", pin15: "SDA", pin16: "ALERT_N",
        pin17: "FAULT0_N", pin18: "FAULT1_N", pin19: "RUN0", pin20: "RUN1", pin21: "ASEL0", pin22: "ASEL1", pin23: "VOUT0_CFG", pin24: "VOUT1_CFG",
        pin25: "FREQ_CFG", pin26: "PHAS_CFG", pin27: "VDD25", pin28: "WP", pin29: "SHARE_CLK", pin30: "VDD33", pin31: "ITH1", pin32: "ITHR1",
        pin33: "PGOOD1", pin34: "PGOOD0", pin35: "VSENSE1_P", pin36: "TSNS1", pin37: "NC", pin38: "TG1", pin39: "SW1", pin40: "BOOST1",
        pin41: "NC", pin42: "BG1", pin43: "EXTVCC", pin44: "DRVCC", pin45: "NC", pin46: "IIN_N", pin47: "IIN_P", pin48: "VIN", pin49: "NC",
        pin50: "BG0", pin51: "NC", pin52: "BOOST0", pin53: "EP_GND",
      }}
      connections={{
        pin1: "net.SW_A", pin2: "net.TG_A", pin4: "net.ISNS_A_PF", pin5: "net.ISNS_A_NF", pin6: "net.TSNS_A", pin7: "net.N5V_A", pin8: "net.GND",
        pin9: "net.ISNS_B_PF", pin10: "net.ISNS_B_NF", pin11: "net.ITHR_A", pin12: "net.ITH_A", pin13: "net.LTC_SYNC", pin14: "net.HUB_SCL",
        pin15: "net.HUB_SDA", pin16: "net.LTC_ALERT_N", pin17: "net.LTC_FAULT_N", pin18: "net.LTC_FAULT_N", pin19: "net.RUN_A", pin20: "net.RUN_B",
        pin21: "net.GND", pin22: "net.GND", pin25: "net.FREQ_CFG", pin26: "net.GND", pin27: "net.VDD25", pin28: "net.GND", pin29: "net.SHARE_CLK",
        pin30: "net.N3V3_LOGIC", pin31: "net.ITH_B", pin32: "net.ITHR_B", pin33: "net.PGOOD_B_N", pin34: "net.PGOOD_A_N", pin35: "net.N5V_B",
        pin36: "net.TSNS_B", pin38: "net.TG_B", pin39: "net.SW_B", pin40: "net.BOOST_B", pin42: "net.BG_B", pin43: "net.AUX_6V",
        pin44: "net.DRVCC", pin46: "net.VIN_PROTECTED", pin47: "net.VIN_PROTECTED", pin48: "net.VIN_PROTECTED", pin50: "net.BG_A", pin52: "net.BOOST_A", pin53: "net.GND",
      }} />

    <PowerMosfet name="Q3" source="SW_A" gate="TG_A" drain="VIN_PROTECTED" />
    <PowerMosfet name="Q4" source="GND" gate="BG_A" drain="SW_A" />
    <PowerMosfet name="Q5" source="SW_B" gate="TG_B" drain="VIN_PROTECTED" />
    <PowerMosfet name="Q6" source="GND" gate="BG_B" drain="SW_B" />
    <inductor name="L1" inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }} connections={{ pin1: "net.SW_A", pin2: "net.SENSE_A" }} footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
    <inductor name="L2" inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }} connections={{ pin1: "net.SW_A", pin2: "net.SENSE_A" }} footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
    <inductor name="L4" inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }} connections={{ pin1: "net.SW_B", pin2: "net.SENSE_B" }} footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
    <inductor name="L5" inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }} connections={{ pin1: "net.SW_B", pin2: "net.SENSE_B" }} footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
    <R2 name="R14" value="0.01" a="SENSE_A" b="N5V_A" fp="2512" jlc="C844901" />
    <R2 name="R15" value="0.01" a="SENSE_A" b="N5V_A" fp="2512" jlc="C844901" />
    <R2 name="R16" value="0.01" a="SENSE_B" b="N5V_B" fp="2512" jlc="C844901" />
    <R2 name="R17" value="0.01" a="SENSE_B" b="N5V_B" fp="2512" jlc="C844901" />
    <R2 name="R6" value="30" a="SENSE_A" b="ISNS_A_PF" />
    <R2 name="R7" value="30" a="N5V_A" b="ISNS_A_NF" />
    <R2 name="R8" value="30" a="SENSE_B" b="ISNS_B_PF" />
    <R2 name="R9" value="30" a="N5V_B" b="ISNS_B_NF" />
    <C2 name="C4" value="1nF" a="ISNS_A_PF" b="ISNS_A_NF" />
    <C2 name="C5" value="1nF" a="ISNS_B_PF" b="ISNS_B_NF" />

    <chip name="D2" supplierPartNumbers={{ jlcpcb: ["C2128"] }} pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: "net.BOOST_A", pin2: "net.DRVCC" }} footprint={<Pol2 w="0.6mm" h="1mm" dx="1.25mm" />} />
    <chip name="D3" supplierPartNumbers={{ jlcpcb: ["C2128"] }} pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: "net.BOOST_B", pin2: "net.DRVCC" }} footprint={<Pol2 w="0.6mm" h="1mm" dx="1.25mm" />} />
    <C2 name="C7" value="330nF" a="BOOST_A" b="SW_A" />
    <C2 name="C8" value="330nF" a="BOOST_B" b="SW_B" />
    {[9, 10, 11, 12].map((n) => <C2 key={`vin${n}`} name={`C${n}`} value="10uF" a="VIN_PROTECTED" b="GND" fp="1210" />)}
    <C2 name="C13" value="4.7uF" a="DRVCC" b="GND" />
    <C2 name="C14" value="4.7uF" a="AUX_6V" b="GND" />
    <C2 name="C15" value="1uF" a="VDD25" b="GND" />
    <C2 name="C16" value="1uF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C17" value="4.7nF" a="ITH_A" b="GND" />
    <C2 name="C18" value="100pF" a="ITHR_A" b="GND" />
    <C2 name="C19" value="4.7nF" a="ITH_B" b="GND" />
    <C2 name="C20" value="100pF" a="ITHR_B" b="GND" />
    <C2 name="C25" value="10nF" a="TSNS_A" b="GND" />
    <C2 name="C26" value="10nF" a="TSNS_B" b="GND" />
    {[101, 102, 103, 104].map((n) => <C2 key={`oa${n}`} name={`C${n}`} value="100uF" a="N5V_A" b="GND" fp="1210" />)}
    {[105, 106, 107, 108].map((n) => <C2 key={`ob${n}`} name={`C${n}`} value="100uF" a="N5V_B" b="GND" fp="1210" />)}

    <R2 name="R12" value="10k" a="N3V3_LOGIC" b="LTC_ALERT_N" />
    <R2 name="R13" value="10k" a="N3V3_LOGIC" b="LTC_FAULT_N" />
    <R2 name="R18" value="10k" a="N3V3_LOGIC" b="RUN_A" />
    <R2 name="R19" value="10k" a="N3V3_LOGIC" b="RUN_B" />
    <R2 name="R20" value="24.9k" a="VDD25" b="FREQ_CFG" />
    <R2 name="R21" value="9.09k" a="FREQ_CFG" b="GND" />
    <R2 name="R22" value="100k" a="N3V3_LOGIC" b="RUN_A_HOLD" />
    <R2 name="R23" value="100k" a="N3V3_LOGIC" b="RUN_B_HOLD" />
    <R2 name="R24" value="10k" a="N3V3_LOGIC" b="SHARE_CLK" />
    <R2 name="R25" value="10k" a="N3V3_LOGIC" b="PGOOD_A_N" />
    <R2 name="R26" value="10k" a="N3V3_LOGIC" b="PGOOD_B_N" />
    <R2 name="R27" value="5k" a="N3V3_LOGIC" b="LTC_SYNC" />
    <chip name="Q7" supplierPartNumbers={{ jlcpcb: ["C85047"] }} pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }} connections={{ pin1: "net.RUN_A_HOLD", pin2: "net.GND", pin3: "net.RUN_A" }} footprint="sot23" />
    <chip name="Q8" supplierPartNumbers={{ jlcpcb: ["C85047"] }} pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }} connections={{ pin1: "net.RUN_B_HOLD", pin2: "net.GND", pin3: "net.RUN_B" }} footprint="sot23" />
    <chip name="Q21" supplierPartNumbers={{ jlcpcb: ["MMBT3906LT1G"] }} pinLabels={{ pin1: "B", pin2: "E", pin3: "C" }} connections={{ pin1: "net.GND", pin2: "net.TSNS_A", pin3: "net.GND" }} footprint="sot23" />
    <chip name="Q22" supplierPartNumbers={{ jlcpcb: ["MMBT3906LT1G"] }} pinLabels={{ pin1: "B", pin2: "E", pin3: "C" }} connections={{ pin1: "net.GND", pin2: "net.TSNS_B", pin3: "net.GND" }} footprint="sot23" />
  </group>
)

const AuxPower = () => (
  <group name="auxiliary_power">
    <chip name="U3" supplierPartNumbers={{ jlcpcb: ["C1858394"] }}
      pinLabels={{ pin1: "PGND", pin2: "VIN", pin3: "EN", pin4: "PG", pin5: "FB", pin6: "VCC", pin7: "BOOT", pin8: "SW", pin9: "EP" }}
      connections={{ pin1: "net.GND", pin2: "net.VIN_PROTECTED", pin3: "net.VIN_PROTECTED", pin4: "net.AUX_PG_N", pin5: "net.AUX_FB", pin6: "net.AUX_VCC", pin7: "net.AUX_BOOT", pin8: "net.AUX_SW", pin9: "net.GND" }}
      footprint={<TwoSided pins={9} pitch={1.27} span={5.5} />} />
    <inductor name="L6" inductance="33uH" supplierPartNumbers={{ jlcpcb: ["C2045462"] }} connections={{ pin1: "net.AUX_SW", pin2: "net.AUX_6V" }} footprint={<Pol2 w="3.5mm" h="12mm" dx="4.95mm" />} />
    <R2 name="R200" value="100k" a="AUX_6V" b="AUX_FB" />
    <R2 name="R201" value="20k" a="AUX_FB" b="GND" />
    <R2 name="R202" value="10k" a="N3V3_LOGIC" b="AUX_PG_N" />
    <C2 name="C200" value="2.2uF" a="VIN_PROTECTED" b="GND" fp="1210" />
    <C2 name="C201" value="220nF" a="VIN_PROTECTED" b="GND" />
    <C2 name="C202" value="22uF" a="AUX_6V" b="GND" fp="1210" />
    <C2 name="C203" value="22uF" a="AUX_6V" b="GND" fp="1210" />
    <C2 name="C204" value="22uF" a="AUX_6V" b="GND" fp="1210" />
    <C2 name="C205" value="1uF" a="AUX_VCC" b="GND" />
    <C2 name="C206" value="100nF" a="AUX_BOOT" b="AUX_SW" />
  </group>
)

const RetiredPortCell = ({ p, efuse, blocker, mux, esd, jack, rail, adcV, adcI }: any) => {
  const N = (s: string) => `P${p}_${s}`
  const b = 400 + p * 20
  const out = N("EFUSE_OUT"), vbus = N("VBUS")
  return <group name={`port${p}`}>
    <chip name={efuse} supplierPartNumbers={{ jlcpcb: ["C20607218"] }} footprint={<Tps25983Fp />}
      pinLabels={{ pin1:"IN1",pin2:"IN2",pin3:"IN3",pin4:"GND4",pin5:"GND5",pin6:"EN_UVLO",pin7:"ITIMER",pin8:"ILIM",pin9:"IMON",pin10:"RETRY_DLY",pin11:"NRETRY",pin12:"OVLO",pin13:"PG",pin14:"GND14",pin15:"BGATE",pin16:"IN16",pin17:"OUT17",pin18:"OUT18",pin19:"OUT19",pin20:"OUT20",pin21:"OUT21",pin22:"OUT22",pin23:"OUT23",pin24:"OUT24",pin25:"EP_IN",pin26:"EP_GND" }}
      connections={{ pin1:`net.${rail}`,pin2:`net.${rail}`,pin3:`net.${rail}`,pin4:"net.GND",pin5:"net.GND",pin6:`net.${N("PWR_EN")}`,pin7:`net.${N("ITIMER")}`,pin8:`net.${N("ILIM")}`,pin9:`net.${N("IMON_RAW")}`,pin10:"net.GND",pin11:"net.GND",pin12:"net.GND",pin13:`net.${N("FLT_N")}`,pin14:"net.GND",pin15:`net.${N("BGATE_DRV")}`,pin16:`net.${rail}`,pin17:`net.${out}`,pin18:`net.${out}`,pin19:`net.${out}`,pin20:`net.${out}`,pin21:`net.${out}`,pin22:`net.${out}`,pin23:`net.${out}`,pin24:`net.${out}`,pin25:`net.${rail}`,pin26:"net.GND" }} />
    <chip name={blocker} supplierPartNumbers={{ jlcpcb: ["C404363"] }} footprint={<PowerS08 />}
      pinLabels={{pin1:"S1",pin2:"S2",pin3:"S3",pin4:"G",pin5:"D5",pin6:"D6",pin7:"D7",pin8:"D8"}}
      connections={{pin1:`net.${out}`,pin2:`net.${out}`,pin3:`net.${out}`,pin4:`net.${N("BLOCK_GATE")}`,pin5:`net.${vbus}`,pin6:`net.${vbus}`,pin7:`net.${vbus}`,pin8:`net.${vbus}`}} />
    <R2 name={`R${b}`} value="100k" a={N("PWR_EN")} b="GND" />
    <R2 name={`R${b+1}`} value="10k" a="N3V3_LOGIC" b={N("FLT_N")} />
    <R2 name={`R${b+2}`} value="300" a={N("ILIM")} b="GND" />
    <R2 name={`R${b+3}`} value="2.15k" a={N("IMON_RAW")} b="GND" />
    <R2 name={`R${b+4}`} value="1k" a={N("IMON_RAW")} b={adcI} />
    <R2 name={`R${b+5}`} value="100k" a={vbus} b={N("VBUS_SENSE")} />
    <R2 name={`R${b+6}`} value="68k" a={N("VBUS_SENSE")} b="GND" />
    <R2 name={`R${b+7}`} value="1k" a={N("VBUS_SENSE")} b={adcV} />
    <R2 name={`R${b+8}`} value="10" a={N("BGATE_DRV")} b={N("BLOCK_GATE")} />
    <R2 name={`R${b+9}`} value="10k" a="N3V3_LOGIC" b={N("DATA_ISO")} />
    <C2 name={`C${b}`} value="2.2nF" a={N("ITIMER")} b="GND" />
    <C2 name={`C${b+1}`} value="100nF" a={rail} b="GND" />
    <C2 name={`C${b+2}`} value="22uF" a={vbus} b="GND" fp="1210" />
    <C2 name={`C${b+3}`} value="100nF" a={vbus} b="GND" />
    <C2 name={`C${b+4}`} value="100nF" a={adcI} b="GND" />
    <C2 name={`C${b+5}`} value="100nF" a={adcV} b="GND" />
    <chip name={`D${p+3}`} supplierPartNumbers={{jlcpcb:["C85098"]}} pinLabels={{pin1:"K",pin2:"A"}} connections={{pin1:`net.${vbus}`,pin2:"net.GND"}} footprint={<Pol2 w="2mm" h="2.3mm" dx="2.4mm"/>}/>
    <chip name={mux} supplierPartNumbers={{jlcpcb:["C11355"]}} footprint={<TwoSided pins={10} pitch={0.5} span={3.4}/>}
      pinLabels={{pin1:"VCC",pin2:"SEL",pin3:"D_PLUS",pin4:"D_MINUS",pin5:"GND",pin6:"HSD1_MINUS",pin7:"HSD1_PLUS",pin8:"HSD2_MINUS",pin9:"HSD2_PLUS",pin10:"OE"}}
      connections={{pin1:"net.N3V3_LOGIC",pin2:"net.GND",pin3:`net.${N("HUB_P")}`,pin4:`net.${N("HUB_N")}`,pin5:"net.GND",pin6:`net.${N("PORT_N")}`,pin7:`net.${N("PORT_P")}`,pin10:`net.${N("DATA_ISO")}`}}/>
    <C2 name={`C${b+6}`} value="100nF" a="N3V3_LOGIC" b="GND"/>
    <chip name={esd} supplierPartNumbers={{jlcpcb:["C7519"]}} footprint="sot23_6" pinLabels={{pin1:"IO1",pin2:"GND",pin3:"IO2",pin4:"IO2B",pin5:"VBUS",pin6:"IO1B"}} connections={{pin1:`net.${N("PORT_P")}`,pin2:"net.GND",pin3:`net.${N("PORT_N")}`,pin4:`net.${N("CONN_N")}`,pin5:`net.${vbus}`,pin6:`net.${N("CONN_P")}`}}/>
    <chip name={jack} supplierPartNumbers={{jlcpcb:["USB1130-15-A"]}} footprint={<UsbA3A/>} pinLabels={{pin1:"VBUS",pin2:"D_MINUS",pin3:"D_PLUS",pin4:"GND",pin5:"SHIELD"}} connections={{pin1:`net.${vbus}`,pin2:`net.${N("CONN_N")}`,pin3:`net.${N("CONN_P")}`,pin4:"net.GND",pin5:"net.GND"}}/>
  </group>
}

const PortCell = ({ p, efuse, mux, esd, jack, rail, adcV, adcI }: any) => {
  const N = (suffix: string) => `P${p}_${suffix}`
  const base = 400 + p * 10
  return <group name={`port${p}`}>
    <chip name={efuse} supplierPartNumbers={{ jlcpcb: ["C3662799"] }}
      pinLabels={{ pin1: "EN_UVLO", pin2: "OVLO", pin3: "AUXOFF", pin4: "FLT", pin5: "IN", pin6: "OUT", pin7: "DVDT", pin8: "GND", pin9: "ILM", pin10: "ITIMER" }}
      connections={{ pin1: `net.${N("PWR_EN")}`, pin2: `net.${N("OVLO")}`, pin4: `net.${N("FLT_N")}`, pin5: `net.${rail}`, pin6: `net.${N("VBUS")}`, pin7: `net.${N("DVDT")}`, pin8: "net.GND", pin9: `net.${N("ILIM")}`, pin10: `net.${N("ITIMER")}` }}
      footprint={<TwoSided pins={10} pitch={0.45} span={2.4} />} />
    <R2 name={`R${base}`} value="100k" a={N("PWR_EN")} b="GND" />
    <R2 name={`R${base + 1}`} value="36.5k" a={rail} b={N("OVLO")} />
    <R2 name={`R${base + 2}`} value="10k" a={N("OVLO")} b="GND" />
    <R2 name={`R${base + 3}`} value="10k" a="N3V3_LOGIC" b={N("FLT_N")} />
    <R2 name={`R${base + 4}`} value="1.47k" a={N("ILIM")} b="GND" jlc="C22841" />
    <R2 name={`R${base + 5}`} value="1k" a={N("ILIM")} b={adcI} />
    <R2 name={`R${base + 6}`} value="100k" a={N("VBUS")} b={N("VBUS_SENSE")} />
    <R2 name={`R${base + 7}`} value="68k" a={N("VBUS_SENSE")} b="GND" />
    <R2 name={`R${base + 8}`} value="1k" a={N("VBUS_SENSE")} b={adcV} />
    <R2 name={`R${base + 9}`} value="10k" a="N3V3_LOGIC" b={N("DATA_ISO")} />
    <C2 name={`C${base}`} value="3.3nF" a={N("DVDT")} b="GND" />
    <C2 name={`C${base + 1}`} value="2.2nF" a={N("ITIMER")} b="GND" />
    <C2 name={`C${base + 2}`} value="100nF" a={rail} b="GND" />
    <C2 name={`C${base + 3}`} value="22uF" a={N("VBUS")} b="GND" fp="1210" />
    <C2 name={`C${base + 4}`} value="100nF" a={N("VBUS")} b="GND" />
    <C2 name={`C${base + 5}`} value="100nF" a="N3V3_LOGIC" b="GND" />
    <chip name={`D${p + 3}`} supplierPartNumbers={{ jlcpcb: ["C85098"] }}
      pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: `net.${N("VBUS")}`, pin2: "net.GND" }}
      footprint={<Pol2 w="2mm" h="2.3mm" dx="2.4mm" />} />
    <chip name={mux} supplierPartNumbers={{ jlcpcb: ["C11355"] }} footprint={<TwoSided pins={10} pitch={0.5} span={3.4} />}
      pinLabels={{ pin1: "VCC", pin2: "SEL", pin3: "D_PLUS", pin4: "D_MINUS", pin5: "GND", pin6: "HSD1_MINUS", pin7: "HSD1_PLUS", pin8: "HSD2_MINUS", pin9: "HSD2_PLUS", pin10: "OE" }}
      connections={{ pin1: "net.N3V3_LOGIC", pin2: "net.GND", pin3: `net.${N("HUB_P")}`, pin4: `net.${N("HUB_N")}`, pin5: "net.GND", pin6: `net.${N("PORT_N")}`, pin7: `net.${N("PORT_P")}`, pin10: `net.${N("DATA_ISO")}` }} />
    <chip name={esd} supplierPartNumbers={{ jlcpcb: ["C7519"] }} footprint="sot23_6"
      pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
      connections={{ pin1: `net.${N("PORT_P")}`, pin2: "net.GND", pin3: `net.${N("PORT_N")}`, pin4: `net.${N("CONN_N")}`, pin5: `net.${N("VBUS")}`, pin6: `net.${N("CONN_P")}` }} />
    <chip name={jack} supplierPartNumbers={{ jlcpcb: ["USB1130-15-A"] }} footprint={<UsbA3A />}
      pinLabels={{ pin1: "VBUS", pin2: "D_MINUS", pin3: "D_PLUS", pin4: "GND", pin5: "SHIELD" }}
      connections={{ pin1: `net.${N("VBUS")}`, pin2: `net.${N("CONN_N")}`, pin3: `net.${N("CONN_P")}`, pin4: "net.GND", pin5: "net.GND" }} />
  </group>
}
export default () => (
  <board width="130mm" height="90mm" routingDisabled>
    {/* Input: locking terminal -> replaceable 10 A MINI fuse -> LM74810-Q1
        common-drain back-to-back FETs -> protected rail and protected-side TVS. */}
    <chip name="J1" supplierPartNumbers={{ jlcpcb: ["C3819953"] }}
      pinLabels={{ pin1: "VIN_RAW_POS", pin2: "VIN_RAW_NEG" }}
      connections={{ pin1: "net.VIN_RAW", pin2: "net.GND" }} footprint={<InputTerminal />} />
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["3568"] }}
      pinLabels={{ pin1: "FUSE_IN", pin2: "FUSE_OUT" }}
      connections={{ pin1: "net.VIN_RAW", pin2: "net.VIN_FUSED" }} footprint={<BladeFuse />} />
    <PowerMosfet name="Q1" source="VIN_FUSED" gate="DGATE" drain="FET_MID" />
    <PowerMosfet name="Q2" source="VIN_PROTECTED" gate="HGATE" drain="FET_MID" />
    <chip name="U1" supplierPartNumbers={{ jlcpcb: ["C3215601"] }}
      pinLabels={{ pin1: "DGATE", pin2: "A", pin3: "VSNS", pin4: "SW", pin5: "OV", pin6: "EN_UVLO", pin7: "GND", pin8: "HGATE", pin9: "OUT", pin10: "VS", pin11: "CAP", pin12: "C", pin13: "RTN_FLOAT" }}
      connections={{ pin1: "net.DGATE", pin2: "net.VIN_FUSED", pin3: "net.VIN_FUSED", pin4: "net.OV_TOP", pin5: "net.OV_SENSE", pin6: "net.UV_SENSE", pin7: "net.GND", pin8: "net.HGATE", pin9: "net.VIN_PROTECTED", pin10: "net.FET_MID", pin11: "net.CAP", pin12: "net.FET_MID" }} footprint={<Wson13 />} />
    <R2 name="R1" value="90.9k" a="VIN_FUSED" b="OV_TOP" jlc="C2930136" />
    <R2 name="R2" value="0" a="OV_TOP" b="OV_SENSE" />
    <R2 name="R3" value="4.64k" a="OV_SENSE" b="GND" jlc="C2078999" />
    <R2 name="R4" value="90.9k" a="VIN_FUSED" b="UV_SENSE" />
    <R2 name="R5" value="11.5k" a="UV_SENSE" b="GND" />
    <C2 name="C1" value="220nF" a="CAP" b="FET_MID" />
    <C2 name="C2" value="100nF" a="FET_MID" b="GND" fp="1206" />
    <C2 name="C3" value="100nF" a="VIN_FUSED" b="GND" fp="1206" />
    <chip name="D1" supplierPartNumbers={{ jlcpcb: ["C224017"] }} pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VIN_PROTECTED", pin2: "net.GND" }} footprint={<Pol2 w="2.1mm" h="2.4mm" dx="2.2mm" />} />

    <Buck s="A" vout="N5V_A" ids={{
      U: "U2", CIN: ["C107", "C108", "C109", "C110"], COUT: ["C112", "C113"],
      RT: "R101", FBT: "R102", FBTRIM: "R111", FBB: "R103", CFF: "C101",
    }} />
    <Buck s="B" vout="N5V_B" ids={{
      U: "U3", CIN: ["C207", "C208", "C209", "C210"], COUT: ["C212", "C213"],
      RT: "R201", FBT: "R202", FBTRIM: "R211", FBB: "R203", CFF: "C201",
    }} />

    {/* The fixed 3.3 V regulator is qualified for the protected-input rail's
        bounded operating and transient envelope. */}
    <chip name="U4" supplierPartNumbers={{ jlcpcb: ["C5248536"] }}
      pinLabels={{ pin1: "FB", pin2: "EN", pin3: "VIN", pin4: "GND", pin5: "SW", pin6: "BST" }}
      connections={{ pin1: "net.N3V3_LOGIC", pin2: "net.VIN_PROTECTED", pin3: "net.VIN_PROTECTED", pin4: "net.GND", pin5: "net.SW_3V3", pin6: "net.BST_3V3" }} footprint="sot23_6" />
    <inductor name="L3" inductance="4.7uH" supplierPartNumbers={{ jlcpcb: ["C307880"] }} footprint={<Pol2 w="1.9mm" h="5.1mm" dx="2.1mm" />} connections={{ pin1: "net.SW_3V3", pin2: "net.N3V3_LOGIC" }} />
    <C2 name="C21" value="10uF" a="VIN_PROTECTED" b="GND" fp="1206" />
    <C2 name="C22" value="100nF" a="BST_3V3" b="SW_3V3" />
    <C2 name="C23" value="22uF" a="N3V3_LOGIC" b="GND" fp="1206" />
    <C2 name="C24" value="22uF" a="N3V3_LOGIC" b="GND" fp="1206" />

    {/* Upstream USB-B and low-capacitance ESD. */}
    <chip name="J2" supplierPartNumbers={{ jlcpcb: ["C86462"] }}
      pinLabels={{ pin1: "VBUS", pin2: "D_MINUS", pin3: "D_PLUS", pin4: "GND", pin5: "SHIELD" }}
      connections={{ pin1: "net.USB_UP_VBUS", pin2: "net.UP_CONN_N", pin3: "net.UP_CONN_P", pin4: "net.GND", pin5: "net.GND" }} footprint={<UsbB />} />
    <chip name="U5" supplierPartNumbers={{ jlcpcb: ["C7519"] }} pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
      connections={{ pin1: "net.UP_CONN_P", pin2: "net.GND", pin3: "net.UP_CONN_N", pin4: "net.UP_HUB_N", pin5: "net.USB_UP_VBUS", pin6: "net.UP_HUB_P" }} footprint="sot23_6" />

    {/* USB2517I: external ports 1-4, management MCU on port 5, 6/7 disabled by SMBus. */}
    <chip name="U6" supplierPartNumbers={{ jlcpcb: ["C478081"] }} footprint={<Qfn64Ep />}
      pinLabels={{ pin1: "DN1_DM", pin2: "DN1_DP", pin3: "DN2_DM", pin4: "DN2_DP", pin5: "VDDA33", pin6: "DN3_DM", pin7: "DN3_DP", pin8: "DN4_DM", pin9: "DN4_DP", pin10: "VDDA33", pin11: "DN5_DM", pin12: "DN5_DP", pin13: "CFG2", pin14: "LED_B7", pin15: "LED_A7", pin16: "LED_B6", pin17: "LED_A6", pin18: "LED_B5", pin19: "TEST", pin20: "PRTPWR4", pin21: "OCS4_N", pin22: "OCS3_N", pin23: "PRTPWR3", pin24: "VDD33CR", pin25: "VDD18", pin26: "PRTPWR2", pin27: "OCS2_N", pin28: "OCS1_N", pin29: "PRTPWR1", pin30: "PRTPWR5", pin31: "LED_A5", pin32: "LED_B4", pin33: "LED_A4", pin34: "LED_B3", pin35: "OCS5_N", pin36: "PRTPWR7", pin37: "OCS7_N", pin38: "OCS6_N", pin39: "PRTPWR6", pin40: "SDA", pin41: "SCL_CFG0", pin42: "CFG1", pin43: "RESET_N", pin44: "VBUS_DET", pin45: "LOCAL_PWR", pin46: "VDD33", pin47: "LED_A3", pin48: "LED_B2", pin49: "LED_A2", pin50: "LED_B1", pin51: "LED_A1", pin52: "VDDA33", pin53: "DN6_DM", pin54: "DN6_DP", pin55: "DN7_DM", pin56: "DN7_DP", pin57: "VDDA33", pin58: "UP_DM", pin59: "UP_DP", pin60: "XTAL2", pin61: "XTAL1", pin62: "VDD18PLL", pin63: "RBIAS", pin64: "VDD33PLL", pin65: "EP_VSS" }}
      connections={{ pin1: "net.P1_HUB_N", pin2: "net.P1_HUB_P", pin3: "net.P2_HUB_N", pin4: "net.P2_HUB_P", pin5: "net.N3V3_LOGIC", pin6: "net.P3_HUB_N", pin7: "net.P3_HUB_P", pin8: "net.P4_HUB_N", pin9: "net.P4_HUB_P", pin10: "net.N3V3_LOGIC", pin11: "net.MGMT_N", pin12: "net.MGMT_P", pin13: "net.GND", pin20: "net.HUB_PP4", pin21: "net.P4_FLT_N", pin22: "net.P3_FLT_N", pin23: "net.HUB_PP3", pin24: "net.N3V3_LOGIC", pin25: "net.VDD18", pin26: "net.HUB_PP2", pin27: "net.P2_FLT_N", pin28: "net.P1_FLT_N", pin29: "net.HUB_PP1", pin35: "net.N3V3_LOGIC", pin37: "net.N3V3_LOGIC", pin38: "net.N3V3_LOGIC", pin40: "net.HUB_SDA", pin41: "net.HUB_SCL", pin42: "net.GND", pin43: "net.HUB_RESET_N", pin44: "net.HUB_VBUS_DET", pin46: "net.N3V3_LOGIC", pin52: "net.N3V3_LOGIC", pin57: "net.N3V3_LOGIC", pin58: "net.UP_HUB_N", pin59: "net.UP_HUB_P", pin60: "net.XTAL2", pin61: "net.XTAL1", pin62: "net.VDD18PLL", pin63: "net.RBIAS", pin64: "net.N3V3_LOGIC", pin65: "net.GND" }} />
    <chip name="Y1" supplierPartNumbers={{ jlcpcb: ["C1985204"] }} pinLabels={{ pin1: "X1", pin2: "GND1", pin3: "X2", pin4: "GND2" }}
      connections={{ pin1: "net.XTAL1", pin2: "net.GND", pin3: "net.XTAL2", pin4: "net.GND" }} footprint={<TwoSided pins={4} pitch={1.6} span={3.2} />} />
    <R2 name="R30" value="1M" a="XTAL1" b="XTAL2" />
    <R2 name="R31" value="12k" a="RBIAS" b="GND" />
    <R2 name="R32" value="100k" a="USB_UP_VBUS" b="HUB_VBUS_DET" />
    <R2 name="R33" value="100k" a="HUB_VBUS_DET" b="GND" />
    <R2 name="R34" value="4.7k" a="N3V3_LOGIC" b="HUB_SDA" />
    <R2 name="R35" value="4.7k" a="N3V3_LOGIC" b="HUB_SCL" />
    <R2 name="R36" value="10k" a="HUB_RESET_N" b="GND" />
    <C2 name="C30" value="18pF" a="XTAL1" b="GND" />
    <C2 name="C31" value="18pF" a="XTAL2" b="GND" />
    {[32, 33, 34, 35].map((n) => <C2 key={`hvd${n}`} name={`C${n}`} value="100nF" a="N3V3_LOGIC" b="GND" />)}
    <C2 name="C36" value="1uF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C37" value="1uF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C38" value="100nF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C39" value="100nF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C40" value="1uF" a="VDD18" b="GND" />
    <C2 name="C41" value="1uF" a="VDD18PLL" b="GND" />

    {/* Management MCU: host USB device, hub SMBus master, port control and ADC telemetry. */}
    <chip name="U7" supplierPartNumbers={{ jlcpcb: ["C2847904"] }} footprint={<TwoSided pins={48} pitch={0.5} span={7.8} />}
      pinLabels={{ pin1: "PC13", pin2: "PC14", pin3: "PC15", pin4: "VBAT", pin5: "VREF", pin6: "VDD_VDDA", pin7: "VSS_VSSA", pin8: "PF0", pin9: "PF1", pin10: "NRST", pin11: "PA0", pin12: "PA1", pin13: "PB0", pin14: "PB1", pin15: "PB2", pin16: "PB10", pin17: "PB11", pin18: "PB12", pin19: "PA2", pin20: "PA3", pin21: "PA4", pin22: "PA5", pin23: "PA6", pin24: "PA7", pin25: "PB13", pin26: "PB14", pin27: "PB15", pin28: "PA8", pin29: "PA9", pin30: "PC6", pin31: "PC7", pin32: "PA10", pin33: "USB_DM", pin34: "USB_DP", pin35: "SWDIO", pin36: "SWCLK_BOOT0", pin37: "PB3", pin38: "PB4", pin39: "PB5", pin40: "PB6", pin41: "PB7", pin42: "PB8", pin43: "PB9", pin44: "PD0", pin45: "PD1", pin46: "PD2", pin47: "PD3", pin48: "PA15" }}
      connections={{ pin4: "net.N3V3_LOGIC", pin5: "net.N3V3_LOGIC", pin6: "net.N3V3_LOGIC", pin7: "net.GND", pin10: "net.MCU_NRST", pin11: "net.ADC_P1_VBUS", pin12: "net.ADC_P2_VBUS", pin13: "net.P1_PWR_CMD", pin14: "net.P2_PWR_CMD", pin15: "net.P3_PWR_CMD", pin16: "net.P4_PWR_CMD", pin17: "net.P1_DATA_ISO", pin18: "net.P2_DATA_ISO", pin19: "net.ADC_P3_VBUS", pin20: "net.ADC_P4_VBUS", pin21: "net.ADC_P1_IMON", pin22: "net.ADC_P2_IMON", pin23: "net.ADC_P3_IMON", pin24: "net.ADC_P4_IMON", pin25: "net.P3_DATA_ISO", pin26: "net.P4_DATA_ISO", pin27: "net.P1_FLT_N", pin28: "net.P2_FLT_N", pin29: "net.P3_FLT_N", pin30: "net.P4_FLT_N", pin31: "net.RUN_A_HOLD", pin32: "net.RUN_B_HOLD", pin33: "net.MGMT_N", pin34: "net.MGMT_P", pin35: "net.SWDIO", pin36: "net.SWCLK", pin40: "net.HUB_SCL", pin41: "net.HUB_SDA", pin42: "net.HUB_RESET_N" }} />
    <C2 name="C42" value="100nF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C43" value="4.7uF" a="N3V3_LOGIC" b="GND" />
    <C2 name="C44" value="100nF" a="N3V3_LOGIC" b="GND" />
    <R2 name="R37" value="10k" a="MCU_NRST" b="N3V3_LOGIC" />
    <R2 name="R38" value="100k" a="P1_PWR_CMD" b="GND" />
    <R2 name="R39" value="100k" a="P2_PWR_CMD" b="GND" />
    <R2 name="R40" value="100k" a="P3_PWR_CMD" b="GND" />
    <R2 name="R41" value="100k" a="P4_PWR_CMD" b="GND" />
    <chip name="J7" supplierPartNumbers={{ jlcpcb: ["C19191796"] }} pinLabels={{ pin1: "VTREF", pin2: "SWDIO", pin3: "GND", pin4: "SWCLK", pin5: "GND", pin6: "SWO", pin7: "KEY", pin8: "NC", pin9: "GND_DETECT", pin10: "NRST" }}
      connections={{ pin1: "net.N3V3_LOGIC", pin2: "net.SWDIO", pin3: "net.GND", pin4: "net.SWCLK", pin5: "net.GND", pin9: "net.GND", pin10: "net.MCU_NRST" }} footprint={<Header2x5 />} />

    {/* Standard USB hub power policy AND host command.  On reset every MCU command
        is low, so no port can energize before firmware explicitly enables it. */}
    <chip name="U8" supplierPartNumbers={{ jlcpcb: ["C6053"] }} footprint={<TwoSided pins={14} pitch={0.65} span={5.4} />}
      pinLabels={{ pin1: "1A", pin2: "1B", pin3: "1Y", pin4: "2A", pin5: "2B", pin6: "2Y", pin7: "GND", pin8: "3Y", pin9: "3A", pin10: "3B", pin11: "4Y", pin12: "4A", pin13: "4B", pin14: "VCC" }}
      connections={{ pin1: "net.HUB_PP1", pin2: "net.P1_PWR_CMD", pin3: "net.P1_PWR_EN", pin4: "net.HUB_PP2", pin5: "net.P2_PWR_CMD", pin6: "net.P2_PWR_EN", pin7: "net.GND", pin8: "net.P3_PWR_EN", pin9: "net.HUB_PP3", pin10: "net.P3_PWR_CMD", pin11: "net.P4_PWR_EN", pin12: "net.HUB_PP4", pin13: "net.P4_PWR_CMD", pin14: "net.N3V3_LOGIC" }} />
    <C2 name="C45" value="100nF" a="N3V3_LOGIC" b="GND" />

    <PortCell p={1} efuse="U9" mux="U13" esd="U17" jack="J3" rail="N5V_A" adcV="ADC_P1_VBUS" adcI="ADC_P1_IMON" />
    <PortCell p={2} efuse="U10" mux="U14" esd="U18" jack="J4" rail="N5V_A" adcV="ADC_P2_VBUS" adcI="ADC_P2_IMON" />
    <PortCell p={3} efuse="U11" mux="U15" esd="U19" jack="J5" rail="N5V_B" adcV="ADC_P3_VBUS" adcI="ADC_P3_IMON" />
    <PortCell p={4} efuse="U12" mux="U16" esd="U20" jack="J6" rail="N5V_B" adcV="ADC_P4_VBUS" adcI="ADC_P4_IMON" />
  </board>
)

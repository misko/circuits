// usb-hub-3s — 3S LiPo (XT60) -> 3x USB-A (2A cont / 2.5A burst, TPS2557-limited,
// TPS2513 DCP) + 1x USB-C PD3.0 source (IP6559-C, 100W class, 20V/5A e-marked).
//
// AUTHORING RULES honoured (03_tscircuit/contracts.md):
//  - every pin bound with connections={{...}} to explicit net.NAME (parity by
//    construction); the only digit-leading rail is authored N5VA -> canon "5VA".
//  - every specialty part carries supplierPartNumbers (the 02_parts FPID handle).
//  - alphanumeric pads (J5 A1..B12/SH, J2-4 SH) carry DUAL portHints
//    [realname, number] — probe-verified 2026-07-21: part is kept by tsci and
//    the converter names symbol pins by the REAL pad name. parity_padmap.txt
//    documents the numbering.
//  - polarized 2-pad parts (diodes, TVS, polymer caps) are authored as <chip>
//    with pad 1 = CATHODE (diodes) / POSITIVE (caps), matching the KiCad
//    footprint marker convention, so no generic-symbol reversal can ship
//    (canon: polarity is a part fact; floorplan pad_net asserts re-check).
//  - placement is 03_src/floorplan.yaml (generate_board path); no pcbX here.
//
// Circuit derivation: 01_docs/DETAIL_DESIGN.md; datasheet refs in 02_parts/*.

// ---- shared tiny footprints (render-only; fab footprints come from 02_parts FPIDs) ----

const Dfn56 = () => (
  <footprint>
    <smtpad portHints={["1"]} pcbX="-1.905mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["2"]} pcbX="-0.635mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["3"]} pcbX="0.635mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["4"]} pcbX="1.905mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["5"]} pcbX="0mm" pcbY="1.1mm" width="4.4mm" height="3.9mm" shape="rect" />
  </footprint>
)

// 2-pad polarized: pad 1 = cathode (diode) / positive (polymer cap) — KiCad marker side
const Pol2 = ({ w, h, dx }: { w: string; h: string; dx: string }) => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={`-${dx}`} pcbY="0mm" width={w} height={h} shape="rect" />
    <smtpad portHints={["2"]} pcbX={dx} pcbY="0mm" width={w} height={h} shape="rect" />
  </footprint>
)

export default () => (
  <board width="100mm" height="80mm" routingDisabled>
    {/* ================= INPUT: XT60 -> fuse -> reverse-polarity P-FET -> VIN ================= */}
    <chip name="J1" supplierPartNumbers={{ jlcpcb: ["C98732"] }}
      pinLabels={{ pin1: "MINUS", pin2: "PLUS" }}
      connections={{ pin1: "net.GND", pin2: "net.VBAT" }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="6mm" holeDiameter="4mm" shape="circle" />
          <platedhole portHints={["2"]} pcbX="7.2mm" pcbY="0mm" outerDiameter="6mm" holeDiameter="4mm" shape="circle" />
        </footprint>
      } />
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["3568"] }}
      pinLabels={{ pin1: "IN", pin2: "OUT" }}
      connections={{ pin1: "net.VBAT", pin2: "net.VBAT_F" }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="-5mm" pcbY="0mm" outerDiameter="3.5mm" holeDiameter="1.9mm" shape="circle" />
          <platedhole portHints={["2"]} pcbX="5mm" pcbY="0mm" outerDiameter="3.5mm" holeDiameter="1.9mm" shape="circle" />
        </footprint>
      } />
    {/* Q1 reverse-polarity P-FET: D=VBAT_F (battery side), S=VIN, body diode conducts on first contact */}
    <chip name="Q1" supplierPartNumbers={{ jlcpcb: ["C2760089"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.VIN", pin2: "net.VIN", pin3: "net.VIN", pin4: "net.RPP_G", pin5: "net.VBAT_F" }}
      footprint={<Dfn56 />} />
    <resistor name="R13" resistance="100k" footprint="0603" connections={{ pin1: "net.RPP_G", pin2: "net.GND" }} />
    {/* D5 zener S->G clamp: cathode (pad1) at SOURCE=VIN, anode at gate */}
    <chip name="D5" supplierPartNumbers={{ jlcpcb: ["C173429"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VIN", pin2: "net.RPP_G" }}
      footprint={<Pol2 w="0.9mm" h="1.2mm" dx="1.65mm" />} />
    {/* D1 input TVS SMBJ15A on VIN (AFTER Q1 — v1.1 fix, review X1/X29: on VBAT_F a
        reversed pack forward-biased it into a crowbar through F1. On VIN, behind Q1's
        blocking body diode, a reversal is non-destructive; hot-plug clamping is
        equivalent through the enhanced Q1. ADR-0001 amendment; INV-D1-PLACEMENT. */}
    <chip name="D1" supplierPartNumbers={{ jlcpcb: ["C83846"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="2.1mm" h="2.4mm" dx="2.2mm" />} />
    {/* VIN bulk: 2x 100uF/35V polymer at entry (pad1 = POSITIVE) */}
    <chip name="C1" supplierPartNumbers={{ jlcpcb: ["C2982822"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="1.6mm" h="3.2mm" dx="2.9mm" />} />
    <chip name="C2" supplierPartNumbers={{ jlcpcb: ["C2982822"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="1.6mm" h="3.2mm" dx="2.9mm" />} />

    {/* ================= 5VA BUCK — LM5116 + AON6354 pair (5V/7A, TI 5V/7A design) ================= */}
    <chip name="U2" supplierPartNumbers={{ jlcpcb: ["C13755"] }}
      pinLabels={{
        pin1: "VIN", pin2: "UVLO", pin3: "RT", pin4: "EN", pin5: "RAMP",
        pin6: "AGND", pin7: "SS", pin8: "FB", pin9: "COMP", pin10: "VOUT",
        pin11: "DEMB", pin12: "CS", pin13: "CSG", pin14: "PGND", pin15: "LO",
        pin16: "VCC", pin17: "VCCX", pin18: "HB", pin19: "HO", pin20: "SW",
        pin21: "EP",
      }}
      connections={{
        pin1: "net.VIN", pin2: "net.UVLO_A", pin3: "net.RT_A", pin4: "net.EN_A",
        pin5: "net.RAMP_A", pin6: "net.GND", pin7: "net.SS_A", pin8: "net.FB_A",
        pin9: "net.COMP_A", pin10: "net.N5VA", pin11: "net.GND", pin12: "net.CSF_A",
        pin13: "net.CSGF_A", pin14: "net.GND", pin15: "net.LO_A", pin16: "net.VCC_A",
        pin17: "net.GND", pin18: "net.BOOT_A", pin19: "net.HO_A", pin20: "net.SW_A",
        pin21: "net.GND",
      }}
      footprint={
        <footprint>
          {Array.from({ length: 10 }, (_, i) => (
            <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-2.9mm" pcbY={`${(4.5 * 0.65) - i * 0.65}mm`} width="1.35mm" height="0.4mm" shape="rect" />
          ))}
          {Array.from({ length: 10 }, (_, i) => (
            <smtpad key={`r${i}`} portHints={[`${i + 11}`]} pcbX="2.9mm" pcbY={`${-(4.5 * 0.65) + i * 0.65}mm`} width="1.35mm" height="0.4mm" shape="rect" />
          ))}
          <smtpad portHints={["21"]} pcbX="0mm" pcbY="0mm" width="3.4mm" height="6.5mm" shape="rect" />
        </footprint>
      } />
    {/* power pair: Q2 HS (D=VIN S=SW_A G=HO), Q3 LS (D=SW_A S=CS_A G=LO); Rs 10m from CS_A to GND */}
    <chip name="Q2" supplierPartNumbers={{ jlcpcb: ["C404363"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.SW_A", pin2: "net.SW_A", pin3: "net.SW_A", pin4: "net.HO_A", pin5: "net.VIN" }}
      footprint={<Dfn56 />} />
    <chip name="Q3" supplierPartNumbers={{ jlcpcb: ["C404363"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.CS_A", pin2: "net.CS_A", pin3: "net.CS_A", pin4: "net.LO_A", pin5: "net.SW_A" }}
      footprint={<Dfn56 />} />
    <resistor name="RS1" resistance="0.01" footprint="2512" supplierPartNumbers={{ jlcpcb: ["C127692"] }}
      connections={{ pin1: "net.CS_A", pin2: "net.GND" }} />
    <inductor name="L2" inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }}
      connections={{ pin1: "net.SW_A", pin2: "net.N5VA" }}
      footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
    {/* boot diode VCC->HB (cathode pad1 at HB) + boot cap HB-SW */}
    <chip name="D4" supplierPartNumbers={{ jlcpcb: ["C2128"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.BOOT_A", pin2: "net.VCC_A" }}
      footprint={<Pol2 w="0.6mm" h="1mm" dx="1.25mm" />} />
    <capacitor name="C18" capacitance="1uF" footprint="0603" connections={{ pin1: "net.BOOT_A", pin2: "net.SW_A" }} />
    <capacitor name="C19" capacitance="1uF" footprint="0603" connections={{ pin1: "net.VCC_A", pin2: "net.GND" }} />
    {/* input caps 4x 10uF/25V 1210 + 100n; output 4x 100uF/6.3V 1210 */}
    <capacitor name="C5" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C6" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C7" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C8" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C9" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C10" capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C49066"] }} connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    <capacitor name="C11" capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C49066"] }} connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    <capacitor name="C12" capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C49066"] }} connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    <capacitor name="C13" capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C49066"] }} connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    {/* control small parts: RT, RAMP, FB divider, comp, SS, UVLO divider, EN pull-up, CS 0R pair */}
    <resistor name="R1" resistance="12.4k" footprint="0603" connections={{ pin1: "net.RT_A", pin2: "net.GND" }} />
    <capacitor name="C14" capacitance="330pF" footprint="0603" connections={{ pin1: "net.RAMP_A", pin2: "net.GND" }} />
    <resistor name="R2" resistance="3.74k" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.FB_A" }} />
    <resistor name="R3" resistance="1.21k" footprint="0603" connections={{ pin1: "net.FB_A", pin2: "net.GND" }} />
    <resistor name="R4" resistance="18k" footprint="0603" connections={{ pin1: "net.COMP_A", pin2: "net.CMZ_A" }} />
    <capacitor name="C15" capacitance="3.3nF" footprint="0603" connections={{ pin1: "net.CMZ_A", pin2: "net.FB_A" }} />
    <capacitor name="C16" capacitance="100pF" footprint="0603" connections={{ pin1: "net.COMP_A", pin2: "net.FB_A" }} />
    <capacitor name="C17" capacitance="10nF" footprint="0603" connections={{ pin1: "net.SS_A", pin2: "net.GND" }} />
    <resistor name="R5" resistance="49.9k" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.UVLO_A" }} />
    <resistor name="R6" resistance="6.98k" footprint="0603" connections={{ pin1: "net.UVLO_A", pin2: "net.GND" }} />
    <resistor name="R9" resistance="100k" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.EN_A" }} />
    {/* CS kelvin 0R links: chip CS pin (CSF_A) -R7- Rs top (CS_A); chip CSG pin (CSGF_A) -R8- Rs bottom (GND) */}
    <resistor name="R7" resistance="0" footprint="0603" connections={{ pin1: "net.CS_A", pin2: "net.CSF_A" }} />
    <resistor name="R8" resistance="0" footprint="0603" connections={{ pin1: "net.GND", pin2: "net.CSGF_A" }} />

    {/* DCP advertisement — TPS2513 dual-channel: U6 serves ports 1+2, U7 serves port 3 */}
    <chip name="U6" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2", pin4: "DM2", pin5: "IN", pin6: "DM1" }}
      connections={{
        pin1: "net.DP_A1", pin2: "net.GND", pin3: "net.DP_A2", pin4: "net.DM_A2",
        pin5: "net.N5VA", pin6: "net.DM_A1",
      }}
      footprint="sot23_6" />
    <chip name="U7" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2", pin4: "DM2", pin5: "IN", pin6: "DM1" }}
      connections={{
        pin1: "net.DP_A3", pin2: "net.GND", pin5: "net.N5VA", pin6: "net.DM_A3",
      }}
      footprint="sot23_6" />
    <capacitor name="C42" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    <capacitor name="C43" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />

    {/* ================= USB-A PORT CHANNELS x3 (TPS2557 + TPS2513 + USBLC6) ================= */}
    {[1, 2, 3].map((n) => {
      const sw = ["U3", "U4", "U5"][n - 1]
      const rl = ["R10", "R11", "R12"][n - 1]
      const cin = ["C33", "C34", "C35"][n - 1]
      const cout = ["C36", "C37", "C38"][n - 1]
      const chf = ["C39", "C40", "C41"][n - 1]
      const esd = ["U8", "U9", "U10"][n - 1]
      const jn = ["J2", "J3", "J4"][n - 1]
      return (
        <group key={`porta${n}`} name={`porta${n}`}>
          <chip name={sw} supplierPartNumbers={{ jlcpcb: ["C130056"] }}
            pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "EN", pin5: "ILIM", pin6: "OUT1", pin7: "OUT2", pin8: "FAULT", pin9: "EP" }}
            connections={{
              pin1: "net.GND", pin2: "net.N5VA", pin3: "net.N5VA", pin4: "net.N5VA",
              pin5: `net.ILIM${n}`, pin6: `net.VBUSA${n}`, pin7: `net.VBUSA${n}`, pin9: "net.GND",
            }}
            footprint={
              <footprint>
                {Array.from({ length: 4 }, (_, i) => (
                  <smtpad key={`a${i}`} portHints={[`${i + 1}`]} pcbX="-1.5mm" pcbY={`${0.975 - i * 0.65}mm`} width="0.8mm" height="0.35mm" shape="rect" />
                ))}
                {Array.from({ length: 4 }, (_, i) => (
                  <smtpad key={`b${i}`} portHints={[`${i + 5}`]} pcbX="1.5mm" pcbY={`${-0.975 + i * 0.65}mm`} width="0.8mm" height="0.35mm" shape="rect" />
                ))}
                <smtpad portHints={["9"]} pcbX="0mm" pcbY="0mm" width="1.65mm" height="2.4mm" shape="rect" />
              </footprint>
            } />
          <resistor name={rl} resistance="36.5k" footprint="0603" connections={{ pin1: `net.ILIM${n}`, pin2: "net.GND" }} />
          <capacitor name={cin} capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
          <capacitor name={cout} capacitance="22uF" footprint="0805" supplierPartNumbers={{ jlcpcb: ["C29277"] }} connections={{ pin1: `net.VBUSA${n}`, pin2: "net.GND" }} />
          <capacitor name={chf} capacitance="100nF" footprint="0603" connections={{ pin1: `net.VBUSA${n}`, pin2: "net.GND" }} />
          {/* ESD array: 1/6 pass D+; 3/4 pass D-; VBUS pin5 on the 5V port rail */}
          <chip name={esd} supplierPartNumbers={{ jlcpcb: ["C7519"] }}
            pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
            connections={{
              pin1: `net.DP_A${n}`, pin2: "net.GND", pin3: `net.DM_A${n}`,
              pin4: `net.DM_A${n}`, pin5: `net.VBUSA${n}`, pin6: `net.DP_A${n}`,
            }}
            footprint={
              <footprint>
                {Array.from({ length: 3 }, (_, i) => (
                  <smtpad key={`x${i}`} portHints={[`${i + 1}`]} pcbX={`${-0.95 + i * 0.95}mm`} pcbY="-1.3mm" width="0.6mm" height="0.7mm" shape="rect" />
                ))}
                {Array.from({ length: 3 }, (_, i) => (
                  <smtpad key={`y${i}`} portHints={[`${i + 4}`]} pcbX={`${0.95 - i * 0.95}mm`} pcbY="1.3mm" width="0.6mm" height="0.7mm" shape="rect" />
                ))}
              </footprint>
            } />
          {/* USB-A receptacle KH-AF90DIP-112 (C503996): 1=VBUS 2=D- 3=D+ 4=GND + SH shell (THT) */}
          <chip name={jn} supplierPartNumbers={{ jlcpcb: ["C503996"] }}
            pinLabels={{ pin1: "VBUS", pin2: "DM", pin3: "DP", pin4: "GND", pin5: "SHIELD" }}
            connections={{
              pin1: `net.VBUSA${n}`, pin2: `net.DM_A${n}`, pin3: `net.DP_A${n}`,
              pin4: "net.GND", pin5: "net.GND",
            }}
            footprint={
              <footprint>
                {[-3.5, -1.0, 1.0, 3.5].map((x, i) => (
                  <platedhole key={`p${i}`} portHints={[`${i + 1}`]} pcbX={`${x}mm`} pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1.0mm" shape="circle" />
                ))}
                <platedhole portHints={["SH", "5"]} pcbX="-6.62mm" pcbY="2.6mm" outerDiameter="4mm" holeDiameter="3mm" shape="circle" />
              </footprint>
            } />
        </group>
      )
    })}

    {/* ================= USB-C PD STAGE — IP6559-C (DS Fig.8 + Fig.9) ================= */}
    <chip name="U1" supplierPartNumbers={{ jlcpcb: ["C5140592"] }}
      pinLabels={{
        pin1: "VOUT2G", pin2: "NC2", pin3: "NC3", pin4: "GPIO17", pin5: "EN",
        pin6: "NC6", pin7: "NC7", pin8: "NC8", pin9: "NC9", pin10: "VOUTI",
        pin11: "AGND1", pin12: "VIO", pin13: "CSN1", pin14: "CSP1", pin15: "PCON",
        pin16: "HG1", pin17: "BST1", pin18: "LX1", pin19: "LG1", pin20: "LG2",
        pin21: "LX2", pin22: "BST2", pin23: "HG2", pin24: "PCIN", pin25: "CSN2",
        pin26: "CSP2", pin27: "VIN", pin28: "AGND2", pin29: "VCC5V", pin30: "AGND3",
        pin31: "NC31", pin32: "VCCIO", pin33: "GPIO4", pin34: "GPIO3", pin35: "GPIO2",
        pin36: "GPIO1", pin37: "GPIO0", pin38: "CC2", pin39: "DPC", pin40: "DMC",
        pin41: "CC1", pin42: "DPA", pin43: "DMA", pin44: "VOUT1", pin45: "VOUT1G",
        pin46: "GPIO21", pin47: "GPIO22", pin48: "VOUT2", pin49: "EP",
      }}
      connections={{
        pin1: "net.PATH_G", pin5: "net.EN_PD", pin10: "net.VOUT_PD",
        pin11: "net.GND", pin12: "net.VOUT_PD", pin13: "net.SNS_OUT_N", pin14: "net.SNS_OUT_P",
        pin15: "net.VOUT_PDS", pin16: "net.HG1", pin17: "net.BST1", pin18: "net.LX1",
        pin19: "net.LG1", pin20: "net.LG2", pin21: "net.LX2", pin22: "net.BST2",
        pin23: "net.HG2", pin24: "net.VIN_S", pin25: "net.SNS_IN_N", pin26: "net.SNS_IN_P",
        pin27: "net.VIN", pin28: "net.GND", pin29: "net.VCC5V", pin30: "net.GND",
        pin32: "net.VCCIO", pin37: "net.PDO_CFG", pin38: "net.CC2", pin39: "net.DPC",
        pin40: "net.DMC", pin41: "net.CC1", pin46: "net.EMK2", pin47: "net.EMK1",
        pin48: "net.VOUT2_SNS", pin49: "net.GND",
      }}
      footprint={
        <footprint>
          {Array.from({ length: 12 }, (_, i) => (
            <smtpad key={`w${i}`} portHints={[`${i + 1}`]} pcbX="-3.5mm" pcbY={`${2.75 - i * 0.5}mm`} width="0.85mm" height="0.28mm" shape="rect" />
          ))}
          {Array.from({ length: 12 }, (_, i) => (
            <smtpad key={`s${i}`} portHints={[`${i + 13}`]} pcbX={`${-2.75 + i * 0.5}mm`} pcbY="-3.5mm" width="0.28mm" height="0.85mm" shape="rect" />
          ))}
          {Array.from({ length: 12 }, (_, i) => (
            <smtpad key={`e${i}`} portHints={[`${i + 25}`]} pcbX="3.5mm" pcbY={`${-2.75 + i * 0.5}mm`} width="0.85mm" height="0.28mm" shape="rect" />
          ))}
          {Array.from({ length: 12 }, (_, i) => (
            <smtpad key={`n${i}`} portHints={[`${i + 37}`]} pcbX={`${2.75 - i * 0.5}mm`} pcbY="3.5mm" width="0.28mm" height="0.85mm" shape="rect" />
          ))}
          <smtpad portHints={["49"]} pcbX="0mm" pcbY="0mm" width="5.45mm" height="5.45mm" shape="rect" />
        </footprint>
      } />
    {/* v1.1 (X27): PD-stage local VIN capacitance AT the cell — C44 bulk polymer +
        C3/C45 the DETAIL-promised 2x10uF (v1.0 built only one) + C4 100n */}
    <capacitor name="C3" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C4" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C45" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <chip name="C44" supplierPartNumbers={{ jlcpcb: ["C2982822"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="1.6mm" h="3.2mm" dx="2.9mm" />} />
    {/* input sense: VIN -[RS2 5m]- VIN_S ; kelvin CSP2 (via 10R) / CSN2 ; PCIN at VIN_S */}
    <resistor name="RS2" resistance="0.005" footprint="2512" supplierPartNumbers={{ jlcpcb: ["C308572"] }}
      connections={{ pin1: "net.VIN", pin2: "net.VIN_S" }} />
    <resistor name="R14" resistance="10" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.SNS_IN_P" }} />
    <resistor name="R15" resistance="10" footprint="0603" connections={{ pin1: "net.VIN_S", pin2: "net.SNS_IN_N" }} />
    <capacitor name="C20" capacitance="1uF" footprint="0603" connections={{ pin1: "net.SNS_IN_P", pin2: "net.SNS_IN_N" }} />
    {/* H-bridge: Q4 HS-in (D=VIN_S S=LX2 G=QG4), Q5 LS-in, Q6 HS-out (D=VOUT_PDS S=LX1 G=QG6), Q7 LS-out.
        v1.1: gates driven THROUGH 0R 0603 slots R28-R31 (DS Fig.7 tuning slots — X4/X24;
        INV-GATE-R); FET = ADR-0007 coordinated part (v1.0's 30V AON6354 replaced). */}
    <chip name="Q4" supplierPartNumbers={{ jlcpcb: ["C431185"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.LX2", pin2: "net.LX2", pin3: "net.LX2", pin4: "net.QG4", pin5: "net.VIN_S" }}
      footprint={<Dfn56 />} />
    <chip name="Q5" supplierPartNumbers={{ jlcpcb: ["C431185"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.GND", pin2: "net.GND", pin3: "net.GND", pin4: "net.QG5", pin5: "net.LX2" }}
      footprint={<Dfn56 />} />
    <chip name="Q6" supplierPartNumbers={{ jlcpcb: ["C431185"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.LX1", pin2: "net.LX1", pin3: "net.LX1", pin4: "net.QG6", pin5: "net.VOUT_PDS" }}
      footprint={<Dfn56 />} />
    <chip name="Q7" supplierPartNumbers={{ jlcpcb: ["C431185"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.GND", pin2: "net.GND", pin3: "net.GND", pin4: "net.QG7", pin5: "net.LX1" }}
      footprint={<Dfn56 />} />
    {/* gate-R tuning slots, 0R populated, placed AT the gates (X4) */}
    <resistor name="R28" resistance="0" footprint="0603" connections={{ pin1: "net.HG2", pin2: "net.QG4" }} />
    <resistor name="R29" resistance="0" footprint="0603" connections={{ pin1: "net.LG2", pin2: "net.QG5" }} />
    <resistor name="R30" resistance="0" footprint="0603" connections={{ pin1: "net.HG1", pin2: "net.QG6" }} />
    <resistor name="R31" resistance="0" footprint="0603" connections={{ pin1: "net.LG1", pin2: "net.QG7" }} />
    {/* v1.1 bridge-rail HF banks (X18: v1.0 had ZERO caps on VIN_S/VOUT_PDS; the hot
        loops closed 44-63mm away through the shunts). Ceramics on BOTH sides of each
        shunt keep RS2/RS3 out of the HF loop. INV-BRIDGE-RAIL-CAPS. */}
    <capacitor name="C46" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN_S", pin2: "net.GND" }} />
    <capacitor name="C47" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN_S", pin2: "net.GND" }} />
    <capacitor name="C48" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VIN_S", pin2: "net.GND" }} />
    <capacitor name="C49" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VOUT_PDS", pin2: "net.GND" }} />
    <capacitor name="C50" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VOUT_PDS", pin2: "net.GND" }} />
    <capacitor name="C51" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VOUT_PDS", pin2: "net.GND" }} />
    <inductor name="L1" inductance="10uH" supplierPartNumbers={{ jlcpcb: ["C20613209"] }}
      connections={{ pin1: "net.LX2", pin2: "net.LX1" }}
      footprint={<Pol2 w="3.8mm" h="13mm" dx="8.1mm" />} />
    {/* boot caps + snubbers + LX TVS (v1.1 ADR-0007: per-node clamps - D6 SMAJ15A on LX2, D7 SMAJ24A on LX1; 60V AON6262E bridge) */}
    <capacitor name="C21" capacitance="100nF" footprint="0603" connections={{ pin1: "net.BST2", pin2: "net.LX2" }} />
    <capacitor name="C22" capacitance="100nF" footprint="0603" connections={{ pin1: "net.BST1", pin2: "net.LX1" }} />
    <resistor name="R16" resistance="2" footprint="0603" connections={{ pin1: "net.LX2", pin2: "net.SNB2" }} />
    <capacitor name="C23" capacitance="1nF" footprint="0603" connections={{ pin1: "net.SNB2", pin2: "net.GND" }} />
    <resistor name="R17" resistance="2" footprint="0603" connections={{ pin1: "net.LX1", pin2: "net.SNB1" }} />
    <capacitor name="C24" capacitance="1nF" footprint="0603" connections={{ pin1: "net.SNB1", pin2: "net.GND" }} />
    <chip name="D6" supplierPartNumbers={{ jlcpcb: ["C148216"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.LX2", pin2: "net.GND" }}
      footprint={<Pol2 w="1.5mm" h="1.8mm" dx="2mm" />} />
    <chip name="D7" supplierPartNumbers={{ jlcpcb: ["C148222"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.LX1", pin2: "net.GND" }}
      footprint={<Pol2 w="1.5mm" h="1.8mm" dx="2mm" />} />
    {/* output sense: VOUT_PDS -[RS3 5m]- VOUT_PD ; kelvin CSP1 (via 10R) / CSN1 ; PCON at VOUT_PDS */}
    <resistor name="RS3" resistance="0.005" footprint="2512" supplierPartNumbers={{ jlcpcb: ["C308572"] }}
      connections={{ pin1: "net.VOUT_PDS", pin2: "net.VOUT_PD" }} />
    <resistor name="R18" resistance="10" footprint="0603" connections={{ pin1: "net.VOUT_PDS", pin2: "net.SNS_OUT_P" }} />
    <resistor name="R19" resistance="10" footprint="0603" connections={{ pin1: "net.VOUT_PD", pin2: "net.SNS_OUT_N" }} />
    <capacitor name="C25" capacitance="1uF" footprint="0603" connections={{ pin1: "net.SNS_OUT_P", pin2: "net.SNS_OUT_N" }} />
    {/* converter output caps + path FET + VBUSC */}
    <chip name="C26" supplierPartNumbers={{ jlcpcb: ["C46550465"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }}
      connections={{ pin1: "net.VOUT_PD", pin2: "net.GND" }}
      footprint={<Pol2 w="1.6mm" h="3.2mm" dx="2.9mm" />} />
    <capacitor name="C27" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VOUT_PD", pin2: "net.GND" }} />
    <chip name="Q8" supplierPartNumbers={{ jlcpcb: ["C431185"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.VBUSC", pin2: "net.VBUSC", pin3: "net.VBUSC", pin4: "net.PATH_G", pin5: "net.VOUT_PD" }}
      footprint={<Dfn56 />} />
    <resistor name="R20" resistance="10" footprint="0603" connections={{ pin1: "net.VBUSC", pin2: "net.VOUT2_SNS" }} />
    <capacitor name="C28" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
    <capacitor name="C29" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
    <chip name="D3" supplierPartNumbers={{ jlcpcb: ["C148222"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VBUSC", pin2: "net.GND" }}
      footprint={<Pol2 w="1.5mm" h="1.8mm" dx="2mm" />} />
    {/* LDO decoupling + EN divider + PDO config slot (DNP) */}
    <capacitor name="C30" capacitance="2.2uF" footprint="0603" connections={{ pin1: "net.VCC5V", pin2: "net.GND" }} />
    <capacitor name="C31" capacitance="2.2uF" footprint="0603" connections={{ pin1: "net.VCCIO", pin2: "net.GND" }} />
    <resistor name="R21" resistance="10k" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.EN_PD" }} />
    <resistor name="R22" resistance="10k" footprint="0603" connections={{ pin1: "net.EN_PD", pin2: "net.GND" }} />
    {/* R25 = PDO-config slot on GPIO0 — DNP (ADR 0004: variant-default 100W PDO
        set; value table is app-note-only). bom_seed forces Value=DNP; pads stay. */}
    <resistor name="R25" resistance="0" footprint="0603" connections={{ pin1: "net.PDO_CFG", pin2: "net.GND" }} />
    {/* Vconn e-marker switches (DS Fig.9): 5VA -> D2 -> VCONN5V; GPIO22->CC1 leg, GPIO21->CC2 leg */}
    <chip name="D2" supplierPartNumbers={{ jlcpcb: ["C14996"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VCONN5V", pin2: "net.N5VA" }}
      footprint={<Pol2 w="1.5mm" h="1.8mm" dx="2mm" />} />
    <capacitor name="C32" capacitance="1uF" footprint="0603" connections={{ pin1: "net.VCONN5V", pin2: "net.GND" }} />
    <chip name="Q9" supplierPartNumbers={{ jlcpcb: ["C15127"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.VCONN_G1", pin2: "net.VCONN5V", pin3: "net.CC1" }}
      footprint="sot23" />
    <resistor name="R23" resistance="10k" footprint="0603" connections={{ pin1: "net.VCONN5V", pin2: "net.VCONN_G1" }} />
    <chip name="Q10" supplierPartNumbers={{ jlcpcb: ["C8545"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.EMK1", pin2: "net.GND", pin3: "net.VCONN_G1" }}
      footprint="sot23" />
    <resistor name="R24" resistance="10k" footprint="0603" connections={{ pin1: "net.EMK1", pin2: "net.GND" }} />
    <chip name="Q11" supplierPartNumbers={{ jlcpcb: ["C15127"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.VCONN_G2", pin2: "net.VCONN5V", pin3: "net.CC2" }}
      footprint="sot23" />
    <resistor name="R26" resistance="10k" footprint="0603" connections={{ pin1: "net.VCONN5V", pin2: "net.VCONN_G2" }} />
    <chip name="Q12" supplierPartNumbers={{ jlcpcb: ["C8545"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.EMK2", pin2: "net.GND", pin3: "net.VCONN_G2" }}
      footprint="sot23" />
    <resistor name="R27" resistance="10k" footprint="0603" connections={{ pin1: "net.EMK2", pin2: "net.GND" }} />
    {/* C-port data ESD (rail-independent bidirectional pairs) */}
    <chip name="D8" supplierPartNumbers={{ jlcpcb: ["C5246195"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.DPC", pin2: "net.GND" }}
      footprint={<Pol2 w="0.5mm" h="0.6mm" dx="0.75mm" />} />
    <chip name="D9" supplierPartNumbers={{ jlcpcb: ["C5246195"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.DMC", pin2: "net.GND" }}
      footprint={<Pol2 w="0.5mm" h="0.6mm" dx="0.75mm" />} />
    {/* USB-C receptacle: 16 pads A1..B12 (numbered 1..16) + SH (17) — dual portHints */}
    <chip name="J5" supplierPartNumbers={{ jlcpcb: ["C5337088"] }}
      pinLabels={{
        pin1: "GNDA1", pin2: "VBUSA4", pin3: "CC1", pin4: "DPA6", pin5: "DMA7",
        pin6: "SBU1", pin7: "VBUSA9", pin8: "GNDA12", pin9: "GNDB1", pin10: "VBUSB4",
        pin11: "CC2", pin12: "DPB6", pin13: "DMB7", pin14: "SBU2", pin15: "VBUSB9",
        pin16: "GNDB12", pin17: "SHIELD",
      }}
      connections={{
        pin1: "net.GND", pin2: "net.VBUSC", pin3: "net.CC1", pin4: "net.DPC",
        pin5: "net.DMC", pin7: "net.VBUSC", pin8: "net.GND", pin9: "net.GND",
        pin10: "net.VBUSC", pin11: "net.CC2", pin12: "net.DPC", pin13: "net.DMC",
        pin15: "net.VBUSC", pin16: "net.GND", pin17: "net.GND",
      }}
      footprint={
        <footprint>
          {(["A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12"] as const).map((p, i) => (
            <smtpad key={p} portHints={[p, `${i + 1}`]} pcbX={`${-3.2 + i * 0.9}mm`} pcbY="3mm" width="0.4mm" height="1.1mm" shape="rect" />
          ))}
          {(["B1", "B4", "B5", "B6", "B7", "B8", "B9", "B12"] as const).map((p, i) => (
            <smtpad key={p} portHints={[p, `${i + 9}`]} pcbX={`${-3.2 + i * 0.9}mm`} pcbY="1.2mm" width="0.4mm" height="1.1mm" shape="rect" />
          ))}
          <platedhole portHints={["SH", "17"]} pcbX="-4.7mm" pcbY="-1mm" outerDiameter="1.2mm" holeDiameter="0.7mm" shape="circle" />
        </footprint>
      } />
  </board>
)

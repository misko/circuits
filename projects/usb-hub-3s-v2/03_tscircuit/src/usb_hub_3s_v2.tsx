// usb-hub-3s-v2 — 3S LiPo (XT60) -> 3x USB-A (2A cont / 2.5A burst, TPS2557 +
// TPS2513A DCP) + 1x USB-C 5V/5A PD source (TPS25740A PD PHY + external path FET).
//
// ALL-BUCK redesign of usb-hub-3s v1 (E-TOPO green): the USB-C port is fixed 5V
// ONLY (BRIEF D1), so both rails are step-down bucks — v1's IP6559 buck-boost is
// GONE. Two proven LM5116 5V bucks (ADR-0010): buck A -> 5VA (USB-A, 6A), buck C
// -> 5VC (USB-C, 5A). PD signalling is a pure PHY on the 5VC rail (ADR-0004-v2).
//
// AUTHORING RULES honoured (03_tscircuit/contracts.md):
//  - every pin bound with connections={{...}} to explicit net.NAME (parity by
//    construction); leading-digit rails authored N5VA/N5VC -> converter strips
//    the N guard -> canon 5VA/5VC.
//  - every specialty part carries supplierPartNumbers (the 02_parts FPID handle).
//  - alphanumeric pads (J5 A1..B12/SH, J2-4 SH) carry DUAL portHints.
//  - polarized 2-pad parts (diodes, TVS, polymer caps) authored as <chip> with
//    pad 1 = CATHODE (diodes) / POSITIVE (caps), matching the KiCad footprint
//    marker convention, so no generic-symbol reversal can ship.
//
// Circuit derivation: 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; buck values are
// v1's proven 5V/7A LM5116 design reused verbatim (both bucks fit inside 7A).

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

// LM5116 HTSSOP-20-EP footprint (v1-proven): 10 pads/side @ 0.65mm + EP pad 21
const Lm5116Fp = () => (
  <footprint>
    {Array.from({ length: 10 }, (_, i) => (
      <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-2.9mm" pcbY={`${(4.5 * 0.65) - i * 0.65}mm`} width="1.35mm" height="0.4mm" shape="rect" />
    ))}
    {Array.from({ length: 10 }, (_, i) => (
      <smtpad key={`r${i}`} portHints={[`${i + 11}`]} pcbX="2.9mm" pcbY={`${-(4.5 * 0.65) + i * 0.65}mm`} width="1.35mm" height="0.4mm" shape="rect" />
    ))}
    <smtpad portHints={["21"]} pcbX="0mm" pcbY="0mm" width="3.4mm" height="6.5mm" shape="rect" />
  </footprint>
)

// TPS2557 VSON-8 footprint (v1-proven): 4 pads/side @ 0.65mm + EP pad 9
const Tps2557Fp = () => (
  <footprint>
    {Array.from({ length: 4 }, (_, i) => (
      <smtpad key={`a${i}`} portHints={[`${i + 1}`]} pcbX="-1.5mm" pcbY={`${0.975 - i * 0.65}mm`} width="0.8mm" height="0.35mm" shape="rect" />
    ))}
    {Array.from({ length: 4 }, (_, i) => (
      <smtpad key={`b${i}`} portHints={[`${i + 5}`]} pcbX="1.5mm" pcbY={`${-0.975 + i * 0.65}mm`} width="0.8mm" height="0.35mm" shape="rect" />
    ))}
    <smtpad portHints={["9"]} pcbX="0mm" pcbY="0mm" width="1.65mm" height="2.4mm" shape="rect" />
  </footprint>
)

// LM5116 buck cell — one instance per rail. `s` = net suffix (A/C), `vout` = the
// output net (N5VA/N5VC), `ids` = the refdes for every part in the cell.
const Buck = ({ s, vout, ids }: {
  s: string; vout: string;
  ids: {
    U: string; QH: string; QL: string; RS: string; L: string; DB: string;
    RT: string; FBT: string; FBB: string; RCMP: string; UVT: string; UVB: string;
    REN: string; RCSK: string; RCSG: string;
    CRAMP: string; CCMZ: string; CCMP: string; CSS: string; CBOOT: string; CVCC: string;
    CIN: string[]; CINH: string; COUT: string[];
  };
}) => {
  const n = (x: string) => `net.${x}_${s}`
  return (
    <group name={`buck${s}`}>
      <chip name={ids.U} supplierPartNumbers={{ jlcpcb: ["C13755"] }}
        pinLabels={{
          pin1: "VIN", pin2: "UVLO", pin3: "RT", pin4: "EN", pin5: "RAMP",
          pin6: "AGND", pin7: "SS", pin8: "FB", pin9: "COMP", pin10: "VOUT",
          pin11: "DEMB", pin12: "CS", pin13: "CSG", pin14: "PGND", pin15: "LO",
          pin16: "VCC", pin17: "VCCX", pin18: "HB", pin19: "HO", pin20: "SW",
          pin21: "EP",
        }}
        connections={{
          pin1: "net.VIN", pin2: n("UVLO"), pin3: n("RT"), pin4: n("EN"),
          pin5: n("RAMP"), pin6: "net.GND", pin7: n("SS"), pin8: n("FB"),
          pin9: n("COMP"), pin10: `net.${vout}`, pin11: "net.GND", pin12: n("CSF"),
          pin13: n("CSGF"), pin14: "net.GND", pin15: n("LO"), pin16: n("VCC"),
          pin17: "net.GND", pin18: n("BOOT"), pin19: n("HO"), pin20: n("SW"),
          pin21: "net.GND",
        }}
        footprint={<Lm5116Fp />} />
      {/* power pair: QH HS (D=VIN S=SW G=HO), QL LS (D=SW S=CS G=LO); Rs 10m CS->GND */}
      <chip name={ids.QH} supplierPartNumbers={{ jlcpcb: ["C404363"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: n("SW"), pin2: n("SW"), pin3: n("SW"), pin4: n("HO"), pin5: "net.VIN" }}
        footprint={<Dfn56 />} />
      <chip name={ids.QL} supplierPartNumbers={{ jlcpcb: ["C404363"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: n("CS"), pin2: n("CS"), pin3: n("CS"), pin4: n("LO"), pin5: n("SW") }}
        footprint={<Dfn56 />} />
      <resistor name={ids.RS} resistance="0.01" footprint="2512" supplierPartNumbers={{ jlcpcb: ["C127692"] }}
        connections={{ pin1: n("CS"), pin2: "net.GND" }} />
      <inductor name={ids.L} inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }}
        connections={{ pin1: n("SW"), pin2: `net.${vout}` }}
        footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
      {/* boot diode VCC->HB (cathode pad1 at HB) + boot cap HB-SW + VCC cap */}
      <chip name={ids.DB} supplierPartNumbers={{ jlcpcb: ["C2128"] }}
        pinLabels={{ pin1: "K", pin2: "A" }}
        connections={{ pin1: n("BOOT"), pin2: n("VCC") }}
        footprint={<Pol2 w="0.6mm" h="1mm" dx="1.25mm" />} />
      <capacitor name={ids.CBOOT} capacitance="1uF" footprint="0603" connections={{ pin1: n("BOOT"), pin2: n("SW") }} />
      <capacitor name={ids.CVCC} capacitance="1uF" footprint="0603" connections={{ pin1: n("VCC"), pin2: "net.GND" }} />
      {/* input caps 4x 10uF/25V 1210 + 100n */}
      {ids.CIN.map((c) => (
        <capacitor key={c} name={c} capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
      ))}
      <capacitor name={ids.CINH} capacitance="100nF" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
      {/* output caps 4x 100uF/6.3V 1210 */}
      {ids.COUT.map((c) => (
        <capacitor key={c} name={c} capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C49066"] }} connections={{ pin1: `net.${vout}`, pin2: "net.GND" }} />
      ))}
      {/* control small parts: RT, RAMP, FB divider, comp, SS, UVLO divider, EN, CS 0R pair */}
      <resistor name={ids.RT} resistance="12.4k" footprint="0603" connections={{ pin1: n("RT"), pin2: "net.GND" }} />
      <capacitor name={ids.CRAMP} capacitance="330pF" footprint="0603" connections={{ pin1: n("RAMP"), pin2: "net.GND" }} />
      <resistor name={ids.FBT} resistance="3.74k" footprint="0603" connections={{ pin1: `net.${vout}`, pin2: n("FB") }} />
      <resistor name={ids.FBB} resistance="1.21k" footprint="0603" connections={{ pin1: n("FB"), pin2: "net.GND" }} />
      <resistor name={ids.RCMP} resistance="18k" footprint="0603" connections={{ pin1: n("COMP"), pin2: n("CMZ") }} />
      <capacitor name={ids.CCMZ} capacitance="3.3nF" footprint="0603" connections={{ pin1: n("CMZ"), pin2: n("FB") }} />
      <capacitor name={ids.CCMP} capacitance="100pF" footprint="0603" connections={{ pin1: n("COMP"), pin2: n("FB") }} />
      <capacitor name={ids.CSS} capacitance="10nF" footprint="0603" connections={{ pin1: n("SS"), pin2: "net.GND" }} />
      <resistor name={ids.UVT} resistance="49.9k" footprint="0603" connections={{ pin1: "net.VIN", pin2: n("UVLO") }} />
      <resistor name={ids.UVB} resistance="6.98k" footprint="0603" connections={{ pin1: n("UVLO"), pin2: "net.GND" }} />
      <resistor name={ids.REN} resistance="100k" footprint="0603" connections={{ pin1: "net.VIN", pin2: n("EN") }} />
      {/* CS kelvin 0R links: chip CS pin (CSF) -R- Rs top (CS); chip CSG pin (CSGF) -R- GND */}
      <resistor name={ids.RCSK} resistance="0" footprint="0603" connections={{ pin1: n("CS"), pin2: n("CSF") }} />
      <resistor name={ids.RCSG} resistance="0" footprint="0603" connections={{ pin1: "net.GND", pin2: n("CSGF") }} />
    </group>
  )
}

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
    {/* F1 10A MINI blade fuse holder (Keystone 3568) — hand-solder; blade fuse separate */}
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["C5249699"] }}
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
    <resistor name="R1" resistance="100k" footprint="0603" connections={{ pin1: "net.RPP_G", pin2: "net.GND" }} />
    {/* D2 zener S->G clamp: cathode (pad1) at SOURCE=VIN, anode at gate */}
    <chip name="D2" supplierPartNumbers={{ jlcpcb: ["C173429"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VIN", pin2: "net.RPP_G" }}
      footprint={<Pol2 w="0.9mm" h="1.2mm" dx="1.65mm" />} />
    {/* D1 input TVS SMBJ15A on VIN (AFTER Q1 — the v1.1 D1-position fix built correctly
        from the start: on VIN behind Q1's blocking body diode, reversal is non-destructive.
        ADR-0001; INV-D1-PLACEMENT. */}
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

    {/* ================= BUCK A — LM5116 5V/7A -> 5VA (USB-A rail, <=6A) ================= */}
    <Buck s="A" vout="N5VA" ids={{
      U: "U2", QH: "Q2", QL: "Q3", RS: "RS1", L: "L1", DB: "D3",
      RT: "R2", FBT: "R3", FBB: "R4", RCMP: "R5", UVT: "R6", UVB: "R7",
      REN: "R8", RCSK: "R9", RCSG: "R10",
      CRAMP: "C3", CCMZ: "C4", CCMP: "C5", CSS: "C6", CBOOT: "C7", CVCC: "C8",
      CIN: ["C9", "C10", "C11", "C12"], CINH: "C13", COUT: ["C14", "C15", "C16", "C17"],
    }} />

    {/* ================= BUCK C — LM5116 5V/7A -> 5VC (USB-C rail, <=5A) ================= */}
    <Buck s="C" vout="N5VC" ids={{
      U: "U11", QH: "Q4", QL: "Q5", RS: "RS2", L: "L2", DB: "D4",
      RT: "R11", FBT: "R12", FBB: "R13", RCMP: "R14", UVT: "R15", UVB: "R16",
      REN: "R17", RCSK: "R18", RCSG: "R19",
      CRAMP: "C18", CCMZ: "C19", CCMP: "C20", CSS: "C21", CBOOT: "C22", CVCC: "C23",
      CIN: ["C24", "C25", "C26", "C27"], CINH: "C28", COUT: ["C29", "C30", "C31", "C32"],
    }} />

    {/* ============ DCP advertisement — TPS2513A dual-channel: U6 ports 1+2, U7 port 3 ============ */}
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
    <capacitor name="C33" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    <capacitor name="C34" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />

    {/* ================= USB-A PORT CHANNELS x3 (TPS2557 + USBLC6 + KH-AF90DIP) ================= */}
    {[1, 2, 3].map((k) => {
      const n = k - 1
      const sw = ["U3", "U4", "U5"][n]
      const rl = ["R20", "R21", "R22"][n]
      const cin = ["C35", "C36", "C37"][n]
      const cout = ["C38", "C39", "C40"][n]
      const chf = ["C41", "C42", "C43"][n]
      const esd = ["U8", "U9", "U10"][n]
      const jn = ["J2", "J3", "J4"][n]
      return (
        <group key={`porta${k}`} name={`porta${k}`}>
          <chip name={sw} supplierPartNumbers={{ jlcpcb: ["C130056"] }}
            pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "EN", pin5: "ILIM", pin6: "OUT1", pin7: "OUT2", pin8: "FAULT", pin9: "EP" }}
            connections={{
              pin1: "net.GND", pin2: "net.N5VA", pin3: "net.N5VA", pin4: "net.N5VA",
              pin5: `net.ILIM${k}`, pin6: `net.VBUSA${k}`, pin7: `net.VBUSA${k}`, pin9: "net.GND",
            }}
            footprint={<Tps2557Fp />} />
          <resistor name={rl} resistance="36.5k" footprint="0603" connections={{ pin1: `net.ILIM${k}`, pin2: "net.GND" }} />
          <capacitor name={cin} capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
          <capacitor name={cout} capacitance="22uF" footprint="0805" supplierPartNumbers={{ jlcpcb: ["C29277"] }} connections={{ pin1: `net.VBUSA${k}`, pin2: "net.GND" }} />
          <capacitor name={chf} capacitance="100nF" footprint="0603" connections={{ pin1: `net.VBUSA${k}`, pin2: "net.GND" }} />
          {/* ESD array: 1/6 pass D+; 3/4 pass D-; VBUS pin5 on the 5V port rail */}
          <chip name={esd} supplierPartNumbers={{ jlcpcb: ["C7519"] }}
            pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
            connections={{
              pin1: `net.DP_A${k}`, pin2: "net.GND", pin3: `net.DM_A${k}`,
              pin4: `net.DM_A${k}`, pin5: `net.VBUSA${k}`, pin6: `net.DP_A${k}`,
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
              pin1: `net.VBUSA${k}`, pin2: `net.DM_A${k}`, pin3: `net.DP_A${k}`,
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

    {/* ================= USB-C PD CELL — TPS25740A (SLVSDG8B) + back-to-back path FETs + J5 =========
        5VC (buck C) -> Rs -> back-to-back N-FETs -> USB-C VBUS, gated by the TPS25740A PD PHY.
        Straps (part.yaml): EN9V HIGH (5V-only), HIPWR 100k->GND (5A), PSEL 100k->GND, PCTRL/GD ->
        VAUX (enabled). Pure PD PHY — no DC-DC. Nets: N5VC, RSNS(Rs load/ISNS), PDSRC(common source/
        GDNS), PDGATE(common gate), VBUSC, CC1/CC2, DPC/DMC, DVDD/VAUX/VTX bias, GDNG, DSCG_N. */}
    <group name="pdcell">
      <chip name="U1" supplierPartNumbers={{ jlcpcb: ["C544309"] }}
        pinLabels={{
          pin1: "VTX", pin2: "CC1", pin3: "CC2", pin4: "GND", pin5: "HIPWR", pin6: "CTL1",
          pin7: "CTL2", pin8: "EN9V", pin9: "NC9", pin10: "NC10", pin11: "UFP", pin12: "PSEL",
          pin13: "DVDD", pin14: "PCTRL", pin15: "GD", pin16: "VAUX", pin17: "VDD", pin18: "AGND",
          pin19: "ISNS", pin20: "VPWR", pin21: "VBUS", pin22: "GDNG", pin23: "GDNS", pin24: "DSCG",
          pin25: "EP",
        }}
        connections={{
          pin1: "net.VTX", pin2: "net.CC1", pin3: "net.CC2", pin4: "net.GND", pin5: "net.HIPWR",
          pin8: "net.DVDD", pin9: "net.GND", pin10: "net.GND", pin12: "net.PSEL",
          pin13: "net.DVDD", pin14: "net.VAUX", pin15: "net.VAUX", pin16: "net.VAUX",
          pin17: "net.GND", pin18: "net.GND", pin19: "net.RSNS", pin20: "net.N5VC",
          pin21: "net.VBUSC", pin22: "net.GDNG", pin23: "net.PDSRC", pin24: "net.DSCG_N",
          pin25: "net.GND",
          // pin6 CTL1, pin7 CTL2, pin11 UFP left unconnected (NC — sanctioned floats)
        }}
        footprint={
          <footprint>
            {Array.from({ length: 6 }, (_, i) => (
              <smtpad key={`L${i}`} portHints={[`${i + 1}`]} pcbX="-2.2mm" pcbY={`${1.25 - i * 0.5}mm`} width="0.6mm" height="0.28mm" shape="rect" />
            ))}
            {Array.from({ length: 6 }, (_, i) => (
              <smtpad key={`B${i}`} portHints={[`${i + 7}`]} pcbX={`${-1.25 + i * 0.5}mm`} pcbY="-2.2mm" width="0.28mm" height="0.6mm" shape="rect" />
            ))}
            {Array.from({ length: 6 }, (_, i) => (
              <smtpad key={`R${i}`} portHints={[`${i + 13}`]} pcbX="2.2mm" pcbY={`${-1.25 + i * 0.5}mm`} width="0.6mm" height="0.28mm" shape="rect" />
            ))}
            {Array.from({ length: 6 }, (_, i) => (
              <smtpad key={`T${i}`} portHints={[`${i + 19}`]} pcbX={`${1.25 - i * 0.5}mm`} pcbY="2.2mm" width="0.28mm" height="0.6mm" shape="rect" />
            ))}
            <smtpad portHints={["25"]} pcbX="0mm" pcbY="0mm" width="2.7mm" height="2.7mm" shape="rect" />
          </footprint>
        } />
      {/* Rs 5mR sense: VPWR(5VC) supply side -> RSNS load side (ISNS Kelvin). */}
      <resistor name="RS3" resistance="0.005" footprint="2512" supplierPartNumbers={{ jlcpcb: ["C308572"] }}
        connections={{ pin1: "net.N5VC", pin2: "net.RSNS" }} />
      {/* Back-to-back path N-FETs (AON6354, 30V logic-level): common SOURCE=PDSRC=GDNS,
          common GATE=PDGATE. Q6 drain=RSNS (supply), Q7 drain=VBUSC (connector). */}
      <chip name="Q6" supplierPartNumbers={{ jlcpcb: ["C404363"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: "net.PDSRC", pin2: "net.PDSRC", pin3: "net.PDSRC", pin4: "net.PDGATE", pin5: "net.RSNS" }}
        footprint={<Dfn56 />} />
      <chip name="Q7" supplierPartNumbers={{ jlcpcb: ["C404363"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: "net.PDSRC", pin2: "net.PDSRC", pin3: "net.PDSRC", pin4: "net.PDGATE", pin5: "net.VBUSC" }}
        footprint={<Dfn56 />} />
      {/* gate series R (GDNG -> gate), config straps, discharge bleed */}
      <resistor name="R25" resistance="10" footprint="0603" connections={{ pin1: "net.GDNG", pin2: "net.PDGATE" }} />
      <resistor name="R23" resistance="100k" footprint="0603" connections={{ pin1: "net.HIPWR", pin2: "net.GND" }} />
      <resistor name="R24" resistance="100k" footprint="0603" connections={{ pin1: "net.PSEL", pin2: "net.GND" }} />
      <resistor name="R26" resistance="120" footprint="0603" connections={{ pin1: "net.VBUSC", pin2: "net.DSCG_N" }} />
      {/* bias/bypass caps */}
      <capacitor name="C44" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VC", pin2: "net.GND" }} />
      <capacitor name="C45" capacitance="220nF" footprint="0603" connections={{ pin1: "net.DVDD", pin2: "net.GND" }} />
      <capacitor name="C46" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VAUX", pin2: "net.GND" }} />
      <capacitor name="C47" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VTX", pin2: "net.GND" }} />
      {/* C_PDIN bulk on the 5VC feed + VBUS receptacle bulk (>10uF) + HF */}
      <capacitor name="C48" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.N5VC", pin2: "net.GND" }} />
      <capacitor name="C49" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
      <capacitor name="C50" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
      <capacitor name="C51" capacitance="100nF" footprint="0603" connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
      {/* C-port data ESD (USBLC6) + BC1.2 DCP short (D+ <-> D-) for non-PD fallback charging */}
      <chip name="U12" supplierPartNumbers={{ jlcpcb: ["C7519"] }}
        pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
        connections={{ pin1: "net.DPC", pin2: "net.GND", pin3: "net.DMC", pin4: "net.DMC", pin5: "net.VBUSC", pin6: "net.DPC" }}
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
      <resistor name="R27" resistance="0" footprint="0603" connections={{ pin1: "net.DPC", pin2: "net.DMC" }} />
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
          // pin6 SBU1, pin14 SBU2 left unconnected (NC — sideband unused on a charger)
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
    </group>
  </board>
)

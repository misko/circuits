// Pluto RX2 8-Way v5 — autonomous receive-only one-of-eight RF selector.
//
// This source was authored from the v5 brief, ADRs, exact-part dossiers and
// rules.  It intentionally does not use a previous Pluto selector's schematic
// or PCB.  One Pluto RX input connects to at most one of eight antenna ports.
// The physical receiver is AD9363 silicon operated under the user's accepted
// AD9361-profile risk through 5.9 GHz; no ADI out-of-rating guarantee is made.
//
// USB-C supplies 5 V only.  There is no USB data or runtime control path.  U2
// runs a preprogrammed, versioned dwell profile and is reflashed over keyed
// Cortex SWD header J11 by direct Raspberry Pi GPIO SWD or an external ST-LINK.

// tscircuit rejects a net token beginning with a digit.  The shared converter
// canonically removes this transport-only N prefix (N3V3 -> 3V3), which the
// generated-netlist label-survival gate independently verifies.
const N = (name: string) => `net.${/^\d/.test(name) ? `N${name}` : name}`

const SHEET: Record<string, string> = {
  "USB-C power and protection": "power",
  "RF switch core": "rf_core",
  "RF interfaces": "rf_ports",
  "Autonomous control and SWD": "control",
}

const sheetFor = (section: string) => {
  const sheet = SHEET[section]
  if (!sheet) throw new Error(`No schematic sheet owns section: ${section}`)
  return sheet
}

const R2 = ({ name, value, a, b, jlc, mpn, section, schX, schY }: any) => (
  <resistor name={name} resistance={value} footprint="0402"
    supplierPartNumbers={{ jlcpcb: [jlc] }} manufacturerPartNumber={mpn}
    schSectionName={section} schSheetName={sheetFor(section)} schX={schX} schY={schY}
    connections={{ pin1: N(a), pin2: N(b) }} />
)

const C2 = ({ name, value, a, b, jlc, mpn, footprint = "0402", section, schX, schY }: any) => (
  <capacitor name={name} capacitance={value} footprint={footprint}
    supplierPartNumbers={{ jlcpcb: [jlc] }} manufacturerPartNumber={mpn}
    schSectionName={section} schSheetName={sheetFor(section)} schX={schX} schY={schY}
    connections={{ pin1: N(a), pin2: N(b) }} />
)

const Pol2 = ({ dx = 1.4, w = 1.4, h = 2.2 }: any) => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={`${-dx}mm`} pcbY="0mm" width={`${w}mm`} height={`${h}mm`} shape="rect" />
    <smtpad portHints={["2"]} pcbX={`${dx}mm`} pcbY="0mm" width={`${w}mm`} height={`${h}mm`} shape="rect" />
  </footprint>
)

const TwoSided = ({ pins, pitch = 0.5, span = 3.2 }: any) => {
  const left = Math.ceil(pins / 2)
  return (
    <footprint>
      {Array.from({ length: left }, (_, i) => (
        <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX={`${-span / 2}mm`}
          pcbY={`${((left - 1) / 2 - i) * pitch}mm`} width="0.8mm" height="0.28mm" shape="rect" />
      ))}
      {Array.from({ length: pins - left }, (_, i) => (
        <smtpad key={`r${i}`} portHints={[`${left + i + 1}`]} pcbX={`${span / 2}mm`}
          pcbY={`${(-(pins - left - 1) / 2 + i) * pitch}mm`} width="0.8mm" height="0.28mm" shape="rect" />
      ))}
    </footprint>
  )
}

const Qfn24Ep = () => (
  <footprint>
    {Array.from({ length: 24 }, (_, i) => {
      const side = Math.floor(i / 6)
      const p = i + 1
      const d = (i % 6 - 2.5) * 0.5
      if (side === 0) return <smtpad key={p} portHints={[`${p}`]} pcbX="-2mm" pcbY={`${-d}mm`} width="0.8mm" height="0.25mm" shape="rect" />
      if (side === 1) return <smtpad key={p} portHints={[`${p}`]} pcbX={`${d}mm`} pcbY="-2mm" width="0.25mm" height="0.8mm" shape="rect" />
      if (side === 2) return <smtpad key={p} portHints={[`${p}`]} pcbX="2mm" pcbY={`${d}mm`} width="0.8mm" height="0.25mm" shape="rect" />
      return <smtpad key={p} portHints={[`${p}`]} pcbX={`${-d}mm`} pcbY="2mm" width="0.25mm" height="0.8mm" shape="rect" />
    })}
    <smtpad portHints={["25"]} pcbX="0mm" pcbY="0mm" width="2.5mm" height="2.5mm" shape="rect" />
  </footprint>
)

const Sma = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="-2.54mm" pcbY="-2.54mm" outerDiameter="2mm" holeDiameter="1.1mm" shape="circle" />
    <platedhole portHints={["3"]} pcbX="2.54mm" pcbY="-2.54mm" outerDiameter="2mm" holeDiameter="1.1mm" shape="circle" />
    <platedhole portHints={["4"]} pcbX="-2.54mm" pcbY="2.54mm" outerDiameter="2mm" holeDiameter="1.1mm" shape="circle" />
    <platedhole portHints={["5"]} pcbX="2.54mm" pcbY="2.54mm" outerDiameter="2mm" holeDiameter="1.1mm" shape="circle" />
  </footprint>
)

const UsbC = () => (
  <footprint>
    {(["A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12"] as const).map((p, i) => (
      <smtpad key={p} portHints={[p, `${i + 1}`]} pcbX={`${-3.15 + i * 0.9}mm`} pcbY="2.8mm"
        width="0.35mm" height="1.1mm" shape="rect" />
    ))}
    {(["B1", "B4", "B5", "B6", "B7", "B8", "B9", "B12"] as const).map((p, i) => (
      <smtpad key={p} portHints={[p, `${i + 9}`]} pcbX={`${-3.15 + i * 0.9}mm`} pcbY="1.2mm"
        width="0.35mm" height="1.1mm" shape="rect" />
    ))}
    <platedhole portHints={["SH", "17"]} pcbX="-4.7mm" pcbY="-1mm" outerDiameter="1.2mm" holeDiameter="0.7mm" shape="circle" />
  </footprint>
)

// Samtec's recommended FTSH-DV land pattern: five 1.27 mm-pitch pads per
// row, 4.065 mm row-centre spacing, 0.74 x 2.79 mm lands.  The exact KiCad
// footprint is project-owned and selected through the J11 part dossier.
const CortexSwd = () => (
  <footprint>
    {Array.from({ length: 5 }, (_, i) => (
      <smtpad key={`odd${i}`} portHints={[`${i * 2 + 1}`]}
        pcbX={`${(i - 2) * 1.27}mm`} pcbY="2.0325mm"
        width="0.74mm" height="2.79mm" shape="rect" />
    ))}
    {Array.from({ length: 5 }, (_, i) => (
      <smtpad key={`even${i}`} portHints={[`${i * 2 + 2}`]}
        pcbX={`${(i - 2) * 1.27}mm`} pcbY="-2.0325mm"
        width="0.74mm" height="2.79mm" shape="rect" />
    ))}
  </footprint>
)

const RF = ({ name, net, x, y }: any) => (
  <chip name={name} supplierPartNumbers={{ jlcpcb: ["C429844"] }}
    manufacturerPartNumber="901-143-6RFX"
    schSectionName="RF interfaces" schSheetName="rf_ports" schX={x} schY={y}
    pinLabels={{ pin1: "RF", pin2: "GND1", pin3: "GND2", pin4: "GND3", pin5: "GND4" }}
    connections={{ pin1: N(net), pin2: N("GND"), pin3: N("GND"), pin4: N("GND"), pin5: N("GND") }}
    footprint={<Sma />} />
)

export default () => (
  <board width="100mm" height="80mm" routingDisabled>
    <schematicsheet name="power"
      displayName="USB-C POWER ONLY — 5 V sink / independent CC1+CC2 Rd / fuse, TVS and 3.3 V LDO / NO USB DATA" sheetIndex={1} />
    <schematicsheet name="rf_core"
      displayName="RF SWITCH CORE — PE42482 true absorptive SP8T / receive only / 100 MHz–5.9 GHz user-accepted extended operation" sheetIndex={2} />
    <schematicsheet name="rf_ports"
      displayName="RF INTERFACES — one Pluto RX common SMA and eight antenna SMAs / one selected throw maximum" sheetIndex={3} />
    <schematicsheet name="control"
      displayName="AUTONOMOUS CONTROL — STM32C011 / generated fast20-v1 dwell profile / keyed Cortex SWD connector" sheetIndex={4} />

    <chip name="J1" supplierPartNumbers={{ jlcpcb: ["C5184243"] }}
      manufacturerPartNumber="USB4105-GF-A-120"
      schSectionName="USB-C power and protection" schSheetName="power" schX="-8mm" schY="0mm"
      pinLabels={{
        pin1: "A1_GND", pin2: "A4_VBUS", pin3: "A5_CC1", pin4: "A6_DP_NC",
        pin5: "A7_DM_NC", pin6: "A8_SBU1_NC", pin7: "A9_VBUS", pin8: "A12_GND",
        pin9: "B1_GND", pin10: "B4_VBUS", pin11: "B5_CC2", pin12: "B6_DP_NC",
        pin13: "B7_DM_NC", pin14: "B8_SBU2_NC", pin15: "B9_VBUS", pin16: "B12_GND", pin17: "SH",
      }}
      connections={{
        pin1: N("GND"), pin2: N("VBUS_RAW"), pin3: N("USB_CC1"),
        pin7: N("VBUS_RAW"), pin8: N("GND"), pin9: N("GND"),
        pin10: N("VBUS_RAW"), pin11: N("USB_CC2"), pin15: N("VBUS_RAW"),
        pin16: N("GND"), pin17: N("GND"),
      }} footprint={<UsbC />} />

    <chip name="U4" supplierPartNumbers={{ jlcpcb: ["C1972959"] }}
      manufacturerPartNumber="TPD2E2U06DRLR"
      schSectionName="USB-C power and protection" schSheetName="power" schX="-4mm" schY="6mm"
      pinLabels={{ pin1: "NC1", pin2: "NC2", pin3: "IO1_CC1", pin4: "GND", pin5: "IO2_CC2" }}
      connections={{ pin3: N("USB_CC1"), pin4: N("GND"), pin5: N("USB_CC2") }}
      footprint={<TwoSided pins={5} pitch={0.5} span={1.5} />} />
    <R2 name="R1" value="5.1k" a="USB_CC1" b="GND" jlc="C105872" mpn="RC0402FR-075K1L" section="USB-C power and protection" schX="1mm" schY="6mm" />
    <R2 name="R2" value="5.1k" a="USB_CC2" b="GND" jlc="C105872" mpn="RC0402FR-075K1L" section="USB-C power and protection" schX="6mm" schY="6mm" />
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["C207010"] }} manufacturerPartNumber="0603L010YR"
      schSectionName="USB-C power and protection" schSheetName="power" schX="-3mm" schY="-3mm"
      pinLabels={{ pin1: "IN", pin2: "OUT" }} connections={{ pin1: N("VBUS_RAW"), pin2: N("VBUS_PROTECTED") }}
      footprint="0603" />
    <chip name="D1" supplierPartNumbers={{ jlcpcb: ["C83270"] }} manufacturerPartNumber="SMBJ6.0A"
      schSectionName="USB-C power and protection" schSheetName="power" schX="1mm" schY="-6mm"
      pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: N("VBUS_PROTECTED"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.1} h={2.4} />} />
    <C2 name="C1" value="4.7uF" a="VBUS_PROTECTED" b="GND" jlc="C19666" mpn="CL10A475KO8NNNC" footprint="0603" section="USB-C power and protection" schX="5mm" schY="-6mm" />
    <chip name="U3" supplierPartNumbers={{ jlcpcb: ["C2866134"] }} manufacturerPartNumber="TPS7A2433DBVR"
      schSectionName="USB-C power and protection" schSheetName="power" schX="7mm" schY="-2mm"
      pinLabels={{ pin1: "IN", pin2: "GND", pin3: "EN", pin4: "NC", pin5: "OUT" }}
      connections={{ pin1: N("VBUS_PROTECTED"), pin2: N("GND"), pin3: N("VBUS_PROTECTED"), pin5: N("3V3") }}
      footprint={<TwoSided pins={5} pitch={0.95} span={2.8} />} />
    <C2 name="C2" value="4.7uF" a="3V3" b="GND" jlc="C19666" mpn="CL10A475KO8NNNC" footprint="0603" section="USB-C power and protection" schX="10mm" schY="-6mm" />

    <chip name="U1" supplierPartNumbers={{ jlcpcb: ["C5121458"] }} manufacturerPartNumber="PE42482A-X"
      schSectionName="RF switch core" schSheetName="rf_core" schX="0mm" schY="0mm"
      pinLabels={{
        pin1: "LS", pin2: "RF2", pin3: "GND2", pin4: "RF3", pin5: "GND3", pin6: "RF4", pin7: "GND4",
        pin8: "VDD", pin9: "V1", pin10: "V2", pin11: "V3", pin12: "V4", pin13: "RF5", pin14: "GND5",
        pin15: "RF6", pin16: "GND6", pin17: "RF7", pin18: "GND7", pin19: "RF8", pin20: "NC",
        pin21: "GND_RFC", pin22: "RFC", pin23: "GND1", pin24: "RF1", pin25: "EP_GND",
      }}
      schPinArrangement={{ leftSide: [22, 24, 2, 4, 6, 13, 15, 17, 19], rightSide: [9, 10, 11, 12], topSide: [8], bottomSide: [1, 3, 5, 7, 14, 16, 18, 21, 23, 25, 20] }}
      connections={{
        pin1: N("GND"), pin2: N("RF_ANT2"), pin3: N("GND"), pin4: N("RF_ANT3"), pin5: N("GND"),
        pin6: N("RF_ANT4"), pin7: N("GND"), pin8: N("3V3"), pin9: N("SW_V1"), pin10: N("SW_V2"),
        pin11: N("SW_V3"), pin12: N("SW_V4"), pin13: N("RF_ANT5"), pin14: N("GND"),
        pin15: N("RF_ANT6"), pin16: N("GND"), pin17: N("RF_ANT7"), pin18: N("GND"),
        pin19: N("RF_ANT8"), pin21: N("GND"), pin22: N("RF_COMMON"), pin23: N("GND"),
        pin24: N("RF_ANT1"), pin25: N("GND"),
      }} footprint={<Qfn24Ep />} />
    <C2 name="C4" value="100nF" a="3V3" b="GND" jlc="C1525" mpn="CL05B104KO5NNNC" section="RF switch core" schX="-11mm" schY="-8mm" />
    <R2 name="R3" value="10k" a="3V3" b="SW_V4" jlc="C60490" mpn="RC0402FR-0710KL" section="RF switch core" schX="10mm" schY="7mm" />
    <R2 name="R4" value="10k" a="SW_V1" b="GND" jlc="C60490" mpn="RC0402FR-0710KL" section="RF switch core" schX="7mm" schY="-7mm" />
    <R2 name="R5" value="10k" a="SW_V2" b="GND" jlc="C60490" mpn="RC0402FR-0710KL" section="RF switch core" schX="12mm" schY="-7mm" />
    <R2 name="R6" value="10k" a="SW_V3" b="GND" jlc="C60490" mpn="RC0402FR-0710KL" section="RF switch core" schX="9mm" schY="-7mm" />

    <RF name="J2" net="RF_COMMON" x="-9mm" y="0mm" />
    <RF name="J3" net="RF_ANT1" x="-7mm" y="6mm" />
    <RF name="J4" net="RF_ANT2" x="-2mm" y="6mm" />
    <RF name="J5" net="RF_ANT3" x="3mm" y="6mm" />
    <RF name="J6" net="RF_ANT4" x="8mm" y="6mm" />
    <RF name="J7" net="RF_ANT5" x="-7mm" y="-6mm" />
    <RF name="J8" net="RF_ANT6" x="-2mm" y="-6mm" />
    <RF name="J9" net="RF_ANT7" x="3mm" y="-6mm" />
    <RF name="J10" net="RF_ANT8" x="8mm" y="-6mm" />

    <chip name="U2" supplierPartNumbers={{ jlcpcb: ["C5452432"] }} manufacturerPartNumber="STM32C011F4P6"
      schSectionName="Autonomous control and SWD" schSheetName="control" schX="0mm" schY="-1mm"
      pinLabels={{
        pin1: "PB7_NC", pin2: "PC14_OSCX_IN_NC", pin3: "PC15_OSCX_OUT_NC", pin4: "VDD_VDDA", pin5: "VSS_VSSA", pin6: "PF2_NRST",
        pin7: "PA0_V1", pin8: "PA1_V2", pin9: "PA2_V3", pin10: "PA3_V4", pin11: "PA4_NC",
        pin12: "PA5_NC", pin13: "PA6_NC", pin14: "PA7_NC", pin15: "PA8_NC", pin16: "PA11_PA9_NC",
        pin17: "PA12_PA10_NC", pin18: "PA13_SWDIO", pin19: "PA14_BOOT0_SWCLK", pin20: "PB6_NC",
      }}
      schPinArrangement={{ leftSide: [4, 6, 18, 19], rightSide: [7, 8, 9, 10], bottomSide: [5], topSide: [1, 2, 3, 11, 12, 13, 14, 15, 16, 17, 20] }}
      connections={{ pin4: N("3V3"), pin5: N("GND"), pin6: N("NRST"), pin7: N("SW_V1"),
        pin8: N("SW_V2"), pin9: N("SW_V3"), pin10: N("SW_V4"), pin18: N("SWDIO"), pin19: N("SWCLK") }}
      footprint={<TwoSided pins={20} pitch={0.5} span={4.4} />} />
    <C2 name="C3" value="4.7uF" a="3V3" b="GND" jlc="C19666" mpn="CL10A475KO8NNNC" footprint="0603" section="Autonomous control and SWD" schX="-12mm" schY="-6mm" />
    <C2 name="C5" value="100nF" a="3V3" b="GND" jlc="C1525" mpn="CL05B104KO5NNNC" section="Autonomous control and SWD" schX="-7mm" schY="-6mm" />
    <C2 name="C6" value="100nF" a="NRST" b="GND" jlc="C1525" mpn="CL05B104KO5NNNC" section="Autonomous control and SWD" schX="9mm" schY="-6mm" />
    <chip name="J11" supplierPartNumbers={{ jlcpcb: ["C2932107"] }}
      manufacturerPartNumber="FTSH-105-01-L-DV-K-P-TR"
      schSectionName="Autonomous control and SWD" schSheetName="control" schX="0mm" schY="7mm"
      pinLabels={{
        pin1: "VTREF_3V3", pin2: "SWDIO", pin3: "GND", pin4: "SWCLK",
        pin5: "GND", pin6: "SWO_NC", pin7: "KEY_NC", pin8: "TDI_NC",
        pin9: "GNDDETECT", pin10: "NRST",
      }}
      schPinArrangement={{ leftSide: [1, 3, 5, 7, 9], rightSide: [2, 4, 6, 8, 10] }}
      connections={{
        pin1: N("3V3"), pin2: N("SWDIO"), pin3: N("GND"), pin4: N("SWCLK"),
        pin5: N("GND"), pin9: N("GND"), pin10: N("NRST"),
      }} footprint={<CortexSwd />} />
  </board>
)

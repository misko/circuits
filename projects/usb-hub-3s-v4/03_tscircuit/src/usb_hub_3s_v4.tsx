// USB Hub 3S v4 — four-port, power-only 3S LiPo USB supply.
//
// This is the single electrical source for the human tscircuit schematic and
// the KiCad machine bridge. There is deliberately no USB data path and no USB
// Power Delivery path. USB-A D+/D- terminate in charging-signature controllers;
// USB-C D+/D- and SBU contacts are explicit no-connects.
//
// Component values follow the exact vendor application circuits cited in
// 01_docs/DETAIL_DESIGN.md. The two feedback ratios are intentional custom
// setpoints for delivery-path IR loss; they are not TI's stock 5.000 V values.

import { sel } from "tscircuit"

const N = (name: string) => `net.${name}`

// A component owns exactly one human-schematic section and one page.  Keeping
// that mapping here makes page membership reviewable without changing the
// electrical connection model or the PCB floorplan.
const SCHEMATIC_SHEET_BY_SECTION: Record<string, string> = {
  "Input protection and enable": "input",
  "Input enable and verification": "input_enable",
  "USB-A supply": "usba_supply",
  "USB-A aggregate protection": "usba_breaker",
  "USB-A charging signatures": "usba_signatures",
  "USB-A port 1": "usba_port_1",
  "USB-A port 2": "usba_port_2",
  "USB-A port 3": "usba_port_3",
  "USB-C regulated supply": "usbc_supply",
  "USB-C attach-controlled output": "usbc_output",
}

const schematicSheetFor = (section: string) => {
  const sheet = SCHEMATIC_SHEET_BY_SECTION[section]
  if (!sheet) throw new Error(`No schematic sheet owns section: ${section}`)
  return sheet
}

const R2 = ({ name, value, a, b, jlc, fp = "0603", section, schX, schY }: any) => (
  <resistor name={name} resistance={value} footprint={fp}
    schSectionName={section} schSheetName={schematicSheetFor(section)}
    schX={schX} schY={schY}
    supplierPartNumbers={{ jlcpcb: [jlc] }}
    connections={{ pin1: N(a), pin2: N(b) }} />
)

const C2 = ({ name, value, a, b, jlc, fp = "0402", section, schX, schY, schRotation }: any) => (
  <capacitor name={name} capacitance={value} footprint={fp}
    schSectionName={section} schSheetName={schematicSheetFor(section)}
    schX={schX} schY={schY} schRotation={schRotation}
    supplierPartNumbers={{ jlcpcb: [jlc] }}
    connections={{ pin1: N(a), pin2: N(b) }} />
)

const Pol2 = ({ dx = 1.4, w = 1.4, h = 2.2 }: any) => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={`${-dx}mm`} pcbY="0mm" width={`${w}mm`} height={`${h}mm`} shape="rect" />
    <smtpad portHints={["2"]} pcbX={`${dx}mm`} pcbY="0mm" width={`${w}mm`} height={`${h}mm`} shape="rect" />
  </footprint>
)

// The inline geometry exists to preserve every authored pin in circuit.json.
// The KiCad backend resolves the real manufacturer land pattern from each
// 02_parts dossier before board generation.
const TwoSided = ({ pins, pitch = 0.65, span = 5 }: any) => {
  const left = Math.ceil(pins / 2)
  return (
    <footprint>
      {Array.from({ length: left }, (_, i) => (
        <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX={`${-span / 2}mm`}
          pcbY={`${((left - 1) / 2 - i) * pitch}mm`} width="1mm" height={`${Math.min(0.34, pitch * 0.55)}mm`} shape="rect" />
      ))}
      {Array.from({ length: pins - left }, (_, i) => (
        <smtpad key={`r${i}`} portHints={[`${left + i + 1}`]} pcbX={`${span / 2}mm`}
          pcbY={`${(-(pins - left - 1) / 2 + i) * pitch}mm`} width="1mm" height={`${Math.min(0.34, pitch * 0.55)}mm`} shape="rect" />
      ))}
    </footprint>
  )
}

const InputTerminal = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="-2.5mm" pcbY="0mm" outerDiameter="2.2mm" holeDiameter="1.3mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="2.5mm" pcbY="0mm" outerDiameter="2.2mm" holeDiameter="1.3mm" shape="circle" />
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

const SlideSwitch = () => (
  <footprint>
    {[-2, 0, 2].map((x, i) => (
      <platedhole key={`sw${i}`} portHints={[`${i + 1}`]} pcbX={`${x}mm`} pcbY="0mm"
        outerDiameter="1.5mm" holeDiameter="0.8mm" shape="circle" />
    ))}
  </footprint>
)

const UsbA = () => (
  <footprint>
    {[1, 2, 3, 4].map((p, i) => (
      <platedhole key={`u${p}`} portHints={[`${p}`]} pcbX={`${(-3.5 + i * 2) }mm`} pcbY="3.5mm"
        outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
    ))}
    <platedhole portHints={["SH", "5"]} pcbX="-3.5mm" pcbY="-1mm" outerDiameter="3.4mm" holeDiameter="2.26mm" shape="circle" />
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

const UsbLc = ({ name, vbus, dm, dp, section }: any) => (
  <chip name={name} supplierPartNumbers={{ jlcpcb: ["C7519"] }}
    manufacturerPartNumber="USBLC6-2SC6"
    schSectionName={section} schSheetName={schematicSheetFor(section)}
    pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
    connections={{ pin1: N(dp), pin2: N("GND"), pin3: N(dm), pin4: N(dm), pin5: N(vbus), pin6: N(dp) }}
    footprint="sot23_6" />
)

const Tps2559 = ({ u, cin, cout, rilim, rflt, fault, ilim, vbus, section }: any) => (
  <>
    <chip name={u} supplierPartNumbers={{ jlcpcb: ["C206199"] }}
      manufacturerPartNumber="TPS2559DRCR"
      schSectionName={section} schSheetName={schematicSheetFor(section)}
      pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "IN3", pin5: "EN", pin6: "ILIM", pin7: "OUT1", pin8: "OUT2", pin9: "OUT3", pin10: "FAULT", pin11: "EP" }}
      schPinArrangement={{
        leftSide: [2, 3, 4, 5],
        rightSide: [7, 8, 9, 10],
        topSide: [6],
        bottomSide: [1, 11],
      }}
      connections={{ pin1: N("GND"), pin2: N("N5VA"), pin3: N("N5VA"), pin4: N("N5VA"), pin5: N("N5VA"), pin6: N(ilim), pin7: N(vbus), pin8: N(vbus), pin9: N(vbus), pin10: N(fault), pin11: N("GND") }}
      footprint={<TwoSided pins={11} pitch={0.5} span={2.8} />} />
    <C2 name={cin} value="100nF" a="N5VA" b="GND" jlc="C1525" section={section} />
    <R2 name={rilim} value="43.2k" a={ilim} b="GND" jlc="C861404" section={section} />
    <R2 name={rflt} value="100k" a="N5VA" b={fault} jlc="C25803" section={section} />
    <chip name={cout} supplierPartNumbers={{ jlcpcb: ["C264054"] }}
      manufacturerPartNumber="EEEFK1A151P"
      schSectionName={section} schSheetName={schematicSheetFor(section)}
      pinLabels={{ pin1: "POS", pin2: "NEG" }} connections={{ pin1: N(vbus), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.2} h={2.7} />} />
  </>
)

export default () => (
  <board width="100mm" height="80mm" routingDisabled>
    {/* Page declarations are presentation-only: they introduce no copper,
        footprint, component, pin or connection.  The exact Circuit JSON is
        fitted one page at a time by render_schematic_pdf.mjs. */}
    <schematicsheet name="input"
      displayName="BATTERY INPUT — JLC fits 3568 holder only / USER FIT F1 0297010.WXNV 10 A, 32 VDC, 1 kA interrupt / external UV disconnect >=9.0 V / no active OVP" sheetIndex={1} />
    <schematicsheet name="input_enable"
      displayName="POWER ENABLE — SW1 hard-off control / OFF-state and ground test points" sheetIndex={2} />
    <schematicsheet name="usba_supply"
      displayName="USB-A REGULATOR — U1 TPSM63610RDFR / 6 A continuous / SW and VCC intentionally open per TI" sheetIndex={3} />
    <schematicsheet name="usba_breaker"
      displayName="USB-A AGGREGATE PROTECTION — U9 TPS259827 no-OVLO circuit breaker" sheetIndex={4} />
    <schematicsheet name="usba_signatures"
      displayName="USB-A CHARGING SIGNATURES — TPS2513A / no upstream data / U8 channel 2 open" sheetIndex={5} />
    <schematicsheet name="usba_port_1"
      displayName="USB-A PORT 1 — independent TPS2559 current limit / POWER ONLY" sheetIndex={6} />
    <schematicsheet name="usba_port_2"
      displayName="USB-A PORT 2 — independent TPS2559 current limit / POWER ONLY" sheetIndex={7} />
    <schematicsheet name="usba_port_3"
      displayName="USB-A PORT 3 — independent TPS2559 current limit / POWER ONLY" sheetIndex={8} />
    <schematicsheet name="usbc_supply"
      displayName="USB-C SUPPLY — U2 TPSM63604RDLR / 5.15 V / 15 mV reserve / SW and VCC intentionally open per TI" sheetIndex={9} />
    <schematicsheet name="usbc_output"
      displayName="USB-C OUTPUT — fixed 5 V / no PD or data / D+/D−, SBU and unused U3 status pins open" sheetIndex={10} />

    {/* Input order is a safety property: terminal -> fuse -> reverse-FET ->
        TVS/damping. A Littelfuse 0297010.WXNV 10 A MINI blade is user-fitted
        in the F1 holder after assembly. */}
    <chip name="J1" supplierPartNumbers={{ jlcpcb: ["C3817933"] }}
      manufacturerPartNumber="1715022"
      schSectionName="Input protection and enable" schSheetName="input"
      pinLabels={{ pin1: "BAT_POS", pin2: "BAT_NEG" }}
      connections={{ pin1: N("BAT_POS"), pin2: N("GND") }} footprint={<InputTerminal />} />
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["C5249699"] }}
      manufacturerPartNumber="3568"
      schSectionName="Input protection and enable" schSheetName="input"
      pinLabels={{ pin1: "FUSE_A", pin2: "FUSE_B" }}
      connections={{ pin1: N("BAT_POS"), pin2: N("VBAT_FUSED") }} footprint={<BladeFuse />} />
    <chip name="Q1" supplierPartNumbers={{ jlcpcb: ["C264098"] }}
      manufacturerPartNumber="DMP3013SFV-7"
      schSectionName="Input protection and enable" schSheetName="input"
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D1", pin6: "D2", pin7: "D3", pin8: "D4" }}
      schPinArrangement={{ leftSide: [5, 6, 7, 8], bottomSide: [4], rightSide: [1, 2, 3] }}
      connections={{ pin1: N("VIN"), pin2: N("VIN"), pin3: N("VIN"), pin4: N("RPP_GATE"), pin5: N("VBAT_FUSED"), pin6: N("VBAT_FUSED"), pin7: N("VBAT_FUSED"), pin8: N("VBAT_FUSED") }}
      footprint={<TwoSided pins={8} pitch={0.65} span={3.3} />} />
    <chip name="D5" supplierPartNumbers={{ jlcpcb: ["C124196"] }}
      manufacturerPartNumber="BZT52C12-7-F"
      schSectionName="Input protection and enable" schSheetName="input"
      schPinArrangement={{ topSide: [1], bottomSide: [2] }}
      pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: N("VIN"), pin2: N("RPP_GATE") }}
      footprint={<Pol2 dx={1.35} w={1.2} h={1.5} />} />
    {/* The 200k:100k gate divider bounds VGS using Q1's full +/-10uA gate-
        leakage limit; D5 remains a secondary transient clamp. */}
    <R2 name="R22" value="100k" a="VIN" b="RPP_DIV" jlc="C25803" section="Input protection and enable" />
    <R2 name="R23" value="100k" a="RPP_DIV" b="RPP_GATE" jlc="C25803" section="Input protection and enable" />
    <R2 name="R1" value="100k" a="RPP_GATE" b="GND" jlc="C25803" section="Input protection and enable" />
    <chip name="D1" supplierPartNumbers={{ jlcpcb: ["C83846"] }}
      manufacturerPartNumber="SMBJ15A"
      schSectionName="Input protection and enable" schSheetName="input"
      pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: N("VIN"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.1} h={2.4} />} />
    <chip name="C1" supplierPartNumbers={{ jlcpcb: ["C88744"] }}
      manufacturerPartNumber="35TZV100M6.3X8"
      schSectionName="Input protection and enable" schSheetName="input"
      pinLabels={{ pin1: "POS", pin2: "NEG" }} connections={{ pin1: N("VIN"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.2} h={2.7} />} />

    {/* One shared high-value pull-up minimizes OFF-state battery drain. SW1
        hard-grounds both module enables in OFF; its unused throw is NC. */}
    <R2 name="R2" value="1M" a="VIN" b="EN_BUS" jlc="C22935" section="Input enable and verification" />
    <chip name="SW1" supplierPartNumbers={{ jlcpcb: ["C273394"] }}
      manufacturerPartNumber="EG1218"
      schSectionName="Input enable and verification" schSheetName="input_enable"
      pinLabels={{ pin1: "OFF_GND", pin2: "COMMON", pin3: "ON_NC" }}
      connections={{ pin1: N("GND"), pin2: N("EN_BUS") }} footprint={<SlideSwitch />} />

    {/* U1: 6 A continuous / 7.5 A peak USB-A bank. Two 10 uF/50 V inputs,
        six characterized 22 uF/16 V X7R outputs plus a 100 uF polymer bulk
        part, 1 MHz, auto mode, spread spectrum with tone correction, and a
        custom 5.12 V nominal setpoint. The ceramic bank clears TI's 75 uF
        effective-capacitance minimum after tolerance, temperature and DC-bias
        derating. No feed-forward branch is fitted: C22's permitted low-ESR
        polymer corner places an output-capacitor ESR zero below the 200 kHz
        boundary where TPSM63610 explicitly forbids CFF. */}
    <chip name="U1" supplierPartNumbers={{ jlcpcb: ["C7125816"] }}
      manufacturerPartNumber="TPSM63610RDFR"
      schSectionName="USB-A supply" schSheetName="usba_supply"
      pinLabels={{
        pin1: "VIN1", pin2: "RBOOT", pin3: "CBOOT", pin4: "SW", pin5: "VLDOIN", pin6: "VCC",
        pin7: "AGND1", pin8: "FB", pin9: "VOUT1", pin10: "VOUT2", pin11: "AGND2", pin12: "RT",
        pin13: "PG", pin14: "SPSP", pin15: "SYNC_MODE", pin16: "NC", pin17: "EN", pin18: "VIN2",
        pin19: "PGND1", pin20: "PGND2", pin21: "AGND3", pin22: "AGND4",
      }}
      connections={{
        pin1: N("VIN"), pin2: N("BOOT_A_R"), pin3: N("BOOT_A_C"), pin5: N("N5VA_RAW"),
        pin7: N("GND"), pin8: N("FB_A"), pin9: N("N5VA_RAW"), pin10: N("N5VA_RAW"), pin11: N("GND"),
        pin12: N("RT_A"), pin13: N("PG_A"), pin14: N("SPSP_A"), pin15: N("GND"), pin17: N("EN_BUS"),
        pin18: N("VIN"), pin19: N("GND"), pin20: N("GND"), pin21: N("GND"), pin22: N("GND"),
      }} footprint={<TwoSided pins={22} pitch={0.65} span={7.5} />} />
    <capacitor name="C2" capacitance="10uF" footprint="1210"
      schSectionName="USB-A supply" schSheetName="usba_supply"
      schX="-12.0mm" schY="-4.8mm" schRotation="270deg"
      supplierPartNumbers={{ jlcpcb: ["C77102"] }} />
    <group name="c2_vin_label" schSheetName="usba_supply">
      <netlabel net="VIN" connectsTo={sel.C2.pin1}
        schX="-12.0mm" schY="-4.0mm" anchorSide="bottom" />
    </group>
    <group name="c2_gnd_label" schSheetName="usba_supply">
      <netlabel net="GND" connectsTo={sel.C2.pin2}
        schX="-12.0mm" schY="-5.6mm" anchorSide="top" />
    </group>
    <C2 name="C3" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210" section="USB-A supply" />
    <R2 name="R3" value="0" a="BOOT_A_R" b="BOOT_A_C" jlc="C21189" section="USB-A supply" />
    <R2 name="R4" value="15.8k" a="RT_A" b="GND" jlc="C22880" section="USB-A supply" />
    <R2 name="R5" value="41.2k" a="N5VA_RAW" b="FB_A" jlc="C855851" section="USB-A supply" />
    <R2 name="R6" value="10k" a="FB_A" b="GND" jlc="C95204" section="USB-A supply" />
    <R2 name="R7" value="100k" a="N5VA_RAW" b="PG_A" jlc="C25803" section="USB-A supply" />
    <R2 name="R8" value="20k" a="SPSP_A" b="GND" jlc="C4184" section="USB-A supply" />
    {[6, 7, 8, 24, 25, 26].map((c) => <C2 key={`ca${c}`} name={`C${c}`} value="22uF" a="N5VA_RAW" b="GND" jlc="C342660" fp="1210" section="USB-A supply" />)}
    <capacitor name="C22" capacitance="100uF" supplierPartNumbers={{ jlcpcb: ["C2919856"] }}
      manufacturerPartNumber="160AV5K101M0606C"
      polarized
      schSectionName="USB-A supply" schSheetName="usba_supply"
      connections={{ pin1: N("N5VA_RAW"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.2} h={2.7} />} />

    {/* U9 is the no-OVLO circuit-breaker variant. R26 sets a machine-derived
        6.160-8.066 A charged threshold. Its worst-high is below U1's 10 A
        peak rating and is bounded by C29's <=45.962 ms interrupt corner;
        the exact board must qualify that short >8 A interval. C29's
        fully charged timer corner admits every <=10 ms
        coincident port peak; C30 slows dV/dt enough to satisfy TI's maximum
        ITIMER-capacitance startup relation. A persistent aggregate overload
        latches off, and cycling SW1 resets the latch. */}
    <chip name="U9" supplierPartNumbers={{ jlcpcb: ["C2155765"] }}
      manufacturerPartNumber="TPS259827ONRGET"
      schSectionName="USB-A aggregate protection" schSheetName="usba_breaker"
      pinLabels={{
        pin1: "IN1", pin2: "IN2", pin3: "IN3", pin4: "GND1", pin5: "GND2",
        pin6: "EN_UVLO", pin7: "ITIMER", pin8: "ILIM", pin9: "IMON_NC",
        pin10: "RETRY_DLY", pin11: "NRETRY_NC", pin12: "LDSTRT", pin13: "PG_NC",
        pin14: "GND3", pin15: "DVDT", pin16: "IN4", pin17: "OUT1", pin18: "OUT2",
        pin19: "OUT3", pin20: "OUT4", pin21: "OUT5", pin22: "OUT6", pin23: "OUT7",
        pin24: "OUT8", pin25: "IN_PAD", pin26: "GND_PAD",
      }}
      schPinArrangement={{
        leftSide: [1, 2, 3, 16, 25, 6, 7, 8, 15],
        rightSide: [17, 18, 19, 20, 21, 22, 23, 24],
        bottomSide: [4, 5, 10, 12, 14, 26],
        topSide: [9, 11, 13],
      }}
      connections={{
        pin1: N("N5VA_RAW"), pin2: N("N5VA_RAW"), pin3: N("N5VA_RAW"),
        pin4: N("GND"), pin5: N("GND"), pin6: N("N5VA_RAW"), pin7: N("ITIMER_A"),
        pin8: N("ILIM_BANK"), pin10: N("GND"), pin12: N("GND"), pin14: N("GND"),
        pin15: N("DVDT_BANK"),
        pin16: N("N5VA_RAW"), pin17: N("N5VA"), pin18: N("N5VA"), pin19: N("N5VA"),
        pin20: N("N5VA"), pin21: N("N5VA"), pin22: N("N5VA"), pin23: N("N5VA"),
        pin24: N("N5VA"), pin25: N("N5VA_RAW"), pin26: N("GND"),
      }} footprint={<TwoSided pins={26} pitch={0.5} span={4} />} />
    <R2 name="R26" value="210" a="ILIM_BANK" b="GND" jlc="C478880" section="USB-A aggregate protection" />
    <C2 name="C29" value="47nF" a="ITIMER_A" b="GND" jlc="C2220670" fp="1206" section="USB-A aggregate protection" />
    <C2 name="C30" value="3.3nF" a="DVDT_BANK" b="GND" jlc="C2239978" fp="0603" section="USB-A aggregate protection" />

    {/* U2: independent Pi rail. Three characterized 22 uF/16 V X7R parts
        clear the module's 30 uF effective-ceramic minimum after derating.
        No CFF is fitted because this mixed ceramic/polymer bank is not close
        to that minimum; its exact loop response remains a first-article
        frequency-response/load-step qualification. The cold-socket bank
        combines those ceramics with C23's qualified 115.2 uF polymer
        life-corner minimum to clear TPS25810's >=120 uF requirement. */}
    <chip name="U2" supplierPartNumbers={{ jlcpcb: ["C5219289"] }}
      manufacturerPartNumber="TPSM63604RDLR"
      schSectionName="USB-C regulated supply" schSheetName="usbc_supply"
      pinLabels={{
        pin1: "VIN1", pin2: "SW", pin3: "CBOOT", pin4: "RBOOT", pin5: "VLDOIN", pin6: "AGND1",
        pin7: "VCC", pin8: "VOUT1", pin9: "VOUT2", pin10: "FB", pin11: "AGND2", pin12: "RT",
        pin13: "PG", pin14: "EN_SYNC", pin15: "NC", pin16: "VIN2", pin17: "PGND1", pin18: "PGND2",
        pin19: "PGND3", pin20: "PGND4",
      }}
      schPinArrangement={{
        leftSide: [1, 16, 14, 3, 4],
        rightSide: [8, 9, 5, 10, 13],
        topSide: [2, 7, 15],
        bottomSide: [6, 11, 17, 18, 19, 20, 12],
      }}
      connections={{
        pin1: N("VIN"), pin3: N("BOOT_C_C"), pin4: N("BOOT_C_R"), pin5: N("N5VC_RAW"), pin6: N("GND"),
        pin8: N("N5VC_RAW"), pin9: N("N5VC_RAW"), pin10: N("FB_C"), pin11: N("GND"), pin12: N("RT_C"),
        pin13: N("PG_C"), pin14: N("EN_BUS"), pin16: N("VIN"), pin17: N("GND"), pin18: N("GND"),
        pin19: N("GND"), pin20: N("GND"),
      }} footprint={<TwoSided pins={20} pitch={0.65} span={5.5} />} />
    <C2 name="C4" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210"
      schX="18.2mm" schY="-5.2mm" section="USB-C regulated supply" />
    <C2 name="C5" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210"
      schX="17.8mm" schY="-4.28mm" section="USB-C regulated supply" />
    <R2 name="R9" value="0" a="BOOT_C_R" b="BOOT_C_C" jlc="C21189" section="USB-C regulated supply" />
    <R2 name="R10" value="13k" a="RT_C" b="GND" jlc="C22797" section="USB-C regulated supply" />
    <R2 name="R11" value="4.12k" a="N5VC_RAW" b="FB_C_TOP" jlc="C861436" section="USB-C regulated supply" />
    <R2 name="R24" value="24.3" a="FB_C_TOP" b="FB_C" jlc="C861251" section="USB-C regulated supply" />
    <R2 name="R12" value="1k" a="FB_C" b="GND" jlc="C110776" section="USB-C regulated supply" />
    <R2 name="R13" value="100k" a="N5VC_RAW" b="PG_C" jlc="C25803" section="USB-C regulated supply" />
    {[9, 10, 11].map((c) => <C2 key={`cc${c}`} name={`C${c}`} value="22uF" a="N5VC_RAW" b="GND" jlc="C342660" fp="1210" section="USB-C regulated supply" />)}
    <capacitor name="C23" capacitance="180uF" supplierPartNumbers={{ jlcpcb: ["C369910"] }}
      manufacturerPartNumber="160AV5K181M0606C"
      polarized
      schSectionName="USB-C regulated supply" schSheetName="usbc_supply"
      connections={{ pin1: N("N5VC_RAW"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.2} h={2.7} />} />

    {/* TPS25810 fixed 5 V Type-C source: attach-controlled VBUS, 3 A Rp and
        3.4 A nominal limit. IN1/IN2/AUX/EN/CHG/CHG_HI share the local rail.
        Unused open-drain status pins remain NC. */}
    <chip name="U3" supplierPartNumbers={{ jlcpcb: ["C473913"] }}
      manufacturerPartNumber="TPS25810RVCR"
      schSectionName="USB-C attach-controlled output" schSheetName="usbc_output"
      schX="-20mm" schY="-18mm"
      pinLabels={{
        pin1: "FAULT", pin2: "IN1A", pin3: "IN1B", pin4: "IN2", pin5: "AUX", pin6: "EN",
        pin7: "CHG", pin8: "CHG_HI", pin9: "REF_RTN", pin10: "REF", pin11: "CC1", pin12: "GND",
        pin13: "CC2", pin14: "OUT1", pin15: "OUT2", pin16: "DEBUG", pin17: "AUDIO", pin18: "POL",
        pin19: "UFP", pin20: "LD_DET", pin21: "EP",
      }}
      schWidth="3mm"
      schHeight="3.6mm"
      schPinArrangement={{
        leftSide: [9, 10, 2, 3, 4, 5, 6, 7, 8],
        rightSide: [1, 14, 15, 11, 13],
        topSide: [20, 19, 18, 17, 16],
        bottomSide: [12, 21],
      }}
      connections={{
        pin1: N("FAULT_C"), pin2: N("N5VC_RAW"), pin3: N("N5VC_RAW"), pin4: N("N5VC_RAW"),
        pin5: N("N5VC_RAW"), pin6: N("N5VC_RAW"), pin7: N("N5VC_RAW"), pin8: N("N5VC_RAW"),
        pin9: N("REF_RTN_C"), pin10: N("REF_C"), pin11: N("CC1"), pin12: N("GND"), pin13: N("CC2"),
        pin14: N("VBUSC"), pin15: N("VBUSC"), pin21: N("GND"),
      }} footprint={<TwoSided pins={21} pitch={0.5} span={4} />} />
    <C2 name="C12" value="100nF" a="N5VC_RAW" b="GND" jlc="C1525" section="USB-C attach-controlled output" />
    <C2 name="C13" value="10uF" a="VBUSC" b="GND" jlc="C39232" fp="1210" section="USB-C attach-controlled output" />
    <R2 name="R14" value="100k" a="REF_C" b="REF_RTN_C" jlc="C844888" section="USB-C attach-controlled output" />
    <R2 name="R15" value="100k" a="N5VC_RAW" b="FAULT_C" jlc="C25803"
      schX="-21.8mm" schY="-14.4mm" section="USB-C attach-controlled output" />
    <chip name="D6" supplierPartNumbers={{ jlcpcb: ["C97502"] }}
      manufacturerPartNumber="TPD2EUSB30DRTR"
      schSectionName="USB-C attach-controlled output" schSheetName="usbc_output"
      pinLabels={{ pin1: "IO1", pin2: "IO2", pin3: "GND" }}
      connections={{ pin1: N("CC1"), pin2: N("CC2"), pin3: N("GND") }}
      footprint={<TwoSided pins={3} pitch={0.5} span={1.4} />} />
    <chip name="J5" supplierPartNumbers={{ jlcpcb: ["C3020560"] }}
      manufacturerPartNumber="USB4105-GF-A"
      schSectionName="USB-C attach-controlled output" schSheetName="usbc_output"
      schX="-14.5mm" schY="-18.9mm"
      schWidth="3mm" schHeight="2.8mm"
      schPinArrangement={{
        leftSide: [3, 4, 5, 6, 11, 12, 13, 14],
        rightSide: [2, 7, 10, 15],
        bottomSide: [1, 8, 9, 16, 17],
      }}
      pinLabels={{
        pin1: "GNDA1", pin2: "VBUSA4", pin3: "CC1A5", pin4: "DPA6", pin5: "DMA7", pin6: "SBU1A8",
        pin7: "VBUSA9", pin8: "GNDA12", pin9: "GNDB1", pin10: "VBUSB4", pin11: "CC2B5", pin12: "DPB6",
        pin13: "DMB7", pin14: "SBU2B8", pin15: "VBUSB9", pin16: "GNDB12", pin17: "SHIELD",
      }}
      connections={{
        pin1: N("GND"), pin2: N("VBUSC"), pin3: N("CC1"), pin7: N("VBUSC"), pin8: N("GND"),
        pin9: N("GND"), pin10: N("VBUSC"), pin11: N("CC2"), pin15: N("VBUSC"), pin16: N("GND"),
        pin17: N("GND"),
      }} footprint={<UsbC />} />

    {/* Three independently current-limited USB-A outputs. */}
    <Tps2559 u="U4" cin="C14" cout="C17" rilim="R16" rflt="R17" fault="FAULT_A1" ilim="ILIM_A1" vbus="VBUSA1" section="USB-A port 1" />
    <Tps2559 u="U5" cin="C15" cout="C18" rilim="R18" rflt="R19" fault="FAULT_A2" ilim="ILIM_A2" vbus="VBUSA2" section="USB-A port 2" />
    <Tps2559 u="U6" cin="C16" cout="C19" rilim="R20" rflt="R21" fault="FAULT_A3" ilim="ILIM_A3" vbus="VBUSA3" section="USB-A port 3" />

    {/* Presentation-only labels make three safety-critical multi-pin buses
        explicit at the component boundary. They add no source trace or copper:
        the connected pin already owns the named electrical net. */}
    <group name="q1_fused_input_label" schSheetName="input">
      <netlabel net="VBAT_FUSED" connectsTo={sel.Q1.pin5}
        schX="-30.1mm" schY="-5.36mm" anchorSide="right" />
    </group>
    <group name="u9_raw_input_label" schSheetName="usba_breaker">
      <netlabel net="N5VA_RAW" connectsTo={sel.U9.pin1}
        schX="7.0mm" schY="-4.05mm" anchorSide="right" />
    </group>
    <group name="u3_vbus_output_label" schSheetName="usbc_output">
      <netlabel net="VBUSC" connectsTo={sel.U3.pin14}
        schX="-18.1mm" schY="-17.8mm" anchorSide="left" />
    </group>
    <group name="u1_raw_output_label" schSheetName="usba_supply">
      <netlabel net="N5VA_RAW" connectsTo={sel.U1.pin9}
        schX="-12.4mm" schY="-7.0mm" anchorSide="right" />
    </group>
    <group name="u2_vin_input_label" schSheetName="usbc_supply">
      <netlabel net="VIN" connectsTo={sel.U2.pin1}
        schX="19.8mm" schY="-4.19mm" anchorSide="right" />
    </group>

    {/* The TPS2559 parallel input/output lands are one electrical node per
        side. Explicit labels sit level with the top input pin; ground and ILIM
        now leave on separate symbol sides, so their text cannot merge. */}
    <group name="u4_input_label" schSheetName="usba_port_1">
      <netlabel net="N5VA" connectsTo={sel.U4.pin2}
        schX="-11.3mm" schY="-22.82mm" anchorSide="right" />
    </group>
    <group name="u5_input_label" schSheetName="usba_port_2">
      <netlabel net="N5VA" connectsTo={sel.U5.pin2}
        schX="0.5mm" schY="-22.82mm" anchorSide="right" />
    </group>
    <group name="u6_input_label" schSheetName="usba_port_3">
      <netlabel net="N5VA" connectsTo={sel.U6.pin2}
        schX="12.35mm" schY="-22.82mm" anchorSide="right" />
    </group>
    <group name="u4_output_label" schSheetName="usba_port_1">
      <netlabel net="VBUSA1" connectsTo={sel.U4.pin7}
        schX="-4.0mm" schY="-19.78mm" anchorSide="left" />
    </group>
    <group name="u5_output_label" schSheetName="usba_port_2">
      <netlabel net="VBUSA2" connectsTo={sel.U5.pin7}
        schX="7.75mm" schY="-19.78mm" anchorSide="left" />
    </group>
    <group name="u6_output_label" schSheetName="usba_port_3">
      <netlabel net="VBUSA3" connectsTo={sel.U6.pin7}
        schX="19.6mm" schY="-19.78mm" anchorSide="left" />
    </group>

    <UsbLc name="D2" vbus="VBUSA1" dm="DM_A1" dp="DP_A1" section="USB-A port 1" />
    <UsbLc name="D3" vbus="VBUSA2" dm="DM_A2" dp="DP_A2" section="USB-A port 2" />
    <UsbLc name="D4" vbus="VBUSA3" dm="DM_A3" dp="DP_A3" section="USB-A port 3" />

    {[
      ["J2", "VBUSA1", "DM_A1", "DP_A1", "USB-A port 1"],
      ["J3", "VBUSA2", "DM_A2", "DP_A2", "USB-A port 2"],
      ["J4", "VBUSA3", "DM_A3", "DP_A3", "USB-A port 3"],
    ].map(([j, vbus, dm, dp, section]) => (
      <chip key={j} name={j} supplierPartNumbers={{ jlcpcb: ["C5815149"] }}
        manufacturerPartNumber="USB1130-15-A"
        schSectionName={section} schSheetName={schematicSheetFor(section)}
        pinLabels={{ pin1: "VBUS", pin2: "DM", pin3: "DP", pin4: "GND", pin5: "SHIELD" }}
        connections={{ pin1: N(vbus), pin2: N(dm), pin3: N(dp), pin4: N("GND"), pin5: N("GND") }}
        footprint={<UsbA />} />
    ))}

    {/* Two dual-port signature controllers; U8's unused second channel is an
        intentional open circuit and is called out on its schematic page. */}
    <chip name="U7" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      manufacturerPartNumber="TPS2513ADBVR"
      schSectionName="USB-A charging signatures" schSheetName="usba_signatures"
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2", pin4: "DM2", pin5: "IN", pin6: "DM1" }}
      connections={{ pin1: N("DP_A1"), pin2: N("GND"), pin3: N("DP_A2"), pin4: N("DM_A2"), pin5: N("N5VA"), pin6: N("DM_A1") }}
      footprint="sot23_6" />
    <chip name="U8" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      manufacturerPartNumber="TPS2513ADBVR"
      schSectionName="USB-A charging signatures" schSheetName="usba_signatures"
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2_NC", pin4: "DM2_NC", pin5: "IN", pin6: "DM1" }}
      connections={{ pin1: N("DP_A3"), pin2: N("GND"), pin5: N("N5VA"), pin6: N("DM_A3") }}
      footprint="sot23_6" />
    <C2 name="C20" value="100nF" a="N5VA" b="GND" jlc="C1525" section="USB-A charging signatures" />
    <C2 name="C21" value="100nF" a="N5VA" b="GND" jlc="C1525" section="USB-A charging signatures" />

    {/* Bring out only slow power/status nodes needed for first-article proof. */}
    {[
      ["TP1", "VIN", "Input protection and enable"],
      ["TP2", "N5VA", "USB-A aggregate protection"],
      ["TP3", "N5VC_RAW", "USB-C regulated supply"],
      ["TP4", "VBUSC", "USB-C attach-controlled output"],
      ["TP5", "EN_BUS", "Input enable and verification"],
      ["TP6", "PG_A", "USB-A supply"],
      ["TP7", "PG_C", "USB-C regulated supply"],
      ["TP8", "FAULT_C", "USB-C attach-controlled output"],
      ["TP9", "FAULT_A1", "USB-A port 1"],
      ["TP10", "FAULT_A2", "USB-A port 2"],
      ["TP11", "FAULT_A3", "USB-A port 3"],
      ["TP12", "GND", "Input enable and verification"],
    ].map(([tp, net, section]) => (
      <testpoint key={tp} name={tp} footprintVariant="pad" padShape="circle" padDiameter="1.5mm"
        schSectionName={section} schSheetName={schematicSheetFor(section)}
        schX={tp === "TP8" ? "-17.2mm" : undefined}
        schY={tp === "TP8" ? "-16.5mm" : undefined}
        connections={{ pin1: N(net) }} />
    ))}
  </board>
)

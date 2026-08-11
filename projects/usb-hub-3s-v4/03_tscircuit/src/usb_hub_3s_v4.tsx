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

const N = (name: string) => `net.${name}`

const R2 = ({ name, value, a, b, jlc, fp = "0603" }: any) => (
  <resistor name={name} resistance={value} footprint={fp}
    supplierPartNumbers={{ jlcpcb: [jlc] }}
    connections={{ pin1: N(a), pin2: N(b) }} />
)

const C2 = ({ name, value, a, b, jlc, fp = "0402" }: any) => (
  <capacitor name={name} capacitance={value} footprint={fp}
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

const UsbLc = ({ name, vbus, dm, dp }: any) => (
  <chip name={name} supplierPartNumbers={{ jlcpcb: ["C7519"] }}
    pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
    connections={{ pin1: N(dp), pin2: N("GND"), pin3: N(dm), pin4: N(dm), pin5: N(vbus), pin6: N(dp) }}
    footprint="sot23_6" />
)

const Tps2557 = ({ u, cin, cout, rilim, rflt, fault, ilim, vbus }: any) => (
  <group name={`${u}_port_switch`}>
    <chip name={u} supplierPartNumbers={{ jlcpcb: ["C130056"] }}
      pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "EN", pin5: "ILIM", pin6: "OUT1", pin7: "OUT2", pin8: "FAULT", pin9: "EP" }}
      connections={{ pin1: N("GND"), pin2: N("N5VA"), pin3: N("N5VA"), pin4: N("N5VA"), pin5: N(ilim), pin6: N(vbus), pin7: N(vbus), pin8: N(fault), pin9: N("GND") }}
      footprint={<TwoSided pins={9} pitch={0.65} span={3.2} />} />
    <C2 name={cin} value="100nF" a="N5VA" b="GND" jlc="C1525" />
    <R2 name={rilim} value="39.2k" a={ilim} b="GND" jlc="C861871" />
    <R2 name={rflt} value="100k" a="N5VA" b={fault} jlc="C25803" />
    <chip name={cout} supplierPartNumbers={{ jlcpcb: ["C264054"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }} connections={{ pin1: N(vbus), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.2} h={2.7} />} />
  </group>
)

export default () => (
  <board width="100mm" height="80mm" routingDisabled>
    {/* Input order is a safety property: terminal -> fuse -> reverse-FET ->
        TVS/damping. The 10 A MINI fuse blade is user-installed in F1. */}
    <chip name="J1" supplierPartNumbers={{ jlcpcb: ["C3817933"] }}
      pinLabels={{ pin1: "BAT_POS", pin2: "BAT_NEG" }}
      connections={{ pin1: N("BAT_POS"), pin2: N("GND") }} footprint={<InputTerminal />} />
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["C5249699"] }}
      pinLabels={{ pin1: "FUSE_A", pin2: "FUSE_B" }}
      connections={{ pin1: N("BAT_POS"), pin2: N("VBAT_FUSED") }} footprint={<BladeFuse />} />
    <chip name="Q1" supplierPartNumbers={{ jlcpcb: ["C264098"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D1", pin6: "D2", pin7: "D3", pin8: "D4" }}
      connections={{ pin1: N("VIN"), pin2: N("VIN"), pin3: N("VIN"), pin4: N("RPP_GATE"), pin5: N("VBAT_FUSED"), pin6: N("VBAT_FUSED"), pin7: N("VBAT_FUSED"), pin8: N("VBAT_FUSED") }}
      footprint={<TwoSided pins={8} pitch={0.65} span={3.3} />} />
    <chip name="D5" supplierPartNumbers={{ jlcpcb: ["C124196"] }}
      pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: N("VIN"), pin2: N("RPP_GATE") }}
      footprint={<Pol2 dx={1.35} w={1.2} h={1.5} />} />
    <R2 name="R1" value="1M" a="RPP_GATE" b="GND" jlc="C22935" />
    <chip name="D1" supplierPartNumbers={{ jlcpcb: ["C83846"] }}
      pinLabels={{ pin1: "K", pin2: "A" }} connections={{ pin1: N("VIN"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.1} h={2.4} />} />
    <chip name="C1" supplierPartNumbers={{ jlcpcb: ["C88744"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }} connections={{ pin1: N("VIN"), pin2: N("GND") }}
      footprint={<Pol2 dx={2.2} w={2.2} h={2.7} />} />

    {/* One shared high-value pull-up minimizes OFF-state battery drain. SW1
        hard-grounds both module enables in OFF; its unused throw is NC. */}
    <R2 name="R2" value="1M" a="VIN" b="EN_BUS" jlc="C22935" />
    <chip name="SW1" supplierPartNumbers={{ jlcpcb: ["C273394"] }}
      pinLabels={{ pin1: "OFF_GND", pin2: "COMMON", pin3: "ON_NC" }}
      connections={{ pin1: N("GND"), pin2: N("EN_BUS") }} footprint={<SlideSwitch />} />

    {/* U1: 6 A continuous / 7.5 A peak USB-A bank. Two 10 uF/50 V inputs,
        three 47 uF/10 V X7R outputs, 1 MHz, auto mode, spread spectrum with
        tone correction, and a custom 5.12 V nominal setpoint. */}
    <chip name="U1" supplierPartNumbers={{ jlcpcb: ["C7125816"] }}
      pinLabels={{
        pin1: "VIN1", pin2: "RBOOT", pin3: "CBOOT", pin4: "SW", pin5: "VLDOIN", pin6: "VCC",
        pin7: "AGND1", pin8: "FB", pin9: "VOUT1", pin10: "VOUT2", pin11: "AGND2", pin12: "RT",
        pin13: "PG", pin14: "SPSP", pin15: "SYNC_MODE", pin16: "NC", pin17: "EN", pin18: "VIN2",
        pin19: "PGND1", pin20: "PGND2", pin21: "AGND3", pin22: "AGND4",
      }}
      connections={{
        pin1: N("VIN"), pin2: N("BOOT_A_R"), pin3: N("BOOT_A_C"), pin5: N("N5VA"),
        pin7: N("GND"), pin8: N("FB_A"), pin9: N("N5VA"), pin10: N("N5VA"), pin11: N("GND"),
        pin12: N("RT_A"), pin13: N("PG_A"), pin14: N("SPSP_A"), pin15: N("GND"), pin17: N("EN_BUS"),
        pin18: N("VIN"), pin19: N("GND"), pin20: N("GND"), pin21: N("GND"), pin22: N("GND"),
      }} footprint={<TwoSided pins={22} pitch={0.65} span={7.5} />} />
    <C2 name="C2" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210" />
    <C2 name="C3" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210" />
    <R2 name="R3" value="0" a="BOOT_A_R" b="BOOT_A_C" jlc="C21189" />
    <R2 name="R4" value="15.8k" a="RT_A" b="GND" jlc="C22880" />
    <R2 name="R5" value="41.2k" a="N5VA" b="FB_A" jlc="C855851" />
    <R2 name="R6" value="10k" a="FB_A" b="GND" jlc="C95204" />
    <R2 name="R7" value="100k" a="N5VA" b="PG_A" jlc="C25803" />
    <R2 name="R8" value="20k" a="SPSP_A" b="GND" jlc="C4184" />
    {[6, 7, 8].map((c) => <C2 key={`ca${c}`} name={`C${c}`} value="47uF" a="N5VA" b="GND" jlc="C23692991" fp="1210" />)}

    {/* U2: independent Pi rail. The three 47 uF output capacitors are the
        module output bank and TPS25810's required >=120 uF cold-socket input
        bank because U2 and U3 form one adjacent power cell. */}
    <chip name="U2" supplierPartNumbers={{ jlcpcb: ["C5219289"] }}
      pinLabels={{
        pin1: "VIN1", pin2: "SW", pin3: "CBOOT", pin4: "RBOOT", pin5: "VLDOIN", pin6: "AGND1",
        pin7: "VCC", pin8: "VOUT1", pin9: "VOUT2", pin10: "FB", pin11: "AGND2", pin12: "RT",
        pin13: "PG", pin14: "EN_SYNC", pin15: "NC", pin16: "VIN2", pin17: "PGND1", pin18: "PGND2",
        pin19: "PGND3", pin20: "PGND4",
      }}
      connections={{
        pin1: N("VIN"), pin3: N("BOOT_C_C"), pin4: N("BOOT_C_R"), pin5: N("N5VC_RAW"), pin6: N("GND"),
        pin8: N("N5VC_RAW"), pin9: N("N5VC_RAW"), pin10: N("FB_C"), pin11: N("GND"), pin12: N("RT_C"),
        pin13: N("PG_C"), pin14: N("EN_BUS"), pin16: N("VIN"), pin17: N("GND"), pin18: N("GND"),
        pin19: N("GND"), pin20: N("GND"),
      }} footprint={<TwoSided pins={20} pitch={0.65} span={5.5} />} />
    <C2 name="C4" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210" />
    <C2 name="C5" value="10uF" a="VIN" b="GND" jlc="C77102" fp="1210" />
    <R2 name="R9" value="0" a="BOOT_C_R" b="BOOT_C_C" jlc="C21189" />
    <R2 name="R10" value="13k" a="RT_C" b="GND" jlc="C22797" />
    <R2 name="R11" value="41.7k" a="N5VC_RAW" b="FB_C" jlc="C861394" />
    <R2 name="R12" value="10k" a="FB_C" b="GND" jlc="C95204" />
    <R2 name="R13" value="100k" a="N5VC_RAW" b="PG_C" jlc="C25803" />
    {[9, 10, 11].map((c) => <C2 key={`cc${c}`} name={`C${c}`} value="47uF" a="N5VC_RAW" b="GND" jlc="C23692991" fp="1210" />)}

    {/* TPS25810 fixed 5 V Type-C source: attach-controlled VBUS, 3 A Rp and
        3.4 A nominal limit. IN1/IN2/AUX/EN/CHG/CHG_HI share the local rail.
        Unused open-drain status pins remain NC. */}
    <chip name="U3" supplierPartNumbers={{ jlcpcb: ["C473913"] }}
      pinLabels={{
        pin1: "FAULT", pin2: "IN1A", pin3: "IN1B", pin4: "IN2", pin5: "AUX", pin6: "EN",
        pin7: "CHG", pin8: "CHG_HI", pin9: "REF_RTN", pin10: "REF", pin11: "CC1", pin12: "GND",
        pin13: "CC2", pin14: "OUT1", pin15: "OUT2", pin16: "DEBUG", pin17: "AUDIO", pin18: "POL",
        pin19: "UFP", pin20: "LD_DET", pin21: "EP",
      }}
      connections={{
        pin1: N("FAULT_C"), pin2: N("N5VC_RAW"), pin3: N("N5VC_RAW"), pin4: N("N5VC_RAW"),
        pin5: N("N5VC_RAW"), pin6: N("N5VC_RAW"), pin7: N("N5VC_RAW"), pin8: N("N5VC_RAW"),
        pin9: N("REF_RTN_C"), pin10: N("REF_C"), pin11: N("CC1"), pin12: N("GND"), pin13: N("CC2"),
        pin14: N("VBUSC"), pin15: N("VBUSC"), pin21: N("GND"),
      }} footprint={<TwoSided pins={21} pitch={0.5} span={4} />} />
    <C2 name="C12" value="100nF" a="N5VC_RAW" b="GND" jlc="C1525" />
    <C2 name="C13" value="10uF" a="VBUSC" b="GND" jlc="C39232" fp="1210" />
    <R2 name="R14" value="100k" a="REF_C" b="REF_RTN_C" jlc="C844888" />
    <R2 name="R15" value="100k" a="N5VC_RAW" b="FAULT_C" jlc="C25803" />
    <chip name="D6" supplierPartNumbers={{ jlcpcb: ["C97502"] }}
      pinLabels={{ pin1: "IO1", pin2: "IO2", pin3: "GND" }}
      connections={{ pin1: N("CC1"), pin2: N("CC2"), pin3: N("GND") }}
      footprint={<TwoSided pins={3} pitch={0.5} span={1.4} />} />
    <chip name="J5" supplierPartNumbers={{ jlcpcb: ["C3020560"] }}
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
    <Tps2557 u="U4" cin="C14" cout="C17" rilim="R16" rflt="R17" fault="FAULT_A1" ilim="ILIM_A1" vbus="VBUSA1" />
    <Tps2557 u="U5" cin="C15" cout="C18" rilim="R18" rflt="R19" fault="FAULT_A2" ilim="ILIM_A2" vbus="VBUSA2" />
    <Tps2557 u="U6" cin="C16" cout="C19" rilim="R20" rflt="R21" fault="FAULT_A3" ilim="ILIM_A3" vbus="VBUSA3" />

    {/* Two dual-port signature controllers; U8's unused second channel is NC. */}
    <chip name="U7" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2", pin4: "DM2", pin5: "IN", pin6: "DM1" }}
      connections={{ pin1: N("DP_A1"), pin2: N("GND"), pin3: N("DP_A2"), pin4: N("DM_A2"), pin5: N("N5VA"), pin6: N("DM_A1") }}
      footprint="sot23_6" />
    <chip name="U8" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2_NC", pin4: "DM2_NC", pin5: "IN", pin6: "DM1" }}
      connections={{ pin1: N("DP_A3"), pin2: N("GND"), pin5: N("N5VA"), pin6: N("DM_A3") }}
      footprint="sot23_6" />
    <C2 name="C20" value="100nF" a="N5VA" b="GND" jlc="C1525" />
    <C2 name="C21" value="100nF" a="N5VA" b="GND" jlc="C1525" />

    <UsbLc name="D2" vbus="VBUSA1" dm="DM_A1" dp="DP_A1" />
    <UsbLc name="D3" vbus="VBUSA2" dm="DM_A2" dp="DP_A2" />
    <UsbLc name="D4" vbus="VBUSA3" dm="DM_A3" dp="DP_A3" />

    {[
      ["J2", "VBUSA1", "DM_A1", "DP_A1"],
      ["J3", "VBUSA2", "DM_A2", "DP_A2"],
      ["J4", "VBUSA3", "DM_A3", "DP_A3"],
    ].map(([j, vbus, dm, dp]) => (
      <chip key={j} name={j} supplierPartNumbers={{ jlcpcb: ["C5815149"] }}
        pinLabels={{ pin1: "VBUS", pin2: "DM", pin3: "DP", pin4: "GND", pin5: "SHIELD" }}
        connections={{ pin1: N(vbus), pin2: N(dm), pin3: N(dp), pin4: N("GND"), pin5: N("GND") }}
        footprint={<UsbA />} />
    ))}

    {/* Bring out only slow power/status nodes needed for first-article proof. */}
    {[
      ["TP1", "VIN"], ["TP2", "N5VA"], ["TP3", "N5VC_RAW"], ["TP4", "VBUSC"],
      ["TP5", "EN_BUS"], ["TP6", "PG_A"], ["TP7", "PG_C"], ["TP8", "FAULT_C"],
      ["TP9", "FAULT_A1"], ["TP10", "FAULT_A2"], ["TP11", "FAULT_A3"], ["TP12", "GND"],
    ].map(([tp, net]) => (
      <testpoint key={tp} name={tp} footprintVariant="pad" padShape="circle" padDiameter="1.5mm"
        connections={{ pin1: N(net) }} />
    ))}
  </board>
)

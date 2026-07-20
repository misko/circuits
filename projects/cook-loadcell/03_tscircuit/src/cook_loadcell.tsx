// cook-loadcell — tscircuit render (node-for-node from the KiCad fab-of-record)
//
// Fab-of-record (authoritative, canon S-DSL): ../../04_kicad/cook_loadcell.kicad_pcb
// This is a SECOND-OPINION render only. 33 KiCad footprints, 16 real nets + 2 U1
// no-connects (VBG pin6, XO pin13) + 4 non-electrical M3 mounting holes.
//
// Net-name normalization (KiCad -> tscircuit net label):
//   3V3 -> N3V3 , 5V -> N5V  (tscircuit selectors dislike a leading digit);
//   every other KiCad net name is preserved verbatim. Full map in verification/notes.md.
//
// Connectivity is authored via each element's `connections` prop -> `net.<NAME>`, so the
// netlist is correct by construction. Placement/routing is auto (not fidelity-relevant).

export default () => (
  <board width="40mm" height="40mm">
    {/* ---- HX711 24-bit bridge ADC (U1, SOIC-16) ---- */}
    <chip
      name="U1"
      footprint="soic16_p1.27mm"
      supplierPartNumbers={{ jlcpcb: ["C43656"] }}
      pinLabels={{
        pin1: "VSUP", pin2: "BASE", pin3: "AVDD", pin4: "VFB",
        pin5: "AGND", pin6: "VBG", pin7: "INA_N", pin8: "INA_P",
        pin9: "INB_N", pin10: "INB_P", pin11: "PD_SCK", pin12: "DOUT",
        pin13: "XO", pin14: "XI", pin15: "RATE", pin16: "DVDD",
      }}
      connections={{
        pin1: "net.N5V",
        pin2: "net.BASE",
        pin3: "net.E_PLUS",
        pin4: "net.AVDD_FB",
        pin5: "net.GND",
        // pin6 VBG: no-connect (KiCad unconnected-(U1-VBG-Pad6))
        pin7: "net.S_MINUS",
        pin8: "net.S_PLUS",
        pin9: "net.GND",
        pin10: "net.GND",
        pin11: "net.CLK",
        pin12: "net.DAT",
        // pin13 XO: no-connect (KiCad unconnected-(U1-XO-Pad13))
        pin14: "net.GND",
        pin15: "net.RATE_SEL",
        pin16: "net.N3V3",
      }}
    />

    {/* ---- Excitation pass PNP (Q1, SOT-23: 1=B 2=E 3=C) ---- */}
    <chip
      name="Q1"
      footprint="sot23"
      supplierPartNumbers={{ jlcpcb: ["C8542"] }}
      pinLabels={{ pin1: "B", pin2: "E", pin3: "C" }}
      connections={{ pin1: "net.BASE", pin2: "net.N5V", pin3: "net.E_PLUS" }}
    />

    {/* ---- Analog regulator divider ---- */}
    <resistor name="R1" resistance="20k" footprint="0603"
      connections={{ pin1: "net.E_PLUS", pin2: "net.AVDD_FB" }} />
    <resistor name="R2" resistance="8.2k" footprint="0603"
      connections={{ pin1: "net.AVDD_FB", pin2: "net.GND" }} />
    <resistor name="R7" resistance="100" footprint="0603"
      connections={{ pin1: "net.SH", pin2: "net.GND" }} />

    {/* ---- Decoupling / bulk caps ---- */}
    <capacitor name="C1" capacitance="10uF" footprint="0805"
      connections={{ pin1: "net.E_PLUS", pin2: "net.GND" }} />
    <capacitor name="C2" capacitance="100nF" footprint="0603"
      connections={{ pin1: "net.E_PLUS", pin2: "net.GND" }} />
    <capacitor name="C3" capacitance="100nF" footprint="0603"
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C4" capacitance="10uF" footprint="0805"
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C5" capacitance="100nF" footprint="0603"
      connections={{ pin1: "net.N5V", pin2: "net.GND" }} />
    <capacitor name="C6" capacitance="10uF" footprint="0805"
      connections={{ pin1: "net.N5V", pin2: "net.GND" }} />
    <capacitor name="C7" capacitance="100nF" footprint="0603"
      connections={{ pin1: "net.SH", pin2: "net.GND" }} />

    {/* ---- ESD TVS on the digital lines (SOD-323: 1=K 2=A) ---- */}
    <diode name="D1" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }}
      connections={{ pin1: "net.DAT", pin2: "net.GND" }} />
    <diode name="D2" footprint="sod323" supplierPartNumbers={{ jlcpcb: ["C5158048"] }}
      connections={{ pin1: "net.CLK", pin2: "net.GND" }} />

    {/* ---- Sensor daisy-chain connectors (JST XH 3P, B3B-XH-A) ---- */}
    <chip name="J1" footprint="pinrow3_p2.5mm" supplierPartNumbers={{ jlcpcb: ["C144394"] }}
      connections={{ pin1: "net.RING_41", pin2: "net.E_PLUS", pin3: "net.RING_12" }} />
    <chip name="J2" footprint="pinrow3_p2.5mm" supplierPartNumbers={{ jlcpcb: ["C144394"] }}
      connections={{ pin1: "net.RING_12", pin2: "net.S_PLUS", pin3: "net.RING_23" }} />
    <chip name="J3" footprint="pinrow3_p2.5mm" supplierPartNumbers={{ jlcpcb: ["C144394"] }}
      connections={{ pin1: "net.RING_23", pin2: "net.GND", pin3: "net.RING_34" }} />
    <chip name="J4" footprint="pinrow3_p2.5mm" supplierPartNumbers={{ jlcpcb: ["C144394"] }}
      connections={{ pin1: "net.RING_34", pin2: "net.S_MINUS", pin3: "net.RING_41" }} />

    {/* ---- Full-bridge alt (J5) + hub (J6) — JST XH 5P, B5B-XH-A ---- */}
    <chip name="J5" footprint="pinrow5_p2.5mm" supplierPartNumbers={{ jlcpcb: ["C157991"] }}
      connections={{ pin1: "net.E_PLUS", pin2: "net.S_PLUS", pin3: "net.S_MINUS", pin4: "net.GND", pin5: "net.SH" }} />
    <chip name="J6" footprint="pinrow5_p2.5mm" supplierPartNumbers={{ jlcpcb: ["C157991"] }}
      connections={{ pin1: "net.N5V", pin2: "net.N3V3", pin3: "net.GND", pin4: "net.DAT", pin5: "net.CLK" }} />

    {/* ---- RATE-select jumper (JP1, 1x03 2.54mm header) ---- */}
    <chip name="JP1" footprint="pinrow3"
      connections={{ pin1: "net.GND", pin2: "net.RATE_SEL", pin3: "net.N3V3" }} />

    {/* ---- Shield-bond solder jumper (SJ1, DNP) ---- */}
    <solderjumper name="SJ1" footprint="solderjumper2_bridged12" pinCount={2}
      connections={{ pin1: "net.SH", pin2: "net.GND" }} />

    {/* ---- Test points ---- */}
    <testpoint name="TP1" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.E_PLUS" }} />
    <testpoint name="TP2" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.S_PLUS" }} />
    <testpoint name="TP3" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.S_MINUS" }} />
    <testpoint name="TP4" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.GND" }} />
    <testpoint name="TP5" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.DAT" }} />
    <testpoint name="TP6" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.CLK" }} />
    <testpoint name="TP7" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.N3V3" }} />

    {/* ---- Non-electrical M3 mounting holes (no nets, no refdes in tsc netlist) ---- */}
    <hole name="H1" diameter="3.2mm" pcbX={-18} pcbY={18} />
    <hole name="H2" diameter="3.2mm" pcbX={18} pcbY={18} />
    <hole name="H3" diameter="3.2mm" pcbX={-18} pcbY={-18} />
    <hole name="H4" diameter="3.2mm" pcbX={18} pcbY={-18} />
  </board>
)

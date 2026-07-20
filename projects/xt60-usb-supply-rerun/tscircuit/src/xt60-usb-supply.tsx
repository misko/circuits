// xt60-usb-supply-rerun — tscircuit render (node-for-node from the KiCad fab-of-record)
//
// Fab-of-record: ../../04_kicad/xt60-usb-supply.kicad_pcb (51 components, 28 named nets).
// KiCad stays authoritative (canon S-DSL); this is the second-opinion tscircuit authoring.
// Parity-by-construction: every element binds its pins to explicit nets via `connections`
// so the readable-netlist matches KiCad verbatim after ONE normalization:
//   KiCad net `5V_A` -> tscircuit net `N5V_A`   (leading digit breaks the net. selector)
//   KiCad net `5V_C` -> tscircuit net `N5V_C`
//
// Footprint sourcing (the connector-heavy stress test):
//   footprinter strings work for: 0603, 1206, 1210, 0805, sot23_6, smb
//   HAND <footprint> children (footprinter gap) for the specialty parts:
//     J1  XT60PW-M            (Amass power connector, THT blades + board-lock pegs)
//     J2/J3/J4 USB-A          (Stewart SS-52100 horizontal, THT 4-pin + 2 shield pegs)
//     J5  USB-C               (HRO TYPE-C-31-M-12, 16 SMD signal pads + 4 shield PTH)
//     U1/U2 SY8368            (irregular flip-chip QFN3x3-10, split pad 9)
//     L1/L2 FXL0630           (7.0x6.6 wirewound, 2 large SMD lands)
//     Q1  AOD4185             (TO-252-2 DPAK — footprinter has no `to252`)
//     CB1/CB2 CP_Elec 6.3x5.9 (polymer e-cap — footprinter has no `cp`)
//     F1  Littelfuse NANO2    (451/453 — footprinter has no fuse land)
//     H1-H4 M3 mounting holes (NPTH)

// ---- specialty <footprint> children (KiCad land patterns, pad-for-pad) ----

const fpXT60 = (
  <footprint>
    {/* pad 1 = GND blade (origin), pad 2 = VBAT_RAW blade, P7.2mm; + 2 board-lock pegs */}
    <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="4.1mm" holeDiameter="2.7mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="0mm" pcbY="7.2mm" outerDiameter="4.1mm" holeDiameter="2.7mm" shape="circle" />
    <hole pcbX="6mm" pcbY="-3.15mm" diameter="0.9mm" />
    <hole pcbX="6mm" pcbY="10.35mm" diameter="0.9mm" />
  </footprint>
)

const usbA = (dcp: string) => (
  <footprint>
    {/* Stewart SS-52100 horizontal: 1=5V 2,3=D 4=GND (THT), + 2 shield pegs */}
    <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="1.6mm" holeDiameter="0.9mm" shape="circle" />
    <platedhole portHints={["2"]} pcbX="0mm" pcbY="2.5mm" outerDiameter="1.6mm" holeDiameter="0.9mm" shape="circle" />
    <platedhole portHints={["3"]} pcbX="0mm" pcbY="4.5mm" outerDiameter="1.6mm" holeDiameter="0.9mm" shape="circle" />
    <platedhole portHints={["4"]} pcbX="0mm" pcbY="7.0mm" outerDiameter="1.6mm" holeDiameter="0.9mm" shape="circle" />
    <platedhole portHints={["SH"]} pcbX="-2.71mm" pcbY="-3.07mm" outerDiameter="3.0mm" holeDiameter="2.0mm" shape="circle" />
    <platedhole portHints={["SH"]} pcbX="-2.71mm" pcbY="10.07mm" outerDiameter="3.0mm" holeDiameter="2.0mm" shape="circle" />
  </footprint>
)

const fpUSBC = (
  <footprint>
    {/* HRO TYPE-C-31-M-12: A/B rows mid-mount (overlap by design), 4 shield PTH, 2 NPTH */}
    <smtpad portHints={["A1"]} pcbX="-3.25mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A4"]} pcbX="-2.45mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A5"]} pcbX="-1.25mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A6"]} pcbX="-0.25mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A7"]} pcbX="0.25mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A8"]} pcbX="1.25mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A9"]} pcbX="2.45mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["A12"]} pcbX="3.25mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B1"]} pcbX="3.25mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B4"]} pcbX="2.45mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B5"]} pcbX="1.75mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B6"]} pcbX="0.75mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B7"]} pcbX="-0.75mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B8"]} pcbX="-1.75mm" pcbY="4.045mm" width="0.3mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B9"]} pcbX="-2.45mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <smtpad portHints={["B12"]} pcbX="-3.25mm" pcbY="4.045mm" width="0.6mm" height="1.45mm" shape="rect" layer="top" />
    <platedhole portHints={["SH"]} pcbX="-4.32mm" pcbY="3.13mm" outerDiameter="1.6mm" holeDiameter="1.0mm" shape="circle" />
    <platedhole portHints={["SH"]} pcbX="-4.32mm" pcbY="-1.05mm" outerDiameter="1.6mm" holeDiameter="1.0mm" shape="circle" />
    <platedhole portHints={["SH"]} pcbX="4.32mm" pcbY="3.13mm" outerDiameter="1.6mm" holeDiameter="1.0mm" shape="circle" />
    <platedhole portHints={["SH"]} pcbX="4.32mm" pcbY="-1.05mm" outerDiameter="1.6mm" holeDiameter="1.0mm" shape="circle" />
    <hole pcbX="-2.89mm" pcbY="2.6mm" diameter="0.65mm" />
    <hole pcbX="2.89mm" pcbY="2.6mm" diameter="0.65mm" />
  </footprint>
)

const fpQFN = (
  <footprint>
    {/* SY8368 flip-chip QFN3x3-10: top row 1-6, irregular power pads 7,8,10, split GND pad 9 */}
    <smtpad portHints={["1"]} pcbX="1.13mm" pcbY="-1.3mm" width="0.6mm" height="0.25mm" shape="rect" layer="top" />
    <smtpad portHints={["2"]} pcbX="0.67mm" pcbY="-1.3mm" width="0.6mm" height="0.25mm" shape="rect" layer="top" />
    <smtpad portHints={["3"]} pcbX="0.23mm" pcbY="-1.3mm" width="0.6mm" height="0.25mm" shape="rect" layer="top" />
    <smtpad portHints={["4"]} pcbX="-0.22mm" pcbY="-1.3mm" width="0.6mm" height="0.25mm" shape="rect" layer="top" />
    <smtpad portHints={["5"]} pcbX="-0.68mm" pcbY="-1.3mm" width="0.6mm" height="0.25mm" shape="rect" layer="top" />
    <smtpad portHints={["6"]} pcbX="-1.12mm" pcbY="-1.3mm" width="0.6mm" height="0.25mm" shape="rect" layer="top" />
    <smtpad portHints={["7"]} pcbX="-1.09mm" pcbY="-0.64mm" width="1.12mm" height="0.225mm" shape="rect" layer="top" />
    <smtpad portHints={["8"]} pcbX="-0.96mm" pcbY="0.7mm" width="2.0mm" height="0.87mm" shape="rect" layer="top" />
    <smtpad portHints={["9"]} pcbX="0.71mm" pcbY="-0.64mm" width="0.225mm" height="1.88mm" shape="rect" layer="top" />
    <smtpad portHints={["9"]} pcbX="0.71mm" pcbY="1.3mm" width="0.25mm" height="1.88mm" shape="rect" layer="top" />
    <smtpad portHints={["9"]} pcbX="0.05mm" pcbY="0.48mm" width="2.45mm" height="0.555mm" shape="rect" layer="top" />
    <smtpad portHints={["10"]} pcbX="1.01mm" pcbY="0.3mm" width="1.15mm" height="0.775mm" shape="rect" layer="top" />
  </footprint>
)

const fpTO252 = (
  <footprint>
    {/* AOD4185 TO-252-2: 1=gate, 2=tab (big), 3=drain-side land */}
    <smtpad portHints={["1"]} pcbX="-2.28mm" pcbY="-5.04mm" width="2.2mm" height="1.2mm" shape="rect" layer="top" />
    <smtpad portHints={["2"]} pcbX="0mm" pcbY="1.26mm" width="6.4mm" height="5.8mm" shape="rect" layer="top" />
    <smtpad portHints={["3"]} pcbX="2.28mm" pcbY="-5.04mm" width="2.2mm" height="1.2mm" shape="rect" layer="top" />
  </footprint>
)

const fpCPElec = (
  <footprint>
    {/* CP_Elec_6.3x5.9 polymer e-cap, 2 lands P5.6mm */}
    <smtpad portHints={["1"]} pcbX="-2.8mm" pcbY="0mm" width="3.5mm" height="1.6mm" shape="rect" layer="top" />
    <smtpad portHints={["2"]} pcbX="2.8mm" pcbY="0mm" width="3.5mm" height="1.6mm" shape="rect" layer="top" />
  </footprint>
)

const fpFuse = (
  <footprint>
    {/* Littelfuse NANO2 451/453, 2 lands P4.91mm */}
    <smtpad portHints={["1"]} pcbX="-2.455mm" pcbY="0mm" width="1.96mm" height="3.15mm" shape="rect" layer="top" />
    <smtpad portHints={["2"]} pcbX="2.455mm" pcbY="0mm" width="1.96mm" height="3.15mm" shape="rect" layer="top" />
  </footprint>
)

const fpFXL0630 = (
  <footprint>
    {/* FXL0630 7.0x6.6 wirewound inductor, 2 large lands P6.0mm (non-polar) */}
    <smtpad portHints={["1"]} pcbX="-3mm" pcbY="0mm" width="2.4mm" height="3.2mm" shape="rect" layer="top" />
    <smtpad portHints={["2"]} pcbX="3mm" pcbY="0mm" width="2.4mm" height="3.2mm" shape="rect" layer="top" />
  </footprint>
)

const fpMountM3 = (
  <footprint>
    <hole pcbX="0mm" pcbY="0mm" diameter="3.2mm" />
  </footprint>
)

export default () => (
  <board width="90mm" height="70mm">
    {/* ================= INPUT: XT60 -> fuse -> reverse-polarity P-FET ================= */}
    <chip name="J1" footprint={fpXT60} pcbX="-38mm" pcbY="0mm"
      connections={{ "1": "net.GND", "2": "net.VBAT_RAW" }} />
    <fuse name="F1" currentRating="15A" footprint={fpFuse} pcbX="-30mm" pcbY="-10mm"
      connections={{ pin1: "net.VBAT_RAW", pin2: "net.VBAT_F" }} />
    <chip name="Q1" footprint={fpTO252} pcbX="-22mm" pcbY="-10mm"
      connections={{ "1": "net.PFET_G", "2": "net.VBAT_F", "3": "net.VBAT_P" }} />
    <resistor name="R1" resistance="100k" footprint="0603" pcbX="-22mm" pcbY="-4mm"
      connections={{ pin1: "net.PFET_G", pin2: "net.GND" }} />
    <diode name="D1" footprint="smb" pcbX="-16mm" pcbY="-10mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />

    {/* bulk input across VBAT_P */}
    <capacitor name="CB1" capacitance="100uF" polarized footprint={fpCPElec} pcbX="-12mm" pcbY="6mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />
    <capacitor name="CB2" capacitance="100uF" polarized footprint={fpCPElec} pcbX="-4mm" pcbY="6mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />

    {/* ================= BUCK A (5V_A -> N5V_A) : SY8368 ================= */}
    <chip name="U1" footprint={fpQFN} pcbX="0mm" pcbY="-14mm"
      connections={{
        "1": "net.VBAT_P", "2": "net.NC_U1_PG", "3": "net.GND", "4": "net.FB_A",
        "5": "net.VCC_A", "6": "net.BST_A", "7": "net.VBAT_P", "8": "net.VBAT_P",
        "9": "net.GND", "10": "net.SW_A",
      }} />
    <inductor name="L1" inductance="1.5uH" footprint={fpFXL0630} pcbX="8mm" pcbY="-14mm"
      connections={{ pin1: "net.SW_A", pin2: "net.N5V_A" }} />
    <capacitor name="CBS1" capacitance="100nF" footprint="0603" pcbX="0mm" pcbY="-18mm"
      connections={{ pin1: "net.BST_A", pin2: "net.SW_A" }} />
    <capacitor name="CVCC1" capacitance="2.2uF" footprint="0603" pcbX="-3mm" pcbY="-18mm"
      connections={{ pin1: "net.VCC_A", pin2: "net.GND" }} />
    <resistor name="RFA1" resistance="22k" footprint="0603" pcbX="3mm" pcbY="-18mm"
      connections={{ pin1: "net.N5V_A", pin2: "net.FB_A" }} />
    <resistor name="RFA2" resistance="3k" footprint="0603" pcbX="3mm" pcbY="-20mm"
      connections={{ pin1: "net.FB_A", pin2: "net.GND" }} />
    <capacitor name="CIN_A1" capacitance="10uF" footprint="1206" pcbX="-2mm" pcbY="-10mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />
    <capacitor name="CIN_A2" capacitance="10uF" footprint="1206" pcbX="2mm" pcbY="-10mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />
    <capacitor name="COUT_A1" capacitance="22uF" footprint="1210" pcbX="12mm" pcbY="-18mm"
      connections={{ pin1: "net.N5V_A", pin2: "net.GND" }} />
    <capacitor name="COUT_A2" capacitance="22uF" footprint="1210" pcbX="16mm" pcbY="-18mm"
      connections={{ pin1: "net.N5V_A", pin2: "net.GND" }} />
    <capacitor name="COUT_A3" capacitance="22uF" footprint="1210" pcbX="12mm" pcbY="-22mm"
      connections={{ pin1: "net.N5V_A", pin2: "net.GND" }} />
    <capacitor name="COUT_A4" capacitance="22uF" footprint="1210" pcbX="16mm" pcbY="-22mm"
      connections={{ pin1: "net.N5V_A", pin2: "net.GND" }} />

    {/* ================= BUCK C (5V_C -> N5V_C) : SY8368 ================= */}
    <chip name="U2" footprint={fpQFN} pcbX="0mm" pcbY="14mm"
      connections={{
        "1": "net.VBAT_P", "2": "net.NC_U2_PG", "3": "net.GND", "4": "net.FB_C",
        "5": "net.VCC_C", "6": "net.BST_C", "7": "net.VBAT_P", "8": "net.VBAT_P",
        "9": "net.GND", "10": "net.SW_C",
      }} />
    <inductor name="L2" inductance="2.2uH" footprint={fpFXL0630} pcbX="8mm" pcbY="14mm"
      connections={{ pin1: "net.SW_C", pin2: "net.N5V_C" }} />
    <capacitor name="CBS2" capacitance="100nF" footprint="0603" pcbX="0mm" pcbY="18mm"
      connections={{ pin1: "net.BST_C", pin2: "net.SW_C" }} />
    <capacitor name="CVCC2" capacitance="2.2uF" footprint="0603" pcbX="-3mm" pcbY="18mm"
      connections={{ pin1: "net.VCC_C", pin2: "net.GND" }} />
    <resistor name="RFC1" resistance="22k" footprint="0603" pcbX="3mm" pcbY="18mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.FB_C" }} />
    <resistor name="RFC2" resistance="3k" footprint="0603" pcbX="3mm" pcbY="20mm"
      connections={{ pin1: "net.FB_C", pin2: "net.GND" }} />
    <capacitor name="CIN_C1" capacitance="10uF" footprint="1206" pcbX="-2mm" pcbY="10mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />
    <capacitor name="CIN_C2" capacitance="10uF" footprint="1206" pcbX="2mm" pcbY="10mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.GND" }} />
    <capacitor name="COUT_C1" capacitance="22uF" footprint="1210" pcbX="12mm" pcbY="18mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />
    <capacitor name="COUT_C2" capacitance="22uF" footprint="1210" pcbX="16mm" pcbY="18mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />
    <capacitor name="COUT_C3" capacitance="22uF" footprint="1210" pcbX="12mm" pcbY="22mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />
    <capacitor name="COUT_C4" capacitance="22uF" footprint="1210" pcbX="16mm" pcbY="22mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.GND" }} />

    {/* ================= USB-A outputs (5V_A) + per-port DCP short + ESD ================= */}
    <chip name="J2" footprint={usbA("DCP1")} pcbX="30mm" pcbY="-22mm"
      connections={{ "1": "net.N5V_A", "2": "net.DCP1", "3": "net.DCP1", "4": "net.GND", "SH": "net.GND" }} />
    <chip name="J3" footprint={usbA("DCP2")} pcbX="30mm" pcbY="-12mm"
      connections={{ "1": "net.N5V_A", "2": "net.DCP2", "3": "net.DCP2", "4": "net.GND", "SH": "net.GND" }} />
    <chip name="J4" footprint={usbA("DCP3")} pcbX="30mm" pcbY="-2mm"
      connections={{ "1": "net.N5V_A", "2": "net.DCP3", "3": "net.DCP3", "4": "net.GND", "SH": "net.GND" }} />
    <chip name="U3" footprint="sot23_6" pcbX="24mm" pcbY="-22mm"
      connections={{ "1": "net.DCP1", "2": "net.GND", "3": "net.DCP1", "4": "net.DCP1", "5": "net.N5V_A", "6": "net.DCP1" }} />
    <chip name="U4" footprint="sot23_6" pcbX="24mm" pcbY="-12mm"
      connections={{ "1": "net.DCP2", "2": "net.GND", "3": "net.DCP2", "4": "net.DCP2", "5": "net.N5V_A", "6": "net.DCP2" }} />
    <chip name="U5" footprint="sot23_6" pcbX="24mm" pcbY="-2mm"
      connections={{ "1": "net.DCP3", "2": "net.GND", "3": "net.DCP3", "4": "net.DCP3", "5": "net.N5V_A", "6": "net.DCP3" }} />

    {/* ================= USB-C output (5V_C) + CC + DCP + ESD ================= */}
    <chip name="J5" footprint={fpUSBC} pcbX="30mm" pcbY="12mm"
      connections={{
        "A1": "net.GND", "A4": "net.N5V_C", "A5": "net.CC1", "A6": "net.DCPC", "A7": "net.DCPC",
        "A8": "net.NC_J5_SBU1", "A9": "net.N5V_C", "A12": "net.GND",
        "B1": "net.GND", "B4": "net.N5V_C", "B5": "net.CC2", "B6": "net.DCPC", "B7": "net.DCPC",
        "B8": "net.NC_J5_SBU2", "B9": "net.N5V_C", "B12": "net.GND", "SH": "net.GND",
      }} />
    <chip name="U6" footprint="sot23_6" pcbX="24mm" pcbY="12mm"
      connections={{ "1": "net.CC1", "2": "net.GND", "3": "net.CC2", "4": "net.CC2", "5": "net.N5V_C", "6": "net.CC1" }} />
    <resistor name="R3" resistance="10k" footprint="0603" pcbX="24mm" pcbY="6mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.CC1" }} />
    <resistor name="R4" resistance="10k" footprint="0603" pcbX="24mm" pcbY="8mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.CC2" }} />

    {/* ================= status LEDs ================= */}
    <resistor name="R2" resistance="1k" footprint="0603" pcbX="-30mm" pcbY="16mm"
      connections={{ pin1: "net.VBAT_P", pin2: "net.LED1_A" }} />
    <led name="LED1" footprint="0805" pcbX="-30mm" pcbY="20mm"
      connections={{ pin1: "net.GND", pin2: "net.LED1_A" }} />
    <resistor name="R5" resistance="1k" footprint="0603" pcbX="-24mm" pcbY="16mm"
      connections={{ pin1: "net.N5V_A", pin2: "net.LED2_A" }} />
    <led name="LED2" footprint="0805" pcbX="-24mm" pcbY="20mm"
      connections={{ pin1: "net.GND", pin2: "net.LED2_A" }} />
    <resistor name="R6" resistance="1k" footprint="0603" pcbX="-18mm" pcbY="16mm"
      connections={{ pin1: "net.N5V_C", pin2: "net.LED3_A" }} />
    <led name="LED3" footprint="0805" pcbX="-18mm" pcbY="20mm"
      connections={{ pin1: "net.GND", pin2: "net.LED3_A" }} />

    {/* ================= mounting holes (mechanical, no net) ================= */}
    <chip name="H1" footprint={fpMountM3} pcbX="-42mm" pcbY="-30mm" />
    <chip name="H2" footprint={fpMountM3} pcbX="42mm" pcbY="-30mm" />
    <chip name="H3" footprint={fpMountM3} pcbX="-42mm" pcbY="30mm" />
    <chip name="H4" footprint={fpMountM3} pcbX="42mm" pcbY="30mm" />
  </board>
)

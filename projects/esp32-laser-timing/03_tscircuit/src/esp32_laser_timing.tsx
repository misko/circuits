// esp32-laser-timing — tscircuit render (node-for-node from the KiCad fab-of-record)
//
// Fab-of-record (authoritative, canon S-DSL): ../../04_kicad/esp32_laser_timing.kicad_pcb
// This is a SECOND-OPINION render only. 76 KiCad footprints (72 electrical + 4 M3 holes),
// 36 named nets (+ KiCad "unconnected-*" auto-nets = true no-connects, not authored).
//
// Net-name normalization (KiCad -> tscircuit net label):
//   3V3 -> N3V3 , 5V -> N5V  (tscircuit `net.` selectors dislike a leading digit);
//   every other KiCad net name is preserved verbatim. Full map in verification/notes.md.
//
// Connectivity is authored via each element's `connections` prop -> `net.<NAME>`, so the
// netlist is correct by construction. Placement/routing is auto (not fidelity-relevant).
//
// SCALE / ACTIVE-IC STRESS + a real finding: the two big parts (U1 ESP32-S3-WROOM-1 module,
// 41 pads incl EPAD; J1 USB-C, 22 pads) carry a hand-authored land pattern. tscircuit's
// kicad_sch EXPORTER only emits pin1/pin2 for a chip whose <footprint> is an INLINE CHILD,
// so a custom footprint MUST be passed via the `footprint={const}` PROP (as here) for the
// schematic-net export to include every pin. See verification/notes.md.

const N3V3 = "net.N3V3"
const N5V = "net.N5V"
const GND = "net.GND"

// ==== ESP32-S3-WROOM-1 land pattern (LCC-40 perimeter pads 1..40 + EPAD 41) ====
const fpU1 = (
  <footprint>
    <smtpad portHints={["1"]} pcbX={-8.750} pcbY={-5.260} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["2"]} pcbX={-8.750} pcbY={-3.990} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["3"]} pcbX={-8.750} pcbY={-2.720} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["4"]} pcbX={-8.750} pcbY={-1.450} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["5"]} pcbX={-8.750} pcbY={-0.180} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["6"]} pcbX={-8.750} pcbY={1.090} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["7"]} pcbX={-8.750} pcbY={2.360} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["8"]} pcbX={-8.750} pcbY={3.630} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["9"]} pcbX={-8.750} pcbY={4.900} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["10"]} pcbX={-8.750} pcbY={6.170} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["11"]} pcbX={-8.750} pcbY={7.440} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["12"]} pcbX={-8.750} pcbY={8.710} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["13"]} pcbX={-8.750} pcbY={9.980} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["14"]} pcbX={-8.750} pcbY={11.250} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["15"]} pcbX={-6.985} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["16"]} pcbX={-5.715} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["17"]} pcbX={-4.445} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["18"]} pcbX={-3.175} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["19"]} pcbX={-1.905} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["20"]} pcbX={-0.635} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["21"]} pcbX={0.635} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["22"]} pcbX={1.905} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["23"]} pcbX={3.175} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["24"]} pcbX={4.445} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["25"]} pcbX={5.715} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["26"]} pcbX={6.985} pcbY={12.500} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["27"]} pcbX={8.750} pcbY={11.250} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["28"]} pcbX={8.750} pcbY={9.980} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["29"]} pcbX={8.750} pcbY={8.710} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["30"]} pcbX={8.750} pcbY={7.440} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["31"]} pcbX={8.750} pcbY={6.170} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["32"]} pcbX={8.750} pcbY={4.900} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["33"]} pcbX={8.750} pcbY={3.630} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["34"]} pcbX={8.750} pcbY={2.360} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["35"]} pcbX={8.750} pcbY={1.090} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["36"]} pcbX={8.750} pcbY={-0.180} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["37"]} pcbX={8.750} pcbY={-1.450} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["38"]} pcbX={8.750} pcbY={-2.720} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["39"]} pcbX={8.750} pcbY={-3.990} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["40"]} pcbX={8.750} pcbY={-5.260} width={1.500} height={0.900} shape="rect" />
    <smtpad portHints={["41"]} pcbX={-1.500} pcbY={2.460} width={3.900} height={3.900} shape="rect" />
  </footprint>
)

// ==== USB-C receptacle HRO TYPE-C-31-M-12 land pattern (A/B rows overlap by design; 4 SH) ====
const fpJ1 = (
  <footprint>
    <smtpad portHints={["A1"]} pcbX={4.045} pcbY={-3.250} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["A4"]} pcbX={4.045} pcbY={-2.450} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["A5"]} pcbX={4.045} pcbY={-1.250} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["A6"]} pcbX={4.045} pcbY={-0.250} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["A7"]} pcbX={4.045} pcbY={0.250} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["A8"]} pcbX={4.045} pcbY={1.250} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["A9"]} pcbX={4.045} pcbY={2.450} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["A12"]} pcbX={4.045} pcbY={3.250} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["B1"]} pcbX={-4.045} pcbY={3.250} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["B4"]} pcbX={-4.045} pcbY={2.450} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["B5"]} pcbX={-4.045} pcbY={1.750} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["B6"]} pcbX={-4.045} pcbY={0.750} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["B7"]} pcbX={-4.045} pcbY={-0.750} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["B8"]} pcbX={-4.045} pcbY={-1.750} width={0.300} height={1.450} shape="rect" />
    <smtpad portHints={["B9"]} pcbX={-4.045} pcbY={-2.450} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["B12"]} pcbX={-4.045} pcbY={-3.250} width={0.600} height={1.450} shape="rect" />
    <smtpad portHints={["SH"]} pcbX={3.130} pcbY={-4.320} width={1.000} height={2.100} shape="rect" />
    <smtpad portHints={["SH"]} pcbX={-1.050} pcbY={-4.320} width={1.000} height={1.600} shape="rect" />
    <smtpad portHints={["SH"]} pcbX={3.130} pcbY={4.320} width={1.000} height={2.100} shape="rect" />
    <smtpad portHints={["SH"]} pcbX={-1.050} pcbY={4.320} width={1.000} height={1.600} shape="rect" />
  </footprint>
)

// A KF128L-3.5-2P screw-terminal land: two 2.4mm pads on a 3.5mm pitch.
const TermFootprint = () => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={0} pcbY={0} width={2.4} height={2.4} shape="rect" />
    <smtpad portHints={["2"]} pcbX={3.5} pcbY={0} width={2.4} height={2.4} shape="rect" />
  </footprint>
)

// ---- passives: [ref, value, lcsc, pin1-net, pin2-net] (pad order matches KiCad) ----
const RES: [string, string, string, string, string][] = [
  ["R1", "5.1k", "C27834", "net.CC1", GND],
  ["R2", "5.1k", "C27834", "net.CC2", GND],
  ["R3", "10k", "C17414", N3V3, "net.EN"],
  ["R4", "1k", "C17513", N3V3, "net.LED_A"],
  ["R10", "100", "C17408", "net.LDRV1", "net.GATE1"],
  ["R11", "100k", "C149504", "net.GATE1", GND],
  ["R12", "100", "C17408", "net.LDRV2", "net.GATE2"],
  ["R13", "100k", "C149504", "net.GATE2", GND],
  ["R14", "100", "C17408", "net.LDRV3", "net.GATE3"],
  ["R15", "100k", "C149504", "net.GATE3", GND],
  ["R20", "1k", "C17513", "net.PD1", GND],
  ["R21", "1k", "C17513", "net.PD2", GND],
  ["R22", "1k", "C17513", "net.PD3", GND],
  ["R23", "10k", "C17414", N3V3, "net.VTH1"],
  ["R24", "10k", "C17414", N3V3, "net.VTH2"],
  ["R25", "10k", "C17414", N3V3, "net.VTH3"],
  ["R26", "2.7k", "C17530", "net.VTH1", GND],
  ["R27", "2.7k", "C17530", "net.VTH2", GND],
  ["R28", "2.7k", "C17530", "net.VTH3", GND],
  ["R29", "33k", "C17633", "net.PD1", "net.COMP1"],
  ["R30", "33k", "C17633", "net.PD2", "net.COMP2"],
  ["R31", "33k", "C17633", "net.PD3", "net.COMP3"],
  ["R32", "10k", "C17414", N3V3, "net.COMP1"],
  ["R33", "10k", "C17414", N3V3, "net.COMP2"],
  ["R34", "10k", "C17414", N3V3, "net.COMP3"],
  ["R40", "10k", "C17414", N3V3, "net.BTN1_N"],
  ["R41", "10k", "C17414", N3V3, "net.BTN2_N"],
  ["R42", "10k", "C17414", N3V3, "net.BTN3_N"],
  ["R43", "1k", "C17513", "net.BTN1_N", "net.BTN1_G"],
  ["R44", "1k", "C17513", "net.BTN2_N", "net.BTN2_G"],
  ["R45", "1k", "C17513", "net.BTN3_N", "net.BTN3_G"],
  ["R50", "4.7k", "C17673", N3V3, "net.SDA"],
  ["R51", "4.7k", "C17673", N3V3, "net.SCL"],
]

// ceramic caps: [ref, value, lcsc, pin1-net, pin2-net]
const CAP: [string, string, string, string, string][] = [
  ["C1", "1uF", "C28323", "net.EN", GND],
  ["C2", "22uF", "C45783", N5V, GND],
  ["C3", "22uF", "C45783", N3V3, GND],
  ["C4", "22uF", "C45783", N3V3, GND],
  ["C5", "100nF", "C49678", N3V3, GND],
  ["C6", "100nF", "C49678", N5V, GND],
  ["C7", "100nF", "C49678", N3V3, GND],
  ["C8", "100nF", "C49678", "net.BTN1_N", GND],
  ["C9", "100nF", "C49678", "net.BTN2_N", GND],
  ["C10", "100nF", "C49678", "net.BTN3_N", GND],
  ["C12", "100nF", "C49678", N5V, GND],
]

// SOT-23 N-ch MOSFETs (AO3400A): 1=G 2=S 3=D
const FET: [string, string, string, string][] = [
  ["Q1", "net.GATE1", GND, "net.LSW1"],
  ["Q2", "net.GATE2", GND, "net.LSW2"],
  ["Q3", "net.GATE3", GND, "net.LSW3"],
]

// KF128L-3.5-2P screw terminals: [ref, pin1-net, pin2-net]
const TERM: [string, string, string][] = [
  ["J4", N5V, "net.LSW1"],
  ["J5", N5V, "net.LSW2"],
  ["J6", N5V, "net.LSW3"],
  ["J7", N5V, "net.PD1"],
  ["J8", N5V, "net.PD2"],
  ["J9", N5V, "net.PD3"],
  ["J10", "net.BTN1_N", GND],
  ["J11", "net.BTN2_N", GND],
  ["J12", "net.BTN3_N", GND],
]

const TP: [string, string][] = [
  ["TP1", "net.COMP1"], ["TP2", "net.COMP2"], ["TP3", "net.COMP3"],
  ["TP4", N5V], ["TP5", N3V3], ["TP6", GND],
]

export default () => (
  <board width="90mm" height="70mm">
    {/* =================== U1 — ESP32-S3-WROOM-1-N8R2 (LCC-40 + EPAD, 41 pins) =================== */}
    {/* pinLabels = datasheet function per pad, keyed to the SAME pad numbers as the KiCad symbol.
        GND pads 1/40/41 get unique labels (GND / GND40 / EPAD) so the schematic ports stay distinct. */}
    <chip
      name="U1"
      footprint={fpU1}
      supplierPartNumbers={{ jlcpcb: ["C2913204"] }}
      pinLabels={{
        pin1: "GND", pin2: "V3V3", pin3: "EN", pin4: "IO4", pin5: "IO5",
        pin6: "IO6", pin7: "IO7", pin8: "IO15", pin9: "IO16", pin10: "IO17",
        pin11: "IO18", pin12: "IO8", pin13: "IO19_DM", pin14: "IO20_DP", pin15: "IO3",
        pin16: "IO46", pin17: "IO9", pin18: "IO10", pin19: "IO11", pin20: "IO12",
        pin21: "IO13", pin22: "IO14", pin23: "IO21", pin24: "IO47", pin25: "IO48",
        pin26: "IO45", pin27: "IO0", pin28: "IO35", pin29: "IO36", pin30: "IO37",
        pin31: "IO38", pin32: "IO39", pin33: "IO40", pin34: "IO41", pin35: "IO42",
        pin36: "RXD0", pin37: "TXD0", pin38: "IO2", pin39: "IO1", pin40: "GND40",
        pin41: "EPAD",
      }}
      connections={{
        pin1: GND, pin2: N3V3, pin3: "net.EN", pin4: "net.COMP1", pin5: "net.COMP2",
        pin6: "net.COMP3", pin7: "net.LDRV1", pin8: "net.LDRV2", pin9: "net.LDRV3",
        pin10: "net.BTN1_G", pin11: "net.BTN2_G", pin13: "net.USB_DM", pin14: "net.USB_DP",
        pin23: "net.BTN3_G", pin27: "net.BOOT", pin38: "net.SCL", pin39: "net.SDA",
        pin40: GND, pin41: GND,
        // pins 12,15-22,24-26,28-37 = unconnected GPIO (KiCad unconnected-* no-connects)
      }}
    />

    {/* =================== U3 — LM339DT quad comparator (SOIC-14) =================== */}
    <chip
      name="U3"
      footprint="soic14_p1.27mm"
      supplierPartNumbers={{ jlcpcb: ["C71036"] }}
      pinLabels={{
        pin1: "OUT2", pin2: "OUT1", pin3: "VCC", pin4: "IN1n", pin5: "IN1p",
        pin6: "IN2n", pin7: "IN2p", pin8: "IN3n", pin9: "IN3p", pin10: "IN4n",
        pin11: "IN4p", pin12: "GND", pin13: "OUT4", pin14: "OUT3",
      }}
      connections={{
        pin1: "net.COMP2", pin2: "net.COMP1", pin3: N5V, pin4: "net.VTH1", pin5: "net.PD1",
        pin6: "net.VTH2", pin7: "net.PD2", pin8: "net.VTH3", pin9: "net.PD3", pin10: "net.VTH3",
        pin11: GND, pin12: GND, pin14: "net.COMP3",
        // pin13 OUT4: no-connect (KiCad unconnected-(U3-OUT4-Pad13))
      }}
    />

    {/* =================== U2 — AMS1117-3.3 LDO (SOT-223, tab = Vout) =================== */}
    <chip
      name="U2"
      footprint="sot223"
      supplierPartNumbers={{ jlcpcb: ["C6186"] }}
      pinLabels={{ pin1: "GND", pin2: "VOUT", pin3: "VIN", pin4: "TAB" }}
      connections={{ pin1: GND, pin2: N3V3, pin3: N5V, pin4: N3V3 }}
    />

    {/* =================== D1 — USBLC6-2SC6 ESD array (SOT-23-6) =================== */}
    <chip
      name="D1"
      footprint="sot23_6"
      supplierPartNumbers={{ jlcpcb: ["C2687116"] }}
      pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2b", pin5: "VBUS", pin6: "IO1b" }}
      connections={{
        pin1: "net.USB_DP", pin2: GND, pin3: "net.USB_DM",
        pin4: "net.USB_DM", pin5: N5V, pin6: "net.USB_DP",
      }}
    />

    {/* =================== J1 — USB-C receptacle TYPE-C-31-M-12 (prop-form footprint) =================== */}
    <chip
      name="J1"
      footprint={fpJ1}
      supplierPartNumbers={{ jlcpcb: ["C165948"] }}
      connections={{
        A1: GND, A4: N5V, A5: "net.CC1", A6: "net.USB_DP", A7: "net.USB_DM",
        A9: N5V, A12: GND, B1: GND, B4: N5V, B5: "net.CC2",
        B6: "net.USB_DP", B7: "net.USB_DM", B9: N5V, B12: GND, SH: GND,
        // A8 (SBU1), B8 (SBU2): no-connect
      }}
    />

    {/* =================== J2 — OLED header 1x4 female (2.54mm) =================== */}
    <chip
      name="J2"
      footprint="pinrow4"
      supplierPartNumbers={{ jlcpcb: ["C2718488"] }}
      connections={{ pin1: GND, pin2: N3V3, pin3: "net.SCL", pin4: "net.SDA" }}
    />

    {/* =================== Q1..Q3 — AO3400A N-ch MOSFETs (SOT-23) =================== */}
    {FET.map(([ref, g, s, d]) => (
      <chip
        key={ref}
        name={ref}
        footprint="sot23"
        supplierPartNumbers={{ jlcpcb: ["C20917"] }}
        pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
        connections={{ pin1: g, pin2: s, pin3: d }}
      />
    ))}

    {/* =================== Resistors (0805) =================== */}
    {RES.map(([ref, val, lcsc, p1, p2]) => (
      <resistor key={ref} name={ref} resistance={val} footprint="0805"
        supplierPartNumbers={{ jlcpcb: [lcsc] }} connections={{ pin1: p1, pin2: p2 }} />
    ))}

    {/* =================== Ceramic caps (0805) =================== */}
    {CAP.map(([ref, val, lcsc, p1, p2]) => (
      <capacitor key={ref} name={ref} capacitance={val} footprint="0805"
        supplierPartNumbers={{ jlcpcb: [lcsc] }} connections={{ pin1: p1, pin2: p2 }} />
    ))}

    {/* =================== C11 — 100uF bulk electrolytic (CP_Elec 6.3x5.4) =================== */}
    <capacitor name="C11" capacitance="100uF" polarized
      supplierPartNumbers={{ jlcpcb: ["C2887276"] }} connections={{ pin1: N5V, pin2: GND }}>
      <footprint>
        <smtpad portHints={["1"]} pcbX={-3.1} pcbY={0} width={1.8} height={2.5} shape="rect" />
        <smtpad portHints={["2"]} pcbX={3.1} pcbY={0} width={1.8} height={2.5} shape="rect" />
      </footprint>
    </capacitor>

    {/* =================== D2 — green PWR LED (0805); KiCad pad1=K(GND) pad2=A(LED_A) =================== */}
    <led name="D2" footprint="0805" supplierPartNumbers={{ jlcpcb: ["C2297"] }}
      connections={{ pin1: GND, pin2: "net.LED_A" }} />

    {/* =================== SW1/SW2 — TS-1187A tactile (BOOT / RESET) =================== */}
    <pushbutton name="SW1" supplierPartNumbers={{ jlcpcb: ["C318884"] }}
      connections={{ pin1: "net.BOOT", pin2: GND }} />
    <pushbutton name="SW2" supplierPartNumbers={{ jlcpcb: ["C318884"] }}
      connections={{ pin1: "net.EN", pin2: GND }} />

    {/* =================== J4..J12 — KF128L-3.5-2P screw terminals =================== */}
    {TERM.map(([ref, p1, p2]) => (
      <chip key={ref} name={ref} supplierPartNumbers={{ jlcpcb: ["C474930"] }}
        connections={{ pin1: p1, pin2: p2 }}>
        <TermFootprint />
      </chip>
    ))}

    {/* =================== Test points =================== */}
    {TP.map(([ref, net]) => (
      <testpoint key={ref} name={ref} footprintVariant="pad" padShape="circle"
        padDiameter="1.5mm" connections={{ pin1: net }} />
    ))}

    {/* =================== Non-electrical M3 mounting holes =================== */}
    <hole name="H1" diameter="3.2mm" pcbX={-40} pcbY={30} />
    <hole name="H2" diameter="3.2mm" pcbX={40} pcbY={30} />
    <hole name="H3" diameter="3.2mm" pcbX={-40} pcbY={-30} />
    <hole name="H4" diameter="3.2mm" pcbX={40} pcbY={-30} />
  </board>
)

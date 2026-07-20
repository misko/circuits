// ShuntMonitor — a reusable, parameterized current-monitor channel (ADR-0002 Phase C, THE REGISTRY)
//
// This is the canonical "repeated proven subcircuit" from ble-bus-bar's 6-port bus bar:
// one INA238 (I2C current/voltage monitor) + one WSLP2726 0.5 mR Kelvin power shunt +
// a differential input filter (2x 10R sense + 100n diff cap) + a 100n decoupler, with the
// I2C address set by the A1/A0 straps. ble-bus-bar hand-authored this block SIX times
// (channels 1..6, addresses 0x40..0x45). This module lets a new board COMPOSE it instead.
//
// Provenance (all node-for-node from projects/ble-bus-bar):
//   - 03_src/generate_schematic.py  port_channel(i)  — the sealed topology this reproduces
//   - 02_parts/INA238AIDGSR/part.yaml  — VSSOP/MSOP-10, JLC C2868250, pin map (fig 4-1 SLYS025B):
//         1=A1 2=A0 3=ALERT 4=SDA 5=SCL 6=VS 7=GND 8=VBUS 9=IN- 10=IN+
//   - 02_parts/WSLP2726L5000FEA/part.yaml — 0.5 mR 5W Power Metal Strip, JLC C844297,
//         land pattern (solder-pad table doc 30179): 2 pads 5.71 x 2.69 mm, centers 4.93 mm apart.
//
// Net contract (Kelvin sense preserved exactly as the sealed board):
//   busNet  --[shunt RS]-- loadNet          (current path; shunt across the two studs)
//   busNet  --[10R RP]-- KA -> INA IN+       (Kelvin tap at the bus-side pad)
//   loadNet --[10R RN]-- KB -> INA IN-,VBUS  (Kelvin tap at the load-side pad; VBUS reads through RN)
//   KA --[100n CD]-- KB                      (differential input filter)
//   vsNet --[100n CB]-- gndNet               (INA VS decoupler)
//   INA: VS=vsNet GND=gndNet SDA=sdaNet SCL=sclNet ALERT=alertNet; A1/A0 = address straps
//
// Internal nets (KA/KB) are CHANNEL-PREFIXED so N instances never collide. Rails/signals
// (vs/gnd/sda/scl/alert) and the two studs (bus/load) are passed in by the composing board.
//
// Net-name convention (ADR-0001 canonical-name / the converter's canon_net): the `net.`
// selector can't author a leading digit, so the 3V3 rail is passed as "N3V3" and the
// converter strips the guard N -> "3V3". Pass vsNet="N3V3", gndNet="GND", etc.

export interface ShuntMonitorProps {
  /** 1-based channel index; prefixes internal nets (KA{ch}/KB{ch}) and refdes suffixes. */
  channel: number
  /** INA238 7-bit I2C address, 0x40..0x4F. Decodes to the A1/A0 strap targets. */
  i2cAddress: number
  /** Bus-side stud net (shunt pin 1, RP tap). e.g. "VF1" (post-fuse). */
  busNet: string
  /** Load-side stud net (shunt pin 2, RN tap). e.g. "VP1" (to the port lug). */
  loadNet: string
  /** I2C data net, e.g. "SDA". */
  sdaNet: string
  /** I2C clock net, e.g. "SCL". */
  sclNet: string
  /** Open-drain alert net, e.g. "ALERT". */
  alertNet: string
  /** INA supply / VS rail (also an address-strap target). Canonical-guarded, e.g. "N3V3". */
  vsNet: string
  /** Ground (also an address-strap target), e.g. "GND". */
  gndNet: string
  /** Shunt value in milliohm (default 0.5 = WSLP2726L5000FEA). */
  shuntMilliohm?: number
  /** JLCPCB code for the INA238 (default C2868250 = INA238AIDGSR). */
  inaJlc?: string
  /** JLCPCB code for the shunt (default C844297 = WSLP2726L5000FEA). */
  shuntJlc?: string
}

// INA238 A1/A0 address decode (datasheet SLYS025B addr table; 0x40 base = (GND,GND)).
// Each strap pin selects one of {GND, VS, SDA, SCL}; address = 0x40 + A1state*4 + A0state.
// Reproduces ble-bus-bar's ADDR map exactly for 0x40..0x45.
const strapNet = (
  state: number,
  { vsNet, gndNet, sdaNet, sclNet }: Pick<ShuntMonitorProps, "vsNet" | "gndNet" | "sdaNet" | "sclNet">,
): string => [gndNet, vsNet, sdaNet, sclNet][state & 3]

export const ShuntMonitor = (p: ShuntMonitorProps) => {
  const ch = p.channel
  const shuntMilliohm = p.shuntMilliohm ?? 0.5
  const inaJlc = p.inaJlc ?? "C2868250"
  const shuntJlc = p.shuntJlc ?? "C844297"

  // channel-prefixed internal Kelvin sense nodes (never collide across instances)
  const ka = `net.KA${ch}`
  const kb = `net.KB${ch}`

  // board-supplied nets -> net. selectors
  const bus = `net.${p.busNet}`
  const load = `net.${p.loadNet}`
  const sda = `net.${p.sdaNet}`
  const scl = `net.${p.sclNet}`
  const alert = `net.${p.alertNet}`
  const vs = `net.${p.vsNet}`
  const gnd = `net.${p.gndNet}`

  // I2C address straps
  const off = p.i2cAddress - 0x40
  const a1 = `net.${strapNet(off >> 2, p)}`
  const a0 = `net.${strapNet(off & 3, p)}`

  return (
    <group name={`mon${ch}`}>
      {/* WSLP2726 0.5 mR Kelvin power shunt: bus stud -> load stud. Custom land pattern
          (solder-pad table doc 30179) so tscircuit renders it; the converter maps JLC
          C844297 -> bbar:R_Shunt_WSLP2726 from ble-bus-bar's 02_parts. */}
      <resistor
        name={`RS${ch}`}
        resistance={`${shuntMilliohm}mOhm`}
        supplierPartNumbers={{ jlcpcb: [shuntJlc] }}
        connections={{ pin1: bus, pin2: load }}
        footprint={
          <footprint>
            <smtpad portHints={["1"]} pcbX="0mm" pcbY="2.465mm" width="5.71mm" height="2.69mm" shape="rect" />
            <smtpad portHints={["2"]} pcbX="0mm" pcbY="-2.465mm" width="5.71mm" height="2.69mm" shape="rect" />
          </footprint>
        }
      />

      {/* Differential input filter — Kelvin taps at the shunt studs, 10R each, 100n across. */}
      <resistor name={`RP${ch}`} resistance="10" footprint="0805" connections={{ pin1: bus, pin2: ka }} />
      <resistor name={`RN${ch}`} resistance="10" footprint="0805" connections={{ pin1: load, pin2: kb }} />
      <capacitor name={`CD${ch}`} capacitance="100nF" footprint="0805" connections={{ pin1: ka, pin2: kb }} />

      {/* INA238 supply decoupler. */}
      <capacitor name={`CB${ch}`} capacitance="100nF" footprint="0805" connections={{ pin1: vs, pin2: gnd }} />

      {/* INA238 I2C current/voltage monitor. Pads 1..10 = A1 A0 ALERT SDA SCL VS GND VBUS IN- IN+.
          VBUS(8) ties to IN-(9)=KB so bus voltage reads through RN (nA bias -> ~0 error). */}
      <chip
        name={`U${ch}`}
        footprint="msop10"
        supplierPartNumbers={{ jlcpcb: [inaJlc] }}
        pinLabels={{
          pin1: "A1", pin2: "A0", pin3: "ALERT", pin4: "SDA", pin5: "SCL",
          pin6: "VS", pin7: "GND", pin8: "VBUS", pin9: "INN", pin10: "INP",
        }}
        connections={{
          pin1: a1, pin2: a0, pin3: alert, pin4: sda, pin5: scl,
          pin6: vs, pin7: gnd, pin8: kb, pin9: kb, pin10: ka,
        }}
      />
    </group>
  )
}

export default ShuntMonitor

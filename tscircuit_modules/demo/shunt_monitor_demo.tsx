// shunt_monitor_demo — ADR-0002 Phase C gate board.
//
// Composes the ShuntMonitor registry module SIX times (channels 1..6, addresses
// 0x40..0x45), reproducing ble-bus-bar's 6 hand-authored current-monitor channels
// from ONE authored module. Plus a minimal bus + MCU stub to close the nets
// (fuses VBUS->VF{i}, load studs on VP{i}, an MCU/bus header, and the I2C/ALERT pullups).
//
// The gate (verification/): the converter kicad_sch's per-channel INA238+shunt+filter
// subnet must match ble-bus-bar's corresponding sealed port channel node-for-node,
// addresses distinct 0x40..0x45, Kelvin sense preserved. ERC severity-all = 0.

import { ShuntMonitor } from "../src/ShuntMonitor"

const CHANNELS = [1, 2, 3, 4, 5, 6]

export default () => (
  <board width="120mm" height="60mm">
    {/* ---- bus input + electronics rail stub (closes VBUS / N3V3 / GND) ---- */}
    <chip name="JBUS" footprint="pinrow2"
      connections={{ pin1: "net.VBUS", pin2: "net.GND" }} />
    <chip name="JPWR" footprint="pinrow2"
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ---- MCU / I2C stub (closes SDA / SCL / ALERT) ---- */}
    <chip name="JMCU" footprint="pinrow5"
      connections={{ pin1: "net.N3V3", pin2: "net.GND", pin3: "net.SDA", pin4: "net.SCL", pin5: "net.ALERT" }} />
    <resistor name="R15" resistance="4.7k" footprint="0805" connections={{ pin1: "net.SDA", pin2: "net.N3V3" }} />
    <resistor name="R16" resistance="4.7k" footprint="0805" connections={{ pin1: "net.SCL", pin2: "net.N3V3" }} />
    <resistor name="R17" resistance="10k" footprint="0805" connections={{ pin1: "net.ALERT", pin2: "net.N3V3" }} />

    {/* ---- six per-port fuse + load-stud stubs (close VF{i} / VP{i} to the bus) ---- */}
    {CHANNELS.map((ch) => (
      <chip key={`f${ch}`} name={`F${ch}`} footprint="pinrow2"
        connections={{ pin1: "net.VBUS", pin2: `net.VF${ch}` }} />
    ))}
    {CHANNELS.map((ch) => (
      <testpoint key={`j${ch}`} name={`J${ch}`} footprintVariant="pad" padShape="circle"
        padDiameter="1.5mm" connections={{ pin1: `net.VP${ch}` }} />
    ))}

    {/* ---- THE REGISTRY MODULE, composed 6x — author once, compose everywhere ---- */}
    {CHANNELS.map((ch) => (
      <ShuntMonitor
        key={`mon${ch}`}
        channel={ch}
        i2cAddress={0x40 + (ch - 1)}
        busNet={`VF${ch}`}
        loadNet={`VP${ch}`}
        sdaNet="SDA"
        sclNet="SCL"
        alertNet="ALERT"
        vsNet="N3V3"
        gndNet="GND"
      />
    ))}
  </board>
)

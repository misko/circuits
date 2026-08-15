// Four-channel Raspberry Pi controlled inline USB 3 / USB 2 switch fixture.
// Electrical source only; placement and routing are owned by 03_src.

const N = (name: string) => `net.${name}`

const SHEETS: Record<string, string> = {
  input: "input",
  gpio: "gpio",
  straps: "straps",
  ch1_up_front: "channel_1_up_front", ch1_up_ac: "channel_1_up_ac", ch1_core: "channel_1_core", ch1_dn_front: "channel_1_dn_front", ch1_dn_ac: "channel_1_dn_ac", ch1_ctl: "channel_1_ctl",
  ch2_up_front: "channel_2_up_front", ch2_up_ac: "channel_2_up_ac", ch2_core: "channel_2_core", ch2_dn_front: "channel_2_dn_front", ch2_dn_ac: "channel_2_dn_ac", ch2_ctl: "channel_2_ctl",
  ch3_up_front: "channel_3_up_front", ch3_up_ac: "channel_3_up_ac", ch3_core: "channel_3_core", ch3_dn_front: "channel_3_dn_front", ch3_dn_ac: "channel_3_dn_ac", ch3_ctl: "channel_3_ctl",
  ch4_up_front: "channel_4_up_front", ch4_up_ac: "channel_4_up_ac", ch4_core: "channel_4_core", ch4_dn_front: "channel_4_dn_front", ch4_dn_ac: "channel_4_dn_ac", ch4_ctl: "channel_4_ctl",
}

const Pads = ({ pins, pitch = 0.65, span = 4, tht = false }: any) => {
  const left = Math.ceil(pins / 2)
  const Pad: any = tht ? "platedhole" : "smtpad"
  return <footprint>
    {Array.from({ length: left }, (_, i) => <Pad key={`l${i}`}
      portHints={[`${i + 1}`]} pcbX={`${-span / 2}mm`}
      pcbY={`${((left - 1) / 2 - i) * pitch}mm`}
      {...(tht ? { outerDiameter: "1mm", holeDiameter: "0.5mm", shape: "circle" }
                : { width: "1mm", height: `${Math.min(0.35, pitch * 0.55)}mm`, shape: "rect" })} />)}
    {Array.from({ length: pins - left }, (_, i) => <Pad key={`r${i}`}
      portHints={[`${left + i + 1}`]} pcbX={`${span / 2}mm`}
      pcbY={`${(-(pins - left - 1) / 2 + i) * pitch}mm`}
      {...(tht ? { outerDiameter: "1mm", holeDiameter: "0.5mm", shape: "circle" }
                : { width: "1mm", height: `${Math.min(0.35, pitch * 0.55)}mm`, shape: "rect" })} />)}
  </footprint>
}

const supplier = (code: string) => code?.startsWith("C")
  ? { jlcpcb: [code] } : undefined

// Disposable tscircuit PCB coordinates only: keep its packer out of the
// schematic build. The manufacturing placement is independently authored in
// floorplan.yaml and never imported from these coordinates.
const loc = (name: string) => {
  const prefix = name[0]
  const number = Number(name.slice(1)) || 1
  const index = prefix === "F" ? 0
    : prefix === "J" ? number
    : prefix === "Q" ? 10 + number
    : prefix === "U" ? 15 + number
    : prefix === "R" ? 40 + number
    : 120 + number
  return { pcbX: `${-200 + (index % 20) * 20}mm`,
           pcbY: `${140 - Math.floor(index / 20) * 30}mm` }
}

const R = ({ name, value, a, b, code, sheet, schX, schY, schRotation }: any) => <resistor
  name={name} resistance={value} footprint="0402"
  manufacturerPartNumber={code} supplierPartNumbers={supplier(code)}
  {...loc(name)}
  schSectionName={sheet} schSheetName={SHEETS[sheet]}
  schX={schX} schY={schY} schRotation={schRotation}
  connections={{ pin1: N(a), pin2: N(b) }} />

const C = ({ name, value, a, b, code, sheet, schX, schY, schRotation }: any) => <capacitor
  name={name} capacitance={value} footprint="0402"
  manufacturerPartNumber={code} supplierPartNumbers={supplier(code)}
  {...loc(name)}
  schSectionName={sheet} schSheetName={SHEETS[sheet]}
  schX={schX} schY={schY} schRotation={schRotation}
  connections={{ pin1: N(a), pin2: N(b) }} />

const Chip = ({ name, mpn, code, pins, connections, sheet, pitch, span, tht = false,
  arrangement, schX, schY, schRotation, schPinStyle }: any) => <chip name={name} manufacturerPartNumber={mpn}
  supplierPartNumbers={supplier(code || mpn)}
  {...loc(name)}
  schSectionName={sheet} schSheetName={SHEETS[sheet]}
  schX={schX} schY={schY} schRotation={schRotation}
  schPinStyle={schPinStyle}
  pinLabels={Object.fromEntries(Object.entries(pins).map(([k, v]) => [`pin${k}`, v]))}
  schPinArrangement={arrangement}
  connections={Object.fromEntries(Object.entries(connections).map(([k, v]) => [`pin${k}`, N(v as string)]))}
  footprint={<Pads pins={Math.max(...Object.keys(pins).map(Number))} pitch={pitch} span={span} tht={tht} />} />

type ChannelSpec = {
  n: number, up: string, dn: string, redriver: string, usb2: string,
  power: string, esdUp: string, esdDn: string, gate: string, fet: string,
  cap0: number, res0: number,
}

const Channel = (s: ChannelSpec) => {
  const i = s.n
  const upFrontSheet = `ch${i}_up_front`, upAcSheet = `ch${i}_up_ac`
  const coreSheet = `ch${i}_core`, dnFrontSheet = `ch${i}_dn_front`
  const dnAcSheet = `ch${i}_dn_ac`, ctlSheet = `ch${i}_ctl`
  const ss = (path: string, seg: string, pol: string) => `USB${i}_SS_${path}_${seg}_${pol}`
  const hs = (side: string, pol: string) => `USB${i}_HS_${side}_${pol}`
  const pwr = `PWR_EN${i}`, data = `DATA_EN${i}`, ok = `DATA_OK${i}`
  const oe = `USB2_OE${i}`, sel = `USB2_SEL${i}`, fault = `VBUS_FAULT${i}_N`
  const vbus = `VBUS${i}_SW`, ilim = `ILIM${i}`
  const r = (offset: number) => `R${s.res0 + offset}`
  const c = (offset: number) => `C${s.cap0 + offset}`

  const series = [
    ["TX_UP", 0, 0], ["TX_UP", 1, 1],
    ["TX_DN", 0, 2], ["TX_DN", 1, 3],
    ["RX_DN", 0, 4], ["RX_DN", 1, 5],
    ["RX_UP", 0, 6], ["RX_UP", 1, 7],
  ] as const
  const pol = (p: number) => p === 0 ? "P" : "N"

  return <>
    <Chip name={s.up} mpn="692221030100" code="C5334230" sheet={upFrontSheet}
      pins={{1:"VBUS_NC",2:"D-",3:"D+",4:"GND",5:"SSTX-",6:"SSTX+",7:"GND_DRAIN",8:"SSRX-",9:"SSRX+",10:"SHIELD"}}
      connections={{2:hs("UP","N"),3:hs("UP","P"),4:"GND",5:ss("RX_UP","CONN","N"),6:ss("RX_UP","CONN","P"),7:"GND",8:ss("TX_UP","CONN","N"),9:ss("TX_UP","CONN","P"),10:"GND"}}
      pitch={1.5} span={8} schX={5} schY={0}
      arrangement={{ leftSide: [2,3,5,6,8,9], topSide: [1,10], bottomSide: [4,7] }} tht />
    <Chip name={s.dn} mpn="692121030100" code="692121030100" sheet={dnFrontSheet}
      pins={{1:"VBUS",2:"D-",3:"D+",4:"GND",5:"SSRX-",6:"SSRX+",7:"GND_DRAIN",8:"SSTX-",9:"SSTX+",10:"SHIELD"}}
      connections={{1:vbus,2:hs("DN","N"),3:hs("DN","P"),4:"GND",5:ss("RX_DN","CONN","N"),6:ss("RX_DN","CONN","P"),7:"GND",8:ss("TX_DN","CONN","N"),9:ss("TX_DN","CONN","P"),10:"GND"}}
      pitch={1.5} span={8} schX={5} schY={0}
      arrangement={{ leftSide: [2,3,5,6,8,9], topSide: [1,10], bottomSide: [4,7] }} tht />

    <Chip name={s.esdUp} mpn="TPD6E05U06RVZR" code="C962978" sheet={upFrontSheet}
      pins={{1:"NC1",2:"NC2",3:"NC3",4:"NC4",5:"GND1",6:"NC6",7:"NC7",8:"D3-",9:"D3+",10:"GND2",11:"D2-",12:"D2+",13:"D1-",14:"D1+"}}
      // TI SLVSBO7O Table 4-3 and Figure 7-11 explicitly reserve the opposite
      // NC lands for optional straight-through PCB routing.  Tie each such
      // land to the same external net as the protected I/O opposite it; the
      // package does not join them internally, but the continuous board trace
      // does.  Physical connector lane order remains RX, USB2, TX.
      connections={{1:ss("TX_UP","CONN","P"),2:ss("TX_UP","CONN","N"),3:hs("UP","P"),4:hs("UP","N"),5:"GND",6:ss("RX_UP","CONN","P"),7:ss("RX_UP","CONN","N"),8:ss("RX_UP","CONN","N"),9:ss("RX_UP","CONN","P"),10:"GND",11:hs("UP","N"),12:hs("UP","P"),13:ss("TX_UP","CONN","N"),14:ss("TX_UP","CONN","P")}}
      pitch={0.5} span={3.5} schX={-5} schY={0}
      schPinStyle={{pin4: {marginTop: "2mm"}}}
      arrangement={{ leftSide: [1,2,3,4,6,7], rightSide: [8,9], topSide: [11,12], bottomSide: [13,14,5,10] }} />
    <Chip name={s.esdDn} mpn="TPD6E05U06RVZR" code="C962978" sheet={dnFrontSheet}
      pins={{1:"NC1",2:"NC2",3:"NC3",4:"NC4",5:"GND1",6:"NC6",7:"NC7",8:"D3-",9:"D3+",10:"GND2",11:"D2-",12:"D2+",13:"D1-",14:"D1+"}}
      // The Type-A footprint presents RX_N, RX_P, HS_P, HS_N, TX_N, TX_P.
      // Pair each protected I/O with its opposite optional flow-through land,
      // preserving named polarity end to end.
      connections={{1:ss("RX_DN","CONN","N"),2:ss("RX_DN","CONN","P"),3:hs("DN","P"),4:hs("DN","N"),5:"GND",6:ss("TX_DN","CONN","N"),7:ss("TX_DN","CONN","P"),8:ss("TX_DN","CONN","P"),9:ss("TX_DN","CONN","N"),10:"GND",11:hs("DN","N"),12:hs("DN","P"),13:ss("RX_DN","CONN","P"),14:ss("RX_DN","CONN","N")}}
      pitch={0.5} span={3.5} schX={-5} schY={0}
      schPinStyle={{pin4: {marginTop: "2mm"}}}
      arrangement={{ leftSide: [1,2,3,4,6,7], rightSide: [13,14], topSide: [11,12], bottomSide: [8,9,5,10] }} />

    {series.map(([path, pi, ro]) => {
      const upstream = path.endsWith("UP")
      const lane = upstream ? ({0:6,1:2,6:-2,7:-6} as Record<number,number>)[ro]
                            : ({2:6,3:2,4:-2,5:-6} as Record<number,number>)[ro]
      return <R key={r(ro)} name={r(ro)} value="2.2ohm"
      a={ss(path,"CONN",pol(pi))} b={ss(path,"MID",pol(pi))}
      code="C327251" sheet={upstream ? upAcSheet : dnAcSheet} schX={-3} schY={lane} />
    })}
    <C name={c(0)} value="100nF" a={ss("TX_UP","MID","P")} b={ss("TX_UP","IC","P")} code="C1525" sheet={upAcSheet} schX={3} schY={6} />
    <C name={c(1)} value="100nF" a={ss("TX_UP","MID","N")} b={ss("TX_UP","IC","N")} code="C1525" sheet={upAcSheet} schX={3} schY={2} />
    <C name={c(2)} value="100nF" a={ss("TX_DN","IC","P")} b={ss("TX_DN","MID","P")} code="C1525" sheet={dnAcSheet} schX={3} schY={6} />
    <C name={c(3)} value="100nF" a={ss("TX_DN","IC","N")} b={ss("TX_DN","MID","N")} code="C1525" sheet={dnAcSheet} schX={3} schY={2} />
    <C name={c(4)} value="100nF" a={ss("RX_UP","IC","P")} b={ss("RX_UP","MID","P")} code="C1525" sheet={upAcSheet} schX={3} schY={-2} />
    <C name={c(5)} value="100nF" a={ss("RX_UP","IC","N")} b={ss("RX_UP","MID","N")} code="C1525" sheet={upAcSheet} schX={3} schY={-6} />
    <C name={c(6)} value="330nF" a={ss("RX_DN","MID","P")} b={ss("RX_DN","IC","P")} code="C19271634" sheet={dnAcSheet} schX={3} schY={-2} />
    <C name={c(7)} value="330nF" a={ss("RX_DN","MID","N")} b={ss("RX_DN","IC","N")} code="C19271634" sheet={dnAcSheet} schX={3} schY={-6} />
    <R name={`R${33 + (i-1)*2}`} value="220kohm" a={ss("RX_DN","IC","P")} b="GND" code="C138030" sheet={coreSheet} schX={8} schY={3} schRotation={90} />
    <R name={`R${34 + (i-1)*2}`} value="220kohm" a={ss("RX_DN","IC","N")} b="GND" code="C138030" sheet={coreSheet} schX={8} schY={-3} schRotation={90} />

    <Chip name={s.redriver} mpn="TUSB522PIRGER" code="C2675181" sheet={coreSheet}
      pins={{1:"VCC1",2:"EQ1",3:"DE2",4:"OS2",5:"EN_RXD",6:"NC6",7:"NC7",8:"RX1N",9:"RX1P",10:"GND1",11:"TX2N",12:"TX2P",13:"VCC2",14:"RSV",15:"OS1",16:"DE1",17:"EQ2",18:"NC18",19:"RX2P",20:"RX2N",21:"GND2",22:"TX1P",23:"TX1N",24:"NC24",25:"EP"}}
      connections={{1:"N3V3",2:"TUSB_EQ1",3:"TUSB_DE2",4:"TUSB_OS2",5:ok,8:ss("TX_UP","IC","N"),9:ss("TX_UP","IC","P"),10:"GND",11:ss("RX_UP","IC","N"),12:ss("RX_UP","IC","P"),13:"N3V3",15:"TUSB_OS1",16:"TUSB_DE1",17:"TUSB_EQ2",19:ss("RX_DN","IC","P"),20:ss("RX_DN","IC","N"),21:"GND",22:ss("TX_DN","IC","P"),23:ss("TX_DN","IC","N"),25:"GND"}}
      pitch={0.5} span={4} schX={0} schY={0}
      arrangement={{ leftSide: [8,9,11,12], rightSide: [19,20,22,23], topSide: [1,2,3,4,5,13,15,16,17], bottomSide: [6,7,10,14,18,21,24,25] }} />
    <C name={c(8)} value="100nF" a="N3V3" b="GND" code="C1525" sheet={coreSheet} schX={-8} schY={4} />
    <C name={c(9)} value="100nF" a="N3V3" b="GND" code="C1525" sheet={coreSheet} schX={-8} schY={0} />
    <C name={c(10)} value="10uF" a="N3V3" b="GND" code="C15525" sheet={coreSheet} schX={-8} schY={-4} />

    <Chip name={s.usb2} mpn="TS3USB221ERSER" code="C129313" sheet={ctlSheet}
      pins={{1:"1D+",2:"1D-",3:"2D+_NC",4:"2D-_NC",5:"GND",6:"OE",7:"D-",8:"D+",9:"S",10:"VCC"}}
      connections={{1:hs("DN","P"),2:hs("DN","N"),5:"GND",6:oe,7:hs("UP","N"),8:hs("UP","P"),9:sel,10:"N3V3"}}
      pitch={0.4} span={2} />
    <C name={c(11)} value="100nF" a="N3V3" b="GND" code="C1525" sheet={ctlSheet} />
    <Chip name={s.fet} mpn="2N7002-7-F" code="C85049" sheet={ctlSheet}
      pins={{1:"G",2:"S",3:"D"}} connections={{1:ok,2:"GND",3:oe}}
      pitch={0.95} span={2.4} />
    <R name={`R${57+i-1}`} value="100kohm" a="N3V3" b={oe} code="C60491" sheet={ctlSheet} />
    <R name={`R${61+i-1}`} value="100kohm" a={sel} b="GND" code="C60491" sheet={ctlSheet} />

    <Chip name={s.gate} mpn="SN74LVC1G08DCKR" code="C7832" sheet={ctlSheet}
      pins={{1:"A",2:"B",3:"GND",4:"Y",5:"VCC"}}
      connections={{1:pwr,2:data,3:"GND",4:ok,5:"N3V3"}} pitch={0.65} span={2.2} />
    <C name={c(13)} value="100nF" a="N3V3" b="GND" code="C1525" sheet={ctlSheet} />

    <Chip name={s.power} mpn="TPS2557DRBR" code="C130056" sheet={ctlSheet}
      pins={{1:"GND",2:"IN1",3:"IN2",4:"EN",5:"ILIM",6:"OUT1",7:"OUT2",8:"FAULT",9:"EP"}}
      connections={{1:"GND",2:"P5V_PROTECTED",3:"P5V_PROTECTED",4:pwr,5:ilim,6:vbus,7:vbus,8:fault,9:"GND"}}
      pitch={0.65} span={3} />
    <C name={c(12)} value="100nF" a="P5V_PROTECTED" b="GND" code="C1525" sheet={ctlSheet} />
    <R name={`R${66+i-1}`} value="100kohm" a={ilim} b="GND" code="C60491" sheet={ctlSheet} />
    <R name={`R${71+i-1}`} value="10kohm" a="N3V3" b={fault} code="C60490" sheet={ctlSheet} />
    <C name={c(14)} value="100nF" a={vbus} b="GND" code="C1525" sheet={ctlSheet} />
    <C name={c(15)} value="150uF" a={vbus} b="GND" code="C264054" sheet={ctlSheet} />
  </>
}

const channels: ChannelSpec[] = [
  {n:1,up:"J3",dn:"J4",redriver:"U2",usb2:"U3",power:"U4",esdUp:"U5",esdDn:"U6",gate:"U7",fet:"Q2",cap0:6,res0:1},
  {n:2,up:"J5",dn:"J6",redriver:"U8",usb2:"U9",power:"U10",esdUp:"U11",esdDn:"U12",gate:"U13",fet:"Q3",cap0:22,res0:9},
  {n:3,up:"J7",dn:"J8",redriver:"U14",usb2:"U15",power:"U16",esdUp:"U17",esdDn:"U18",gate:"U19",fet:"Q4",cap0:38,res0:17},
  {n:4,up:"J9",dn:"J10",redriver:"U20",usb2:"U21",power:"U22",esdUp:"U23",esdDn:"U24",gate:"U25",fet:"Q5",cap0:54,res0:25},
]

const GpioControl = ({ i }: { i: number }) => <>
  <R name={`R${39+i*2}`} value="1kohm" a={["GPIO17_RAW","GPIO22_RAW","GPIO24_RAW","GPIO5_RAW"][i-1]} b={`PWR_EN${i}`} code="C106235" sheet="gpio" schX={1} schY={15-(i-1)*10} />
  <R name={`R${40+i*2}`} value="1kohm" a={["GPIO27_RAW","GPIO23_RAW","GPIO25_RAW","GPIO6_RAW"][i-1]} b={`DATA_EN${i}`} code="C106235" sheet="gpio" schX={1} schY={11-(i-1)*10} />
  <R name={`R${47+i*2}`} value="100kohm" a={`PWR_EN${i}`} b="GND" code="C60491" sheet="gpio" schX={7} schY={15-(i-1)*10} />
  <R name={`R${48+i*2}`} value="100kohm" a={`DATA_EN${i}`} b="GND" code="C60491" sheet="gpio" schX={7} schY={11-(i-1)*10} />
</>

// This canvas is intentionally generous because tscircuit still runs its
// disposable component packer even with routing disabled. It is not the PCB
// outline; the reviewed KiCad floorplan owns manufacturing geometry.
export default () => <board width="500mm" height="350mm" routingDisabled>
  <schematicsheet name="input" displayName="SEPARATE 5.2 V INPUT — FUSE / REVERSE POLARITY / LOCAL 3.3 V" sheetIndex={1} />
  <schematicsheet name="gpio" displayName="RASPBERRY PI 40-PIN GPIO — SUPPLY PINS NC / EIGHT FAIL-SAFE COMMANDS" sheetIndex={2} />
  <schematicsheet name="straps" displayName="TUSB522P GLOBAL STRAPS — ALL SIX STATES FIXED LOW" sheetIndex={3} />
  {[1,2,3,4].flatMap((i) => [
    <schematicsheet key={`${i}uf`} name={`channel_${i}_up_front`}
      displayName={`USB CHANNEL ${i} — UPSTREAM TYPE-B / ESD FRONT END`} sheetIndex={4+(i-1)*6} />,
    <schematicsheet key={`${i}ua`} name={`channel_${i}_up_ac`}
      displayName={`USB CHANNEL ${i} — UPSTREAM SUPER SPEED SERIES / AC PATHS`} sheetIndex={5+(i-1)*6} />,
    <schematicsheet key={`${i}r`} name={`channel_${i}_core`}
      displayName={`USB CHANNEL ${i} — TUSB522P REDRIVER CORE / STRAPS`} sheetIndex={6+(i-1)*6} />,
    <schematicsheet key={`${i}df`} name={`channel_${i}_dn_front`}
      displayName={`USB CHANNEL ${i} — DOWNSTREAM TYPE-A / ESD FRONT END`} sheetIndex={7+(i-1)*6} />,
    <schematicsheet key={`${i}da`} name={`channel_${i}_dn_ac`}
      displayName={`USB CHANNEL ${i} — DOWNSTREAM SUPER SPEED SERIES / AC PATHS`} sheetIndex={8+(i-1)*6} />,
    <schematicsheet key={`${i}c`} name={`channel_${i}_ctl`}
      displayName={`USB CHANNEL ${i} — POWER / USB2 / HARDWARE INTERLOCK`} sheetIndex={9+(i-1)*6} />,
  ])}

  <Chip name="J1" mpn="1935161" code="C3819953" sheet="input"
    pins={{1:"EXT_5V_RAW",2:"GND"}} connections={{1:"EXT_5V_RAW",2:"GND"}}
    pitch={5} span={5} tht />
  <Chip name="F1" mpn="3568" code="C5249699" sheet="input"
    pins={{1:"FUSE_A",2:"FUSE_B"}} connections={{1:"EXT_5V_RAW",2:"EXT_5V_FUSED"}}
    pitch={5} span={9.9} tht />
  <Chip name="Q1" mpn="DMP3007SPS-13" code="C397981" sheet="input"
    pins={{1:"G",2:"S1",3:"S2",4:"S3",5:"D1",6:"D2",7:"D3",8:"D4"}}
    connections={{1:"RPP_GATE",2:"P5V_PROTECTED",3:"P5V_PROTECTED",4:"P5V_PROTECTED",5:"EXT_5V_FUSED",6:"EXT_5V_FUSED",7:"EXT_5V_FUSED",8:"EXT_5V_FUSED"}}
    pitch={1.27} span={5.2} />
  <R name="R65" value="100kohm" a="RPP_GATE" b="GND" code="C60491" sheet="input" />
  <R name="R70" value="1Mohm" a="P5V_PROTECTED" b="RPP_GATE" code="C138033" sheet="input" />
  <C name="C1" value="180uF" a="EXT_5V_RAW" b="GND" code="C136277" sheet="input" />
  <C name="C2" value="180uF" a="P5V_PROTECTED" b="GND" code="C136277" sheet="input" />
  <Chip name="U1" mpn="TLV76133DCYR" code="C7527500" sheet="input"
    pins={{1:"GND",2:"OUT",3:"IN"}} connections={{1:"GND",2:"N3V3",3:"P5V_PROTECTED"}}
    pitch={2.3} span={5} />
  <C name="C3" value="100nF" a="P5V_PROTECTED" b="GND" code="C1525" sheet="input" />
  <C name="C4" value="1uF" a="N3V3" b="GND" code="C52923" sheet="input" />
  <C name="C5" value="10uF" a="N3V3" b="GND" code="C15525" sheet="input" />

  <Chip name="J2" mpn="61304021121" code="C5364405" sheet="gpio"
    pins={Object.fromEntries(Array.from({length:40},(_,i)=>[i+1,`P${i+1}`]))}
    connections={{6:"GND",9:"GND",11:"GPIO17_RAW",13:"GPIO27_RAW",14:"GND",15:"GPIO22_RAW",16:"GPIO23_RAW",18:"GPIO24_RAW",20:"GND",22:"GPIO25_RAW",25:"GND",29:"GPIO5_RAW",30:"GND",31:"GPIO6_RAW",34:"GND",39:"GND"}}
    pitch={2.54} span={2.54} schX={-7} schY={-2}
    arrangement={{ leftSide: [1,2,3,4,5,7,8,10,12,17,19,21,23,24,26,27,28,32,33,35,36,37,38,40], rightSide: [11,13,15,16,18,22,29,31], bottomSide: [6,9,14,20,25,30,34,39] }} tht />
  {[1,2,3,4].map((i) => <GpioControl key={i} i={i} />)}
  {[["TUSB_EQ1",75],["TUSB_EQ2",76],["TUSB_DE1",77],["TUSB_DE2",78],["TUSB_OS1",79],["TUSB_OS2",80]].map(([net,ref]:any) =>
    <R key={ref} name={`R${ref}`} value="4.7kohm" a={net} b="GND" code="C105871" sheet="straps"
      schX={-5+(ref-75)*2} schY={0} schRotation={90} />)}

  {channels.map((channel) => <Channel key={channel.n} {...channel} />)}
</board>

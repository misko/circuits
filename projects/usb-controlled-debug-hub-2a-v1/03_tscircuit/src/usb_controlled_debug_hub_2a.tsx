// Four-port self-powered USB 2.0 debug hub with 2 A continuous capability at
// every USB-A port. USB-C DATA is upstream USB 2.0 data and VBUS sense only.
// USB-C POWER is a hardware-configured 20 V / 3 A PD sink feeding two retained
// 5 V / 6 A converter banks. One internal downstream port is a
// factory-programmed MCP2221A management function; no project firmware exists.

import { sel } from "tscircuit"

// Orderable sourcing aliases preserve a declared value and footprint while
// replacing catalog rows that the JLCPCB uploader could not allocate. Keep
// this map release-neutral: stale release numbers in authoritative electrical
// source previously made a later release non-hermetic.
const ORDERABLE_SOURCING: Record<string, string> = {
  C25741: "C25741",    // 100k, 1%, 0402
  C392963: "C60474",   // 100nF, X7R, 16V, 0402
  C843837: "C25744",   // 10k, 1%, 0402
  C2483395: "C2076721", // 165k, 1%, 0402
  C326568: "C52923",   // 1uF, X5R, 25V, 0402
  C55530: "C21397",    // 22uF, X7R, 25V, 1210
  C342849: "C107048",  // 3.3nF, C0G, 5%, 0603
  C482193: "C25900",   // 4.7k, 1%, 0402
}

const sourcingCode = (code: string) => ORDERABLE_SOURCING[code] ?? code

const TwoSided = ({ pins, pitch = 0.65, span = 5.4 }: { pins: number; pitch?: number; span?: number }) => {
  const half = Math.ceil(pins / 2)
  return <footprint>
    {Array.from({ length: half }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 1}`]}
      pcbX={`${-span / 2}mm`} pcbY={`${((half - 1) / 2 - i) * pitch}mm`}
      width="1mm" height={`${Math.min(0.32, pitch * 0.58)}mm`} shape="rect" />)}
    {Array.from({ length: pins - half }, (_, i) => <smtpad key={`r${i}`} portHints={[`${half + i + 1}`]}
      pcbX={`${span / 2}mm`} pcbY={`${(-(pins - half - 1) / 2 + i) * pitch}mm`}
      width="1mm" height={`${Math.min(0.32, pitch * 0.58)}mm`} shape="rect" />)}
  </footprint>
}

const Qfn64Ep = () => <footprint>
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`b${i}`} portHints={[`${i + 1}`]} pcbX={`${-3.75 + i * 0.5}mm`} pcbY="-4.5mm" width="0.28mm" height="1mm" shape="rect" />)}
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${i + 17}`]} pcbX="4.5mm" pcbY={`${-3.75 + i * 0.5}mm`} width="1mm" height="0.28mm" shape="rect" />)}
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`t${i}`} portHints={[`${i + 33}`]} pcbX={`${3.75 - i * 0.5}mm`} pcbY="4.5mm" width="0.28mm" height="1mm" shape="rect" />)}
  {Array.from({ length: 16 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 49}`]} pcbX="-4.5mm" pcbY={`${3.75 - i * 0.5}mm`} width="1mm" height="0.28mm" shape="rect" />)}
  <smtpad portHints={["65"]} pcbX="0mm" pcbY="0mm" width="4.7mm" height="4.7mm" shape="rect" />
</footprint>

const UsbB = () => <footprint>
  <platedhole portHints={["1"]} pcbX="1.25mm" pcbY="-2mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="-1.25mm" pcbY="-2mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["3"]} pcbX="-1.25mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["4"]} pcbX="1.25mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />
  <platedhole portHints={["5", "SH"]} pcbX="-6.02mm" pcbY="2.71mm" outerDiameter="3.5mm" holeDiameter="2.3mm" shape="circle" />
  <platedhole portHints={["5", "SH"]} pcbX="6.02mm" pcbY="2.71mm" outerDiameter="3.5mm" holeDiameter="2.3mm" shape="circle" />
</footprint>

// HRO TYPE-C-31-M-12 / JLC C165948. The real KiCad footprint is authored
// directly from the exact drawing; this inline copy preserves its electrical
// pad identities and land geometry through the TSX bridge.
const UsbC16 = () => <footprint>
  {[[-3.2,"A1"],[-2.4,"A4"],[-1.25,"A5"],[-0.25,"A6"],[0.25,"A7"],[1.25,"A8"],[2.4,"A9"],[3.2,"A12"],
    [3.2,"B1"],[2.4,"B4"],[1.75,"B5"],[0.75,"B6"],[-0.75,"B7"],[-1.75,"B8"],[-2.4,"B9"],[-3.2,"B12"]].map(([x,p],i) =>
    <smtpad key={`${p}`} portHints={[`${p}`,`${i + 1}`]} pcbX={`${x}mm`} pcbY="-3.67mm"
      width={`${Math.abs(Number(x)) === 2.4 || Math.abs(Number(x)) === 3.2 ? 0.6 : 0.3}mm`} height="1.14mm" shape="rect" />)}
  <platedhole portHints={["SH","17"]} pcbX="-4.325mm" pcbY="-3.1mm" outerWidth="0.9mm" outerHeight="2mm" holeWidth="0.6mm" holeHeight="1.7mm" shape="oval" />
  <platedhole portHints={["SH","17"]} pcbX="4.325mm" pcbY="-3.1mm" outerWidth="0.9mm" outerHeight="2mm" holeWidth="0.6mm" holeHeight="1.7mm" shape="oval" />
  <platedhole portHints={["SH","17"]} pcbX="-4.325mm" pcbY="1.08mm" outerWidth="0.9mm" outerHeight="1.7mm" holeWidth="0.6mm" holeHeight="1.4mm" shape="oval" />
  <platedhole portHints={["SH","17"]} pcbX="4.325mm" pcbY="1.08mm" outerWidth="0.9mm" outerHeight="1.7mm" holeWidth="0.6mm" holeHeight="1.4mm" shape="oval" />
</footprint>

const Ch224kFp = () => <footprint>
  {Array.from({ length: 5 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 1}`]}
    pcbX="-2.45mm" pcbY={`${2 - i}mm`} width="1.1mm" height="0.55mm" shape="rect" />)}
  {Array.from({ length: 5 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${10 - i}`]}
    pcbX="2.45mm" pcbY={`${2 - i}mm`} width="1.1mm" height="0.55mm" shape="rect" />)}
  <smtpad portHints={["11","EP"]} pcbX="0mm" pcbY="0mm" width="2.8mm" height="3.2mm" shape="rect" />
</footprint>

const Tps56637Fp = () => <footprint>
  {[1,2,3,4].map((p,i) => <smtpad key={`l${p}`} portHints={[`${p}`]}
    pcbX="-1.4mm" pcbY={`${-0.75 + i * 0.5}mm`} width="0.6mm" height="0.25mm" shape="rect" />)}
  <smtpad portHints={["5"]} pcbX="-0.7mm" pcbY="1.05mm" width="0.6mm" height="0.37mm" shape="rect" />
  <smtpad portHints={["6"]} pcbX="0mm" pcbY="0.475mm" width="1.4mm" height="0.95mm" shape="rect" />
  <smtpad portHints={["7"]} pcbX="0.7mm" pcbY="1.05mm" width="0.6mm" height="0.37mm" shape="rect" />
  {[8,9,10].map((p,i) => <smtpad key={`r${p}`} portHints={[`${p}`]}
    pcbX="1.4mm" pcbY={`${0.5 - i * 0.5}mm`} width="0.6mm" height="0.25mm" shape="rect" />)}
</footprint>

const Mwsa0804 = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-2.65mm" pcbY="0mm" width="2.5mm" height="3.4mm" shape="rect" />
  <smtpad portHints={["2"]} pcbX="2.65mm" pcbY="0mm" width="2.5mm" height="3.4mm" shape="rect" />
</footprint>

// TSX bridge geometry only. The KiCad promotion step replaces these by the
// exact source-owned 1206 footprints selected from the part dossiers.
const Smd1206 = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-1.4mm" pcbY="0mm" width="1.4mm" height="1.8mm" shape="rect" />
  <smtpad portHints={["2"]} pcbX="1.4mm" pcbY="0mm" width="1.4mm" height="1.8mm" shape="rect" />
</footprint>

const UsbA = () => <footprint>
  {Array.from({ length: 4 }, (_, i) => <platedhole key={`p${i}`} portHints={[`${i + 1}`]}
    pcbX={`${[-3, -1, 1, 3][i]}mm`} pcbY="3.5mm" outerDiameter="1.7mm" holeDiameter="0.92mm" shape="circle" />)}
  <platedhole portHints={["5", "SH"]} pcbX="-3.5mm" pcbY="-1mm" outerDiameter="3.4mm" holeDiameter="2.26mm" shape="circle" />
</footprint>

const InputTerminal = () => <footprint>
  <platedhole portHints={["1"]} pcbX="-2.5mm" pcbY="0mm" outerDiameter="2.2mm" holeDiameter="1.3mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="2.5mm" pcbY="0mm" outerDiameter="2.2mm" holeDiameter="1.3mm" shape="circle" />
</footprint>

const BladeFuse = () => <footprint>
  <platedhole portHints={["1"]} pcbX="-4.95mm" pcbY="-2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  <platedhole portHints={["1"]} pcbX="-4.95mm" pcbY="2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="4.95mm" pcbY="-2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
  <platedhole portHints={["2"]} pcbX="4.95mm" pcbY="2.5mm" outerDiameter="3.4mm" holeDiameter="2mm" shape="circle" />
</footprint>

const PowerDi5060 = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-1.905mm" pcbY="2.74mm" width="0.6mm" height="1.27mm" shape="rect" />
  {[2, 3, 4].map((p, i) => <smtpad key={`s${p}`} portHints={[`${p}`]} pcbX={`${-0.635 + i * 1.27}mm`} pcbY="2.74mm" width="0.6mm" height="1.27mm" shape="rect" />)}
  {[5, 6, 7, 8].map((p, i) => <smtpad key={`d${p}`} portHints={[`${p}`]} pcbX={`${1.905 - i * 1.27}mm`} pcbY="-2.74mm" width="0.6mm" height="1.02mm" shape="rect" />)}
</footprint>

const SunlordSwpa4030 = () => <footprint>
  <smtpad portHints={["1"]} pcbX="-1.5mm" pcbY="0mm" width="1.1mm" height="3.7mm" shape="rect" />
  <smtpad portHints={["2"]} pcbX="1.5mm" pcbY="0mm" width="1.1mm" height="3.7mm" shape="rect" />
</footprint>

const Tps2557Fp = () => <footprint>
  {Array.from({ length: 4 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-1.65mm" pcbY={`${0.975 - i * 0.65}mm`} width="0.9mm" height="0.35mm" shape="rect" />)}
  {Array.from({ length: 4 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${i + 5}`]} pcbX="1.65mm" pcbY={`${-0.975 + i * 0.65}mm`} width="0.9mm" height="0.35mm" shape="rect" />)}
  <smtpad portHints={["9"]} pcbX="0mm" pcbY="0mm" width="1.65mm" height="2.4mm" shape="rect" />
</footprint>

// TI RPW0010A HotRod QFN. The project-local KiCad footprint is checked against
// TI drawing 4225183/A and exact JLC CAD for this shared physical package;
// this source footprint preserves the ten-pin topology for schematic export.
const Tps25947Fp = () => <footprint>
  {[1, 2, 3, 4].map((p, i) => <smtpad key={`l${p}`} portHints={[`${p}`]}
    pcbX="-0.9mm" pcbY={`${0.7125 - i * 0.475}mm`} width="0.6mm" height="0.25mm" shape="rect" />)}
  <smtpad portHints={["5"]} pcbX="-0.3mm" pcbY="0mm" width="0.3mm" height="1.8mm" shape="rect" />
  <smtpad portHints={["6"]} pcbX="0.3mm" pcbY="0mm" width="0.3mm" height="1.8mm" shape="rect" />
  {[7, 8, 9, 10].map((p, i) => <smtpad key={`r${p}`} portHints={[`${p}`]}
    pcbX="0.9mm" pcbY={`${-0.7125 + i * 0.475}mm`} width="0.6mm" height="0.25mm" shape="rect" />)}
</footprint>

// TI RGE0024M VQFN-24. The project-local KiCad footprint replaces this
// schematic/export land with TI's exact split PowerPAD geometry and nine
// filled/capped 0.20 mm via-in-pad sites.
const Tps25980Fp = () => <footprint>
  {[1, 2, 3, 4, 5, 6].map((p, i) => <smtpad key={`l${p}`} portHints={[`${p}`]}
    pcbX="-1.9125mm" pcbY={`${-1.25 + i * 0.5}mm`} width="0.575mm" height="0.24mm" shape="rect" />)}
  {[7, 8, 9, 10, 11, 12].map((p, i) => <smtpad key={`b${p}`} portHints={[`${p}`]}
    pcbX={`${-1.25 + i * 0.5}mm`} pcbY="1.9125mm" width="0.24mm" height="0.575mm" shape="rect" />)}
  {[13, 14, 15, 16, 17, 18].map((p, i) => <smtpad key={`r${p}`} portHints={[`${p}`]}
    pcbX="1.9125mm" pcbY={`${1.25 - i * 0.5}mm`} width="0.575mm" height="0.24mm" shape="rect" />)}
  {[19, 20, 21, 22, 23, 24].map((p, i) => <smtpad key={`t${p}`} portHints={[`${p}`]}
    pcbX={`${1.25 - i * 0.5}mm`} pcbY="-1.9125mm" width="0.24mm" height="0.575mm" shape="rect" />)}
  <smtpad portHints={["25", "IN_POWERPAD"]} pcbX="0mm" pcbY="-0.625mm" width="2.7mm" height="1.45mm" shape="rect" />
  <smtpad portHints={["26", "GND_POWERPAD"]} pcbX="0mm" pcbY="0.925mm" width="2.7mm" height="0.85mm" shape="rect" />
</footprint>

// TI DRV0006A / TVS2200DRVR, WSON-6 2x2 mm. Pins 1-3 and exposed pad 7 are
// ground; pins 4-6 are the protected input. The project-local KiCad footprint
// is authored from the exact TI package drawing and example land pattern.
const Tvs2200Fp = () => <footprint>
  {[1, 2, 3].map((p, i) => <smtpad key={`g${p}`} portHints={[`${p}`]}
    pcbX="-1.03mm" pcbY={`${-0.65 + i * 0.65}mm`} width="0.607mm" height="0.364mm" shape="rect" />)}
  {[4, 5, 6].map((p, i) => <smtpad key={`v${p}`} portHints={[`${p}`]}
    pcbX="1.03mm" pcbY={`${0.65 - i * 0.65}mm`} width="0.607mm" height="0.364mm" shape="rect" />)}
  <smtpad portHints={["7", "EP"]} pcbX="0mm" pcbY="0mm" width="1mm" height="1.6mm" shape="rect" />
</footprint>

const Tps16630Fp = () => <footprint>
  {Array.from({ length: 10 }, (_, i) => <smtpad key={`l${i}`} portHints={[`${i + 1}`]}
    pcbX="-2.7mm" pcbY={`${2.925 - i * 0.65}mm`} width="1mm" height="0.35mm" shape="rect" />)}
  {Array.from({ length: 10 }, (_, i) => <smtpad key={`r${i}`} portHints={[`${20 - i}`]}
    pcbX="2.7mm" pcbY={`${-2.925 + i * 0.65}mm`} width="1mm" height="0.35mm" shape="rect" />)}
  <smtpad portHints={["21", "EP"]} pcbX="0mm" pcbY="0mm" width="3mm" height="4.2mm" shape="rect" />
</footprint>

const Polymer63 = () => <footprint>
  <smtpad portHints={["1", "POS"]} pcbX="-2.3mm" pcbY="0mm" width="2.2mm" height="2.7mm" shape="rect" />
  <smtpad portHints={["2", "NEG"]} pcbX="2.3mm" pcbY="0mm" width="2.2mm" height="2.7mm" shape="rect" />
</footprint>

const schProps = (name: string) => {
  // Most sheets contain label-connected functional islands. Keep those islands
  // close enough that the page renderer does not shrink symbols and labels to
  // an unreadable scale. The interlock sheet is already compact by construction.
  const at = (sheet: string, section: string, x: number, y: number) => {
    const scaleBySheet: Record<string, number> = {
      pd_power: 0.55,
      power: 0.55,
      hub: 0.28,
      hub_straps: 0.35,
      management: 0.35,
      interlocks: 1,
      port_1: 0.28,
      port_2: 0.28,
      port_3: 0.28,
      port_4: 0.28,
    }
    const scale = scaleBySheet[sheet] ?? 0.35
    return {
      schSheetName: sheet,
      schSectionName: section,
      schX: `${x * scale}mm`,
      schY: `${y * scale}mm`,
    }
  }
  const pdPower: Record<string, [number, number]> = {
    J_POWER: [-56, 10], F_PD: [-46, 10], D_PD_TVS: [-46, -1], U_PD: [-34, 10],
    R_PD_VDD: [-40, -8], C_PD_VDD: [-31, -8], R_PD_VBUS: [-27, -14],
    U_PD_IN: [-18, 10], R_PD_UV_TOP_HI: [-22, -8], R_PD_UV_TOP_LO: [-17, -8], R_PD_UV_MID: [-12, -8],
    R_PD_OV_BOT: [-4, -8], R_PD_IN_ILIM: [-20, -16], C_PD_IN_DVDT: [-10, -16],
    C_PD_IN1: [-14, 19], C_PD_IN2: [-5, 19], C_PD_IN_HF: [-26, 19],
  }
  if (pdPower[name]) return at("pd_power", "USB-C 20 V PD negotiation and protected input", ...pdPower[name])

  const bankPower = name.match(/^(?:U_BUCK|L_BUCK|U_AGG|C_BUCK|R_BUCK|R_FB|C_BST|C_AGG|R_AGG|C_BANK)_([AB])(?:_|$)/)
  if (bankPower) {
    const bank = bankPower[1]
    const normalized = name.replace(new RegExp(`_${bank}(?=_|$)`), "_N")
    const bankPos: Record<string, [number, number]> = {
      U_BUCK_N: [-40, 12], C_BUCK_N_IN1: [-46, 3], C_BUCK_N_IN2: [-38, 3], C_BST_N: [-31, 3],
      L_BUCK_N: [-27, 12], R_FB_N_TOP: [-20, 3], R_FB_N_BOT: [-13, 3],
      C_BUCK_N_OUT1: [-18, 12], C_BUCK_N_OUT2: [-11, 12], U_AGG_N: [12, 12],
      C_AGG_N_IN: [12, 3], R_AGG_N_ILIM: [20, -6], C_AGG_N_TIMER: [28, -6], C_AGG_N_DVDT: [36, -6],
      C_BANK_N_HF: [24, 12], C_BANK_N_BULK: [34, 12], C_BANK_N_POLY: [46, 12],
      R_BUCK_N_EN_TOP: [-45, -4], R_BUCK_N_EN_BOT: [-35, -4],
    }
    const [x, y] = bankPos[normalized] ?? [0, 0]
    return at("power", `5 V bank ${bank}`, x, y + (bank === "A" ? 0 : -24))
  }

  if (/^(?:U_MAIN|L_MAIN|C_MAIN(?:_.*)?|C_BST)$/.test(name)) {
    const mainPos: Record<string, [number, number]> = {
      U_MAIN: [-55, 34], C_MAIN_IN: [-65, 24], C_BST: [-45, 24],
      L_MAIN: [-40, 34], C_MAIN_OUT1: [-28, 34], C_MAIN_OUT2: [-28, 24],
    }
    return at("power", "Direct protected-input 3.3 V regulator", ...(mainPos[name] ?? [0, -34]))
  }

  const strap = name.match(/^R_(CFG|NONREM|SWAP|GANG|BOOST|DIS)(.*)$/)
  if (strap) {
    const strapPos: Record<string, [number, number]> = {
      R_CFG0: [-20, 12], R_CFG1: [-10, 12], R_CFG2: [0, 12],
      R_NONREM1: [10, 12], R_NONREM0: [20, 12],
      R_SWAP1: [-18, 2], R_SWAP2: [-6, 2], R_SWAP3: [6, 2], R_SWAP4: [18, 2],
      R_SWAP5: [-12, -8], R_SWAP6: [0, -8], R_SWAP7: [12, -8],
      R_GANG: [-12, -18], R_BOOST0: [0, -18], R_BOOST1: [12, -18],
      R_DIS6N: [-18, -28], R_DIS6P: [-6, -28], R_DIS7N: [6, -28], R_DIS7P: [18, -28],
    }
    return at("hub_straps", "USB2517I hardware configuration and disabled ports", ...(strapPos[name] ?? [0, 0]))
  }

  const hub: Record<string, [number, number]> = {
    J_DATA: [-38, 8], R_CC1: [-34, -4], R_CC2: [-27, -4], U_ESD_UP: [-20, 8], U_HUB: [0, 4], Y_HUB: [18, -4],
    R_XTAL: [18, -10], R_RBIAS: [12, 16], C_XTAL1: [14, -17], C_XTAL2: [22, -17],
    R_HUB_RESET: [-18, -12], C_HUB_RESET: [-10, -12],
    R_VBUS_TOP: [-22, 17], R_VBUS_BOT: [-15, 17],
  }
  const hubCaps = ["C_HUB_A1", "C_HUB_A2", "C_HUB_A3", "C_HUB_A4", "C_HUB_A_BULK", "C_HUB_CR_HF",
    "C_HUB_CR_BULK", "C_HUB_DD", "C_HUB_PLL", "C_HUB_18", "C_HUB_18PLL"]
  if (hubCaps.includes(name)) {
    const i = hubCaps.indexOf(name), row = Math.floor(i / 6), col = i % 6
    return at("hub", "Upstream USB and seven-port hub core", -22 + col * 9, -24 - row * 8)
  }
  if (hub[name]) return at("hub", "Upstream USB and seven-port hub core", ...hub[name])

  const port = name.match(/^(?:U_DATA|Q_DATA|U_PWR|U_ESD|J_PORT|R_ILIM|R_DATA_OE|R_DATA_OK|R_PWR_EN|C_DATA|C_PWR|C_PORT)([1-4])(?:_|$)/)
  if (port) {
    const prefix = name.replace(port[1], "N")
    const portPos: Record<string, [number, number]> = {
      U_DATAN: [-13, 5], C_DATAN: [-19, -1], R_DATA_OEN: [-13, 15], Q_DATAN: [-2, 12], R_DATA_OKN: [-1, 1],
      U_PWRN: [-8, -13], R_ILIMN: [-17, -19], R_PWR_ENN: [-7, -23], C_PWRN_IN: [-18, -10],
      C_PORTN_HF: [7, -13], C_PORTN_BULK: [25, -13], U_ESDN: [9, 5], J_PORTN: [35, 5],
    }
    return at(`port_${port[1]}`, `External USB port ${port[1]}`, ...(portPos[prefix] ?? [0, 0]))
  }

  const interlock: Record<string, [number, number]> = {
    U_AND_PWR: [-10, 6], C_AND_PWR: [-10, -6], U_AND_DATA: [10, 6], C_AND_DATA: [10, -6],
  }
  if (interlock[name]) return at("interlocks", "Hardware power and data interlocks", ...interlock[name])

  const management: Record<string, [number, number]> = {
    U_PWR_CTRL: [-20, 8], R_ILIM_CTRL: [-24, -2], C_PWR_CTRL_IN: [-17, -6],
    C_PWR_CTRL_OUT_HF: [-24, -10], C_PWR_CTRL_OUT: [-20, -17],
    U_CTRL: [-6, 5], C_CTRL_VDD: [-10, -7], C_CTRL_VUSB: [-4, -8], R_CTRL_RESET: [-12, -14],
    R_I2C_SCL: [-2, -19], R_I2C_SDA: [5, -19], U_EXP: [13, 5], C_EXP_VDD: [10, -7], R_EXP_RESET: [18, -10],
    R_PWR_CMD1: [-18, -25], R_PWR_CMD2: [-6, -25], R_PWR_CMD3: [6, -25], R_PWR_CMD4: [18, -25],
    R_DATA_CMD1: [-18, -33], R_DATA_CMD2: [-6, -33], R_DATA_CMD3: [6, -33], R_DATA_CMD4: [18, -33],
  }
  const managementProps = at("management", "Factory USB management and GPIO expander", ...(management[name] ?? [0, 0]))
  if (name === "R_I2C_SCL" || name === "R_I2C_SDA") return { ...managementProps, schRotation: "90deg" }
  return managementProps
}

const R = ({ name, value, a, b, jlc, fp = "0402" }: any) => <resistor name={name} resistance={value} footprint={fp}
  {...schProps(name)} supplierPartNumbers={{ jlcpcb: [sourcingCode(jlc)] }} connections={{ pin1: `net.${a}`, pin2: `net.${b}` }} />
const C = ({ name, value, a, b, jlc, fp = "0402", studyX, studyY }: any) => <capacitor name={name} capacitance={value} footprint={fp}
  {...schProps(name)}
  {...(studyX !== undefined ? { pcbX: `${studyX}mm`, pcbY: `${studyY}mm` } : {})}
  supplierPartNumbers={{ jlcpcb: [sourcingCode(jlc)] }} connections={{ pin1: `net.${a}`, pin2: `net.${b}` }} />

const Tps2557 = ({ name, input, en, out, fault, ilim, cin, coutHf, coutBulk, studyX }: any) => <group name={`${name}_cell`}>
  <chip name={name} manufacturerPartNumber="TPS2557DRBR"
    supplierPartNumbers={{ jlcpcb: ["C130056"] }} footprint={<Tps2557Fp />}
    {...schProps(name)}
    pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "EN", pin5: "ILIM", pin6: "OUT1", pin7: "OUT2", pin8: "FAULT_N", pin9: "EP" }}
    connections={{ pin1: "net.GND", pin2: `net.${input}`, pin3: `net.${input}`, pin4: `net.${en}`, pin5: `net.${ilim}`, pin6: `net.${out}`, pin7: `net.${out}`, pin8: `net.${fault}`, pin9: "net.GND" }} />
  <R name={`R_${ilim}`} value={out === "VBUS_CTRL" ? "187k" : "165k"} a={ilim} b="GND" jlc={out === "VBUS_CTRL" ? "C163486" : "C2483395"} />
  <C name={cin} value="100nF" a={input} b="GND" jlc="C392963" studyX={studyX} studyY={0} />
  <C name={coutHf} value="100nF" a={out} b="GND" jlc="C392963" studyX={studyX + 3} studyY={0} />
  {coutBulk ? <C name={coutBulk} value={out === "VBUS_CTRL" ? "1uF" : "22uF"} a={out} b="GND"
    jlc={out === "VBUS_CTRL" ? "C326568" : "C55530"} fp={out === "VBUS_CTRL" ? "0402" : "1210"} /> : null}
</group>

// TPS259470A uses the proven RPW0010A land and adds true reverse-current
// blocking to each exposed USB-A
// VBUS path.  FLT is active-low and therefore preserves the USB2517 OCS
// interface without an inversion or a firmware dependency.
const Tps259470Port = ({ name, input, en, out, fault, ilim, cin, coutHf, coutBulk, studyX }: any) => <group name={`${name}_cell`}>
  <chip name={name} manufacturerPartNumber="TPS259470ARPWR"
    supplierPartNumbers={{ jlcpcb: ["C3662799"] }} footprint={<Tps25947Fp />}
    {...schProps(name)}
    pinLabels={{ pin1: "EN_UVLO", pin2: "OVLO", pin3: "AUXOFF", pin4: "FAULT_N", pin5: "IN", pin6: "OUT", pin7: "DVDT", pin8: "GND", pin9: "ILM", pin10: "ITIMER" }}
    connections={{ pin1: `net.${en}`, pin2: "net.GND", pin4: `net.${fault}`, pin5: `net.${input}`, pin6: `net.${out}`, pin8: "net.GND", pin9: `net.${ilim}` }} />
  <R name={`R_${ilim}`} value="1.40k" a={ilim} b="GND" jlc="C178086" fp="0603" />
  <C name={cin} value="100nF" a={input} b="GND" jlc="C60474" studyX={studyX} studyY={0} />
  <C name={coutHf} value="100nF" a={out} b="GND" jlc="C60474" studyX={studyX + 3} studyY={0} />
  {coutBulk ? <C name={coutBulk} value="22uF" a={out} b="GND" jlc="C21397" fp="1210" /> : null}
</group>

const ExternalPort = ({ p, hubP, hubN, prtPwr, ocs, powerNet }: any) => {
  const hp = `P${p}_HUB_P`, hn = `P${p}_HUB_N`, pp = `P${p}_PORT_P`, pn = `P${p}_PORT_N`
  const vbus = `VBUS${p}_SW`
  return <group name={`external_port_${p}`} pcbX={`${(p - 2.5) * 105}mm`} pcbY="-100mm">
    <chip name={`U_DATA${p}`} supplierPartNumbers={{ jlcpcb: ["C11355"] }} footprint={<TwoSided pins={10} pitch={0.5} span={3.4} />}
      {...schProps(`U_DATA${p}`)}
      pinLabels={{ pin1: "VCC", pin2: "SEL", pin3: "D_PLUS", pin4: "D_MINUS", pin5: "GND", pin6: "HSD1_MINUS", pin7: "HSD1_PLUS", pin8: "HSD2_MINUS", pin9: "HSD2_PLUS", pin10: "OE" }}
      // The analog switch channels are electrically symmetric.  The outward-
      // facing USB-A footprint puts connector D+ on the left launch, so use
      // HSD1- / D- for logical D+ and HSD1+ / D+ for logical D-.  This keeps
      // the physical pair ordered through the switch without a PCB crossover.
      connections={{ pin1: "net.N3V3_MAIN", pin2: "net.GND", pin3: `net.${hn}`, pin4: `net.${hp}`, pin5: "net.GND", pin6: `net.${pp}`, pin7: `net.${pn}`, pin10: `net.DATA_OE${p}_N` }} />
    <C name={`C_DATA${p}`} value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />
    <R name={`R_DATA_OE${p}`} value="10k" a="N3V3_MAIN" b={`DATA_OE${p}_N`} jlc="C843837" />
    <chip name={`Q_DATA${p}`} supplierPartNumbers={{ jlcpcb: ["C85047"] }} footprint="sot23"
      {...schProps(`Q_DATA${p}`)}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: `net.DATA_OK${p}`, pin2: "net.GND", pin3: `net.DATA_OE${p}_N` }} />
    <R name={`R_DATA_OK${p}`} value="10k" a={`DATA_OK${p}`} b="GND" jlc="C843837" />
    <Tps259470Port name={`U_PWR${p}`} input={powerNet} en={`PWR_EN${p}`} out={vbus} fault={ocs} ilim={`ILIM${p}`}
      cin={`C_PWR${p}_IN`} coutHf={`C_PORT${p}_HF`} coutBulk={`C_PORT${p}_BULK`} studyX={-12} />
    <R name={`R_PWR_EN${p}`} value="10k" a={`PWR_EN${p}`} b="GND" jlc="C843837" />
    <chip name={`U_ESD${p}`} manufacturerPartNumber="PESD2USB5UX-TR" supplierPartNumbers={{ jlcpcb: ["C3709087"] }}
      footprint="sot23"
      {...schProps(`U_ESD${p}`)}
      pinLabels={{ pin1: "IO1", pin2: "IO2", pin3: "GND" }}
      connections={{ pin1: `net.${pp}`, pin2: `net.${pn}`, pin3: "net.GND" }} />
    <chip name={`J_PORT${p}`} manufacturerPartNumber="USB1130-15-A" footprint={<UsbA />}
      {...schProps(`J_PORT${p}`)}
      pinLabels={{ pin1: "VBUS", pin2: "D_MINUS", pin3: "D_PLUS", pin4: "GND", pin5: "SHIELD" }}
      connections={{ pin1: `net.${vbus}`, pin2: `net.${pn}`, pin3: `net.${pp}`, pin4: "net.GND", pin5: "net.GND" }} />
  </group>
}

// This oversized board is only tscircuit's non-authoritative auto-placement
// canvas. KiCad floorplan/placement owns the real 110 x 75 mm starting outline.
export default () => <board width="500mm" height="350mm" routingDisabled>
  <schematicsheet name="pd_power"
    displayName="USB-C POWER — 20 V / 3 A PD sink and 60 V protected input" sheetIndex={1} />
  <schematicsheet name="power"
    displayName="POWER DISTRIBUTION — dual 5 V / 6 A banks, bank eFuses and 3.3 V buck" sheetIndex={2} />
  <schematicsheet name="hub"
    displayName="USB HUB — USB-C data-only upstream, ESD, USB2517I, straps, clock and bypass" sheetIndex={3} />
  <schematicsheet name="hub_straps"
    displayName="USB HUB CONFIGURATION — P1 swapped, P2-5 normal, P6-7 disabled" sheetIndex={4} />
  <schematicsheet name="management"
    displayName="MANAGEMENT — factory MCP2221A HID/I2C and MCP23017 command bank" sheetIndex={5} />
  <schematicsheet name="interlocks"
    displayName="INTERLOCKS — hub policy AND host command; data follows commanded power enable" sheetIndex={6} />
  <schematicsheet name="port_1" displayName="EXTERNAL PORT 1 — independent power/data disconnect" sheetIndex={7} />
  <schematicsheet name="port_2" displayName="EXTERNAL PORT 2 — independent power/data disconnect" sheetIndex={8} />
  <schematicsheet name="port_3" displayName="EXTERNAL PORT 3 — independent power/data disconnect" sheetIndex={9} />
  <schematicsheet name="port_4" displayName="EXTERNAL PORT 4 — independent power/data disconnect" sheetIndex={10} />
  <group name="pd_input_dual_5v_and_3v3" pcbX="-150mm" pcbY="100mm">
    <chip name="J_POWER" manufacturerPartNumber="TYPE-C-31-M-12"
      supplierPartNumbers={{ jlcpcb: ["C165948"] }} footprint={<UsbC16 />}
      {...schProps("J_POWER")}
      pinLabels={{ pin1:"GND_A1",pin2:"VBUS_A4",pin3:"CC1",pin4:"DP_A6",pin5:"DM_A7",pin6:"SBU1",pin7:"VBUS_A9",pin8:"GND_A12",
        pin9:"GND_B1",pin10:"VBUS_B4",pin11:"CC2",pin12:"DP_B6",pin13:"DM_B7",pin14:"SBU2",pin15:"VBUS_B9",pin16:"GND_B12",pin17:"SHIELD" }}
      connections={{ pin1:"net.GND",pin2:"net.VBUS_PD_RAW",pin3:"net.PD_CC1",pin7:"net.VBUS_PD_RAW",pin8:"net.GND",
        pin9:"net.GND",pin10:"net.VBUS_PD_RAW",pin11:"net.PD_CC2",pin15:"net.VBUS_PD_RAW",pin16:"net.GND",pin17:"net.GND" }} />
    <fuse name="F_PD" currentRating="3A" manufacturerPartNumber="0466003.NRHF"
      supplierPartNumbers={{ jlcpcb: ["C14165"] }} footprint={<Smd1206 />}
      {...schProps("F_PD")} connections={{ pin1:"net.VBUS_PD_RAW",pin2:"net.VBUS_PD" }} />
    <chip name="D_PD_TVS" manufacturerPartNumber="TVS2200DRVR" supplierPartNumbers={{ jlcpcb: ["C523793"] }}
      footprint={<Tvs2200Fp />} {...schProps("D_PD_TVS")}
      pinLabels={{ pin1:"GND1",pin2:"GND2",pin3:"GND3",pin4:"IN1",pin5:"IN2",pin6:"IN3",pin7:"EP_GND" }}
      connections={{ pin1:"net.GND",pin2:"net.GND",pin3:"net.GND",pin4:"net.VBUS_PD",pin5:"net.VBUS_PD",pin6:"net.VBUS_PD",pin7:"net.GND" }} />
    <chip name="U_PD" manufacturerPartNumber="CH224K" supplierPartNumbers={{ jlcpcb: ["C970725"] }}
      footprint={<Ch224kFp />} {...schProps("U_PD")}
      pinLabels={{ pin1:"VDD",pin2:"CFG2",pin3:"CFG3",pin4:"DP",pin5:"DM",pin6:"CC2",pin7:"CC1",pin8:"VBUS",pin9:"CFG1",pin10:"PG",pin11:"EP_GND" }}
      connections={{ pin1:"net.PD_VDD",pin2:"net.PD_VDD",pin3:"net.PD_VDD",pin4:"net.PD_PROTO",pin5:"net.PD_PROTO",pin6:"net.PD_CC2",pin7:"net.PD_CC1",
        pin8:"net.PD_VBUS_SENSE",pin9:"net.GND",pin11:"net.GND" }} />
    <R name="R_PD_VDD" value="1k" a="VBUS_PD" b="PD_VDD" jlc="C52444" fp="1210" />
    <C name="C_PD_VDD" value="1uF" a="PD_VDD" b="GND" jlc="C52923" />
    <R name="R_PD_VBUS" value="10k" a="VBUS_PD" b="PD_VBUS_SENSE" jlc="C25744" />

    {/* TPS16630 rejects default/15 V contracts and accepts only the 20 V PDO.
        The 60 V front end and TVS2200 protect every downstream 28 V converter. */}
    <chip name="U_PD_IN" manufacturerPartNumber="TPS16630PWPR" supplierPartNumbers={{ jlcpcb: ["C1849461"] }}
      footprint={<Tps16630Fp />} {...schProps("U_PD_IN")}
      pinLabels={{ pin1:"IN1",pin2:"IN2",pin3:"NC1",pin4:"NC2",pin5:"NC3",pin6:"P_IN",pin7:"UVLO",pin8:"OVP",pin9:"GND",pin10:"DVDT",pin11:"ILIM",pin12:"MODE",pin13:"SHDN",pin14:"IMON",pin15:"FLT",pin16:"PGOOD",pin17:"NC4",pin18:"OUT1",pin19:"OUT2",pin20:"NC5",pin21:"EP" }}
      connections={{ pin1:"net.VBUS_PD",pin2:"net.VBUS_PD",pin6:"net.VBUS_PD",pin7:"net.PD_IN_UV",pin8:"net.PD_IN_OV",pin9:"net.GND",pin10:"net.PD_IN_DVDT",pin11:"net.PD_IN_ILIM",pin12:"net.GND",pin13:"net.VBUS_PD",pin18:"net.VBUS_PD_PROTECTED",pin19:"net.VBUS_PD_PROTECTED",pin21:"net.GND" }} />
    <R name="R_PD_UV_TOP_HI" value="910k" a="VBUS_PD" b="PD_UV_TOP_MID" jlc="C25800" />
    <R name="R_PD_UV_TOP_LO" value="22k" a="PD_UV_TOP_MID" b="PD_IN_UV" jlc="C25768" />
    <R name="R_PD_UV_MID" value="20k" a="PD_IN_UV" b="PD_IN_OV" jlc="C25765" />
    <R name="R_PD_OV_BOT" value="51k" a="PD_IN_OV" b="GND" jlc="C107229" />
    <R name="R_PD_IN_ILIM" value="5.90k" a="PD_IN_ILIM" b="GND" jlc="C23071" fp="0603" />
    <C name="C_PD_IN_DVDT" value="3.3nF" a="PD_IN_DVDT" b="GND" jlc="C107048" fp="0603" />
    <capacitor name="C_PD_IN1" capacitance="10uF" footprint={<Smd1206 />}
      {...schProps("C_PD_IN1")} supplierPartNumbers={{ jlcpcb: ["C5449000"] }}
      connections={{ pin1: "net.VBUS_PD_PROTECTED", pin2: "net.GND" }} />
    <capacitor name="C_PD_IN2" capacitance="10uF" footprint={<Smd1206 />}
      {...schProps("C_PD_IN2")} supplierPartNumbers={{ jlcpcb: ["C5449000"] }}
      connections={{ pin1: "net.VBUS_PD_PROTECTED", pin2: "net.GND" }} />
    <C name="C_PD_IN_HF" value="1uF" a="VBUS_PD" b="GND" jlc="C5360793" fp="0603" />
    {(["A", "B"] as const).map((bank) => {
      const raw = `P5V_BANK_${bank}`, protectedNet = `P5V_${bank}_PROTECTED`
      return <group key={`bank_${bank}`} name={`bank_${bank}`}>
        <chip name={`U_BUCK_${bank}`} manufacturerPartNumber="TPS56637RPAR" supplierPartNumbers={{ jlcpcb: ["C841386"] }}
          footprint={<TwoSided pins={10} pitch={0.5} span={3.8} />} {...schProps(`U_BUCK_${bank}`)}
          pinLabels={{ pin1:"EN",pin2:"FB",pin3:"AGND",pin4:"PG",pin5:"NC",pin6:"SW",pin7:"BOOT",pin8:"VIN",pin9:"PGND",pin10:"MODE" }}
          connections={{ pin1:`net.BUCK_${bank}_EN`,pin2:`net.FB_${bank}`,pin3:"net.GND",pin6:`net.SW_${bank}`,pin7:`net.BOOT_${bank}`,pin8:"net.VBUS_PD_PROTECTED",pin9:"net.GND",pin10:"net.GND" }} />
        <R name={`R_BUCK_${bank}_EN_TOP`} value="200k" a="VBUS_PD_PROTECTED" b={`BUCK_${bank}_EN`} jlc="C25764" />
        <R name={`R_BUCK_${bank}_EN_BOT`} value="27.4k" a={`BUCK_${bank}_EN`} b="GND" jlc="C26971" />
        <capacitor name={`C_BUCK_${bank}_IN1`} capacitance="10uF" footprint={<Smd1206 />} supplierPartNumbers={{ jlcpcb: ["C5449000"] }} {...schProps(`C_BUCK_${bank}_IN1`)} connections={{ pin1:"net.VBUS_PD_PROTECTED",pin2:"net.GND" }} />
        <capacitor name={`C_BUCK_${bank}_IN2`} capacitance="10uF" footprint={<Smd1206 />} supplierPartNumbers={{ jlcpcb: ["C5449000"] }} {...schProps(`C_BUCK_${bank}_IN2`)} connections={{ pin1:"net.VBUS_PD_PROTECTED",pin2:"net.GND" }} />
        <C name={`C_BST_${bank}`} value="100nF" a={`BOOT_${bank}`} b={`SW_${bank}`} jlc="C60474" />
        <inductor name={`L_BUCK_${bank}`} inductance="3.3uH" manufacturerPartNumber="MWSA0804S-3R3MT" supplierPartNumbers={{ jlcpcb: ["C17700166"] }} footprint={<Mwsa0804 />} {...schProps(`L_BUCK_${bank}`)} connections={{ pin1:`net.SW_${bank}`,pin2:`net.${raw}` }} />
        <R name={`R_FB_${bank}_TOP`} value="75k" a={raw} b={`FB_${bank}`} jlc="C319478" />
        <R name={`R_FB_${bank}_BOT`} value="10k" a={`FB_${bank}`} b="GND" jlc="C190095" />
        <C name={`C_BUCK_${bank}_OUT1`} value="22uF" a={raw} b="GND" jlc="C21397" fp="1210" />
        <C name={`C_BUCK_${bank}_OUT2`} value="22uF" a={raw} b="GND" jlc="C21397" fp="1210" />
        <chip name={`U_AGG_${bank}`} manufacturerPartNumber="TPS259827ONRGET" supplierPartNumbers={{ jlcpcb: ["C2155765"] }} footprint={<Tps25980Fp />} {...schProps(`U_AGG_${bank}`)}
          pinLabels={{ pin1:"IN1",pin2:"IN2",pin3:"IN3",pin4:"GND1",pin5:"GND2",pin6:"EN_UVLO",pin7:"ITIMER",pin8:"ILIM",pin9:"IMON",pin10:"RETRY_DLY",pin11:"NRETRY",pin12:"LDSTRT",pin13:"PG",pin14:"GND3",pin15:"DVDT",pin16:"IN4",pin17:"OUT1",pin18:"OUT2",pin19:"OUT3",pin20:"OUT4",pin21:"OUT5",pin22:"OUT6",pin23:"OUT7",pin24:"OUT8",pin25:"IN_POWERPAD",pin26:"GND_POWERPAD" }}
          connections={{ pin1:`net.${raw}`,pin2:`net.${raw}`,pin3:`net.${raw}`,pin4:"net.GND",pin5:"net.GND",pin6:`net.${raw}`,pin7:`net.AGG_${bank}_TIMER`,pin8:`net.AGG_${bank}_ILIM`,pin10:"net.GND",pin11:"net.GND",pin12:"net.GND",pin14:"net.GND",pin15:`net.AGG_${bank}_DVDT`,pin16:`net.${raw}`,pin17:`net.${protectedNet}`,pin18:`net.${protectedNet}`,pin19:`net.${protectedNet}`,pin20:`net.${protectedNet}`,pin21:`net.${protectedNet}`,pin22:`net.${protectedNet}`,pin23:`net.${protectedNet}`,pin24:`net.${protectedNet}`,pin25:`net.${raw}`,pin26:"net.GND" }} />
        <C name={`C_AGG_${bank}_IN`} value="100nF" a={raw} b="GND" jlc="C60474" />
        <R name={`R_AGG_${bank}_ILIM`} value="300" a={`AGG_${bank}_ILIM`} b="GND" jlc="C23025" fp="0603" />
        <C name={`C_AGG_${bank}_TIMER`} value="6.8nF" a={`AGG_${bank}_TIMER`} b="GND" jlc="C162241" fp="0603" />
        <C name={`C_AGG_${bank}_DVDT`} value="3.3nF" a={`AGG_${bank}_DVDT`} b="GND" jlc="C107048" fp="0603" />
        <C name={`C_BANK_${bank}_HF`} value="100nF" a={protectedNet} b="GND" jlc="C60474" />
        <C name={`C_BANK_${bank}_BULK`} value="22uF" a={protectedNet} b="GND" jlc="C21397" fp="1210" />
        <capacitor name={`C_BANK_${bank}_POLY`} capacitance="180uF" polarized manufacturerPartNumber="16SVPF180M" supplierPartNumbers={{ jlcpcb: ["C136277"] }} {...schProps(`C_BANK_${bank}_POLY`)} footprint={<Polymer63 />} connections={{ pin1:`net.${protectedNet}`,pin2:"net.GND" }} />
      </group>
    })}

    <chip name="U_MAIN" manufacturerPartNumber="AP63203QWU-7" supplierPartNumbers={{ jlcpcb: ["C5248536"] }} footprint="sot23_6"
      {...schProps("U_MAIN")}
      pinLabels={{ pin1: "FB", pin2: "EN", pin3: "VIN", pin4: "GND", pin5: "SW", pin6: "BST" }}
      connections={{ pin1: "net.N3V3_MAIN", pin2: "net.VBUS_PD_PROTECTED", pin3: "net.VBUS_PD_PROTECTED", pin4: "net.GND", pin5: "net.SW_3V3", pin6: "net.BST_3V3" }} />
    <inductor name="L_MAIN" inductance="3.3uH" supplierPartNumbers={{ jlcpcb: ["C15269"] }}
      {...schProps("L_MAIN")}
      connections={{ pin1: "net.SW_3V3", pin2: "net.N3V3_MAIN" }} footprint={<SunlordSwpa4030 />} />
    <capacitor name="C_MAIN_IN" capacitance="10uF" footprint={<Smd1206 />} supplierPartNumbers={{ jlcpcb: ["C5449000"] }} {...schProps("C_MAIN_IN")} connections={{ pin1:"net.VBUS_PD_PROTECTED",pin2:"net.GND" }} />
    <C name="C_BST" value="100nF" a="BST_3V3" b="SW_3V3" jlc="C392963" />
    <C name="C_MAIN_OUT1" value="22uF" a="N3V3_MAIN" b="GND" jlc="C21397" fp="1210" />
    <C name="C_MAIN_OUT2" value="22uF" a="N3V3_MAIN" b="GND" jlc="C21397" fp="1210" />
  </group>

  <group name="upstream_and_hub" pcbX="0mm" pcbY="100mm">
    <chip name="J_DATA" manufacturerPartNumber="TYPE-C-31-M-12"
      supplierPartNumbers={{ jlcpcb: ["C165948"] }} footprint={<UsbC16 />}
      {...schProps("J_DATA")}
      pinLabels={{ pin1:"GND_A1",pin2:"VBUS_A4",pin3:"CC1",pin4:"DP_A6",pin5:"DM_A7",pin6:"SBU1",pin7:"VBUS_A9",pin8:"GND_A12",
        pin9:"GND_B1",pin10:"VBUS_B4",pin11:"CC2",pin12:"DP_B6",pin13:"DM_B7",pin14:"SBU2",pin15:"VBUS_B9",pin16:"GND_B12",pin17:"SHIELD" }}
      connections={{ pin1:"net.GND",pin2:"net.USB_UP_VBUS",pin3:"net.DATA_CC1",pin4:"net.UP_HUB_P",pin5:"net.UP_HUB_N",
        pin7:"net.USB_UP_VBUS",pin8:"net.GND",pin9:"net.GND",pin10:"net.USB_UP_VBUS",pin11:"net.DATA_CC2",
        pin12:"net.UP_HUB_P",pin13:"net.UP_HUB_N",pin15:"net.USB_UP_VBUS",pin16:"net.GND",pin17:"net.GND" }} />
    <R name="R_CC1" value="5.1k" a="DATA_CC1" b="GND" jlc="C25905" />
    <R name="R_CC2" value="5.1k" a="DATA_CC2" b="GND" jlc="C25905" />
    <chip name="U_ESD_UP" manufacturerPartNumber="PESD2USB5UX-TR" supplierPartNumbers={{ jlcpcb: ["C3709087"] }}
      footprint="sot23"
      {...schProps("U_ESD_UP")}
      pinLabels={{ pin1: "IO1", pin2: "IO2", pin3: "GND" }}
      connections={{ pin1: "net.UP_HUB_N", pin2: "net.UP_HUB_P", pin3: "net.GND" }} />

    <chip name="U_HUB" supplierPartNumbers={{ jlcpcb: ["C478081"] }} footprint={<Qfn64Ep />}
      schWidth="4mm" schHeight="8mm"
      {...schProps("U_HUB")}
      pinLabels={{ pin1:"DN1_DM",pin2:"DN1_DP",pin3:"DN2_DM",pin4:"DN2_DP",pin5:"VDDA33_1",pin6:"DN3_DM",pin7:"DN3_DP",pin8:"DN4_DM",pin9:"DN4_DP",pin10:"VDDA33_2",pin11:"DN5_DM",pin12:"DN5_DP",pin13:"CFG_SEL2",pin14:"LED_B7",pin15:"PRT_SWP7",pin16:"LED_B6",pin17:"PRT_SWP6",pin18:"LED_B5",pin19:"TEST",pin20:"PRTPWR4",pin21:"OCS4_N",pin22:"OCS3_N",pin23:"PRTPWR3",pin24:"VDD33CR",pin25:"VDD18",pin26:"PRTPWR2",pin27:"OCS2_N",pin28:"OCS1_N",pin29:"PRTPWR1",pin30:"PRTPWR5",pin31:"PRT_SWP5",pin32:"LED_B4",pin33:"PRT_SWP4",pin34:"GANG_EN",pin35:"OCS5_N",pin36:"PRTPWR7",pin37:"OCS7_N",pin38:"OCS6_N",pin39:"PRTPWR6",pin40:"NON_REM1",pin41:"CFG_SEL0",pin42:"CFG_SEL1",pin43:"RESET_N",pin44:"VBUS_DET",pin45:"NON_REM0",pin46:"VDD33",pin47:"PRT_SWP3",pin48:"BOOST1",pin49:"PRT_SWP2",pin50:"BOOST0",pin51:"PRT_SWP1",pin52:"VDDA33_3",pin53:"DN6_DM",pin54:"DN6_DP",pin55:"DN7_DM",pin56:"DN7_DP",pin57:"VDDA33_4",pin58:"UP_DM",pin59:"UP_DP",pin60:"XTAL2",pin61:"XTAL1",pin62:"VDD18PLL",pin63:"RBIAS",pin64:"VDD33PLL",pin65:"EP_VSS" }}
      connections={{
        // PRT_SWP1 is deliberately high: logical D+ occupies physical DN1_DM
        // and logical D- occupies physical DN1_DP, removing a geometric pair
        // crossover to the onboard controller. External ports 2..5 retain
        // normal physical polarity and keep their PRT_SWP straps low.
        pin1:"net.MGMT_P",pin2:"net.MGMT_N",pin3:"net.P1_HUB_N",pin4:"net.P1_HUB_P",pin5:"net.N3V3_MAIN",pin6:"net.P2_HUB_N",pin7:"net.P2_HUB_P",pin8:"net.P3_HUB_N",pin9:"net.P3_HUB_P",pin10:"net.N3V3_MAIN",pin11:"net.P4_HUB_N",pin12:"net.P4_HUB_P",pin13:"net.HUB_CFG2",pin15:"net.HUB_SWAP7",pin17:"net.HUB_SWAP6",pin20:"net.HUB_PRTPWR4",pin21:"net.HUB_OCS4_N",pin22:"net.HUB_OCS3_N",pin23:"net.HUB_PRTPWR3",pin24:"net.N3V3_MAIN",pin25:"net.HUB_VDD18",pin26:"net.HUB_PRTPWR2",pin27:"net.HUB_OCS2_N",pin28:"net.HUB_OCS1_N",pin29:"net.HUB_PRTPWR1",pin30:"net.HUB_PRTPWR5",pin31:"net.HUB_SWAP5",pin33:"net.HUB_SWAP4",pin34:"net.HUB_GANG",pin35:"net.HUB_OCS5_N",pin40:"net.HUB_NONREM1",pin41:"net.HUB_CFG0",pin42:"net.HUB_CFG1",pin43:"net.HUB_RESET_N",pin44:"net.HUB_VBUS_SENSE",pin45:"net.HUB_NONREM0",pin46:"net.N3V3_MAIN",pin47:"net.HUB_SWAP3",pin48:"net.HUB_BOOST1",pin49:"net.HUB_SWAP2",pin50:"net.HUB_BOOST0",pin51:"net.HUB_SWAP1",pin52:"net.N3V3_MAIN",pin53:"net.HUB_DIS6_N",pin54:"net.HUB_DIS6_P",pin55:"net.HUB_DIS7_N",pin56:"net.HUB_DIS7_P",pin57:"net.N3V3_MAIN",pin58:"net.UP_HUB_N",pin59:"net.UP_HUB_P",pin60:"net.XTAL2",pin61:"net.XTAL1",pin62:"net.HUB_VDD18PLL",pin63:"net.RBIAS",pin64:"net.N3V3_MAIN",pin65:"net.GND"
      }} />
    <chip name="Y_HUB" manufacturerPartNumber="X322524MOB4SI" supplierPartNumbers={{ jlcpcb: ["C70590"] }} footprint={<TwoSided pins={4} pitch={1.6} span={3.2} />}
      {...schProps("Y_HUB")}
      pinLabels={{ pin1:"X1",pin2:"GND1",pin3:"X2",pin4:"GND2" }} connections={{ pin1:"net.XTAL1",pin2:"net.GND",pin3:"net.XTAL2",pin4:"net.GND" }} />
    <R name="R_XTAL" value="1M" a="XTAL1" b="XTAL2" jlc="C138033" />
    <R name="R_RBIAS" value="12k" a="RBIAS" b="GND" jlc="C114760" />
    <C name="C_XTAL1" value="18pF" a="XTAL1" b="GND" jlc="C1549" />
    <C name="C_XTAL2" value="18pF" a="XTAL2" b="GND" jlc="C1549" />
    {[1,2,3,4].map(n => <C key={`ha${n}`} name={`C_HUB_A${n}`} value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />)}
    <C name="C_HUB_A_BULK" value="1uF" a="N3V3_MAIN" b="GND" jlc="C326568" />
    <C name="C_HUB_CR_HF" value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />
    <C name="C_HUB_CR_BULK" value="1uF" a="N3V3_MAIN" b="GND" jlc="C326568" />
    <C name="C_HUB_DD" value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />
    <C name="C_HUB_PLL" value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />
    <C name="C_HUB_18" value="1uF" a="HUB_VDD18" b="GND" jlc="C326568" />
    <C name="C_HUB_18PLL" value="1uF" a="HUB_VDD18PLL" b="GND" jlc="C326568" />
    <R name="R_HUB_RESET" value="10k" a="N3V3_MAIN" b="HUB_RESET_N" jlc="C843837" />
    <C name="C_HUB_RESET" value="1uF" a="HUB_RESET_N" b="GND" jlc="C326568" />
    <R name="R_VBUS_TOP" value="47k" a="USB_UP_VBUS" b="HUB_VBUS_SENSE" jlc="C25792" />
    <R name="R_VBUS_BOT" value="100k" a="HUB_VBUS_SENSE" b="GND" jlc="C25741" />
    {[0,1,2].map(n => <R key={`cfg${n}`} name={`R_CFG${n}`} value="10k" a={`HUB_CFG${n}`} b="GND" jlc="C843837" />)}
    <R name="R_NONREM1" value="10k" a="HUB_NONREM1" b="GND" jlc="C843837" />
    <R name="R_NONREM0" value="10k" a="N3V3_MAIN" b="HUB_NONREM0" jlc="C843837" />
    <R name="R_SWAP1" value="100k" a="HUB_SWAP1" b="N3V3_MAIN" jlc="C25741" />
    {[2,3,4,5,6,7].map(n => <R key={`sw${n}`} name={`R_SWAP${n}`} value="100k" a={`HUB_SWAP${n}`} b="GND" jlc="C25741" />)}
    <R name="R_GANG" value="10k" a="HUB_GANG" b="GND" jlc="C843837" />
    <R name="R_BOOST0" value="10k" a="HUB_BOOST0" b="GND" jlc="C843837" />
    <R name="R_BOOST1" value="10k" a="HUB_BOOST1" b="GND" jlc="C843837" />
    <R name="R_DIS6N" value="10k" a="N3V3_MAIN" b="HUB_DIS6_N" jlc="C843837" />
    <R name="R_DIS6P" value="10k" a="N3V3_MAIN" b="HUB_DIS6_P" jlc="C843837" />
    <R name="R_DIS7N" value="10k" a="N3V3_MAIN" b="HUB_DIS7_N" jlc="C843837" />
    <R name="R_DIS7P" value="10k" a="N3V3_MAIN" b="HUB_DIS7_P" jlc="C843837" />
  </group>

  <group name="management_device" pcbX="150mm" pcbY="100mm">
    <Tps2557 name="U_PWR_CTRL" input="P5V_A_PROTECTED" en="HUB_PRTPWR1" out="VBUS_CTRL" fault="HUB_OCS1_N" ilim="ILIM_CTRL"
      cin="C_PWR_CTRL_IN" coutHf="C_PWR_CTRL_OUT_HF" coutBulk="C_PWR_CTRL_OUT" studyX={-12} />
    <chip name="U_CTRL" manufacturerPartNumber="MCP2221A-I/ST" supplierPartNumbers={{ jlcpcb: ["C130462"] }} footprint={<TwoSided pins={14} pitch={0.65} span={6.4} />}
      {...schProps("U_CTRL")}
      pinLabels={{ pin1:"VDD",pin2:"GP0",pin3:"GP1",pin4:"RST",pin5:"URX",pin6:"UTX",pin7:"GP2",pin8:"GP3",pin9:"SDA",pin10:"SCL",pin11:"VUSB",pin12:"D_MINUS",pin13:"D_PLUS",pin14:"VSS" }}
      connections={{ pin1:"net.VBUS_CTRL",pin4:"net.CTRL_RESET_N",pin9:"net.I2C_SDA",pin10:"net.I2C_SCL",pin11:"net.CTRL_VUSB_3V3",pin12:"net.MGMT_N",pin13:"net.MGMT_P",pin14:"net.GND" }} />
    <C name="C_CTRL_VDD" value="100nF" a="VBUS_CTRL" b="GND" jlc="C392963" />
    <C name="C_CTRL_VUSB" value="330nF" a="CTRL_VUSB_3V3" b="GND" jlc="C19271634" />
    <R name="R_CTRL_RESET" value="10k" a="VBUS_CTRL" b="CTRL_RESET_N" jlc="C843837" />
    <R name="R_I2C_SCL" value="4.7k" a="VBUS_CTRL" b="I2C_SCL" jlc="C482193" />
    <R name="R_I2C_SDA" value="4.7k" a="VBUS_CTRL" b="I2C_SDA" jlc="C482193" />

    <chip name="U_EXP" supplierPartNumbers={{ jlcpcb: ["C558584"] }} footprint={<TwoSided pins={28} pitch={0.65} span={7.2} />}
      {...schProps("U_EXP")}
      pinLabels={{ pin1:"GPB0",pin2:"GPB1",pin3:"GPB2",pin4:"GPB3",pin5:"GPB4",pin6:"GPB5",pin7:"GPB6",pin8:"GPB7",pin9:"VDD",pin10:"VSS",pin11:"NC1",pin12:"SCL",pin13:"SDA",pin14:"NC2",pin15:"A0",pin16:"A1",pin17:"A2",pin18:"RESET_N",pin19:"INTB",pin20:"INTA",pin21:"GPA0",pin22:"GPA1",pin23:"GPA2",pin24:"GPA3",pin25:"GPA4",pin26:"GPA5",pin27:"GPA6",pin28:"GPA7" }}
      connections={{ pin9:"net.VBUS_CTRL",pin10:"net.GND",pin12:"net.I2C_SCL",pin13:"net.I2C_SDA",pin15:"net.GND",pin16:"net.GND",pin17:"net.GND",pin18:"net.EXP_RESET_N",pin21:"net.PWR_CMD1",pin22:"net.PWR_CMD2",pin23:"net.PWR_CMD3",pin24:"net.PWR_CMD4",pin25:"net.DATA_CMD1",pin26:"net.DATA_CMD2",pin27:"net.DATA_CMD3",pin28:"net.DATA_CMD4" }} />
    <C name="C_EXP_VDD" value="100nF" a="VBUS_CTRL" b="GND" jlc="C392963" studyX={12} studyY={0} />
    <R name="R_EXP_RESET" value="10k" a="VBUS_CTRL" b="EXP_RESET_N" jlc="C843837" />
    {[1,2,3,4].map(n => <R key={`pc${n}`} name={`R_PWR_CMD${n}`} value="10k" a={`PWR_CMD${n}`} b="GND" jlc="C843837" />)}
    {[1,2,3,4].map(n => <R key={`dc${n}`} name={`R_DATA_CMD${n}`} value="10k" a={`DATA_CMD${n}`} b="GND" jlc="C843837" />)}
  </group>

  <group name="hardware_interlocks" pcbX="150mm" pcbY="0mm">
    <chip name="U_AND_PWR" manufacturerPartNumber="74LVC08APW,118"
      supplierPartNumbers={{ jlcpcb: ["C6053"] }} footprint={<TwoSided pins={14} />}
      {...schProps("U_AND_PWR")}
      pinLabels={{ pin1:"1A",pin2:"1B",pin3:"1Y",pin4:"2A",pin5:"2B",pin6:"2Y",pin7:"GND",pin8:"3Y",pin9:"3A",pin10:"3B",pin11:"4Y",pin12:"4A",pin13:"4B",pin14:"VCC" }}
      connections={{ pin1:"net.HUB_PRTPWR2",pin2:"net.PWR_CMD1",pin3:"net.PWR_EN1",pin4:"net.HUB_PRTPWR3",pin5:"net.PWR_CMD2",pin6:"net.PWR_EN2",pin7:"net.GND",pin8:"net.PWR_EN3",pin9:"net.HUB_PRTPWR4",pin10:"net.PWR_CMD3",pin11:"net.PWR_EN4",pin12:"net.HUB_PRTPWR5",pin13:"net.PWR_CMD4",pin14:"net.N3V3_MAIN" }} />
    <C name="C_AND_PWR" value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />
    <chip name="U_AND_DATA" manufacturerPartNumber="74LVC08APW,118"
      supplierPartNumbers={{ jlcpcb: ["C6053"] }} footprint={<TwoSided pins={14} />}
      {...schProps("U_AND_DATA")}
      pinLabels={{ pin1:"1A",pin2:"1B",pin3:"1Y",pin4:"2A",pin5:"2B",pin6:"2Y",pin7:"GND",pin8:"3Y",pin9:"3A",pin10:"3B",pin11:"4Y",pin12:"4A",pin13:"4B",pin14:"VCC" }}
      connections={{ pin1:"net.PWR_EN1",pin2:"net.DATA_CMD1",pin3:"net.DATA_OK1",pin4:"net.PWR_EN2",pin5:"net.DATA_CMD2",pin6:"net.DATA_OK2",pin7:"net.GND",pin8:"net.DATA_OK3",pin9:"net.PWR_EN3",pin10:"net.DATA_CMD3",pin11:"net.DATA_OK4",pin12:"net.PWR_EN4",pin13:"net.DATA_CMD4",pin14:"net.N3V3_MAIN" }} />
    <C name="C_AND_DATA" value="100nF" a="N3V3_MAIN" b="GND" jlc="C392963" />
  </group>

  {/* Human-readback notes distinguish deliberate no-connects from omissions.
      These are presentation-only and do not create nets or copper. */}
  <group name="hub_intentional_nc_note" schSheetName="hub">
    <schematictext schX="0mm" schY="-13mm" anchor="center" fontSize={0.65}
      text="INTENTIONAL NC: U_HUB LED/TEST and disabled-port 6/7 PWR/OCS pins." />
  </group>
  <group name="management_intentional_nc_note" schSheetName="management">
    <schematictext schX="0mm" schY="-14mm" anchor="center" fontSize={0.65}
      text="INTENTIONAL NC: unused U_CTRL GPIO/UART; U_EXP GPB/INT/NC pins." />
  </group>

  <ExternalPort p={1} hubP="P1_HUB_P" hubN="P1_HUB_N" prtPwr="HUB_PRTPWR2" ocs="HUB_OCS2_N" powerNet="P5V_A_PROTECTED" />
  <ExternalPort p={2} hubP="P2_HUB_P" hubN="P2_HUB_N" prtPwr="HUB_PRTPWR3" ocs="HUB_OCS3_N" powerNet="P5V_A_PROTECTED" />
  <ExternalPort p={3} hubP="P3_HUB_P" hubN="P3_HUB_N" prtPwr="HUB_PRTPWR4" ocs="HUB_OCS4_N" powerNet="P5V_B_PROTECTED" />
  <ExternalPort p={4} hubP="P4_HUB_P" hubN="P4_HUB_N" prtPwr="HUB_PRTPWR5" ocs="HUB_OCS5_N" powerNet="P5V_B_PROTECTED" />

  {/* Presentation-only boundary labels for parallel power lands. Without an
      explicit label, circuit-to-svg joins same-net pins into an anonymous loop,
      which is electrically correct but not reviewable by a human. These labels
      add no new source trace or copper; every selected pin already owns the net. */}
  <group name="control_power_input_label" schSheetName="management">
    <netlabel net="P5V_A_PROTECTED" connectsTo={sel.U_PWR_CTRL.pin2}
      schX="-10.0mm" schY="2.95mm" anchorSide="right" />
    <netlabel net="P5V_A_PROTECTED" connectsTo={sel.U_PWR_CTRL.pin3}
      schX="-10.0mm" schY="2.75mm" anchorSide="right" />
    <netlabel net="GND" connectsTo={sel.U_PWR_CTRL.pin1}
      schX="-8.5mm" schY="3.15mm" anchorSide="right" />
  </group>
  <group name="control_power_output_label" schSheetName="management">
    <netlabel net="VBUS_CTRL" connectsTo={sel.U_PWR_CTRL.pin7}
      schX="-2.0mm" schY="2.95mm" anchorSide="left" />
    <netlabel net="VBUS_CTRL" connectsTo={sel.U_PWR_CTRL.pin6}
      schX="-2.0mm" schY="2.75mm" anchorSide="left" />
    <netlabel net="GND" connectsTo={sel.U_PWR_CTRL.pin9}
      schX="-3.5mm" schY="3.15mm" anchorSide="left" />
  </group>
  {[1, 2, 3, 4].map((p) => <group key={`port_power_labels_${p}`}
      name={`port_power_labels_${p}`} schSheetName={`port_${p}`}>
    <netlabel net={p <= 2 ? "P5V_A_PROTECTED" : "P5V_B_PROTECTED"} connectsTo={sel[`U_PWR${p}`].pin5}
      schX="-5.2mm" schY="-3.2mm" anchorSide="right" />
    <netlabel net={`VBUS${p}_SW`} connectsTo={sel[`U_PWR${p}`].pin6}
      schX="0.7mm" schY="-3.2mm" anchorSide="left" />
  </group>)}
</board>

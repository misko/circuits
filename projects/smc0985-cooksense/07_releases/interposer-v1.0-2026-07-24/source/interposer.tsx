// ============================================================================
// interposer — SMC0985KS Board C: passive keypad interposer (ADR-0007/0008/0009)
//
// OEM membrane tail --> [J_MEMBRANE 10FDZ-BT ZIF] ==10 straight-through nets==>
// [J_CN1_JUMPER 10FDZ-BT ZIF] --> flex jumper (separate part, Task #13) --> OEM CN1.
// Every line also breaks out to J_KEY_MATRIX (JST GH SM10B-GHS-TB), pin map
// IDENTICAL to the sealed cooksense main board's J_KEY_MATRIX (read back
// read-only 2026-07-24: pins 1..10 = KP_U1..KP_U6,KP_D1..KP_D4; MP tabs float)
// so one 1:1 GHR-10V-S 10-way ribbon joins the boards.
//
// PASSIVE + ISOLATED (BRIEF §5): 10 floating nets, NO GND, NO power, NO
// active parts, no bond to logic ground or chassis. D4 (T3): passes through
// unchanged with labeled TPs; lockout is downstream (firmware/main board).
//
// Test points: one per line per side (TP_M_* by J_MEMBRANE, TP_C_* by
// J_CN1_JUMPER) — the G6 continuity-map probe field, labeled on silk.
//
// AUTHORING IDIOM (03_tscircuit/contracts.md): every pin bound to an explicit
// net.<NAME>; specialty parts carry supplierPartNumbers so the converter
// resolves the KiCad FPID from 02_parts/<MPN>/part.yaml ("10FDZ-BT" folder /
// C2683602). footprint tokens are for tscircuit pad COUNT only.
// ============================================================================

const LINES = ["U1", "U2", "U3", "U4", "U5", "U6", "D1", "D2", "D3", "D4"]
const KP = (l: string) => `net.KP_${l}`

export default () => (
  <board width="48mm" height="42mm">
    {/* J_MEMBRANE — 10FDZ-BT ZIF, receives the ORIGINAL OEM membrane tail */}
    <chip name="J_MEMBRANE" footprint="pinrow10" supplierPartNumbers={{ jlcpcb: ["10FDZ-BT"] }}
      connections={{
        pin1: KP("U1"), pin2: KP("U2"), pin3: KP("U3"), pin4: KP("U4"), pin5: KP("U5"),
        pin6: KP("U6"), pin7: KP("D1"), pin8: KP("D2"), pin9: KP("D3"), pin10: KP("D4"),
      }} />

    {/* J_CN1_JUMPER — identical 10FDZ-BT ZIF, receives the flex jumper to OEM CN1 */}
    <chip name="J_CN1_JUMPER" footprint="pinrow10" supplierPartNumbers={{ jlcpcb: ["10FDZ-BT"] }}
      connections={{
        pin1: KP("U1"), pin2: KP("U2"), pin3: KP("U3"), pin4: KP("U4"), pin5: KP("U5"),
        pin6: KP("U6"), pin7: KP("D1"), pin8: KP("D2"), pin9: KP("D3"), pin10: KP("D4"),
      }} />

    {/* J_KEY_MATRIX — keyed GH breakout to the main board (pin map == sealed cooksense) */}
    <chip name="J_KEY_MATRIX" footprint="pinrow10" supplierPartNumbers={{ jlcpcb: ["C2683602"] }}
      connections={{
        pin1: KP("U1"), pin2: KP("U2"), pin3: KP("U3"), pin4: KP("U4"), pin5: KP("U5"),
        pin6: KP("U6"), pin7: KP("D1"), pin8: KP("D2"), pin9: KP("D3"), pin10: KP("D4"),
      }} />

    {/* test points — membrane side (TP_M_*) and CN1-jumper side (TP_C_*), all 10 lines */}
    {LINES.map((l) => (
      <testpoint key={`TPM${l}`} name={`TP_M_${l}`} footprintVariant="pad" padShape="circle"
        padDiameter="1.5mm" connections={{ pin1: KP(l) }} />
    ))}
    {LINES.map((l) => (
      <testpoint key={`TPC${l}`} name={`TP_C_${l}`} footprintVariant="pad" padShape="circle"
        padDiameter="1.5mm" connections={{ pin1: KP(l) }} />
    ))}
  </board>
)

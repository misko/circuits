// ============================================================================
// pluto-cal-switch — 5-port SMA RF calibration adapter for an ADALM-PlutoPlus.
//
//   CTRL = 0 (power-on)  RX_ANT1 -> RX_PLUTO1 and RX_ANT2 -> RX_PLUTO2
//   CTRL = 1             TX_PLUTO -> pad -> resistive delta split -> pad -> BOTH
//                        RX_PLUTO ports, >=40 dB MINIMUM across 70 MHz - 6 GHz
//
// Authored in tscircuit (repo ADR-0001 / ADR-0002). Compiled by our converter
// (circuit_json_to_kicad_sch.py) into the authoritative KiCad schematic bridge,
// and driven through the SHARED GENERIC BACKEND — this board writes ZERO
// board-specific generation Python (ADR-0002 amendment 2026-07-23).
//
// AUTHORING IDIOM (03_tscircuit/contracts.md):
//   * every pin bound to an EXPLICIT net (connections={{ pin: "net.NAME" }}),
//     never a pairwise <trace> — parity by construction (canon S2);
//   * leading-digit rails carry an author-prefix N (N3V3 -> 3V3), and the one
//     name the convention cannot reach is in net_aliases.txt;
//   * every specialty part carries supplierPartNumbers so the converter
//     resolves its KiCad FPID from 02_parts/<MPN>/part.yaml;
//   * a pad simply LEFT OUT of `connections` resolves to net=None and the
//     converter emits a KiCad `no_connect` flag. Unused pins are NEVER shorted
//     onto a shared net.
//
// PIN MAPS ARE TAKEN VERBATIM FROM THE VERIFIED 02_parts/*/part.yaml. Do not
// re-derive them here; if one is wrong, the dossier is wrong.
//
// ---------------------------------------------------------------------------
// FOUR THINGS THIS BOARD'S OWN DOCS SAY WILL BE GOT WRONG, AND WHERE THEY LIVE
// ---------------------------------------------------------------------------
//  1. RF1 = ANTENNA, RF2 = LOOPBACK, on BOTH switches. The truth table is
//     CTRL=0 -> RFIN-RF1 (BGS12WN6 Table 12), so this wiring is what makes
//     power-on = ANTENNA mode fall out of the SILICON with zero logic
//     (ADR-0001). Swapping RF1/RF2 inverts the SAFE STATE, not the feature,
//     and the board still passes ERC, DRC, parity and every render.
//  2. THE COMPLETE PAD CHAIN IS UPSTREAM OF BOTH SWITCHES. TX_PLUTO touches
//     exactly one thing — PAD_A1's first chip — so no switch state and no
//     switch FAULT (including a die shorting RFin-RF1-RF2) can present raw TX
//     to a receiver (ADR-0016, DETAIL_DESIGN sec.7.2).
//  3. THE LOOPBACK PATH CARRIES NO DC BLOCKING CAPACITORS, DELIBERATELY. The
//     YAT pads DC-reference the whole internal RF node to ground through
//     ~70 ohm/port, which satisfies the switches' V_RFDC = 0 V rating by
//     construction. Blocks are fitted ONLY on the two user-facing ANTENNA
//     ports, where an unknown DC source can appear (ADR-0005).
//  4. LOOP_ARM1 / LOOP_ARM2 ARE A MIRROR-SYMMETRIC MATCHED PAIR whose delta is
//     a PUBLISHED RELEASE ARTIFACT (ADR-0011 / brief D4). They are authored
//     part-for-part identical, in the same cascade order, so that the only
//     difference between the two arms is geometry. RF_CTRL must never run
//     parallel to either arm (ARCHITECTURE sec.10.6) — a routing rule, carried
//     by the CTRL netclass.
//
// D7 IS STILL OPEN AND IS FIRMWARE-ONLY: which control surface wins when the
// header and USB disagree. Authored to the assumed resolution
// RF_CTRL = HEADER_level OR USB_bit plus a 10 s USB watchdog (ADR-0008). That
// consumes NO hardware — the header reaches an ADC pin and USB reaches the MCU;
// the OR happens in firmware. A different answer is a firmware one-liner.
// ============================================================================

const N = (s: string) => `net.${s}`

// build a chip `connections` object from a { padNumber: netName } map.
// pads absent from the map are left unbound -> no_connect (a sanctioned float).
const conn = (m: Record<number, string>) =>
  Object.fromEntries(Object.entries(m).map(([k, v]) => [`pin${k}`, N(v)]))

// Throwaway pad geometry for a <footprint> child: N numeric pads on a
// non-overlapping grid. ONLY the portHints (pad names) and the pad COUNT are
// load-bearing at the schematic gate — the real land pattern comes from the
// 02_parts FPID that supplierPartNumbers resolves. Every pad name on this
// board is numeric, so tsx_preflight (TSX-PRE) has nothing to map: there is no
// USB-C `A1..B12` or shield `SH` here, which is the class that gets a part
// DROPPED SILENTLY with ERC still reading 0.
const grid = (names: (string | number)[]) =>
  names.map((nm, i) => (
    <smtpad
      key={`p${nm}`}
      portHints={[String(nm)]}
      pcbX={`${(i % 16) * 0.8 - 6}mm`}
      pcbY={`${Math.floor(i / 16) * 0.8 - 4}mm`}
      width="0.4mm"
      height="0.4mm"
      shape="rect"
    />
  ))

const fp = (names: (string | number)[]) => <footprint>{grid(names)}</footprint>

// ---- LCSC codes, one place, all from 02_parts/<MPN>/part.yaml sourcing.lcsc --
const LCSC = {
  SMA:      "C504007",     // KH-SMA-KE-Z          vertical THT SMA JACK x5
  YAT10:    "C5839318",    // YAT-10A+             MCLP 2x2, DC-18 GHz  x4
  YAT2:     "C5205333",    // YAT-2A+              MCLP 2x2, DC-18 GHz  x5
  R499:     "C25120",      // 0402WGF499JTCE       49.9 ohm 1% 0402, JLC BASIC
  SPDT:     "C534203",     // BGS12WN6             PG-TSNP-6-10 SPDT
  DCBLK:    "C307441",     // CL05C102JB5NNNC      1 nF 50 V C0G  <- DIELECTRIC
  MCU:      "C2040",       // RP2040               QFN-56 0.4 mm
  FLASH:    "C82317",      // W25Q16JVSSIQ         SOIC-8 208-mil
  XTAL:     "C20625731",   // ABM8-272-T3          12 MHz CL10pF ESR<=50R
  XTALCAP:  "C86285",      // CL05C150JB5NNNC      15 pF 50 V C0G
  LDO:      "C82942",      // ME6211C33M5G-N       SOT-23-5 fixed 3.3 V
  USB:      "C319160",     // U254-051T-4BH83-S1S  micro-B, 2 THT legs
  USBESD:   "C7519",       // USBLC6-2SC6          SOT-23-6L
  HDRESD:   "C1972959",    // TPD2E2U06DRLR        SOT-553 2-ch bidirectional
  HDR:      "C2894927",    // PZ254-1-04-Z-8.5     1x4 2.54 mm THT header
  BOOTSW:   "C318884",     // TS-1187A-B-A-B       tact switch, JLC BASIC
  LED:      "C2286",       // KT-0603R             red 0603, JLC BASIC
  FERRITE:  "C3716677",    // BLM21SP601SN1D       0805 600R@100MHz 2.3 A
  PPTC:     "C2649901",    // MINISMDC050F-2       PPTC 0.5 A hold, series VBUS
} as const

// ---- GENERIC PASSIVES: PINNED, NOT LEFT TO THE PARTS ENGINE ----------------
// A bare <resistor resistance=.. footprint=..> lets tscircuit's parts engine
// choose the LCSC code, and THAT CHOICE IS A SNAPSHOT OF THE CATALOG ON THE DAY
// IT RAN. cooksense v1.5 (2026-07-27) had two auto-chosen codes go unbuyable —
// C25744 at stockCount 0 across 17 refs. Left unpinned on THIS board the engine
// chose C25890 for the 3.3 kohm divider leg, which read stockCount 31 on
// 2026-07-28: one board's margin over a 20-board build.
// So every passive code is pinned here, at source, where a rebuild cannot
// silently re-choose. Codes marked (ledger) are already catalog-verified in
// skills/jlcpcb-fab/references/lcsc_passives_ledger.yaml; the rest carry a
// 02_parts/<MPN>/part.yaml dossier. Either way `bom_source_check --circuit-only`
// can resolve the catalog value offline and compare it to the value prop below
// — that is leg C, and it is what caught R12/R30 three seals too late.
const P = {
  R1K:    "C11702",   // 0402WGF1001TCE   1k    1% 0402  (ledger)  stk 1.09 M
  R2K2:   "C25879",   // 0402WGF2201TCE   2.2k  1% 0402  (ledger)  stk 1.29 M
  R3K3:   "C137992",  // RC0402FR-073K3L  3.3k  1% 0402  (dossier) stk 674 k
  R10K:   "C60490",   // RC0402FR-0710KL  10k   1% 0402  (ledger)  stk 8.15 M
  R27:    "C138021",  // RC0402FR-0727RL  27    1% 0402  (dossier) stk 237 k
  R680:   "C137948",  // RC0402FR-07680RL 680   1% 0402  (ledger)  stk 578 k
  C100N:  "C1525",    // CL05B104KO5NNNC  100nF 16V X7R 0402 (ledger) stk 47.6 M
  C1N:    "C1523",    // 0402B102K500NT   1nF   50V X7R 0402 (ledger) stk 5.65 M
  C1U:    "C52923",   // CL05A105KA5NQNC  1uF   25V X5R 0402 (ledger) stk 14.4 M
  C4U7:   "C1779",    // CL21A475KAQNNNE  4.7uF 25V X5R 0805 (ledger) stk 2.98 M
} as const

// KH-SMA-KE-Z: centre hole = signal (pad 1), four corner posts = GND (2..5).
// The four posts are a MECHANICAL ground, not a shield: they sit at 5.08 mm =
// lambda_g/4.7 at 6 GHz, which is why ADR-0007 mandates a <=2.0 mm via fence
// beside every launch. That rule is geometry and rides in 03_src/rules.
const SmaJack = ({ name, rf }: { name: string; rf: string }) => (
  <chip name={name} supplierPartNumbers={{ jlcpcb: [LCSC.SMA] }}
    footprint={fp([1, 2, 3, 4, 5])}
    pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
    connections={conn({ 1: rf, 2: "GND", 3: "GND", 4: "GND", 5: "GND" })} />
)

// YAT-xxA+ fixed attenuator, MCLP 2x2 (case MC1630). Pads 1/3/4/6 = GND,
// 2 = RF_IN, 5 = RF_OUT, 7 = EXPOSED PAD.
// THE EXPOSED PAD IS THE RF GROUND RETURN, NOT A THERMAL PAD ("Case is defined
// as ground lead", YAT abs-max note 3 p.2). Tenting it or leaving it floating
// breaks the RETURN PATH, not just the heat path — which is why pad 7 is bound
// to GND here explicitly rather than left to a pour to find.
const Yat = ({ name, code, i, o }: {
  name: string; code: string; i: string; o: string
}) => (
  <chip name={name} supplierPartNumbers={{ jlcpcb: [code] }}
    footprint={fp([1, 2, 3, 4, 5, 6, 7])}
    pinLabels={{
      pin1: "GND", pin2: "RF_IN", pin3: "GND", pin4: "GND",
      pin5: "RF_OUT", pin6: "GND", pin7: "EP",
    }}
    connections={conn({ 1: "GND", 2: i, 3: "GND", 4: "GND", 5: o, 6: "GND", 7: "GND" })} />
)

// One loopback arm: splitter vertex -> YAT-10A+ -> YAT-2A+ -> switch RF2.
// BOTH ARMS ARE INSTANTIATED FROM THIS ONE FUNCTION so they cannot drift apart
// part-for-part. The published D4 delta is only meaningful if the only
// difference between the two arms is GEOMETRY (ADR-0011).
const ArmPad = ({ ids, armIn, mid, armOut }: {
  ids: [string, string]; armIn: string; mid: string; armOut: string
}) => (
  <group name={`arm_${ids[0]}`}>
    <Yat name={ids[0]} code={LCSC.YAT10} i={armIn} o={mid} />
    <Yat name={ids[1]} code={LCSC.YAT2} i={mid} o={armOut} />
  </group>
)

// One SPDT channel + its control network. RF1 FACES THE ANTENNA, RF2 FACES THE
// LOOPBACK ARM — see note 1 in the header block.
const SwitchChannel = ({ n, ant, loop, rxPluto, ctrl, ids }: {
  n: number; ant: string; loop: string; rxPluto: string; ctrl: string
  ids: { SW: string; RS: string; CB: string; PD: string; CV: string; CV2: string }
}) => (
  <group name={`sw${n}`}>
    <chip name={ids.SW} supplierPartNumbers={{ jlcpcb: [LCSC.SPDT] }}
      footprint={fp([1, 2, 3, 4, 5, 6])}
      pinLabels={{
        pin1: "RF2", pin2: "GND", pin3: "RF1",
        pin4: "VDD", pin5: "RFIN", pin6: "CTRL",
      }}
      connections={conn({
        1: loop, 2: "GND", 3: ant, 4: "N3V3_SW", 5: rxPluto, 6: ctrl,
      })} />
    {/* 1 kohm series: chosen for RF DAMPING, not for level — I_Ctrl max is
        10 nA, so the drop is 10 uV against a V_Ctrl,H floor of 1.0 V. */}
    <resistor name={ids.RS} resistance="1k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R1K] }}
      connections={{ pin1: N("RF_CTRL"), pin2: N(ctrl) }} />
    {/* 1 nF shunt AT the CTRL pin. Infineon's own measurement board carried
        1 nF CTRL-GND (Table 6 fn 2). WITHOUT IT THE SHARED CONTROL NET IS A
        RESONATOR, NOT A WIRE: 25 mm of this stackup's microstrip is lambda/4
        at ~1.5 GHz, mid-band, radiating into the calibration path. */}
    <capacitor name={ids.CB} capacitance="1nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C1N] }}
      connections={{ pin1: N(ctrl), pin2: N("GND") }} />
    {/* 10 kohm pull-down AT the switch. CTRL FLOATS: I_Ctrl is 2 nA typ, so an
        undriven CTRL has NO defined state. This covers the one case the MCU's
        internal 50-80 kohm pull-down cannot — IOVDD = 0 V, USB unplugged, pin
        genuinely floating. Bounded at 45 kohm by E-INV part_value (0.45 V /
        10 nA); 10 kohm is fitted for noise immunity. */}
    <resistor name={ids.PD} resistance="10k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R10K] }}
      connections={{ pin1: N(ctrl), pin2: N("GND") }} />
    {/* VDD bypass at the pad: 100 nF + 1 nF, the configuration Infineon's
        published harmonic/IMD numbers were measured in (Table 6 fn 2). */}
    <capacitor name={ids.CV} capacitance="100nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C100N] }}
      connections={{ pin1: N("N3V3_SW"), pin2: N("GND") }} />
    <capacitor name={ids.CV2} capacitance="1nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C1N] }}
      connections={{ pin1: N("N3V3_SW"), pin2: N("GND") }} />
  </group>
)

// RP2040 — 56 pins + centre pad (57). Bound pins only; every unlisted GPIO is
// intentionally omitted -> no_connect. GPIO15 is kept free (errata RP2040-E5:
// the SDK's USB enumeration workaround uses it during bus reset), GPIO0/1 are
// kept free for a debug UART, and the header input is on GPIO28 because
// GPIO26-29 are the ONLY ADC-capable pins (ADR-0008/ADR-0012).
const MCU_PINS: Record<number, string> = {
  // --- control + indication (see the pin-choice constraints above) ---
  4: "RF_CTRL",             // GPIO2  -> both switch CTRL nets via 1k each
  5: "LED_MODE",            // GPIO3  -> loopback indicator anode
  6: "HDR_STATE_GPIO",      // GPIO4  -> emulated open-drain state out, via 1k
  40: "HDR_CTRL_ADC",       // GPIO28/ADC2 — REQUIRED to be ADC-capable
  // --- strapping / miscellaneous ---
  19: "GND",                // TESTEN: Table 619 says plainly "connect to Gnd"
  26: "N3V3",               // RUN: DS sec.2.12 verbatim "If RUN is not used, it
                            //      should be tied high."  No reset button fitted.
  // --- crystal (sec.2.3 reference circuit; 1k damping on the XOUT side) ---
  20: "XIN",
  21: "XOUT",
  // --- USB (27 ohm series terminators sit between these and the pair) ---
  46: "USB_DM_MCU",
  47: "USB_DP_MCU",
  // --- QSPI execute-in-place bus to the flash ---
  51: "QSPI_SD3", 52: "QSPI_SCLK", 53: "QSPI_SD0",
  54: "QSPI_SD2", 55: "QSPI_SD1", 56: "QSPI_CSN",
  // --- power: 12 pins + the pad, each with its own decoupler ---
  1: "N3V3", 10: "N3V3", 22: "N3V3", 33: "N3V3", 42: "N3V3", 49: "N3V3", // IOVDD x6
  23: "VREG_VOUT", 50: "VREG_VOUT",       // DVDD x2, linked OFF-CHIP (sec.2.9.7.1)
  44: "N3V3",                              // VREG_VIN
  45: "VREG_VOUT",                         // VREG_VOUT
  48: "N3V3",                              // USB_VDD
  43: "N3V3",                              // ADC_AVDD
  57: "GND",                               // centre pad -> L2 via array
}

// W25Q16JVSSIQ SOIC-8. Names are the RP2040-side QSPI roles; the datasheet
// labels are in 02_parts/W25Q16JVSSIQ/part.yaml.
const FLASH_PINS: Record<number, string> = {
  1: "QSPI_CSN",   // /CS
  2: "QSPI_SD1",   // DO (IO1)
  3: "QSPI_SD2",   // /WP (IO2)
  4: "GND",
  5: "QSPI_SD0",   // DI (IO0)
  6: "QSPI_SCLK",  // CLK
  7: "QSPI_SD3",   // /HOLD or /RESET (IO3)
  8: "N3V3",
}

export default () => (
  <board width="70mm" height="55mm" name="pluto_cal_switch">

    {/* ==================================================================== */}
    {/* BLOCK 1 — THE FIVE SMA PORTS (ADR-0007, extended to x5 by ADR-0015)   */}
    {/* All five are KH-SMA-KE-Z JACKS. Gender chain: the Pluto's ports are   */}
    {/* JACKS (MEASURED) => the cables are MALE-MALE => ours are JACKS.       */}
    {/* NOTHING PHYSICAL DISTINGUISHES RX1 FROM RX2 any more — the non-uniform*/}
    {/* Pluto pitch that used to make a transposition semi-visible died with  */}
    {/* the cable decision, so the netlist assertions in                      */}
    {/* electrical_invariants.yaml are the ONLY thing standing between this   */}
    {/* board and two silently transposed channels.                          */}
    {/* ==================================================================== */}
    <SmaJack name="J_SMA_ANT1" rf="RX_ANT1" />
    <SmaJack name="J_SMA_ANT2" rf="RX_ANT2" />
    <SmaJack name="J_SMA_RX1" rf="RX_PLUTO1" />
    <SmaJack name="J_SMA_RX2" rf="RX_PLUTO2" />
    <SmaJack name="J_SMA_TX" rf="TX_PLUTO" />

    {/* ---- DC blocks: ANTENNA PORTS ONLY (ADR-0005) --------------------- */}
    {/* The two user-facing antenna ports are the ONE place an unknown DC     */}
    {/* source can appear (an active antenna, a bias-tee'd LNA). Without a    */}
    {/* block that bias is shorted to ground through the switch die and the   */}
    {/* YAT pads, driving fault current through a 0.7 x 1.1 mm part.          */}
    {/* C0G IS PART OF THE SPEC, NOT A PREFERENCE — an X7R 1 nF fits the same */}
    {/* land and destroys the amplitude accuracy this board exists to sell,   */}
    {/* which is why the LCSC code is PINNED instead of left to the parts     */}
    {/* engine. Value derived in DETAIL_DESIGN sec.8: 1 nF is the compromise  */}
    {/* across 85.7:1 (RL 32.9 dB @70 MHz / 16.5 dB @6 GHz).                  */}
    <capacitor name="C_DCBLK1" capacitance="1nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.DCBLK] }}
      connections={{ pin1: N("RX_ANT1"), pin2: N("SW1_ANT") }} />
    <capacitor name="C_DCBLK2" capacitance="1nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.DCBLK] }}
      connections={{ pin1: N("RX_ANT2"), pin2: N("SW2_ANT") }} />

    {/* ==================================================================== */}
    {/* BLOCK 2 — PAD_A1, THE 25.78 dB PRE-SPLIT PAD (ADR-0016)              */}
    {/* 2x YAT-10A+ then 3x YAT-2A+, IN THAT ORDER. The order is not          */}
    {/* cosmetic: DETAIL_DESIGN sec.4.3 computes the board's +27 dBm TX abuse */}
    {/* ceiling against the FIRST chip (a YAT-10A+ at 1.7 W), and sec.7 sets  */}
    {/* the TX port's return loss from that same first chip. Everything       */}
    {/* downstream of it got 16 dB colder when A9 moved 18 dB pre-split.      */}
    {/* Five chips in series is not free and it is BUDGETED, not waved away:  */}
    {/* 4 x 3 mm of interconnect = 0.43 dB at 6 GHz (DETAIL_DESIGN sec.2).    */}
    {/* WHY FIVE CHIPS: YAT-10A+ and YAT-2A+ are the only two values with     */}
    {/* VERIFIED stock, and the >=40 dB guarantee is built on datasheet MIN   */}
    {/* columns — a substitute with an unread min column cannot carry it.     */}
    {/* ==================================================================== */}
    <Yat name="U_PAD_A1A" code={LCSC.YAT10} i="TX_PLUTO" o="PAD_A1_1" />
    <Yat name="U_PAD_A1B" code={LCSC.YAT10} i="PAD_A1_1" o="PAD_A1_2" />
    <Yat name="U_PAD_A1C" code={LCSC.YAT2} i="PAD_A1_2" o="PAD_A1_3" />
    <Yat name="U_PAD_A1D" code={LCSC.YAT2} i="PAD_A1_3" o="PAD_A1_4" />
    <Yat name="U_PAD_A1E" code={LCSC.YAT2} i="PAD_A1_4" o="LOOP_SPLIT" />

    {/* ==================================================================== */}
    {/* BLOCK 3 — THE RESISTIVE DELTA SPLITTER (ADR-0003)                    */}
    {/* Three 49.9 ohm 0402 in a DELTA: one between each PAIR of the three    */}
    {/* ports. R_DELTA3 bridges the two ARMS and is the leg that exists ONLY  */}
    {/* in a delta — its absence IS the star topology, and a star is 9.3 dB   */}
    {/* worse on return loss at 6 GHz with identical parts. Under symmetric   */}
    {/* excitation R_DELTA3 carries ZERO current, which is why the delta's    */}
    {/* through path crosses ONE chip body where a star's crosses two.        */}
    {/* 50/50/50 is the ONLY all-ports-matched resistive 3-port (the port-2   */}
    {/* match reduces to Rb^2 + 50Rb - 5000 = 0 => Rb = 50 uniquely), so the  */}
    {/* VALUE here IS the topology and nothing but E-INV can tell a delta     */}
    {/* from a star in a netlist.                                            */}
    {/* ==================================================================== */}
    <resistor name="R_DELTA1" resistance="49.9" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.R499] }}
      connections={{ pin1: N("LOOP_SPLIT"), pin2: N("LOOP_ARM1") }} />
    <resistor name="R_DELTA2" resistance="49.9" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.R499] }}
      connections={{ pin1: N("LOOP_SPLIT"), pin2: N("LOOP_ARM2") }} />
    <resistor name="R_DELTA3" resistance="49.9" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.R499] }}
      connections={{ pin1: N("LOOP_ARM1"), pin2: N("LOOP_ARM2") }} />

    {/* ==================================================================== */}
    {/* BLOCK 4 — THE TWO ARM PADS, 11.9 dB EACH (ADR-0004)                  */}
    {/* A9 added 18 dB and ALL of it went pre-split; PAD_A2 is UNCHANGED,     */}
    {/* because its value was never set by the total. Four independent        */}
    {/* arguments pin it: (a) inter-channel isolation is 6.02 + 2*A2, so 6.02 */}
    {/* dB becomes 29.9 dB; (b) an unplugged RX cable would otherwise add     */}
    {/* +3.52 dB to the OTHER channel with no error indication — the arm pads */}
    {/* mask the open by 24 dB and the error falls to ~0.2 dB; (c) in ANTENNA */}
    {/* mode both arms face the switches' REFLECTIVE SHORTS and without arm   */}
    {/* pads the splitter's Zin is INFINITE (TX sees Gamma = +1); (d) the     */}
    {/* AD936x RX match MOVES WITH THE AGC GAIN INDEX, so the contamination   */}
    {/* the 6 dB isolation lets through is non-stationary and cannot be       */}
    {/* calibrated out.                                                       */}
    {/* Both arms come from ONE component function so they cannot drift.      */}
    {/* ==================================================================== */}
    <ArmPad ids={["U_PAD_A2A1", "U_PAD_A2A2"]}
      armIn="LOOP_ARM1" mid="PAD_A2A_1" armOut="LOOP_ARM1_SW" />
    <ArmPad ids={["U_PAD_A2B1", "U_PAD_A2B2"]}
      armIn="LOOP_ARM2" mid="PAD_A2B_1" armOut="LOOP_ARM2_SW" />

    {/* ==================================================================== */}
    {/* BLOCK 5 — THE TWO SPDT SWITCHES (ADR-0001, ADR-0002)                 */}
    {/* ONE control net drives both: they are one instrument and must switch  */}
    {/* together. VDD is the FERRITE-ISOLATED 3V3_SW branch, never raw 3V3    */}
    {/* and NEVER the 5 V rail — BGS12WN6's VDD absolute max is 4.2 V and the */}
    {/* pin-identical BGS12P2L6's is 3.6 V, against a 3.366 V worst-case rail.*/}
    {/* ==================================================================== */}
    <SwitchChannel n={1} ant="SW1_ANT" loop="LOOP_ARM1_SW" rxPluto="RX_PLUTO1"
      ctrl="RF_CTRL_SW1"
      ids={{ SW: "U_SW1", RS: "R_CTRL1", CB: "C_CTRL1", PD: "R_CTRL_PD1",
             CV: "C_SW1A", CV2: "C_SW1B" }} />
    <SwitchChannel n={2} ant="SW2_ANT" loop="LOOP_ARM2_SW" rxPluto="RX_PLUTO2"
      ctrl="RF_CTRL_SW2"
      ids={{ SW: "U_SW2", RS: "R_CTRL2", CB: "C_CTRL2", PD: "R_CTRL_PD2",
             CV: "C_SW2A", CV2: "C_SW2B" }} />

    {/* ==================================================================== */}
    {/* BLOCK 6 — USB ENTRY, PROTECTION AND THE 3V3 RAIL (ADR-0009)          */}
    {/* Order is BINDING and E-INV asserts it as one chain:                   */}
    {/*   VBUS --[F1 PPTC]-- VBUS_PF --[FB1 ferrite]-- VBUS_F --[LDO]-- 3V3   */}
    {/* THE PPTC PROTECTS THE HOST, NOT THIS BOARD: a shorted rail here must  */}
    {/* not kill the laptop's USB port. It is first, at the connector.        */}
    {/* ==================================================================== */}
    {/* micro-B: 1=VBUS 2=D- 3=D+ 4=ID(NC) 5=GND 6=SHELL. THE SIGNAL NAMES    */}
    {/* ARE INFERRED, NOT PRINTED — XKB's drawing labels only "PIN 1"/"PIN 5" */}
    {/* and gives current ratings by group. STILL OWED: a fresh-context pin   */}
    {/* review against JLC's own footprint (02_parts/README.md deviations).   */}
    {/* If pin 1 is at the opposite end, VBUS and GND swap and the board dies */}
    {/* on first plug-in. The shell and BOTH THT legs tie DIRECTLY to GND —   */}
    {/* no R/C isolation network: on an RF board the SMA grounds, the board   */}
    {/* ground and the cable shield must be ONE system.                       */}
    <chip name="J_USB" supplierPartNumbers={{ jlcpcb: [LCSC.USB] }}
      footprint={fp([1, 2, 3, 4, 5, 6])}
      pinLabels={{
        pin1: "VBUS", pin2: "DM", pin3: "DP", pin4: "ID",
        pin5: "GND", pin6: "SHELL",
      }}
      connections={conn({ 1: "VBUS", 2: "USB_DM", 3: "USB_DP", 5: "GND", 6: "GND" })}
      /* 4 = ID -> no_connect: this is a device-only port */ />

    {/* USBLC6-2SC6 AT THE CONNECTOR, upstream of everything on D+/D-.        */}
    {/* PINS 1 AND 6 ARE THE SAME INTERNAL NODE, and so are 3 and 4 (Figure 1,*/}
    {/* Doc ID 11265 Rev 5 p.1). Its "route the data line in one pin and out  */}
    {/* the other" is a COPPER instruction — no stub in the clamp path —      */}
    {/* NOT two electrical nets. Binding pin 6 to a different net from pin 1  */}
    {/* would draw a part that does not exist and make a shunt clamp look     */}
    {/* like a series element to every human reading the schematic PDF.       */}
    {/* Its section 2.3 works the arithmetic that makes this a LAYOUT part:   */}
    {/* 6 nH of track (10 mm x 0.5 mm) raises the clamp from +31 V to +319 V  */}
    {/* at a 1 ns edge.                                                       */}
    <chip name="U_ESD" supplierPartNumbers={{ jlcpcb: [LCSC.USBESD] }}
      footprint={fp([1, 2, 3, 4, 5, 6])}
      pinLabels={{
        pin1: "IO1", pin2: "GND", pin3: "IO2",
        pin4: "IO2", pin5: "VBUS", pin6: "IO1",
      }}
      connections={conn({
        1: "USB_DP", 2: "GND", 3: "USB_DM", 4: "USB_DM", 5: "VBUS", 6: "USB_DP",
      })} />

    {/* VBUS bulk AT THE CONNECTOR. THE BINDING CONSTRAINT IS A CEILING, NOT  */}
    {/* A FLOOR: USB 2.0 sec.7.2.4.1 caps downstream bulk at 10 uF without    */}
    {/* surge limiting. Board total = 4.7 + 0.1 + 1.0 (LDO in) + 1.0 (LDO out)*/}
    {/* = 6.8 uF, compliant with ZERO soft-start parts. This is the number    */}
    {/* people silently violate by adding "one more 10 uF".                   */}
    <capacitor name="C_VBUS" capacitance="4.7uF" footprint="0805"
      supplierPartNumbers={{ jlcpcb: [P.C4U7] }}
      connections={{ pin1: N("VBUS"), pin2: N("GND") }} />
    <capacitor name="C_VBUSH" capacitance="100nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C100N] }}
      connections={{ pin1: N("VBUS"), pin2: N("GND") }} />
    <chip name="F1" supplierPartNumbers={{ jlcpcb: [LCSC.PPTC] }}
      footprint={fp([1, 2])}
      connections={conn({ 1: "VBUS", 2: "VBUS_PF" })} />
    {/* 600 ohm @100 MHz. The USB cable is a ~1 m antenna galvanically bonded */}
    {/* to the RF ground system; this keeps host-side common-mode junk off    */}
    {/* the 3V3 that biases the switches. 10 mV drop at 100 mA.               */}
    <inductor name="FB1" inductance="600" footprint="0805"
      supplierPartNumbers={{ jlcpcb: [LCSC.FERRITE] }}
      connections={{ pin1: N("VBUS_PF"), pin2: N("VBUS_F") }} />

    {/* ME6211C33M5G-N SOT-23-5: 1=VIN 2=VSS 3=CE 4=NC 5=VOUT.               */}
    {/* CE IS TIED TO VIN EXPLICITLY. Figure 2 (p.2) shows it that way and    */}
    {/* the datasheet NEVER states whether the C series has an internal       */}
    {/* pull-up or pull-down — a floating CE is UNDEFINED power-up behaviour. */}
    {/* CIN = COUT = 1 uF are the CONDITIONS every electrical number on p.8   */}
    {/* is specified under, not suggestions.                                  */}
    <chip name="U_LDO" supplierPartNumbers={{ jlcpcb: [LCSC.LDO] }}
      footprint={fp([1, 2, 3, 4, 5])}
      pinLabels={{ pin1: "VIN", pin2: "VSS", pin3: "CE", pin4: "NC", pin5: "VOUT" }}
      connections={conn({ 1: "VBUS_F", 2: "GND", 3: "VBUS_F", 5: "N3V3" })}
      /* 4 = NC -> no_connect */ />
    <capacitor name="C_LDOI" capacitance="1uF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C1U] }}
      connections={{ pin1: N("VBUS_F"), pin2: N("GND") }} />
    <capacitor name="C_LDOO" capacitance="1uF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C1U] }}
      connections={{ pin1: N("N3V3"), pin2: N("GND") }} />

    {/* Ferrite-isolated switch bias. ONE ferrite, ONE 3V3_SW net, BOTH       */}
    {/* switches on it — they must switch together and be biased together.    */}
    <inductor name="FB2" inductance="600" footprint="0805"
      supplierPartNumbers={{ jlcpcb: [LCSC.FERRITE] }}
      connections={{ pin1: N("N3V3"), pin2: N("N3V3_SW") }} />

    {/* ==================================================================== */}
    {/* BLOCK 7 — THE GPIO HEADER: AN ANALOG INPUT, DELIBERATELY (ADR-0008)  */}
    {/* PlutoPlus IO is 1.8 V and RP2040's VIH is a FLAT 2.0 V (not           */}
    {/* 0.65*IOVDD). A Zynq HR bank at VCCO = 1.8 V has a worst-case VOH of   */}
    {/* 1.35 V, SO A DIRECT DIGITAL CONNECTION READS PERMANENTLY LOW — and    */}
    {/* that failure is FAIL-SAFE, which is exactly what makes it dangerous:  */}
    {/* it passes every bench test that asks "can it spuriously enter         */}
    {/* loopback" and surfaces only as "the GPIO control doesn't work",       */}
    {/* plausibly after seal. The divider into an ADC pin reads 1.8 / 3.3 /   */}
    {/* 5.0 V logic with no translator and no second rail, and is INPUT-ONLY  */}
    {/* BY CONSTRUCTION — an ADC-configured pin has its digital output        */}
    {/* disabled, so no firmware bug can drive 3.3 V into a Zynq pin whose    */}
    {/* absolute maximum is ~2.35 V.                                          */}
    {/* Header order GND / CTRL_IN / STATE_OUT / GND: the two grounds FLANK   */}
    {/* the signals so a one-position miswire lands a signal on a ground.     */}
    {/* 3V3 IS DELIBERATELY NOT EXPORTED — a back-feed must not fight the LDO.*/}
    {/* ==================================================================== */}
    <chip name="J_HDR" supplierPartNumbers={{ jlcpcb: [LCSC.HDR] }}
      footprint={fp([1, 2, 3, 4])}
      pinLabels={{ pin1: "GND", pin2: "CTRL_IN", pin3: "STATE_OUT", pin4: "GND" }}
      connections={conn({
        1: "GND", 2: "HDR_CTRL_IN", 3: "HDR_STATE_OUT", 4: "GND",
      })} />
    {/* ESD clamp UPSTREAM of both series resistors, at the connector. It is  */}
    {/* rated V_RWM 5.5 V against the header's declared 5.0 V ceiling — the   */}
    {/* clamp and the 2.2 kohm series are ONE mechanism, neither alone covers */}
    {/* the miswire. Pins 1/2 are NC internally and are FLOATED (the          */}
    {/* datasheet's own conservative choice).                                 */}
    <chip name="U_HDR_ESD" supplierPartNumbers={{ jlcpcb: [LCSC.HDRESD] }}
      footprint={fp([1, 2, 3, 4, 5])}
      pinLabels={{ pin1: "NC", pin2: "NC", pin3: "IO1", pin4: "GND", pin5: "IO2" }}
      connections={conn({ 3: "HDR_CTRL_IN", 4: "GND", 5: "HDR_STATE_OUT" })}
      /* 1, 2 = NC -> no_connect */ />
    {/* 2.2k / 3.3k = /2.5. Header at the pin: 1.8 V -> 0.72 V, 3.3 V ->      */}
    {/* 1.32 V, 5.0 V -> 2.00 V, all inside the 0-3.3 V ADC range; firmware   */}
    {/* thresholds at 0.36 V and a 12-bit LSB is 0.81 mV. The 2.2k is also    */}
    {/* the FAULT-CURRENT BOUND, not just a divider leg: a firmware bug       */}
    {/* driving 3.3 V into a clamped 1.8 V Zynq pin sources 0.45 mA.          */}
    <resistor name="R_HDR_S" resistance="2.2k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R2K2] }}
      connections={{ pin1: N("HDR_CTRL_IN"), pin2: N("HDR_CTRL_ADC") }} />
    {/* Divider bottom AND the pull-down that makes an UNCONNECTED header     */}
    {/* read 0 V = ANTENNA mode. */}
    <resistor name="R_HDR_G" resistance="3.3k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R3K3] }}
      connections={{ pin1: N("HDR_CTRL_ADC"), pin2: N("GND") }} />
    {/* Emulated open-drain state output: firmware drives LOW or leaves the   */}
    {/* pin a hi-Z input, so it cannot exceed whatever rail the user pulls it */}
    {/* up to and cannot damage a 1.8 V device. STATE_OUT is an ADDITION, not */}
    {/* something the brief asked for (ADR-0008 sec.3).                       */}
    <resistor name="R_HDR_O" resistance="1k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R1K] }}
      connections={{ pin1: N("HDR_STATE_GPIO"), pin2: N("HDR_STATE_OUT") }} />

    {/* ==================================================================== */}
    {/* BLOCK 8 — RP2040 (ADR-0012). Chosen because its power-on-safe state   */}
    {/* is documented PER PIN and is fail-safe against a MISSING external     */}
    {/* resistor: PADS_BANK0 resets PDE=1/PUE=0, GPIO_OE resets to 0, and the */}
    {/* internal 50-80 kohm pull-down sits in PARALLEL with the external 10k. */}
    {/* A blank board from JLCPCB falls into the USB mass-storage bootloader, */}
    {/* whose bootrom touches only the QSPI pads, so the pull-down survives   */}
    {/* indefinitely. POWER-ON = CTRL LOW = ANTENNA MODE, in silicon.         */}
    {/* ==================================================================== */}
    <chip name="U_MCU" supplierPartNumbers={{ jlcpcb: [LCSC.MCU] }}
      footprint={fp(Array.from({ length: 57 }, (_, i) => i + 1))}
      connections={conn(MCU_PINS)} />

    {/* One 100 nF per power pin (vendor sec.2.1.2 pp.7-8) — the reference    */}
    {/* design calls its OWN single violation (two pins sharing one cap) a    */}
    {/* compromise that "could have the effect of limiting the maximum        */}
    {/* speed", so no sharing here. IOVDD x6: */}
    <capacitor name="C_IO1" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_IO2" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_IO3" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_IO4" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_IO5" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_IO6" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    {/* DVDD x2 (the core rail, fed OFF-CHIP from VREG_VOUT per sec.2.9.7.1) */}
    <capacitor name="C_DV1" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("VREG_VOUT"), pin2: N("GND") }} />
    <capacitor name="C_DV2" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("VREG_VOUT"), pin2: N("GND") }} />
    <capacitor name="C_USBV" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    {/* ADC_AVDD is fed from 3V3 directly, NOT through an LC filter, and that */}
    {/* is a JUDGEMENT rather than an omission: the only ADC channel on this  */}
    {/* board reads a STATIC header level against a 0.36 V threshold with a   */}
    {/* 0.81 mV LSB. There is ~440 LSB of margin; converter noise cannot      */}
    {/* reach the decision. If an analogue measurement is ever added here,    */}
    {/* this is the line to revisit.                                          */}
    <capacitor name="C_ADCV" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C100N] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    {/* 1 uF at BOTH the internal regulator's input and output (sec.2.1.3) */}
    <capacitor name="C_VREGI" capacitance="1uF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C1U] }} connections={{ pin1: N("N3V3"), pin2: N("GND") }} />
    <capacitor name="C_VREGO" capacitance="1uF" footprint="0402" supplierPartNumbers={{ jlcpcb: [P.C1U] }} connections={{ pin1: N("VREG_VOUT"), pin2: N("GND") }} />

    {/* ---- 12 MHz crystal: THE VENDOR REFERENCE CIRCUIT, UNMODIFIED ------ */}
    {/* ADR-0012 left the crystal deliberately unselected with TWO fully      */}
    {/* specified resolutions. Resolution (a) is taken: ABM8-272-T3 is        */}
    {/* CL = 10 pF / ESR = 50 ohm MAX, exactly Raspberry Pi's stated limits,  */}
    {/* and its own datasheet p.(2) reads "Crystal approved for use with      */}
    {/* Raspberry Pi's RP2040". So the load caps are the reference 15 pF —    */}
    {/* DERIVED, not copied: 2 x (CL - Cstray) = 2 x (10 - 3) = 14 -> E24 15. */}
    {/* Resolution (b) (the JLC BASIC 20 pF C9002) would need 33 pF and a     */}
    {/* start-up test at both temperature extremes in the release gate.       */}
    {/* A CRYSTAL THAT DOES NOT START MEANS USB NEVER ENUMERATES, and on this */}
    {/* board that is a brick: the ONLY programming path is the USB           */}
    {/* mass-storage bootloader.                                              */}
    <chip name="Y1" supplierPartNumbers={{ jlcpcb: [LCSC.XTAL] }}
      footprint={fp([1, 2, 3, 4])}
      pinLabels={{ pin1: "XA", pin2: "GND", pin3: "XB", pin4: "GND" }}
      connections={conn({ 1: "XIN", 2: "GND", 3: "XOUT_R", 4: "GND" })} />
    <capacitor name="C_XIN" capacitance="15pF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.XTALCAP] }}
      connections={{ pin1: N("XIN"), pin2: N("GND") }} />
    <capacitor name="C_XOUT" capacitance="15pF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [LCSC.XTALCAP] }}
      connections={{ pin1: N("XOUT_R"), pin2: N("GND") }} />
    {/* 1 kohm damping on the XOUT side — sized against a 50 ohm ESR part,    */}
    {/* which is the other half of why the crystal had to meet ESR <= 50 ohm. */}
    <resistor name="R_XTAL" resistance="1k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R1K] }}
      connections={{ pin1: N("XOUT_R"), pin2: N("XOUT") }} />

    {/* ---- USB series termination, "placed close to the chip" ------------ */}
    <resistor name="R_USBP" resistance="27" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R27] }}
      connections={{ pin1: N("USB_DP"), pin2: N("USB_DP_MCU") }} />
    <resistor name="R_USBM" resistance="27" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R27] }}
      connections={{ pin1: N("USB_DM"), pin2: N("USB_DM_MCU") }} />

    {/* ---- QSPI flash. THE BUS IS AN RF PROBLEM ON THIS BOARD ------------ */}
    {/* The RP2040 executes in place, so this runs continuously at tens of    */}
    {/* MHz with sub-ns edges whose harmonics land inside the 70 MHz - 6 GHz  */}
    {/* band the board exists to measure. "Short connections" is a SPUR rule  */}
    {/* here, not only a signal-integrity one: flash hugs the MCU, both at    */}
    {/* the far end from every SMA jack (ARCHITECTURE sec.10.5).              */}
    <chip name="U_FLASH" supplierPartNumbers={{ jlcpcb: [LCSC.FLASH] }}
      footprint={fp([1, 2, 3, 4, 5, 6, 7, 8])}
      pinLabels={{
        pin1: "CSn", pin2: "IO1", pin3: "IO2", pin4: "GND",
        pin5: "IO0", pin6: "CLK", pin7: "IO3", pin8: "VCC",
      }}
      connections={conn(FLASH_PINS)} />
    <capacitor name="C_FLASH" capacitance="100nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.C100N] }}
      connections={{ pin1: N("N3V3"), pin2: N("GND") }} />

    {/* ---- BOOTSEL. AN AUTHORING DECISION, DECLARED, NOT IN ANY ADR ------ */}
    {/* A blank board enters the bootloader by itself (ADR-0012), so this is  */}
    {/* not needed for the FIRST flash — it is needed for every SUBSEQUENT    */}
    {/* one. D7 (control arbitration) is still open, so the firmware WILL be  */}
    {/* rebuilt at least once; without this the only reflash path is shorting */}
    {/* a pin by hand next to a 0.4 mm-pitch QFN. The 1 kohm isolates the     */}
    {/* button node from the QSPI line and sits AT THE FLASH (vendor sec.2.2).*/}
    <resistor name="R_BOOT" resistance="1k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R1K] }}
      connections={{ pin1: N("QSPI_CSN"), pin2: N("USB_BOOT") }} />
    <chip name="SW_BOOT" supplierPartNumbers={{ jlcpcb: [LCSC.BOOTSW] }}
      footprint={fp([1, 2, 3, 4])}
      pinLabels={{ pin1: "A", pin2: "A", pin3: "B", pin4: "B" }}
      connections={conn({ 1: "USB_BOOT", 2: "USB_BOOT", 3: "GND", 4: "GND" })} />

    {/* ==================================================================== */}
    {/* BLOCK 9 — STATUS INDICATION                                          */}
    {/* Two identical red 0603s: PWR (rail present) and MODE (RF path is in   */}
    {/* LOOPBACK). Being the same device, THE SILK is what distinguishes them */}
    {/* — a functional-caption obligation, not decoration.                    */}
    {/* 680 ohm from (3.3 - 2.0)/2 mA = 650 -> E24 680 => 1.9 mA each, inside */}
    {/* the power tree's declared 4 mA LED budget at the worst Vf corner.     */}
    {/* Pad 1 is the CATHODE.                                                 */}
    {/* ==================================================================== */}
    <chip name="D_LED_PWR" supplierPartNumbers={{ jlcpcb: [LCSC.LED] }}
      footprint={fp([1, 2])} pinLabels={{ pin1: "K", pin2: "A" }}
      connections={conn({ 1: "LED_PWR_K", 2: "N3V3" })} />
    <resistor name="R_LED1" resistance="680" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R680] }}
      connections={{ pin1: N("LED_PWR_K"), pin2: N("GND") }} />
    <chip name="D_LED_MODE" supplierPartNumbers={{ jlcpcb: [LCSC.LED] }}
      footprint={fp([1, 2])} pinLabels={{ pin1: "K", pin2: "A" }}
      connections={conn({ 1: "LED_MODE_K", 2: "LED_MODE" })} />
    <resistor name="R_LED2" resistance="680" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [P.R680] }}
      connections={{ pin1: N("LED_MODE_K"), pin2: N("GND") }} />

  </board>
)

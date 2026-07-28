// pluto-rx2-8way — an 8-element antenna selector for angle-of-arrival on an
// ADALM-PlutoPlus RX2. THE BOARD, authored in tscircuit (repo ADR-0001/0002).
//
// One absorptive SP8T (U_SW, pSemi PE42482A-X) sits at the geometric centre of
// a ring of ten vertical SMA jacks and puts one of eight antennas on Pluto RX2
// at a time. Element 8 is not a dedicated antenna: it is the RX1 antenna,
// tapped through a two-resistor pickoff (R_T1/R_T2, 220 ohm each) so RX1 keeps
// its own path and loses 0.43 dB. A free-running RP2040 PIO walks three select
// bits, dwelling 8192 clean samples on each ordinary element and 4096 on the
// tapped reference; the asymmetry is the frame marker (BRIEF D1).
//
// The circuit is derived in 01_docs/{ARCHITECTURE,DETAIL_DESIGN}.md and the
// eight ADRs. NOTHING is re-derived here — this file is the capture.
//
// ===========================================================================
// AUTHORING RULES HONOURED (03_tscircuit/contracts.md), and what each buys:
//
//  1. EVERY pin is bound with connections={{...}} to an explicit `net.NAME` —
//     never a pairwise <trace>. Parity by construction (canon S2): tscircuit
//     never gets to invent a `C1_pos`-style auto net name.
//  2. Every specialty part carries supplierPartNumbers={{jlcpcb:["C..."]}}.
//     That JLC code is the HANDLE the converter uses to resolve the part's
//     real FPID from 02_parts/*/part.yaml. No code -> empty FPID ->
//     generate_board hard-errors. It is the one authoring-completeness step.
//  3. The digit-leading rail 3V3 is authored `N3V3`; the converter's canon_net
//     strips a single leading N that GUARDS A DIGIT. `net_aliases.txt` states
//     the mapping explicitly anyway, because rules/nets.yaml keys its
//     netclasses on the CANONICAL names and on this board a netclass miss is
//     an IMPEDANCE or an AMPACITY defect, not a cosmetic one.
//  4. J_USB's pads are ALPHANUMERIC (A1..B12 + SH) and tscircuit DROPS such a
//     part SILENTLY with ERC still 0 (2026-07-21: four USB connectors, 48/52).
//     Every one carries DUAL portHints [realName, numericAlias] and the
//     mapping is recorded in parity_padmap.txt; tsx_preflight.py is run BEFORE
//     the first tsci build and count_parity.py after it.
//  5. Two-pad POLARIZED parts (D_TVS, the LEDs) are authored as <chip> with
//     pad 1 = CATHODE, matching the KiCad footprint marker convention, so no
//     generic-symbol reversal can ship. This is the usb-hub-3s v1.0 D1 defect
//     class: symbol, footprint, netlist and board were consistently WRONG
//     together and only INTENT disagreed.
//  6. Exposed pads are authored as real pads (U_SW.25, U_MCU.57, U_LDO.4).
//     U_MCU's centre pad is the chip's ONLY ground connection — 56 peripheral
//     leads and not one of them is GND (Table 621, PDF p615).
//
// FOUR THINGS THIS FILE IS THE FIRST ARTIFACT TO CARRY, all of them corrections
// merged at stage 2/3 and all of them invisible to every downstream gate:
//   * D_TVS pad 1 is the CATHODE and goes to VBUS_F (downstream of F_IN).
//   * A6<->B6 and A7<->B7 are STRAPPED. A Type-C plug is reversible; a board
//     that wires one pair enumerates in ONE insertion orientation and is DEAD
//     in the other, and ERC/DRC/parity ALL pass either way because every pin
//     has a net.
//   * VBUS_LDO exists as its own net. FB_IN is a SERIES element, so the node
//     feeding U_LDO.VIN is NOT VBUS_F. Without the name it would have taken
//     the default 0.25 mm netclass while carrying the whole 0.15 A.
//   * DVDD_1V1 exists as its own net. RP2040's 1.1 V core regulator is ON-DIE
//     and its output leaves at VREG_VOUT (45) and must be wired IN COPPER back
//     to DVDD (23, 50). Omit the link and every artifact still looks correct:
//     VREG_VOUT reads as an unused output, DVDD as an undriven supply.
// ===========================================================================

// ---- LCSC codes for the two parts back-filled at stage 4 (see the journal).
// Kept as named constants because each serves TWO refdes and a divergence
// between the two instances would be a sourcing defect nothing else catches.
const LED_JLC = "C2286"    // KT-0603R, RED 0603 indicator (Vf ~2.0 V - the ballast depends on it)
const SW_JLC = "C318884"   // TS-1187A-B-A-B, SMD tact; ONE MPN serves SW_BOOT + SW_RUN

// ---- COMMODITY PASSIVE LCSC CODES, PINNED. -------------------------------
// tscircuit's parts engine will happily CHOOSE a JLC code for any un-coded
// passive, and it did: measured 2026-07-28, all 38 commodity passives came
// back from `tsci build` carrying a supplier code nobody authored. Two
// consequences, both bad, and both fixed by pinning:
//
//  1. `tsci build` IS NON-DETERMINISTIC, so an unpinned BOM's LCSC codes are
//     a build-time choice rather than a design decision. Canon M3 says the
//     board must be regenerable from source; a BOM line that can change
//     between two builds of the same source is not.
//  2. THE ENGINE'S CHOICE IS NOT GRADED FOR STOCK. Its 47 ohm pick was
//     C25118 (0402WGF470JTCE) at **stock 10, extended** — for a part this
//     board uses FOUR times, and the one whose value ADR-0005 machine-asserts
//     because it is what holds PE42482A-X's 3.6 V digital absolute maximum.
//     C137864 (RC0402JR-0747RL, 47R +/-5%) is the same value at stock 86,783.
//     Its 680 ohm pick (C25130) is likewise unverified where the repo's own
//     vetted passives ledger already carries C137948 (RC0402FR-07680RL).
//
// Every code below was READ FROM THE JLC CATALOG on 2026-07-28 (stock +
// library tier + the describe string), not inferred from a part number.
const R47 = "C137864"      // RC0402JR-0747RL   47R +/-5%   0402  stock 86,783
const R220 = "C25091"      // 0402WGF2200TCE    220R +/-1%  0402  base, 995,162
const R680 = "C137948"     // RC0402FR-07680RL  680R        0402  stock 575,326
const R1K = "C11702"       // 0402WGF1001TCE    1k          0402  ledger-vetted
const R5K1 = "C25905"      // 0402WGF5101TCE    5.1k        0402  ledger-vetted
const R10K = "C25744"      // 0402WGF1002TCE    10k         0402  ledger-vetted
const R27R4 = "C274349"    // RC0402FR-0727R4L  27.4R +/-1% 0402  stock 5,133
const C100N = "C1525"      // CL05B104KO5NNNC   100nF X7R   0402  ledger-vetted
const C15P = "C1548"       // 0402CG150J500NT   15pF C0G    0402  base, 2,388,330
const C1U0603 = "C15849"   // CL10A105KB8NNNC   1uF         0603  ledger-vetted
const C1U0805 = "C28323"   // CL21B105KBFNNNE   1uF X7R     0805  ledger-vetted
const C4U7 = "C1779"       // CL21A475KAQNNNE   4.7uF       0805  ledger-vetted

// ===================== render-only footprints ==============================
// These exist so tscircuit can RENDER the part. The FAB footprint always comes
// from 02_parts/<MPN>/part.yaml via the JLC code (rule 2 above) — including
// the three project-authored ones in 03_src/lib/pluto_rx2_8way.pretty/. What
// MUST be right here is the set of PAD NAMES, because those become the KiCad
// symbol's pin numbers and therefore the netlist's identity.

// PE42482A-X — QFN-24 4x4 P0.5 + EP. Vendor land (Figure 23, PDF p21): 24 pads
// 0.30 x 0.60 with centres at r = 1.90, EP 2.75 sq. Pin order: 1-6 left column
// top->bottom, 7-12 bottom left->right, 13-18 right column bottom->top,
// 19-24 top right->left; pin-1 dot at the TOP-LEFT.
const Qfn24Ep = () => {
  const o = [1.25, 0.75, 0.25, -0.25, -0.75, -1.25]
  return (
    <footprint>
      {o.map((y, i) => (
        <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-1.9mm" pcbY={`${y}mm`}
          width="0.6mm" height="0.3mm" shape="rect" />
      ))}
      {o.map((x, i) => (
        <smtpad key={`b${i}`} portHints={[`${i + 7}`]} pcbX={`${-x}mm`} pcbY="-1.9mm"
          width="0.3mm" height="0.6mm" shape="rect" />
      ))}
      {o.map((y, i) => (
        <smtpad key={`r${i}`} portHints={[`${i + 13}`]} pcbX="1.9mm" pcbY={`${-y}mm`}
          width="0.6mm" height="0.3mm" shape="rect" />
      ))}
      {o.map((x, i) => (
        <smtpad key={`t${i}`} portHints={[`${i + 19}`]} pcbX={`${x}mm`} pcbY="1.9mm"
          width="0.3mm" height="0.6mm" shape="rect" />
      ))}
      <smtpad portHints={["25"]} pcbX="0mm" pcbY="0mm" width="2.75mm" height="2.75mm" shape="rect" />
    </footprint>
  )
}

// RP2040 — QFN-56 7x7 P0.4 + the REDUCED 3.2 mm ePad (datasheet sec 5.1 NOTE:
// smaller than most, which is what opens the 1.400 mm routing channel between
// the pad ring and the centre pad). 1-14 left top->bottom, 15-28 bottom
// left->right, 29-42 right bottom->top, 43-56 top right->left; EP = 57.
const Qfn56Ep = () => {
  const o = Array.from({ length: 14 }, (_, i) => 2.6 - i * 0.4)
  return (
    <footprint>
      {o.map((y, i) => (
        <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-3.4375mm" pcbY={`${y}mm`}
          width="0.875mm" height="0.2mm" shape="rect" />
      ))}
      {o.map((x, i) => (
        <smtpad key={`b${i}`} portHints={[`${i + 15}`]} pcbX={`${-x}mm`} pcbY="-3.4375mm"
          width="0.2mm" height="0.875mm" shape="rect" />
      ))}
      {o.map((y, i) => (
        <smtpad key={`r${i}`} portHints={[`${i + 29}`]} pcbX="3.4375mm" pcbY={`${-y}mm`}
          width="0.875mm" height="0.2mm" shape="rect" />
      ))}
      {o.map((x, i) => (
        <smtpad key={`t${i}`} portHints={[`${i + 43}`]} pcbX={`${x}mm`} pcbY="3.4375mm"
          width="0.2mm" height="0.875mm" shape="rect" />
      ))}
      <smtpad portHints={["57"]} pcbX="0mm" pcbY="0mm" width="3.2mm" height="3.2mm" shape="rect" />
    </footprint>
  )
}

// KH-SMA-KE-Z — vertical THT flange jack. FIVE D1.4 holes: pad 1 = the centre
// signal pin (the continuation of the coax inner conductor), pads 2-5 = the
// four ground posts on a 5.08 mm square. The posts ARE the launch return path.
const SmaVert = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="1.9mm" holeDiameter="1.4mm" shape="circle" />
    {([[-2.54, -2.54], [2.54, -2.54], [2.54, 2.54], [-2.54, 2.54]] as const).map(([x, y], i) => (
      <platedhole key={`g${i}`} portHints={[`${i + 2}`]} pcbX={`${x}mm`} pcbY={`${y}mm`}
        outerDiameter="2.2mm" holeDiameter="1.4mm" shape="circle" />
    ))}
  </footprint>
)

// TYPE-C-31-M-12A — 16 contacts on 12 lands + 4 shell legs. RENDER-ONLY as two
// rows (the real land merges A1+B12, A4+B9, B4+A9, B1+A12 two-to-a-pad); the
// fab footprint is the project-authored pluto_rx2_8way:USB_C_Receptacle_HRO_
// TYPE-C-31-M-12A, which KiCad's stock part disagrees with by 0.375 mm on
// pad-centre-to-alignment-hole. DUAL portHints: real name + numeric alias.
const ROW_A = ["A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12"] as const
const ROW_B = ["B1", "B4", "B5", "B6", "B7", "B8", "B9", "B12"] as const
const UsbCFp = () => (
  <footprint>
    {ROW_A.map((p, i) => (
      <smtpad key={p} portHints={[p, `${i + 1}`]} pcbX={`${-3.2 + i * 0.9}mm`} pcbY="3mm"
        width="0.4mm" height="1.1mm" shape="rect" />
    ))}
    {ROW_B.map((p, i) => (
      <smtpad key={p} portHints={[p, `${i + 9}`]} pcbX={`${-3.2 + i * 0.9}mm`} pcbY="1.2mm"
        width="0.4mm" height="1.1mm" shape="rect" />
    ))}
    <platedhole portHints={["SH", "17"]} pcbX="-4.7mm" pcbY="-1mm" outerDiameter="1.4mm" holeDiameter="0.8mm" shape="circle" />
  </footprint>
)

// MCP1755S-3302E/DB — SOT-223-3. THE TAB IS PAD 4, NOT PAD 2, and KiCad ships
// both numberings; because the EP is internally tied to GND the wrong one
// still yields a WORKING board, invisible to ERC, DRC and parity and visible
// only as a jlc_twin PAD-MISMATCH. Package_TO_SOT_SMD:SOT-223 is the pad-4
// variant and is what 02_parts declares.
const Sot223Tab4 = () => (
  <footprint>
    {[-2.3, 0, 2.3].map((x, i) => (
      <smtpad key={`p${i}`} portHints={[`${i + 1}`]} pcbX={`${x}mm`} pcbY="-3.1mm"
        width="0.8mm" height="1.5mm" shape="rect" />
    ))}
    <smtpad portHints={["4"]} pcbX="0mm" pcbY="3.1mm" width="3.8mm" height="1.5mm" shape="rect" />
  </footprint>
)

// USBLC6-2SC6 — SOT23-6L. Pins 1+6 are ONE node and 3+4 are ONE node (Figure 1
// internal conductor). Wiring only pin 1 and leaving 6 open is electrically
// identical and LAYOUT-WRONG: in on 1 / out on 6 is what forces the data line
// to pass THROUGH the clamp with a zero-length stub (Figure 7).
const Sot23_6 = () => (
  <footprint>
    {[0.95, 0, -0.95].map((y, i) => (
      <smtpad key={`a${i}`} portHints={[`${i + 1}`]} pcbX="-1.1375mm" pcbY={`${y}mm`}
        width="0.6mm" height="0.55mm" shape="rect" />
    ))}
    {[-0.95, 0, 0.95].map((y, i) => (
      <smtpad key={`b${i}`} portHints={[`${i + 4}`]} pcbX="1.1375mm" pcbY={`${y}mm`}
        width="0.6mm" height="0.55mm" shape="rect" />
    ))}
  </footprint>
)

// W25Q128JVSIQ — SOIC-8 208-mil (5.3 x 5.3, P1.27). A REAL GND lead (pad 4),
// not an exposed pad.
const Soic8 = () => (
  <footprint>
    {[1.905, 0.635, -0.635, -1.905].map((y, i) => (
      <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-3.3mm" pcbY={`${y}mm`}
        width="1.5mm" height="0.6mm" shape="rect" />
    ))}
    {[-1.905, -0.635, 0.635, 1.905].map((y, i) => (
      <smtpad key={`r${i}`} portHints={[`${i + 5}`]} pcbX="3.3mm" pcbY={`${y}mm`}
        width="1.5mm" height="0.6mm" shape="rect" />
    ))}
  </footprint>
)

// ABM8-272-T3 — 3225-4Pin. Pads 2 and 4 are the can/ground.
const Xtal4 = () => (
  <footprint>
    {([[-1.1, -0.85], [1.1, -0.85], [1.1, 0.85], [-1.1, 0.85]] as const).map(([x, y], i) => (
      <smtpad key={`x${i}`} portHints={[`${i + 1}`]} pcbX={`${x}mm`} pcbY={`${y}mm`}
        width="1.2mm" height="1.05mm" shape="rect" />
    ))}
  </footprint>
)

// 2-pad POLARIZED: pad 1 = the KiCad marker end (cathode on a diode/LED).
const Pol2 = ({ w, h, dx }: { w: string; h: string; dx: string }) => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={`-${dx}`} pcbY="0mm" width={w} height={h} shape="rect" />
    <smtpad portHints={["2"]} pcbX={dx} pcbY="0mm" width={w} height={h} shape="rect" />
  </footprint>
)

// TS-1187A-B-A-B — SMD tact switch. FOUR PHYSICAL FEET, **TWO** ELECTRICAL
// NODES, and KiCad's Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A expresses
// that by giving TWO pad NUMBERS to four pads: pad "1" at (-3, -1.875) AND
// (+3, -1.875), pad "2" at (-3, +1.875) AND (+3, +1.875) — read from the
// .kicad_mod text, not assumed. The symbol therefore has TWO pins. Authoring
// four would emit pins 3 and 4 that no pad on the real footprint answers to,
// which surfaces as a schematic-parity failure at the board stage and not
// here. Both feet of each node are drawn so the render is honest about the
// mechanical anchoring.
const Tact2 = () => (
  <footprint>
    {([[-3, -1.875, "1", "a"], [3, -1.875, "1", "b"],
       [-3, 1.875, "2", "a"], [3, 1.875, "2", "b"]] as const).map(
      ([x, y, p, s]) => (
        <smtpad key={`${p}${s}`} portHints={[p]} pcbX={`${x}mm`} pcbY={`${y}mm`}
          width="1mm" height="0.75mm" shape="rect" />
      ))}
  </footprint>
)

// ===================== the board ===========================================
// 50 x 68 mm (03_src/floorplan.yaml outline). routingDisabled: tscircuit's own
// router is never our fab route (ADR-0002's two hard lines — KRT owns routing
// physics, jlc_twin owns the independent referee).

export default () => (
  <board width="50mm" height="68mm" routingDisabled>

    {/* ================================================================
        RF CORE — the SP8T, the ten SMA jacks, the RX1 pickoff.
        Pin map from Figure 22 + Table 8 (PDF p20). Three assertions in
        electrical_invariants.yaml pin the port assignment (ADR-0006) and
        three more pin the control plane (ADR-0005), because NONE of it is
        observable in copper: RF8 was chosen by an isolation argument, RF1
        is the delta reference for the whole published phase table, and
        V1-as-MSB is what stops the antenna sweep running backwards (an AoA
        solver absorbs a reversed sweep as a ROTATED ARRAY).
        LS (pin 1) is on GND, not on a pulled-down net: it has a 1 Mohm
        INTERNAL PULL-UP (Table 5 fn 1) so a float selects the COMPLEMENTED
        half of the truth table and the board still sweeps eight antennas in
        a plausible order. Table 3 fn 1 also makes it an RF GROUND.
        NC (pin 20) is tied to GND per Table 8 fn 2 — it sits between RF8 and
        GND inside the RF fan, so grounding it closes the via fence there.
        ================================================================ */}
    <chip name="U_SW" supplierPartNumbers={{ jlcpcb: ["C5121458"] }}
      pinLabels={{
        pin1: "LS", pin2: "RF2", pin3: "GND", pin4: "RF3", pin5: "GND", pin6: "RF4",
        pin7: "GND", pin8: "VDD", pin9: "V1", pin10: "V2", pin11: "V3", pin12: "V4",
        pin13: "RF5", pin14: "GND", pin15: "RF6", pin16: "GND", pin17: "RF7",
        pin18: "GND", pin19: "RF8", pin20: "NC", pin21: "GND", pin22: "RFC",
        pin23: "GND", pin24: "RF1", pin25: "EP",
      }}
      connections={{
        pin1: "net.GND", pin2: "net.ANT2", pin3: "net.GND", pin4: "net.ANT3",
        pin5: "net.GND", pin6: "net.ANT4", pin7: "net.GND", pin8: "net.N3V3",
        pin9: "net.SW_V1", pin10: "net.SW_V2", pin11: "net.SW_V3", pin12: "net.SW_V4",
        pin13: "net.ANT5", pin14: "net.GND", pin15: "net.ANT6", pin16: "net.GND",
        pin17: "net.ANT7", pin18: "net.GND", pin19: "net.RX1_TAP", pin20: "net.GND",
        pin21: "net.GND", pin22: "net.RX2_OUT", pin23: "net.GND", pin24: "net.ANT1",
        pin25: "net.GND",
      }}
      footprint={<Qfn24Ep />} />

    {/* Seven ordinary elements. Every jack: pad 1 = signal, pads 2-5 = the
        four ground posts, each of which gets its own via cluster at the pad
        (ARCHITECTURE sec 6 — the posts are the launch's return path and are
        only electrically short if the return is). */}
    {[1, 2, 3, 4, 5, 6, 7].map((k) => (
      <chip key={`ant${k}`} name={`J_ANT${k}`} supplierPartNumbers={{ jlcpcb: ["C504007"] }}
        pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
        connections={{
          pin1: `net.ANT${k}`, pin2: "net.GND", pin3: "net.GND",
          pin4: "net.GND", pin5: "net.GND",
        }}
        footprint={<SmaVert />} />
    ))}

    {/* J_ANT8 is THE RX1 ANTENNA, not an eighth dedicated element (BRIEF P2).
        Its jack, the RX1-out jack and the pickoff arm meet at ONE node
        (DETAIL_DESIGN sec 3): Z0 = 50, Rs = R_T1 + R_T2 = 440, Rp = 490
        => tap|port -20.26 dB, main-line IL 0.432 dB, RL 26.28 dB. */}
    <chip name="J_ANT8" supplierPartNumbers={{ jlcpcb: ["C504007"] }}
      pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
      connections={{
        pin1: "net.RX1_MAIN", pin2: "net.GND", pin3: "net.GND",
        pin4: "net.GND", pin5: "net.GND",
      }}
      footprint={<SmaVert />} />
    <chip name="J_RX1" supplierPartNumbers={{ jlcpcb: ["C504007"] }}
      pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
      connections={{
        pin1: "net.RX1_MAIN", pin2: "net.GND", pin3: "net.GND",
        pin4: "net.GND", pin5: "net.GND",
      }}
      footprint={<SmaVert />} />
    <chip name="J_RX2" supplierPartNumbers={{ jlcpcb: ["C504007"] }}
      pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
      connections={{
        pin1: "net.RX2_OUT", pin2: "net.GND", pin3: "net.GND",
        pin4: "net.GND", pin5: "net.GND",
      }}
      footprint={<SmaVert />} />

    {/* THE PICKOFF IS A SERIES PAIR BY DECISION, NOT BY CONVENIENCE (ADR-0002,
        user-confirmed as BRIEF A6). Two 220 ohm 0402s put their ~0.04 pF
        parasitics in SERIES: C_eff halves, the 6 GHz tap tilt drops from
        +1.69 dB to +0.43 dB, and — the number that actually justifies the
        second resistor — the UNKNOWN band narrows from 2.73 dB to 0.83 dB.
        A single 440 ohm part satisfies the topology in spirit and destroys
        the property, so the chain is machine-asserted, and so is each value:
        the netlist, DRC, ERC and parity are IDENTICAL for any resistance. */}
    <resistor name="R_T1" resistance="220" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [R220] }}
      connections={{ pin1: "net.RX1_MAIN", pin2: "net.RX1_TAP_MID" }} />
    <resistor name="R_T2" resistance="220" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [R220] }}
      connections={{ pin1: "net.RX1_TAP_MID", pin2: "net.RX1_TAP" }} />

    {/* ================================================================
        CONTROL PLANE (ADR-0005). 47 ohm SOURCE terminations at the MCU end
        and 10 k pull-downs at the SWITCH end.
        The 47 ohm is not a convention: PE42482A-X's digital absolute maximum
        is 3.6 V on a 3.3 V rail (300 mV), the CTRL line is 67 ohm, and the
        far-end peak is 2*Vdd*Z/(Z+Zdrv+Rs) = 4.81 V without it and 3.18 V
        with it at the RP2040's STRONGEST drive. Protection that lives in a
        firmware register is not protection.
        The pull-downs are MANDATORY: V1-V4 have NO internal pull of any kind
        (5 uA max input current, Table 2), so all four float during reset and
        supply ramp — and a floating V4 selects the ALL-PORTS-TERMINATED state
        and SILENTLY MUTES the receiver.
        Power-on default = 0000 = RF1, a real antenna, not the mute state and
        not dependent on the MCU's pad-reset behaviour.
        NO SHUNT CAPACITANCE ANYWHERE ON THIS CLASS: a 1k + 1nF RC is 4.6 us
        to 99%, more than the entire 4.267 us blanking allowance.
        ================================================================ */}
    {[1, 2, 3, 4].map((k) => (
      <resistor key={`rs${k}`} name={`R_S${k}`} resistance="47" footprint="0402" supplierPartNumbers={{ jlcpcb: [R47] }}
        connections={{ pin1: `net.SEL_V${k}`, pin2: `net.SW_V${k}` }} />
    ))}
    {[1, 2, 3, 4].map((k) => (
      <resistor key={`rpd${k}`} name={`R_PD${k}`} resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: [R10K] }}
        connections={{ pin1: `net.SW_V${k}`, pin2: "net.GND" }} />
    ))}
    {/* U_SW VDD bypass at pin 8, span <= 3 mm. IDD is 120 uA typ, so this is
        decoupling for CONTROL-LINE transients, not for load current — which is
        exactly why it has to be AT the pad to be anything at all. */}
    <capacitor name="C_SW1" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_SW2" capacitance="1uF" footprint="0603" supplierPartNumbers={{ jlcpcb: [C1U0603] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ================================================================
        SEQUENCER — RP2040. Select lines are GPIO12..GPIO15 (pins 15-18):
        four CONSECUTIVE GPIOs on the side rotation 180 turns toward the
        switch, because ADR-0005 requires all bits written in ONE PIO
        instruction and a PIO OUT/SET writes a CONTIGUOUS pin range.
        Non-consecutive pins force a read-modify-write, which is exactly the
        transient the ADR forbids.
        TESTEN (19) to GND — "Factory test mode pin. Tie to GND" (Table 1).
        The 26 unused GPIOs and the two SWD pins carry no net and become
        explicit ERC no-connect flags.
        SWCLK/SWDIO ARE DELIBERATELY LEFT OPEN AND THAT IS A DECISION, NOT AN
        OVERSIGHT: nets.yaml (gated at stage 3) declares no net for either,
        the firmware path is UF2 over USB-C, and both pins have specified
        internal pull-ups at reset. Reversing it costs two test pads and a
        nets.yaml line; it is recorded in the stage-4 journal.
        ================================================================ */}
    <chip name="U_MCU" supplierPartNumbers={{ jlcpcb: ["C2040"] }}
      pinLabels={{
        pin1: "IOVDD", pin10: "IOVDD", pin15: "GPIO12", pin16: "GPIO13",
        pin17: "GPIO14", pin18: "GPIO15", pin19: "TESTEN", pin20: "XIN",
        pin21: "XOUT", pin22: "IOVDD", pin23: "DVDD", pin24: "SWCLK",
        pin25: "SWDIO", pin26: "RUN", pin33: "IOVDD", pin37: "GPIO25",
        pin42: "IOVDD", pin43: "ADC_AVDD", pin44: "VREG_VIN", pin45: "VREG_VOUT",
        pin46: "USB_DM", pin47: "USB_DP", pin48: "USB_VDD", pin49: "IOVDD",
        pin50: "DVDD", pin51: "QSPI_SD3", pin52: "QSPI_SCLK", pin53: "QSPI_SD0",
        pin54: "QSPI_SD2", pin55: "QSPI_SD1", pin56: "QSPI_SS_N", pin57: "GND",
      }}
      connections={{
        pin1: "net.N3V3", pin10: "net.N3V3", pin22: "net.N3V3", pin33: "net.N3V3",
        pin42: "net.N3V3", pin49: "net.N3V3",
        pin15: "net.SEL_V1", pin16: "net.SEL_V2", pin17: "net.SEL_V3",
        pin18: "net.SEL_V4",
        pin19: "net.GND", pin20: "net.XIN", pin21: "net.XOUT",
        pin23: "net.DVDD_1V1", pin50: "net.DVDD_1V1", pin45: "net.DVDD_1V1",
        pin26: "net.RUN_N", pin37: "net.LED_STAT",
        pin43: "net.N3V3", pin44: "net.N3V3", pin48: "net.N3V3",
        pin46: "net.USB_DM_MCU", pin47: "net.USB_DP_MCU",
        pin51: "net.QSPI_SD3", pin52: "net.QSPI_SCLK", pin53: "net.QSPI_SD0",
        pin54: "net.QSPI_SD2", pin55: "net.QSPI_SD1", pin56: "net.QSPI_CSN",
        pin57: "net.GND",
      }}
      footprint={<Qfn56Ep />} />

    {/* TEN 100 nF, one per power pin — SIX IOVDD (1, 10, 22, 33, 42, 49), TWO
        DVDD (23, 50), USB_VDD (48), ADC_AVDD (43). DETAIL_DESIGN sec 5 budgeted
        FOUR until 2026-07-28. Raspberry Pi's own minimal design runs NINE and
        says WHY it compromised (two-layer board, "not a lot of room on that
        side"); this board is four-layer and has no such excuse. C_MCU7 and
        C_MCU8 sit on DVDD_1V1, the 1.1 V core rail — NOT on 3V3. */}
    {[1, 2, 3, 4, 5, 6].map((k) => (
      <capacitor key={`cm${k}`} name={`C_MCU${k}`} capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
        connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    ))}
    <capacitor name="C_MCU7" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.DVDD_1V1", pin2: "net.GND" }} />
    <capacitor name="C_MCU8" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.DVDD_1V1", pin2: "net.GND" }} />
    <capacitor name="C_MCU9" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_MCU10" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* THE ON-DIE 1.1 V REGULATOR'S TWO MANDATORY CAPACITORS (sec 2.10.1, PDF
        p157: "The regulator must have 1uF capacitors placed close to its input
        (VREG_VIN) and output (VREG_VOUT) pins"). Missing from DETAIL_DESIGN
        sec 5 until 2026-07-28. C_VREG_OUT is the DVDD_1V1 rail's only bulk. */}
    <capacitor name="C_VREG_IN" capacitance="1uF" footprint="0603" supplierPartNumbers={{ jlcpcb: [C1U0603] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_VREG_OUT" capacitance="1uF" footprint="0603" supplierPartNumbers={{ jlcpcb: [C1U0603] }}
      connections={{ pin1: "net.DVDD_1V1", pin2: "net.GND" }} />

    {/* CRYSTAL. R_XTAL is CONDITIONALLY required, and both conditions hold
        here: the RP2040 HD guide sec 2.3 (PDF p11) specifies a 1 k series
        resistor on XOUT when the crystal's ESR max is <= 50 ohm AND IOVDD is
        3.3 V. ABM8-272-T3 is a 50 ohm part and this board is 3.3 V. It sits
        between the XOUT PIN and the crystal terminal, and the XOUT-side load
        capacitor sits on the CRYSTAL side of it (Figure 8) — which is why
        XOUT_XTAL is its own net.
        15 pF is C0G/NP0 and the DIELECTRIC IS PART OF THE VALUE: "15 pF 0402"
        is orderable as X7R, whose capacitance moves with bias and temperature,
        on a load capacitance that sets oscillator start-up margin.
        The value survived two corrected inputs: C_L is CITED at 10 pF (drawing
        456603 Rev B p1) and C_stray is 3 pF (Raspberry Pi's own worked number
        for this exact chip), and 2*(10-3) = 14 => 15 pF E24, identical to the
        old 2*(12-5). Recorded because the next person would otherwise
        re-derive 10 pF from a C_stray with no source and UNDER-LOAD it. */}
    <chip name="Y_XTAL" supplierPartNumbers={{ jlcpcb: ["C20625731"] }}
      pinLabels={{ pin1: "XTAL_A", pin2: "GND", pin3: "XTAL_B", pin4: "GND" }}
      connections={{
        pin1: "net.XIN", pin2: "net.GND", pin3: "net.XOUT_XTAL", pin4: "net.GND",
      }}
      footprint={<Xtal4 />} />
    <resistor name="R_XTAL" resistance="1k" footprint="0402" supplierPartNumbers={{ jlcpcb: [R1K] }}
      connections={{ pin1: "net.XOUT", pin2: "net.XOUT_XTAL" }} />
    <capacitor name="C_XTAL1" capacitance="15pF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C15P] }}
      connections={{ pin1: "net.XIN", pin2: "net.GND" }} />
    <capacitor name="C_XTAL2" capacitance="15pF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C15P] }}
      connections={{ pin1: "net.XOUT_XTAL", pin2: "net.GND" }} />

    {/* QSPI XIP FLASH. Note the pad order on the RP2040 is SD3, SCLK, SD0,
        SD2, SD1, SS_N (pins 51-56) — the four data lines are NOT in numerical
        order and SCLK sits BETWEEN SD3 and SD0, so laying the flash out by
        numerical order produces crossings the reference design does not have.
        This bus is the board's ONLY continuous in-band spur source, 25 mm from
        a nine-arm receive fan, so "short" is an EMI rule here and not only a
        signal-integrity one. */}
    <chip name="U_FLASH" supplierPartNumbers={{ jlcpcb: ["C97521"] }}
      pinLabels={{
        pin1: "CSn", pin2: "DO_IO1", pin3: "WP_IO2", pin4: "GND",
        pin5: "DI_IO0", pin6: "CLK", pin7: "HOLD_IO3", pin8: "VCC",
      }}
      connections={{
        pin1: "net.QSPI_CSN", pin2: "net.QSPI_SD1", pin3: "net.QSPI_SD2",
        pin4: "net.GND", pin5: "net.QSPI_SD0", pin6: "net.QSPI_SCLK",
        pin7: "net.QSPI_SD3", pin8: "net.N3V3",
      }}
      footprint={<Soic8 />} />
    <capacitor name="C_FLASH" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* BOOT + RESET. QSPI_SS_N is ALSO the boot strap and it is sampled ONCE
        (sec 2.8.1: "Check if SPI CS pin is tied low"). The strap is 1 kohm and
        NOT 0 ohm because QSPI_SS is a driven OUTPUT in normal operation and the
        button would otherwise be a hard drive-fight into the pad.
        R_CSPU IS POPULATED, NOT DNF, AND THAT IS A DEPARTURE FROM RASPBERRY
        PI'S REFERENCE WITH A REASON. Their R2 is marked DNF because with this
        exact flash family the RP2040's own 50-80 k internal pull-up suffices —
        a BOM-cost optimisation on a mass-produced board. But W25Q128JV sec 9.3
        (PDF p62) requires /CS to TRACK VCC on the supply ramp, and the HD guide
        itself concedes "there is a short period of time during switch-on where
        the state of the QSPI_SS pin cannot be guaranteed". A DNF footprint is
        also the blank-LCSC CPL class that shipped 13 rows on cooksense v1.1,
        and this board would otherwise have ZERO unpopulated parts. Populating
        costs 3.3 V / 10 k = 0.33 mA against a 150 mA envelope. Divider check
        against the strap: 10 k (|| the internal 50-80 k) over R_BOOT's 1 k puts
        BOOTSEL at ~0.3 V, far below V_IL.
        RUN has a specified 50-80 k internal pull-up, so a button to GND is a
        complete reset circuit and needs no external pull. Do NOT copy ADR-0005's
        external-pull-down reasoning onto this pin: that reasoning exists because
        PE42482A-X publishes NO internal pull at all. */}
    <resistor name="R_CSPU" resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: [R10K] }}
      connections={{ pin1: "net.QSPI_CSN", pin2: "net.N3V3" }} />
    <resistor name="R_BOOT" resistance="1k" footprint="0402" supplierPartNumbers={{ jlcpcb: [R1K] }}
      connections={{ pin1: "net.QSPI_CSN", pin2: "net.BOOTSEL_N" }} />
    <chip name="SW_BOOT" supplierPartNumbers={{ jlcpcb: [SW_JLC] }}
      pinLabels={{ pin1: "SW_A", pin2: "SW_B" }}
      connections={{ pin1: "net.BOOTSEL_N", pin2: "net.GND" }}
      footprint={<Tact2 />} />
    <chip name="SW_RUN" supplierPartNumbers={{ jlcpcb: [SW_JLC] }}
      pinLabels={{ pin1: "SW_A", pin2: "SW_B" }}
      connections={{ pin1: "net.RUN_N", pin2: "net.GND" }}
      footprint={<Tact2 />} />

    {/* ================================================================
        USB-C ENTRY — power in, and the ONLY non-power job this port has is
        BOOTSEL/UF2 firmware load.
        THE STRAP IS NON-NEGOTIABLE: A6<->B6 = USB_DP and A7<->B7 = USB_DM.
        A Type-C plug is REVERSIBLE, so in one insertion the cable's D+ lands
        on A6 and in the other on B6. A board that wires one pair enumerates
        one way round and is DEAD the other, and NOTHING sees it — every pin
        has a net so ERC passes, the copper is legal so DRC passes, and the
        netlist is self-consistent so schematic-parity passes. Same defect
        CLASS as the reversed XT60 and the usb-hub-3s D1 cathode. The strap is
        electrically FREE: full-speed 12 Mbit/s with ~4 ns edges makes a 3 mm
        T-stub ~20 ps of skew.
        SBU1 (A8) and SBU2 (B8) are REAL PADS and are left OPEN — explicit ERC
        no-connect, no trace, no via, no test point. Do NOT ground them: the
        Type-C spec requires a device with no alternate mode and no audio
        accessory to leave SBU unconnected, and a grounded SBU misdeclares the
        port AND gives an ESD strike a path INTO the board. It is also what
        makes the 2-channel ESD array's coverage argument sound — an isolated
        pad with nothing behind it has no victim.
        SH bonds DIRECTLY to GND, all four legs, each with its own via at the
        pad. No 1M||4.7nF break: this board has ONE ground (GND is poured and
        stitched on all four layers and carries no netclass), so there is no
        second domain to isolate from and the network would break nothing while
        inserting ~34 ohm at 1 GHz into the ESD return path. The stainless shell
        is ~40x the resistivity of copper — the METAL is not the bond, the four
        plated legs are.
        ================================================================ */}
    <chip name="J_USB" supplierPartNumbers={{ jlcpcb: ["C5337088"] }}
      pinLabels={{
        pin1: "GND_A1", pin2: "VBUS_A4", pin3: "CC1", pin4: "DP1", pin5: "DN1",
        pin6: "SBU1", pin7: "VBUS_A9", pin8: "GND_A12", pin9: "GND_B1",
        pin10: "VBUS_B4", pin11: "CC2", pin12: "DP2", pin13: "DN2", pin14: "SBU2",
        pin15: "VBUS_B9", pin16: "GND_B12", pin17: "SHIELD",
      }}
      connections={{
        pin1: "net.GND", pin2: "net.VBUS", pin3: "net.USB_CC1",
        pin4: "net.USB_DP", pin5: "net.USB_DM",
        // pin6 = SBU1 (A8): NO NET, by decision — emitted as an ERC no-connect
        pin7: "net.VBUS", pin8: "net.GND", pin9: "net.GND", pin10: "net.VBUS",
        pin11: "net.USB_CC2", pin12: "net.USB_DP", pin13: "net.USB_DM",
        // pin14 = SBU2 (B8): NO NET, by decision — emitted as an ERC no-connect
        pin15: "net.VBUS", pin16: "net.GND", pin17: "net.GND",
      }}
      footprint={<UsbCFp />} />

    {/* Rd = 5.1 k on BOTH CC lines. This is a PROTECTION part, not plumbing
        (ADR-0004): two 5.1 k pull-downs advertise the board as a plain 5 V
        sink, which is what makes the sustained-overvoltage case (a PD source
        at 9/15/20 V) UNREACHABLE rather than survivable — and the USBLC6's own
        survival depends on it, because its VBR is 6 V MIN and 9 V on VBUS makes
        it conduct CONTINUOUSLY into a die rated for microsecond pulses.
        BOTH are required: one Rd advertises a sink in ONE insertion
        orientation, the same invisible half-dead failure as an unstrapped
        D+/D-. Both values are machine-asserted, because a wrong one is
        electrically undetectable on the bench until a PD charger is plugged in. */}
    <resistor name="R_CC1" resistance="5.1k" footprint="0402" supplierPartNumbers={{ jlcpcb: [R5K1] }}
      connections={{ pin1: "net.USB_CC1", pin2: "net.GND" }} />
    <resistor name="R_CC2" resistance="5.1k" footprint="0402" supplierPartNumbers={{ jlcpcb: [R5K1] }}
      connections={{ pin1: "net.USB_CC2", pin2: "net.GND" }} />

    {/* ESD ARRAY. Pins 1+6 are ONE node (USB_DP) and 3+4 are ONE node
        (USB_DM) — a straight internal conductor, so putting them on DIFFERENT
        nets would be a latent short no gate could see. Both ends of each are
        authored on the same net; the IN-on-1 / OUT-on-6 dress is a LAYOUT
        intent recorded in the floorplan and the ADR, invisible here.
        PIN 5 IS ON VBUS_F — the decision ADR-0008 exists to make, and the one
        thing stage 2 deliberately left open. C_ESD is ST Figure 18's CBUS and
        was in NEITHER dossier's power to add.
        Pin 2 is the SINGLE ground pin and carries the ENTIRE surge return; by
        ST sec 2.2's arithmetic a 10 mm ground trace alone costs 144 V of clamp,
        so it takes its own via to the L2 plane AT the pad. */}
    <chip name="U_ESD" supplierPartNumbers={{ jlcpcb: ["C7519"] }}
      pinLabels={{
        pin1: "IO1_in", pin2: "GND", pin3: "IO2_in", pin4: "IO2_out",
        pin5: "VBUS", pin6: "IO1_out",
      }}
      connections={{
        pin1: "net.USB_DP", pin2: "net.GND", pin3: "net.USB_DM",
        pin4: "net.USB_DM", pin5: "net.VBUS_F", pin6: "net.USB_DP",
      }}
      footprint={<Sot23_6 />} />
    <capacitor name="C_ESD" capacitance="100nF" footprint="0402" supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.VBUS_F", pin2: "net.GND" }} />

    {/* 27.4 ohm series terminations, REQUIRED not suggested (RP2040 Table 620
        and Table 614 both: "27 ohm series resistor required for USB
        operation"). 27.4 because 27 is not an E24 value and 27.4 1% is what
        Raspberry Pi's reference was measured with. Bus pull-ups/pull-downs are
        INTERNAL and must NOT be added. These split each data line, which is
        why the pair is FOUR nets: connector side USB_DP/USB_DM through U_ESD,
        die side USB_DP_MCU/USB_DM_MCU. */}
    <resistor name="R_USB1" resistance="27.4" footprint="0402" supplierPartNumbers={{ jlcpcb: [R27R4] }}
      connections={{ pin1: "net.USB_DP", pin2: "net.USB_DP_MCU" }} />
    <resistor name="R_USB2" resistance="27.4" footprint="0402" supplierPartNumbers={{ jlcpcb: [R27R4] }}
      connections={{ pin1: "net.USB_DM", pin2: "net.USB_DM_MCU" }} />

    {/* ================================================================
        POWER CHAIN (ADR-0004): VBUS -[F_IN]- VBUS_F -[FB_IN]- VBUS_LDO -> 3V3.
        THE FUSE IS UPSTREAM OF THE CLAMP, deliberately: a TVS that fails SHORT
        must open the fuse rather than burn on the host's current budget. That
        ordering is only checkable as a CHAIN, which is why both series links
        are series_chain invariants rather than prose.
        D_TVS PAD 1 IS THE CATHODE and it clamps VBUS_F, not raw VBUS. This is
        the exact geometry of the usb-hub-3s v1.0 D1 defect, which passed ERC,
        DRC, parity, twin AND pin review because every artifact was
        consistently wrong together. The invariant asserting it was itself
        written BACKWARDS at stage 3 (D_TVS.2) and corrected at the stage-2
        merge — a gate that asserts the defect it was written to prevent is
        worse than no gate.
        6.0 V standoff, not 5.0: Littelfuse defines V_R as the maximum voltage
        appliable WITHOUT operation and USB-C vSafe5V runs to 5.50 V, so a
        5.0 V part leaks ~1.26 mA at 5.25 V against ~47 uA for this one.
        FB_IN is a SERIES element and therefore makes VBUS_LDO a distinct net.
        A pour that bridged VBUS_F to VBUS_LDO would short the ferrite out
        completely and nothing else could see it: DRC clean (same-net copper),
        ERC clean, parity clean, and the board works.
        ================================================================ */}
    <chip name="F_IN" supplierPartNumbers={{ jlcpcb: ["C2154056"] }}
      pinLabels={{ pin1: "IN", pin2: "OUT" }}
      connections={{ pin1: "net.VBUS", pin2: "net.VBUS_F" }}
      footprint={<Pol2 w="1.15mm" h="1.8mm" dx="1.5mm" />} />
    <chip name="D_TVS" supplierPartNumbers={{ jlcpcb: ["C83270"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VBUS_F", pin2: "net.GND" }}
      footprint={<Pol2 w="2.2mm" h="2.3mm" dx="2.15mm" />} />
    <capacitor name="C_BULK" capacitance="4.7uF" footprint="0805" supplierPartNumbers={{ jlcpcb: [C4U7] }}
      connections={{ pin1: "net.VBUS_F", pin2: "net.GND" }} />
    <chip name="FB_IN" supplierPartNumbers={{ jlcpcb: ["C3716677"] }}
      pinLabels={{ pin1: "1", pin2: "2" }}
      connections={{ pin1: "net.VBUS_F", pin2: "net.VBUS_LDO" }}
      footprint={<Pol2 w="0.9mm" h="1.45mm" dx="0.95mm" />} />

    {/* MCP1755S-3302E/DB, SOT-223-3. Three HARD constraints, all cleared by
        2.7x / 7.3 V / 3.1x: dropout <= 1.23 V at 0.15 A (500 mV max at the
        part's RATED 300 mA); V_IN abs max >= 10.3 V (+17.6 V, and 16.0 V
        OPERATING so it stays IN REGULATION through a clamp event rather than
        merely surviving); theta_JA <= 195 C/W (62 C/W).
        The 1.23 V is not the naive 4.75 - 3.40 = 1.35: F_IN (R_1max 0.75 ohm)
        and FB_IN (DCR 0.06) drop 121.5 mV at 0.15 A ahead of the pass element,
        and that CHANGED THE ANSWER — AMS1117-3.3, the obvious JLC-Basic
        default, is 1.3 V max and passes 1.35 while failing 1.23.
        C_LDI must be >= C_LDO (DS20005160B sec 4.4 p17) and is met AT EQUALITY,
        the boundary of the rule; C_BULK does not help because FB_IN sits
        between them. Both are 0805 because the 1 uF floor is on EFFECTIVE
        capacitance at 3.3 V bias and a 1 uF X7R 0402 can derate below it. */}
    <capacitor name="C_LDI" capacitance="1uF" footprint="0805" supplierPartNumbers={{ jlcpcb: [C1U0805] }}
      connections={{ pin1: "net.VBUS_LDO", pin2: "net.GND" }} />
    <chip name="U_LDO" supplierPartNumbers={{ jlcpcb: ["C638611"] }}
      pinLabels={{ pin1: "VIN", pin2: "GND", pin3: "VOUT", pin4: "EP" }}
      connections={{
        pin1: "net.VBUS_LDO", pin2: "net.GND", pin3: "net.N3V3", pin4: "net.GND",
      }}
      footprint={<Sot223Tab4 />} />
    <capacitor name="C_LDO" capacitance="1uF" footprint="0805" supplierPartNumbers={{ jlcpcb: [C1U0805] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ================================================================
        INDICATORS. 680 ohm gives (3.3 - 2.0)/680 = 1.91 mA, so the LED must be
        a Vf ~2.0 V part — a green/blue at Vf 2.6-3.1 V would be a DIFFERENT
        design, not a colour preference.
        LED_PWR is on the 3V3 rail: dark means the LDO is not delivering, which
        on this board means the USB-C protection chain opened.
        LED_ST is driven from GPIO25 and is the firmware's own heartbeat — the
        cheapest evidence that the PIO frame is running at all, on a board
        whose output is otherwise only visible on a spectrum analyser.
        Pad 1 is the CATHODE on both (KiCad LED_SMD marks pad 1 with the F.Fab
        chamfer and the F.SilkS band). ================================ */}
    <resistor name="R_LED1" resistance="680" footprint="0402" supplierPartNumbers={{ jlcpcb: [R680] }}
      connections={{ pin1: "net.N3V3", pin2: "net.LED_PWR" }} />
    <chip name="LED_PWR" supplierPartNumbers={{ jlcpcb: [LED_JLC] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.GND", pin2: "net.LED_PWR" }}
      footprint={<Pol2 w="0.7mm" h="0.9mm" dx="0.75mm" />} />
    <resistor name="R_LED2" resistance="680" footprint="0402" supplierPartNumbers={{ jlcpcb: [R680] }}
      connections={{ pin1: "net.LED_STAT", pin2: "net.LED_STAT_A" }} />
    <chip name="LED_ST" supplierPartNumbers={{ jlcpcb: [LED_JLC] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.GND", pin2: "net.LED_STAT_A" }}
      footprint={<Pol2 w="0.7mm" h="0.9mm" dx="0.75mm" />} />

  </board>
)

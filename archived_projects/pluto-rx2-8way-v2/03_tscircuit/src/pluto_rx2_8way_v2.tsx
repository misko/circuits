// pluto-rx2-8way-v2 — the MODULE arm of an 8-element antenna selector for
// angle-of-arrival on an ADALM-PlutoPlus RX2. THE BOARD, authored in tscircuit
// (repo ADR-0001/0002).
//
// v1 (projects/pluto-rx2-8way) is the BARE-CHIP arm. It is NOT superseded and
// is not written to. v2 changes exactly ONE variable — the MCU is a pre-built
// Waveshare RP2040-Zero module instead of a bare RP2040 — and holds every RF
// decision of v1 fixed so the two boards can be compared.
//
// THE MEASUREMENT THAT MOTIVATED THIS BOARD (taken on v1's own .kicad_pcb):
// nineteen named nets leave v1's QFN-56, and exactly FIVE of them are the
// board's function (SEL_V1..V4, LED_STAT). The other fourteen are the chip
// keeping itself alive — QSPI x6, XIN/XOUT, USB_DM/DP, RUN_N, DVDD_1V1, 3V3,
// GND. Seventy-four per cent of the escape demand on the hardest package on
// the board bought nothing the board sells. This file is what happens when
// Ossmann's rule 2 ("use the most integrated components you can find") is
// actually followed.
//
// The circuit is derived in 01_docs/{ARCHITECTURE,DETAIL_DESIGN}.md and the
// three ADRs. NOTHING is re-derived here — this file is the capture.
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
//     generate_board hard-errors.
//  3. The digit-leading rails 3V3 and 3V3_MOD are authored `N3V3`/`N3V3_MOD`;
//     the converter's canon_net strips a single leading N that GUARDS A DIGIT.
//     net_aliases.txt states BOTH mappings explicitly anyway, because
//     rules/nets.yaml keys its netclasses on the CANONICAL names and on this
//     board a netclass miss is an IMPEDANCE or an AMPACITY defect.
//  4. NO ALPHANUMERIC PADS EXIST ON THIS BOARD. v1's only such part was the
//     USB-C receptacle (A1..B12 + SH), which tscircuit drops SILENTLY with ERC
//     still 0; ADR-0002 deleted that connector, so the hazard left with it.
//     tsx_preflight.py and count_parity.py are run anyway — see
//     parity_padmap.txt for why an empty mapping file is not the same as a
//     gate nobody ran.
//  5. Two-pad POLARIZED parts (LED_ST) are authored as <chip> with pad 1 =
//     CATHODE, matching the KiCad footprint marker convention, so no
//     generic-symbol reversal can ship. This is the usb-hub-3s v1.0 D1 defect
//     class: symbol, footprint, netlist and board were consistently WRONG
//     together and only INTENT disagreed.
//  6. Exposed pads are authored as real pads (U_SW.25).
//
// THREE THINGS THIS FILE IS THE FIRST ARTIFACT TO CARRY:
//   * 3V3_MOD exists as its OWN net. FB_3V3 is a SERIES element, so the node
//     on the module side is NOT the same net as the node at the switch. v1
//     learned this the hard way with VBUS_LDO, which was missing from its
//     netclass until a late merge and would have been graded as a signal
//     while carrying the whole rail. Here the consequence is worse than a
//     width: merging them DELETES THE ONLY FILTER on the board, and DRC, ERC
//     and parity all pass.
//   * The module's `5V` pad (pad 1) is DELIBERATELY UNCONNECTED. This board
//     has no power entry of its own (ADR-0002); the module's own USB-C is the
//     only port. Connecting 5V to anything would create a second power path.
//   * SEL_V1..SEL_V4 are GP0..GP3 — four CONSECUTIVE GPIOs that are also
//     PHYSICALLY ADJACENT AND IN ORDER down the module's right edge. A PIO
//     `out pins, 4` writes a CONTIGUOUS pin range in ONE instruction;
//     non-consecutive pins force a read-modify-write, and the whole level
//     change has to land inside the 4.267 us blanking allowance. This is why
//     RP2040-Zero was chosen over XIAO RP2040, whose GP0..GP4 are contiguous
//     in NUMBER but scrambled in SPACE (pads D6, D7, D8, D10, D9).
// ===========================================================================

// ---- LCSC codes. Named constants because several serve more than one refdes
// and a divergence between two instances would be a sourcing defect nothing
// else catches.
const SW_JLC = "C5121458"    // PE42482A-X   SP8T absorptive DC-8 GHz, QFN-24
const SMA_JLC = "C504007"    // KH-SMA-KE-Z  vertical THT flange jack, x10
const MOD_JLC = "C9900173620" // RP2040-Zero-NoLogo — a C99* CONSIGN placeholder.
// ^ NOT A STOCK NUMBER AND NOT A BUYABLE LINE. C99* codes are JLC's
//   consigned-sourcing placeholders and are permanently stock 0 BY
//   CONSTRUCTION. It is here because it is the code JLC's assembly line uses to
//   place a module WE SHIP THEM onto footprint LCC-23(18x23.5).
//   See 03_src/rules/assembly.yaml `consigned:` and ADR-0002.
const R220 = "C25091"        // 0402WGF2200TCE   220R +/-1%  0402  base
const R47 = "C137864"        // RC0402JR-0747RL   47R +/-5%  0402
const R680 = "C137948"       // RC0402FR-07680RL 680R        0402
const R10K = "C60490"        // RC0402FR-0710KL   10k        0402  ledger-vetted
// ^ WAS C25744 (UniOhm 0402WGF1002TCE) until 2026-07-31. C25744 is BUYABLE BUT
//   NOT AT OUR QUANTITY: JLC's selectSmtComponentList returns minPurchaseNum
//   779 against our need of 20 (4 refdes x 5 boards), with canPresaleNumber
//   -6,175,510 — its 30,949 catalog units are already oversubscribed by six
//   million, which is why the minimum jumped. jlc_stock_check.py reads
//   stockCount ONLY (blind spot #73), so A-STOCK reported PASS on a line that
//   cannot be ordered as budgeted. C60490 is the same 10k +/-1% 62.5 mW 0402,
//   already in the vetted ledger, minPurchaseNum 1.
//   COST OF THE SWAP: C60490 is `expand` where C25744 was `base`, so this line
//   now carries an extended-part setup fee. Recorded in ORDER_README section 1.
const C100N = "C1525"        // CL05B104KO5NNNC 100nF X7R    0402  ledger-vetted
const C1U0603 = "C15849"     // CL10A105KB8NNNC   1uF        0603  ledger-vetted
const C4U7 = "C1779"         // CL21A475KAQNNNE  4.7uF       0805  ledger-vetted
const FB_JLC = "C3716677"    // BLM21SP601SN1D  600R@100MHz  0805
const LED_JLC = "C2286"      // KT-0603R RED 0603 (Vf 1.8-2.4 V, no typical)

// ---- footprints ----------------------------------------------------------

// PE42482A-X — QFN-24 4x4 P0.5 + a 2.70 mm square exposed pad. 1-6 left
// top->bottom, 7-12 bottom left->right, 13-18 right bottom->top, 19-24 top
// right->left; EP = 25. Pin-1 dot at the TOP-LEFT corner (Figure 22, PDF p20).
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

// KH-SMA-KE-Z — vertical THT flange jack. FIVE D1.4 holes: pad 1 = the centre
// signal pin (the continuation of the coax inner conductor), pads 2-5 = the
// four ground posts on a 5.08 mm square. The posts ARE the launch return path
// and are only electrically short if the return is.
// D1.4 AND NOT D1.3: a 0.9 mm SQUARE post has a 1.273 mm diagonal, so D1.3
// leaves 0.014 mm radial clearance — inside JLC's plated-hole tolerance. The
// vendor drawing's own PCB-layout inset says 5-D1.4.
const SmaVert = () => (
  <footprint>
    <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="1.9mm" holeDiameter="1.4mm" shape="circle" />
    {([[-2.54, -2.54], [2.54, -2.54], [2.54, 2.54], [-2.54, 2.54]] as const).map(([x, y], i) => (
      <platedhole key={`g${i}`} portHints={[`${i + 2}`]} pcbX={`${x}mm`} pcbY={`${y}mm`}
        outerDiameter="2.2mm" holeDiameter="1.4mm" shape="circle" />
    ))}
  </footprint>
)

// RP2040-Zero — 18.00 x 23.50 mm castellated module, 23 pads at 2.54 mm on
// three edges. The USB-C is on the FOURTH (top) edge, which carries no pads.
//
// PAD NUMBERING IS OURS AND IS DECLARED HERE, because the vendor labels the
// pads by FUNCTION and does not number them. We walk the perimeter the way a
// QFN does, starting at the top-left and going DOWN the left edge:
//     1..9   left edge,   top -> bottom   (5V, GND, 3V3, GP29, 28, 27, 26, 15, 14)
//     10..14 bottom edge, left -> right   (GP13, GP12, GP11, GP10, GP9)
//     15..23 right edge,  bottom -> top   (GP8 .. GP0)
// The GPIO sequence is then ONE CONTINUOUS DECREASING RUN from GP29 to GP0
// around the perimeter, which is a useful self-check on the read: any single
// transposition breaks the monotonicity.
//
// Geometry, from Waveshare's own dimension drawing: 2.54 mm pitch, first side
// pad 1.59 mm from the top edge (so the nine side pads span 20.32 mm and sit
// symmetrically), bottom row first pad 3.92 mm in (five pads span 10.16 mm,
// also symmetric). Corroborated INDEPENDENTLY by JLC's own footprint name for
// this part: `LCC-23(18x23.5)` — 23 pads, 18 x 23.5 mm.
//
// Lands are drawn straddling the module edge, half under the castellation and
// half outside it, which is the standard castellated-module land and what the
// Raspberry Pi Pico datasheet's own SMT footprint does (it also warns that the
// paste stencil must be OVER-pasted relative to the land).
// PAD NUMBERING IS THE VENDOR'S AND IT RUNS CLOCKWISE FROM THE TOP-RIGHT — the
// MIRROR of every IC. Top view, USB-C up: pad 1 (GP0) is the TOPMOST pad of the
// RIGHT edge; 1..9 down the right edge; 10..14 right-to-left along the bottom;
// 15..23 up the left edge to 5V at top-left. Cited from the Waveshare schematic
// sheet "Pin Out" (header P1, "Header 23") and corroborated by the wiki FAQ,
// which calls VSYS "Pin23" and 3V3 "Pin 21".
// AN EARLIER REVISION OF THIS FILE NUMBERED THEM COUNTER-CLOCKWISE FROM THE
// TOP-LEFT, which is the EXACT REVERSE (ours = 24 - vendor) and produced a
// perfect mirror image that assembles, powers up, and reads every GPIO on the
// wrong pad. It was withdrawn 2026-07-30. See 02_parts/RP2040-Zero/part.yaml.
// Pad geometry must stay identical to
// 03_src/lib/pluto_rx2_8way_v2.pretty/RP2040_Zero_LCC23_18x23.5.kicad_mod:
// 2.60 x 1.20 straddling the module edge 1.00 outboard / 1.60 inboard, so the
// centre sits 0.30 mm INBOARD of the edge (x = +/-8.70, y = -11.45).
const Rp2040Zero = () => {
  const sideY = Array.from({ length: 9 }, (_, i) => 10.16 - i * 2.54)  // top -> bottom
  const botX = Array.from({ length: 5 }, (_, i) => 5.08 - i * 2.54)    // right -> left
  return (
    <footprint>
      {sideY.map((y, i) => (
        <smtpad key={`r${i}`} portHints={[`${i + 1}`]} pcbX="8.70mm" pcbY={`${y}mm`}
          width="2.6mm" height="1.2mm" shape="rect" />
      ))}
      {botX.map((x, i) => (
        <smtpad key={`b${i}`} portHints={[`${i + 10}`]} pcbX={`${x}mm`} pcbY="-11.45mm"
          width="1.2mm" height="2.6mm" shape="rect" />
      ))}
      {sideY.map((y, i) => (
        <smtpad key={`l${i}`} portHints={[`${23 - i}`]} pcbX="-8.70mm" pcbY={`${y}mm`}
          width="2.6mm" height="1.2mm" shape="rect" />
      ))}
    </footprint>
  )
}

// KT-0603R — 0603 indicator LED. Authored as a <chip>, NOT a <led>, so PAD 1
// IS EXPLICITLY THE CATHODE (the KiCad footprint marker convention). A generic
// two-pin symbol on a polarized footprint is invisible to DRC, ERC, netlist
// and parity — every artifact is self-consistently wrong together.
const Pol2 = () => (
  <footprint>
    <smtpad portHints={["1"]} pcbX="-0.7875mm" pcbY="0mm" width="0.9mm" height="0.95mm" shape="rect" />
    <smtpad portHints={["2"]} pcbX="0.7875mm" pcbY="0mm" width="0.9mm" height="0.95mm" shape="rect" />
  </footprint>
)

// ===================== the board ===========================================
// 50 x 68 mm, carried from v1 as a STARTING outline. The star geometry (ten
// SMA jacks around one switch) dominates it and is unchanged; what changed is
// that v1's MCU field — a QFN-56 plus flash, crystal, USB-C, two switches and
// ten decouplers — collapsed to one 18 x 23.5 mm module. The final outline is
// a STAGE-5 decision and may shrink. routingDisabled: tscircuit's own router
// is never our fab route (ADR-0002's two hard lines — KRT owns routing
// physics, jlc_twin owns the independent referee).

export default () => (
  <board width="50mm" height="68mm" routingDisabled>

    {/* ================================================================
        RF CORE — the SP8T, the ten SMA jacks, the RX1 pickoff.
        Pin map from Figure 22 + Table 8 (PDF p20). Assertions in
        electrical_invariants.yaml pin the port assignment and the control
        plane, because NONE of it is observable in copper: RF8 was chosen by
        an isolation argument, RF1 is the delta reference for the whole
        published phase table, and V1-as-MSB is what stops the antenna sweep
        running backwards (an AoA solver absorbs a reversed sweep as a
        ROTATED ARRAY and reports a plausible wrong answer).
        LS (pin 1) is on GND, not on a pulled-down net: it has a 1 Mohm
        INTERNAL PULL-UP (Table 5 fn 1) so a float selects the COMPLEMENTED
        half of the truth table and the board still sweeps eight antennas in
        a plausible order. Table 3 fn 1 also makes it an RF GROUND.
        NC (pin 20) is tied to GND per Table 8 fn 2 — it sits between RF8 and
        GND inside the RF fan, so grounding it closes the via fence there.
        ================================================================ */}
    <chip name="U_SW" supplierPartNumbers={{ jlcpcb: [SW_JLC] }}
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
      <chip key={`ant${k}`} name={`J_ANT${k}`} supplierPartNumbers={{ jlcpcb: [SMA_JLC] }}
        pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
        connections={{
          pin1: `net.ANT${k}`, pin2: "net.GND", pin3: "net.GND",
          pin4: "net.GND", pin5: "net.GND",
        }}
        footprint={<SmaVert />} />
    ))}

    {/* J_ANT8 is THE RX1 ANTENNA, not an eighth dedicated element. Its jack,
        the RX1-out jack and the pickoff arm meet at ONE node (DETAIL_DESIGN
        sec 2): Z0 = 50, Rs = R_T1 + R_T2 = 440, Rp = 490 => tap -20.2567 dB,
        main-line IL 0.4322 dB, RL 26.2773 dB — all three RE-DERIVED for this
        board from the topology alone, and all three agreeing with v1 to the
        last published digit. */}
    <chip name="J_ANT8" supplierPartNumbers={{ jlcpcb: [SMA_JLC] }}
      pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
      connections={{
        pin1: "net.RX1_MAIN", pin2: "net.GND", pin3: "net.GND",
        pin4: "net.GND", pin5: "net.GND",
      }}
      footprint={<SmaVert />} />
    <chip name="J_RX1" supplierPartNumbers={{ jlcpcb: [SMA_JLC] }}
      pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
      connections={{
        pin1: "net.RX1_MAIN", pin2: "net.GND", pin3: "net.GND",
        pin4: "net.GND", pin5: "net.GND",
      }}
      footprint={<SmaVert />} />
    <chip name="J_RX2" supplierPartNumbers={{ jlcpcb: [SMA_JLC] }}
      pinLabels={{ pin1: "RF", pin2: "GND", pin3: "GND", pin4: "GND", pin5: "GND" }}
      connections={{
        pin1: "net.RX2_OUT", pin2: "net.GND", pin3: "net.GND",
        pin4: "net.GND", pin5: "net.GND",
      }}
      footprint={<SmaVert />} />

    {/* THE PICKOFF IS A SERIES PAIR BY DECISION, NOT BY CONVENIENCE. Two
        220 ohm 0402s put their ~0.04 pF parasitics in SERIES: C_eff halves,
        the 6 GHz tap tilt drops from +1.69 dB to +0.43 dB, and — the number
        that actually justifies the second resistor — the UNKNOWN band narrows
        from 2.73 dB to 0.83 dB. A single 440 ohm part satisfies the topology
        in spirit and destroys the property, so the chain is machine-asserted
        and so is EACH value: the netlist, DRC, ERC and parity are IDENTICAL
        for any resistance. */}
    <resistor name="R_T1" resistance="220" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [R220] }}
      connections={{ pin1: "net.RX1_MAIN", pin2: "net.RX1_TAP_MID" }} />
    <resistor name="R_T2" resistance="220" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [R220] }}
      connections={{ pin1: "net.RX1_TAP_MID", pin2: "net.RX1_TAP" }} />

    {/* ================================================================
        CONTROL PLANE. 47 ohm SOURCE terminations at the MODULE end and 10 k
        pull-downs at the SWITCH end.
        The 47 ohm is not a convention: PE42482A-X's digital absolute maximum
        is 3.6 V on a 3.3 V rail (300 mV of headroom), the CTRL line is
        ~67 ohm, and the far-end peak is 2*Vdd*Z/(Z+Zdrv+Rs) = 4.807 V without
        it and 3.181 V with it at the RP2040's STRONGEST drive. Protection
        that lives in a firmware register is not protection.
        THE MODULE MAKES THIS MORE NECESSARY, NOT LESS: the line is now our
        copper PLUS the module's internal trace from the RP2040 pad to the
        castellation, so the electrical length grows. The driver silicon is
        identical, so Zdrv is unchanged and 47 ohm carries over.
        The pull-downs are MANDATORY: V1-V4 have NO internal pull of any kind
        (5 uA max input current, Table 2), so all four float during reset and
        supply ramp — and a floating V4 selects the ALL-PORTS-TERMINATED state
        and SILENTLY MUTES the receiver.
        Power-on default = 0000 = RF1, a real antenna, not the mute state and
        not dependent on the module's pad-reset behaviour.
        NO SHUNT CAPACITANCE ANYWHERE ON THIS CLASS: a 1k + 1nF RC is 4.6 us
        to 99%, more than the entire 4.267 us blanking allowance.
        ================================================================ */}
    {[1, 2, 3, 4].map((k) => (
      <resistor key={`rs${k}`} name={`R_S${k}`} resistance="47" footprint="0402"
        supplierPartNumbers={{ jlcpcb: [R47] }}
        connections={{ pin1: `net.SEL_V${k}`, pin2: `net.SW_V${k}` }} />
    ))}
    {[1, 2, 3, 4].map((k) => (
      <resistor key={`rpd${k}`} name={`R_PD${k}`} resistance="10k" footprint="0402"
        supplierPartNumbers={{ jlcpcb: [R10K] }}
        connections={{ pin1: `net.SW_V${k}`, pin2: "net.GND" }} />
    ))}

    {/* ================================================================
        SWITCH SUPPLY. The board's ENTIRE power tree is these four parts,
        because it has no power connector of its own (ADR-0002): the only
        input is the module's 3V3 castellation.
        FB_3V3 IS THE ONE PLACE THIS BOARD'S SUPPLY MEETS ITS RF PART. The
        RP2040's core and QSPI current transients ride the module's 3V3 rail,
        and PE42482A-X publishes NO PSRR figure. It is an RF measure, not a
        protection measure — v1's ferrite sat on VBUS and did a different job.
        3V3_MOD and 3V3 ARE TWO NETS. A ferrite is a SERIES element. Merging
        them deletes the only filter on the board and every gate still passes.
        C_SW1/C_SW2 sit AT pin 8, span <= 3 mm. IDD is 120 uA typ, so this is
        decoupling for CONTROL-LINE transients, not for load current — which
        is exactly why it has to be AT the pad to be anything at all.
        ================================================================ */}
    <chip name="FB_3V3" supplierPartNumbers={{ jlcpcb: [FB_JLC] }}
      pinLabels={{ pin1: "IN", pin2: "OUT" }}
      connections={{ pin1: "net.N3V3_MOD", pin2: "net.N3V3" }}
      footprint="0805" />
    <capacitor name="C_BULK" capacitance="4.7uF" footprint="0805"
      supplierPartNumbers={{ jlcpcb: [C4U7] }}
      connections={{ pin1: "net.N3V3_MOD", pin2: "net.GND" }} />
    <capacitor name="C_SW1" capacitance="100nF" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [C100N] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />
    <capacitor name="C_SW2" capacitance="1uF" footprint="0603"
      supplierPartNumbers={{ jlcpcb: [C1U0603] }}
      connections={{ pin1: "net.N3V3", pin2: "net.GND" }} />

    {/* ================================================================
        THE SEQUENCER — and on this board it is ONE PART.
        Waveshare RP2040-Zero, CONSIGNED (ADR-0002): no Pico-class RP2040
        module is machine-placeable from JLC stock, so we ship the modules and
        JLC places them. It stays ON the CPL — consignment is a SOURCING
        class, not a population class.
        WHY THIS MODULE AND NOT A PICO (ADR-0001): the Pico's 3V3 comes from an
        RT6150 buck-boost SMPS whose PS pin (GPIO23) defaults to PFM — a
        VARIABLE, load-dependent switching frequency, which is the worst spur
        shape next to a receiver because it cannot be planned around.
        RP2040-Zero uses an RT9013-33 LDO: no inductor anywhere on Waveshare's
        schematic, and Richtek market it as "Ultra-Low-Noise for RF
        Application". The objection is resolved by SELECTION, not mitigation —
        there is no GPIO23 to hold high, no PWM-forcing firmware, no +/-20%
        f_OSC spread to plan around, and no unsupported 3V3-backfeed hack.
        SELECT LINES ARE GP0..GP3 (pads 23, 22, 21, 20): four consecutive
        GPIOs that are also physically adjacent and in order down the right
        edge, because a PIO `out pins, 4` writes a CONTIGUOUS pin range in ONE
        instruction and the whole level change must land inside the 4.267 us
        blanking allowance.
        PAD 1 (5V) IS DELIBERATELY UNCONNECTED — see the header. Fifteen
        further GPIO pads are unconnected because this board needs five
        signals; that is the entire point of the module, and it is also the
        module's one real cost: those pads are soldered down and cannot be
        probed. A future revision wanting debug access must bring them out
        BEFORE the board is built, not after.
        ================================================================ */}
    <chip name="U_MCU" supplierPartNumbers={{ jlcpcb: [MOD_JLC] }}
      /* VENDOR NUMBERING. NOTE THE TRAP: the silkscreen prints GPIO numbers,
         not pad numbers, and they agree for SIXTEEN CONSECUTIVE PADS (1..16 =
         GP0..GP15) before diverging at pad 17. Sixteen agreements is exactly
         long enough to convince a reviewer the mapping is the identity. */
      pinLabels={{
        pin1: "GP0", pin2: "GP1", pin3: "GP2", pin4: "GP3", pin5: "GP4",
        pin6: "GP5", pin7: "GP6", pin8: "GP7", pin9: "GP8", pin10: "GP9",
        pin11: "GP10", pin12: "GP11", pin13: "GP12", pin14: "GP13",
        pin15: "GP14", pin16: "GP15", pin17: "GP26", pin18: "GP27",
        pin19: "GP28", pin20: "GP29", pin21: "3V3", pin22: "GND", pin23: "5V",
      }}
      connections={{
        pin22: "net.GND",
        pin21: "net.N3V3_MOD",
        pin5: "net.LED_STAT",
        pin4: "net.SEL_V4",
        pin3: "net.SEL_V3",
        pin2: "net.SEL_V2",
        pin1: "net.SEL_V1",
      }}
      footprint={<Rp2040Zero />} />

    {/* Status LED. Driven from GP4, so it loads a MODULE pin and is NOT on
        this board's 3V3 net. KT-0603R publishes Vf 1.8 V min / 2.4 V max at
        IF = 20 mA and NO TYPICAL, so the current is a RANGE by construction:
        2.206 / 1.912 / 1.324 mA across the bin.
        LED_ST pad 1 = CATHODE (goes to GND), pad 2 = anode. */}
    <resistor name="R_LED" resistance="680" footprint="0402"
      supplierPartNumbers={{ jlcpcb: [R680] }}
      connections={{ pin1: "net.LED_STAT", pin2: "net.LED_STAT_A" }} />
    <chip name="LED_ST" supplierPartNumbers={{ jlcpcb: [LED_JLC] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.GND", pin2: "net.LED_STAT_A" }}
      footprint={<Pol2 />} />

  </board>
)

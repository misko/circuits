// usb-hub-3s-v3 (rev v1.6) — PROPRIETARY 3S-LiPo POWER-DISTRIBUTION board.
//
// v1.6 REVISION — STATUS LEDs (the only schematic change; everything else in v1.6
// is copper, footprint or paperwork). Five indicators, +11 placements, +2 BOM
// lines: D8 amber = PACK LIVE (FET-gated by Q8 off ENKILL, because SW1 switches
// ENABLE and there is no switched power node to tap); D9/D10/D11 green = PER-PORT
// USB-A, tapped on VBUSA1/2/3 POST the TPS2557 switches so a latched-off port
// reads dark; D12 green = USB-C, tapped on VBUSC POST Q6+F2 so a dark C LED means
// the ADR-0002 protection chain opened. Ballasts are 6.98k C23215 and the gate FET
// is C78284 — both already on this BOM (R7/R16 and Q7), so five new placements
// cost ZERO new feeders. See the block below the buck cells.
//
// v1.2 REVISION — DISCRETE VBUS PROTECTION (BRIEF A2/D2, user decision). The v1.1
// TPS26631 eFuse was over-built for a 5V/5A Pi rail and root-caused BOTH the board
// routing wall (its 20-pin HTSSOP IN_SYS pin boxed in the fine-pitch west escape)
// AND v1.1's two order-blockers. It is DROPPED and replaced by a simple discrete
// chain (reusing the on-BOM Q6/Q7 FETs):
//   5VC -> Q6 (AON6403 P-FET, reverse-block, ENABLE-GATED via Q7 BSS138 off ENKILL)
//        -> PMID -> F2 (PPTC polyfuse ~6A, over-current)
//        -> VBUSC (protected connector; D5 TVS to GND, over-voltage) -> J5
//  - Reverse-current: Q6 body diode (D=5VC/S=PMID) blocks VBUS->pack back-feed when
//    Q6 is OFF; Q7 inverts ENKILL so Q6 is ON (low-drop forward) when the hub is on
//    and OFF on master-off (RT-T4, OFF-state). No gate Zener (Vgs<=5.4V << 20V max).
//  - Over-current: F2 PPTC polyfuse (resettable). Over-voltage: D5 TVS crowbar +
//    F2 trip on a buck-fail-high.
//  - KEPT from v1.1: buck-C FB on LOCAL 5VC (R12=4.12k -> 5VC 5.352V; the runaway
//    fix). REVERTED: buck-C EN re-merged to ENKILL (the eFuse FLT->EN_C un-merge +
//    D6 coupling diode are gone). REMOVED: U13, R31/R32/R33/R36, C51/C52, D6, D7.
//
// NOT a USB hub, NOT USB-PD / USB-standards-compliant: it is a Pi-DEDICATED
// power supply. 3x USB-A = dumb 5V CHARGING ports (2A cont / 2.5A burst,
// TPS2557 + TPS2513A DCP advertisement, NO data). 1x USB-C = a proprietary
// PROTECTED 5V rail for a RASPBERRY PI 4 ONLY, at the Pi 4's official 5V/3A
// (15W). v1.6 CORRECTION (ADR-0004): this read 'Pi 5 ... PSU_MAX_CURRENT=5000'.
// That is a Pi 5 bootloader-EEPROM setting and DOES NOT EXIST ON A PI 4 -- a Pi 4
// does not negotiate PD for its power input at all, so a plain regulated 5V rail
// is its NATIVE interface, not an override. The board stays PROVISIONED for 5A
// (buck, F2, VBUSC vias) -- deliberate over-provisioning, not a contradiction.
// Powered from a PROTECTED 3S pack + balance charger ONLY.
//
// v3 = v2 MINUS the routing-hard TPS25740A PD cell (ADR-0001): the USB-C rail
// is a regulated buck output, not a PD-negotiated one. Removed vs v2: U1
// (TPS25740A), the v2 PD pass FETs, RS3 5mR sense, and every PD-config passive.
//
// v1.1 REVISION (this file) — targeted hardening of the sealed v1.0:
//  1. PROTECTED VBUS: a TPS26631 eFuse (U13) + reverse-current-blocking FET
//     pair (Q6 AON6354 power FET + Q7 BSS138 fast gate-pulldown, per datasheet
//     SLVSE94G 8.3.5/8.3.6) between the 5VC buck and J5 VBUS — adjustable
//     current limit (R_ILIM 3.09k -> 5.83A), ~5.9V input-OV cutoff (OVP
//     divider), 10nF dVdT soft-start, MODE->GND auto-retry, and reverse-current
//     blocking (stops a powered sink back-feeding the pack, red-team RT-T4).
//  2. FB: (v1.1 sensed VBUSC post-eFuse; SUPERSEDED by v1.2 item A above — buck-C
//     FB now senses LOCAL 5VC. Buck-A keeps sensing its own 5VA output.)
//  3. MASTER OFF: SS12D07 slide switch (SW1) grounds the ENKILL bus -> buck-A off
//     directly + buck-C off via the D6 EN_C->ENKILL coupling diode + eFuse off,
//     kills the mA quiescent Iq.
//     ^ SUPERSEDED BY v1.2 (see the v1.2 block above): D6, EN_C and the eFuse are
//       GONE. Both bucks' EN pins sit directly on ENKILL. Kept as the dated v1.1
//       record; do NOT read it as current intent. (A stale sibling of this note at
//       SW1 itself was still describing D6 as live and was corrected in v1.8 after
//       a zero-context pin review caught it.)
//  4. CAPS: buck input MLCC 25V->50V (C77102), buck output MLCC 6.3V->10V (C84455).
//  5. SNUBBERS: optional-populate RC (2.2R + 1nF C0G) on each LM5116 SW node.
//
// ALL-BUCK (E-TOPO green): two proven LM5116 5V bucks (ADR-0010): buck A -> 5VA
// (USB-A, 6A), buck C -> 5VC -> eFuse -> USB-C VBUS (5A). v1's IP6559 buck-boost
// is GONE. (Board name stays usb_hub_3s_v2 for source continuity.)
//
// AUTHORING RULES honoured (03_tscircuit/contracts.md):
//  - every pin bound with connections={{...}} to explicit net.NAME (parity by
//    construction); leading-digit rails authored N5VA/N5VC -> converter strips
//    the N guard -> canon 5VA/5VC.
//  - every specialty part carries supplierPartNumbers (the 02_parts FPID handle).
//  - alphanumeric pads (J5 A1..B12/SH, J2-4 SH) carry DUAL portHints.
//  - polarized 2-pad parts (diodes, TVS, polymer caps) authored as <chip> with
//    pad 1 = CATHODE (diodes) / POSITIVE (caps), matching the KiCad footprint
//    marker convention, so no generic-symbol reversal can ship.
//
// Circuit derivation: 01_docs/ARCHITECTURE.md + DETAIL_DESIGN.md; buck values are
// v1's proven 5V/7A LM5116 design reused verbatim (both bucks fit inside 7A).

// ---- shared tiny footprints (render-only; fab footprints come from 02_parts FPIDs) ----

const Dfn56 = () => (
  <footprint>
    <smtpad portHints={["1"]} pcbX="-1.905mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["2"]} pcbX="-0.635mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["3"]} pcbX="0.635mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["4"]} pcbX="1.905mm" pcbY="-2.4mm" width="0.99mm" height="0.99mm" shape="rect" />
    <smtpad portHints={["5"]} pcbX="0mm" pcbY="1.1mm" width="4.4mm" height="3.9mm" shape="rect" />
  </footprint>
)

// 2-pad polarized: pad 1 = cathode (diode) / positive (polymer cap) — KiCad marker side
const Pol2 = ({ w, h, dx }: { w: string; h: string; dx: string }) => (
  <footprint>
    <smtpad portHints={["1"]} pcbX={`-${dx}`} pcbY="0mm" width={w} height={h} shape="rect" />
    <smtpad portHints={["2"]} pcbX={dx} pcbY="0mm" width={w} height={h} shape="rect" />
  </footprint>
)

// LM5116 HTSSOP-20-EP footprint (v1-proven): 10 pads/side @ 0.65mm + EP pad 21
const Lm5116Fp = () => (
  <footprint>
    {Array.from({ length: 10 }, (_, i) => (
      <smtpad key={`l${i}`} portHints={[`${i + 1}`]} pcbX="-2.9mm" pcbY={`${(4.5 * 0.65) - i * 0.65}mm`} width="1.35mm" height="0.4mm" shape="rect" />
    ))}
    {Array.from({ length: 10 }, (_, i) => (
      <smtpad key={`r${i}`} portHints={[`${i + 11}`]} pcbX="2.9mm" pcbY={`${-(4.5 * 0.65) + i * 0.65}mm`} width="1.35mm" height="0.4mm" shape="rect" />
    ))}
    <smtpad portHints={["21"]} pcbX="0mm" pcbY="0mm" width="3.4mm" height="6.5mm" shape="rect" />
  </footprint>
)

// TPS2557 VSON-8 footprint (v1-proven): 4 pads/side @ 0.65mm + EP pad 9
const Tps2557Fp = () => (
  <footprint>
    {Array.from({ length: 4 }, (_, i) => (
      <smtpad key={`a${i}`} portHints={[`${i + 1}`]} pcbX="-1.5mm" pcbY={`${0.975 - i * 0.65}mm`} width="0.8mm" height="0.35mm" shape="rect" />
    ))}
    {Array.from({ length: 4 }, (_, i) => (
      <smtpad key={`b${i}`} portHints={[`${i + 5}`]} pcbX="1.5mm" pcbY={`${-0.975 + i * 0.65}mm`} width="0.8mm" height="0.35mm" shape="rect" />
    ))}
    <smtpad portHints={["9"]} pcbX="0mm" pcbY="0mm" width="1.65mm" height="2.4mm" shape="rect" />
  </footprint>
)

// LM5116 buck cell — one instance per rail. `s` = net suffix (A/C), `vout` = the
// output net (N5VA/N5VC), `ids` = the refdes for every part in the cell.
const Buck = ({ s, vout, ids, fbsense, en, fbtop, fbtopMpn }: {
  s: string; vout: string; fbsense?: string; en?: string; fbtop: string; fbtopMpn?: string;
  ids: {
    U: string; QH: string; QL: string; RS: string; L: string; DB: string;
    RT: string; FBT: string; FBB: string; RCMP: string; UVT: string; UVB: string;
    REN: string; RCSK: string; RCSG: string;
    CRAMP: string; CCMZ: string; CCMP: string; CSS: string; CBOOT: string; CVCC: string;
    CIN: string[]; CINH: string; COUT: string[];
    RSNB: string; CSNB: string;
  };
}) => {
  const n = (x: string) => `net.${x}_${s}`
  // v1.1: FB top senses `fbsense` if given (buck-C -> VBUSC connector, option-a),
  // else the buck output vout (buck-A). EN merges to `en` (ENKILL master-off bus).
  const fbNet = fbsense ? `net.${fbsense}` : `net.${vout}`
  const enNet = en ? `net.${en}` : n("EN")
  return (
    <group name={`buck${s}`}>
      <chip name={ids.U} supplierPartNumbers={{ jlcpcb: ["C13755"] }}
        pinLabels={{
          pin1: "VIN", pin2: "UVLO", pin3: "RT", pin4: "EN", pin5: "RAMP",
          pin6: "AGND", pin7: "SS", pin8: "FB", pin9: "COMP", pin10: "VOUT",
          pin11: "DEMB", pin12: "CS", pin13: "CSG", pin14: "PGND", pin15: "LO",
          pin16: "VCC", pin17: "VCCX", pin18: "HB", pin19: "HO", pin20: "SW",
          pin21: "EP",
        }}
        connections={{
          pin1: "net.VIN", pin2: n("UVLO"), pin3: n("RT"), pin4: enNet,
          pin5: n("RAMP"), pin6: "net.GND", pin7: n("SS"), pin8: n("FB"),
          pin9: n("COMP"), pin10: `net.${vout}`, pin11: "net.GND", pin12: n("CSF"),
          pin13: n("CSGF"), pin14: "net.GND", pin15: n("LO"), pin16: n("VCC"),
          pin17: "net.GND", pin18: n("BOOT"), pin19: n("HO"), pin20: n("SW"),
          pin21: "net.GND",
        }}
        footprint={<Lm5116Fp />} />
      {/* power pair: QH HS (D=VIN S=SW G=HO), QL LS (D=SW S=CS G=LO); Rs 10m CS->GND */}
      <chip name={ids.QH} supplierPartNumbers={{ jlcpcb: ["C404363"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: n("SW"), pin2: n("SW"), pin3: n("SW"), pin4: n("HO"), pin5: "net.VIN" }}
        footprint={<Dfn56 />} />
      <chip name={ids.QL} supplierPartNumbers={{ jlcpcb: ["C404363"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: n("CS"), pin2: n("CS"), pin3: n("CS"), pin4: n("LO"), pin5: n("SW") }}
        footprint={<Dfn56 />} />
      <resistor name={ids.RS} resistance="0.01" footprint="2512" supplierPartNumbers={{ jlcpcb: ["C127692"] }}
        connections={{ pin1: n("CS"), pin2: "net.GND" }} />
      <inductor name={ids.L} inductance="6.8uH" supplierPartNumbers={{ jlcpcb: ["C408523"] }}
        connections={{ pin1: n("SW"), pin2: `net.${vout}` }}
        footprint={<Pol2 w="4mm" h="11.4mm" dx="4.85mm" />} />
      {/* boot diode VCC->HB (cathode pad1 at HB) + boot cap HB-SW + VCC cap */}
      <chip name={ids.DB} supplierPartNumbers={{ jlcpcb: ["C2128"] }}
        pinLabels={{ pin1: "K", pin2: "A" }}
        connections={{ pin1: n("BOOT"), pin2: n("VCC") }}
        footprint={<Pol2 w="0.6mm" h="1mm" dx="1.25mm" />} />
      <capacitor name={ids.CBOOT} capacitance="1uF" footprint="0603" connections={{ pin1: n("BOOT"), pin2: n("SW") }} />
      <capacitor name={ids.CVCC} capacitance="1uF" footprint="0603" connections={{ pin1: n("VCC"), pin2: "net.GND" }} />
      {/* input caps 4x 10uF/50V 1210 (v1.1: 25V->50V, GRM32ER71H106KA12L C77102) + 100n */}
      {ids.CIN.map((c) => (
        <capacitor key={c} name={c} capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77102"] }} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
      ))}
      <capacitor name={ids.CINH} capacitance="100nF" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
      {/* output caps 4x 100uF/10V 1210 (v1.1: 6.3V->10V, GRM32ER61A107ME20L C84455) */}
      {ids.COUT.map((c) => (
        <capacitor key={c} name={c} capacitance="100uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C84455"] }} connections={{ pin1: `net.${vout}`, pin2: "net.GND" }} />
      ))}
      {/* control small parts: RT, RAMP, FB divider, comp, SS, UVLO divider, EN, CS 0R pair */}
      <resistor name={ids.RT} resistance="12.4k" footprint="0603" connections={{ pin1: n("RT"), pin2: "net.GND" }} />
      <capacitor name={ids.CRAMP} capacitance="330pF" footprint="0603" connections={{ pin1: n("RAMP"), pin2: "net.GND" }} />
      {/* v1.2: FB top per-buck (fbtop/fbtopMpn). pin1 senses fbNet. LM5116 Vref
          1.215V, FB-bot 1.21k -> Vout = 1.215*(1+Rtop/1.21).
          buck-A: 3.92k (C728591) -> 5.151V on 5VA (local; USB-A window-centred).
          buck-C (v1.2 LOCAL-SENSE fix): 4.12k -> 5.352V on 5VC (local, NOT VBUSC).
          The v1.1 VBUSC (post-eFuse) sense caused the FB-integrator RUNAWAY when
          the eFuse limited/opened (loop wound 5VC toward VIN). Sensing LOCAL 5VC
          makes 5VC unconditionally regulated; the +0.2V setpoint bump covers the
          eFuse+FET drop (~0.17-0.24V @5A) so the connector still delivers >=5.0V. */}
      <resistor name={ids.FBT} resistance={fbtop} footprint="0603"
        {...(fbtopMpn ? { supplierPartNumbers: { jlcpcb: [fbtopMpn] } } : {})}
        connections={{ pin1: fbNet, pin2: n("FB") }} />
      <resistor name={ids.FBB} resistance="1.21k" footprint="0603" connections={{ pin1: n("FB"), pin2: "net.GND" }} />
      <resistor name={ids.RCMP} resistance="18k" footprint="0603" connections={{ pin1: n("COMP"), pin2: n("CMZ") }} />
      <capacitor name={ids.CCMZ} capacitance="3.3nF" footprint="0603" connections={{ pin1: n("CMZ"), pin2: n("FB") }} />
      <capacitor name={ids.CCMP} capacitance="100pF" footprint="0603" connections={{ pin1: n("COMP"), pin2: n("FB") }} />
      <capacitor name={ids.CSS} capacitance="10nF" footprint="0603" connections={{ pin1: n("SS"), pin2: "net.GND" }} />
      <resistor name={ids.UVT} resistance="49.9k" footprint="0603" connections={{ pin1: "net.VIN", pin2: n("UVLO") }} />
      <resistor name={ids.UVB} resistance="6.98k" footprint="0603" connections={{ pin1: n("UVLO"), pin2: "net.GND" }} />
      {/* v1.1: EN pull-up 100k -> VIN lands on enNet (ENKILL merged master-off bus) */}
      <resistor name={ids.REN} resistance="100k" footprint="0603" connections={{ pin1: "net.VIN", pin2: enNet }} />
      {/* CS kelvin 0R links: chip CS pin (CSF) -R- Rs top (CS); chip CSG pin (CSGF) -R- GND */}
      <resistor name={ids.RCSK} resistance="0" footprint="0603" connections={{ pin1: n("CS"), pin2: n("CSF") }} />
      <resistor name={ids.RCSG} resistance="0" footprint="0603" connections={{ pin1: "net.GND", pin2: n("CSGF") }} />
      {/* v1.1 SW-node RC snubber (OPTIONAL-POPULATE / DNP by default): fit only if
          bench shows SW ring. R 2.2R 1206 (C137327) in series with C 1nF C0G 0805
          (C62774), SW -> GND. Tune R~=sqrt(Lpar/Cpar) on the bench. */}
      <resistor name={ids.RSNB} resistance="2.2" footprint="1206" supplierPartNumbers={{ jlcpcb: ["C137327"] }} connections={{ pin1: n("SW"), pin2: n("SNUB") }} />
      <capacitor name={ids.CSNB} capacitance="1nF" footprint="0805" supplierPartNumbers={{ jlcpcb: ["C62774"] }} connections={{ pin1: n("SNUB"), pin2: "net.GND" }} />
    </group>
  )
}

export default () => (
  <board width="100mm" height="80mm" routingDisabled>
    {/* ================= INPUT: XT60 -> fuse -> reverse-polarity P-FET -> VIN ================= */}
    <chip name="J1" supplierPartNumbers={{ jlcpcb: ["C98732"] }}
      pinLabels={{ pin1: "MINUS", pin2: "PLUS" }}
      connections={{ pin1: "net.GND", pin2: "net.VBAT" }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="0mm" pcbY="0mm" outerDiameter="6mm" holeDiameter="4mm" shape="circle" />
          <platedhole portHints={["2"]} pcbX="7.2mm" pcbY="0mm" outerDiameter="6mm" holeDiameter="4mm" shape="circle" />
        </footprint>
      } />
    {/* F1 10A MINI blade fuse holder (Keystone 3568) — hand-solder; blade fuse separate */}
    <chip name="F1" supplierPartNumbers={{ jlcpcb: ["C5249699"] }}
      pinLabels={{ pin1: "IN", pin2: "OUT" }}
      connections={{ pin1: "net.VBAT", pin2: "net.VBAT_F" }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="-5mm" pcbY="0mm" outerDiameter="3.5mm" holeDiameter="1.9mm" shape="circle" />
          <platedhole portHints={["2"]} pcbX="5mm" pcbY="0mm" outerDiameter="3.5mm" holeDiameter="1.9mm" shape="circle" />
        </footprint>
      } />
    {/* Q1 reverse-polarity P-FET: D=VBAT_F (battery side), S=VIN, body diode conducts on first contact */}
    <chip name="Q1" supplierPartNumbers={{ jlcpcb: ["C2760089"] }}
      pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
      connections={{ pin1: "net.VIN", pin2: "net.VIN", pin3: "net.VIN", pin4: "net.RPP_G", pin5: "net.VBAT_F" }}
      footprint={<Dfn56 />} />
    <resistor name="R1" resistance="100k" footprint="0603" connections={{ pin1: "net.RPP_G", pin2: "net.GND" }} />
    {/* D2 zener S->G clamp: cathode (pad1) at SOURCE=VIN, anode at gate */}
    <chip name="D2" supplierPartNumbers={{ jlcpcb: ["C173429"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VIN", pin2: "net.RPP_G" }}
      footprint={<Pol2 w="0.9mm" h="1.2mm" dx="1.65mm" />} />
    {/* D1 input TVS SMBJ15A on VIN (AFTER Q1 — the v1.1 D1-position fix built correctly
        from the start: on VIN behind Q1's blocking body diode, reversal is non-destructive.
        ADR-0001; INV-D1-PLACEMENT. */}
    <chip name="D1" supplierPartNumbers={{ jlcpcb: ["C83846"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="2.1mm" h="2.4mm" dx="2.2mm" />} />
    {/* VIN bulk: 2x 100uF/35V polymer at entry (pad1 = POSITIVE) */}
    <chip name="C1" supplierPartNumbers={{ jlcpcb: ["C2982822"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="1.6mm" h="3.2mm" dx="2.9mm" />} />
    <chip name="C2" supplierPartNumbers={{ jlcpcb: ["C2982822"] }}
      pinLabels={{ pin1: "POS", pin2: "NEG" }}
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
      footprint={<Pol2 w="1.6mm" h="3.2mm" dx="2.9mm" />} />

    {/* ================= BUCK A — LM5116 5V/7A -> 5VA (USB-A rail, <=6A) ================= */}
    {/* buck-A senses its LOCAL 5VA output (no eFuse in its path). R3 STAYS 3.92k
        (5.151V): USB-A window is 4.75-5.25V and no-load 5VA must clear the 5.25V
        (+5%) ceiling. Raising R3 "proportionally" to buck-C's 4.12k would push
        5VA no-load to 5.35V > 5.25V -> USB-A over-voltage. So the local-sense
        principle applies, but the value is set by buck-A's own (tighter) window:
        5.151V -> USB-A ~5.07V @2A after the TPS2557 ~43mOhm drop, both in-window. */}
    <Buck s="A" vout="N5VA" en="ENKILL" fbtop="3.92k" fbtopMpn="C728591" ids={{
      U: "U2", QH: "Q2", QL: "Q3", RS: "RS1", L: "L1", DB: "D3",
      RT: "R2", FBT: "R3", FBB: "R4", RCMP: "R5", UVT: "R6", UVB: "R7",
      REN: "R8", RCSK: "R9", RCSG: "R10",
      CRAMP: "C3", CCMZ: "C4", CCMP: "C5", CSS: "C6", CBOOT: "C7", CVCC: "C8",
      CIN: ["C9", "C10", "C11", "C12"], CINH: "C13", COUT: ["C14", "C15", "C16", "C17"],
      RSNB: "R34", CSNB: "C53",
    }} />

    {/* ================= BUCK C — LM5116 5V/7A -> 5VC (USB-C rail, <=5A) ================= */}
    {/* v1.2 LOCAL-SENSE (fixes the v1.1 post-eFuse RUNAWAY blocker): buck-C FB now
        senses its LOCAL 5VC output (fbsense removed), NOT the post-eFuse VBUSC.
        5VC is regulated to 5.352V (R12 4.12k); the connector then sees
        5.352 - I*R_efuse = ~5.11-5.18V @5A (>=5.0V worst-corner). Because FB is
        local, an eFuse current-limit/open can no longer starve the loop -> 5VC
        cannot wind up toward VIN.
        EN is on ENKILL (the master-off bus), MERGED with buck-A again — the eFuse
        FLT->EN_C un-merge is reverted (the eFuse and its FLT are gone in the
        discrete-protection redesign; there is no per-buck fault flag to isolate). */}
    {/* v1.3 R12 FIX (was the v1.2 DO-NOT-ORDER blocker): the code is now BAKED
        (fbtopMpn="C2984354" = AR03BTCX4121, Viking 4.12k 0.1% 25ppm 0603, JLC-catalog
        VERIFIED 2026-07-23, stock 15353). v1.2 OMITTED the code so tscircuit
        value-resolved "4.12k" to C2933210 (FRC0603F3741TS = 3.74k 1%!) -> 5VC 4.97V
        undervoltage. NEVER leave R12 uncoded. DO-NOT-USE C2933210 (3.74k). Verified
        alt: C861436 (RT0603BRD074K12L Yageo, same spec, stock 4927). See
        02_parts/AR03BTCX4121/part.yaml. */}
    <Buck s="C" vout="N5VC" fbtop="4.12k" fbtopMpn="C2984354" en="ENKILL" ids={{
      U: "U11", QH: "Q4", QL: "Q5", RS: "RS2", L: "L2", DB: "D4",
      RT: "R11", FBT: "R12", FBB: "R13", RCMP: "R14", UVT: "R15", UVB: "R16",
      REN: "R17", RCSK: "R18", RCSG: "R19",
      CRAMP: "C18", CCMZ: "C19", CCMP: "C20", CSS: "C21", CBOOT: "C22", CVCC: "C23",
      CIN: ["C24", "C25", "C26", "C27"], CINH: "C28", COUT: ["C29", "C30", "C31", "C32"],
      RSNB: "R35", CSNB: "C54",
    }} />

    {/* ===== v1.6 R42 — DNP 5VC SETPOINT-TRIM STRAP (user request) =====
        BENCH-DECIDABLE INSURANCE, SHIPPED UNPOPULATED. If the bench says U12 is
        too stressed at the nominal 5.352 V rail, fit R42 and the rail drops to
        ~5.25 V, landing exactly on U12's 5.25 V V_RWM.

        WHY IT IS IN PARALLEL WITH THE FB TOP AND NOT IN SERIES WITH THE RAIL.
        The first instinct is a series resistor in the 5 V line. It has the WRONG
        TRANSFER FUNCTION, and the reason is worth writing down because it is a
        genuinely attractive trap:
          - over-voltage is a LIGHT-load phenomenon; IR drop is a HEAVY-load one.
            They are ANTI-CORRELATED. At 0 A a series resistor drops 0 mV, so it
            does nothing at all in the exact condition you added it for; at full
            load it removes voltage precisely when the rail is already lowest.
          - the cost is real: 20 mOhm at the Pi 4's 3 A is 72 mV and 0.18 W
            (at 5 A it would be 100 mV and 0.5 W). That is delivery margin spent
            to fix a no-load problem.
          - and it does nothing about the case that actually endangers anything:
            against a fail-high buck, 20 mOhm x 3 A = 60 mV of a multi-volt
            excursion.
        Trimming the SETPOINT moves the regulation target itself: load-independent,
        zero heat, zero delivery-path cost.

        ARITHMETIC. Vout = Vref x (1 + Rtop/Rbot), Vref 1.215 V, Rbot = R13 1.21k,
        Rtop = R12 4.12k -> 5.352 V. R42 160k in PARALLEL with R12 gives
        Rtop = 4.12k || 160k = 4.017k -> 1.215 x (1 + 4.017/1.21) = 5.249 V.
        The worst-case corner scales the same way: vout_min 5.227 -> 5.125 V, and
        at the Pi 4's 3 A that is 5.125 - 349 mV = 4.776 V, still +146 mV above
        the 4.63 V undervoltage threshold. THE TRIM IS ONLY AFFORDABLE BECAUSE
        THE LOAD IS A PI 4 AT 3 A; at the mistaken 5 A it would have eaten the
        entire margin and then some.

        THE CODE IS BAKED, and it was NOT baked at first -- the first export
        value-resolved it to C25757 on its own, which is EXACTLY the mechanism that
        shipped R12 as 3.74k (design said 4.12k) and R30 as 3.09k (design said
        100k). Verified before baking: C25757 = UNI-ROYAL 0402WGF1603TCE, 160k
        +-1% 0402 62.5mW, MPN decode 1603 -> 160x10^3, LCSC stock 455,100 on
        2026-07-25. The resolver happened to be RIGHT this time; that is luck, not
        a process, so the code is now explicit. Value additionally pinned by an
        E-INV part_value assert.

        BEING HONEST ABOUT WHERE IT ENDS UP: `not_assembled` in assembly.yaml
        drops a ref from the CPL but KEEPS it on the BOM by design (same as SW1
        and F1 on this board). So JLC SOURCES one 160k 0402 and does NOT place
        it -- it arrives loose with the order, which is the useful outcome for a
        bench-decidable strap: whoever runs gate Q8 already has the part. */}
    <resistor name="R42" resistance="160k" footprint="0402"
      supplierPartNumbers={{ jlcpcb: ["C25757"] }}
      connections={{ pin1: "net.N5VC", pin2: "net.FB_C" }} />

    {/* ===== MASTER OFF — SS12D07 slide switch grounds the ENKILL bus =====
        CORRECTED v1.8 (zero-context pin review, 2026-07-26). This block described
        the eFuse-era D6 / EN_C scheme AS IF IT WERE CURRENT — "buck-C EN is now the
        SEPARATE net.EN_C ... coupled to ENKILL by diode D6" — while the header of
        this same file (v1.2 notes) correctly records that D6 and the EN_C un-merge
        were REVERTED and D6 REMOVED. The file contradicted itself, and the stale
        half was the more specific-sounding half. The COPPER was never wrong: E-INV
        asserts ENKILL == {U2.4, U11.4, SW1.2, Q7.1, R8.2, R17.2} and the netlist
        agrees, which is why nothing machine-checkable caught it. A comment that
        describes a deleted circuit is the same defect class as an ADR whose stated
        reason is false: it reads as authority.

        WHAT IS ACTUALLY TRUE: there is no EN_C net and no D6. BOTH bucks' enable
        pins (U2.4 and U11.4) sit directly on net.ENKILL, each pulled to VIN by its
        own 100k (R8 for buck-A, R17 for buck-C). SW1 COM(2)=ENKILL, T1(1)=GND,
        T2(3)=open/NC. Slide to T1 -> ENKILL grounded -> BOTH LM5116s to ~9 uA
        shutdown, AND Q7 turns off so Q6's gate floats to its source and the USB-C
        reverse-block opens. Slide to T2 -> ENKILL floats up through R8||R17 = 50k
        -> both bucks ON. That 50k pull-up pair into a grounded bus is the 252 uA
        that dominates the 271 uA OFF-state budget in power_tree.yaml.
        NOTE SW1 SWITCHES ENABLE, NOT POWER: VBAT/VBAT_F never reach a switch pole,
        so the XT60 stays live with the switch off — hence the board silk
        "LEDS DARK = SWITCH OFF" / "PACK STILL LIVE AT XT60".
        Mounting posts are mechanical (off the render footprint; the FPID land
        carries them). */}
    <chip name="SW1" supplierPartNumbers={{ jlcpcb: ["C2939728"] }}
      pinLabels={{ pin1: "T1", pin2: "COM", pin3: "T2" }}
      connections={{ pin1: "net.GND", pin2: "net.ENKILL" }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="-2.5mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1.1mm" shape="circle" />
          <platedhole portHints={["2"]} pcbX="0mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1.1mm" shape="circle" />
          <platedhole portHints={["3"]} pcbX="2.5mm" pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1.1mm" shape="circle" />
        </footprint>
      } />

    {/* ================= v1.6 STATUS LEDs — one PACK + four RAIL indicators =================
        USER DECISION (task#30 D2/D3/D4): amber = PACK LIVE, green = RAIL GOOD, and
        the USB-A indication is PER PORT (three LEDs, not one) because with a single
        5VA LED a current-limited port is indistinguishable from a working one.

        THE PACK LED MUST BE FET-GATED. There is NO switched power node on this board
        to tap: SW1's pads are pad1=GND, pad2=ENKILL, pad3=NC — it switches ENABLE, not
        power. Net VBAT touches only J1 and F1; VBAT_F only F1 and Q1. So an "LED after
        the master switch" cannot be built by wiring to any net; it needs an active gate.
        MEASURED consequence of NOT gating it: (12.6-2.0)/6980 = 1.519 mA, which on top
        of the declared 270 uA OFF-state budget is 6.6x over, and flattens a 3S 5000 mAh
        pack in ~117 days. Q8 (BSS138, the SAME line as Q7 -> +0 feeder) is a low-side
        gate on the pack LED's cathode with its gate on ENKILL: master-off opens it and
        the adder falls to Q8's Idss, <=0.5 uA (270 -> 271 uA, see power_tree.yaml:25).

        The four rail LEDs need no gate: 5VA/5VC collapse when the bucks are disabled and
        Q6 opens, so every rail LED is dark in the OFF state by construction.

        THE C-PORT LED TAPS VBUSC, NOT 5VC — deliberately POST-protection (Q6 -> F2 ->
        VBUSC). A dark C LED with the A LEDs lit then means the ADR-0002 protection chain
        OPENED, which is the single most useful thing an indicator on this board can say.
        Cost to the thin Pi margin: 0.358 mA x 42.4 mOhm = 15.2 uV = 0.0152 mV, i.e. 0.10%
        of the 15 mV slack in power_tree.yaml — E-MARGIN arithmetic does not move.

        Ballasts are 6.98k C23215, ALREADY on this BOM as R7/R16 (the two LM5116 UVLO
        bottoms) -> five new feeders cost ZERO new BOM lines. The LCSC code is BAKED, not
        value-resolved: R12 (C2933210 = 3.74k, not 4.12k) and R30 (C2933195 = 3.09k, not
        100k) both shipped wrong because a bare value string was resolved by the toolchain.
        Net BOM delta for this whole cell is exactly TWO lines (C2296 + C2297).

        POLARITY: authored as <chip> pad 1 = CATHODE, matching KiCad Device:LED (pin 1 = K,
        verified in /usr/share/kicad/symbols/Device.kicad_sym) and LED_0805_2012Metric
        (pad 1 west, F.Fab chamfer west, F.SilkS cathode band at x=-1.685). JLC's own
        LED0805-R-RD model numbers pad 1 = ANODE, so the CPL rotation offset MUST come
        from a numbering-free channel — see the A-ROT rows for C2296/C2297. */}
    <chip name="Q8" supplierPartNumbers={{ jlcpcb: ["C78284"] }}
      pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
      connections={{ pin1: "net.ENKILL", pin2: "net.GND", pin3: "net.LEDPKK" }}
      footprint="sot23" />
    <resistor name="R37" resistance="6.98k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C23215"] }}
      connections={{ pin1: "net.VIN", pin2: "net.LEDPK" }} />
    {/* D8 amber PACK LED: A(pad2)=LEDPK (ballasted from VIN), K(pad1)=LEDPKK -> Q8 drain */}
    <chip name="D8" supplierPartNumbers={{ jlcpcb: ["C2296"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.LEDPKK", pin2: "net.LEDPK" }}
      footprint={<Pol2 w="0.975mm" h="1.4mm" dx="0.9375mm" />} />
    {/* three PER-PORT USB-A rail LEDs, tapped on the TPS2557 OUTPUT (VBUSAk), so a
        latched-off port reads as a dark LED rather than as a lit 5VA */}
    {[1, 2, 3].map((k) => {
      const rl = ["R38", "R39", "R40"][k - 1]
      const dl = ["D9", "D10", "D11"][k - 1]
      return (
        <group key={`ledva${k}`} name={`ledva${k}`}>
          <resistor name={rl} resistance="6.98k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C23215"] }}
            connections={{ pin1: `net.VBUSA${k}`, pin2: `net.LEDVA${k}` }} />
          <chip name={dl} supplierPartNumbers={{ jlcpcb: ["C2297"] }}
            pinLabels={{ pin1: "K", pin2: "A" }}
            connections={{ pin1: "net.GND", pin2: `net.LEDVA${k}` }}
            footprint={<Pol2 w="0.975mm" h="1.4mm" dx="0.9375mm" />} />
        </group>
      )
    })}
    {/* USB-C rail LED on VBUSC (POST Q6 + F2) — dark == the protection chain opened */}
    <resistor name="R41" resistance="6.98k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C23215"] }}
      connections={{ pin1: "net.VBUSC", pin2: "net.LEDVC" }} />
    <chip name="D12" supplierPartNumbers={{ jlcpcb: ["C2297"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.GND", pin2: "net.LEDVC" }}
      footprint={<Pol2 w="0.975mm" h="1.4mm" dx="0.9375mm" />} />

    {/* ============ DCP advertisement — TPS2513A dual-channel: U6 ports 1+2, U7 port 3 ============ */}
    <chip name="U6" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2", pin4: "DM2", pin5: "IN", pin6: "DM1" }}
      connections={{
        pin1: "net.DP_A1", pin2: "net.GND", pin3: "net.DP_A2", pin4: "net.DM_A2",
        pin5: "net.N5VA", pin6: "net.DM_A1",
      }}
      footprint="sot23_6" />
    <chip name="U7" supplierPartNumbers={{ jlcpcb: ["C473910"] }}
      pinLabels={{ pin1: "DP1", pin2: "GND", pin3: "DP2", pin4: "DM2", pin5: "IN", pin6: "DM1" }}
      connections={{
        pin1: "net.DP_A3", pin2: "net.GND", pin5: "net.N5VA", pin6: "net.DM_A3",
      }}
      footprint="sot23_6" />
    <capacitor name="C33" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
    <capacitor name="C34" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />

    {/* ================= USB-A PORT CHANNELS x3 (TPS2557 + USBLC6 + KH-AF90DIP) ================= */}
    {[1, 2, 3].map((k) => {
      const n = k - 1
      const sw = ["U3", "U4", "U5"][n]
      const rl = ["R20", "R21", "R22"][n]
      const cin = ["C35", "C36", "C37"][n]
      const cout = ["C38", "C39", "C40"][n]
      const chf = ["C41", "C42", "C43"][n]
      const esd = ["U8", "U9", "U10"][n]
      const jn = ["J2", "J3", "J4"][n]
      return (
        <group key={`porta${k}`} name={`porta${k}`}>
          <chip name={sw} supplierPartNumbers={{ jlcpcb: ["C130056"] }}
            pinLabels={{ pin1: "GND", pin2: "IN1", pin3: "IN2", pin4: "EN", pin5: "ILIM", pin6: "OUT1", pin7: "OUT2", pin8: "FAULT", pin9: "EP" }}
            connections={{
              pin1: "net.GND", pin2: "net.N5VA", pin3: "net.N5VA", pin4: "net.N5VA",
              pin5: `net.ILIM${k}`, pin6: `net.VBUSA${k}`, pin7: `net.VBUSA${k}`, pin9: "net.GND",
            }}
            footprint={<Tps2557Fp />} />
          <resistor name={rl} resistance="36.5k" footprint="0603" connections={{ pin1: `net.ILIM${k}`, pin2: "net.GND" }} />
          <capacitor name={cin} capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5VA", pin2: "net.GND" }} />
          <capacitor name={cout} capacitance="22uF" footprint="0805" supplierPartNumbers={{ jlcpcb: ["C29277"] }} connections={{ pin1: `net.VBUSA${k}`, pin2: "net.GND" }} />
          <capacitor name={chf} capacitance="100nF" footprint="0603" connections={{ pin1: `net.VBUSA${k}`, pin2: "net.GND" }} />
          {/* ESD array: 1/6 pass D+; 3/4 pass D-; VBUS pin5 on the 5V port rail */}
          <chip name={esd} supplierPartNumbers={{ jlcpcb: ["C7519"] }}
            pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
            connections={{
              pin1: `net.DP_A${k}`, pin2: "net.GND", pin3: `net.DM_A${k}`,
              pin4: `net.DM_A${k}`, pin5: `net.VBUSA${k}`, pin6: `net.DP_A${k}`,
            }}
            footprint={
              <footprint>
                {Array.from({ length: 3 }, (_, i) => (
                  <smtpad key={`x${i}`} portHints={[`${i + 1}`]} pcbX={`${-0.95 + i * 0.95}mm`} pcbY="-1.3mm" width="0.6mm" height="0.7mm" shape="rect" />
                ))}
                {Array.from({ length: 3 }, (_, i) => (
                  <smtpad key={`y${i}`} portHints={[`${i + 4}`]} pcbX={`${0.95 - i * 0.95}mm`} pcbY="1.3mm" width="0.6mm" height="0.7mm" shape="rect" />
                ))}
              </footprint>
            } />
          {/* USB-A receptacle KH-AF90DIP-112 (C503996): 1=VBUS 2=D- 3=D+ 4=GND + SH shell (THT) */}
          <chip name={jn} supplierPartNumbers={{ jlcpcb: ["C503996"] }}
            pinLabels={{ pin1: "VBUS", pin2: "DM", pin3: "DP", pin4: "GND", pin5: "SHIELD" }}
            connections={{
              pin1: `net.VBUSA${k}`, pin2: `net.DM_A${k}`, pin3: `net.DP_A${k}`,
              pin4: "net.GND", pin5: "net.GND",
            }}
            footprint={
              <footprint>
                {[-3.5, -1.0, 1.0, 3.5].map((x, i) => (
                  <platedhole key={`p${i}`} portHints={[`${i + 1}`]} pcbX={`${x}mm`} pcbY="0mm" outerDiameter="1.7mm" holeDiameter="1.0mm" shape="circle" />
                ))}
                <platedhole portHints={["SH", "5"]} pcbX="-6.62mm" pcbY="2.6mm" outerDiameter="4mm" holeDiameter="3mm" shape="circle" />
              </footprint>
            } />
        </group>
      )
    })}

    {/* ============ USB-C PORT (v3 plain 5V/5A, NO PD; v1.1 PROTECTED via eFuse) ======
        v1.1: the 5VC buck output no longer feeds VBUS directly. It feeds a TPS26631
        eFuse (U13) whose OUTPUT net VBUSC is the protected USB-C VBUS: J5's four VBUS
        pads, U12.VBUS, C49/C50 bulk, the two CC Rp pull-ups (R28/R29) and the buck-C
        FB sense (option-a) all land on VBUSC. The eFuse adds current limit, input-OV
        cutoff, soft-start and REVERSE-CURRENT BLOCKING (a powered sink can no longer
        back-feed 5VC -> the pack; red-team RT-T4). Two 10k CC Rp advertise a 3A
        source, which is all a Pi 4 ever asks for (it draws its 3A without negotiating;
          the PSU_MAX_CURRENT=5000 story here was a Pi 5 feature -- ADR-0004).
          Kept from v2: J5, U12 data
        ESD, R27 DCP short. Removed: TPS25740A PHY, RS3, all PD-config passives. */}
    <group name="usbc">
      {/* ==== v1.2 DISCRETE VBUS PROTECTION — TPS26631 eFuse DROPPED (BRIEF A2/D2) ====
          The eFuse (U13) + its OVP/SHDN/dVdT/ILIM control passives + control-pin
          clamps are REMOVED: over-built for a 5V/5A Pi rail and the root cause of
          the routing wall (its 20-pin HTSSOP IN_SYS pin boxed in the west escape
          row) AND v1.1's two blockers (post-eFuse FB runaway + SHDN 5.5V abs-max).
          USER DECISION: replace with a simple discrete chain reusing the on-BOM
          Q6/Q7 FETs (enable-gated P-FET), NOT an ideal-diode controller:
             5VC -> Q6 (AON6403 P-FET, reverse-block) -> PMID -> F2 (PPTC polyfuse,
             over-current) -> VBUSC (protected connector) -> D5 (TVS, over-voltage) -> J5
          buck-C FB STAYS on LOCAL 5VC (v1.1 fix, correct). buck-C EN RE-MERGES to
          ENKILL (the eFuse FLT->EN_C un-merge + D6 coupling diode are reverted). */}
      {/* Q6 = reverse-block P-FET (AON6403, PowerPAK SO-8): D(5)=5VC, S(1-3)=PMID,
          G(4)=QG. Body diode anode=D=5VC / cathode=S=PMID BLOCKS PMID->5VC (reverse
          back-feed) when Q6 is off. ENABLE-GATED: Q7 (BSS138) inverts ENKILL onto QG.
          Board ON (ENKILL high) -> Q7 on -> QG=GND -> Vgs=-5V -> Q6 ON (low-drop
          forward). Master-OFF (ENKILL low) -> Q7 off -> QG pulled to source (PMID)
          by R30 -> Vgs=0 -> Q6 OFF -> body diode blocks a powered sink back-feeding
          the pack (red-team RT-T4, OFF-state). Vgs |max| 20V, here <=5.4V -> no gate
          Zener needed (unlike the 12.6V input Q1). */}
      <chip name="Q6" supplierPartNumbers={{ jlcpcb: ["C2760089"] }}
        pinLabels={{ pin1: "S1", pin2: "S2", pin3: "S3", pin4: "G", pin5: "D" }}
        connections={{ pin1: "net.PMID", pin2: "net.PMID", pin3: "net.PMID", pin4: "net.QG", pin5: "net.N5VC" }}
        footprint={<Dfn56 />} />
      {/* Q7 = gate inverter (BSS138 SOT-23): G(1)=ENKILL, S(2)=GND, D(3)=QG.
          ENKILL swings 0..VIN(12.6V); Vgs<=12.6V < 20V max. */}
      <chip name="Q7" supplierPartNumbers={{ jlcpcb: ["C78284"] }}
        pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }}
        connections={{ pin1: "net.ENKILL", pin2: "net.GND", pin3: "net.QG" }}
        footprint="sot23" />
      {/* R30 = Q6 gate pull-up to its SOURCE (PMID): holds Q6 OFF when Q7 is off
          (master-off) so a back-feed keeps Vgs~0 and the body diode blocks. 100k
          (mirrors the input Q1 gate pulldown R1). */}
      {/* v1.3 R30 FIX (2nd wrong-part the semantic M-BOM gate caught, v1.2 addendum
          688a8af): tscircuit value-resolved R30 to C2933195 = FRC0603F3091TS =
          catalog 3.09k, NOT 100k (burned ~1.6mA through Q7 when ON). Code now BAKED:
          C25803 = UNI-ROYAL 0603WAF1003T5E, ledger-verified 100k 1% 0603 (JLC basic)
          — the SAME code R1/R8/R17 (the board's other 100k 0603s) already resolve to.
          MPN decode: 1003 -> 100x10^3 = 100k. DO-NOT-USE C2933195 (3.09k).
          Margins @100k: ON waste PMID->QG 5.35V/100k = 54uA (vs 1.7mA at 3.09k);
          OFF back-feed Vgs = -(Q7 Idss + Q6 Igss)~1uA x 100k = -0.1V << AON6403
          Vgs(th) — Q6 stays OFF, body diode blocks. */}
      <resistor name="R30" resistance="100k" footprint="0603" supplierPartNumbers={{ jlcpcb: ["C25803"] }} connections={{ pin1: "net.PMID", pin2: "net.QG" }} />
      {/* F2 = PPTC resettable polyfuse (OVER-CURRENT), PMID -> VBUSC. 2920 (7.4x5.1mm)
          — a 6A/16V hold does NOT exist in 1812, and a 6A part nuisance-trips at 5A
          @50C (derates ~4.8A). 7A hold (SMD2920-700/16N, C6165170; ~5.6A @50C > 5A
          load) + Vmax 16V (buck-fail-high). 16V/stock per parts-research, order-day
          recheck MANDATORY (Extended). Fallback C3762416 6A (degraded). 02_parts/SMD2920-700. */}
      <chip name="F2" supplierPartNumbers={{ jlcpcb: ["C6165170"] }}
        pinLabels={{ pin1: "1", pin2: "2" }}
        connections={{ pin1: "net.PMID", pin2: "net.VBUSC" }}
        footprint={<Pol2 w="1.8mm" h="5.1mm" dx="3.0mm" />} />
      {/* D5 = TVS over-voltage clamp, VBUSC -> GND. v1.3 DIRECTIONALITY FIX: code was
          C140903, which JLC's catalog lists as a BIDIRECTIONAL SMBJ6.0A (LRC SMB-FL) —
          it has no cathode, so the pad1=K / D5.1=VBUSC polarity assertion was
          meaningless. Now C113976 = SMBJ6.0A UNIDIRECTIONAL (DO-214AA/SMB, Vwm 6.0V,
          Vbr 7.37V, Vclamp 10.3V, JLC-VERIFIED 2026-07-23, stock 74758). Uni-dir,
          cathode=pad1 at VBUSC. Vwm 6.0V clears the 5.43V no-load VBUSC max; on a
          buck-fail-high it clamps + draws through F2 -> polyfuse trips (SECONDARY
          protection; see ADR-0002). */}
      <chip name="D5" supplierPartNumbers={{ jlcpcb: ["C113976"] }}
        pinLabels={{ pin1: "K", pin2: "A" }}
        connections={{ pin1: "net.VBUSC", pin2: "net.GND" }}
        footprint={<Pol2 w="2.1mm" h="2.4mm" dx="2.2mm" />} />
      {/* C-port data ESD (USBLC6) + BC1.2 DCP short (D+ <-> D-) for charging */}
      <chip name="U12" supplierPartNumbers={{ jlcpcb: ["C7519"] }}
        pinLabels={{ pin1: "IO1", pin2: "GND", pin3: "IO2", pin4: "IO2B", pin5: "VBUS", pin6: "IO1B" }}
        connections={{ pin1: "net.DPC", pin2: "net.GND", pin3: "net.DMC", pin4: "net.DMC", pin5: "net.VBUSC", pin6: "net.DPC" }}
        footprint={
          <footprint>
            {Array.from({ length: 3 }, (_, i) => (
              <smtpad key={`x${i}`} portHints={[`${i + 1}`]} pcbX={`${-0.95 + i * 0.95}mm`} pcbY="-1.3mm" width="0.6mm" height="0.7mm" shape="rect" />
            ))}
            {Array.from({ length: 3 }, (_, i) => (
              <smtpad key={`y${i}`} portHints={[`${i + 4}`]} pcbX={`${0.95 - i * 0.95}mm`} pcbY="1.3mm" width="0.6mm" height="0.7mm" shape="rect" />
            ))}
          </footprint>
        } />
      <resistor name="R27" resistance="0" footprint="0603" connections={{ pin1: "net.DPC", pin2: "net.DMC" }} />
      {/* CC1/CC2 Rp pull-ups to VBUSC (protected VBUS): 10k advertises 3A source-present.
          Pi override draws the full 5A; a generic USB-C device would cap at 3A. */}
      {/* v1.11: C25744 (UNI-ROYAL 0402WGF1002TCE, basic) went to stockCount 0 and
          JLC's uploader returned "10 shortfall" on the v1.10 BOM. It was the ONLY
          basic-library 10k 0402 in the catalog, so every replacement is Extended.
          C60490 = YAGEO RC0402FR-0710KL, stock 8,220,334 (queried 2026-07-27), and
          its catalog `describe` string is CHARACTER-IDENTICAL to C25744's:
          -55C~+155C 10kOhm 50V 62.5mW Thick Film Resistor +-1% +-100ppm/C 0402.
          Same land pattern -> no copper, footprint or netlist change. */}
      <resistor name="R28" resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C60490"] }}
        connections={{ pin1: "net.CC1", pin2: "net.VBUSC" }} />
      <resistor name="R29" resistance="10k" footprint="0402" supplierPartNumbers={{ jlcpcb: ["C60490"] }}
        connections={{ pin1: "net.CC2", pin2: "net.VBUSC" }} />
      {/* VBUS receptacle bulk decoupling near J5 (on VBUSC, the eFuse output = the eFuse OUT cap) */}
      <capacitor name="C49" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
      <capacitor name="C50" capacitance="10uF" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C77100"] }} connections={{ pin1: "net.VBUSC", pin2: "net.GND" }} />
      {/* USB-C receptacle: 16 pads A1..B12 (numbered 1..16) + SH (17) — dual portHints.
          VBUS pads (A4/A9/B4/B9) -> net.VBUSC (the eFuse-PROTECTED VBUS). */}
      <chip name="J5" supplierPartNumbers={{ jlcpcb: ["C5337088"] }}
        pinLabels={{
          pin1: "GNDA1", pin2: "VBUSA4", pin3: "CC1", pin4: "DPA6", pin5: "DMA7",
          pin6: "SBU1", pin7: "VBUSA9", pin8: "GNDA12", pin9: "GNDB1", pin10: "VBUSB4",
          pin11: "CC2", pin12: "DPB6", pin13: "DMB7", pin14: "SBU2", pin15: "VBUSB9",
          pin16: "GNDB12", pin17: "SHIELD",
        }}
        connections={{
          pin1: "net.GND", pin2: "net.VBUSC", pin3: "net.CC1", pin4: "net.DPC",
          pin5: "net.DMC", pin7: "net.VBUSC", pin8: "net.GND", pin9: "net.GND",
          pin10: "net.VBUSC", pin11: "net.CC2", pin12: "net.DPC", pin13: "net.DMC",
          pin15: "net.VBUSC", pin16: "net.GND", pin17: "net.GND",
          // pin6 SBU1, pin14 SBU2 left unconnected (NC — sideband unused on a charger)
        }}
        footprint={
          <footprint>
            {(["A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12"] as const).map((p, i) => (
              <smtpad key={p} portHints={[p, `${i + 1}`]} pcbX={`${-3.2 + i * 0.9}mm`} pcbY="3mm" width="0.4mm" height="1.1mm" shape="rect" />
            ))}
            {(["B1", "B4", "B5", "B6", "B7", "B8", "B9", "B12"] as const).map((p, i) => (
              <smtpad key={p} portHints={[p, `${i + 9}`]} pcbX={`${-3.2 + i * 0.9}mm`} pcbY="1.2mm" width="0.4mm" height="1.1mm" shape="rect" />
            ))}
            <platedhole portHints={["SH", "17"]} pcbX="-4.7mm" pcbY="-1mm" outerDiameter="1.2mm" holeDiameter="0.7mm" shape="circle" />
          </footprint>
        } />
    </group>
  </board>
)

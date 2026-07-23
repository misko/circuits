// crow_mic_pod_v2 — remote microphone POD (board a, CROW ACOUSTIC LOCALIZATION ARRAY)
//
// Cable-powered remote acoustic node. One Cat5e home-run from the central recorder
// powers, references and (for calibration) drives it. Signal EAST->WEST:
//   AOM-5024 electret (MK1) -> OPA1678 active-balanced driver (U1) -> ESD (D1) -> RJ45 (J1)
// Calibration transducer (LS1) + flyback (D2, D3-DNP) in the isolated SW-corner beep loop.
//
// Net-name convention (converter canon_net): leading-digit rails authored N-prefixed
//   N5V_AUDIO -> 5V_AUDIO ; N5V_BEEP -> 5V_BEEP.  Board ground = "GND" (= cable GND_AUDIO,
//   pins 7,8); native KiCad ground symbols + GND pours/stitch.
// Specialty parts author supplierPartNumbers (resolves FPID from 02_parts/*/part.yaml).
// MK1 has no JLC code (hand-solder) -> its MPN is used as the resolution handle (matches
// the 02_parts override key). Placement + outline come from 03_src/floorplan.yaml (the
// generic backend), NOT tscircuit auto-place; footprint-child pad coords here only feed
// tscircuit's own render + the port-hint -> KiCad-pad-name mapping.
//
// Diode polarity (KiCad D_SMA pad 1 = cathode): D2/D3 pin1(K)->5V_BEEP, pin2(A)->BEEP_RET.
// Guarded by floorplan pad_net asserts + electrical_invariants pin_on_net + the pin review.

export default () => (
  <board width="80mm" height="42mm">

    {/* ================= RJ45 CABLE PORT — CUSTOM NON-ETHERNET PINOUT ================= */}
    {/* Contacts 1-8 only; shield "SH" + LED pads 9-12 are unconnected at the pod        */}
    {/* (shield single-point-grounded at central, ADR-0001). Real KiCad footprint         */}
    {/* Connector_RJ:RJ45_Amphenol_RJHSE538X via the C9900035627 override.                */}
    <chip name="J1"
      supplierPartNumbers={{ jlcpcb: ["C9900035627"] }}
      pinLabels={{ pin1: "AUDIO+", pin2: "AUDIO-", pin3: "5V_BEEP", pin4: "5V_AUD",
                   pin5: "5V_AUD", pin6: "BEEP_RET", pin7: "GND", pin8: "GND" }}
      connections={{
        pin1: "net.AUDIO_P", pin2: "net.AUDIO_N",
        pin3: "net.N5V_BEEP", pin6: "net.BEEP_SWITCHED_RETURN",
        pin4: "net.N5V_AUDIO", pin5: "net.N5V_AUDIO",
        pin7: "net.GND", pin8: "net.GND",
      }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="0mm"     pcbY="0mm"    holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["2"]} pcbX="1.016mm" pcbY="1.78mm" holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["3"]} pcbX="2.032mm" pcbY="0mm"    holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["4"]} pcbX="3.048mm" pcbY="1.78mm" holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["5"]} pcbX="4.064mm" pcbY="0mm"    holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["6"]} pcbX="5.08mm"  pcbY="1.78mm" holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["7"]} pcbX="6.096mm" pcbY="0mm"    holeDiameter="0.9mm" outerDiameter="1.6mm" />
          <platedhole portHints={["8"]} pcbX="7.112mm" pcbY="1.78mm" holeDiameter="0.9mm" outerDiameter="1.6mm" />
        </footprint>
      }
    />

    {/* ================= ELECTRET MIC + BIAS (FAR EAST) ================= */}
    <resistor name="R1" resistance="100"  footprint="0603" connections={{ pin1: "net.N5V_AUDIO", pin2: "net.VMIC_F" }} />
    <capacitor name="C1" capacitance="100uF" footprint="1210" connections={{ pin1: "net.VMIC_F", pin2: "net.GND" }} />
    <resistor name="R2" resistance="3.9k" footprint="0603" connections={{ pin1: "net.VMIC_F", pin2: "net.MIC_OUT" }} />
    <chip name="MK1"
      supplierPartNumbers={{ jlcpcb: ["AOM-5024L-HD-R"] }}
      pinLabels={{ pin1: "+", pin2: "-" }}
      connections={{ pin1: "net.MIC_OUT", pin2: "net.GND" }}
      footprint={
        <footprint>
          <platedhole portHints={["1"]} pcbX="-1.27mm" pcbY="0mm" holeDiameter="0.9mm" outerDiameter="1.8mm" />
          <platedhole portHints={["2"]} pcbX="1.27mm"  pcbY="0mm" holeDiameter="0.9mm" outerDiameter="1.8mm" />
        </footprint>
      }
    />

    {/* ================= INPUT COUPLING + VMID VIRTUAL GROUND ================= */}
    <capacitor name="C2" capacitance="1uF"  footprint="0603" connections={{ pin1: "net.MIC_OUT", pin2: "net.INP" }} />
    <resistor  name="R3" resistance="100k"  footprint="0603" connections={{ pin1: "net.INP",   pin2: "net.VMID" }} />
    <resistor  name="R4" resistance="22k"   footprint="0603" connections={{ pin1: "net.N5V_AUDIO", pin2: "net.VMID" }} />
    <resistor  name="R5" resistance="22k"   footprint="0603" connections={{ pin1: "net.VMID",  pin2: "net.GND" }} />
    <capacitor name="C3" capacitance="10uF" footprint="0805" connections={{ pin1: "net.VMID",  pin2: "net.GND" }} />

    {/* ================= OPA1678 DUAL — ACTIVE-BALANCED DRIVER (~3 V/V DIFF) ================= */}
    {/* U1A non-inv +1.5 (hot OUTA) ; U1B inv -1 (cold OUTB) ; Vdiff = OUTA-OUTB = 3*Vsig    */}
    <chip name="U1" footprint="soic8"
      supplierPartNumbers={{ jlcpcb: ["C192421"] }}
      pinLabels={{ pin1: "OUTA", pin2: "-INA", pin3: "+INA", pin4: "V-",
                   pin5: "+INB", pin6: "-INB", pin7: "OUTB", pin8: "V+" }}
      connections={{
        pin1: "net.OUTA", pin2: "net.INA", pin3: "net.INP", pin4: "net.GND",
        pin5: "net.VMID", pin6: "net.INB", pin7: "net.OUTB", pin8: "net.N5V_AUDIO",
      }}
    />
    {/* stage A gain network: R6 feedback, R7+C4 gain leg to VMID (DC gain 1) */}
    <resistor  name="R6" resistance="10k"   footprint="0603" connections={{ pin1: "net.OUTA", pin2: "net.INA" }} />
    <resistor  name="R7" resistance="20k"   footprint="0603" connections={{ pin1: "net.INA",  pin2: "net.GLA" }} />
    <capacitor name="C4" capacitance="10uF" footprint="0805" connections={{ pin1: "net.GLA",  pin2: "net.VMID" }} />
    {/* stage B inverter: R8 from hot OUTA, R9 feedback */}
    <resistor  name="R8" resistance="10k"   footprint="0603" connections={{ pin1: "net.OUTA", pin2: "net.INB" }} />
    <resistor  name="R9" resistance="10k"   footprint="0603" connections={{ pin1: "net.OUTB", pin2: "net.INB" }} />

    {/* ================= OUTPUT NETWORK: series R + DC-block coupling ================= */}
    <resistor  name="R10" resistance="100"  footprint="0603" connections={{ pin1: "net.OUTA", pin2: "net.OLA" }} />
    <capacitor name="C5"  capacitance="10uF" footprint="0805" connections={{ pin1: "net.OLA", pin2: "net.AUDIO_P" }} />
    <resistor  name="R11" resistance="100"  footprint="0603" connections={{ pin1: "net.OUTB", pin2: "net.OLB" }} />
    <capacitor name="C6"  capacitance="10uF" footprint="0805" connections={{ pin1: "net.OLB", pin2: "net.AUDIO_N" }} />

    {/* ================= U1 SUPPLY DECOUPLING + RAIL BULK ================= */}
    <capacitor name="C7"  capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5V_AUDIO", pin2: "net.GND" }} />
    <capacitor name="C8"  capacitance="10uF"  footprint="0805" connections={{ pin1: "net.N5V_AUDIO", pin2: "net.GND" }} />
    <capacitor name="C9"  capacitance="10uF"  footprint="0805" connections={{ pin1: "net.N5V_AUDIO", pin2: "net.GND" }} />
    <capacitor name="C10" capacitance="100nF" footprint="0603" connections={{ pin1: "net.N5V_AUDIO", pin2: "net.GND" }} />

    {/* ================= ESD ON THE EXPOSED AUDIO PAIR (TPD2E2U06, at J1) ================= */}
    {/* SOT-553: 1,2=NC (tied GND, datasheet-permitted), 3=IO1, 4=GND, 5=IO2 */}
    <chip name="D1"
      supplierPartNumbers={{ jlcpcb: ["C1972959"] }}
      pinLabels={{ pin1: "NC", pin2: "NC", pin3: "IO1", pin4: "GND", pin5: "IO2" }}
      connections={{ pin1: "net.GND", pin2: "net.GND", pin3: "net.AUDIO_P", pin4: "net.GND", pin5: "net.AUDIO_N" }}
      footprint={
        <footprint>
          <smtpad portHints={["1"]} pcbX="-0.5mm"  pcbY="-0.5mm" width="0.3mm" height="0.5mm" shape="rect" />
          <smtpad portHints={["2"]} pcbX="0mm"     pcbY="-0.5mm" width="0.3mm" height="0.5mm" shape="rect" />
          <smtpad portHints={["3"]} pcbX="0.5mm"   pcbY="-0.5mm" width="0.3mm" height="0.5mm" shape="rect" />
          <smtpad portHints={["4"]} pcbX="0.25mm"  pcbY="0.5mm"  width="0.3mm" height="0.5mm" shape="rect" />
          <smtpad portHints={["5"]} pcbX="-0.25mm" pcbY="0.5mm"  width="0.3mm" height="0.5mm" shape="rect" />
        </footprint>
      }
    />

    {/* ================= CALIBRATION TRANSDUCER (SW CORNER, ISOLATED BEEP LOOP) ================= */}
    <chip name="LS1"
      supplierPartNumbers={{ jlcpcb: ["C22359707"] }}
      pinLabels={{ pin1: "+", pin2: "-" }}
      connections={{ pin1: "net.N5V_BEEP", pin2: "net.BEEP_SWITCHED_RETURN" }}
      footprint={
        <footprint>
          <smtpad portHints={["1"]} pcbX="-3.5mm" pcbY="3.5mm"  width="2.5mm" height="2.5mm" shape="rect" />
          <smtpad portHints={["2"]} pcbX="-3.5mm" pcbY="-3.5mm" width="2.5mm" height="2.5mm" shape="rect" />
        </footprint>
      }
    />
    {/* D2 SS14 flyback (populated): pad1 K -> 5V_BEEP, pad2 A -> BEEP_RET */}
    <chip name="D2"
      supplierPartNumbers={{ jlcpcb: ["C2480"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.N5V_BEEP", pin2: "net.BEEP_SWITCHED_RETURN" }}
      footprint={
        <footprint>
          <smtpad portHints={["1"]} pcbX="-2mm" pcbY="0mm" width="1.5mm" height="1.6mm" shape="rect" />
          <smtpad portHints={["2"]} pcbX="2mm"  pcbY="0mm" width="1.5mm" height="1.6mm" shape="rect" />
        </footprint>
      }
    />
    {/* D3 SMAJ6.0A DNP over-clamp position (same net orientation as D2) */}
    <chip name="D3"
      supplierPartNumbers={{ jlcpcb: ["C559105"] }}
      pinLabels={{ pin1: "K", pin2: "A" }}
      connections={{ pin1: "net.N5V_BEEP", pin2: "net.BEEP_SWITCHED_RETURN" }}
      footprint={
        <footprint>
          <smtpad portHints={["1"]} pcbX="-2mm" pcbY="0mm" width="1.5mm" height="1.6mm" shape="rect" />
          <smtpad portHints={["2"]} pcbX="2mm"  pcbY="0mm" width="1.5mm" height="1.6mm" shape="rect" />
        </footprint>
      }
    />

    {/* ================= TEST POINTS (south edge) ================= */}
    <testpoint name="TP1" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.N5V_AUDIO" }} />
    <testpoint name="TP2" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.GND" }} />
    <testpoint name="TP3" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.AUDIO_P" }} />
    <testpoint name="TP4" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.AUDIO_N" }} />
    <testpoint name="TP5" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.N5V_BEEP" }} />
    <testpoint name="TP6" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.BEEP_SWITCHED_RETURN" }} />
    <testpoint name="TP7" footprintVariant="pad" padShape="circle" padDiameter="1.5mm" connections={{ pin1: "net.VMID" }} />

  </board>
)

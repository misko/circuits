# DETAIL_DESIGN — crow-recorder-central-v2

Component-value derivations with margins. Values marked [PARTS] are filled from
the 02_parts datasheet research (FB reference, crystal CL, PTC resistance).

## Power rails

### 3V3 digital buck (U7, AP61102Z6-7)
- Vin 5V, Vout 3.3V, Iout ~0.6A. Topology BUCK (E-TOPO: 3.3 < 4.9).
- FB divider: Vout = Vref*(1+R1/R2). Vref = [PARTS from AP61102 datasheet].
  R1/R2 computed for 3.3V once Vref known. 1% resistors (E-MARGIN not tight;
  digital rail).
- Inductor + Cout per datasheet design table for 1.5A / ~1MHz. [PARTS]
- Cin: 10µF X7R + 100nF, HARD against VIN/GND (<2mm hot loop, ledger gotcha).
- EN: forced-PWM (EN < VIN-200mV from sequencing logic) for lower ripple.
- PG output -> U8 (0V9 core) EN (ADR-0005 sequencing).

### 0V9 core buck (U8, AP61102Z6-7)
- Vin 5V, Vout 0.9V, Iout ~0.8A (XU316 core). Topology BUCK.
- FB divider for 0.9V from Vref. [PARTS]
- EN driven by U7 PG (PG_3V3 net) — core after IO rail.
- Same Cin hot-loop discipline.

### 1V8 LDO (U9, TCR2LF18; TLV70018 fallback)
- Vin 3V3, Vout 1.8V, ~50mA. Drop 1.5V @ 50mA = 75mW. Cin/Cout 1µF X7R.
- Fed from 3V3 so it rises right after 3V3 (never last, ADR-0005).

### 3V3A quiet analog LDO (U10, XC6227C331PR-G)
- Vin 5V, Vout 3.3V, ~70mA (2x PCM1865 AVDD). Drop 1.7V @ 70mA = 119mW (SOT-89
  handles it). Cin 1µF + Cout 1µF X7R (datasheet stability). [PARTS confirm Cout]
- CE tied to VIN (always-on; floating CE = OFF per ledger).
- Separate quiet rail: joins digital only at GND (star at ADC AVSS region).

## Input protection (ADR-0001)
- Q1 AO3401A P-FET RPP: S->5V, D->VIN_RAW, G->GND via R (10k) + a gate-source
  path. Vgs = -5V (< -12V abs-max, fine).
- D1 SMAJ5.0A TVS: cathode->VIN_RAW, anode->GND.
- F_IN fuse ~2A on VIN_RAW (fuse-on-fault crowbar with the TVS).
- C bulk on 5V: 22µF + 100nF.

## Clock tree (ADR-0004)
- Y1 FA-238 24MHz + 2 load caps. CL = [PARTS]; Cload_cap = 2*(CL - Cstray),
  Cstray ~3pF. Short symmetric traces, GND guard.
- U4 NC7NZ34: all 3 inputs tied to MCLK; Y1..Y2 out. VCC 3V3 decoupled 100nF.
- 33R source-series: one on each buffered MCLK leg (to U2/U3 SCKI), one each on
  BCLK and LRCK at the XU316 driver. All CLOCK netclass (0.25mm), kept short.
- Both PCM1865 XI (pin 10) TIED TO GND (abs-max 2.1V — the critical invariant).

## Analog input RC (per channel, quiet analog band) — the anti-alias/EMI cell
Balanced line audio (~3V/V diff from the pod OPA1678) into PCM1865 diff inputs.
Per channel (x8, 6 populated):
- TPD2E2U06 ESD at the RJ45 AUDIO+/- tails (D-ADJ hard against the connector).
- Series DC-block caps 2.2µF X7R on + and - (AC-couple; PCM1865 input biased to
  VCM internally / via mode). [confirm input mode vs PCM1865 datasheet]
- Series R 100R on + and -, shunt differential C 1nF across +/- at the ADC pin
  (RC anti-alias/EMI, fc ~ 1/(2*pi*100*1n) well above audio; guards RF ingress
  on 25ft cable). Kept SHORT + SYMMETRIC (archetype failure mode).
NOTE: exact input coupling (AC vs DC, VCM bias) to be finalized against the
PCM1865 datasheet's line-input application circuit at authoring.

## Beeper switch (ADR/D1, low-side, slow edges)
- Q2 AO3400A N-FET: D->BEEP_RETURN (common to all 6 ports green-6), S->GND.
- Gate: XU316 GPIO -> series R (1k) -> gate; shunt C (1-10nF) gate-to-GND +
  gate pulldown R (100k). The RC softens the 4kHz burst edges (slew-limit) to
  cut harmonics/EMI on the +5V_BEEP bus and cable. Slew ~ set by R*C.
- +5V_BEEP is the always-on 5V bus to all pods (green-3); the pod transducer
  sits between +5V_BEEP and green-6; Q2 sinks the common return.

## Per-port power protection
- MINISMDC050F-2 PTC (F1..F8) on +5V_AUDIO feed per port. Rhold = [PARTS]; in
  the pod power delivery IR budget (power_tree PLUS5V_AUDIO). 0.5A hold >> 20mA
  pod audio; trips on a shorted Cat5e.

## USB (controlled short HS)
- USB4105 USB-C device receptacle (J2). CC1/CC2 each -> 5.1k Rd to GND (sink/
  device advertisement). VBUS -> divider to an XU316 GPIO (VBUS present sense).
- D+/D- -> TPD4EUSB30 ESD (close to J2) -> XU316 USB_DP/USB_DM. Short controlled
  pair, F.Cu-only lane from the south edge to the SoC (archetype: reserve first).
- USB series/termination per XMOS USB PHY guidance [PARTS from XU316 datasheet].

## SHT40 temp/humidity (U6)
- I2C (shared bus with the two ADCs); address 0x44 [PARTS confirm]. 100nF
  decoupler. Placed away from the regulators + XU316 (self-heating error).

## I2C bus
- SDA/SCL from XU316; 4.7k pull-ups to 3V3. Devices: U2 (0x4A), U3 (0x4B),
  U6 SHT40 (0x44). MD0=GND on both ADCs selects I2C control.

## QSPI boot (W25Q16 flash, U5)
- IO0..IO3, CLK, CS# to the XU316 QSPI boot port [PARTS: which XU316 pins].
  CS# pull-up 10k to 3V3. 100nF decoupler. 3V3 part.

## Decoupling strategy
- XU316: per XMOS hardware checklist [PARTS] — bulk + per-supply-pin 100nF, PLL
  filter, USB_VDD decoupling. Distribute 100nF close to each VDD/VDDIO pin.
- PCM1865 (x2): AVDD/DVDD/IOVDD each 100nF + bulk 10µF on AVDD; VREF/VCM caps
  per datasheet.
- Every regulator: Cin/Cout per datasheet.

## Test points (G12) + injection header (G13)
- TP: 5V, 3V3, 0V9, 1V8, 3V3A, GND, MCLK, BCLK, LRCK, ADC_DOUT (TDM), BEEP_RETURN,
  +5V_BEEP.
- JP_INJ: same-signal injection header — a 2-3 pin header feeding a common test
  signal into both ADC groups' inputs (via series R) to measure inter-ADC skew.

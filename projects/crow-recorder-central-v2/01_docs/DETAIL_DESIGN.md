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
- EN: tied to VIN (U7.5 = 5V) = AUTO PFM at light load, as-built. Accepted per
  the ADR-0005 amendment (red-team RT1-P1-1, 2026-07-23): 3V3 is digital-only
  (3V3A comes from 5V via U10), so PFM ripple is benign; the forced-PWM
  EN-divider stays a v-next option. (This line previously claimed forced-PWM
  — stale-doc fix 2026-07-24, pin-review catch.)
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
  handles it). Cin 1µF + Cout 2.2µF X5R 25V-rated (Torex ETR03054 'Input and Output Capacitors' p.9: CL=2.2µF for the 2.5-5.0V output band; 25V rating keeps DC-bias derating mild at 3.3V, ~1.9µF effective — fresh-lens P1 fix 2026-07-23; was authored 1µF with an unresolved [PARTS confirm] placeholder)
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
- D+/D- -> TPD4EUSB30 ESD (close to J2) -> XU316 USB_DP/USB_DN. Short controlled
  pair, F.Cu-only lane from the south edge to the SoC (archetype: reserve first).
  (Net renamed USB_DM -> USB_DN at v1.1: KiCad recognizes differential pairs
  ONLY by name suffix P/N, +/-, _P/_N — with DP/DM no diff-pair rule could
  ever bind, which is why v1.0's diff_pair_dimensions sat empty.)
- USB series/termination per XMOS USB PHY guidance [PARTS from XU316 datasheet].

### USB 90ohm — stackup + solved geometry (v1.1, external-review F2 closure)
- Fab stackup (ORDER_README orders it EXPLICITLY): JLCPCB 6-layer
  **JLC06161H-3313**, 1.6mm — L1 1oz (0.035mm finished) over prepreg 3313
  **h = 0.0994mm, Er = 4.1**, then the In1.Cu solid GND plane (this pair's
  reference). Source: jlcpcb.com/impedance, fetched 2026-07-24.
- Solved geometry: **w = 0.125mm, edge gap = 0.15mm**, edge-coupled
  microstrip L1-over-In1 with soldermask (~20um, Er~3.8) ->
  **Zdiff = 89.7-90.5 ohm** (2D finite-difference Laplace field solve,
  odd-mode capacitance method, Zodd = 1/(c*sqrt(Cd*Ca)); grid 4um and 3um
  agree within 0.8 ohm; sanity anchor: the same solver gives 50.6 ohm
  single-ended at w = 0.14mm on this stackup, matching JLC-family calculator
  values). Within the 90 ohm +/-10% USB 2.0 HS window with margin even at
  JLC's +/-10% process tolerance.
- Enforcement (all three ACTIVE, not documentation): nets.yaml `USB_DIFF`
  class `diff_pair {width 0.125, gap 0.15}` -> netclass dims + `.kicad_dru`
  `USB_DIFF_diffpair` rule (`diff_pair_gap` min 0.145/opt 0.15) + board
  `diff_pair_dimensions`. Proven able to FAIL: tightening min to 0.30mm
  yields 10 diff_pair_gap_out_of_range findings on this exact pair.
- Routed result (measured, audit_board R-LEN gate): USB_DP 23.62mm /
  USB_DN 23.51mm, spread 0.110mm <= 1mm (XMOS XU316 skew budget), every
  segment 0.125mm on F.Cu, ZERO vias -> In1 reference unbroken. The D_USB
  ESD stub rides the J2 mirror-pad legs (placement unchanged from v1.0).
- Order posture: controlled impedance NOT purchased; the stackup-specific
  calc above carries the claim, and ORDER_README makes a USB-HS host/cable
  first-article matrix a REQUIRED bring-up gate.

## XU316 LV_x_N IO-voltage straps — RESOLVED (PR2-P0-1, fixed pre-seal 2026-07-24)

v1.0 (and the first v1.1 staging) tied U1.40 (LV_L_N), U1.43 (LV_T_N),
U1.52 (LV_R_N) HARD to 3V3 — a confirmed over-AMR P0, fixed in the sealed
v1.1 by DELIBERATE FLOAT (no_connect-sanctioned; measured: netlist diff vs
v1.0 shows exactly these 3 pins moving to unconnected — see the release
verification/lv_strap_fix_diff.md). Datasheet basis — XU316-1024-TQ128
datasheet v2.0.0 (xmos.com, fetched 2026-07-24):

- §4.4 "Power Control Pins": LV_L_N(40)/LV_R_N(52)/LV_T_N(43) = "Select low
  voltage VDDIOL/R/T, active low — Input, PU, **IOB**". IOB = powered from
  VDDIOB18; §4.8: "the bottom IO domain, which includes JTAG and the crystal
  oscillator, is **always at 1.8V**".
- §15.1 Absolute Maximum Ratings: "V(Vin) — Voltage applied to any IO pin:
  −0.5 … **VDDIO + 0.5 V**". For an IOB pin that is 1.8 + 0.5 = **2.3V max**.
  A hard 3.3V tie is ~1.0V beyond AMR on three pins of the consigned SoC.
  **The LV straps are NOT 3.3V-tolerant.**
- Correct 3.3V-domain select (§4.8): pins "should be **tied high or left
  floating** to specify the domain uses a 3.3V nominal supply" — "high" is
  the IOB domain's 1.8V, and floating is the documented select (internal
  pull-up, I(PU) −35µA max at 1V8). §14: "If you use 1.8V for any of the
  VDDIOL/T/R domains, strap the corresponding LV_x_N pins to GROUND."

FIX (APPLIED, v1.1): LV_L_N / LV_T_N / LV_R_N disconnected from 3V3 and
left floating — the datasheet-documented 3.3V select (internal PU holds them
high); a driven high, if ever needed, must come from 1V8. Root cause: the part.yaml gotcha said "tie HIGH(or float)=3V3 mode" and HIGH
was read as 3V3 — but HIGH for an IOB-domain pin means 1.8V. Caught by the
v1.1 zero-context pin review; datasheet-confirmed before seal.

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
- XU316: per XMOS hardware checklist — bulk + per-supply-pin 100nF, PLL
  filter, USB_VDD decoupling. Distribute 100nF close to each VDD/VDDIO pin.
- **XU316 core (0V9) VENDOR MINIMUM (verified v1.2, external review EXT2-F1)**:
  XU316-1024-TQ128 datasheet XM-014532-PC-2.0.0, §14 "Integration" (p.29):
  "The VDD supply should be well decoupled at high frequencies. Place many
  (at least 12) 100 nF low inductance multi-layer ceramic capacitors close to
  the chip between the supplies and GND." Also §14: VDDIO "several 100nF …
  for example, one 100nF 0402 low inductance MLCC on each supply pin"; "The
  ground side of the decoupling capacitors should have as short a path back
  to the GND pins as possible. A bulk decoupling capacitor of at least 10 uF
  should be placed on VDD and VDDIO supplies." Checklist §H.2 (p.92) repeats
  multiple-per-supply + 10uF bulk. AS BUILT (v1.2): 13x 100nF 0402 (C1525)
  on 0V9 (C_c1..C_c13; v1.1 had 8 for 15 core-VDD pins — below the stated
  minimum, the v1.2 respin driver), each ≤3.22mm from its nearest core-VDD
  pin (pins 50/54 = 2.01/2.02mm after the C_b0v9 slot swap), GND sides on
  the F.Cu pour with In1/In4 plane vias; C_b0v9 10uF bulk retained (moved
  3.75mm south, fed by 0.4mm B.Cu + 2 vias).
- PCM1865 (x2): AVDD/DVDD/IOVDD each 100nF + bulk 10µF on AVDD; VREF/VCM caps
  per datasheet.
- Every regulator: Cin/Cout per datasheet.

## Test points (G12) + injection header (G13)
- TP: 5V, 3V3, 0V9, 1V8, 3V3A, GND, MCLK, BCLK, LRCK, ADC_DOUT (TDM), BEEP_RETURN,
  +5V_BEEP.
- JP_INJ: same-signal injection header — a 2-3 pin header feeding a common test
  signal into both ADC groups' inputs (via series R) to measure inter-ADC skew.

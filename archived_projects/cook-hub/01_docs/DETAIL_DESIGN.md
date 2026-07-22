# DETAIL_DESIGN — cook-hub (every value derived)

## 1. Input protection (ADR-0001)
- F1 Bourns MF-MSMF200L-2 polyfuse: Ihold 2.0 A, Itrip 4 A, 16 V — budget
  0.61 A typ / <1.5 A worst (all coils + inrush), replaceable-free reset (§7.3).
- Q3 AO3401A reverse PFET: drain=J1+, source=5VF node, gate=GND via 100 k.
  Vgs(th) −0.9 V, on at −5 V (Rds 60 mΩ @ −4.5 V, drop <0.1 V @1 A). Reverse
  input: body diode blocked, Vgs=0 → open. Vds max −30 V, Vgs max ±12 V ok.
- D2 SMBJ5.0A on 5VP: stand-off 5 V, clamp ≤9.2 V @ 60 A — below AO3401 Vds,
  AMS1117 Vin 15 V, ULN COM 50 V, Pico VSYS 5.5 V…: VSYS is fed through D1
  (SS34, 40 V) and the Pico tolerates VSYS ≤ 5.5 V; a 9.2 V clamp event
  exceeds that only during the surge itself; acceptable for 8/20 µs
  transients per RPi hardware design norm; continuous overvoltage >5.5 V is
  out of scope for a bench SELV supply (recorded residual risk, ADR-0001).
- Bulk: CE1 220 µF/16 V alu-polymer + C_5VP 100 µF? → 220 µF electrolytic +
  2×22 µF X5R: relay switching step ΔI=10 mA — trivial; sized instead for
  hot-plug ring-down and §7.3 "bulk capacitance for relay transients".

## 2. Relay bank (ADR-0002)
- DIP05-1A72-12L: coil 500 Ω @5 V → 10 mA; pull-in ≤3.5 V, drop-out ≥0.75 V.
  ULN2803A sat ≤0.9 V @10 mA → coil sees ≥4.1 V ≥ pull-in ✓ (margin 17%).
  Contact: 10 W / 200 V / 0.5 A switching — keypad scan lines are <24 V,
  <5 mA ⇒ ≥10⁸ ops class (life chart, series DS p.5); §16.4's 1000-cycle
  fixture is trivial against this.
- Geometry: super-column pitch 15.24 mm; coil col at x_k, contact col at
  x_k+7.62. Contact↔SELV min air = 7.62 − 2×0.75 (pad r) = 6.12 mm ≥6 mm;
  creepage across the inter-column gap ≥ 6.12 + slot detour ≈ 8+ mm (2 mm
  slots, 7 off). Rows y-pitch 20.0 mm (body 19.3 → 0.7 clear).
- Flyback: ULN2803A internal diodes, COM → RELAY_5V. Coil off-transient
  clamps to rail+Vf; rail bulk absorbs 10 mA·5 mH ≈ nJ — fine.
- One-key-at-a-time is firmware (§6.7); hardware default = all off (three
  locks, ARCHITECTURE). §6.4 diagnostic LEDs: coil-side only — omitted
  (16 LEDs cost + clutter; COIL_n test points serve diagnosis; spec says
  "optional").

## 3. Watchdog timing (ADR-0003, D5)
tw = K·Rext·Cext, K≈1.0 @3.3 V (SCES586E §8): R11 390 kΩ 1% + C11 1 µF X7R
±10% → 351–429 ms nominal band; with K 0.9–1.1 → 316–472 ms ⊂ [300, 500] ms
(§6.5). Retrigger period at 5 Hz = 200 ms < 316 ms min ✓ (margin 1.6×);
at boot Q=low until first edge ✓. Datasheet Rext range 5 kΩ–1 MΩ ✓.

## 4. Gating logic (ADR-0003)
- /OE: R21 10 k pullup to 3V3 (disabled default); U8 74LVC1G00 NAND drives it
  from RLY_EN (GP14, R22 10 k pulldown) and WD_OK.
- Coil rail: U9 74LVC1G11 AND3(WD_OK, ESTOP_OK, RLY_EN) → R24 1 k → Q2
  2N7002 → pulls Q1 gate (R23 47 k to 5VP) low. Q1 AO3401A: 160 mA load,
  Rds 60 mΩ → 10 mV drop. R25 10 k bleeder on RELAY_5V.
- 595 MR tied 3V3 (reset unused — /OE + rail gating own the safe state;
  firmware clears registers before enabling per §11.1).

## 5. E-stop & door (§3.8/3.9)
- E-stop: 3V3 —R31 3.3k— ESTOP_RAW —J8— NC loop —GND. R32 10 k + C31 100 n
  RC (τ=1 ms) → U11A 74HC14 → ESTOP_OK (high=closed). GP9 monitors ESTOP_OK.
  PESD5V0S1BA on ESTOP_RAW.
- Door: 3V3 —R33 3.3k— DOOR_RAW —J7.2— loop; 10 k EOL across the NC reed at
  the FAR end (D8): closed 0 V / open 2.48 V / cut 3.3 V. R34 10 k + C33
  100 n RC → GP8 (RP2350 Schmitt). SJ1 solder link → GP28 for analog EOL
  discrimination. J7.1 = 3V3 via JP5 for the §3.8b Hall option (open by
  default), J7.3 = GND. PESD on DOOR_RAW.
- 74HC14 spare gates: buffer ESTOP_OK→GP9 (2nd inverter pair) — implemented
  as two inverters in series (U11B feeds GP9 with re-inverted, i.e. U11A→
  U11B gives ESTOP_OK_BUF); remaining 2 inputs tied to GND, outputs NC.
  (6 gates: A=raw→/est, B=/est→ESTOP_OK, C=spare in GND, D..F in GND.)
  Correction: ESTOP_OK = output of B (non-inverted sense, high=closed);
  AND3 and GP9 both take ESTOP_OK.

## 6. I2C buses (§3.3/3.4/3.5, D11)
- Pullups: 2.2 k (JP fitted) or 4.7 k (JP open) per line; MLX90640+SHT45 on
  0.3 m cable ≈ 150 pF ⇒ τ = 2.2k·150p = 330 ns < 1 µs rise budget @100 kHz,
  ok to 400 kHz at 2.2 k.
- R41-44 33 Ω series damping at the connector (0 Ω alternate in BOM notes).
- U13/U14 USBLC6-2SC6: line cap 3.5 pF, I/O pairs on SDA/SCL, VBUS pin → 3V3.
- TPs on both buses at the connectors (§3.3e).

## 7. MAX31856 (§3.6)
3V3A supply (AVDD+DVDD), decoupled 100 n + 10 µ. Input network per datasheet
typical circuit: 100 Ω each leg, 100 nF differential + 10 nF each leg to
AGND→GND; BIAS ties to the T− node (sets TC common-mode). Open/short fault
detection internal (§3.6f), /FAULT + /DRDY to test points. Placed at NW board
edge, J5 (PCC-SMP-K, keyed) on the edge beside it; >100 mm from relays,
regulators at SW (§3.6a/b). CS1 = GP20 → J15 DNP header (D10).

## 8. Thermistor channels (§3.10)
3V3A —R51 10 k 1%— TH1 —(NTC 10 k ext)— GND; R52/TH2 same; R53/TH3 spare.
RC: 1 k + 100 nF (τ=100 µs, fs≥2 S/s ✓). PESD on each. Ratio metric error:
divider top = 3V3A while Pico ADC ref = module 3V3 → ±1.5% abs worst; NTC
±1 °C class unaffected for trends; ADC_VREF tap = TP (module keeps its own
filter). β configurable in firmware (§3.10d).

## 9. Thermal/ambient (§8.2)
AMS1117: (5−3.3)·0.3 A = 0.51 W max → θja ~64 °C/W w/ tab pour → +33 °C
above 60 °C ambient = 93 °C ≪ 125 °C limit. Standex relay Top max 70 °C
ambient: NE zone far from LDO, coil self-heat 50 mW — margin ok at 60 °C but
70 °C is the relay's cap: recorded as the board's ambient ceiling.
ULN2803: one coil 10 mA → negligible; all-16 fault case 160 mA·0.9 V=0.14 W ok.

## 10. Test points (§8.6)
5VP, 3V3, 3V3A, GND×2, SDA0, SCL0, SDA1, SCL1, SCK, MISO, MOSI, CS0, CS1,
HX DAT, HX CLK, RLY DATA/CLK/LATCH//OE, WD_PULSE, WD_OK, DOOR, ESTOP,
TH1/TH2/TH3, CONT (opto in), VBUS(pico), RUN, ADC_VREF, COIL_1..COIL_16.
None in the keypad zone (§8.4: J11 pins are the only contact-side access).

## 11. Connector map (§8.5) — all locking/keyed where practical
J1 DC-005 barrel 5V/2A · J2 Pico 2 socket pair (USB exits via module) ·
J3 XH-4 I2C0 · J4 XH-4 I2C1 · J5 PCC-SMP-K · J6 XH-5 loadcell digital
(5V,3V3,GND,DAT,CLK) · J7 XH-3 door · J8 XH-2 E-stop · J9 XH-6 thermistors
(TH1,G,TH2,G,TH3,G) · J10 KF350 3.5 mm contactor (C,E; 30 V 50 mA) ·
J11 X9555WV 2×16 keyed (isolated) · J12 XH-5 encoder DNP · J13 XH-4
step/dir/en DNP · J14 XH-5 spare I2C0+GP4 · J15 1×6 DNP MAX31865.

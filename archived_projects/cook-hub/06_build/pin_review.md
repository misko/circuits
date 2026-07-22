# cook-hub v1.0 — fresh-context pin reviews (2026-07-19)

Protocol: conclusion-free dossiers (pin_audit.py) + fresh agents deriving
expected pinouts from datasheets, judging every pad's actual net. Three
independent reviews; verdicts below. Full transcripts in the session log.

## Review 1 — relay / driver / watchdog chain: PASS (11/11 refs)
- U5/U6 ULN2803ADWR: 1-8=IN(DRV1-16), 9=GND, 10=COM=RELAY_5V (switched
  rail), 18..11=OUT=COIL_1..16; opposite-corner pairing verified (pin
  18=OUT1=COIL_1 vs K1.7); non-mirrored CCW winding.
- U7 SN74LVC1G123 (DCT): A#=GND, B=WD_PULSE (rising-edge trigger), CLR#=3V3,
  Q=WD_OK, C11 across Cext/Rext-Cext, R11 to 3V3 — canonical monostable.
  Monostable math: t_w ≈ 1.0 x 390k x 1u = 390 ms > 200 ms worst retrigger
  gap (5-20 Hz), ~1.95x margin; tolerance band 316-472 ms still passes.
- U8 LVC1G00: OE_N = NAND(RLY_EN, WD_OK). U9 LVC1G11: COIL_EN =
  WD_OK & ESTOP_OK & RLY_EN (pin 2 correctly GND on the SOT-23-6).
- DEFAULT-OFF proof (Pico absent/unprogrammed, all GPIO Hi-Z), three
  independent layers: (1) R22 10k pulls RLY_EN low -> COIL_EN low AND
  OE_N high; (2) R21 10k pulls /OE high even with U8 dead -> 595s Hi-Z;
  (3) R23 47k pulls Q1 gate to 5VP -> P-FET off -> RELAY_5V rail dead;
  plus U7 Q powers up LOW until the first WD edge; R25 bleeds the rail.
- K1 DIP05-1A72-12L: coil 1/7 (RELAY_5V/COIL_1), contacts 8/14 (KC1B/KC1A),
  winding matches the Standex DS fig (pinout 12); contact nets touch ONLY
  J11 — isolation boundary intact (1.5 kVDC coil-contact).
- Q1 AO3401A: G/S/D = Q1G/5VP/RELAY_5V (source at supply). Q2 2N7002:
  G/S/D = Q2G/GND/Q1G. U10 LTV-817S: LED SELV side, C/E dry to J10.
  U11 74HC14: double-inversion Schmitt chain, unused inputs grounded.
- Note: U8 pinout verified against the universal TI 5-pin single-gate
  convention (its PDF not stored locally).

## Review 2 — sensor front-ends: PASS (5/5 refs)
- U1 MAX31856 (TSSOP-14): full 14-pin map independently matches the ADI
  datasheet (1/14 GND, 2 BIAS->TC_N per the typical operating circuit,
  3/4 T-/T+ through the 100R + 10n CM + 100n diff filter to J5 KF350,
  5 AVDD=3V3A, 7 DRDY_N, 8 DVDD=3V3A, 9-12 SPI CS0/SCK/MISO/MOSI,
  13 FAULT_N, 6 DNC). part.yaml "pending DS confirmation" flag satisfied.
- U12 AMS1117-3.3: 1=GND, 2+tab=3V3 out, 3=5VP in — not swapped.
- D1 SS34 (SMA): pad1 cathode = VSYS (Pico ORing diode) — correct.
- D2 SMBJ5.0A (SMB): pad1 cathode = 5VP, anode GND — correct TVS.
- SJ1: bridges DOOR_RAW <-> TH3_ADC only; open by default.

## Review 3 — connectors vs spec §8.5: PASS (17/17)
- J1 barrel: tip pad 1 = 5V_IN (center-positive per silk), sleeve = GND;
  feeds F1 fuse first. Note: footprint is the CUI PJ-063AH pattern for the
  DC-005-20A (same tip=pad-1 convention).
- J6 loadcell: 1=5VP 2=3V3 3=GND 4=HX_DAT 5=HX_CLK — PIN-FOR-PIN the
  cook-loadcell J6 (straight cable safe).
- J11 keypad: pins 2n-1/2n = KC{n}A/KC{n}B for all n=1..16, no
  transpositions.
- J2 Pico 2 socket 40/40 pins match RP2350 Pico pinout (grounds on
  3/8/13/18/23/28/33/38; VSYS 39; ADC_VREF 35).
- J3/J4/J14 I2C order 3V3/GND/SDA/SCL; J5 TC; J7 door (HALL_PWR/DOOR_RAW/
  GND); J8 e-stop; J9 NTC alternating TH/GND; J10 dry opto C/E only;
  J12/J13 DNP futures (shared-GPIO exclusivity noted); J15 DNP SPI;
  JP1/JP2 centre-common pullup selects; JP5 hall power option.

# cook-loadcell v1.0 — HX711 review: PASS after E- fix
- U1 HX711 SOP-16 full pin map matches the AVIA datasheet; AVDD =
  1.25 x 28.2k/8.2k = 4.30 V (<= VSUP-0.35 = 4.65 V) via Q1 SS8550
  (B/E/C = BASE/5V/E_PLUS); INA+/- = S_PLUS/S_MINUS; INB tied off; XI=GND
  (internal osc), RATE via JP1 (GND default 10SPS / DVDD 80SPS);
  DOUT=DAT, PD_SCK=CLK.
- SHIP-BLOCKER FOUND AND FIXED: E_MINUS was a floating 2-net island with
  no GND tie (no excitation return -> dead bridge in both modes). BRIEF D2
  E-=AGND: J3.2/J5.4 now land directly on GND; board rerouted; gate 0/0/0.
- Bridge ring topology exactly per D1; J5 = same 4 nodes + SH (R7||C7
  hybrid bond + SJ1 hard-short option). D1/D2 PESD5V0S1BA are
  BIdirectional — orientation electrically indifferent, pad1 on signal by
  CPL convention. J6 = 1:5V 2:3V3 3:GND 4:DAT 5:CLK.
- Advisory (open item): RATE_SEL floats if JP1's shunt is lost; a 100k
  pulldown would be cheap insurance next spin.

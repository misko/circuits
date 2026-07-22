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

# DETAIL_DESIGN — cook-loadcell (every value derived)

1. Excitation (D2): HX711 DS typical circuit: Q1 S8550 PNP, base from
   BASE pin; AVDD = VBG*(R1+R2)/R2 = 1.25*(20k+8.2k)/8.2k = 4.30 V from
   5 V in (headroom 0.7 V > Vsat + margin). R1 20k 1% (AVDD-VFB), R2 8.2k
   1% (VFB-AGND). C1 10u + C2 100n on AVDD/E+.
2. Bridge (D1): ring splices carried as fat 0.5 mm traces J-to-J; nodes
   E+/S+/E-/S- < 15 mm stubs into INA+/INA- and excitation. No series
   RC in the signal path (HX711 has internal 20 SPS-class LPF; the DS
   reference design goes direct for 4-wire bathroom-scale rigs).
3. Rate (D3): RATE = JP1 center; 1=GND (10 SPS dflt), 3=DVDD (80 SPS).
4. Digital: DOUT/PD_SCK straight to J6 with D1/D2 PESD5V0S1BA clamps at
   the connector; DVDD = 3V3 (C3 100n + C4 10u); VSUP = 5V (C5 100n +
   C6 10u). XI = GND (internal oscillator), XO = no_connect.
   INB+/INB- = AGND (channel B unused, DS-sanctioned tie).
5. Shield (D4): SH terminal -> R7 100R || C7 100n -> GND; SJ1 hard bond.
6. Thermals/EMI (§8.3): board sits under the platform, away from the
   oven body; the only clock on board is PD_SCK (bursts at read time).
7. Cost (§14.2): HX711 ~$0.6 + connectors ~$1.1 + Q1/passives ~$0.6 +
   PESD ~$0.15 => BOM ≈ $2.5 << $20 target.

# BRIEF — cook-loadcell (SMC0985KS Phase-1 load-cell daughterboard, spec PCB C)

Parent commission: `projects/smc0985-cook/` (01_docs/BRIEF.md P1-P10, A1,
D1-D3; BRIEF_SOURCE.txt sha256
cd254dd7bb7bb76cd497ab34355a6fdb7547ac7a7efa249265376371fd64e487 is the
authoritative spec — § references below are into that document).

This board is D1(b): spec §2.4 "PCB C" — the HX711 + bridge-combination
daughterboard, located under the appliance platform close to the load
cells, minimising microvolt-level analog cable length (§3.7a). It links to
cook-hub J6 over a 5-wire digital cable (5V, 3V3, GND, DAT, CLK).

## Requirements binding this board
- §3.7: four 50 kg 3-wire half-bridge load sensors OR one standard 4/6-wire
  full bridge (b); shield/drain termination (c); selectable 10/80 SPS,
  default 10 (d); short guarded analog, away from relays/clocks (e);
  calibration and raw-count test points (f); calibration constants live on
  the Pi/Pico (g) — nothing stored here.
- §8.2/8.3: locking connectors, strain relief, shielded/twisted cable.
- §14.2: BOM < $20.

## Decisions
- D1 (bridge topology): the four 3-wire half-bridge sensors wire as the
  classic series ring (each sensor's two outer gauge ends splice with its
  neighbours'), and the four RED centre-taps land on the four bridge nodes:
  J1.R=E+, J2.R=S+, J3.R=E-, J4.R=S-. A 4-wire full-bridge cell connects
  to the SAME four nodes through J5. MODE SELECT = POPULATION: plug either
  the four corner sensors or the one full-bridge cell — no jumpers, no
  shared-path failure modes. (§3.7b "support ... or ..." satisfied; both
  modes verified in bring-up checklist.)
- D2 (excitation): HX711 internal analog regulator drives E+ via the
  datasheet S8550 PNP + VFB divider R1/R2 = 20k/8.2k 1% -> AVDD = E+ ≈
  4.3 V from the 5 V input (best PSRR per HX711 DS "analog supply" note);
  E- = AGND. DVDD = 3V3 from the hub (RP2350-safe logic levels).
- D3 (rate select): 3-pin header JP1: RATE to GND (1-2, DEFAULT 10 SPS) or
  DVDD (2-3, 80 SPS). Shunt shipped on 1-2.
- D4 (shield): J5 pin 5 + a dedicated SH terminal land the cable
  drain/shield; bonded to GND through R7 100R || C7 100n (hybrid bond,
  keeps mains-borne shield noise from circulating through AGND); SJ1
  solder jumper shorts it hard to GND if bench EMI testing prefers.
- D5 (guarding): 2-layer board, solid bottom GND pour + top pour; bridge
  nodes routed as short daisy stubs in one corner; DAT/CLK + 5V/3V3 kept
  on the opposite edge; no clocks cross the analog nodes (audit-checked).
- D6 (connectors): JST XH throughout (locking, matches cook-hub family):
  J1-J4 = B3B-XH-A (B/R/W per sensor), J5 = B5B-XH-A (E+ S+ S- E- SH),
  J6 = B5B-XH-A (5V 3V3 GND DAT CLK — pin-for-pin the cook-hub J6).
- D7 (input protection ADR-0001): powered only from cook-hub's protected
  5VP/3V3 rails over a <1 m captive cable: no fuse/reverse stage repeated
  here; 100n+10u local decoupling per rail; PESD5V0S1BA on DAT and CLK at
  the connector (cable ESD). Recorded as the mandatory protection ADR.
- D8 (test points, §3.7f): TP E+, S+, S-, GND (raw bridge probing =
  calibration aid), TP DAT, TP CLK, TP 3V3. All SMD D1.5.

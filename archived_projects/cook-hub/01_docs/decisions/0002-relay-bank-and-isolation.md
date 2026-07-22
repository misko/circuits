# ADR-0002 — Relay selection, bank geometry, isolation implementation

Context: §6.2 wants 12–16 SPST-NO reed relays; §6.3 wants ≥1 kV contact-coil
isolation, two isolated pins per channel, no shared common, and 6–8 mm
clearance+creepage between keypad-contact copper and ALL SELV copper; §8.4
wants a slotted, silk-labelled, pour-free isolation zone; §15.4 wants the
relay on the do-not-substitute list.

Decision — part: Standex-Meder **DIP05-1A72-12L** ×16 (do-not-substitute):
- Pin-out code 12 (series DS p.3 Pin-Out figures): coil = pins 1,7 (one
  7.62 mm row), contacts = pins 14,8 (other row) — coil and contact copper
  land on opposite sides of the package axis, enabling a straight isolation
  boundary per relay.
- Dielectric coil/contact 1.5 kVDC (DS p.3 Relay Data, EN60255-27) ≥ 1 kV.
- Coil 5 V/500 Ω/10 mA (DS p.2); contacts 10 W/200 V/0.5 A model 72 (p.1).
- Active product (v03 datasheet Aug 2025); DigiKey-class availability;
  JLC catalog C1561362 stock 0 ⇒ hand-solder line, 16+spares via global
  sourcing. Approved alternate: DIP05-1A72-12D (identical pinout, internal
  diode cathode-to-pin-1; our net map keeps pin 1 = RELAY_5V so the alternate
  drops in without change). Rejected: HE721A0510 (obsolete + only 500 Vac),
  Cosmo S1A050000 (SIP: 2.54–5 mm coil-contact pin spacing < 6 mm), any
  unbranded reed relay (violates §15.4).

Decision — geometry: 8 super-columns × 2 rows, NE corner. Super-column pitch
15.24 mm ⇒ contact column to NEXT super-column's coil column = 7.62 mm gap
(6.12 mm pad-edge to pad-edge, ≥6 mm) with a 2 mm milled slot in every gap
(7) + 1 slot guarding the contact strip's west end. Contact traces (0.4 mm)
run only inside the comb region {north strip y<46 + 8 vertical corridors};
J11 (XKB X9555WV-2x16, keyed; channel n → pins 2n−1/2n) sits in the strip.
No copper pour of any layer enters the comb (L2 GND and L3 power outlines
stop 6 mm short); machine enforcement is three-fold:
1. `.kicad_dru` rule: clearance ≥6 mm between netclass KEYPAD and any other
   net (DRC-gated every rebuild);
2. audit I-ISO: independent geometric sweep of every KEYPAD pad/track vs
   every SELV pad/track/via/zone-fill, assert min ≥6.0 mm, plus slot-presence
   check in Edge.Cuts;
3. the twin/render review eyeballs the boundary silk ("ISOLATION BOUNDARY —
   KEYPAD SIDE", both sides marked).

§2.3 combine-conditions demonstration lives here: spacing (above),
serviceability (zone contains only THT relays + J11; patch harness per §6.9
detaches at the keyed header), routing (32 generator-drawn contact traces,
zero SELV crossings — checked by I-ISO).

LEDs on coils (§6.4 optional): omitted — COIL_n test points give per-channel
diagnosis without 16 extra parts; firmware status over USB covers §16.4.

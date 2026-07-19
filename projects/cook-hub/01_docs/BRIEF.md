# BRIEF — cook-hub (SMC0985KS Phase 1 sensor/control hub, PCB A + PCB B combined)

Parent commission: `projects/smc0985-cook/` (01_docs/BRIEF.md, P1–P10, A1, D1–D3;
BRIEF_SOURCE.txt sha256 cd254dd7bb7bb76cd497ab34355a6fdb7547ac7a7efa249265376371fd64e487
is the authoritative spec — § references below are into that document).

This board is D1(a): the spec's PCB A (Pico 2 sensor/control hub) and PCB B
(reed-relay keypad board) COMBINED on one 4-layer board, as §2.3 allows
"only if isolation spacing, serviceability, and routing remain satisfactory."
The demonstration of those three conditions is a release deliverable
(ADR-0002 + audit I-ISO + DRC rule `iso_keypad`).

## Requirements binding this board (from parent P#)
- P1 safety boundaries §1; P3 sensors §3 (except 3.7 analog → cook-loadcell);
  P4 pin allocation §5; P5 keypad/relay §6; P6 power §7; P7 layout §8;
  P8 firmware-interface skeletons §10/11/15.5; P9 cost §14.2; P10 validation §16.

## Decisions (this board)
- D4 (relay selection, DO-NOT-SUBSTITUTE per §15.4): Standex-Meder
  **DIP05-1A72-12L** ×16. Pin-out code 12 = coil pins 1,7 on one pin row,
  switch contacts pins 14,8 on the other row, rows 7.62 mm apart — the only
  stocked-family package geometry that lets a straight milled slot separate
  coil copper from contact copper under the part. Dielectric coil/contact
  1.5 kVDC (EN60255-27, series DS p.3) ≥ the §6.3 1 kV requirement. 5 V/500 Ω
  coil (10 mA). Approved alternate: DIP05-1A72-12D (same pinout, high profile,
  internal coil diode cathode = pin 1; wiring keeps pin 1 = +RELAY_5V so both
  variants drop in). Littelfuse HE721A0510 is OBSOLETE (DigiKey 2026-07) and
  only 500 Vac coil-contact — rejected. JLC stock is zero for all reed relays
  of this class → relays are a hand-solder line (global sourcing, DigiKey
  ~$4.36/1). Cosmo S1A050000 (JLC-stocked, $1.67) rejected: SIP package has no
  ≥6 mm coil/contact pin separation.
- D5 (watchdog IC): TI **SN74LVC1G123** single retriggerable monostable
  (genuine TI, JLC C123302). B input = rising-edge retrigger from Pico
  WD_PULSE; A=GND, /CLR=3V3. tw = K·R·C, K≈1: 390 kΩ 1% × 1 µF X7R → ~390 ms
  (spec window 300–500 ms holds over K 0.9–1.1, C ±10%). §6.5's monostable
  option; 74HC123 rejected (only clone stock at JLC). Do-not-substitute.
- D6 (watchdog toggle pin): §5 allocates no pin for the §6.5 watchdog input
  (spec gap). WD_PULSE = **GP5** (was spare). GP4 remains the spare digital.
  All §5 preserved resources remain intact.
- D7 (future headers J12/J13 share pins): the Pico exposes 26 GPIO and §5
  consumes all of them. J12 (encoder A/B/HOME) = GP21/GP22/GP4 and
  J13 (STEP/DIR/EN) = GP21/GP22/GP4 — same three nets on both DNP headers,
  encoder XOR motor use per §13.2/§13.3 (Phase 2 chooses; simultaneous
  closed-loop turntable needs Rev B). Satisfies §5 "three future turntable
  signals" + both §8.5 headers. Open item in §17 list.
- D8 (door EOL discrimination): NC loop with 10 kΩ end-of-line resistor
  ACROSS the switch at the far end, 3.3 kΩ pullup: closed = 0 V, open door =
  2.48 V (logic 1 via RP2350 built-in Schmitt), cut wire = 3.3 V. Digital
  open/closed on GP8; open-vs-broken discrimination is optional analog via a
  solder-link to spare ADC GP28 (SJ1, default open). "Where practical" §3.8d.
- D9 (K-type connector): PCC-SMP-K style miniature thermocouple PCB socket,
  vendored footprint, hand-solder, uncoded (not in JLC catalog). Silk
  polarity + "K-TYPE" label. §3.6c keyed requirement met by the keyed socket.
- D10 (MAX31865 provision §3.6e): CS1 (GP20) routed to DNP header J15
  (1×6: 3V3A GND SCK MOSI MISO CS1) next to J5 — a MAX31865/PT1000 breakout
  plugs in; second-CS footprint requirement satisfied without carrying an
  unpopulated QFN.
- D11 (I2C pullup select): per bus, 2.2 k pair and 4.7 k pair each enabled by
  a 3-pin 2.54 mm jumper (JP1/JP2 bus0, JP3/JP4 bus1 — shunt on = pair
  active). Ship-default: 2.2 k shunted (300 mm cable, MLX90640 load). Series
  damping 33 Ω fitted (0 Ω alternate listed); low-C ESD = USBLC6-2SC6 per bus.
- D12 (co-power/backfeed §7.1): board 5 V feeds Pico VSYS through SS34; Pico's
  internal VBUS→VSYS Schottky ORs USB power. RELAY_5V taps the protected rail
  UPSTREAM of the OR diode, so Pi USB physically cannot power relay coils and
  the board never backfeeds the Pi. VBUS socket pin → test point only.
- D13 (ESD parts): commodity SOD-323 5V TVS (UMW PESD5V0S1BA) and ST-clone
  USBLC6 acceptable on sensor lines (clone-risk = clamp tolerance, not
  safety); relay, watchdog, gating logic are genuine/do-not-substitute.
- D14 (contact-side header): J11 = XKB X9555WV-2x16 shrouded/keyed box header
  (2.54 mm), IDC-ribbon patch harness per §6.9; channel n on pins (2n−1, 2n),
  no shared common.

Every gate artifact lives per contracts; the §16-condensed bring-up checklist
ships in the release ORDER_README.

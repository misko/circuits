# ADR-0003 — Hardware watchdog + fail-safe relay power gating

Context: §6.5 requires a NON-firmware watchdog (300–500 ms) that kills both
the shift-register OE and the coil rail; §7.4 requires E-stop AND watchdog
each able to remove coil power, default-off unpowered.

Decision — watchdog: TI **SN74LVC1G123** (C123302, genuine TI, VSSOP-8,
do-not-substitute) as retriggerable monostable. B = WD_PULSE (GP5, 5–20 Hz),
A = GND, /CLR = 3V3, Q = WD_OK. tw = K·R·C ≈ 390 kΩ·1 µF ≈ 390 ms; tolerance
band 316–472 ms ⊂ [300,500] (DETAIL_DESIGN #3). Boot state: Q low until the
first edge ⇒ relays locked out until firmware is alive (§16.1).
Rejected: 74HC123 dual monostable — only clone stock at JLC (Sunmoon/UTC),
unacceptable for the safety element; fixed-timeout supervisor ICs
(TPS3823 1.6 s, STWD100 1.6 s/102 ms) — outside the 300–500 ms window.

Decision — gating (three independent locks, ARCHITECTURE):
- /OE = NAND(RLY_EN, WD_OK) via 74LVC1G00 with 10 k pullup on /OE and 10 k
  pulldown on RLY_EN (GP14): any of {unpowered logic, Pico unbooted, watchdog
  starved, firmware disable} ⇒ outputs Hi-Z ⇒ ULN inputs low ⇒ coils off.
- RELAY_5V high-side: AO3401A source-to-5VP, gate 47 k to 5VP (OFF default),
  pulled low by 2N7002 driven from 74LVC1G11 AND3(WD_OK, ESTOP_OK, RLY_EN);
  10 k bleeder discharges the rail. E-stop and watchdog EACH cut coil power
  independent of firmware (§7.4); firmware (RLY_EN) is the third series term.
- Flyback: ULN2803A COM diodes to RELAY_5V (§6.4); rail bulk absorbs the
  10 mA coil energy.

Single-fault review: a shorted Q1 alone still leaves /OE lock + per-channel
ULN off-state; a stuck-on ULN channel alone is stopped by the rail lock; a
stuck WD_OK-high requires a failed monostable AND a hung Pico simultaneously
— accepted for a supervised Phase-1 research rig (§1 boundaries keep worst
case = a phantom keypad press, which the OEM controller still validates).

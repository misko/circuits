# BRIEF — smc0985-cook (parent commission)

Source: 01_docs/BRIEF_SOURCE.txt — "SMC0985KS INTELLIGENT COOKING PROTOTYPE,
Phase 1 Sensor + Raspberry Pi Integration, PCB Design Requirements Rev 1.0",
stored VERBATIM. sha256: cd254dd7bb7bb76cd497ab34355a6fdb7547ac7a7efa249265376371fd64e487
User transmittal (2026-07-19): "Can you please launch an agent to help design
a support board for this project" + A1 below.

## Parsed requirements (summary — the source doc is authoritative)
- P1: Safety boundaries §1 are NON-NEGOTIABLE (no cavity electronics; no
  magnetron/heater/fan/interlock/mains connection; galvanically isolated
  dry-contact keypad emulation only; no Pi/Pico-to-keypad ground; LLM never
  commands hardware; relays default OFF in every fault state; hardware —
  not firmware — watchdog).
- P2: Modular partition §2; PCB A hub (Pico 2, sensors, relay drive,
  watchdog), PCB B relay/keypad (12-16 reed SPST-NO, 6-8mm creepage,
  combinable with A per §2.3), PCB C HX711 daughterboard, PCB D thermal
  port (optional).
- P3: Phase 1 sensor set §3 (MLX90640 I2C0, exhaust SHT45 I2C1, ambient
  SHT45 I2C0, MAX31856 SPI0 + spare CS for MAX31865, HX711, door NC loop
  w/ EOL resistor, E-stop NC, 2x NTC ADC, arc input reserve).
- P4: Pico 2 pin allocation §5 (alterable but preserve listed resources).
- P5: Keypad §6: donor teardown gates the interposer (§1.9/6.1/6.8 TBD);
  relay pairs exit to labeled connector + patch harness (§6.9); 74HC595 x2
  -> ULN2803A -> 5V reed coils; hardware watchdog §6.5 (monostable/WD IC,
  NOT firmware); heartbeat/timing §6.6-6.7.
- P6: Power §7: external SELV 5V >=2A, fuse+reverse+TVS, relay-coil rail
  behind hardware-gated high-side switch (watchdog AND E-stop can cut).
- P7: Layout §8: 4L preferred, isolation zone w/ slots + silk boundary,
  connector map J1-J14, full test-point list §8.6.
- P8: Firmware/protocol §10-11 (COBS/CRC32 USB CDC, packet classes, boot-
  safe states) — interface skeletons are a deliverable (§15.5).
- P9: Cost targets §14: hub <$60 BOM, relay board <$80, loadcell <$20,
  combined <$150.
- P10: Validation tests §16 must be reflected in bring-up docs.

## Q&A
- Q1: Board scope for Rev A? -> A1 (user, 2026-07-19): "please review this
  spec, can we consolidate? we are mostly interested in phase1 of the
  project right now. Pi5 will be a central to our efforts, whats the best
  way to approach this?" — user delegates consolidation review; Phase 1
  focus; Pi 5 central host confirmed.

## Decisions
- D1 (consolidation, per A1 + §2.3 allowance): TWO custom boards for Rev A.
  (a) cook-hub = PCB A + PCB B COMBINED on one 4L board with a milled-slot
  isolation zone (6-8mm creepage, no crossing pours, silk-labeled) — valid
  because §6.8/6.9 already externalize the donor-unknown FPC to a
  post-teardown patch harness/interposer, so the relay bank's keypad side
  is just 16 labeled isolated contact pairs on J11.
  (b) loadcell-hx711 = PCB C kept separate (microvolt bridge physics, §3.7a).
  PCB D deferred: MLX90640 breakout rides its module on <=300mm cable into
  hub J3 (§3.3 allowance). Donor-specific passive interposer = future third
  mini-project, gated on teardown (§1.9).
- D2: execution order: cook-hub first, loadcell-hx711 second (same engineer,
  sequential; shared 02_parts at the sibling level is NOT used — each child
  project self-contained per repo convention).
- D3: child projects: projects/cook-hub/, projects/cook-loadcell/.

# Journal — 00 commission (pluto-rx2-8way)

## 2026-07-27 18:00 — start

- did: commissioned `pluto-rx2-8way` from a verbatim brief (4 user utterances,
  sha256 `1bf0eca…`). Scaffold seeded from the pcb-design skill templates only —
  never from a sibling project (the coupling that let a clean-room agent read
  another board's design, 2026-07-20). `mates.yaml` deliberately NOT carried.
- result: 17 files, 9 stage folders + ROOT contract. No engineering spent.
- next: answer the timing question before any part is chosen — it sets the
  control interface.

## 2026-07-27 18:00 — iterate 1 (the timing frame)

- did: derived the blanking budget and the frame arithmetic against the user's
  proposed 8192/4096 steady-state dwells.
- result: **frame = 7x8320 + 4224 = 62,464 samples = 2.0821 ms**; **buffer =
  499,712 samples = exactly 8 complete sweeps** (488 x 1024). Efficiency 98.4%.
  Sweep rate 480.3 Hz; unambiguous Doppler +/-240 Hz.
  Blanking is dominated by the **AD9363 RX digital chain** (0.7 us FIR-bypassed,
  4.9 us at 128 taps), NOT by the RF switch (20-200 ns). The 128-sample
  allowance covers even the 128-tap case.
  Side finding, recorded because it constrains any future dwell change: the
  ideal frame is `15X/2`, which carries a factor of 3, and neither 500,000
  (`2^5 x 5^6`) nor 524,288 (`2^19`) has one — **no dwell length divides those
  buffers evenly.** 499,712 works only because the blank allowance moves the
  frame off `15X/2`.
- next: the control interface is now DERIVED, not chosen — SPI switch control
  (1-10 us) exceeds the entire 4.27 us blanking budget, so **parallel 3-bit
  select is fact-locked**.

## 2026-07-27 18:00 — iterate 2 (D-SPEC, two tensions found BEFORE architecture)

- did: tested the brief's numeric requirements against physics and the part
  universe, per the D-SPEC gate.
- result: **T1 — Ku/Starlink (10.7-12.7 GHz) is 2x beyond the AD9363's 6 GHz
  ceiling.** Downconversion is mandatory and FR4 is unusable at 12 GHz. P7 and
  A2 cannot be one RF chain. User chose (A5) to defer Ku to a separate project.
  **T2 — a 70 MHz-6 GHz directional coupler does not exist** (85.7:1 against a
  coupled-line structure that rolls off 6 dB/octave below its band), *and* the
  deeper objection: **directionality is not the property being bought.** A
  coupler separates forward from reverse waves; a receive antenna has one
  direction. A resistive pickoff meets the actual goal better — **-20 dB tap,
  0.42 dB main-line loss, 26 dB RL, flat DC-6 GHz** vs 6 dB for a resistive
  split. This REVERSES the user's A3 and is recorded as D3 **proposed, not
  applied**, pending explicit confirmation.
- next: sourcing spike (monolithic SP8T vs a 7x BGS12WN6 SPDT tree), then the
  T1/T2 ADRs.

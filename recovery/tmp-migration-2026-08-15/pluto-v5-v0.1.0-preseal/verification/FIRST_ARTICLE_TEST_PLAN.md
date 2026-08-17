# Pluto RX2 8-way v5 — first-article test plan

Status: required before any functional or production claim. This plan does not
authorize an order. Controller software is intentionally not supplied by this
hardware-only archive.

## Equipment and records

Use a current-limited 5 V bench supply, two DMMs, oscilloscope, logic analyzer,
thermal camera or thermocouples, calibrated two-port VNA, 50-ohm terminations
through 6 GHz, torque-controlled SMA tools and known-good cables/adapters.
Record board serial, ambient, instrument IDs/calibration state, setup photos,
raw Touchstone files, waveforms and the exact controller-image identity.

## A. Received-board and unpowered inspection

1. Compare layer mapping, outline and launches against the sealed Gerbers and
   JLC previews. Inspect all nine SMA bodies for edge seating and unobstructed
   mating access.
2. Verify that only the nine 0.45/0.25 mm U1 vias were filled/capped. Use the
   fabricator report and X-ray or cross-section evidence appropriate to the
   first-article risk; reject blanket treatment of ordinary vias.
3. Inspect identity, polarity, pin 1, solder joints and connector keying for all
   29 placements. Confirm J11 cannot be mated in reverse.
4. With power absent, measure resistance from VBUS and 3V3 to ground, continuity
   of ground shells/planes, absence of shorts between adjacent RF conductors,
   and isolation of USB D+/D- from the circuit.

## B. Current-limited first power

1. Leave J11 disconnected and apply 5.0 V with a conservative current limit.
   Stop on unexpected current, heating, odor or unstable rails.
2. Record VBUS, 3V3, supply current and startup waveform. Repeat at 4.75 V and
   5.5 V. Verify regulation and measure U1/D1 temperature to equilibrium.
3. Confirm the hardware-biased safe state while the valid 3.3 V rail is present.
   Do not infer a safe state when supply rails are absent or collapsing.

## C. Controller prerequisite and timing

Do not begin switching or RF acceptance until the user separately requests and
approves a controller image and that image has its own review/build evidence.
Program only through keyed J11 while the PCB is self-powered; do not connect a
Pi/debug-adapter power output.

After that prerequisite is met, independently capture every control line and
state marker. Verify reset/all-off behavior, break-before-make guard intervals,
one-hot selection of all eight paths, the programmed unique dwell sequence and
repeatability over power cycles. The requested 20 ms dwell capability must be
demonstrated on hardware rather than inferred from source. Retain the raw logic
capture and controller-image identifier.

## D. RF qualification

1. Calibrate the VNA at the SMA mating planes over 100 MHz to 5.9 GHz. Keep the
   source at or below 0 dBm and terminate all unused antenna ports in 50 ohms.
2. For each of eight selected paths, save S11, S21 and S22. Check insertion loss
   against <=2.0 dB through 1 GHz and <=3.5 dB at 5.9 GHz, return loss >=10 dB,
   and path-to-path loss spread <=1.5 dB.
3. For every selected state, measure common-to-off isolation to the other seven
   ports. Require >=30 dB through 4 GHz and >=25 dB at 5.9 GHz.
4. Repeat representative worst paths while observing control rails and thermal
   state. Investigate resonances, intermittent SMA launches or state-dependent
   supply coupling rather than averaging them away.

## E. Acceptance

Pass only when the received construction, power behavior, controller timing and
all eight RF paths meet their limits with traceable evidence. Any failure reopens
the design. The AD9363/AD9361-profile use beyond the published AD9363 range is a
recorded user risk and must not be relabeled as guaranteed transceiver support.

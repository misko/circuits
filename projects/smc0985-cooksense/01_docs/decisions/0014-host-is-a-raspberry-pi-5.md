# ADR-0014 — The host is a Raspberry Pi 5, decided explicitly

status: accepted
date: 2026-07-26
tags: host, i2c, firmware, power, thermal, safety

## Context

The Pi 5 was never chosen. It was ASSUMED — by `BRIEF.md` (which names it in
the opening paragraph and again in the §16 design-freeze summary), and then
built upon by ADR-0004 and ADR-0010 until the whole sensor bus architecture
depended on it. No ADR ever recorded the host as a decision with its
alternative, so nothing pointed at what would break if someone swapped it.

That gap was found the way these are usually found: the user asked "Pi 4 or
Pi 5, is there a big difference?" and the answer had to be reconstructed from
general Raspberry Pi specifications, because the project's own record did not
answer it. Two successive recommendations for a Pi 4 were given and both were
wrong, for reasons that were sitting in this folder the entire time.

This ADR exists so the next person asking gets an answer from the repo instead
of from a search engine.

The same class of defect has already cost this fleet a full margin
re-derivation: usb-hub-3s-v3 carried an unrecorded "Pi 5 at 5 A" premise
through four releases, and correcting it to a Pi 4 at 3 A moved the delivery
headroom from +15.0 mV to +247.8 mV WITH NO HARDWARE CHANGE (usb-hub ADR-0004).
An unrecorded host assumption is not a small thing.

NOTE: usb-hub-3s-v3 is a SEPARATE PROJECT and does not power this board.
`J_PI` is signals-only ("Pi power NC/sense"); cooksense takes its own 5 V on
`J_PWR`. That confusion was made during this evaluation and is recorded here so
it is not made again.

## Options

- **Raspberry Pi 5** — CHOSEN. Four I2C controllers reachable on the 40-pin
  header via RP1 dtoverlays; two 4-lane CSI connectors; Cortex-A76 @ 2.4 GHz
  (three microarchitectural generations past the A72, higher IPC, 16 nm);
  PCIe 2.0 ×1 for NVMe; an RTC in the PMIC. Costs: 5 V/5 A (25 W) supply,
  active cooling under sustained load, and GPIO through RP1 — `libgpiod` v2
  only, no `RPi.GPIO`/sysfs.

- **Raspberry Pi 4** — REJECTED, and the reason is architectural rather than
  performance. ADR-0004 moved both MLX90640s (both at 0x33) and both SHT45s
  onto NATIVE Pi I2C buses, one per cable run, point-to-point with no
  branching, and concluded the brief's C5 PCA9548A mux fallback was
  unnecessary. That conclusion rests on the Pi 5 exposing up to four header
  I2C buses through RP1. A Pi 4 does not, so choosing it would reinstate the
  mux — a part, a board revision, an address layer, and a failure mode that
  ADR-0004 deliberately removed. ADR-0010 then published a Pi-5 NATIVE pin map
  that a Pi 4 cannot honour. Pi 4 would also give one CSI port instead of two,
  and no RTC for cook-log timestamps.

  It is genuinely better on two axes and they were weighed: a lower supply
  requirement (15 W), and a decade of mature `RPi.GPIO` examples for the
  watchdog pet. Neither outweighs re-opening the I2C architecture.

## Decision

**The host is a Raspberry Pi 5.** Confirmed by the user 2026-07-26. ADR-0004
and ADR-0010 stand unchanged; this record makes the dependency they created
explicit rather than implicit.

## Consequences

**Committed to, and must hold:**

- **`WD_PET` MUST be driven via `libgpiod` v2.** Pi 5 GPIO is behind RP1;
  legacy `RPi.GPIO` and sysfs paths do not work. This is the hardware
  watchdog pet on a cooking-contactor interlock, so it is the one GPIO the
  safety chain rides. The failure direction is safe — a missed pet trips the
  TPS3823 and drops the contactor — so the risk is nuisance trips, not a
  defeated watchdog. Firmware must not copy a Pi 4 example.
- **I2C bring-up notes are NOT portable.** Pi 5 requires the Pi-5-specific
  overlay form (`dtoverlay=i2c1-pi5,pins_10_11`), not the Pi 4 generic
  `dtoverlay=i2c3`. ADR-0010's pin map assumes the Pi 5 form.
- **5 V / 5 A (25 W) supply for the Pi.** Note this is a NEW obligation on a
  supply nobody has specified: `J_PWR` feeds cooksense, and the Pi is powered
  separately by something no document names. See open questions.
- **Active cooling.** Sustained OCR plus sensor fusion will run the Pi 5 hot
  enough to need a fan or a substantial heatsink.

**Available because of this, and worth using:**

- Two CSI connectors, each with its own I2C — the display-OCR camera can be a
  controlled-exposure CSI part rather than an auto-everything USB webcam.
- An RTC in the PMIC. A cook log without wall-clock time is much less useful,
  and the Pi 4 has no RTC at all.
- PCIe → NVMe, if SD-card wear on a logging workload becomes a problem.

**What breaks if this is reversed:** ADR-0004's point-to-point native-I2C
architecture and ADR-0010's published pin map both collapse, the PCA9548A mux
fallback returns as a board change, and one CSI camera has to move to USB.
Reversal is a board revision, not a configuration change.

**OPEN, and both belong in `BRIEF.md` — neither is recorded anywhere:**

1. **How many RGB cameras, and is one of them doing display OCR?** The brief
   says "cameras" plural and never says how many or CSI-vs-USB. This is the
   requirement that would have justified the host choice on its own merits
   rather than by architectural dependency.
2. **Where does the Pi physically sit relative to the hot enclosure?** The
   brief caps the enclosure at 50/55/65/75 °C and puts the MLX90640
   ELECTRONICS outside the cavity, so a cool zone is implied but never stated
   for the Pi. If the Pi shares the hot volume, its fan is a maintenance
   liability in steam and grease, and it becomes a heat source next to the
   ambient SHT45 that defines `DELTA_AH`.

**Contract drift observed, not fixed here:** `01_docs/decisions/contracts.md`
specifies `---`-delimited frontmatter (`id`, `date`, `status`); ADRs 0004
through 0013 use plain `status:`/`date:`/`tags:` lines after the title. This
file follows its neighbours for consistency. The template and the practice
should be reconciled in one pass rather than one file at a time.

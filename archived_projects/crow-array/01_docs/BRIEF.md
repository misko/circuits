# BRIEF — crow-array

Commissioned: 2026-07-18, via /pcb-design. The verbatim commission document
(Crow Acoustic Localization Array — Rev-A Working Design, text edition,
~30KB) is stored VERBATIM in BRIEF_SOURCE.txt beside this file; its sha256
is 21e54984c7ff5f75d25ff661e5f3b2557fd441ba2e95a9f672d0f301517ece0a. This BRIEF carries the parse,
Q/A, and decision register.

## Parsed requirements (from the Rev-A working design)

- P1 SYSTEM: outdoor crow-call localization; six active-balanced mic pods
  (25 ft radius hexagon) -> one shared-clock 8-channel-capable USB
  recorder -> Raspberry Pi 5. One physical sample clock for all channels;
  NO GPS timing (contrast: crowsync-recorder project).
- P2 POD BOARD (2-layer, 6-8 units): AOM-5024L-HD-R electret (3.9k bias
  from filtered 5V), OPA1678IDR two-stage active-balanced driver (~3 V/V
  diff, 68R output isolation per leg, 100k bias to 2.5V midpoint,
  10k/10k decoupled divider, 1uF coupling), CMT-8504-100-SMT-TR
  calibration transducer (5V/150mA, driven from CENTRAL via dedicated
  pair; no local driver), optional TPD2E2U06 ESD, cable via gland to
  terminal block/pads. Hammond 1551WYBK enclosure target. Conformal coat
  except mic/transducer/connectors/TPs.
- P3 CENTRAL BOARD (4-6 layer): XU316-1024-TQ128-I24 + 2x PCM1865DBTR
  (TDM, shared MCLK/BCLK/LRCK/reset; app-PLL 48kHz; async UAC2),
  W25Q16JVSSIQ QSPI, FA-238 24MHz, NC7NZ34K8X MCLK buffer,
  USB4105-GF-A-060 + TPD4EUSB30DQAR, SHT40-AD1B-R2, 8 RJ45 (RJHSE5384)
  footprints / 6 populated, per-port: TPD2E2U06 analog ESD +
  MINISMDC050F-2 PTC + diff AC coupling + AO3400A low-side beeper driver
  (slowed edges, separate return). Rails: 5V in (Mean Well GST25A05),
  2x AP61102Z6-7 bucks (3.3V dig, 0.9V core), TCR2LF18 1.8V,
  XC6227C331PR-G 3.3V analog LDO. Copy XMOS multichannel audio platform
  reference design for power sequencing/clocking/USB. Test points on all
  rails/clocks/TDM/beeper returns; same-signal injection header.
- P4 CABLING: custom Cat5e star pinout (NOT Ethernet): orange=AUDIO+/-,
  green=+5V_BEEP/BEEP_SWITCHED_RETURN, blue+brown=+5V_AUDIO/GND_AUDIO
  paralleled. Label everything "NOT ETHERNET".
- P5 CALIBRATION: coded 4kHz bursts (31-chip PN, 5-10ms chips, x4/pod),
  one pod at a time; survey + portable-source workflow (software scope).
- P6 BUILD SEQUENCE (the brief's own risk gating): pod prototype ->
  cable test -> outdoor transducer range test -> USB firmware on XMOS
  EVAL BOARD -> only then the custom central PCB.
- P7 Deliberately configurable: input RC/gain, beeper clamp type
  (flyback vs TVS), CM choke footprints, shield pads, 2 spare ports,
  waterproof-mic daughterboard, clock/injection points.
- P8 Non-goals for the PCBs: Pi 5 subsystem, firmware, enclosures,
  cabling install, localization software.

## Q / A

- Q1 scope: A1 (user, 2026-07-18): **BOTH boards now** — pod board and
  central recorder both designed in this campaign (overrides the doc's
  sequential gating for the PCB work; field-test gates still apply to
  ORDERING/mechanical freeze, recorded in each ORDER_README).
- Q2 assembly: A2: **JLC SMT + hand-solder specials** — mic, transducer,
  terminal blocks, RJ45s as uncoded hand-solder lines with a Digi-Key
  order list in ORDER_README.
- Q3 configurables: A3: **delegated** — dual clamp footprints (flyback
  populated, TVS empty), gain per the doc's starting values, CM-choke +
  shield pads unpopulated; each a D# with rationale.

## Decision register

- D1 (2026-07-18): two-board system implemented as TWO sibling pipeline
  projects sharing this commission: projects/crow-array-pod (2-layer,
  qty 8-10) and projects/crow-array-central (4-6 layer XU316 recorder).
  Each carries the full contract set and its own release chain; both
  BRIEFs point here. Rationale: the pipeline's contracts, gates, and
  release model are per-board.
- D2: execution order pod -> central (limits concurrent writers in the
  repo alongside the active shitty-kitty run; also matches the doc's
  risk ordering) — both are in scope per A1.

## Log

- 2026-07-18: commissioned; skeleton + contracts created; verbatim source
  stored (sha256 recorded on commit).

# ARCHITECTURE — crowsync-recorder

USB-powered stereo acoustic recorder around the PCM2900CDBR USB audio codec.
CH1 (VINL) records an outdoor electret microphone through a TLV9062 preamp;
CH2 (VINR) records the GNSS PPS waveform so every audio sample can be mapped
to UTC on the host. All engineering math in `DETAIL_DESIGN.md`; decisions in
`decisions/`. Net facts live in `03_src/rules/nets.yaml`.

## Power tree

```
USB-C VBUS 5V (J1, UFP: 5k1 on CC1+CC2)
 ├── VBUS_5V rail (10u bulk + 100n)                    <= 80 mA total
 │    ├── R7 2R2 -> VBUS_PCM -> U1 PCM2900C pin 3      ~60 mA typ (bus-powered,
 │    │     (1u at pin; datasheet fig 38 input filter)   ALL codec supplies are
 │    │     internal-regulator pins: decouple only)      internal from VBUS)
 │    ├── U3 TPS7A2033 LDO -> 3V3A (low-noise analog)  ~2.5 mA
 │    │    ├── U2 TLV9062 supply (preamp + VCOM buffer) 1.1 mA
 │    │    └── FB1 ferrite -> MIC_BIAS_F -> R8 2k2 -> mic capsule  0.5 mA
 │    └── R18 -> D4 power LED                           ~1.5 mA
 └── (D1 USBLC6-2SC6 clamps VBUS/D+/D- at the connector)
```

The codec is **bus-powered**: VCCCI/VCCP1I/VCCP2I/VCCXI/VDDI (nets of the
same names) are internal-regulator OUTPUTS that get decoupling caps only
(PCM2900C SBFS039 Table 1 note 4, Figure 38). The TPS7A2033 3.3 V rail
powers only the analog front-end — see `decisions/0002`.

## Signal chains

```
CH1  J2.1 (MIC net, bias+signal on one wire)
       ├── D2 ESD clamp (at connector)          ├── R8 2k2 bias from MIC_BIAS_F
       └── R9 100R series -> C19 1u AC couple -> U2A noninv preamp
             (input biased to VCOM_BUF via R10 100k)
           gain 1+Rf/Rg = 4.0x shipped (-24dB capsule), 40x alt (decisions/0003)
       -> R13 100R + C21 1n RC -> C9 1u -> U1 VINL (pin 12)

CH2  J3.1 (PPS net, 3.3V CMOS)
       ├── D2 ESD clamp (at connector)
       └── R14 100R series -> R15 22k / R16 10k divider (-> 1.03 Vpp)
       -> C10 1u AC couple -> U1 VINR (pin 13)

VCOM (U1 pin 14, ~VCCCI/2) -> U2B unity buffer -> VCOM_BUF (preamp DC reference)

USB  J1 D+/D- -> D1 USBLC6 -> R1/R2 22R series -> U1 pins 1/2
     R3 1k5 pullup: U1-side D+ -> VDDI (full-speed attach, fig 38)
     Y1 12MHz crystal on XTI/XTO (pins 21/20) + R6 1M + C5/C6 load caps
```

## Net domains

| Class (nets.yaml) | Nets | Why special |
|---|---|---|
| `PWR` | VBUS_5V, VBUS_PCM, 3V3A, MIC_BIAS_F | supply distribution; 0.3 mm floor (backstop — currents are < 0.1 A) |
| `USB` | DP_C, DM_C, DP, DM | full-speed differential pair: route as a tight, short pair over unbroken GND, no stubs, ESD at the connector end |
| Default | analog + everything else | MIC/AMP nets are noise-sensitive: shortest paths, GND pour guarding, away from Y1 and USB |

## Stackup (4 layer, JLC7628)

| Layer | Use |
|---|---|
| F.Cu | components + all signal routing |
| In1.Cu | **continuous GND plane — never split, no crossings** (P5, decisions/0004) |
| In2.Cu | power islands: VBUS_5V, 3V3A |
| B.Cu | GND pour + overflow routing |

## Ground strategy

One continuous ground (decisions/0004). AGND/DGND partitioning is done by
COMPONENT PLACEMENT, not plane splits: analog front-end (U2, bias, dividers,
J2/J3) occupies the east region; USB entry + crystal stay west/central.
Codec AGNDC/AGNDX/AGNDP/DGND/DGNDU all tie to the one plane at their pins.
Return currents separate naturally because the signal traces above the
plane don't cross domains.

## Critical geometries

- **USB pair**: J1 -> D1 -> R1/R2 -> U1 pins 1-2, < 15 mm, matched, over solid
  GND. ESD array nearest the connector.
- **Crystal**: Y1 + C5/C6 + R6 within ~5 mm of pins 20/21; GND pour ring; keep
  MIC/AMP nets > 5 mm away; no traces under Y1 on F.Cu.
- **Mic path**: J2 -> D2/R9/bias -> U2 -> C9 -> VINL kept in the east/south
  analog region, never parallel to DP/DM or under Y1.
- **Codec analog pins** (10-14, 17-19, 22-23): decouplers within 2 mm, own
  via to plane.
- **USB-C receptacle**: west edge, centered — > 10 mm clear of both west
  mounting holes (P5); connector overhangs the board edge for enclosure wall
  clearance.
- **Mounting**: 4x M2.5 (2.7 mm drill) at 4 mm corner insets; screw-head
  keepout audited (audit_board.py I4/I5).

## Connectors

| Ref | Part | Pinout |
|---|---|---|
| J1 | USB-C receptacle GCT USB4105-GF-A (UFP) | VBUS/GND/D+/D-/CC1/CC2/shield |
| J2 | JST GH 3-pin horizontal (mic harness -> enclosure M8) | 1 = MIC (bias+signal), 2 = GND, 3 = shield->GND |
| J3 | JST GH 2-pin horizontal (PPS harness) | 1 = PPS (3.3 V CMOS), 2 = GND |

Different pin counts on J2/J3 = physical keying against harness swaps.

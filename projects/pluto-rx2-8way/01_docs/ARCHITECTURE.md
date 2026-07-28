# ARCHITECTURE — pluto-rx2-8way

What the board IS. Why it is that way lives in `decisions/`; the machine-
readable net facts live in `03_src/rules/nets.yaml` and
`03_src/rules/power_tree.yaml`; every component value is derived in
`DETAIL_DESIGN.md`. Nothing is restated across those boundaries.

## 1. The one-paragraph description

An eight-element antenna selector for angle-of-arrival on an ADALM-PlutoPlus
**RX2**. A single absorptive SP8T (`U_SW`, pSemi PE42482A-X) sits at the
geometric centre of a ring of ten vertical SMA jacks and connects one of eight
antennas to Pluto RX2 at a time. **Element 8 is not a dedicated antenna: it is
the RX1 antenna, tapped** through a two-resistor pickoff so that RX1 keeps its
own connection to the Pluto and loses only 0.43 dB. A free-running RP2040 PIO
walks the three select bits, dwelling **8192 clean samples** on each of the
seven ordinary elements and **4096** on the tapped reference; the asymmetry is
the frame marker, so the host synchronises without a calibration pass.

## 2. Signal chain

```
J_ANT1 ─ ANT1 ────────────────────────────────┐
J_ANT2 ─ ANT2 ────────────────────────────────┤
J_ANT3 ─ ANT3 ────────────────────────────────┤   U_SW
J_ANT4 ─ ANT4 ────────────────────────────────┤  PE42482A-X   RX2_OUT
J_ANT5 ─ ANT5 ────────────────────────────────┤   SP8T   ├──────────── J_RX2 → Pluto RX2
J_ANT6 ─ ANT6 ────────────────────────────────┤ absorptive
J_ANT7 ─ ANT7 ────────────────────────────────┤
                                              │
J_ANT8 ─┬─ RX1_MAIN ── R_T1 ─ RX1_TAP_MID ─ R_T2 ─ RX1_TAP ─┘   (RF8)
(the RX1 │   220 Ω                              220 Ω
antenna) └──────────────────────────── J_RX1 → Pluto RX1

                 SEL_V1..SEL_V4 ─[R_S1..R_S4 47 Ω]─ SW_V1..SW_V4 ─ U_SW
                        ▲                                   │
                      U_MCU (RP2040 PIO)            R_PD1..R_PD4 10 kΩ ─ GND
```

Nine RF ports leave `U_SW` on three of its four sides; the fourth side (pins
7–12: GND, VDD, V1–V4) carries the entire digital interface and faces the
escape corridor. That is the pin-out's own shape, and the floorplan is built on
it rather than against it — see `decisions/0007-radial-star-floorplan.md`.

## 3. Power tree

One conversion stage. **Machine-readable envelopes live in
`03_src/rules/power_tree.yaml`** (the E-TOPO / E-MARGIN / E-OFF input); this
section is the picture.

```
USB-C host  ──►  J_USB  ──►  VBUS  ──[F_IN 500 mA PPTC]──►  VBUS_F
                                                              │
                                        D_TVS (cathode) ──────┤
                                        C_BULK 4.7 µF ────────┤
                                                              │
                                                     [FB_IN ferrite]
                                                              │
                                                          VBUS_LDO
                                                              │
                                                        U_LDO (linear)
                                                              │
                                                             3V3 ──┬── U_MCU  (RP2040, ~50 mA)
                                                                   ├── U_FLASH (QSPI, ~5 mA)
                                                                   ├── U_SW    (200 µA max)
                                                                   └── indicators + pull-downs
```

| rail | Vin | Vout | I (envelope) | conversion |
|---|---|---|---|---|
| `VBUS` / `VBUS_F` | 4.75 – 5.25 V (USB 2.0 limits at the device end) | — | 0.15 A | none — protected only |
| `3V3` | 4.75 – 5.25 V | 3.20 – 3.40 V | 0.15 A design envelope (~0.06 A typical) | **LINEAR** |

`Vout_max (3.40) < Vin_min (4.75)` ⇒ step-down ⇒ **a linear regulator MEETS
the requirement**, and on this board a switching regulator is REJECTED
regardless of efficiency: its switching harmonics would sit ~25 mm from a
nine-arm receive fan whose purpose is measuring small phase differences.
The regulator's dropout and dissipation bounds, and the two hard selection
constraints it must satisfy, are derived in `DETAIL_DESIGN.md` §5.

**De-energization** is unplugging the cable: the board carries no
self-contained energy source, holds ≤6.1 µF of bypass, and stores nothing.
Declared in `power_tree.yaml` so E-OFF grades it as N-A for a stated reason
rather than by the file's silence.

**Protection posture — including what is deliberately absent** — is
`decisions/0004-input-protection-posture.md`. The headline a reader must not
miss: **there is no ESD device and no DC block on any of the ten RF ports**,
and that is a decision with a reversal trigger.

## 4. Net domains

Classes and widths live in `03_src/rules/nets.yaml`; they are not restated
here, because two homes drift.

| class | what makes it special |
|---|---|
| `RF50` | the nine radial arms plus `RX1_MAIN` / `RX1_TAP_MID` / `RX1_TAP`. The width is an **impedance** width, so widening it is as wrong as narrowing it. L1 only, **no vias**, solid L2 underneath, fenced at ≤1.37 mm |
| `CTRL` | `SEL_V1..4` / `SW_V1..4`. Its impedance is load-bearing: it sets the series-termination value that keeps the switch's 3.6 V digital absolute maximum from being exceeded by reflection. **No shunt capacitance anywhere** — an RC that would be harmless on a static control net costs more than the entire blanking allowance |
| `USB_D` | `USB_DP` / `USB_DM`. The binding rule is the **reference plane**, not the impedance |
| `PWR` | `VBUS`, `VBUS_F`, **`VBUS_LDO`**, `3V3`. Width for IR drop and robustness, far above the ampacity need. `VBUS_LDO` is FB_IN's output — a ferrite is a series element, so it is a fourth net, not a continuation of `VBUS_F`. It was missing from the class until the stage-2 merge, where it would have defaulted to the 0.25 mm class and been graded as a signal while carrying the whole 0.15 A |
| `QSPI` | the execute-in-place bus — the board's only continuous in-band spur source, so "short" is an EMI rule here |
| `DVDD_1V1` | **the 1.1 V core rail, and it is real copper no gate can grade.** RP2040's core regulator is on-die; its output leaves at `VREG_VOUT` (pin 45) and must be wired back IN COPPER to `DVDD` (pins 23, 50). A board that omits the link looks correct in every artifact — `VREG_VOUT` reads as an unused output, `DVDD` as an undriven supply — and no ERC, DRC or parity check objects. E-TOPO cannot grade it either, because the converter is inside the MCU; typing an MCU as a converter to make a rail appear would be worse than the gap |
| default | `LED_PWR`, `LED_STAT`, `RUN_N`, `BOOTSEL_N`, `XIN`, `XOUT`, `USB_CC1`, `USB_CC2` |
| `GND` | pours + stitching on all four layers; no netclass width. `U_SW` pin 1 (LS) is **on this net**, by a via at the pad |

## 5. Stackup

`JLC04161H-7628`, 1.6 mm, 4 layers, **impedance control requested**. Chosen and
refuted-against in `decisions/0003-stackup-and-fab-tier.md`; the derived
constants are in `DETAIL_DESIGN.md` §1.

| layer | | function |
|---|---|---|
| L1 | 35 µm | RF microstrip (0.36 mm = 50 Ω), the pickoff cell, the USB pair |
| | 0.2104 mm prepreg 7628, Dk 4.4 | |
| L2 | 35 µm | **SOLID GND** |
| | 1.065 mm core | |
| L3 | 35 µm | control bus, QSPI, 3V3 — the digital escape layer |
| | 0.2104 mm prepreg | |
| L4 | 35 µm | GND |

Fab tier **`jlc_4layer_advanced`**, forced by one package and one line of
arithmetic (0.50 mm pitch − 0.30 mm standard drill = 0.20 mm against a 0.50 mm
hole-to-hole floor).

## 6. Ground strategy

- **L2 is solid and unbroken under every RF arm and under the USB pair.** That
  is the single most important routing rule on this board: nine arms sharing
  one reference is what makes their phases comparable at all.
- **No plane splits anywhere.** 3V3 is a pour on L3 confined to the digital
  strip plus tracks; there is no power plane, so the RF reference is never
  something else's return path.
- **Ground-via fences** flank every RF arm at ≤1.37 mm pitch (λg/20 at 6 GHz)
  and run between adjacent SMA barrels. The 2.39 mm flange-to-flange gap the
  ring radius buys exists to hold that fence — it is the port-to-port
  isolation budget, not spare board area.
- **Each SMA's four ground posts land on plane copper with their own via
  cluster**, not on a shared pour neck: the posts are the launch's return path
  and are only electrically short if the return is.
- **`U_SW`'s exposed pad is the RF ground return for all nine ports** and gets
  a via array to L2. `LS` (pin 1) takes its own via at the pad — it is a logic
  input AND an RF ground.

## 7. Critical geometries

The things a router will destroy if it does not know:

| geometry | rule | why |
|---|---|---|
| the nine radial arms | equal length, 17.85 mm, L1, no vias, no layer changes | equal length is equal phase by construction, and equality is what bounds thermal DIFFERENTIAL drift (`decisions/0006`) |
| `RX1_TAP_MID` | pad-to-pad span ≤ **1.37 mm** (λg/20) | it is the interior of a lumped element; longer and the two-resistor arm becomes a transmission line with its own delta |
| `R_T1` / `R_T2` | **identical rotation, never mirrored**; same reel | ~0.1 nH of mounting-inductance asymmetry ≈ 2° at 6 GHz. A CPL fact, invisible at export time |
| `U_SW` pin 1 (LS) | ground via centre within **0.5 mm** of the pad centre | it is an RF ground per Table 3 fn 1; a trace is not one. Note this budget is NOT machine-gradeable — see `decisions/0005` |
| `SW_VDD` bypass | ≤3 mm span | the part's own layout block |
| `SW_V4` pull-down | ≤4 mm span | a floating V4 mutes the receiver silently |
| the escape corridor | 90° sector centred straight down off pins 7–12, 4 mm deep, no pours, no footprints | the only side of the package with no RF on it |
| SMA launches | bottom-plane antipad ≥ Ø3.5 mm under the centre barrel | a tight antipad is a capacitive discontinuity that shows up as return loss at 6 GHz, and the correction is geometric, not tunable later |

## 8. The timing frame (D1) — CLOSED, and it is a DESIGN INPUT

The frame is fixed and the arithmetic is why the control interface is what it
is. Restated here because the board cannot be understood without it:

| quantity | value |
|---|---|
| dwell, ordinary element | 8192 clean samples |
| dwell, tapped reference (element 8, on RF8) | 4096 clean samples |
| blanking allowance per hop | 128 samples = **4.267 µs** |
| frame | `7 × 8320 + 4224` = **62,464 samples = 2.0821 ms** |
| sweep rate | **480.3 Hz** |
| buffer | **499,712 samples = exactly 8 complete sweeps** (= 488 × 1024), 16.657 ms at 30 Msps |
| sample efficiency | **98.4 %** |

Two accepted costs: per-element revisit at 480.3 Hz ⇒ **unambiguous Doppler
±240 Hz**, and a signal must persist ≥2.08 ms to appear on all eight elements.

**The arithmetic finding that constrains any future dwell change:** with seven
full dwells and one half dwell the ideal frame is `15X/2`, which carries a
factor of 3 — and neither 500,000 (2⁵·5⁶) nor 524,288 (2¹⁹) has one. **No dwell
length divides those buffers evenly.** 499,712 works only because the 128-sample
blank allowance moves the frame off `15X/2`.

**The blanking allowance is spent, not spare** (`decisions/0005`, itemised):
2183 ns of the 4267 ns with the RX FIR bypassed — a 1.95× margin — and
**6383 ns, i.e. a 1.5× overrun, with a 128-tap FIR**.

## 9. Receiver configuration this design DEPENDS on — DESIGN INPUTS, not preferences

**The frame arithmetic in §8 is FALSE without all three.** They are firmware/
host settings, not board features, and they are recorded here with the same
standing as a component value because the board cannot enforce them:

1. **MGC, not AGC.** AGC settling is tens of microseconds and would swamp a
   4.267 µs budget several times over.
2. **RX FIR bypassed or short.** A 128-tap FIR at 30 Msps smears ~4.9 µs —
   more than the whole allowance (see the §8 table). Bypassed, the halfband
   chain contributes ~0.7 µs.
3. **DC-offset and quadrature tracking FROZEN.** Otherwise the loops chase
   each element's offset on every hop, and what they chase is a function of
   which antenna is selected — i.e. they would inject exactly the
   state-dependent variation that `decisions/0006` exists to eliminate.

Two more, added by this stage:

4. **RP2040 pad drive = 2 mA, slew = slow** on the four select lines. Good
   practice, deliberately NOT load-bearing — the 47 Ω series resistors already
   hold the switch's absolute-maximum bound at the strongest setting.
5. **The host must have a DARK-FRAME mode**: `V4 = 1` with `V1..V3 = 0` puts
   every port in its terminated state, and that measurement is the calibration
   source for the leakage subtraction §10 depends on.

## 10. What this board does NOT solve, stated up front

- **The reference dwell is LEAKAGE-limited above ~2 GHz** — spec tension T3,
  found at stage 3 and quantified in `decisions/0002`. The tapped reference
  sits 20.26 dB below a plain element while the seven live elements leak into
  RFC through the switch's finite isolation, so the reference-dwell SIR runs
  from **+34.7 dB at 10–100 MHz down to +1.2 dB at 4–6 GHz** on guaranteed
  specs. **No tap value fixes it** — even a lossless 3 dB split reaches only
  ~18.5 dB at the top of the band. The fix is that the interference is
  computable from measurements the same frame already contains.
- **Ordinary element dwells are fine**: +21.7 dB SIR at 4–6 GHz, ≈4.75° of
  worst-case phase pull.
- **Port-to-port isolation across ten SMA barrels on one laminate is
  UNMEASURED** and bounds the AoA leakage budget independently of the switch
  (`02_parts/README.md`). A −21.5 dB switch behind a −18 dB connector field is
  a −18 dB board. §9's dark-frame mode exists to measure it.
- **Ku/Starlink is out of scope by decision** (`decisions/0001`), not by
  omission.

# ARCHITECTURE — pluto-cal-switch

What the board IS. Why it is that way lives in `decisions/`; the arithmetic
lives in `DETAIL_DESIGN.md`; the machine-readable net facts live in
`03_src/rules/nets.yaml` and `03_src/rules/power_tree.yaml`.

---

## 1. What it does

A 5-port RF adapter for an ADALM-PlutoPlus with two states, selected by one
control bit.

| control | RF topology |
|---|---|
| **OFF (0)** — power-on default | `RX_ANT1 → RX_PLUTO1` and `RX_ANT2 → RX_PLUTO2`, two independent through paths |
| **ON (1)** | `TX_PLUTO → pad → 2-way split → pad → RX_PLUTO1` **and** `→ pad → RX_PLUTO2`, the two runs length-matched |

Band 70 MHz – 6 GHz, 50 Ω, 30 dB nominal TX→each-RX (see §6 and D5 — the
30 dB is met at ONE frequency and the band tilt is published, not hidden).

## 2. Port map — and the ONE change the mating strategy forces

The brief says "5 SMA ports". Three of those five face the PlutoPlus, and
rigid multi-SMA direct-mount is dead (`pluto-plus-mechanical.md`, VERDICT
section, three independent fatal reasons). The chosen path — SMA→SMP adapters
screwed onto the Pluto's own jacks, daughter board carries SMP and pushes on —
means the BOARD carries three SMP jacks, not three SMA jacks. The SMA
interface still exists; it has moved onto the adapters.

| net | board connector | faces | notes |
|---|---|---|---|
| `RX_ANT1` | SMA jack, THT vertical flange | the user's antenna | true SMA, user-facing |
| `RX_ANT2` | SMA jack, THT vertical flange | the user's antenna | true SMA, user-facing |
| `RX_PLUTO1` | **SMP** | Pluto RX1 (U14) via SMA→SMP adapter | push-on |
| `RX_PLUTO2` | **SMP** | Pluto RX2 (U10) via SMA→SMP adapter | push-on |
| `TX_PLUTO` | **SMP** | Pluto TX1 (U12) via SMA→SMP adapter | push-on |

The Pluto's edge order is `T2 R2 R1 T1` at measured pitches
**12.00 / 11.60 / 12.00 mm** (`pluto-plus-mechanical.md`, two independent
extractions agreeing to 0.003 mm). We tap **R2, R1, T1** — a contiguous run of
three at 11.60 + 11.98 mm. The board's three SMP centres are placed at those
pitches, NOT at a uniform pitch.

`RX_PLUTO2 → RX_PLUTO1 → TX_PLUTO` puts TX at one END of the three, not in the
middle. The splitter's mirror axis therefore sits between the two RX ports and
the TX feed enters that axis from the side (§7).

**See ADR-0006 (mating strategy) and D6 in BRIEF.md** — the board is built to
the **34.88 mm midpoint** between the genuine (35.04 mm) and clone (34.72 mm)
spans, an assumption the user has not confirmed.

## 3. RF signal chain — every element

```
                                  ┌──────── RX_ANT1 (SMA J1)
                                  │
  RX_PLUTO1 (SMP J3) ── SW1 ──────┤ RF1 = antenna
        (RFin)                    │ RF2 = loopback
                                  └──── PAD_A2a (12 dB) ────┐
                                                            │
                                                     ┌──────┴──────┐
  TX_PLUTO (SMP J5) ── PAD_A1 (10 dB) ── R_D1/D2/D3 ─┤  resistive  │
                                          delta split └──────┬──────┘
                                                            │
                                  ┌──── PAD_A2b (12 dB) ─────┘
  RX_PLUTO2 (SMP J4) ── SW2 ──────┤ RF2 = loopback
        (RFin)                    │ RF1 = antenna
                                  └──────── RX_ANT2 (SMA J2)
```

### 3.1 The two SPDT switches — the polarity falls out with ZERO logic

**`BGS12WN6`** (Infineon, PG-TSNP-6-10, LCSC C534203), one per RX channel, both
on ONE control net. `BGS12P2L6` (C3312945) is the pin-, truth-table- and
LAND-PATTERN-identical alternate — **one footprint qualifies both** (ADR-0002).

Truth table (WN6 Table 12, PDF p11 / printed p9; P2L6 Table 11, PDF p9 —
identical): `CTRL=0 → RFIN–RF1`, `CTRL=1 → RFIN–RF2`.

Wire it as `RFin = RX_PLUTOn`, `RF1 = RX_ANTn`, `RF2 = loopback arm`, and the
brief's fact-locked polarity — **OFF = antenna, ON = loopback** — is native to
the part. No inverter, no complementary control line, no decode.

Why WN6 is primary and not the part the sourcing spike picked:

- **It is the only one of the two with ANY published guarantee at BOTH ends of
  the stated band.** P2L6's RF-characteristics table runs 617–5925 MHz, so
  70–617 MHz *and* 5925–6000 MHz — both endpoints — are uncharacterized; the
  "0.05–6 GHz" figure appears only in its Absolute-Maximum table, whose own
  warning box disclaims functionality. WN6 publishes a **50–698 MHz** row
  (IL 0.15 typ / 0.25 max, RL 28 min, isolation 43 min) and a **5925–7125 MHz**
  row. Neither part puts frequency in "Operation ranges", so the band-by-band
  tables ARE the guarantee.
- **VDD headroom.** WN6 operating max is 3.6 V (abs max 4.2 V); P2L6's is
  **3.4 V** (abs max 3.6 V). A 3.3 V rail from a ±2 % LDO tops out at 3.366 V —
  leaving P2L6 just **34 mV**. WN6 leaves 234 mV.

What it costs, recorded rather than glossed: WN6 is **3 dB worse on guaranteed
minimum isolation at 5150–5925 MHz** (21 vs 24 dB) and 5 dB worse
throw-to-throw; its guaranteed return loss falls to **9.5 dB above 5925 MHz**;
and it handles 26 dBm CW against P2L6's 37 dBm. Its IL/RL are also
**prober-station measurements with board effects removed** (Table 4 fn 1) and
so are NOT a board-level budget — DETAIL_DESIGN §3.2 handles that explicitly.

Two properties both parts share, both load-bearing:

- **The loopback path needs NO DC blocking capacitors.** The switched paths are
  DC-connected through the die (Table 1/2 footnote 1 in both) and blocks are
  unnecessary provided no DC appears on the RF lines. The YAT pads DC-reference
  the whole internal RF node to ground through ≈70 Ω per port, so that proviso
  is satisfied BY CONSTRUCTION (DETAIL_DESIGN §8). This removes the
  70 MHz-to-6 GHz broadband DC-block problem from the calibration path — no
  single capacitor value spans 85.7:1. Blocks ARE fitted on the two
  user-facing ANTENNA ports, where an unknown DC source can appear. ADR-0005.
- **Single-pin CMOS control**, 2 nA, VDD-referenced.

### 3.2 The splitter — resistive delta, not Wilkinson

Three 49.9 Ω 0402 (`C25120`, JLC **Basic**, 1.78 M in stock) in a DELTA, one
between each pair of the three ports. Frequency-independent by construction.

D1 in the brief argued a 70 MHz Wilkinson is ~400 mm of λ/4; the real figure
is **601 mm** (εeff 3.17 on 1.6 mm FR4), and there is a SECOND, independent
refutation D1 did not make: the required bandwidth ratio is **85.7:1**, and a
single-section Wilkinson manages ~1.4:1 while published multi-section designs
top out near 10–20:1. Refuted on size AND on bandwidth. ADR-0003.

Delta beats star (wye) by **9.3 dB of return loss at 6 GHz** with identical
parts, because the through path crosses ONE chip body instead of two, and
49.9 Ω 0402 is a JLC Basic part where 16.9 Ω is not. ADR-0003.

The split's 6.02 dB loss and its 6.02 dB port-to-port isolation are the SAME
number and that is a theorem, not a part limitation — see DETAIL_DESIGN §4.3.

### 3.3 The attenuation — SPLIT 10 dB pre / 12 dB per arm, not one 22 dB pad

`YAT-10A+` before the split; `YAT-10A+ + YAT-2A+` in each arm. All Mini-Circuits
MCLP 2×2 mm (case MC1630), DC–18 GHz, absorptive, thin-film.

Putting the whole pad ahead of the split is the obvious answer and it is
wrong on four independent counts (DETAIL_DESIGN §5, ADR-0004):

1. inter-channel isolation stays at 6.02 dB instead of 6.02 + 2·A2 = 30.0 dB;
2. **unplugging one RX cable adds +3.52 dB to the OTHER channel** with no
   error indication — the surviving arm's Zin goes 50 → 83.3 Ω. Arm pads mask
   the open by 24 dB and the error falls to ~0.2 dB;
3. in **antenna** mode both arms face the SPDTs' reflective shorts; with no
   arm pad the splitter's input impedance is *infinite* and TX sees Γ = +1.
   With 12 dB arms it sees |Γ| = 0.063;
4. the AD936x RX input match **moves with the AGC gain index**, so the
   contamination the 6 dB isolation lets through is non-stationary and cannot
   be calibrated out.

The cost is arm-to-arm amplitude imbalance from two independent pad chains
(±1.6 dB worst case on the datasheet windows, far less typical). That is a
STATIC, MEASURABLE quantity, which is exactly what brief D4 already obliges
the release to publish. A known imbalance is benign; unknown cross-coupling
is not.

### 3.4 Connectors

- **SMA (2×, antenna)** — `KH-SMA-KE-Z` / C504007, vertical THT flange jack,
  VSWR ≤1.35 DC–6 GHz on its own datasheet p.1, 5-Ø1.4 mm holes on a
  5.08 × 5.08 mm square. 19 252 in stock. Depth reserve `BWSMA-KE-Z001` /
  C496549 (113 553 in stock) on the identical pattern. ADR-0007.
- **SMP (3×, Pluto-facing)** — `SMP-MSLD-PCE-5T` / C6297051 (Amphenol RF),
  **edge-launch**, limited detent, DC–26.5 GHz, **VSWR 1.11 max over
  DC–6 GHz**, 500 mating cycles, 540 in stock. Land: a routed edge notch
  7.65 mm wide × 6.4 mm deep, 4.12 mm mouth, 0.83 mm centre trace, 1.84 mm
  side pads, coplanar within 0.13 mm. **RF axis 2.00 mm above the board's top
  surface.** ADR-0006.
- **DC blocks (2×, antenna ports only)** — 1 nF 0402 C0G in series with each
  `RX_ANT`. RL 32.9 dB @70 MHz / 16.5 dB @6 GHz, IL 0.002 / 0.05 dB. The
  calibration path carries none. ADR-0005, DETAIL_DESIGN §8.

---

## 4. Control architecture

```
  micro-USB ──► RP2040 ──► GPIO ──┬── 1k ──┬── SW1.CTRL   (+1 nF to GND at the pin)
   (CDC-ACM)      ▲               │        └── 10k to GND
                  │               └── 1k ──┬── SW2.CTRL   (+1 nF to GND at the pin)
                  │                        └── 10k to GND
   GPIO header ── ADC (GPIO28)
   (÷2.5 divider)
```

**One net, `RF_CTRL`, drives both switches.** Both channels must switch
together — they are one instrument.

### 4.1 Power-on state is guaranteed in SILICON, not in firmware

RP2040 PADS_BANK0 resets with `PDE=1 / PUE=0` (Table 341, §2.19.6.3, p.301);
`GPIO_OE` resets to `0x00000000` so nothing is driven (Table 24, p.46); and
Table 615 (§5.5.2.2, pp.612-613) states the per-pin reset state as the single
word `Pull-Down`, RPD = 50–80 kΩ (Table 625, p.615). A board straight from
JLCPCB with blank flash falls into the USB mass-storage bootloader
(§2.8.1, p.129), whose bootrom touches only the QSPI pads — so the pull-down
survives indefinitely.

**Power-on = CTRL LOW = ANTENNA mode.** ADR-0001.

The external 10 kΩ pull-downs at each switch cover the one case the internal
pull-down cannot: IOVDD = 0 V, USB unplugged, pin genuinely floating.

This is why MCP2221A was DISQUALIFIED rather than merely rejected: its factory
flash defaults leave every GP pin a driven push-pull output idling HIGH, so a
board as delivered would drive the RF path into LOOPBACK. ADR-0001.

### 4.2 The GPIO header is an ANALOG input, and that is deliberate

**PlutoPlus IO is 1.8 V. RP2040 VIH is a flat 2.0 V minimum** (Table 625,
§5.5.3.4, p.615) — not 0.65·IOVDD. A Zynq HR bank at VCCO = 1.8 V has a
worst-case VOH of VCCO − 0.45 = **1.35 V**. A 1.8 V header driving an RP2040
digital input reads permanently LOW: the board would silently stay in antenna
mode forever, and the failure is *fail-safe*, so no bench test that asks "can
it spuriously enter loopback" would ever find it.

The header therefore lands on an **ADC-capable pin (GPIO28)** through a
2.2 kΩ / 3.3 kΩ divider (÷2.5), thresholded in firmware at 0.36 V. That:

- reads **1.8 V, 3.3 V and 5.0 V** logic (0.72 / 1.32 / 2.00 V at the pin, all
  inside the 0–3.3 V ADC range) with no level translator and no second rail;
- is **input-only by construction** — an ADC-configured pin has its digital
  output disabled, so no firmware bug can drive 3.3 V into a 1.8 V Zynq pin
  whose absolute max is ≈2.35 V. The 2.2 kΩ series bounds any such fault to
  <1.5 mA regardless;
- reads 0 V when the header is unconnected (the 3.3 kΩ is a pull-down).

ADR-0008.

### 4.3 Which surface wins

`RF_CTRL = HEADER_level OR USB_bit`, plus a **USB watchdog**: if the USB bit
is set and the host stops talking for >10 s, firmware clears it.

The verbatim brief states the header's semantics as a LEVEL ("GPIO = off /
GPIO = on"), so a header held high must produce loopback whatever USB says, or
P2 is violated; and a header held low must not block USB control, or A4 is
violated. OR is the only resolution that satisfies both. The watchdog answers
the real objection to an OR — that the header could never recover the board to
the safe state — by bounding the time USB can hold loopback against it.

**The user has not been asked which surface wins.** Recorded as D7. ADR-0008.

## 5. Power tree

Machine-readable envelopes: `03_src/rules/power_tree.yaml`.

```
  micro-USB VBUS ──[F1 PPTC 500 mA]──[FB1 600Ω@100MHz]──┬── C_BULK 4.7 µF + 100 nF
   4.40 – 5.25 V                                        │
   (USB 2.0 Table 7-7)                                  └── U_LDO ME6211C33M5G-N
                                                             (SOT-23-5, CE→VIN)
                                                              │
                                          3V3 ────────────────┴── 3.30 V ±2%
                                            ├── RP2040 core + IO (VREG_VIN, IOVDD×6,
                                            │     USB_VDD, ADC_AVDD, DVDD×2)   ~50 mA
                                            ├── W25Q16JVSSIQ QSPI flash         ~5 mA
                                            ├──[FB2]── SW1.VDD  (+100 nF +1 nF)  115 µA
                                            ├──[FB2]── SW2.VDD  (+100 nF +1 nF)  115 µA
                                            └── 2× status LED                     4 mA
```

| rail | Vin min–max | Vout | Iout envelope | converter |
|---|---|---|---|---|
| `3V3` | 4.40 – 5.25 V | 3.30 V fixed | 0.10 A (typ 0.06 A) | ME6211C33M5G-N, **linear** |

**Topology is DERIVED, not chosen**: Vout_max (3.30) < Vin_min (4.40) always,
so a STEP-DOWN is required and a boost stage would be over-engineering.
A linear regulator is the correct step-down at 60 mA and 1.7 V of drop
(117 mW, 39 % of the SOT-23 300 mW rating). See DETAIL_DESIGN §7 and the
E-TOPO gate note in §12 below.

**E-OFF is N-A.** The board's only energy source is the USB host; unplugging
the cable de-energizes it completely. There is no cell, no pack, no stored
charge beyond ~5.8 µF of ceramic. `source_type: usb` in `power_tree.yaml`.

**Input protection posture** (ADR-0009), stated including what is deliberately
absent:

| fitted | why |
|---|---|
| USBLC6-2SC6 at the connector | D+/D−/VBUS ESD on a bench instrument a human handles daily |
| VBUS bulk **capped at 10 µF total** | USB 2.0 §7.2.4.1 inrush limit is a HARD ceiling: >10 µF requires surge limiting. 4.7 µF + 100 nF + 2× 1 µF = 6.8 µF |
| PPTC ~500 mA hold, series VBUS | protects the HOST, not this board — a shorted rail here must not kill the laptop port |
| ferrite 600 Ω @100 MHz, VBUS→LDO | the USB cable is a ~1 m antenna galvanically bonded to the RF ground system |
| series R + ESD clamp on the header | the header is the SECOND, UNKEYED entry and the realistic miswire path |
| **NOT** a reverse-polarity FET | micro-B is keyed and is the sole power entry; there is no second source to reverse |
| **NOT** a power TVS / crowbar | ME6211 VIN abs-max is 6.5 V against a 4.40–5.25 V host; the USBLC6 clamps hot-plug. It will NOT survive 12 V into the micro-B — that exposure is taken KNOWINGLY |
| **NOT** UVLO | no battery to over-discharge |

## 6. The 30 dB — and why it is a curve, not a scalar

The chain carries **3.09 dB of irreducible tilt** across 70 MHz – 6 GHz
(DETAIL_DESIGN §3). No pad value makes the total 30 dB at both ends.

The pad is chosen by **MINIMAX** — the value that minimizes the worst-case
deviation from 30 dB, privileging no frequency:

| | 70 MHz | ~3.0 GHz | 6 GHz |
|---|---|---|---|
| non-pad chain loss | 6.54 dB | 8.11 dB | 9.63 dB |
| + 21.86 dB pad | **28.4 dB** | **30.0 dB** | **31.4 dB** |

**30 dB is met at ≈3.0 GHz; the span is 30.0 −1.6 / +1.4 dB.** Recorded as D5 —
the user has not named a reference frequency, and the choice is a one-BOM-line
change (DETAIL_DESIGN §3.4).

The release must publish loss-vs-frequency, exactly as brief D4 makes the
length delta a published artifact rather than a target.

## 7. Stackup

**JLCPCB `JLC04161H-7628`, 4-layer, 1.6 mm — the CHEAPEST tier that works.**

| layer | thickness | function |
|---|---|---|
| L1 | 35 µm Cu | **RF microstrip (0.35 mm = 50 Ω)**, USB pair, control fan-out |
| — | 0.2104 mm prepreg 7628, Dk 4.4 | |
| L2 | 35 µm Cu | **SOLID GND — no splits anywhere under an RF trace or the USB pair.** The single most important rule on this board |
| — | 1.065 mm core | |
| L3 | 35 µm Cu | 3V3 / 5V pours + digital routing |
| — | 0.2104 mm prepreg | |
| L4 | 35 µm Cu | GND |

**Two-layer is REFUTED, and the reason is not the RF loss — it is that the
line does not fit the parts.** A 50 Ω microstrip on 1.6 mm FR4 is 2.9–3.1 mm
wide. The splitter's whole 3×0402 delta is ~2 mm across; the MC1630
attenuator lands are 0.30 mm; the BGS12P2L6 lands are 0.25 mm. Three 3 mm
lines cannot land on a 2 mm triangle, and at the SMA the trace would overlap
the ground pads (half-width 1.556 mm against a pad edge at 1.415–1.540 mm — a
NEGATIVE clearance). On the 0.2104 mm prepreg the 50 Ω line is 0.35 mm and
matches every pad on the board.

**Controlled impedance is REQUESTED**, and the widths above are
Hammerstad-Jensen closed-form — they must be re-confirmed against JLCPCB's own
impedance calculator for the exact stackup ordered, before release. ADR-0010.

Derived constants pinned to this stackup, used throughout DETAIL_DESIGN:
`εeff ≈ 3.26`, `tpd = 6.0 ps/mm`, `λg(6 GHz) = 27.7 mm`,
microstrip loss `0.036 dB/mm @6 GHz`, `0.0018 dB/mm @70 MHz`.

**The tpd number is what makes brief D4 executable**: the published per-arm
length delta converts to picoseconds with a constant pinned to the ordered
stackup, not a guessed one. A software offset is only as good as the number
it is given.

## 8. Ground strategy

- **L2 is one unbroken plane.** No split, no routing channel, no keepout under
  any RF trace, under the splitter, under either attenuator, or under the USB
  differential pair. The USB requirement (`hardware-design-with-rp2040` §2.4.1
  p.11, "A solid, uninterrupted area of ground copper, stretching the entire
  length of the track") and the RF requirement are the same requirement.
- **Via fence at ≤2.0 mm pitch** (λg/12 at 6 GHz) beside every RF trace and
  around every launch. The SMA's four ground posts sit at 5.08 mm = λg/4.7 —
  they are NOT a shield at 6 GHz, and omitting the fence produces both poor
  return loss and poor TX→RX isolation, which will be blamed on the connector.
  Emitted as a generated rule, never a layout habit.
- **SMA bottom-plane antipad ≥ Ø3.5 mm**, opening OUTWARD toward the 5.08 mm
  post square — NOT the minimum-DRC Ø2.6 mm. The through-hole launch's
  dominant term is the barrel + bottom pad inside the antipad, not the top pad
  over solid copper; opening Ø2.6 → Ø3.5 buys ~9 dB of return loss at 6 GHz
  for free. This rule was originally derived BACKWARDS and would have been
  frozen into the footprint. ADR-0007.
- **Micro-USB shell and legs tie DIRECTLY to GND** — no R/C isolation network.
  The SMA grounds, the board ground and the cable shield must be one system.
- **RP2040 centre pad** into L2 with a via array.

## 9. Net domains

Classes and widths: `03_src/rules/nets.yaml`. Every class declares a typed
`current:`; classes with no ampacity obligation say `signal` explicitly.

| class | nets | what makes it special |
|---|---|---|
| `RF50` | `RX_ANT1/2`, `RX_PLUTO1/2`, `TX_PLUTO`, `LOOP_IN`, `LOOP_SPLIT`, `LOOP_ARM1/2`, `SW1_ANT`, `SW2_ANT` | 0.35 mm = 50 Ω on L1 over solid L2. NOT an ampacity width — a width relaxation or a widening both break the impedance. Fenced at ≤2.0 mm |
| `RF_LOOP_MATCH` | `LOOP_ARM1`, `LOOP_ARM2` | the D4 pair: mirror-symmetric by construction, delta MEASURED and PUBLISHED |
| `USB_DP` | `USB_DP`, `USB_DM` | 0.33 mm / 0.25 mm gap ≈ 90 Ω differential, same layer + same reference as RF |
| `CTRL` | `RF_CTRL`, `RF_CTRL_SW1`, `RF_CTRL_SW2`, `HDR_CTRL_IN`, `HDR_STATE_OUT` | slow-edge, 2 mA drive, series R + 1 nF at each switch pin. Must NOT run parallel to either loopback arm |
| `PWR` | `VBUS`, `VBUS_F`, `3V3`, `3V3_SW` | 0.10 A envelope |
| `QSPI` | `QSPI_SCLK`, `QSPI_SS`, `QSPI_D0..D3` | short, direct, flash hugging the RP2040 |
| default | everything else | |
| `GND` | — | pours + stitching, no netclass width |

## 10. Critical geometries — the things a router will destroy

1. **`LOOP_ARM1` and `LOOP_ARM2` are mirror-symmetric about the splitter
   axis**, identical bend-for-bend, same layer, no vias, arm pads at the same
   rotation (NOT mirrored — mirrored placement turns solder-fillet asymmetry
   into phase error; 0.1 nH of Lp mismatch ≈ 2° at 6 GHz).
2. **Inter-arm separation ≥ 3× dielectric height plus a via fence.** Two
   parallel 50 Ω microstrips on a 0.21 mm prepreg couple at roughly
   −25 to −35 dB over a few mm at 6 GHz — at or ABOVE the 30 dB isolation the
   arm pads buy. The pads' work can be undone by the routing.
3. **The splitter triangle stays inside λg/20 = 1.4 mm** of active path. Only
   the R12/R13 legs are active; R23 carries zero current under symmetric
   excitation and does not lengthen the wanted path.
4. **Reference plane CONTINUOUS under the splitter** — do NOT void it. (The
   opposite advice applies to a STAR topology; one more reason not to use one.)
5. **RP2040 + micro-USB at the far end from every SMA/SMP**, so the USB pair's
   uninterrupted-reference requirement never competes with the RF pour, and so
   the QSPI bus (tens of MHz, sub-ns edges, harmonics past 6 GHz) is as far
   from the calibration path as the board allows.
6. **`RF_CTRL` on an inner layer under ground** between the two switches, never
   parallel to a loopback arm. A control trace entering the RF section is a
   resonator: 25 mm of this microstrip is λ/4 at ≈1.5 GHz, mid-band. Series R
   **plus** a 1 nF shunt at each VCTRL pin is what makes it a control line
   instead of an antenna.
7. **BGS12P2L6 pin-2 ground via escapes OUTWARD** from the land, not into it.
   A 0.45 mm standard-tier via centred on the 0.25 mm land leaves 0.050 mm to
   pins 1 and 3, under the 0.127 mm floor. See DETAIL_DESIGN §8.
8. **YAT exposed pad is the RF GROUND RETURN, not a thermal pad**
   ("Case is defined as ground lead", YAT-20A+ p.2 abs-max note 3). Tenting it
   breaks the RF return path.

## 11. Mechanical

- **Board-to-Pluto interface**: `134-1019-451` (Cinch/Johnson) SMA-plug→SMP
  adapters on the Pluto's three jacks; three edge-launch SMP jacks on this
  board; push-on mate with ±0.25–0.3 mm radial and ~4° angular float against a
  ±0.49 mm RSS two-board tolerance stack. Each adapter threads on
  INDEPENDENTLY with nothing else attached, which is what dissolves the
  coupled-datum and wrench-access problems that killed rigid SMA. ADR-0006.
- **The Z stack**, each term with its status:

  | term | value | status |
  |---|---|---|
  | adapter overall length | 14.25 ± 0.51 mm | cited (Cinch dwg 134-1019-451/460 Rev 3) |
  | less coupling-nut thread engagement | ≈4.0 mm | **UNVERIFIED estimate — the dominant error** |
  | ⇒ Pluto SMA face → our board edge | **≈10.2 mm, +0.3/−0.5** | derived |
  | SMP mated axial misalignment allowance | 0 … +0.254 mm | cited (MIL-STD-348) |
  | **RF axis above our board's TOP surface** | **2.00 mm REF** | **cited** (dwg SMP-MSLD-PCE-5X sheet 2) |

- **The RF axis height above the PLUTO's PCB is still NOT ESTABLISHED** and
  cannot be guessed. Those are right-angle THT jacks, so the axis sits above
  the Pluto's board plane; the geometric lower bound is ≥3.2 mm and the family
  typical is 4.5–6 mm. Our board's top copper must sit **2.00 mm below the
  plane containing the Pluto's three SMA axes** — that half is now a number;
  the Pluto half is not. **This is the one open mechanical item.** It gates the
  board's Z position relative to the Pluto; it does NOT gate any of the RF
  design above. See §12.
- **Engagement force is a usability cost**: up to 3 × 45 N = **135 N** to push
  the board on, 3 × 9 N = 27 N minimum to pull it off. Edge-launch takes that
  force in the board plane as shear rather than as peel on SMT pads, which is
  the main reason it was chosen over the vertical part.
- **Enclosure**: PlutoPlus ships in a two-part aluminium shell whose end panel
  is captured ON the SMA barrels, so fitting the adapters is a
  case-disassembly-adjacent operation. Assumed bare board with mounting holes
  for this design until told otherwise.

## 12. Open items — named, not buried

| # | item | blocks | owner |
|---|---|---|---|
| O1 | **RF axis height above the Pluto PCB** — must be measured on a physical unit. Our half is now cited (2.00 mm above our board's top surface) | the board's Z position relative to the Pluto. Blocks NO RF work | user / bench |
| O1b | **PlutoPlus SMA GENDER is INFERRED, not cited** — the schematic says only `SMA-L`. A jack is the universal SDR convention and no contrary evidence was found | the adapter order. A 5-minute caliper check, and $101 of adapters rides on it | user / bench |
| O1c | **SMA coupling-nut thread-engagement depth (≈4.0 mm)** has no primary source | the ≈10.2 mm board-to-Pluto separation, ±0.5 mm | bench |
| O1d | **Will JLC place an edge-launch SMP?** In-library and purchasable ≠ placeable — it straddles a routed outline notch and demands 0.13 mm coplanarity | assembly. Fallback `SMP-MSLD-PCS20T` (vertical) is pre-designed | JLC DFM review |
| O2 | **Which PlutoPlus** — genuine (35.04 mm span) or clone (34.72 mm)? Built to the 34.88 mm midpoint | ±0.16 mm of the ±0.3 mm SMP float | user (D6) |
| O3 | **Reference frequency for "30 dB"** — met at ≈3.0 GHz by minimax | a one-BOM-line pad change | user (D5) |
| O4 | **Which control surface wins** — OR + 10 s USB watchdog assumed | firmware only | user (D7) |
| O5 | **AD936x RX absolute-max input** (+2.5 dBm) is a SECONDARY source. Every primary route was blocked | nothing — 22 dB of margin absorbs a large error | bench / ADI |
| O6 | **PlutoPlus SMA ports DC-free?** All RF ports on both switches are ONE galvanic node through the dice and the resistive splitter. A single DC fault anywhere violates V_RFDC = 0 V on both at once | whether DC blocks become mandatory | bench |
| O7 | **70–617 MHz is unguaranteed** on BGS12P2L6. First-article measurement at 70/100/200/400 MHz is MANDATORY, not optional | acceptance, not design (BGS12WN6 is the drop-in answer) | bench |
| O8 | **E-TOPO cannot express a linear regulator.** `power_topology.py:normalize_type` accepts only buck/boost/buck_boost; `type: ldo_*` raises LoadError and exits 2. This board's only converter is an LDO. Reported as a gate gap, not worked around | the E-TOPO gate on this board | skills/ owner |

## 13. What this board deliberately does NOT do

- **It does not gate TX in antenna mode.** With TX driven at +7 dBm while
  receiving on antennas, the loopback arm sits at ≈−22 dBm on the deselected
  throw and the switch's 24 dB (6 GHz) / 42 dB (900 MHz) isolation puts
  ≈−46 dBm / −64 dBm into RX_PLUTO — well above a Pluto RX noise floor. The
  brief's two states do not include "transmit while receiving on antennas", so
  the simplest reading that satisfies it is taken. A third BGS12P2L6 with one
  throw on a 50 Ω 0402 would add 24–45 dB for ~$0.25 if the user later needs
  it. ADR-0004 records the rejection.
- **It does not terminate the deselected antenna port.** The switch is
  reflective by design. Termination changes the phase of the residual antenna
  leakage, not its magnitude — that is set by the isolation. The consequence
  worth knowing: the residual RIPPLES with frequency (a cable-length comb)
  rather than sitting flat. ADR-0002.
- **It does not solve the second-USB ground loop.** Plugging this board's
  micro-USB into the same host that runs the Pluto closes a loop through the
  coax shields whose coupling is cable-position-dependent — i.e. it differs
  between the calibration run and the measurement run. Mitigations available:
  power from a separate supply, or a common-mode choke on the USB pair.
  Recorded in ADR-0009; the user must be told.

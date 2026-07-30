---
id: 0001
date: 2026-07-30
status: accepted
tags: [rf, part-selection, spec-tension]
---
# 0001 — RP2040-Zero: the spur objection kills the *Pico*, not the module idea

## Context

The commission asks for "the pico class module". The board is a receiver
front-end: an SP8T antenna switch feeding PlutoSDR RX2 from 70 MHz to 6 GHz. v1's
own ARCHITECTURE (section 4, `QSPI` row) names the flash bus as *"the board's
only continuous in-band spur source"* — a fact I read in v1's file, not
inherited.

The stated risk that could kill the commission: **a Raspberry Pi Pico carries an
RT6150 buck-boost SMPS, and GPIO23 drives its PS pin with PFM as the default** —
a variable, load-dependent switching frequency. A moving spur is the worst shape
next to a receiver because it cannot be planned around. Trading a routing problem
for a second, VARIABLE emitter would be a bad bargain, and the brief required
this be settled with evidence rather than assumed in either direction.

**It is settled. The objection is real and fully confirmed — and it applies to
exactly one candidate.**

### Evidence — the RT6150 claim, confirmed in every particular

CITED, Raspberry Pi Pico datasheet §4.4 "Powerchain", p.20
(https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf), verbatim:

> "GPIO23 controls the RT6150 PS (Power Save) pin. When PS is low (**the default
> on Pico**) the regulator is in Pulse Frequency Modulation mode, which, at light
> loads, saves considerable power by only turning on the switching MOSFETs
> occasionally to keep the output capacitor topped up. Setting PS high forces the
> regulator into Pulse Width Modulation (PWM) mode... Note that under heavy load
> the switcher will be in PWM mode irrespective of the PS pin state."

CITED, Richtek RT6150A/B datasheet DS6150A/B-04, Electrical Characteristics p.4:
oscillator frequency **min 0.8 / typ 1.0 / max 1.2 MHz**; Pin Description: *"Pull
low for PSM operation and pull high for fixed switching frequency operation."*
CITED, Pico R3 public schematic: `U2 = RT6150B-33GQW`.

**Two findings that make the mitigation WEAKER than the brief assumed, and they
are the reason "just force PWM" was not adopted:**

1. **Forced PWM is not a known frequency.** f_OSC carries a **±20 % part-to-part
   spread (0.8-1.2 MHz)**. "Force PWM and plan around the spur" buys a spur whose
   position is known only to ±20 % across a production run.
2. **The 3V3-bypass escape hatch is not cleanly supported.** The Pico datasheet
   §4.5 "Powering Pico" covers only VBUS/VSYS and describes 3V3 exclusively as an
   OUTPUT; it never describes feeding 3V3 externally. The Raspberry Pi forum
   thread "Pico 3V3 as power input with RT6150 disabled?"
   (https://forums.raspberrypi.com/viewtopic.php?t=345576) asks exactly the right
   question — is VOUT high-Z to GROUND with EN low? — and gets *"AFAIK there is
   still no official word on this"* with **no Raspberry Pi staff reply**.
   Richtek's *"V_OUT Disconnected from V_IN during Shutdown"* answers the VIN
   half and says nothing about the ground half. **Unsupported hack, rejected.**

### Evidence — and then the finding that dissolves the problem entirely

The RT6150 is a property of the **Raspberry Pi Pico specifically**, not of
"Pico-class modules". The compact castellated modules are **LDO-regulated**:

| module | 3V3 source | topology | inductor in the power path? |
|---|---|---|---|
| **Waveshare RP2040-Zero** | **RT9013-33** (Richtek, SOT-23-5) | **LDO** | **none** |
| Waveshare RP2040-Tiny | RT9013-33 / RT9193-33 | **LDO** | none |
| Seeed XIAO RP2040 | RS3236-3.3YUTDN4 (RUNIC) | **LDO** | none |
| Raspberry Pi Pico | RT6150B-33GQW | **buck-boost SMPS** | yes (L1) |
| WeAct RP2040 core | — | **unknown** | unknown |

CITED, Waveshare RP2040-Zero schematic
(https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf, sheet 1): U1 is a
5-pin `RT9013-33` with nets VIN/VOUT/EN/**BP**/GND, 3x 2.2 uF on VIN, 1 uF on
VOUT, 100 nF on the BP noise-bypass pin. **A full-text search of the schematic
for `uH` / `inductor` / `nH` returns zero hits.** (The `L1` designator on that
sheet is the WS2812B RGB LED, whose pins are VDD/DIN/DOUT/VSS — not an
inductor. Worth recording because it is exactly the kind of thing that reads as
a switching inductor at a glance.)

CITED, Richtek RT9013 product page: *"500mA, Low Dropout, Low Noise Ultra-Fast
Without Bypass Capacitor CMOS LDO Regulator"*, features **"Ultra-Low-Noise for
RF Application"**, 250 mV dropout at 500 mA. There is no switching frequency to
plan around because there is no switching.

### And an honest quantification, because the risk was probably overstated anyway

INFERRED (arithmetic on the cited f_OSC = 1 MHz): reaching 6 GHz from a 1 MHz
converter is harmonic order **n ~ 6000**. A trapezoidal switching edge with
t_rise ~1-5 ns puts the second breakpoint at ~64-320 MHz, so 6 GHz sits 1.3-2
decades into a -40 dB/decade region on top of ~60 dB already accumulated. By
contrast the acknowledged QSPI comb runs at clk_sys/2-clk_sys/4 = **~31-66 MHz**,
which reaches 6 GHz at harmonic **n ~ 90-190** — a vastly lower order in a much
flatter part of the envelope.

**So v1's ARCHITECTURE is right that QSPI dominates, and an RT6150 would have
ranked roughly fourth behind QSPI, the clk_sys/XOSC combs, and USB.** The PFM
concern's real mechanism is rail-ripple modulating something that cares — the
Pico datasheet frames it as an **ADC-reference** problem (§4.3), not an RF-spur
problem — and this board has no on-board synthesiser sharing the rail; the
PE42482A-X's control lines sit DC-static through each dwell.

**That does not make the choice arbitrary — it makes it free.** An LDO module
deletes the question at zero cost, zero firmware dependency, and zero
±20 %-f_OSC uncertainty. When the mitigation costs nothing, you do not spend
paragraphs arguing the risk is small.

## Options

- **Raspberry Pi Pico (51 x 21 mm, RT6150 SMPS).** REJECTED on three counts,
  any one of which is sufficient: the SMPS is the exact hazard the commission
  raised; its mitigation (force PWM via GPIO23) burns a GPIO, adds a firmware
  dependency, and still leaves a ±20 % spur position; and at 1071 mm2 it is 2.6x
  the footprint of the alternatives on a board whose centre is occupied by a
  radial star. The bypass route is vendor-unsupported.
- **Waveshare RP2040-Tiny (18 x 23.5 mm, RT9013-33 LDO).** REJECTED, and it was
  close. Same outline, same 23-pad 2.54 mm pattern, same LDO as the Zero, and it
  has a genuine attraction: **its USB-C is on a SEPARATE adapter board joined by
  an 8-pin 0.5 mm FPC**, so the module carries no USB connector at all. That
  would have answered the two-USB question by construction. Rejected because it
  moves the flashing interface onto a fragile 0.5 mm FPC and a loose second PCB
  that must be stored with the board for its whole life — a mechanical liability
  traded for a cosmetic gain, on an instrument that will be re-flashed often.
- **Seeed XIAO RP2040 (21 x 17.8 mm, RS3236-3.3 LDO).** REJECTED, and it is the
  designated SECOND SOURCE — it satisfies the RF constraint identically. Two
  reasons it loses. (a) **GPIO ordering**: the board's control plane is a
  free-running PIO driving 4 parallel select lines, which wants CONTIGUOUS GPIOs
  laid out in physical order. RP2040-Zero exposes GP0..GP8 in order down one
  edge; XIAO exposes GP0-GP4 as pads D6, D7, D8, D10, D9 — contiguous in GPIO
  number, scrambled in space, so the fanout to the switch crosses itself.
  (b) **11 GPIO and 6 UNDERSIDE pads** in addition to the 14 castellations,
  which complicates a castellated-only mount. Recorded as the second source
  because it survives the RF test and would be the answer if RP2040-Zero were
  unobtainable.
- **WeAct RP2040 core board.** REJECTED on EVIDENCE, not suspicion: the official
  repo publishes only PNGs, a pinout image and a STEP file — **no schematic, no
  netlist, no BOM** (verified by a recursive GitHub tree listing). Its regulator
  topology cannot be established, and on this board the regulator topology is the
  whole question.
- **Stay chip-down (v1's answer).** Not rejected — it is the OTHER ARM of the
  comparison and it keeps running as `projects/pluto-rx2-8way`. This ADR does not
  claim the module is better; it claims the module is VIABLE, which is what the
  commission asked to find out.

## Decision

**Waveshare RP2040-Zero.** 18.00 x 23.50 mm, 23 castellated pads at 2.54 mm,
`RT9013-33` LDO, no inductor in the power path. Seeed XIAO RP2040 is the
recorded second source.

**The spur objection is resolved by SELECTION, not by mitigation.** There is no
GPIO23 to hold high, no PWM-forcing firmware, no ±20 % oscillator to plan
around, and no unsupported 3V3-backfeed. This is the same reasoning v1 used when
it refused a switcher for its own 3V3 rail on RF grounds (v1 ADR-0004) — v2
keeps that principle and buys it in a module.

**A collateral RF gain worth stating, because it was not why we chose but it is
real:** the QSPI comb — the source v1 names as its only continuous in-band one —
moves OFF this laminate. On v1 the flash bus runs on the same copper as the nine
RF arms; on v2 it runs on the module's own PCB with the module's own reference
plane, ~20 mm from the star, coupled only through the shared 3V3/GND pads and
free space.

## Consequences

- **A NEW continuous source arrives with the module, and it must not be buried:
  the onboard WS2812B RGB LED.** It sits on the module's 3V3 rail and its
  internal PWM oscillator free-runs whenever powered. v1 has no equivalent. This
  is a genuine debit against G9 and I am recording it as one rather than
  arguing it away: it is a low-speed LED driver (oscillator in the high-kHz to
  ~1 MHz class, slow edges), so at 70 MHz it is already at high harmonic order
  in a rolled-off envelope, and it is on the module's PCB rather than ours. It
  is weaker in DEGREE than QSPI by a wide margin but it is real in KIND.
  **OWED**: whether RP2040-Zero's WS2812 power can be gated (the XIAO has a
  NeoPixel POWER-ENABLE GPIO; whether the Zero has any equivalent is a schematic
  question, delegated to the part dossier). If it cannot be gated, that is a
  fact for the record and for the first spur measurement, not a reason to
  re-open the module choice — the LDO gain is larger than the WS2812 debit.
- **Commits the firmware to GP0..GP3 for `SEL_V1..SEL_V4`** and one further GPIO
  for `LED_STAT`, chosen from the physically-ordered right edge so the PIO's
  `out pins, 4` maps to a fanout that does not cross.
- **Commits the 3V3 rail's source to the module's RT9013.** Our load is a
  PE42482A-X at 120 uA typ / 200 uA max (v1's dossier, Table 2 PDF p3) against a
  500 mA regulator, so headroom is not the question; rail CLEANLINESS is, and
  the answer is a ferrite plus local decoupling at the switch VDD (see ADR-0002).
- **Deletes from the BOM, versus v1**: the RP2040 itself, W25Q128 flash + its
  decoupler, the 12 MHz crystal + 2 load caps + series R, the 1V1 core-rail link,
  and ten MCU decouplers. That is the routing problem the commission set out to
  remove, removed at part selection rather than at the router.
- **What breaks if reversed:** reverting to the Pico re-opens the SMPS question
  and needs a GPIO23 hold plus a spur survey; reverting to the bare chip is
  simply v1 and already exists.
- **Not yet verified, and honestly flagged:** the module's own regulator, flash
  and LED are all facts about a board WE DID NOT DESIGN and cannot inspect at
  stage 3. They rest on the vendor schematic. The first physical unit should be
  spur-surveyed before the phase table is published.

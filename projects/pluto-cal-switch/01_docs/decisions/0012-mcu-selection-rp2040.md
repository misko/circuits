---
id: 0012
date: 2026-07-27
status: accepted
tags: [topology]
---
# 0012 — RP2040 for the control bit; CH32X035 datasheet-verified and BLOCKED

## Context

BRIEF A4 asks for USB control, P2 asks for a GPIO header, and D3 resolves both
with an MCU. ADR-0001 makes the MCU's **GPIO reset state** the binding spec.

The MCU is also the board's largest complexity and cost lever. An RP2040 route
carries an external QSPI flash, a 12 MHz crystal and ~26 placements, and its
QFN-56 at 0.40 mm pitch computes as `jlc_4layer_advanced` under this repo's own
escape model. That is worth attacking before it is committed — and on an RF
calibration board there is a second reason: **the RP2040 executes in place from
external flash, so it runs a continuous tens-of-MHz bus with sub-nanosecond
edges whose harmonics land inside 70 MHz – 6 GHz**, which is the one band this
board exists to measure cleanly.

So `CH32X035F8U6` (internal flash, claimed crystal-less USB, ~$0.27) was
datasheet-verified rather than waved through as "the cheap alternative".

## Options

- **RP2040** (C2040, 57 220 in stock, $0.76 @100). CHOSEN.
- **`CH32X035F8U6`** (C42442062, 1041 in JLC / 726 at LCSC). **BLOCKED** on
  three primary-document findings, none of which is the reset state:
  1. **The package premise is factually wrong.** It is **QFN-20-EP, 3 × 3 mm,
     0.40 mm pitch, with a mandatory 1.9 mm exposed pad and NO perimeter GND
     pin** — not TSSOP-20 at 0.65 mm. WCH's own naming rule (`U` = QFN,
     DS V2.2 printed p.44), the package table (p.38), the pinout figure (p.13),
     LCSC and the JLC API all agree. **The entire fab-tier savings argument
     rested on a pitch this part does not have.**
  2. **USB clock accuracy is not established in spec.** There is no crystal
     option at all — `HSE` appears ZERO times in the datasheet and the 262-page
     reference manual, and there are no oscillator pins. The only clock spec is
     the internal HSI at **−1.7 %/+1.6 % over 0–70 °C** and **−2.6 %/+2.2 %
     over −40…85 °C** (DS Table 3-9, printed p.26), against USB 2.0 full-speed
     **±0.25 %** — **6.5× to 10× outside budget at every documented temperature
     range, including the narrowest.** Even the TYPICAL ±0.8 % is 3× over. WCH
     documents no SOF-based auto-trim (RCC has no such bit; RM Chapter 18
     USBFS has no clock section) and makes no "meets USB FS" claim anywhere.
     It works in the field via software trimming — but an undocumented
     mechanism cannot be the basis of a spec claim on a calibration
     instrument.
  3. **The programming workflow needs an unbudgeted board provision.** The only
     documented ISP entry is DS Note 8 (printed p.19): *"PC17 is the BOOT
     detection pin. Upon power-up, PC17 is high, causing the chip to enter the
     BOOT zone."* **PC17 is USB D+.** That means a strap from D+ to VDD on a
     board whose D+ also carries USB. Whether a virgin part auto-enters the
     bootloader WITHOUT the strap is **not stated by WCH**. The strap-free
     fallback is 2-wire SDI on PC18/PC19, i.e. a WCH-LinkE probe and two more
     pads — and QFN-20 has no RST pin to help.

  **And a fourth finding that cuts against it on the safety axis itself.** Its
  GPIO reset state IS clean — `GPIOx_CFGLR/HR/XR` reset to `0x44444444`,
  `CNF=01b/MODE=00b` = **floating input**, no internal pull engaged (RM V1.9
  §8.3.1 Table 8-12 printed p.65; §8.2.2 printed p.60). But that means the
  **external pull-down does 100 % of the work**, so an unpopulated, misplaced or
  open pull-down leaves `RF_CTRL` FLOATING. RP2040's internal 50–80 kΩ
  pull-down sits in PARALLEL with the external one, so RP2040 is **fail-safe
  with the resistor missing and CH32X035 is not.** Against a requirement whose
  whole point is "never land in loopback", that is a regression.
- **`MCP2221A-I/ST`** (C130462, 180 in stock, $2.56 @100). **DISQUALIFIED by
  ADR-0001**, not merely out-ranked: its factory flash defaults leave every GP
  pin a driven push-pull output with `GPIOOUTVAL = 1` in an alternate function
  that idles high (DS20005565E Registers 1-12…1-15 pp.12-15; Table 1-5 p.19;
  §1.7.1.3-6 p.19). JLCPCB does not program device flash, so a board as
  delivered would DRIVE the RF path into loopback. It also costs MORE than the
  entire RP2040 subsystem and needs an external OR gate to merge the header.
- **`CH340C` off DTR/RTS** (C84681, 39 611 in stock, $0.38). REJECTED. CH340DS1
  §4 p.3 defines DTR#/RTS# as active-low outputs and **states NO power-on
  level for them**; §5 p.4 says they are "controlled by computer application
  program". A safety default cannot be certified from a pin whose reset state
  the manufacturer declines to specify. The polarity also runs the wrong way
  (an unopened port rests HIGH = loopback), and host serial stacks routinely
  toggle DTR/RTS on port open/close, which would flip the RF path mid-capture.

## Decision

**RP2040 (LCSC C2040), with W25Q16JVSSIQ QSPI flash (C82317) and a 12 MHz
crystal.**

It is the only candidate whose power-on-safe state is documented **per pin**
and is **fail-safe against a missing external resistor**, whose USB is
crystal-referenced and in spec, and whose blank-board programming needs no
strap, no probe and no vendor tool — a blank part falls into a class-compliant
USB mass-storage bootloader and takes a drag-and-drop UF2.

## Consequences

- **The board's fab tier is `jlc_4layer_advanced`** (ADR-0010). RP2040's QFN-56
  at 0.40 mm pitch computes as advanced unconditionally under `escape_check`
  (56 pins is far outside the ≤12-pin outward-only rescue class). **NOTE: the
  tier is independently forced by the BGS12WN6's pin-2 ground via**, so this is
  not the sole justification and the MCU choice does not carry the tier
  decision alone.
- **~29 of 57 pins are electrically live**, not the ~14 the sourcing spike
  assumed: 12 power pins alone (IOVDD ×6 at 1/10/22/33/42/49, DVDD ×2 at
  23/50, VREG_VIN 44, VREG_VOUT 45, USB_VDD 48, ADC_AVDD 43, plus the centre
  pad) — RP2040 DS Table 621 §5.5.2.2 p.613 — each carrying a mandated
  capacitor. That is 10 × 100 nF + 2 × 1 µF ringing the part. Plan the escape
  as a dense power ring plus a 6-bit bus, not a sparse fanout.
- **`05_firmware/` is on the critical path.** A board with blank flash is SAFE
  (antenna mode) but not USABLE. The release is incomplete without a built,
  versioned UF2 and its hash.
- **Pin constraints, recorded so they are not rediscovered:** keep `RF_CTRL`
  OFF GPIO15 (errata RP2040-E5, p.631 — the USB enumeration workaround uses
  GPIO15 during bus reset, and the Pico SDK pulls it in as a TinyUSB
  dependency); off GPIO0/1 if a debug UART is wanted; off QSPI_SS (the BOOTSEL
  strap). Put the header input on an ADC-capable pin (GPIO26–29) per ADR-0008.
- **DO-NOT-SUBSTITUTE: a "pin-compatible upgrade" to a pre-A4 RP2350 destroys
  the ADR-0001 safety argument.** RP2350-E9 is exactly the erratum where the
  pad pull-down cannot hold a floating input below ~2.2 V. (Note RP2040-E9 is
  a different, unrelated bootloader erratum — the two are easily confused.)
- **The FLASH is the fragile supply link, not the MCU.** Four of six 16-Mbit
  QSPI SKUs read out of stock at LCSC on 2026-07-27 (C559216, C194871,
  C559220, C115407). The committed C82317 has 8 927 pieces and costs
  **more than the RP2040 itself** ($0.76). The in-stock fallback
  W25Q16JVUXIQ (C2843335, 21 960) is **USON-8 — a different footprint, so a
  stockout is a re-spin, not a re-BOM.** Re-check C82317 at order time.
- **THE CRYSTAL IS AN OPEN SOURCING ITEM AND MUST NOT BE TAKEN FROM THE BASIC
  LIBRARY BLINDLY.** The JLC Basic 12 MHz part X322512MSB4SI (C9002) is
  **CL = 20 pF and ESR = 80 Ω**, against Raspberry Pi's own reference
  (`hardware-design-with-rp2040` §2.3 p.10, Table 1 §2.3.1 p.11) of
  **CL = 10 pF, ESR ≤ 50 Ω** — 2× the load and 1.6× the ESR ceiling, with the
  1 kΩ damping resistor sized against the 50 Ω part. The vendor states
  outright: *"Any deviation from the crystal circuit shown here … will require
  extensive testing to ensure that the crystal oscillates under all conditions,
  and starts-up sufficiently quickly."* **A crystal that does not start means
  USB never enumerates.** Two acceptable resolutions, and the choice is
  DEFERRED with both fully specified:
  (a) source a 12 MHz **CL ≤ 10 pF, ESR ≤ 50 Ω** part, accept Extended status,
      keep the reference 15 pF load caps and the 1 kΩ series;
  (b) commit C9002, **recompute the load caps to 2 × (20 − 3) = 34 pF ⇒ 33 pF
      E24 — NOT the reference's 15 pF** — and put a start-up test at both
      temperature extremes into the release gate.
  Copying the Pico's 15 pF onto a 20 pF crystal is the single most likely way
  this board ends up with a chip that never enumerates.
- **The RF/EMI argument against RP2040 SURVIVES and is not dismissed.** The
  external XIP flash bus is a real, continuous in-band spur source that an
  internal-flash part would not have, and no measurement was made either way.
  Mitigation is placement (ARCHITECTURE §10.5): RP2040 + micro-USB at the far
  end from every SMA/SMP, QSPI kept short and local to the flash. If measured
  spurs prove a problem, the answer is shielding or a re-pick — and the re-pick
  would have to clear findings 2 and 3 above first.
- MSL 3 at JLCPCB — it bakes before reflow. JLC handles it; it must appear in
  the order paperwork.

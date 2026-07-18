# XMOS xcore.ai Multichannel Audio Board (XK-AUDIO-316-MC-AB) — hardware reference notes

Source document: **"xcore.ai Multichannel Audio Board 1v1 Hardware Manual"**, XMOS doc
XM014727A, publication 2022/10/4 (26 pages). Local copy:
`01_docs/xmos_mc_audio_hw_manual_1V1.pdf`
(sha256 `f2920845fc677ea5c45ab7915c1eba7047a2870d370b0b5de283c218697887b6`).

The board's XU316 is the **XU316-1024-TQ128-C24** (§2, p5). Schematics are embedded as
Figures 23–30 (pp22–25), 8 sheets titled Top Level / XMOS / DAC / ADC / DigitalIO /
Clocks / XTAG4 / Power (sheet names visible in title blocks). All reference designators
and values below were read from those schematic figures rendered at high resolution.
Where something is not shown in the manual it is explicitly stated.

---

## 1. Power tree (§15 pp18–19; Power.SchDoc = Fig 30, p25)

Input: USB VBUS from "USB DEVICE" connector J16, or "EXTERNAL POWER" USB micro-B J23
(10118193). J22 (68001-203HLF 3-pin) "PWR SRC" selects BUS (1-2) vs EXT (2-3) power
(§12 p16, Fig 30).

| Rail | Regulator | Refdes | Source | Set point / notes |
|---|---|---|---|---|
| 5V | NCP360 OVP/inrush limiter | U14 | VBUS | OnSemi NCP360 "overvoltage protection ... and also inrush current limiting" (§15 p19). EN_N pulled via R15 10K to GND; C101 1U in, C102 1U + C103 100N out; FB5 ferrite 220R/2.2A to 5V rail. |
| 3V3X (always-on) | AP61102 buck | U16 | 5V | VFB=0.6V, VO = 0.6×(1+68/15) = **3.32V** (R67 68K / R70 15K, note printed on Fig 30). L2 1U5, C111 10U out, C110 100P feed-forward, C109 4U7 in. EN tied to VIN (R137 220K NF). |
| 1V8 (always-on) | TCR2LF18 LDO | U18 | 3V3X via R139 0R | C118 1U in, C119 1U out, R77 220K bleed. Manual: "1V8 ... uses a low drop out linear regulator from the 3V3X supply. This is because 1V8 uses much less current" (§15 p19). |
| 0V9 core (always-on, sequenced) | AP61102 buck | U17 | 5V (via R73 0R1 sense) | VO = 0.6×(1+10/20) = **0.9V** (R74 10K / R76 20K); L3 1U5, C117 22U + C116 560P, C115 4U7 in. **MARGIN net (X0D22) injects into FB via R75 240K**: DRIVE HIGH(1.8V)=0.850V, PULL UP(20k)=0.854V, HI-Z=0.900V, PULL DN(30k)=0.922V, DRIVE LOW=0.925V (table on Fig 30). "The xcore.ai VDD supply voltage is reduced to around 0.85V from the nominal 0.9V" in USB suspend (§15 p19). |
| 3V3 (switched) | AP22653 load switch | U34 | 3V3X | EN = EN_BRD_PWR (= SUSPEND_N, X0D41, R64 100K pulldown). ILIM R71 68K → "RLIM = 68K => ILIM(MIN) = 311mA"; C113 10U out, R69 10K bleed. |
| 5V_SW (switched) | AP22653 load switch | U35 | 5V | Same EN_BRD_PWR; R143 68K ILIM, C178 4U7, R142 10K bleed. |
| 3V3A (analog, switched) | XC6227C331 LDO | U15 | 5V_SW via FB6 220R/2.2A + R62 0R5 | C105 4U7 in, C106 100N + C107 10U out, R63 4K7 bleed. FB4 (220R 2.2A, NF) is a "FERRITE BUILD OPTION FOR USING 3V3 DC-DC SUPPLY". Note on Fig 30: "3V3A - ADCs 31mA typ. x2 + DACs 32mA x4 max = ~200mA, Pd = (5-3.3)*0.2 = 340mW". |

**Sequencing** (§15 p19): "The supplies are sequenced such that the 3V3X and 1V8
supplies are present before the 0V9 supply is turned on. This meets the requirement of
the xcore.ai device that the VDDIOB18 supply must not be turned on last."
**How enforced (Fig 30):** the 3V3X buck U16's open-drain **PG (pin 6) output goes
through R68 0R into U17's EN (pin 5)**, with R72 10K pull-up to 5V — i.e. a PG→EN
daisy-chain gates the 0V9 core buck behind the 3V3X rail (1V8 is an always-on LDO from
3V3X so it rises with it). Switched rails (3V3/5V_SW/3V3A) come up later under firmware
control via SUSPEND_N. Load switches (not regulator EN pins) are used for on/off
because of inrush concerns (§15 p18).

**xcore GPIO for power control** (Fig 22, p19): X0D22 (port 1G) = VDD core margin
("Drive high for 0.85V, high-z for 0.9V"); X0D41 (P8D5) = SUSPEND_N "Enables the 5V_SW
and 3V3 supplies when high".

### Decoupling for the XU316 (XMOS.SchDoc, Fig 24 p22)
- **0V9 (VDD core, 15 pins)**: C9 2U2 + C10, C39–C51 = 13× 100N (one bank shown by U8A);
  plus a second 2U2 visible on the right of the POWER block.
- **3V3X (VDDIOL/VDDIOT/VDDIOR)**: C52–C57 6× 100N (plus 3V3 plane decoupling C166–C173
  8× 100N on the Power sheet, "3V3 PLANE DECOUPLING FOR SIGNALS SWITCHING REF PLANES").
- **1V8 (VDDIOB18)**: C58, C59 2× 100N.
- **PLL_AVDD**: fed from 0V9 through **FB3 ferrite (1000R @ 100MHz, 0.25A)** with C6 1U.
- **USB_VDD18** (1V8): C7 100N. **USB_VDD33** (3V3X): C8 100N.
- MIPI_VDD18 (pin 24) and MIPI_VDD09 (pin 27) are tied to GND (MIPI unused on this board).
- PLL_AVSS (pin 42) to GND. GND pins 30 and 129 (exposed pad).

## 2. Reset / boot (§3 p5, Top Level Fig 23 p22)

- **RST_N generation: no supervisor.** RST_N is pulled up with **R43 10K to 1V8** with
  **C177 10N to GND** (RC), and is driven by the integrated XTAG4 debugger subsheet
  (U_XTAG4) and brought to the XSYS2 connector (J4 pin 10). RST_N enters the XU316 at
  pin 38 (SYSTEM block, VDDIOB18 1.8V domain).
- **QSPI boot flash**: U9 **W25Q32JVSSIQ** (32Mbit) powered from 3V3X with C62 100N.
  Wiring (Fig 3 p5 table + Fig 23):

  | Flash pin | Signal | XU316 pin | Port |
  |---|---|---|---|
  | CS_N (1) | QSPI_CS_N | X0D01 | P1B0 |
  | SCK (6) | QSPI_CLK | X0D10 | P1C0 |
  | SI/IO0 (5) | QSPI_D0 | X0D04 | P4B0 |
  | SO/IO1 (2) | QSPI_D1 | X0D05 | P4B1 |
  | WP_N/IO2 (3) | QSPI_D2 | X0D06 | P4B2 |
  | HOLD_N/IO3 (7) | QSPI_D3 | X0D07 | P4B3 |

  **R38 10K pull-up from QSPI_CS_N to 3V3X** (only strap-like resistor on the QSPI bus).
  A NF 2×5 header J44 (67997-210HLF) breaks out QSPI for programming.
- **MODE/boot strap pins: the manual does not show any MODE pin straps** — the TQ128
  boot source selection (boot from QSPI) is the device default; no MODE resistors appear
  on any schematic sheet. (See datasheet notes: TQ128 has no dedicated MODE pins; boot
  is from QSPI on ports 1B/1C/4B.)
- The board note "DAC DOUT IS LOOPBACK I2S DATA FOR TESTING" (Fig 25) and I2S loopback
  resistors R24/R25/R27/R32 33R (Fig 23) are test features, not boot related.

## 3. Clocking (§4 p6, §11 pp13–15; XMOS.SchDoc Fig 24; Clocks.SchDoc Fig 28 p24)

- **System crystal**: X2 **Epson FA-238 24MHz** on XIN (pin 34) / XOUT (pin 33), load
  caps **C60/C61 18pF**, feedback **R18 1M** XIN–XOUT, series **R20 680R** between the
  crystal and XOUT. TP5 on XIN, TP16 on XOUT. ("The device is clocked by an integrated
  low power crystal oscillator block using an external 24MHz crystal", §4 p6.)
- **Audio master clock sources** (§11 p13): xcore.ai secondary (application) PLL,
  Cirrus **CS2100-CP** (U22) fractional-N multiplier, or Skyworks **Si5351A-B-GT** (U26).
  Selected by EXT_PLL_SEL (X0D42, P8D6) and MCLK_DIR (X0D43, P8D7); table (Fig 28):
  EXT_PLL_SEL=0,MCLK_DIR=0 → CS2100; 1,0 → Si5351A; X,1 → XMOS MCLK.
- CS2100: CLK_IN (pin5) ← PLL_SYNC (X0D00, P1A0, "CS2100 Frequency Ref"); its own
  reference is X3 24M crystal + C144/C145 27P on XTI/XTO; AD0/CS_N to GND → I2C 0x4E;
  CLK_OUT (pin3) via **R93 33R** into mux. Si5351A: X4 XRCGB 25M crystal on XA/XB;
  CLK0 (pin10) via **R99 33R** into mux; I2C 0x60.
- **Mux/buffer chain** (Fig 28): U24 **74LVC1G157** (S = EXT_PLL_SEL; R135/R136 10K
  pulldowns on inputs) → U25 **74LVC1G157** (S = MCLK_DIR, I1 = MCLK from xcore) →
  **R97 33R** → MCLK trunk → U23 **NC7NZ34** triple buffer fans out through
  **R94/R95/R96 33R** to **MCLK_ADC / MCLK_DAC / MCLK_DIG**. U27 **SN74LVC1G125**
  (OE_N = MCLK_DIR) drives the trunk back through **R98 33R** to **MCLK_XMOS** when the
  external PLLs are the source. Decoupling C140–C143, C146 100N at the logic.
- **MCLK at the XU316**: net MCLK_XMOS connects to **X1D11 (P1D0, pin 23, marked
  "1D/APLLOUT")** through R117 33R, and also to **X0D11 (P1D0 tile0, pin 7)** through
  R118 0R (Fig 23; port map p20/21: "X1D11 P1D0 Audio master clock input or output as
  specified by MCLK_DIR"; "X0D11 P1D0 ... Input only - for use by tile0 threads e.g.
  USB thread for clock sync").
- **I2S/TDM clocks** (Figs 6/9 p7/9, port map pp20–21): **LRCK = X1D01 (P1B0, pin 20)**
  via R12 33R; **BCLK = X1D10 (P1C0, pin 22)** via R13 33R. Both 33R series at source.
- **TDM/I2S data**: ADC inputs X_ADC_D0–D3 = **X1D24 (P1I0), X1D25 (P1J0), X1D34
  (P1K0), X1D35 (P1L0)**; DAC outputs X_DAC_D0–D3 = **X1D39 (P1P0), X1D38 (P1O0),
  X1D37 (P1N0), X1D36 (P1M0)** (Figs 6/9; all 1-bit ports).
- Word-clock input: BNC J29 → R138 10K + optional 75R termination (R92 + jumper J30) →
  R91 1K → clamp D9 MMSD914T1G / D13 MM3Z3V9B zener + C174 10N → SN74LVC1G125 buffer →
  R90 33R → WCLK_IN (X0D39, P1P0/P8D3).

## 4. USB section (§12 p16; Fig 23 p22; XMOS.SchDoc Fig 24)

- Connector J16 micro-B (GCT 10118193). VBUS → **R47 0R1** (current-sense option, J15
  NF) → USB_VBUS; **C63 10N + C64 100N** on VBUS at the connector, **R48 470K**
  discharge to GND. Board can present <10uF on VBUS per USB spec (§15 p18).
- **D+/D-: no series resistors** — USB_D_P/USB_D_N route from J16 pins 3/2 directly to
  XU316 **USB_DP (pin 60) / USB_DM (pin 59)** (termination is on-chip). USB_ID (pin 58)
  NC.
- **ESD**: D8 **NUP4114** 4-channel array clamps USB_D_P, USB_D_N and VBUS, placed at
  the connector (Fig 23).
- **VBUS sensing** (§12 p16): NOT a plain divider — R45 100K from VBUS to base of Q1
  MMBT3904 (R46 100K base-emitter to GND), collector pulled up by R44 47K to 3V3X →
  **VBUS_DETECT (X0D14, P4C0), "High if Vbus is less than ~0.6V"** (i.e. inverted;
  Fig 18 p16 describes it as VBUS presence detect). Chosen over a resistor divider "as
  it avoids any current paths from Vbus to the power supplies on the board" (§12 p16).
  J14 "VBUS DET" jumper: fit for self-powered, no-fit for bus-powered (§12 table).
- **USB PHY rails**: USB_VDD33 (pin 61) from 3V3X with C8 100N; USB_VDD18 (pin 62) from
  1V8 with C7 100N. **No dedicated ferrites on the USB rails** (the only ferrite near
  the core is FB3 on PLL_AVDD; FB5/FB6 are on the 5V/5V_SW power path).

## 5. PCM1865 ADCs (§6 pp6–7, §14 p18; ADC.SchDoc Fig 26 p23)

Two **PCM1865** 4-ch ADCs (U19, U20), 8 single-ended line inputs via 3.5mm jacks
(SJ-3523-SMT), max input 2.1Vrms (§6 p6).

- **I2C**: MD0 (pin 26) = 0 → I2C mode. U19: MS/AD (pin 25) → GND via R83 0R → **0x4A**
  (ch1–4). U20: MS/AD → 3V3 → **0x4B** (ch5–8) (notes printed on Fig 26; matches I2C
  map Fig 21 p18, on I2C bus 0 behind the PCA9540B mux U33 at 0x70).
- **RST wiring: PCM1865 has no reset pin and none is wired** — reset is via I2C
  (RESET register); the manual shows no RST net to the ADCs.
- **Analog input network per channel** (Fig 26): jack tip/ring → **47K to GND**
  (R78/R79/R81/R82/R84/R85/R87/R88) → **10uF AC-coupling cap** (C120/C121/C126/C127/
  C130/C131/C136/C137) → VINL1_VIN1P (pin 3)/VINR1_VIN2P (pin 4)/VINL2_VIN1M (pin 1)/
  VINR2_VIN2M (pin 2). VIN3/VIN4 pins NC; MICBIAS NC.
- **Rails**: IOVDD (pin 14) + DVDD (pin 13) = **3V3** (switched digital rail); AVDD
  (pin 8) = **3V3A** (linear-regulated analog rail). Decoupling per ADC: 3V3A 4U7+100N
  (C122/C123, C132/C133); 3V3 4U7+100N (C124/C125, C134/C135); LDO out (pin 11) C161
  100N + C129 2U2; VREF (pin 6) C128 2U2. DGND (12) and AGND (7) common to GND.
- **Clock/data**: SCKI (15) = MCLK_ADC; BCK (17) = BCLK; LRCK (16) = LRCK; DOUT (18) =
  ADC_DAT0 (U19) / ADC_DAT2 (U20); **MISO/GPIO0 (22) is used as a second data output**
  ADC_DAT1 (U19) / ADC_DAT3 (U20); GPIO1/INTA (21) = shared ADC_GPIO interrupt line via
  R80/R86 33R to X0D33 (P4E3). XI (10) tied low, XO (9) NC (SCKI-clocked).
- ADC data reaches the xcore through the I2S/TDM jumper field J6/J9/J11/J13
  (68001-204HLF): I2S mode = all 2-3; TDM mode per Fig 5 table (p7).

## 6. xSYS debug (§5 p6; Figs 23/24)

- On-board **integrated XTAG4** debugger (U_XTAG4 subsheet) connects to the XU316 JTAG
  + xSCOPE and to the DEBUG micro-B USB. "It only needs to be connected while
  debugging" (§5 p6).
- **XU316 debug pins** (XMOS.SchDoc, SYSTEM block, all in the VDDIOB18 1.8V domain):
  TCK = pin 51, TMS = pin 44, TDI = pin 36, TDO = pin 37, RST_N = pin 38. **There is no
  TRST pin.** TDO passes through R122 33R (and R123 0R to the external connector net
  TDO_X). xSCOPE uses the 2-wire xlink: XL_DN1/XL_DN0/XL_UP0/XL_UP1 = X1D16/X1D17/
  X1D18/X1D19 (P4D0..P4D3, "XSCOPE DEBUG" in port map p21), with R39/R40 33R on the up
  links.
- **XSYS2 debug target connector J4** (Samtec FTSH-110-01-F-DV-K 2×10, NF, "OPTION FOR
  USE WITH EXTERNAL XTAG4", Fig 23): even pins: 2 = TMS, 4 = TCK, 6 = TDO (via R123 0R
  from TDO_X), 8 = TDI, 10 = RST_N, 12 = XL_DN1, 14 = XL_DN0, 16 = XL_UP0, 18 = XL_UP1,
  20 = NC; pin 1 = 1V8 sense, pins 3/5 = 3V3X (C164/C165 100N local decoupling),
  remaining odd pins = GND. J45 is a second NF FTSH-110 "TEST ONLY (CHAIN JTAG)".

## 7. Other board facts worth citing

- I2C fabric: single xcore I2C master (I2C_SCL = X0D35 P1L0, I2C_SDA = X0D36 P1M0,
  4K7 pull-ups R41/R42) → PCA9540B 2-ch mux U33 @0x70 (bus0: 4× PCM5122 DACs 0x4C–0x4F,
  2× PCM1865 0x4A/0x4B; bus1: CS2100 0x4E, Si5351A 0x60) (§14 pp17–18, Fig 21).
- LEDs LED_0..3 = X0D28..X0D31 (P4F0..P4F3) via 470R; buttons BUT_0..2 = X0D26/27/32
  (P4E0/1/2) with 10K pull-ups to 3V3 (Figs 19/20 p17).
- Full pin/port/net map for every used XU316 pin: §18 tables pp20–21.
- Board dimensions 160×130mm, M3 mounting holes (§17 p19).

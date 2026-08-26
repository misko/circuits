# cooksense MAIN (Board A+B) — fresh-context PIN / PAD review, v1.7 REGATE4 (65 °C)

Reviewer: fresh-context agent, no prior session context, no stake in the design.
Date: 2026-07-30.
Artifact under review: `06_build/staging/cooksense-v1.7/`
Board read (READ-ONLY): `04_kicad/cooksense.kicad_pcb`, md5 `9f4fd5fae810f40a52b1035df727243c`
(verified identical to `06_build/staging/cooksense-v1.7/source/cooksense.kicad_pcb`).

Lens: pin / pad correctness only. Every prior verdict on this board was voided by the
material change, so every pin was re-derived from the part's own datasheet figure and
judged electrically against the board net. No `08_reviews/`, `01_docs/journal/`,
`01_docs/learnings/`, `STATUS-*`, `RESUME.md`, or the staging `*redteam*` / `*pin-review*`
/ `*render-review*` / `DISPOSITIONS.md` files were opened.

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```

`order_verdict` is BLOCKED-SOURCING for the single reason handed to me as measured:
BOM line `C265111` (JST SM08B-GHS-TB, `J_THERM_A` / `J_THERM_B`) reads stock 5 against
minPurchaseNum 21 — unbuyable today. That is a supply fact and it has **not** been allowed
to colour `design_verdict`. I found **zero pin FAILs**. Nothing in this lens blocks the
order on design grounds.

---

## 1. Method

1. Dossiers generated conclusion-free with
   `skills/kicad-pcb/scripts/pin_audit.py 04_kicad/cooksense.kicad_pcb
   06_build/staging/cooksense-v1.7/fab/bom_jlc.csv 02_parts <outdir>` (53 dossiers), plus a
   second run with `--refs J_TC` because `J_TC` carries an empty MPN column in `bom_jlc.csv`
   and was silently skipped by the first run.
2. For each part I rendered the datasheet's own pin-configuration figure
   (`pdftoppm -png -r 150..600 -f <page> -l <page>`) and read the pinout off the figure
   **before** looking at the dossier's `function` column.
3. Vendored footprints in `source/cooksense.pretty/` and the library footprints for every
   polarized 2-pad part were parsed for their asymmetric F.Fab / F.SilkS geometry, so that
   polarity was established from graphics rather than from a self-consistent netlist.
4. Every remaining footprint had all its pads enumerated from `pcbnew` and its net read.

Every load-bearing claim below is tagged **MEASURED** (with the figure and page I read) or
**INHERITED** (with the source, not re-verified).

---

## 2. The `DIP05-1A72-13L` reed relays — the defect this board has paid for six times

**Verdict: PASS, 12/12. MEASURED.**

Datasheet: `02_parts/DIP05-1A72-13L/datasheet-reed-relay-series-dip.pdf`
(Standex DIP Series Reed Relays, Version 03, 01 Aug 2025).

### 2.1 What the `-13` pin-out figure actually says

**MEASURED** — DS **p.3**, section *"Pin-Out (Top View) (2.54 mm [0.10"] pitch grid)"*,
sub-figure **"13"**, rendered at 200 dpi and again at 3× zoom. Reading the 2.54 mm grid
directly off the render:

| feature in sub-figure 13 | measured on the grid |
|---|---|
| leads present | exactly four: **2, 6** (lower row) and **8, 14** (upper row) |
| pin 14 ↔ pin 8 separation | 6 grid cells = **15.24 mm** (the two extremes of the 8–14 row) |
| pin 2 ↔ pin 6 separation | 4 grid cells = **10.16 mm**, each inset one pitch from pins 1 and 7 |
| row separation | 3 cells = **7.62 mm** (0.3" DIP) |
| **COIL** | drawn as a 3-hump inductor between **pins 2 and 6** |
| **CONTACT** | drawn as a Form-A (SPST-NO) blade with actuator triangle between **pins 14 and 8** |
| polarity marker | **none**. Contrast sub-figure **19** (Form 1B) on the same page, which *does* carry a `+`. |

So under pin-out code 13 the coil is on the 1–7 row and the contact is on the 8–14 row.
This is exactly the axis on which the `-12L` and `-13L` codes differ.

### 2.2 The land

**MEASURED** — `source/cooksense.pretty/Relay_StandexDIP_1A_pinout13.kicad_mod`, pad centres
read from the file:

| pad | local (x, y) mm | column span | DIP lead position it lands on |
|---|---|---|---|
| 1 | (−3.810, −5.080) | west column, span **10.16** | DIP **2** |
| 2 | (−3.810, +5.080) | west column | DIP **6** |
| 3 | (+3.810, +7.620) | east column, span **15.24** | DIP **8** |
| 4 | (+3.810, −7.620) | east column | DIP **14** |

Column-to-column 7.620 mm = 0.3" DIP. Pin-1 silk marker (`fp_circle` at −4.6, −9.2) sits at
the west-north corner, i.e. the DIP-1 corner, giving pin 1 at (−3.81, −7.62) and the
standard CCW winding — from which the four hole positions above follow arithmetically.

**The decisive check is the span asymmetry, and it passes:** the west hole column spans
**10.16 mm** and the east spans **15.24 mm**. The part's coil row spans 10.16 mm and its
contact row spans 15.24 mm. A 180° in-plane rotation would demand the 10.16 mm coil pair
reach a 15.24 mm hole pair — 2.54 mm of stretch on 0.25 mm leads in 0.80 mm holes. **The
land is mechanically keyed: exactly one insertion orientation exists, and in it the coil
lands on pads 1/2 and the contact on pads 3/4.**

### 2.3 Does coil polarity matter? No — and I checked rather than assumed

**MEASURED** — DS **p.4**, *"Options ( ) Versions with magnetic shield (Top View)"*, rendered
at 200 dpi. The four option figures are:

- **L(M)** — bare grid, **no diode symbol, no shield bar**.
- **E(R)** — adds an electrostatic shield (dashes) tied to pin 8.
- **D(Q)** — adds a **coil-suppression diode** across the lower (coil) row.
- **F(S)** — shield *and* diode.

`DIP05-1A72-13L` is option **L** → **no internal coil diode**. Combined with Form A (dry,
non-polarized contact) and the absence of a `+` in sub-figure 13, **no lead on this part is
polarity-sensitive**. Cross-check, same datasheet **p.2** footnote: *"Coil polarity on Form B
must be observed. Pin 2 is positive."* — scoped explicitly to Form B (pin-out 19), not ours.

Corollary I then verified on the board, because option L forces it: **every one of the 12
coils has an external flyback path.** Eleven run to `U_ULNA`/`U_ULNB` whose COM pin (10) is
on `5V_KEY_RELAY`, the same rail as their coil high sides; `K_STOP` runs to the discrete
`Q_STOPDRV` and is clamped by `D_KSTOP` (cathode on `5V_STOP`). No coil is unclamped.

### 2.4 Nets, all 12 instances

| refdes | pad1 (coil hi) | pad2 (coil lo) | pad3 (contact) | pad4 (contact) |
|---|---|---|---|---|
| K_U1..K_U6 | 5V_KEY_RELAY | COIL_U1..U6_N | KP_U1..KP_U6 | U_SEL_BUS |
| K_D1..K_D4 | 5V_KEY_RELAY | COIL_D1..D4_N | KP_D1..KP_D4 | D_SEL_BUS |
| K_PRESS | 5V_KEY_RELAY | COIL_PRESS_N | RKEY_MID | U_SEL_BUS |
| K_STOP | 5V_STOP | COIL_STOP_N | RSTOP_MID | KP_U6 |

Structurally identical across all 12: pads 1/2 always a supply rail and a driver-pulled coil
return; pads 3/4 always two signal-domain nets and never a rail. No instance diverges.
`K_STOP`'s use of the separate `5V_STOP` rail (fed from `5V_PROTECTED` through `R_STOPRAIL`)
is a deliberate segregation, not a pin error.

**PASS — 12/12.**

---

## 3. Polarized 2-pad parts (the class no electrical check can see)

The footprint convention was **MEASURED**, not assumed: I parsed each library footprint and
read its asymmetric F.Fab geometry.

**`Diode_SMD:D_SMA` / `D_SMB` / `D_SOD-323` — pad 1 = CATHODE.** MEASURED from the F.Fab
diode symbol: in `D_SOD-323` the triangle has base at x=+0.20 and apex at x=−0.30, and a
vertical **bar** sits at x=−0.30 on the apex, with lead stubs to (−0.50, 0) and (+0.45, 0).
Bar = cathode, on the pad-1 (x=−1.05) side. Same construction in `D_SMA` (bar at −0.649,
base at +0.501) and `D_SMB`. Corroborated by F.SilkS, which draws the cathode band as an
extra vertical line on the pad-1 side in all three.

**`Capacitor_SMD:CP_Elec_6.3x7.7` — pad 1 = POSITIVE.** MEASURED: F.Fab carries a drawn `+`
glyph at (−2.39, −1.33) and F.SilkS a second `+` at (−4.04, −1.85), both on the pad-1
(x=−2.7) side, with the body chamfers also on that side.

| refdes | MPN | pad1 net | pad2 net | pad1 role | required | verdict |
|---|---|---|---|---|---|---|
| D_REVCLAMP | SS34 | 5V_FUSED | GND | cathode | reverse clamp: K to rail, A to GND, conducts only on reversed input and blows F1 | **PASS** |
| D_KSTOP | SS34 | 5V_STOP | COIL_STOP_N | cathode | flyback: K to coil supply, A to the low-side switched node | **PASS** |
| D_TVS | SMBJ5.0A | 5V_PROTECTED | GND | cathode | unidirectional TVS (`A` suffix, not `CA`): K to +rail | **PASS** |
| CE1 | RVT220UF16V | 5V_PROTECTED | GND | **+** | + to the 5 V rail | **PASS** |
| D_ESD_IN | PESD5V0S1BA | 5V_IN | GND | K1 | — | **PASS (n/a)** |
| D_ESTOP | PESD5V0S1BA | ESTOP_RAW_IN | GND | K1 | — | **PASS (n/a)** |
| D_LCCLK | PESD5V0S1BA | LC_CLK | GND | K1 | — | **PASS (n/a)** |
| D_LCDAT | PESD5V0S1BA | LC_DAT | GND | K1 | — | **PASS (n/a)** |
| D_COILEN | PESD5V0S1BA | COIL_EN_IN | GND | K1 | — | **PASS (n/a)** |

The five `PESD5V0S1BA` are marked n/a on solid ground, not by hand-waving: **MEASURED** —
Nexperia `PESD5V0S1BA` data sheet (26 April 2024), title line *"Bidirectional ESD protection
diode"*, and **Sec. 5 "Pinning information", Table 2, p.2**: pin 1 = **K1** (cathode diode 1),
pin 2 = **K2** (cathode diode 2). Both pins are cathodes of a back-to-back pair, so the part
is electrically symmetric and **cannot be fitted backwards**. That removes 5 of the 8 diodes
from the polarity-risk population outright.

`F1` (MF-MSMF200L PPTC) and `FB1` (GZ2012D601TF ferrite) are non-polar 2-terminal parts;
`F1` sits 5V_IN→5V_FUSED and `FB1` 3V3→3V3_ANALOG, both correctly in series.

---

## 4. Per-part table

Coverage denominator and the full population are in §6. `fig+page` is the figure I rendered
or the pin table I read myself unless marked INHERITED.

| refdes | MPN | pins checked | datasheet figure + page cited | PASS/FAIL | note |
|---|---|---|---|---|---|
| K_U1–U6, K_D1–D4, K_PRESS, K_STOP (12) | DIP05-1A72-13L | 4×12 = 48 | Standex DIP Series v03, **p.3** sub-fig "13"; **p.4** options L(M)/D(Q); **p.2** Form-B polarity note | **PASS** | land span-keyed 10.16 vs 15.24 mm; option L = no coil diode, so no polarity; all 12 coils externally clamped |
| U_TC | MAX31856MUD+T | 14 | ADI MAX31856 pin list, TSSOP-14 (see note) | **PASS** | 1 AGND=GND, 2 BIAS=TC_NEG, 3 T−=TC_NEG, 4 T+=TC_POS, 5 AVDD=3V3, **6 DNC = open ✓**, 7 DRDY=TC_DRDY_N, 8 DVDD=3V3, 9 CS=TC_CS_N, 10 SCK, 11 SDO→MISO, 12 SDI←MOSI, 13 FAULT, 14 DGND. BIAS tied to T− is the datasheet connection. **Evidence grade: SECONDARY** — no PDF is cached in `02_parts/MAX31856MUD+T/`; two direct fetches of analog.com timed out; the pin list came from a web read of the analog.com datasheet, not a figure I rendered. |
| U_ADC | MCP3208-CI-SL | 16 | DS21298E **p.1** *"Package Types"*, PDIP/SOIC 16-pin MCP3208 | **PASS** | 1–8 CH0–CH7, 9 DGND, 10 CS/SHDN, 11 DIN←MOSI, 12 DOUT→MISO, 13 CLK, 14 AGND, 15 VREF, 16 VDD. SPI directions correct; VREF and VDD both on 3V3_ANALOG. |
| U_EXP | MCP23017-E/SS | 28 | DS20001952C **p.1** *"Package Types"*, SOIC/SPDIP/SSOP column | **PASS** | 9 VDD, 10 VSS, 11 NC open, 12 SCK, 13 SDA, 14 NC open, 15/16/17 A0/A1/A2 = GND (addr 0), **18 RESET = WD_OK**, 19 INTB, 20 INTA. GPB0–7 all inputs, GPA0–7 all outputs/IDs. |
| U_EFUSE | TPS259573DSGR | 8 + EP | SLVSE57C **Sec. 6, p.4**, fig *"TPS2595x3 DSG Package 8-Pin WSON Top View"* | **PASS** | `-73` = **EN/OVLO, active-low**; R_OVT 100k / R_OVB 26.1k divider on pin 2 matches that variant and must not float ✓. 3,4 IN=5V_RPP; 5 OUT; 6 FLT open-drain w/ R_PG pull-up; 7 ILM=R_ILM 1.2k; 8 GND; **EP = GND ✓** |
| U_WD | TPS3823-33DBVR | 5 | SLVS165O **Figure 5-1, p.4** (5-Pin SOT-23 DBV, Top View) | **PASS** | 1 RESET̄=WD_OK (active-low → high means OK), 2 GND, 3 MR̄=WD_MR_N, 4 WDI=WD_PET, 5 VDD=3V3 |
| U_ULNA, U_ULNB | TBD62083AFWG | 18×2 = 36 | TBD62083A (2016-05-11) **p.2** *"Pin explanations"* table | **PASS** | I1–I8=1–8, GND=9, **COMMON=10 → 5V_KEY_RELAY ✓**, O8–O1=11–18. Channel map verified 1:1: In→Out for all 11 driven channels (see §2.3). |
| U_SR1 | SN74HC595DR | 16 | SCLS041J **Sec. 5, p.3**, *"D, N, NS, J, DB, or PW Package, 16-Pin SOIC, Top View"* (rendered) | **PASS** | 1 QB … 7 QH, 8 GND, 9 QH′ open, 10 SRCLR̄, 11 SRCLK, 12 RCLK=KEY_LATCH_G, 13 OE̅=SR_OE_N, 14 SER, 15 QA, 16 VCC |
| U_DECU, U_DECD | SN74HC238DR | 16×2 = 32 | TI D2804 **p.2**, *"logic symbols (alternatives)"*, pin numbers for D/J/N packages (rendered) | **PASS** | A=1,B=2,C=3,Ḡ2A=4,Ḡ2B=5,G1=6,Y7=7,GND=8,Y6=9,Y5=10,Y4=11,Y3=12,Y2=13,Y1=14,Y0=15,VCC=16. Both gates grounded ✓. U_DECD ties C=GND, and exactly Y4–Y7 are the unconnected outputs ✓ |
| U_SCHM | SN74HC14DR | 14 | SCLS085L **Figure 4-1, p.3** | **PASS** | two double-inversion chains (ESTOP_RAW→ESTOP_OK, MODE_RAW→MODE_AUTO_HW); unused inverters 5 and 6 have inputs (11, 13) tied to GND and outputs (10, 12) open ✓ |
| U_ONESHOT | CD74HC221M96 | 16 | SCHS166F **p.1** *"Pinout … CD74HC221 (PDIP, SOIC, SOP, TSSOP) TOP VIEW"* | **PASS** | 1 1Ā=GND (enables B-edge trigger ✓), 2 1B, 3 1R̄, 4 1Q̄, 13 1Q, 14 1CX, 15 1CXRX, 16 VCC; mono 2: 9 2Ā=REARM_N, 10 2B=3V3, 11 2R̄=WD_OK, 12 2Q̄. Timing nets C_OS/R_OS and C_OS2/R_OS2 land on the CX/CXRX pair ✓ |
| U_COMP, U_COMP2 | LMV393IDR | 8×2 = 16 | SLCS136V **Sec. 4, p.3**, fig *"LMV393 … D, DDU, DGK OR PW PACKAGE (TOP VIEW)"* | **PASS** | 1 1OUT, 2 1IN−, 3 1IN+, 4 GND, 5 2IN+, 6 2IN−, 7 2OUT, 8 VCC+. Forms a 4-comparator window (TCAM_THRESH low rail, TCAM_OPEN high rail) wired-AND onto TEMP_OK ✓ |
| U_AND1–3, U_CAND1–2, U_FAULTAND, U_LATCHG, U_OSCLR, U_DECUEN, U_DECDEN (10) | SN74LVC1G11DBVR | 6×10 = 60 | SCES487I **Figure 4-1, p.3**, *"DBV or DCK Package, 6-Pin SOT-23 or SOT-SC70 (Top View)"* | **PASS** | **1 A, 2 GND, 3 B, 4 Y, 5 VCC, 6 C** — not the naive 1/2/3=A/B/C guess; the figure is authoritative and the board matches it on all 10 instances. Every unused AND input is tied to **3V3** (pin 6 on U_LATCHG/U_OSCLR/U_DECUEN/U_DECDEN) — HIGH is the correct don't-care for AND; a LOW there would kill the gate. |
| U_LATCHA, U_LATCHB, U_OENAND, U_STOPINV (4) | SN74LVC1G00DCKR | 5×4 = 20 | SCES214 **Sec. 6, p.3**, DCK PACKAGE (TOP VIEW) | **PASS** | 1 A, 2 B, 3 GND, 4 Y, 5 VCC. U_LATCHA/B form a cross-coupled NAND SR latch (set FAULT_SET_N, reset REARM_PULSE_N); U_STOPINV ties A and B for an inverter ✓ |
| U_LDO | AMS1117-3.3 | 3 + tab | INHERITED — no PDF cached; ds1117 SOT-223 convention (1 GND/ADJ, 2 VOUT, 3 VIN, tab = VOUT) | **PASS** | Stock `Package_TO_SOT_SMD:SOT-223`, pad 4 = 2.0×3.8 tab. **Tab-pin merge is correct: pad 4 and pad 2 are both `3V3`.** Pad 3 VIN = 5V_PROTECTED, pad 1 = GND. |
| U_OPTO | LTV-817S-TA1 | 4 | INHERITED — no PDF cached; Lite-On LTV-8x7S convention (1 A, 2 K, 3 E, 4 C) | **PASS** | LED anode (1) fed from CONTACTOR_DRV through R_OPTOLED 330 Ω, cathode (2) to GND — current direction correct, ≈6.4 mA. Phototransistor C (4) and E (3) come out on J_ISOLOOP pins 1 and 4 as a dry contact. |
| Q_COIL, Q_REV, Q_SWA, Q_SWB, Q_SWRHA, Q_SWRHE (6) | AO3401A (P-ch) | 3×6 = 18 | AO3401A DS **p.1** *"SOT23 Top View / Bottom View"* pictorial + JEDEC TO-236AB numbering (see note) | **PASS** | See §5 — orientation is *different* between Q_REV and the load switches, and **both are right**. |
| Q_COILDRV, Q_STOPDRV, Q_SWDRVA, Q_SWDRVB, Q_SWDRVRHA, Q_SWDRVRHE (6) | 2N7002 (N-ch) | 3×6 = 18 | INHERITED — no PDF cached; JEDEC TO-236AB (1 G, 2 S, 3 D) | **PASS** | all six: gate = logic net, source = GND, drain = the P-FET gate node or coil return ✓ |
| J_PI | 2.54-2×20PPC104 | 40 | Raspberry Pi 40-pin GPIO header standard (see §5.2) | **PASS** | strongest single check on the board — all **8** Pi GND pins land on GND, all four Pi power pins are unconnected, and SPI0 lands exactly on 19/21/23/24/26 |
| J_TC | PCC-SMP-K | 2 (+2 NPTH) | Omega PCC-OST-SMP spec **p.2**, *"PCC-SMP, Miniature Connector"* drawing (rendered at 200 and 600 dpi) | **PASS (land)** / **QUESTION (contact polarity)** | land geometry MEASURED-correct to the drawing; contact `+`/`−` **not resolvable** from the cached sheet. See §5.3. |
| J_THERM_A, J_THERM_B | SM08B-GHS-TB | 10×2 = 20 | JST `eGH.pdf` p.1/p.3, *"No. 1 circuit"* at the row end | **PASS** | stock KiCad footprint, unmodified (pad1 x=−4.375 matches library exactly). 1 3V3_SW, 2 GND, 3 SDA, 4 SCL, 5 TH_CAM, 6 TH_MOUNT, 7 TH_PORT, 8 SHIELD_DRAIN; both MP shells on GND ✓. **These are thermistor-pod connectors, not the K-thermocouple — see §5.4.** |
| J_KEY_MATRIX | SM10B-GHS-TB | 12 | JST `eGH.pdf` p.1/p.3 | **PASS** | 1–6 KP_U1..U6, 7–10 KP_D1..D4 ✓; both MP shells carry **no net** — see §7 O5 |
| J_RH_AMBIENT, J_RH_EXHAUST | SM05B-GHS-TB | 7×2 = 14 | JST `eGH.pdf` p.1/p.3 | **PASS** | 1 3V3_SW_RHx, 2 GND, 3 SDA_A, 4 SCL_A, 5 SHIELD_DRAIN; MP on GND ✓ |
| J_ESTOP | SM03B-SRSS-TB | 5 | JST `eSH.pdf` p.1/p.3 | **PASS** | 1 GND, 2 3V3, 3 ESTOP_RAW_IN. Loop-closed = 3V3 through R_ESTOPPD 470 Ω; open = 0 V → fail-safe ✓ |
| J_MODE | S4B-ZR-SM4A-TF | 6 | JST `eZH.pdf` p.1/p.4 | **PASS** | 1 3V3, 2 MODE_RAW, 3 KEY_RELAY_ALLOWED, 4 COIL_EN_IN; MP on GND ✓ |
| J_LOADCELL | B5B-XH-A | 5 | stock KiCad `JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical`, 2.50 mm pitch verified | **PASS** | 1 5V_PROTECTED, 2 3V3, 3 GND, 4 LC_DAT, 5 LC_CLK; series R_LCDAT/R_LCCLK 33 Ω + PESD clamps ✓ |
| J_PWR | 43650-0224 | 2 + 2 MP | INHERITED — stock KiCad `Molex_Micro-Fit_3.0_43650-0224_...`, whose `descr` cites Molex SD-436500224 | **PASS (INHERITED)** | pad1 = 5V_IN (west), pad2 = GND, both MP tabs on GND. See §5.5 — the part.yaml itself records the Molex PDF fetch as blocked. |
| J_ISOLOOP | KF350-3.5-4P | 4 | vendored `TerminalBlock_KF350_4P.kicad_mod`, 3.50 mm pitch verified from pad centres (−5.25/−1.75/+1.75/+5.25) | **PASS** | 1 CONTACTOR_C, 2+3 CONTACTOR_LOOP (a deliberate shorted pair), 4 CONTACTOR_E |
| R_* (87), C_* (58), F1, FB1 | assorted | 2 each | n/a — non-polar 2-terminal | **PASS** | every pad's net read; no orientation-sensitive assignment exists. 56 of 59 caps are rail↔GND; the 3 that are not are exactly the intended ones (C_TCD across TC_POS/TC_NEG, C_OS and C_OS2 across the one-shot CX/CXRX pairs). |
| TP_* (17), H1–H4 | test point / M2.5 hole | 1 each | n/a | **PASS** | 17 test points all on meaningful nets; 4 mounting holes carry no net (isolated) |

---

## 5. The judgement calls, spelled out

### 5.1 The two P-FET orientations are deliberately different — and both are correct

This is the one place a reviewer could easily mis-call a PASS as a FAIL. **MEASURED** from the
board:

- `Q_REV` (reverse-polarity blocker): pad 2 (**source**) = `5V_RPP` (load side),
  pad 3 (**drain**) = `5V_FUSED` (supply side).
- `Q_SWA`/`Q_SWB`/`Q_SWRHA`/`Q_SWRHE` (load switches): pad 2 (**source**) = `3V3` (supply
  side), pad 3 (**drain**) = `3V3_SW_x` (load side).

These are opposite, and each is right for its job. A P-channel body diode conducts
drain→source. For reverse-polarity protection the body diode must point *with* normal
current, so **drain = supply** — which is what `Q_REV` does; on a reversed input the body
diode is reverse-biased and Vgs collapses to 0. For a load switch the body diode must point
*against* normal current so the load is not back-fed when the FET is off, so **source =
supply** — which is what the four `Q_SW*` do. Getting these the same way round would have
been the error; the board distinguishes them.

**On the pin-number↔function map for the SOT-23 FETs.** The AO3401A datasheet figure (p.1)
is a pictorial with **no pin numbers** — it shows only that D is the lone pin and G, S the
pair. So the map "1 = G, 2 = S, 3 = D" is **INHERITED** from the JEDEC TO-236AB convention.
It is however corroborated by the board's own topology, independently of any library: on all
six P-FETs a **100 kΩ** resistor runs from pad 1 to the rail on pad 2 (`R_HSG`
HS_GATE_COIL→5V_PROTECTED; `R_SWPUA/B/RHA/RHE` SWG_x→3V3). A 100 kΩ from pad 1 to pad 2's
rail is a gate bias if pad 1 is the gate, and a pointless resistor bridging two identical
rails otherwise. The same argument holds on the N-FETs (pad 2 = GND with pad 1 driven by a
logic net through a pulldown). Graded **PASS**.

### 5.2 J_PI — mirror check on a 2×20 socket

`PinSocket_*` footprints number pin 2 at **−x** (unlike `PinHeader_*`, which uses +x); this is
the KiCad library convention for a female socket and it is the classic place a Pi HAT gets
mirrored. **MEASURED**: the stock library file
`/usr/share/kicad/footprints/Connector_PinSocket_2.54mm.pretty/PinSocket_2x20_P2.54mm_Vertical.kicad_mod`
has pad 1 at (0, 0) and pad 2 at (−2.54, 0), and the board's placement reproduces this exactly
— the footprint is used **unmodified**.

The conclusive evidence is behavioural, not conventional. Against the Raspberry Pi 40-pin
standard:

- All **eight** Pi ground pins — 6, 9, 14, 20, 25, 30, 34, 39 — are on `GND`. Every one.
- All four Pi power pins — 1 and 17 (3V3), 2 and 4 (5V) — are **unconnected**, so the board
  never back-feeds the Pi.
- SPI0 lands exactly: 19 = MOSI (GPIO10), 21 = MISO (GPIO9), 23 = SCLK (GPIO11),
  24 = ADC_CS_N (GPIO8 / CE0), 26 = TC_CS_N (GPIO7 / CE1).
- I²C0/1 lands exactly: 3 = SDA (GPIO2), 5 = SCL (GPIO3).
- 27/28 (ID_SD / ID_SC) correctly left free.

Under an odd/even mirror the GND set would move to 5, 10, 13, 19, 26, 29, 33, 40 — which would
put GND on the MOSI pin. It does not. **PASS.**

### 5.3 J_TC (Omega PCC-SMP-K) — land PASS, contact polarity QUESTION

**What is MEASURED and correct.** Omega PCC-OST-SMP spec sheet, **p.2**, *"PCC-SMP Drawing"*,
left sub-drawing *"PCC-SMP, Miniature Connector"*, rendered at 200 and 600 dpi. Every land
dimension matches the vendored footprint:

| drawing | footprint `Omega_PCC-SMP-K_TypeK_PCpin.kicad_mod` |
|---|---|
| ø1.77 (0.070), **4 PLACES** | 2 contact pads drill 1.77 + 2 NPTH drill 1.77 ✓ |
| contact span **7.9** (0.31) | pads at ±3.960 → 7.920 ✓ |
| bracket span **15.7** (0.62) | NPTH at ±7.850 → 15.700 ✓ |
| bracket row offset **6.8** (0.27) | NPTH at y = −6.800 ✓ |

The mating face therefore opens toward +y (south), and the board's south edge is at
y = 102.05 with J_TC at y = 96.0 — the plug inserts from off-board. Mechanically correct.

**What is NOT established.** Both contact holes are ø1.77 and identical; the footprint cannot
key polarity, so which hole receives the chromel (+) contact is fixed solely by the
connector's single possible orientation (bracket to the north). The footprint asserts pad 1
(west) is + via an `fp_text "+"` on F.SilkS at (−6.2, 0), and the board wires pad 1 to
`TC_POS_IN` and pad 2 to `TC_NEG_IN`. **I could not verify that assertion.**

I did establish, and will record, the following genuine sub-findings:

- The drawing's `⊖` / `⊕` marks appear only in the **free-part** projection (upper row of the
  sheet), where the two contacts are drawn stacked vertically: `⊖` upper, `⊕` lower.
- That labelling is internally consistent and I cross-checked it: in the mating-face front
  view (rendered at 600 dpi) the **upper** cavity's contact slot is visibly **taller** than the
  lower one, i.e. it takes the **wider blade** — and per the ANSI miniature-thermocouple
  standard the wider blade is the **negative**. Upper = wider = `⊖`. The marks are right.
- The mapping to the board is the missing link. My first pass treated the middle sub-drawing
  as a plan view and derived `⊕ → east` (i.e. the *opposite* of what the board has). I then
  discarded that derivation: under third-angle projection the view placed to the **right** of
  the front view is the right-**side** view, not the top view, and the sheet's mounted-
  orientation views (the side elevation and the isometric) carry no `⊕`/`⊖` at all. The
  handedness that would settle east-vs-west is simply not on the sheet.
- Two external CAD sources (SnapEDA, componentsearchengine) returned **HTTP 403**; targeted
  searches surfaced only the same Omega sheet.

**Why this is a QUESTION and not a FAIL:** I have no positive evidence the assignment is
wrong — only that it is unverified, and the protocol is explicit that unverified is a
QUESTION. **Blast radius, traced on the board:** `TC_POS`/`TC_NEG` reach only `U_TC`
(MAX31856) and its RC network. `TEMP_OK`, the hardware safety input, is generated by the
`U_COMP`/`U_COMP2` LMV393 window comparators on the `TH_CAM_A`/`TH_CAM_B` **thermistor**
channels — **not** by the thermocouple. `TC_FAULT_N` goes only to `U_EXP` GPB6 as a status
bit. A reversed jack is therefore a **measurement** defect (the Pi reads temperature falling
as the process heats; MAX31856 open-circuit detection would still pass, because the loop is
intact) and is **not in the safety interlock chain**.

**Owed at the mandatory bench hour, one line:** plug a K-probe into J_TC, warm it by hand, and
confirm the MAX31856 reading **rises**. If it falls, the jack is reversed — a 2-wire rework at
J_TC / R_TCP / R_TCN, with no copper change.

### 5.4 A scoping correction to my brief

My brief described `J_THERM_A` / `J_THERM_B` as "the K-type connectors". **They are not.**
MEASURED from the board: they are 8-way JST GH pods carrying `3V3_SW_x`, `GND`, `SDA_x`,
`SCL_x`, `TH_CAM_x`, `TH_MOUNT_x`, `TH_PORT_x`, `SHIELD_DRAIN` — switched-rail thermistor /
I²C sensor pods. **`J_TC` (Omega PCC-SMP-K) is the sole K-thermocouple connector on the
board.** I reviewed both, but flag the mismatch because `J_TC` is also the one part the
orchestrator's dossier generator silently skipped (empty MPN column in `bom_jlc.csv`), so a
reviewer following the brief literally could have missed the only thermocouple jack on the
board.

The thermistor front end itself checks out and is worth one measured note, since it *is* the
safety path: `R_REFn` 10 kΩ pull-ups to `3V3_ANALOG`, `R_CLMPA`/`R_CLMPB` 22 kΩ to GND on the
two interlock channels. With a pod **unplugged**, TH_CAM = 3.3 × 22/(10+22) = **2.27 V**,
which is above TCAM_OPEN = 3.3 × 100/162 = **2.04 V**, so `U_COMP2` pulls `TEMP_OK` low and a
missing sensor reads as not-OK. Fail-safe, and the numbers actually work.

### 5.5 J_PWR — graded INHERITED, and honestly so

The `Molex_Micro-Fit_3.0_43650-0224_1x02-1MP_P3.00mm_Vertical` footprint is the **stock**
KiCad library part, used unmodified (MEASURED: board pads at x = 20.5 / 23.5 about a 22.0
centre → ±1.5, MP at ±5.385 — identical to the library file), and its `descr` cites the Molex
SD-436500224 drawing. Which circuit Molex calls "1" is therefore **INHERITED** from the KiCad
library; I could not re-verify it (molex.com fetch timed out, and the part.yaml itself records
"PENDING Molex SD-436500224 figure confirmation at bring-up (PDF fetch blocked)").

I am comfortable grading this PASS rather than QUESTION because the consequence is bounded by
design: a reversed input cable meets `F1` (PPTC) → `D_REVCLAMP` (SS34, cathode on 5V_FUSED,
MEASURED §3) → `Q_REV` (P-FET, drain = supply, MEASURED §5.1). The board does not power up and
nothing downstream sees reverse voltage. Still worth confirming at the bench hour with a meter
on TP_5VP before first power-on.

---

## 6. Coverage

**Population denominator: 243 footprints on `cooksense.kicad_pcb`** (counted from `pcbnew`).

| class | count | checked | how |
|---|---|---|---|
| Reed relays `K_*` | 12 | **12** | datasheet figure, pad by pad (§2) |
| ICs `U_*` | 30 | **30** | datasheet figure / pin table per MPN (§4) |
| Connectors `J_*` | 12 | **12** | incl. `J_TC`, which needed a second `--refs` run |
| MOSFETs `Q_*` | 12 | **12** | §5.1 |
| Diodes `D_*` | 8 | **8** | footprint F.Fab polarity + part type (§3) |
| Polarized electrolytic `CE1` | 1 | **1** | §3 |
| **orientation-bearing subtotal** | **75** | **75** | **75 / 75 = 100 %** |
| Resistors `R_*` | 87 | 87 | non-polar; both nets read |
| Ceramic caps `C_*` | 58 | 58 | non-polar; both nets read |
| `F1`, `FB1` | 2 | 2 | non-polar 2-terminal |
| Test points `TP_*` | 17 | 17 | single pad |
| Mounting holes `H1–H4` | 4 | 4 | single pad, no net |
| **total** | **243** | **243** | **243 / 243 = 100 %** |

Pins individually judged against a datasheet-derived expectation: **≈420** across the 75
orientation-bearing parts.

**Datasheet-evidence grade by distinct MPN** (16 orientation-bearing MPNs + connectors):

- **MEASURED from a figure/pin-table I read myself (14):** DIP05-1A72-13L, SN74LVC1G11DBVR,
  SN74LVC1G00DCKR, SN74HC595DR, SN74HC238DR, SN74HC14DR, CD74HC221M96, LMV393IDR,
  MCP3208-CI-SL, MCP23017-E/SS, TPS259573DSGR, TPS3823-33DBVR, TBD62083AFWG, PESD5V0S1BA.
- **MEASURED for land geometry, polarity unresolved (1):** PCC-SMP-K.
- **SECONDARY web read, no cached PDF (1):** MAX31856MUD+T.
- **INHERITED from convention, corroborated by board topology (5):** AO3401A / 2N7002
  (number↔function map), AMS1117-3.3, LTV-817S-TA1, SS34, SMBJ5.0A.
- **INHERITED from the stock KiCad library, unmodified (connectors):** all JST parts, Molex
  43650-0224, PinSocket 2×20, B5B-XH-A — each verified byte-for-byte against the system
  library and each with its pad-1 coordinate confirmed against the board.

### Named gaps — every part I could NOT fully check, and why

1. **`J_TC` — PCC-SMP-K (Omega).** Contact `+`/`−` assignment not determinable from the
   cached spec sheet (the `⊕`/`⊖` marks live only in a free-part projection whose handedness
   relative to the mounted orientation the sheet does not fix). SnapEDA and
   componentsearchengine both returned HTTP 403. **QUESTION**, bench-checkable in seconds, not
   in the safety chain. §5.3.
2. **`U_TC` — MAX31856MUD+T.** No PDF cached under `02_parts/MAX31856MUD+T/` (the folder
   holds only `part.yaml`). Two direct fetches of the analog.com datasheet timed out; the
   14-pin list is a **secondary** web read, not a figure I rendered. All 14 board nets agree
   with it, including DNC (pin 6) correctly left open. Caching that PDF would close the gap.
3. **`J_PWR` — Molex 43650-0224.** No vendor drawing cached; circuit-1 identification
   INHERITED from the stock KiCad footprint. §5.5.
4. **`Q_*` SOT-23 FETs — 2N7002 / AO3401A.** The AO3401A pictorial carries no pin numbers and
   no 2N7002 PDF is cached; the 1/2/3 ↔ G/S/D map is JEDEC convention, corroborated by the
   board's own gate-bias resistors. §5.1.
5. **`U_LDO` AMS1117-3.3, `U_OPTO` LTV-817S-TA1, `D_KSTOP`/`D_REVCLAMP` SS34, `D_TVS`
   SMBJ5.0A.** No PDFs cached in `02_parts/`; pin maps from convention. For the three diodes
   the *footprint* polarity was MEASURED from library geometry, so only the part-level
   convention (SS34 = plain 2-terminal Schottky; SMBJ`A` = unidirectional) is inherited.
6. **`J_ISOLOOP` KF350-3.5-4P.** No vendor drawing cached; pitch (3.50 mm) verified from the
   vendored footprint's pad centres. A 4-way terminal block has no polarity to get wrong.

---

## 7. Observations that are not pin failures

**O1 — `U_ULNB` inputs I5–I8 (pins 5–8) float.** Pin 4 (I4) *is* tied to GND, so the
inconsistency is visible on its face. Outputs O5–O8 (pins 11–14) are unconnected, so nothing
downstream can be driven and the effect is benign; but four floating DMOS gate inputs on a
part whose datasheet specifies V_IN(off) ≤ 0.6 V is untidy and costs one tie-off each.

**O2 — `EXP_INTB` is a single-node net** (`U_EXP` pin 19 = INTB, MCP23017). Measured: it is
the only named net on the board with exactly one pad. INTA (pin 20) carries the interrupt to
the Pi as `INT_ALERT`, so INTB is genuinely spare; it should be an explicit no-connect rather
than a named dangling net.

**O3 — out of lens, but read off the same datasheet page while doing the relay work.** The
Standex DIP series *Relay Data* table, **p.3**, gives **Operating Temperature (max) −20 to
+70 °C**, qualified as *"Surrounding of the relay's housing"*. The declared operating ambient
under review is 65 °C. That is 5 K of headroom at the relay housing **before** any self-heating
from twelve 50 mW coils in a row on 15.2 mm centres. I raise it only because it is the same
number the re-gate is about; it is not a pin finding and I make no claim about whether the
thermal work already covers it.

**O4 — out of lens.** `D_TVS` is `SMBJ5.0A`, V_RWM = 5.0 V, standing off a nominally 5.0 V
rail. Correct polarity (§3), but the standoff sits at the rail with no margin. Topology, not
pins.

**O5 — `J_KEY_MATRIX` shell tabs carry no net**, whereas the shells of `J_THERM_A/B`,
`J_RH_AMBIENT/EXHAUST`, `J_ESTOP`, `J_MODE` and `J_PWR` are all on GND. On the one connector
that intercepts the appliance's own keypad ribbon, a floating shell is a plausible deliberate
choice (no ground loop into the appliance). Noted so that it is a decision on the record
rather than an oversight.

**O6 — cosmetic, `part.yaml` only.** `SN74HC14DR` pin 12 is labelled `6A_Y` in the part.yaml
function column; the datasheet name is `6Y` and the board net (unconnected output) is correct.
No board impact.

---

## 8. Verdict

Zero pin FAILs across 243/243 footprints and 75/75 orientation-bearing parts. The relay land
that made six sealed releases DO-NOT-ORDER is now **span-keyed and correct against the `-13`
figure**, and the option-L "no coil diode" reading is backed by the p.4 option figures and by
the fact that all twelve coils have an external clamp. The polarized 2-pad class was audited
against footprint graphics, not against the netlist, and five of the eight diodes turn out to
be bidirectional parts with no polarity to get wrong. The Pi header is not mirrored. The two
P-FET orientations differ on purpose and both are right.

One QUESTION stands — the `J_TC` thermocouple-jack contact polarity — which is unverifiable
from the cached vendor sheet, is outside the hardware safety chain, and is a one-line check at
the mandatory bench hour.

```
design_verdict: SOUND
order_verdict:  BLOCKED-SOURCING
```

`order_verdict` reflects **only** `C265111` (JST SM08B-GHS-TB, stock 5 / minPurchaseNum 21).
It is the sole order-side objection from this lens, and it did not enter `design_verdict`.

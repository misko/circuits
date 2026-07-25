# ORDER README — usb-hub-3s-v3 **v1.5** (internal board name `usb_hub_3s_v2`)

3S-LiPo powered power-distribution board: XT60 pack in → 10 A MINI-blade fuse →
dual synchronous bucks (LM5116) → 3× USB-A (5 V charging, no-data) + 1×
Pi-dedicated USB-C (5 V/5 A, **discrete-protected**). **NOT a USB hub, NOT USB-PD.**
Release **v1.5-2026-07-25**. Board **130.1 × 92.1 mm**, **4 layer**, **110 parts**.

> ## ⛔ v1.4 AND EVERY EARLIER RELEASE ARE **DO-NOT-ORDER**
>
> Sealed v1.4 places **C1 and C2 — 100 µF / 35 V POLARIZED polymer
> electrolytics — at CPL 270.0 where the measured correct value is 90.0.**
> That is **180° reversed, directly across the 9.0-12.6 V 3S LiPo input**.
> A reverse-biased polymer electrolytic on a near-zero-impedance pack heats,
> gasses and **vents**, at first power-up, before any bench gate below can run.
> Full evidence: `08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md` (PCBA-1).
>
> **Order from THIS directory.** v1.4 carries a `SUPERSEDED.md` pointing here.

**v1.5 is a CPL-CORRECTION supersede of v1.4-2026-07-23, plus order paperwork.**
The copper is not touched: `fab/*_gerbers.zip`, both drill files, all of `pdf/`,
`source/` and `3d/` are **sha256-IDENTICAL to v1.4** (20 files, verified in the
MANIFEST). What changed:

- **`fab/cpl.csv` — exactly four cells**, and nothing else:
  `C1 270.0→90.0`, `C2 270.0→90.0`, `Q7 270.0→180.0`, `J1 90.0→0.0`.
- **`fab/bom.csv`** — identical to v1.4 row-for-row except the **MPN column is
  now populated on all 43 lines** (it was empty; that is what leaves JLC's
  matcher at "No Part Selected").
- Order paperwork: the **ORDER-PREVIEW HUMAN GATE** below (v1.4 never mentioned
  the preview at all, while 12 twin findings are waived on exactly that gate),
  assembly side, build quantity, through-hole declaration, stack-up/finish,
  panel-rail policy, and a stock table sorted by how close each line is to
  running out.

---

## ⚠️ ORDER-PREVIEW HUMAN GATE — DO THIS BEFORE YOU PAY

**Why this section exists.** Twelve `jlc_twin` findings on this board are
dispositioned "verify on the JLC order preview" — and until v1.5 the order
paperwork did not mention the preview once. **C1/C2, the parts that killed
v1.4, are on that list.** The preview is not a formality; it is the last gate
between a CPL number and a vented capacitor.

Open JLC's assembly preview (3D + the per-part rotation view) and check each
row. **Colour semantics:** white = your silkscreen; **magenta glyphs = JLC's
own model's pin-1 / polarity markers**. A missing body = no 3D model (the part
still mounts — check the BOM tab, not the render).

| # | Check | What you must see | REJECT if |
|---|---|---|---|
| **P1** | **C1, C2 — polarity. THE ONE THAT MATTERS.** 100 µF/35 V polymer at the board's west edge, beside F1/Q1. | The **“+” / pin-1 end pointing at the VIN (fuse/Q1) side** — i.e. toward the F1 fuse holder, AWAY from the ground pour edge. Our silk marks “+”; JLC's own model silk draws a crossed “+” glyph over its pad 1 and a bar “−” over pad 2 — **the two must agree.** CPL must read **90.0**. | The “+” faces the wrong way, or the CPL cell reads 270.0. **STOP THE ORDER.** This is the v1.4 defect. |
| **P2** | **J1 — XT60 polarity. MANDATORY, NOT OPTIONAL.** | **Pad 1 is the NEGATIVE (−) blade** (`02_parts/XT60PW-M/part.yaml`: "PAD 1 IS NEGATIVE — polarity is a PART FACT"), and pad 1 is the hole on the **GND** net. CPL must read **0.0**. | Anything else. **A reversed XT60 has shipped from this fleet before.** The ROTATION is settled by geometry — the two anchor holes sit 6.0 mm off the blade axis, so the 4-pad fit lands rms 0.0000 mm at one angle and 12.0 mm out at the other, with no reliance on pad numbering. What geometry **cannot** tell you is which blade is “+”. That is a PART FACT and only a human can confirm it against the connector in front of them. |
| **P3** | **D1 (SMBJ15A, input TVS) and D5 (SMBJ6.0A, VBUS TVS) — cathode direction.** | D1 **cathode (pad 1, banded end) on VIN**, anode to GND. D5 **cathode (pad 1) on VBUSC**, anode to GND. Both are D_SMB bodies; the band on JLC's model must line up with the band on our silk. | Band reversed on either. A backwards TVS is a permanent short across the rail it is meant to protect. |
| **P4** | **L1, L2 (Sunlord MWSA1206S-6R8) — seating.** | Both molded inductors square on their end-cap lands beside the SW nodes. `jlc_twin` records a **0.75 mm land-extent difference** (ours vs EasyEDA) on a 12.5 mm body — adjudicated as a land-extent preference, same copper. | The body sits off the pads by more than the pad overhang, or is rotated 90°. Non-polarized, so orientation is cosmetic — **seating is not**. |
| **P5** | **R12 (4.12 kΩ 0.1 %, buck-C FB top) — the part is REALLY C2984354.** | BOM line `4.12kΩ / R12 / AR03BTCX4121 / C2984354` matched and priced. `jlc_twin` reports **FETCH-FAILED** for this code (EasyEDA API 404, probed directly — the part is genuinely absent from their CAD library, not a transient), so there is no model to compare; the BOM line is the check. | JLC substitutes anything. **NEVER accept C2933210 (3.74 kΩ)** — that is the v1.2 undervoltage bug. Verified alternate: **C861436**. |
| **P6** | **SW1 — do NOT let JLC place it.** | SW1 flagged **DNP / not placed** (see §1). Its pitch is unconfirmed (JLC's model is the wrong VG4 variant). | JLC "helpfully" adds placement data for SW1 or F1. |
| **P7** | **Rotation sweep, everything else.** | The 4 corrected cells read **C1 90.0, C2 90.0, Q7 180.0, J1 0.0**. Every polarized 2-pad part (D2, D3, D4 as well as D1/D5/C1/C2) shows its magenta pin-1 marker on the same end as our silk. | Any mismatch. `jlc_twin` returned **0 ROT-DB-SUGGEST** over 231 checks, so a preview disagreement means the preview is telling you something new — investigate, do not rationalize. |

**THT preview offsets are cosmetic** (the holes constrain assembly), **but THT
ROTATION is a real operator instruction** — J1-J4 rotations still matter.
**SMD preview rotation is exactly what the machine does** — fix it, don't
rationalize it.

---

## 1. JLCPCB order options — the full declaration

| Setting | Value | Why |
|---|---|---|
| **Layers** | **4** | GND + VIN planes |
| **Dimensions** | **130.1 × 92.1 mm** | |
| **Board thickness** | **1.6 mm** | The THT connectors (XT60 J1, USB-A J2-J4) and their edge-trim footprints assume a 1.6 mm board; changing it changes the lead engagement. |
| **Outer copper weight** | **1 oz** | JLC 4-layer standard (1 oz outer / 0.5 oz inner). The ampacity floors in `03_src/rules/nets.yaml` were generated against `fab_tier: jlc_4layer_standard`; a lighter copper invalidates them. |
| **Via tier** | **`jlc_4layer_standard`** — 0.45 mm pad / 0.30 mm drill | Standard process is sufficient — **do NOT select the advanced small-via option** (nothing on this board needs it since the PD cell was removed). |
| **Surface finish** | **ENIG** *(recommended)*; lead-free HASL acceptable | Three VSON-8 exposed pads (U3/U4/U5) and two HTSSOP-20 exposed pads (U2/U11) at 0.65 mm pitch. HASL's surface unevenness is worst exactly under large exposed pads, and this is a PCBA order where rework costs more than the finish upgrade. |
| **Solder mask / silkscreen** | **Green / white** | No lead-time penalty; the assembly drawings assume white-on-green legibility. |
| **Assembly side** | **TOP ONLY** | **MEASURED**: 108/108 CPL rows are `top`; the board carries **zero** bottom-side footprints. One reflow pass, no bottom-side cost line. |
| **Build quantity** | **5 boards** | User decision 2026-07-25. Stock is graded at 5 × per-board qty throughout (§3). |
| **Through-hole assembly** | **REQUIRED** | See the THT declaration immediately below. |
| **Assembly files** | BOM `fab/bom.csv` + CPL `fab/cpl.csv` (JLC-upload format, per-refdes LCSC keyed off `circuit.json`) | |

### 1a. THROUGH-HOLE ASSEMBLY — declare it explicitly

**Through-hole assembly REQUIRED — 4 refdes / 22 holes: J1-J4.**

Measured plated-hole census on the sealed board (2026-07-25):

| ref | part | plated holes | note |
|---|---|---|---|
| **J1** | AMASS XT60PW-M battery input | **4** | 2 × 2.7 mm blade + 2 × 0.6 mm anchor |
| **J2** | KH-AF90DIP-112 USB-A | **6** | 4 × 1.0 mm signal + 2 × 3.0 mm shell |
| **J3** | KH-AF90DIP-112 USB-A | **6** | |
| **J4** | KH-AF90DIP-112 USB-A | **6** | |
| | | **22 total** | **these four STAY ON THE CPL** |

**Also tell the fab about J5.** `J5` (TYPE-C-31-M-12A) is a **hybrid**: 16 SMD
contacts **plus 4 × 0.6 mm PTH shield legs** and 2 × 0.65 mm NPTH alignment
posts. It is counted as SMD on the CPL, but **the four shield legs need
soldering** — call it out so the hybrid is not missed.

**NOT machine-assembled** (hand-fitted after delivery, §2): F1 (4 PTH), SW1
(3 PTH + 2 NPTH).

### 1b. PANEL / RAIL POLICY — read this before JLC panelizes

**Submit SINGLE BOARDS. Do NOT submit a customer panel.** JLC will add its own
process rails for SMT assembly (its own fiducials go on those rails — this
board deliberately places **no** fiducials of its own; the smallest
centre-to-centre distance between two distinct pads anywhere on the board is a
**measured 0.500 mm** — J5's USB-C CC/SBU region, pads A5↔B7 — above the
≤0.4 mm pitch that would demand local fiducials. Next finest: 0.600 mm at the
VSON-8s U3/U4/U5.)

**BUT: three of the four edges cannot take a rail.** Measured clearance from
each board edge to the nearest CPL part's extent (2026-07-25):

| edge | nearest placed part | clearance | rail? |
|---|---|---|---|
| **west** (nearest J1) | J1 | **−6.82 mm** (overhangs) | ❌ **NO** |
| **east** (nearest J2-J4) | J4 | **−4.29 mm** (overhangs) | ❌ **NO** |
| **south** (nearest J5 / USB-C) | J5 | **−2.90 mm** (overhangs) | ❌ **NO** |
| **north** — the edge **OPPOSITE the USB-C connector**, nearest H1/H3 and the C9-C13 input-cap row | C12 | **+1.43 mm** | ✅ **the only usable edge** |

The three edge-mount connectors physically **overhang the board outline** (that
is what the `_EdgeTrim` footprints are for). **A rail on the west, east or
south edge would run straight through a connector body.** If JLC's process
needs a rail, it must go on the north edge only; if the process requires two
opposite rails, **contact them rather than letting the panel be generated
automatically.**

### 1c. EXPECT 2 UNMATCHED DESIGNATORS AT UPLOAD — this is intentional

`fab/bom.csv` carries **F1** (C5249699) and **SW1** (C2939728) but
`fab/cpl.csv` deliberately omits both (`FP_EXCLUDE_FROM_POS_FILES` at source,
declared in `03_src/rules/assembly.yaml`). In the JLC order review, **mark F1
and SW1 as DNP / "do not place"**. The codes stay on the BOM so the parts
arrive with the order for hand fitting.

**Re-uploading the BOM resets part matching AND Do-Not-Place marks**; CPL
re-upload only redoes placements. Sequence your edits accordingly.

---

## 2. Hand-solder / off-CPL list + purchasing

| Ref | Part | Why off-CPL |
|---|---|---|
| **F1** | **Keystone 3568 MINI-blade fuse HOLDER (C5249699)** | THT holder with **no JLC placement model** (`jlc_twin` `best=none`, re-confirmed 2026-07-25) — there is nothing to verify a machine placement against. **Next-revision item:** now that THT assembly is being ordered, F1 belongs on the CPL; that needs a board change and v1.5 is a no-copper-change release (audit PCBA-6). |
| **SW1** | SS12D07 master-off slide (C2939728) | **Pin pitch unconfirmed.** Our land is the standard SS-12D07 **2.5 mm** signal pitch (5.00 mm span); JLC's own model file is named `SW-TH_SS12D07VG4` — the **VG4** variant at **2.0 mm** (4.00 mm span), a mislabelled wrong-variant model, and the VG6-087 drawing was un-fetchable (LCSC CDN blocked). Machine-placing a 2.0 mm part on a 2.5 mm land is a placement defect. **Hand-solder after physically confirming the received part's pitch against the pads.** **Fallback if the pitch is wrong:** fit a 2.54 mm 3-pin header + shunt on the same land — **COM-T1 shunted = OFF; shunt removed = ON** (COM = pin 2 = ENKILL, T1 = pin 1 = GND; shunting grounds ENKILL, which shuts BOTH bucks down and opens Q6). Verify by continuity per gate Q6. |

**Hand-fit purchasing list (NOT in the JLC order):**

- 1× **10 A MINI (ATM) blade fuse** — the consumable element for F1
  (deliberately off-BOM; buy locally, keep spares).
- (fallback only) 1× 2.54 mm 3-pin header + 1× shunt/jumper for the SW1 land.

---

## 3. STOCK — sorted by how close each line is to running out

**Re-run `jlc_stock_check` on order day.** Measured **2026-07-25**, at
`--min-stock 5` (i.e. stock ≥ 5 boards × per-board qty): **PASS — 43/43 coded
lines OK, 0 uncoded** (`verification/stock_check.txt` / `.json`).

**Basic / Extended split: 12 Basic / 31 Extended** of 43 lines. Each Extended
reel carries a per-reel setup fee, so budget **~31 feeder setups** — this is
the largest single line item after the parts themselves, and it is stated here
so it is priced **before** the order rather than discovered at checkout.

**`boards` = `floor(stock / per-board qty)` = how many boards that line can
build today.** Tightest first:

| boards | LCSC | MPN | qty/bd | stock | tier | refs | named alternate |
|---:|---|---|---:|---:|---|---|---|
| **37** | **C473910** | TPS2513ADBVR | 2 | **75** | ext | U6, U7 | **C44770** — the non-A TPS2513 (**no** Apple 2.4 A divider mode). Substituting DEGRADES Apple-device charge rate; acceptable, not equivalent. |
| **90** | **C5337088** | TYPE-C-31-M-12A | 1 | **90** | ext | J5 | **none qualified.** Any substitute changes the footprint — a re-spin, not a swap. Recheck on order day; if short, buy the shortfall separately and consign. |
| 225 | C408523 | MWSA1206S-6R8MT | 2 | 450 | ext | L1, L2 | **C408515** (same MWSA1206S series) |
| 664 | C22865 | 0603WAF1242T5E (12.4 k) | 2 | 1329 | ext | R2, R11 | any 12.4 k 1 % 0603 (R_T; sets f_SW — 1 % matters, the exact MPN does not) |
| 711 | C728591 | RT0603BRD073K92L (3.92 k 0.1 %) | 1 | 711 | ext | R3 | **C861384** = RT0603BRD073K83L (3.83 k 0.1 %) — **shifts 5VA to 5.062 V**; still in the USB-A window, re-check before accepting |
| 1203 | C404363 | AON6354 | 4 | 4815 | ext | Q2-Q5 | **C51908846** |
| 1204 | C2760089 | AON6403 | 2 | 2409 | ext | Q1, Q6 | **none qualified** — single-source; qualify one before any volume order |
| 1213 | C5249699 | Keystone 3568 | 1 | 1213 | ext | F1 | none qualified (hand-fit part) |
| 2176 | C98732 | XT60PW-M | 1 | 2176 | ext | J1 | none qualified |
| 2439 | C130056 | TPS2557DRBR | 3 | 7319 | ext | U3-U5 | **C2150199** |
| 3329 | **C6165170** | SMD2920-700/16N (7 A PPTC) | 1 | 3329 | ext | F2 | **C3762416** (Littelfuse 2920L600/16MR-A, 6 A) — **DEGRADED**: a 6 A hold derates to ~4.8 A @50 °C, below the 5 A load. User decision required. |
| 3997 | C13755 | LM5116MHX/NOPB | 2 | 7995 | ext | U2, U11 | **C1519427** |
| 4204 | C503996 | KH-AF90DIP-112 | 3 | 12612 | ext | J2-J4 | none qualified (footprint-specific) |
| 5211 | C84455 | GRM32ER61A107ME20L | 8 | 41692 | ext | C14-C17, C29-C32 | **C97170** (Samsung CL32A107MQVNNNE) |
| 5364 | C7519 | USBLC6-2SC6 | 4 | 21459 | ext | U8-U10, U12 | **C2687116** |
| 10862 | **C2982822** | KNM2100UF35V149EC0055 | 2 | 21724 | ext | **C1, C2** | none qualified — **and any substitute must be re-checked for pad-1 polarity before its CPL rotation is trusted** (audit PCBA-1) |
| 15245 | **C2984354** | AR03BTCX4121 (4.12 k 0.1 %) | 1 | 15245 | ext | R12 | **C861436** (Yageo RT0603BRD074K12L, same 4.12 k/0.1 %/25 ppm). **NEVER C2933210 (3.74 k).** |
| 74562 | **C113976** | SMBJ6.0A **UNI-directional** | 1 | 74562 | ext | D5 | **C83270**. **NEVER C140903** — JLC lists it BIDIRECTIONAL. |
| — | *(remaining 25 lines)* | | | ≥ 20 977 boards each | 12 base / 13 ext | | library-standard; all pass M-BOM |

**Order-day must-recheck, in priority order: C473910 (37 boards), C5337088
(90), C408523 (225)** — plus the three *correctness* codes that have a
DO-NOT-USE twin: **R12 = C2984354** (never C2933210), **D5 = C113976** (never
C140903), **R30 = C25803** (never C2933195).

---

## ⚠️ DEPLOYMENT GATE — REQUIRED PRE-PI-CONNECTION BENCH QUALIFICATION

**Do not connect a Pi until ALL of these pass.** The board is a supervised
prototype whose over-voltage protection is SECONDARY/best-effort (ADR-0002):
these tests are what stands between an assembly/derivation error and the Pi.

| # | Test | Pass criterion | Reject / action |
|---|---|---|---|
| **Q0** | **Visual + ohmmeter check of R12 AND R30 BEFORE first power.** R12: 0603 next to U11 (buck-C FB-top). R30: 0603 at Q6/Q7 (Q6 gate pull-up to PMID). **Also: eyeball C1/C2 “+” orientation against the assembly drawing** (v1.4's defect — confirm the built board matches the corrected CPL). | R12 reads **~4.12 kΩ**; R30 reads **~100 kΩ** (in-circuit lower is investigable; a clean read passes). C1/C2 “+” toward the F1/Q1 side. | **REJECT if R12 reads ~3.74 kΩ** (v1.2 wrong-part C2933210). **REJECT if R30 reads ~3.09 kΩ** (v1.2 wrong-part C2933195). **REJECT AND DO NOT POWER if either C1 or C2 is reversed.** |
| **Q1** | **No-load static rails — RECORD THE NUMBERS, do not just pass/fail.** Measure and **write down** 5VA, 5VC, **VBUSC and VBUSA1/2/3** at ZERO load before connecting anything. | 5VC within **5.23-5.48 V**; **VBUSC no-load ≤ 5.45 V FIRM CEILING**; 5VA within 5.03-5.28 V. **Record the measured VBUSC and VBUSA values in the build log** — this is the evidence for the accepted U12/U8-U10 derating (MANIFEST waiver W-U12, audit PCBA-4, DETAIL_DESIGN sec.5.3): the USBLC6-2SC6 V_BUS pin's characterized standoff is 5.25 V and the design runs 5.352 V nominal / 5.479 V worst corner on the C rail. | VBUSC above 5.45 V no-load: stop — measure R12/R13 and the FB node before any load testing. **If measured VBUSC exceeds 5.55 V**, the acceptance argument (worst corner 521 mV below U12's 6.0 V V_BR minimum) no longer holds — re-derive before proceeding. |
| **Q2** | **8-24 h at max load on an ELECTRONIC LOAD** — 5 A on USB-C (VBUSC) + 6 A total on the USB-A ports, NOT the Pi | **VBUSC at the board ≥ 5.00 V at 5 A**, stable, no F2 nuisance trip, no thermal runaway | Any trip/droop/drift: diagnose before any Pi contact. |
| **Q3** | **Scope BOTH switch nodes (SW_A, SW_C) at Vin = 12.6 V** during startup, shutdown (SW1), abrupt load steps (0→5 A→0), **and CAPTURE VBUSC during a 5 A→0 A load release** | Ringing within FET ratings, clean monotonic soft-start; **load-release overshoot on VBUSC ≤ 5.45 V** | Overshoot reaching the ceiling: stop; snubber/compensation rework (R34/C53, R35/C54 are fitted by default for exactly this). |
| **Q4** | **Thermal soak at the hottest expected ambient** at full load (IR camera or thermocouples: L1/L2, Q2-Q5, U2/U11, F2, **and the F1 fuse clips**) | Steady-state temps in rating with margin; F2 below trip-derate at 5 A. **F1 note:** the worst-case input trunk is **7.12 A on a 10 A blade = 71 % of rating** (DETAIL_DESIGN sec.6) — watch the clips. | Overheating: derate the load spec or rework before deployment. |
| **Q5** | **Verify VBUSC at the END of the actual USB-C cable** (the very cable that will feed the Pi), at 5 A electronic load, thermally settled (hot) | **≥ 4.80-4.85 V at the cable end, hot**; no undervoltage events during fast load transitions. **This floor is deliberately ABOVE the 4.79 V paper worst case** — that estimate is the quadruple-worst corner (Vref low AND R13 high AND F2 fully hot AND a marginal cable); Q5 is a requirement on the DELIVERED system, not a prediction of it. | Below: use a shorter/better 5 A cable, or apply the documented R12 4.12 k→4.22 k mitigation and re-derive. **Do NOT re-label a sub-4.80 V reading as a pass** on the grounds that the paper corner allows 4.79 V — the E-MARGIN slack behind that corner is only **69 mV**. |
| **Q6** | **SW1 / fallback-header logic by CONTINUITY METER before power, then functionally.** | Continuity COM-T1 (shunt fitted / slide to T1) = ENKILL-to-GND = **both bucks OFF**; open = ON. Functional: with the shunt fitted the rails stay dead; remove it and the rails come up. | Any inversion vs this table: re-check the fitted part orientation against the land before power. |
| **Q7** | **Pi stress test (final, after Q0-Q6):** monitor **`vcgencmd get_throttled`** continuously through the full stress run | `get_throttled` = 0x0 throughout | Any UV/throttle flag: capture VBUSC at the Pi end under the failing load; revisit cable/setpoint per Q5. |

Only after Q0-Q7 pass may a Pi be connected — and it should be a **replaceable**
Pi (supervised-prototype context, BRIEF A3/D3). Escalation boundary (verbatim):
"add active OVP if the system becomes unattended, hard-access, carries valuable
storage, or powers expensive SDR".

---

## ⚠️ TOLERANCE-INCLUSIVE WORST-CASE RAIL TABLE

Full derivation in `01_docs/DETAIL_DESIGN.md` sec.2.11 + sec.4.
`Vout = Vref × (1 + Rtop/Rbot)`:

| Rail | Divider | Nominal | Worst-case MIN | Worst-case MAX |
|---|---|---|---|---|
| **5VC** (buck-C, feeds USB-C) | R12 4.12 k **±0.1 %** (C2984354) / R13 1.21 k **±1 %** (C5126242), Vref 1.215 V **±1.5 %** | **5.352 V** | **5.227 V** | **5.479 V** |
| **5VA** (buck-A, feeds 3× USB-A) | R3 3.92 k **±0.1 %** (C728591) / R4 1.21 k **±1 %** (C5126242), Vref ±1.5 % | **5.151 V** | **5.032 V** | **5.273 V** |

**Low corner (undervoltage) — PASS, and the honest slack is 15 mV:**

    headroom      = 5.227 V - 4.63 V (Pi UV trip)              = 597 mV
    raw IR drop   = 97 mOhm x 5 A                              = 485 mV
      (Q6 4.3 + F2 18 cold / 31 hot + BOARD 12 + conn 5 + cable 45 mOhm)
    E-MARGIN need = raw IR x 1.20 derate (the gate's own rule)  = 582 mV
                                              -> PASS, slack   =  15 mV

**Three numbers have been published for this one margin. Use 15 mV.** Each
revision removed an optimistic assumption; the hardware never changed:

| figure | what it assumed | where it came from |
|---|---|---|
| 157 mV | Vref-only corner, no 1.20 derate, 3 mΩ board | v1.4 paperwork |
| 69 mV | tolerance-inclusive corner + the gate's 1.20 derate, 3 mΩ board | v1.5 first pass |
| **15 mV** | **the same, plus the MEASURED board copper** | **v1.5 layout red-team RL-2** |

The board-copper allowance was a **~3 mΩ estimate** carried since v1.3. The
v1.5 layout/thermal red-team measured it by numerical mesh solve (0.3 mm cells,
F.Cu + B.Cu + vias, solver validated against analytic bars and found to read
10-20 % LOW): **5VC L2→Q6 2.198 mΩ + PMID Q6→F2 4.914 mΩ + VBUSC F2→J5
2.209 mΩ = ≥9.32 mΩ**, true ≈10.4-11.6 mΩ, carried conservatively as **12 mΩ**.
`03_src/rules/power_tree.yaml` is synced to 97 mΩ and E-MARGIN re-run: **PASS**.

Worst-case cable-end estimate is now **5.227 − 0.485 = 4.74 V**, still above
the Pi's 4.63 V ±5 % UV trip but by only ~110 mV.

> **15 mV of paper slack is not a margin you ship on.** Gates **Q2 and Q5
> MEASURE** the delivered voltage at the board and at the far end of the actual
> cable, hot, at 5 A. **That measurement — not this table — is what qualifies
> the board.** If Q5 comes in low, the fix is a shorter/better cable or the
> documented R12 4.12 k → 4.22 k setpoint mitigation.

**High corner (no-load static):** 5VC can statically reach **5.479 V** at the
receptacle. Do NOT accept this on paper; gate Q1 measures it against the
**5.45 V firm ceiling**, and Q3 captures load-release overshoot.
**USB-A note:** the 5VA top corner **5.273 V slightly exceeds the intended
5.25 V USB-A ceiling** (R4 is ±1 %). Accepted for no-data charging ports; a
next-rev option is 0.1 % parts for R13/R4.

**ESD-array derating (ACCEPTED, MEASURED — see Q1):** the USBLC6-2SC6 V_BUS pin
on **U12** (C rail) runs **+102 mV nominal / +229 mV worst corner** above the
5.25 V at which its leakage is characterized; U8/U9/U10 (A rail) reach +23 mV
at their top corner. **5.25 V is not an absolute maximum** — ST's Table 1
carries no V_BUS limit at all, and V_BR is **6.0 V minimum**, which the 5.479 V
worst corner clears by 521 mV. The mode is elevated reverse leakage
(≲4.5 µA hot), not breakdown. **R12 is deliberately NOT changed** — lowering
5VC would spend the Pi undervoltage slack above, which is only **69 mV**. Full record:
`01_docs/DETAIL_DESIGN.md` sec.5.3, MANIFEST waiver **W-U12**.

---

## 3a. ⚠️ BUILD NOTES FROM THE LAYOUT RED-TEAM — act on these at assembly

`08_reviews/2026-07-25_v1.5_redteam_layout.md` (verdict **ORDER**, 0 P0, 5 P1,
7 P2) is the first layout/thermal/power-integrity lens ever run against THIS
copper — the only prior one was written against the v1.0 board, before the
whole discrete VBUS protection chain existed. It found nothing that blocks the
order. It found four things you must know while building and deploying:

| # | What | What to do |
|---|---|---|
| **B1** | **H3 mounting hole bridges the 6 A USB-A rail to GND if you fit a metal screw.** H3 is a 3.20 mm NPTH at (106.0, 24.0); measured radially, **5VA copper starts at r = 1.80 mm and GND copper starts at r = 1.80 mm — on BOTH outer layers.** An M3 screw head or washer spans ~3.0 mm radius and would sit on both, separated by solder mask only. | **Fit a NYLON screw + nylon washer at H3, or leave H3 unfitted.** If a metal fastener is required there, add an insulating shoulder washer. **This is a deployment hazard, not a theoretical one** — mask is not an insulator under clamping force. Next-rev: pull both pours back from H3. |
| **B2** | **The 5 A USB-C path crosses Q6 → F2 through TWO 0.30 mm vias in series, with no redundancy.** PMID's F.Cu pour is bisected by the 0.200 mm QG gate route into two islands (18.28 mm² and 27.30 mm²); removing either via in KiCad's own connectivity engine takes the net from 0 to 1 unconnected. Thermally it is fine (ΔT ≈ 0.85 K) — this is a **reliability and IR** finding. | Nothing to do at order time. Include it in the Q2 8-24 h soak: if VBUSC droop drifts upward over the soak, suspect via degradation rather than F2. Next-rev: route QG on B.Cu so PMID is one pour, and stitch the Q6→F2 span with ≥4 vias. |
| **B3** | **J5's four VBUS contacts are unequally fed** — the right-hand pair reaches the board through a single via, so the split measures **2.91 A / 1.90 A (60.5 % / 39.5 %)**; two contacts carry **1.46 A** against the 1.25 A/contact the four-way split implies. | Within the connector's rating, but it is why Q5 measures at the cable end. Next-rev: stitch the second VBUSC island properly. |
| **B4** | **Twelve sole-path power/sense vias.** One is **fail-HIGH**: the 5VA via at (97.925, 46.000) carries buck-A's FB divider *and* VOUT sense — lose it and 5VA runs open-loop toward V_IN into three USB-A ports. | Gate **Q1's no-load reading catches this on the bench** (5VA must sit in 5.03-5.28 V; an open FB shows immediately). Do not skip Q1. Next-rev: double every sole-path power via. |

Also worth knowing, from the same review: F2 — the hottest element on the C
path at **0.775 W** — has **zero thermal vias on either pad** and an 8:1 copper
asymmetry between its input (27.3 mm²) and output (218.5 mm²) sides. Estimated
rise 31-39 °C. That is inside rating but it is the part to point the IR camera
at first in gate **Q4**.

The review also **retires two stale claims**: the R-THERM waiver's "1 via under
U11's exposed pad" and its next-rev work order are both obsolete — measured,
**U2 and U11 each already have 7 GND vias inside the exposed pad**, and VBAT_F
already has 195.6 mm² of B.Cu plus 7 vias.

---

## 4. Required Pi setting (ADR-0001)

The USB-C port is a **plain 5 V/5 A rail, NOT USB-PD**. The Pi MUST draw 5 A
without PD: set **`PSU_MAX_CURRENT=5000`** in the bootloader EEPROM (or
`usb_max_current_enable=1` in `config.txt`). Without it the Pi caps downstream
USB at 600 mA (still boots). A generic USB-C device sees a non-PD 3 A source.

## 5. Cable note

Use a short (0.3-0.5 m), **5 A-rated USB-C cable** for the Pi (no PD → no
e-marker enforcement; the E-MARGIN derivation budgets ~45 mΩ for it — verify
with gate Q5).

## 6. Protection behaviour (discrete SECONDARY protection — ADR-0002, HONEST)

- **Over-current:** F2 PPTC trips on a short/overload (resettable).
- **Over-voltage — SECONDARY / best-effort:** on a buck-fail-high, D5 clamps
  (~10.3 V @Ipp, above the Pi ceiling) and F2 must trip to end the exposure — a
  **crowbar, not a deterministic cutoff. NOT guaranteed against a buck high-side
  short.** Accepted for a supervised prototype with a replaceable Pi (BRIEF
  A3/D3). *(Recorded consequence: U12's V_BUS transil breaks down at 6.0 V min,
  below D5's 6.67-8.15 V window, so on a slow rise U12 conducts first and is
  effectively sacrificial — DETAIL_DESIGN sec.5.4, audit PCBA-15. Normal
  operation is unaffected.)*
- **Reverse-current / master-off:** Q6 (P-FET) is held OFF when the hub is
  switched off (SW1/ENKILL → Q7 opens Q6) → its body diode blocks a powered
  device on the port from back-feeding the pack. Reverse current is NOT
  instantaneously blocked while the port is actively ON (bounded by F2).
- **Protected against:** shorts, overload, reverse-feed with the port off.
  **NOT guaranteed against:** a buck high-side short (fail-high). Escalation
  boundary (verbatim): "add active OVP if the system becomes unattended,
  hard-access, carries valuable storage, or powers expensive SDR".

## 7. Notes carried from v1.1/v1.2/v1.3/v1.4

- **RT-T3:** LM5116 UVLO **9.65 V rise / 8.84 V fall** > 9.0 V nominal —
  accepted P2 (doubles as LiPo deep-discharge protection); spec/silk read
  "9-12.6 V". Derivation incl. the 5 µA pull-up: DETAIL_DESIGN sec.2.9.
- Master-off SW1 kills both bucks + opens Q6 (~270 µA storage draw,
  power_tree E-OFF).
- **First-power ritual (before ANY power):** multimeter the XT60 blades against
  the board nets (polarity + continuity through F1/Q1) — 30 seconds of beeping
  beats every upstream analysis.
- v1.3's electrical fixes (all carried, board unchanged): R12 = catalog-verified
  4.12 k 0.1 % C2984354 (never C2933210 = 3.74 k); D5 = catalog-UNIDIRECTIONAL
  SMBJ6.0A C113976 (never C140903 = bidirectional); R30 = ledger-verified 100 k
  C25803 (never C2933195 = 3.09 k).
- F1 is the **Keystone 3568 MINI-blade fuse holder, C5249699** — *not*
  "KH-AF90DIP-112", which is the USB-A connector family (v1.3 README error).

# ORDER README — usb-hub-3s-v3 **v1.6** (internal board name `usb_hub_3s_v2`)

3S-LiPo powered power-distribution board: XT60 pack in -> 10 A MINI-blade fuse ->
dual synchronous bucks (LM5116) -> 3x USB-A (5 V charging, no-data) + 1x
**Raspberry Pi 4**-dedicated USB-C (plain 5 V, discrete-protected).
**NOT a USB hub, NOT USB-PD.** Release **v1.6-2026-07-26**.
Board **130.1 x 92.1 mm**, **4 layer**, **122 BOM parts / 119 CPL placements**.

> ## v1.5 AND EVERY EARLIER RELEASE ARE **DO-NOT-ORDER**
>
> A new **A-POS** gate measured every CPL row against JLC's actual convention —
> JLC positions a part from the bounding box of its **PAD CENTRES** — and found
> **11 of v1.5's 108 rows off-datum**, because the exporter had been emitting
> `fp.GetPosition()`, the footprint **anchor**:
>
> | ref | error |
> |---|---|
> | **J1** (XT60, the pack inlet) | **4.6861 mm** |
> | **J2 / J3 / J4** (USB-A) | **3.7346 mm** each |
> | **J5** (USB-C, 0.5 mm pitch) | **1.4975 mm** |
> | Q4 / Q5 / Q6 | 0.0625 mm each |
>
> **Every external connector on the board**, and the worst by nearly 5 mm. This
> is not a rotation question and no render would have shown it. In v1.6 all
> **119** rows are graded and the worst residual is **0.00050 mm**.
>
> **Order from THIS directory.** v1.5 carries a `SUPERSEDED.md` pointing here.

## 0. What changed, in one screen

**The load is a Raspberry Pi 4, not a Pi 5.** Do **NOT** look for
`PSU_MAX_CURRENT=5000` or `usb_max_current_enable=1` anywhere — those are Pi 5
bootloader-EEPROM settings, they **do not exist on a Pi 4**, and earlier releases
told you to set them. A Pi 4 does not negotiate PD for its power input at all: it
is a plain 5 V sink at its official **5 V / 3 A (15 W)**. **There is nothing to
configure on the Pi.** (ADR-0004; ADR-0001 is `superseded-by: 0004`, reasoning
only.)

That correction improves the delivery margin **16.5x** with no hardware change —
+15.0 mV -> **+244.2 mV** — and retires the "15 mV of paper slack is not a margin
you ship on" caveat that followed v1.5. **The board is still built for 5 A**
(buck-C, F2's 7 A polyfuse, the VBUSC via count, the pours). That is deliberate
over-provisioning, not a contradiction.

Also new: **5 status LEDs**, an **H3 mounting-hole short fixed**, **3 fiducials**
(earlier releases had none), **PowerPAK paste 100% -> 65% window-pane**, and
**VBUS ampacity 0.5 -> 0.8 mm**. Full list: `01_docs/CHANGELOG.md`.

## 1. Do NOT let JLC place these

| ref | what | why |
|---|---|---|
| **F1** | Keystone MINI blade fuse **holder** | On the BOM, **off the CPL**. Hand-solder at integration. JLC has no placement model (twin `best=none`); the land is the Keystone catalog p.42 pattern. |
| **SW1** | SS12D07 slide switch | On the BOM, **off the CPL**. Its pitch is unconfirmed — JLC's own model file is the **wrong VG4 variant** (2.0 mm) against our 2.5 mm land. Fit by hand after measuring the received part. |
| **R42** | 160 kOhm 0402 setpoint-trim strap | **DNP by design.** On the BOM (so JLC ships one loose), **off the CPL**. Fit ONLY if bench gate **Q9** fails. See section 4. |

The **10 A MINI (ATM) blade fuse element** is a consumable and is deliberately
**off the BOM entirely** — buy locally, fit by hand.

**Through-hole assembly IS part of the order.** J1-J4 (4 refdes / 22 plated
holes) plus J5's 4 hybrid shield legs are on the CPL *because the THT line is
bought*. Do not let anyone "simplify" the quote by dropping it —
`03_src/rules/assembly.yaml` `through_hole:` declares it with the measured hole
census.

## 2. Order-preview human gate — MANDATORY

Open JLC's assembly preview (3D + the per-part rotation view). **Colour
semantics:** white = your silkscreen; **magenta glyphs = JLC's own model's pin-1 /
polarity markers**. A missing body = no 3D model (the part still mounts — check
the BOM tab, not the render).

`rotation_human_gate.txt` in this directory lists the **5 single-channel codes**
whose rotation cannot be settled without a human: **C13755** (U2, U11),
**C98732** (J1), **C7519** (U8-U10, U12), **C130056** (U3-U5), **C473910**
(U6, U7).

| # | Check | What you must see | REJECT if |
|---|---|---|---|
| **P1** | **D8-D12 — the five indicator LEDs. THE ONE THAT MATTERS THIS TIME.** | **CPL rotation 0.0 on all five.** JLC numbers this part's **pad 1 = ANODE**; KiCad numbers **pad 1 = CATHODE**. The two libraries number the terminals **oppositely**, so a pad-number fit confidently says 180 — at a 17.7x margin — and is **physically wrong**. Both libraries draw the cathode on the **same physical side**, so the parts already align at 0. | Any LED row reads **180.0**. That ships every indicator **dark**, which on a bench is indistinguishable from a dry joint. `jlc_twin`'s own marking channel independently confirms the fit is 180 deg out; its `ROT-DB-SUGGEST` line saying "add C2296,180" is a **known tool inconsistency**, adjudicated REJECTED. |
| **P2** | **J1 — XT60 polarity. MANDATORY.** | **Pad 1 is the NEGATIVE (-) blade** (`02_parts/XT60PW-M/part.yaml`: "PAD 1 IS NEGATIVE - polarity is a PART FACT"), on the **GND** net. CPL **0.0**, Mid X/Y **(27.0, -40.4)** — the pad-array centre, **not** (30.0, -44.0). | Anything else. **A reversed XT60 has shipped from this fleet before.** Geometry settles the ROTATION (the two anchor holes sit 6.0 mm off the blade axis: rms 0.0000 mm at one angle, 12.0 mm at the other, no pad numbering involved). Geometry **cannot** tell you which blade is "+". Only a human with the connector can. |
| **P3** | **C1, C2 — polarized polymer electrolytics.** | "+" / pin-1 end toward the VIN (fuse/Q1) side. CPL **90.0**. | Reversed, or CPL 270.0. This was the v1.4 DO-NOT-ORDER defect: a reverse-biased polymer cap on a near-zero-impedance 3S pack **vents**. |
| **P4** | **D1, D2, D3, D4, D5 — cathode direction.** | Cathode (pad 1, banded end) on: D1 -> VIN, D2 -> VIN, D3 -> BOOT_A, D4 -> BOOT_C, D5 -> VBUSC. All read CPL **0.0**. Band on JLC's model must line up with our silk. | Band reversed on any. A backwards TVS is a permanent short across the rail it protects. |
| **P5** | **R12 — the part is REALLY C2984354.** | BOM line `4.12kOhm / R12 / AR03BTCX4121 / C2984354` matched and priced. `jlc_twin` reports **FETCH-FAILED**: EasyEDA's API answers `{"code":404,"message":"Component not found"}` for this code, probed directly after 8 attempts — genuinely absent from their CAD library, not a flake. There is no model to compare, so **the BOM line IS the check**. | JLC substitutes anything. **NEVER accept C2933210 (3.74 kOhm)** — the v1.2 undervoltage bug. Verified alternate: **C861436**. |
| **P6** | **Q1-Q6 — PowerPAK paste.** | The exposed drain pad shows a **2x2 array of paste apertures**, not one big opening. | One 100% aperture. That is the v1.5 geometry and it floats/tilts the package, opening the **gate** joint. |
| **P7** | **R42, F1, SW1 not placed.** | All three flagged DNP / no placement. | JLC "helpfully" adds placement data for any of them. |
| **P8** | **Rotation + datum sweep, everything else.** | Every polarized 2-pad part shows its magenta pin-1 marker on the same end as our silk. Spot-check that connector Mid X/Y values look like pad-array centres, not anchors. | Any mismatch. All 119 rotations resolve from **measured** per-LCSC rows and the datum residual is <= 0.0005 mm, so a preview disagreement means the preview is telling you something new — **investigate, do not rationalize**. |

## 3. The cable is the biggest single risk, and it is yours to control

**~45 of the 98 mOhm delivery budget is the USB-C cable** — the largest single
term, bigger than every piece of board copper combined. And that 45 mOhm figure
**already assumes a good cable**: 0.3-0.5 m, 20 AWG, e-marked
(33.2 mOhm/m x 0.5 m x 2 conductors x 1.157 hot + ~6 mOhm contacts = ~45 mOhm).

- a **1 m** cable adds **~40 mOhm**
- a cheap **24 AWG** cable adds **~160 mOhm** and **fails the Pi 4 at 3 A**

**The cable is a downside risk to eliminate, not headroom to gain.** Use a short,
well-made, e-marked cable, and measure it (gate Q5).

## 4. Bench gates — run in order, record the numbers

All current-dependent gates are stated at the **Pi 4's 3 A**. Earlier releases
stated 5 A; that was the Pi 5 premise (ADR-0004).

| # | Gate | PASS | FAIL action |
|---|---|---|---|
| **Q0** | Visual: no solder bridges; F1/SW1/R42 unpopulated as intended; all 5 LEDs present. | — | — |
| **Q1** | **Nylon standoffs are NO LONGER required** — verify anyway that any metal M3 you fit sees **GND only**. v1.6 fixed H3, where F.Cu *and* B.Cu carried **both 5VA and GND at 1.850 mm** from a 1.600 mm drill; 5VA now stops at **4.500 mm**. | No continuity from any fastener to 5VA / VBUSA3 / VIN. | Stop — a metal screw used to short the 6 A rail to GND on both faces. |
| **Q2** | **8-24 h soak on an ELECTRONIC LOAD** (not the Pi): **3 A** on USB-C + 6 A total across the USB-A ports. | **VBUSC >= 5.00 V at 3 A**, stable, no F2 nuisance trip, no thermal runaway. | Any trip/droop/drift: diagnose before any Pi contact. |
| **Q3** | Scope **SW_A and SW_C** at Vin 12.6 V through startup, shutdown (SW1), load steps 0->3 A->0, and **capture VBUSC on a 3 A->0 A release**. | Ringing within FET ratings; clean monotonic soft-start; **load-release overshoot on VBUSC <= 5.45 V**. | Overshoot at the ceiling: snubber/compensation rework (R34/C53, R35/C54 are fitted by default for exactly this). |
| **Q4** | Thermal soak at the hottest expected ambient, full load (IR camera or thermocouples: L1/L2, Q2-Q5, U2/U11, F2, **and the F1 fuse clips**). | Temps in rating with margin; F2 below trip-derate at 3 A. Worst-case input trunk is **7.12 A on a 10 A blade = 71%** — watch the clips. | Derate the load spec or rework. |
| **Q5** | **VBUSC at the END of the actual cable** that will feed the Pi, at **3 A**, thermally settled (hot). | **>= 4.90 V at the cable end, hot**; no undervoltage events on fast transients. The un-derated paper corner at 3 A is **4.936 V**, so this floor sits deliberately just above the arithmetic. | Below: shorter/better cable first (section 3). Only then consider the R12 4.12k->4.22k mitigation. |
| **Q6** | **PACK QUIESCENT — LEDs fitted, SW1 OFF.** Measure pack current with a **uA meter** and **record the ambient temperature with it**. | **<= 300 uA.** Declared budget 271 uA (252 uA switch sink + 18 uA 2x LM5116 shutdown + <=1 uA Q8 leakage). | Above 300 uA: the pack-LED gate Q8 is leaking, or ENKILL is not fully low. **An ungated pack LED would draw 1.504 mA and flatten a 3S 5000 mAh pack in ~117 days** — this gate exists because the datasheet 0.5 uA is a **25 C maximum** nothing had ever measured, and MOSFET leakage climbs ~10x per 40-50 C. |
| **Q7** | **LED function.** All five light with the board on; each USB-A LED tracks **its own port**. | PACK amber on; USB-A1/2/3 green on; USB-C green on. | **A dark LED is either reversed or a dry joint — you cannot tell which by looking.** If one is dark, re-check P1 first, then the joint. |
| **Q8** | **Protection-chain semantics.** Open F2 or disable Q6 and confirm the **USB-C LED goes dark while the USB-A LEDs stay lit**. | Exactly that. | If the C LED tracks the bucks instead, its tap is on 5VC not VBUSC and it cannot report the fault it exists to report. |
| **Q9** | **U12 stress / R42 decision.** Measure **VBUSC at no load and at 3 A**, and **U12's leakage at the measured voltage over temperature**. | **Fit nothing if U12's leakage is acceptable at 5.352 V. Fit R42 if it is not.** Record the measured numbers **either way** — including the "we fitted nothing" case. | Fitting R42 moves the rail 5.352 -> 5.249 V, onto U12's 5.25 V V_RWM. Cost: worst-case vout_min 5.227 -> 5.125 V, minus 349 mV IR = **4.776 V, still +146 mV** of margin. Affordable only because the load is a Pi 4. |
| **Q10** | **Pi stress test (last).** Monitor `vcgencmd get_throttled` continuously through a full stress run. | `get_throttled` = **0x0** throughout. | Any UV/throttle flag: capture VBUSC at the Pi end under the failing load; revisit the cable (section 3) then Q5. |

## 5. Honest limitations — read before deploying

- **NOTHING ON THIS BOARD PROTECTS THE PI FROM A SUSTAINED OVER-VOLTAGE.** A TVS
  clamps transients, not a stuck regulator. Line the rail up: worst-case
  operating **5.479 V**, Pi 4 absolute maximum **6.00 V** (Pi 4 datasheet p.8,
  "a stress rating only"), U12 guaranteed non-conduction floor **6.00 V**, D5
  breakdown **minimum 6.67 V**. **D5 cannot protect the Pi** — by the time it
  conducts the rail is already 670 mV past the Pi's limit, and no TVS that also
  clears a 5.479 V operating rail could do better. **Do not "fix" this by
  reselecting D5**; the part does not exist (ADR-0003 has the catalog search).
  The escalation, if an unattended or production context ever needs it, is an
  **active OVP at ~5.6-5.7 V — a disconnect or crowbar, not a different TVS.**
  This is the fail-high posture the BRIEF accepts as best-effort **for a
  supervised prototype**.
- **`LEDS DARK = SWITCH OFF` / `PACK STILL LIVE AT XT60`** is on the silk for a
  reason: SW1 switches **ENABLE**, not power. The XT60 stays hot with the switch
  off, and the pack LED is FET-gated, so an all-dark board is **not**
  de-energized.
- **Not USB-PD, not USB-C compliant as a generic source.** Pi-dedicated.
- **Protected 3S pack + balance charger ONLY.**

## 6. Fixed since v1.5 — the two "next-rev" items its own review raised

- **B2** — "the 5 A USB-C path crosses Q6 -> F2 through TWO 0.30 mm vias in
  series, with no redundancy." **Fixed:** PMID now carries **13** vias (4 in each
  F2 pad plus 6 bonding the F.Cu/B.Cu pours).
- **B3** — "J5's four VBUS contacts are unequally fed — the right-hand pair
  reaches the board through a single via (2.91 A / 1.90 A split)." **Fixed:**
  **3 vias per VBUS contact pair**; VBUSC total 5 -> **15**.

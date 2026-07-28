# ORDER README — usb-hub-3s-v3 **v1.11** (internal board name `usb_hub_3s_v2`)

3S-LiPo powered power-distribution board: XT60 pack in -> 10 A MINI-blade fuse ->
dual synchronous bucks (LM5116) -> 3x USB-A (5 V charging, no-data) + 1x
**Raspberry Pi 4**-dedicated USB-C (plain 5 V, discrete-protected).
**NOT a USB hub, NOT USB-PD.** Release **v1.11-2026-07-27**.
Board **130.1 x 92.1 mm**, **4 layer**, **122 BOM parts / 119 CPL placements**.

## ✅ v1.11 SUPERSEDES v1.10 — ONE OUT-OF-STOCK PASSIVE SUBSTITUTED, NO COPPER CHANGE

**v1.10 is not wrong and is not DO-NOT-ORDER. It is UNORDERABLE.** You uploaded
its BOM to JLCPCB and line 8 came back **"10 shortfall"**: `C25744`, the 10 kΩ
0402 on **R28/R29** (the USB-C CC1/CC2 Rp pull-ups). JLC's own parts API,
re-queried 2026-07-27, reports **`stockCount: 0`** for that code.

**The swap, and every number behind it, read live from JLC's catalog on
2026-07-27** (`selectSmtComponentList`, exact `componentCode` match):

| | C25744 (out) | **C60490 (in)** |
|---|---|---|
| MPN | `0402WGF1002TCE` UNI-ROYAL | **`RC0402FR-0710KL` YAGEO** |
| stock | **0** | **8 220 334** |
| library | base | **expand (Extended)** |
| `leastPatchNumber` | 20 | **20** |
| unit price @1–999 | $0.0020 | $0.0058 |
| `describe` | `-55℃~+155℃ 10kΩ 50V 62.5mW Thick Film Resistor ±1% ±100ppm/℃ 0402 Chip Resistor - Surface Mount ROHS` | **character-identical** |

The two `describe` strings were compared **as strings** and are equal: same
package, value, tolerance, tempco, power rating and voltage rating. It is a true
drop-in — **no copper change, no footprint change, no netlist change.**

### 💡 You are paying a one-time EXTENDED-part feeder fee, and there was no way round it

`C25744` was the **only basic-library 10 kΩ 0402 in JLC's catalog**. Every
possible replacement is an Extended part, so the feeder fee is not a consequence
of choosing this particular resistor — it is a consequence of the basic part
being gone. You chose the swap knowing this. Two order-form consequences:

* **The order-day stock recheck on this line is now mandatory, not
  nice-to-have.** Extended parts are not held in JLC's standing feeders.
* The line joins the existing Extended-tier population; it does not add a new
  *category* of obligation, only one more row to it.

### 🔴 What this episode says about our own stock gate — read this before trusting it again

`jlc_stock_check.py` **PASSED v1.10 on that exact line**, hours before JLC
refused it. Its sealed evidence in `v1.10/verification/stock_check.json` reads:

    {"lcsc": "C25744", "designators": "R28,R29", "qty": 2,
     "status": "OK", "stock": 291, "type": "base", ...}

291 ≥ 5×2, so the rule was satisfied and the verdict was `PASS`. **The number it
reads — `stockCount`, LCSC's catalog stock — is not the quantity JLC's assembly
uploader will commit against your order.** The same gate reports
`C13755` (LM5116, U2/U11) at `stock=7275, status OK` today while JLC's assembly
side has **0** and wants a Pre-order. So:

* A **FAIL** from this gate is still real — believe it.
* A **PASS** is a NECESSARY condition and not a sufficient one. It does not
  predict that the uploader will clear the line.
* C60490's 8.2 M is two to four orders of magnitude of headroom over the 291 that
  failed, which materially reduces the risk. It does not eliminate the class.

Fixing the gate to read the assembly-side figure is a SEPARATE change and is
deliberately not folded into this one-line part swap.

### What did NOT change, measured

* `source/usb_hub_3s_v2.kicad_pcb` md5 **`83af8e5a5596a51cf139dd06e8903d47`** —
  identical to v1.10's **and** to `04_kicad/`'s. One file.
* Gerbers + drills **RE-PLOT** from this release's own source board **15/15
  byte-identical** to v1.10's sealed zip after stripping only the plot's own
  timestamps — the pour (36 zones / 106 filled outlines) inside them.
* `fab/cpl.csv` **byte-identical** (`cmp`, 0 differences, 119 rows). Every
  rotation, coordinate and datum in this document is carried forward untouched.
* `fab/bom.csv`: **46 → 46 rows**, designator list identical in order, **two
  cells changed**, both on the `R28,R29` row (MPN and LCSC). Zero Footprint
  changes, zero Comment changes, zero rows added or removed.
* 20 of 22 payload files sha256-identical; the two that differ are `fab/bom.csv`
  and `source/usb_hub_3s_v2.tsx` — the second because canon M3 requires the BOM
  row to have moved *because the source moved*, not by hand.

Full numbers: `verification/replot_identity.txt`.

**Everything below this line describes v1.10 and stands unaltered for v1.11.**
The board, its reviews, its bench gates and its limitations are the same board's.

## ✅ v1.10 SUPERSEDES v1.9 — BOM LEGIBILITY ONLY, NO COPPER CHANGE

**v1.9 is not wrong and is not DO-NOT-ORDER.** Its board is this board: the
`.kicad_pcb` is md5-identical (`83af8e5a5596a51cf139dd06e8903d47`) to v1.9's and
to `04_kicad/`'s, the gerbers and drills RE-PLOT from this release's own source
15/15 byte-identical after the timestamp strip — **including the restored pour**,
36 zones / 106 filled outlines — and `fab/cpl.csv` is byte-identical, so every
rotation and coordinate below is unchanged. **Only `fab/bom.csv` changed, and
only in its Comment and MPN columns.**

**What was wrong with it.** Graded the way the RECIPIENT parses it (canon
F-LEGIBLE, ADR-0006), v1.9's BOM has **26 findings**:

| check | findings on v1.9 | what JLC saw |
|---|---|---|
| F-WORDS | 21 | the Comment is an **LCSC code**, so 21 of 46 rows cannot be reviewed by a human on either side of the upload |
| F-MPN | 4 | `C25757` (R42), `C2296` (D8), `C2297` (D9–D12) ship a **blank MPN** even though all three have `02_parts` dossiers → JLC leaves a code-only line at *No Part Selected*. And **SW1 ships `SS12D07VG6 087` with a SPACE** where `02_parts/SS12D07VG6-087` says a **HYPHEN** — the two match paths DISAGREE |
| F-ENCODE | 1 | `Ω` with **no UTF-8 byte-order-mark**, so a cp936 reader renders `CE A9` as `惟` |

**This release: 0 findings.** 46/46 coded rows carry an MPN resolved from
`02_parts/<MPN>/part.yaml` or the vetted passives ledger, 46/46 Comments read,
and the file carries the byte-order-mark.

The SW1 drift is worth naming: **this is the only board in the fleet that ever
maintained the retired `lcsc_mpn_map.csv` side-file**, so it is the only board
where a second home for the MPN could disagree with the first. The side-file is
retired as an input; the dossier is the one home and it won.

### 🔴 F-ECHO — the human gate this release adds (do it at upload time)

JLC RESOLVES our codes on their side and can silently redirect one: on a sibling
board our source said `C82317` in three places and JLC's resolved output came
back `C131025`. **After uploading `fab/bom.csv`, save JLC's own resolved/matched
part table out of their UI and run:**

```
bom_legibility_check.py 07_releases/v1.11-2026-07-27/fab/bom.csv \
                        --echo <saved-jlc-table>.csv
```

A code JLC redirects is a **SUBSTITUTION and a FINDING**, not a convenience.
The 46-line worklist is `verification/bom_echo_gate.txt`. This is a SECOND
pre-order human gate, beside — not instead of — the A-POL order-preview check
in section 0/3 below.

> # v1.6, v1.7 AND v1.8 ARE **DO-NOT-ORDER**. THEY HAVE NO COPPER POUR.
>
> Three consecutive sealed releases shipped gerbers with **ZERO copper pour on
> all four layers** — **44287.91 mm2 of missing copper**: no GND plane, no VIN
> plane, no 5VA/5VC/VBUS/switch-node islands. Ordering any of them yields a board
> whose 7 A battery trunk and 6 A rails exist only as the handful of thin routed
> stubs that were never meant to carry the current, and whose return path is
> nothing at all.
>
> **Every gate was green.** The cause is one line of doctrine nobody had written
> down: `kicad-cli pcb drc --refill-zones` **refills the zones IN MEMORY**. It
> therefore reports 0/0/0 on a board whose SAVED FILE has no fill. DRC, netlist
> parity, the digital twin, the renders, ERC, the policy audit — every one of
> them was measuring an in-memory board that was correct, while the bytes on disk
> and the bytes in the zip were not.
>
> **Root cause:** `03_src/post_stitch_fixes.py` section 6, added in v1.6, unfills
> the zones so it can drop vias, and never refills before its own save. That
> script holds the **LAST** save in the pipeline, so the refill guard inside the
> stitch driver guarded nothing.
>
> **The signature was visible in the shipped payload the whole time.** v1.8's
> `In1_Cu` and `In2_Cu` gerbers are **BYTE-IDENTICAL at 18921 bytes** — a GND
> plane and a VIN plane cannot be the same file unless neither contains a plane.
> They matched because each held only the layer-independent flash list.
>
> **v1.9 restores the pour and ships the proof.** See section 0.

## 0. What changed, and how you can check it yourself

**Nothing electrical changed.** Netlist parity against v1.8 is **0 differences**
(122 components, 73 nets, 372 nodes, identical), and `fab/cpl.csv` is
**byte-identical** to v1.8's. Placement, connectivity, part selection, rotations
and the datum are all exactly what v1.8 sealed. What changed is copper.

Three independent measurements, all in `verification/`:

| measurement | v1.8 | v1.9 |
|---|---|---|
| **F-PAYLOAD** (`fab_payload_census.py`, opens the SHIPPED zip) | **FAIL: 5 findings, 0 ok** | **OK: 5 checks passed** |
| F-POUR B.Cu / F.Cu / In1.Cu / In2.Cu (G36 regions in the gerber) | **0 / 0 / 0 / 0** | **17 / 87 / 1 / 1** |
| F-IDENT (the two inner-layer gerbers) | **BYTE-IDENTICAL at 18921 B, 0 G36** | **all 4 copper gerbers distinct** |
| M-SHIP read-back on the saved board | 0 `filled_polygon` | **36 pour zones, 106 `filled_polygon`** |
| `fab/usb_hub_3s_v2_gerbers.zip` size | 88 692 B | **394 534 B** |
| DRC (severity-all, refill-zones, schematic-parity) | 0 / 0 / 0 | 0 / 0 / 0 |

The zip is 4.4x larger because the copper is in it. That is the crudest possible
check and you can run it without any tooling.

**The gates that now make this class impossible, both new since v1.8:**
* **M-SHIP read-back** (`route_and_stitch_generic.py verify-fill`) — reopens the
  saved `.kicad_pcb` **AS TEXT** and counts `filled_polygon` blocks. Text, not
  pcbnew, deliberately: pcbnew is the tool whose save behaviour is under test, so
  re-reading through it would share a method with the thing being checked. It is
  wired into both `03_src/rebuild_fast.sh` and `03_src/rebuild_all.sh`.
* **F-PAYLOAD** (`fab_payload_census.py`) — opens the shipped **zip** and grades
  it against the board. This is the one that closes the loop, because it is the
  only gate downstream of the export.

Also in v1.9, all from gates that did not exist when v1.8 sealed:
* **A-AMP now grades 10/10 net-class currents** (it graded 3 of 10 before a
  qualifier-parsing fix; "7 A worst case" was silently unread). Four trunk
  classes now carry MEASURED pour evidence; two are declared track-fed with
  their numbers. Section 6.
* **S-COUNT parity restored 4-way** — the v1.6 status-LED cell (12 refs) was
  never added to `03_tscircuit/manifest.yaml`.
* **`pdf/schematic.pdf` is tscircuit's OWN render again** (ADR-0002). v1.6-v1.8
  regressed to an Eeschema re-render and the evidence gate passed it because it
  checks for the FILENAME, not the producer.
* **`verification/rules_audit.txt` ships** — v1.8 shipped none while A-AMP failed.

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

## 1b. What to select on the PCB order form — the STACKUP

**The board file declares no stackup.** `usb_hub_3s_v2.kicad_pcb` and
`.kicad_pro` contain **zero** `stackup` entries, so the copper weight behind
every ampacity number in this release is a **fab default** — which means it is
whatever the order form says, and nobody had written down what that must be
until v1.9 (fix-lens P2-7).

**ORDER: JLC 4-layer, 1.6 mm, STANDARD — 1 oz outer / 0.5 oz inner
(34.8 um / 17.4 um).** That is JLC's own 4-layer default and it is what every
figure in section 6 assumes. The two inner planes (In1 = GND, In2 = VIN) carry
**half** the copper per unit width of an outer layer, so "1 oz external"
arithmetic does not apply to them.

**It changes no conclusion in this release** — every IPC-2221 requirement quoted
in section 6 is an outer-layer one, and PWR_IN's 1.99x is attributed to VBAT's
8.750 mm on F.Cu, not to the plane. But if you order a **different inner
weight**, the plane figures move and this release's ampacity evidence no longer
describes the board you receive. Declaring the stackup **in the board file** is
a next-revision work order; it was not done in v1.9 because it would change the
sealed payload that the three v1.9 reviews were run against, for a parameter the
gerbers do not carry.

## 2. Order-preview human gate — MANDATORY

Open JLC's assembly preview (3D + the per-part rotation view). **Colour
semantics:** white = your silkscreen; **magenta glyphs = JLC's own model's pin-1 /
polarity markers**. A missing body = no 3D model (the part still mounts — check
the BOM tab, not the render).

`rotation_human_gate.txt` in this directory lists the **5 single-channel codes**
whose rotation cannot be settled without a human: **C13755** (U2, U11),
**C98732** (J1), **C7519** (U8-U10, U12), **C130056** (U3-U5), **C473910**
(U6, U7).

**P0 — NEW THIS RELEASE, AND IT TAKES FIVE SECONDS.** Open the **gerber viewer**
on `fab/usb_hub_3s_v2_gerbers.zip` before you open anything else, and look at
**In1_Cu** and **In2_Cu**. You must see a **solid GND plane** and a **solid VIN
plane**. If either inner layer is blank, or if the two look identical, **STOP** —
that is the v1.6/v1.7/v1.8 defect and you are holding the wrong zip. Do the same
for F_Cu and B_Cu: the outer layers must show large filled regions, not just
tracks.

| # | Check | What you must see | REJECT if |
|---|---|---|---|
| **P1** | **D8-D12 — the five indicator LEDs.** | **CPL rotation 0.0 on all five.** JLC numbers this part's **pad 1 = ANODE**; KiCad numbers **pad 1 = CATHODE**. The two libraries number the terminals **oppositely**, so a pad-number fit confidently says 180 — at a 17.7x margin — and is **physically wrong**. Both libraries draw the cathode on the **same physical side**, so the parts already align at 0. | Any LED row reads **180.0**. That ships every indicator **dark**, which on a bench is indistinguishable from a dry joint. `jlc_twin`'s `ROT-DB-SUGGEST` line saying "add C2296,180" is a **known tool inconsistency**, adjudicated REJECTED — its own marking channel disagrees with its own pad fit. |
| **P2** | **J1 — XT60 polarity. MANDATORY.** | **Pad 1 is the NEGATIVE (-) blade** (`02_parts/XT60PW-M/part.yaml`: "PAD 1 IS NEGATIVE - polarity is a PART FACT"), on the **GND** net. CPL **0.0**, Mid X/Y **(27.0, -40.4)** — the pad-array centre, **not** (30.0, -44.0). | Anything else. **A reversed XT60 has shipped from this fleet before.** Geometry settles the ROTATION; only a human with the connector can say which blade is "+". |
| **P3** | **C1, C2 — polarized polymer electrolytics.** | "+" / pin-1 end toward the VIN (fuse/Q1) side. CPL **90.0**. | Reversed, or CPL 270.0. This was the v1.4 DO-NOT-ORDER defect: a reverse-biased polymer cap on a near-zero-impedance 3S pack **vents**. |
| **P4** | **D1, D2, D3, D4, D5 — cathode direction.** | Cathode (pad 1, banded end) on: D1 -> VIN, D2 -> VIN, D3 -> BOOT_A, D4 -> BOOT_C, D5 -> VBUSC. All read CPL **0.0**. | Band reversed on any. A backwards TVS is a permanent short across the rail it protects. |
| **P5** | **R12 — the part is REALLY C2984354.** | BOM line `4.12kOhm / R12 / AR03BTCX4121 / C2984354` matched and priced. `jlc_twin` reports **FETCH-FAILED**: EasyEDA's API answers 404 for this code (probed directly, and again on 2026-07-27 with 8 attempts) — genuinely absent from their CAD library, not a flake. There is no model to compare, so **the BOM line IS the check**. | JLC substitutes anything. **NEVER accept C2933210 (3.74 kOhm)** — the v1.2 undervoltage bug. Verified alternate: **C861436**. |
| **P6** | **Q1-Q6 — PowerPAK paste.** | The exposed drain pad shows a **2x2 array of paste apertures**, not one big opening. | One 100% aperture. That is the v1.5 geometry and it floats/tilts the package, opening the **gate** joint. |
| **P7** | **R42, F1, SW1 not placed.** | All three flagged DNP / no placement. | JLC "helpfully" adds placement data for any of them. |
| **P8** | **Rotation + datum sweep, everything else.** | Every polarized 2-pad part shows its magenta pin-1 marker on the same end as our silk. Spot-check that connector Mid X/Y values look like pad-array centres, not anchors. | Any mismatch. All 119 rotations resolve from **measured** per-LCSC rows and the datum residual is <= 0.0005 mm, so a preview disagreement means the preview is telling you something new — **investigate, do not rationalize**. |

**Render caveat you need when you look at the 3D preview** (measured by
`twin_overlay.py`, canon A-RENDER; full adjudication in
`verification/gate_adjudications_v1.9.md`): the six PowerPAK SO-8 FETs
**Q1..Q6** have no pad correspondence with JLC's model — the KiCad land names all
four drain pads `5` — so their BODIES are drawn at JLC's own transform, roughly
1.5-2.0 mm off where the board puts them. **Judge Q1..Q6 from the pads and the
courtyard, not from where the body sits in the picture.** Everything else in the
render was measured faithful.

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

All current-dependent gates are stated at the **Pi 4's 3 A**.

| # | Gate | PASS | FAIL action |
|---|---|---|---|
| **Q0** | Visual: no solder bridges; F1/SW1/R42 unpopulated as intended; all 5 LEDs present. **AND: the received bare board has visible copper pour on both outer faces.** | — | If the outer faces are bare between the tracks, you were shipped a v1.6-v1.8 payload. Stop. |
| **Q1** | **Nylon standoffs are NO LONGER required** — verify anyway that any metal M3 you fit sees **GND only**. v1.6 fixed H3, where F.Cu *and* B.Cu carried **both 5VA and GND at 1.850 mm** from a 1.600 mm drill; 5VA now stops at **4.500 mm**. | No continuity from any fastener to 5VA / VBUSA3 / VIN. | Stop — a metal screw used to short the 6 A rail to GND on both faces. |
| **Q2** | **8-24 h soak on an ELECTRONIC LOAD** (not the Pi): **3 A** on USB-C + 6 A total across the USB-A ports. | **VBUSC >= 5.00 V at 3 A**, stable, no F2 nuisance trip, no thermal runaway. | Any trip/droop/drift: diagnose before any Pi contact. |
| **Q3** | Scope **SW_A and SW_C** at Vin 12.6 V through startup, shutdown (SW1), load steps 0->3 A->0, and **capture VBUSC on a 3 A->0 A release**. | Ringing within FET ratings; clean monotonic soft-start; **load-release overshoot on VBUSC <= 5.45 V**. | Overshoot at the ceiling: snubber/compensation rework (R34/C53, R35/C54 are fitted by default for exactly this). |
| **Q4** | Thermal soak at the hottest expected ambient, full load (IR camera or thermocouples: L1/L2, Q2-Q5, U2/U11, F2, **and the F1 fuse clips**). | Temps in rating with margin; F2 below trip-derate at 3 A. Worst-case input trunk is **7.12 A on a 10 A blade = 71%** — watch the clips. | Derate the load spec or rework. |
| **Q4b** | **NEW — the one ampacity item this release did NOT clear at the house dT of 10 C.** IR the **three USB-A VBUS feeds** (the 0.800 mm B.Cu runs from each TPS2557 OUT pin east to its port pour) with **each port at its full 2 A**, hot. | Rise on those runs consistent with the computed **9.6 C at 2.0 A**. | A rise materially above ~16 C (the computed 2.5 A figure) means the current is not what the design budget says. See section 6. |
| **Q5** | **VBUSC at the END of the actual cable** that will feed the Pi, at **3 A**, thermally settled (hot). | **>= 4.90 V at the cable end, hot**. | Below: shorter/better cable first (section 3). Only then consider the R12 4.12k->4.22k mitigation. |
| **Q6** | **PACK QUIESCENT — LEDs fitted, SW1 OFF.** Measure pack current with a **uA meter** and **record the ambient temperature with it**. | **<= 1.00 mA.** Declared budget **714 uA typ / 744 uA worst** (443 uA the two LM5116 UVLO dividers + 252 uA ENKILL switch sink + 18 uA 2x LM5116 shutdown + <=1 uA Q8 leakage). See the note below — **the threshold this release ships is NOT the 300 uA v1.6-v1.8 carried, and 300 uA would have failed a good board.** | **1.00-1.45 mA: INDETERMINATE, not an automatic fail** — see the note. **>= 1.45 mA: the pack-LED gate Q8 is leaking or ENKILL is not fully low.** |
| **Q7** | **LED function.** All five light with the board on; each USB-A LED tracks **its own port**. | PACK amber on; USB-A1/2/3 green on; USB-C green on. | **A dark LED is either reversed or a dry joint — you cannot tell which by looking.** If one is dark, re-check P1 first, then the joint. |
| **Q8** | **Protection-chain semantics.** Open F2 or disable Q6 and confirm the **USB-C LED goes dark while the USB-A LEDs stay lit**. | Exactly that. | If the C LED tracks the bucks instead, its tap is on 5VC not VBUSC and it cannot report the fault it exists to report. |
| **Q9** | **U12 stress / R42 decision. READ THE NOTE BELOW THIS TABLE FIRST — as shipped, U12 runs above a datasheet rating.** Measure **VBUSC at no load and at 3 A**, and **U12's leakage at the measured voltage over temperature**. | **Fit nothing if U12's leakage is acceptable at 5.352 V. Fit R42 if it is not.** Record the measured numbers **either way**. | Fitting R42 moves the rail 5.352 -> 5.249 V, onto U12's 5.25 V V_RWM. Cost: worst-case vout_min 5.227 -> 5.125 V, minus 349 mV IR = **4.776 V, still +146 mV** of margin. |
| **Q10** | **Pi stress test (last).** Monitor `vcgencmd get_throttled` continuously through a full stress run. | `get_throttled` = **0x0** throughout. | Any UV/throttle flag: capture VBUSC at the Pi end under the failing load; revisit the cable (section 3) then Q5. |

### Q6 in plain words: the OLD threshold would have CONDEMNED A GOOD BOARD

**Corrected in v1.9, before this release sealed.** v1.6, v1.7 and v1.8 all
declared an OFF-state budget of **271 uA** and a bench acceptance of
**<= 300 uA**. That budget **omitted the two LM5116 UVLO dividers**, which are
the largest term in it:

* `R6 + R7` (49.9k + 6.98k = **56.88 kOhm**) sits **directly across VIN** on
  buck-A, and `R15 + R16` does the same on buck-C.
* **SW1 gates ENABLE, not power** (pad 1 = T1 -> GND, pad 2 = COM -> ENKILL,
  pad 3 unconnected; no pole touches VBAT / VBAT_F / VIN), so both strings
  conduct for as long as the XT60 is mated — i.e. the whole of storage.
* `12.6 V / 56 880 Ohm = 221.5 uA` **each = 443.0 uA**, absent from the budget.

**Corrected: ~714 uA typ, 744 uA worst case.** A good board reads **more than
twice** the old threshold. `<= 300 uA` was a gate that **could not pass**, which
is the same defect class as a gate that cannot fail — and it would have sent a
correct board back for rework. Storage life on a 3S 5000 mAh pack is
**~292 days to flat / ~233 days to the 20 % LiPo floor**, not the 769 / 615 days
271 uA implied. Full derivation in `03_src/rules/power_tree.yaml`.

**Where 1.00 mA comes from** — it has to clear worst-case-good *and* still catch
the failure Q6 exists for (a pack LED that is not gated off):

    worst-case GOOD (countable, 12.6 V, +-1% resistors)          =  744 uA
    weakest possible BAD (Q8 failed, LED lit, at the WEAKEST
      corner VIN 9.0 V / Vf 2.4 V: 515.5 baseline + 945.6 LED)   = 1461 uA
    sqrt(744 x 1461) = 1042 uA  ->  1.00 mA is the round number nearest
    the split: 1.34x above worst-good, 1.46x below weakest-bad.
    At the NOMINAL corner a failed board reads 714 + 1504 = 2218 uA = 2.2x.

**Why there is an INDETERMINATE band and not just a number.** Two terms are
named in the budget and **not bounded by anything on file**: the D2/R1 zener
gate-clamp leg (0-12 uA, but the zener's microamp-region V-I is not in its
part.yaml) and **C1/C2 polymer leakage** (`KNM2100UF35V149EC0055/part.yaml` has
no leakage entry at all). The 256 uA between 744 uA and 1.00 mA is the stated
allowance for them — an allowance, not slack.

* **<= 1.00 mA — PASS.** Record the number and the ambient.
* **1.00-1.45 mA — INDETERMINATE.** The pack LED **cannot** produce a reading in
  this band on its own; its weakest corner alone takes the board to ~1.46 mA.
  **Discriminate:** lift or short D8 and re-measure. If the reading does not
  move, the excess is C1/C2 leakage or the zener leg — record it, and it becomes
  the measured bound those two terms have never had.
* **>= 1.45 mA — FAIL.** Q8 is leaking, or ENKILL is not fully low. **An ungated
  pack LED draws 1.504 mA typ and flattens a 3S 5000 mAh pack in ~117 days.**

This gate — not the budget line — is what qualifies the number. **Nothing on
this board has ever MEASURED the OFF-state draw**, and the Q8 leakage figure it
leans on is a 25 C datasheet maximum, while MOSFET leakage climbs roughly an
order of magnitude per 40-50 C. That is why the ambient is recorded with the
reading.

### Q9 in plain words: as shipped, U12 is operated above its rated standoff

Surfaced by the v1.8 zero-context pin review and carried forward unchanged.

**R42 ships UNPOPULATED, so in the as-released configuration the USBLC6-2SC6 (U12)
sits on VBUSC at 5.352 V nominal / 5.479 V no-load — roughly 100-230 mV ABOVE its
5.25 V V_RWM, continuously.** It is **below breakdown** (V_BR min 6.0 V), so the
failure mode is **elevated leakage, not damage** — but it is operation above a
datasheet rating on the configuration that ships, and Q9 closes it with a
measurement instead of an assumption. Fitting R42 (supplied loose) removes
essentially all of the exceedance at a cost of 102 mV of delivery margin.
Populating it by default is a **next-revision design decision**: it would put
R42 on the CPL and change the fab payload.

## 5. Honest limitations — read before deploying

- **NOTHING ON THIS BOARD PROTECTS THE PI FROM A SUSTAINED OVER-VOLTAGE.** A TVS
  clamps transients, not a stuck regulator. Worst-case operating **5.479 V**, Pi 4
  absolute maximum **6.00 V**, U12 guaranteed non-conduction floor **6.00 V**, D5
  breakdown **minimum 6.67 V**. **D5 cannot protect the Pi**, and no TVS that also
  clears a 5.479 V operating rail could. **Do not "fix" this by reselecting D5**;
  the part does not exist (ADR-0003 has the catalog search). The escalation is an
  **active OVP at ~5.6-5.7 V — a disconnect or crowbar, not a different TVS.**
- **WHICH 5.25 V APPLIES WHERE** (adjudicated v1.9; DETAIL_DESIGN sec.4). The
  no-load all-tolerance corners are 5VA **5.273 V** and 5VC **5.479 V**.
  * 5VA's 5.273 V is **+23 mV over USB 2.0 §7.2.1's 4.75-5.25 V** downstream-port
    window. Real, small, no-load-only.
  * 5VC's 5.479 V is **INSIDE** USB Type-C `vSafe5V` (4.75-5.5 V for a source) by
    21 mV — a Type-C source is *permitted* 5.5 V, so this is NOT a port-spec
    violation.
  * But 5.479 V IS **+229 mV above the Raspberry Pi 4's own recommended input
    maximum** (5.0 V +-5 %), while staying **521 mV below** its 6.00 V absolute
    maximum. That is the honest statement: a supervised-prototype posture,
    consistent with ADR-0002's best-effort OV story, and exactly what **R42**
    (DNP, shipped loose) and gate **Q9** exist to retire if the bench says so.
- **`LEDS DARK = SWITCH OFF` / `PACK STILL LIVE AT XT60`** is on the silk for a
  reason: SW1 switches **ENABLE**, not power. **The pack drains at ~714 uA
  whenever the XT60 is mated** — ~292 days to flat on a 3S 5000 mAh pack,
  ~233 days to the 20 % LiPo floor. **Unplug the XT60 for long-term storage;
  the switch is not a disconnect.**
- **Not USB-PD, not USB-C compliant as a generic source.** Pi-dedicated.
- **Protected 3S pack + balance charger ONLY.**

## 6. Ampacity — what A-AMP measured, and the one item it did not clear at dT 10 C

`rules_audit.py` A-AMP was fixed on 2026-07-27 (it had been silently unable to
read any current declaration carrying a qualifier — "7 A worst case", "6 A / 5 A"
— and so graded 3 of this board's 10 net classes). It now grades **10/10**. Four
classes were re-declared `pour_fed:` with evidence MEASURED on this board with
pcbnew (narrowest summed zone cross-section along each power path, every copper
layer the net pours on summed because they are via-bonded):

| class | current | narrowest measured pour cross-section | IPC-2221 needs | margin |
|---|---|---|---|---|
| PWR_IN | 7 A | **8.750 mm** (VBAT F.Cu, J1->F1); VIN 38.400 mm on the In2 plane | 4.399 mm | 1.99x |
| SWITCH_NODE | 7 A | **6.050 mm** (SW_A, B.Cu 4.800 + F.Cu 1.250, Q2->L1) | 4.399 mm | 1.38x |
| PWR_RAIL | 6 A / 5 A | **9.300 mm** (PMID, Q6->F2); 5VA 27.450 mm to the farthest port | 3.556 / 2.765 mm | 2.62x |
| GND_RET | return | 25507.56 mm2 of pour across F.Cu/B.Cu/In1.Cu | exempt | — |

Two classes are **NOT** pour-fed and are not declared so:

* **GATE** is 100 % routed track (zero zone copper on all six nets). It was
  failing because "~2 A pk" was being read as 2 A continuous — a 48.4 C rise on
  0.300 mm. A gate net carries 2 A for the switching edge and nothing between:
  Qg <= 76 nC (from the design's own C_HB = 1 uF at <<1 % droop), fsw 250 kHz,
  duty 1.9 %, **I_rms = 0.276 A**, which wants 0.051 mm against the 0.300 mm
  enforced. **5.9x, dT 0.54 C.**
* **VBUS is genuinely track-fed and this is the one number to keep an eye on.**
  Measured: the TPS2557 OUT pads (U3.6/7, U4.6/7, U5.6/7) touch **no pour at
  all**; each port reaches its pour through **one routed 0.800 mm B.Cu track,
  13.554 mm long, of which 8.810 mm is standalone copper**. The design budget
  (DETAIL_DESIGN sec.3) is **2 A continuous / 2.5 A burst** per port, and it is
  self-consistent — 3 x 2 A = 6 A = buck-A's declared `iout_max_A`.
  * at **2.0 A continuous**: 0.800 mm needs 0.781 mm -> **PASS, dT 9.6 C**
  * at **2.5 A burst**: **dT 16.0 C** on that 8.810 mm, which is over the house
    dT of 10 C.
  * at the **HARDWARE CEILING of 2.72 A** (below): wants **1.132 mm**,
    **dT 19.4 C**.
  Both numbers are stated so you can disagree with the judgement rather than
  rediscover the geometry. **Bench gate Q4b measures it.**

**2 A AND 2.5 A ARE LOAD BUDGETS. THE ENFORCED CEILING IS 2.72 A** — added
v1.9 (fix-lens P2-5), because the number **appeared nowhere** and the class read
as though something limited a port to 2.5 A. Nothing does. `R20/R21/R22 =
36.5 kOhm` gives `I_OS(min) = 127981/36.5^1.0708 =` **2717 mA**, and the TPS2557
is guaranteed **not to limit below** that, so **2.72 A is what a port can carry
indefinitely**. Three ports at the ceiling is **8.16 A** on a rail budgeted at
6 A — still below buck-A's 11.0 A valley limit (~10.5 A corrected for the
current-sense error, DETAIL_DESIGN sec.2.5a), so **nothing intervenes**. The
case is reachable and it is survivable: L1 I_rms 10 A / I_sat 15.2 A OK;
RS1 `8.16^2 x 10 mOhm` = **0.67 W** in a 1 W 2512 OK; F1 ~7.2 A of a 10 A blade
OK. What it costs is the 19.4 C above. **A future revision widening that feed
sizes it on 2.72 A (~1.15 mm), not on the 2.5 A figure (1.10 mm)** — there is
room on B.Cu, and the 0.500 mm scoped floor near the VSON pins is a different,
pitch-bound segment.

## REPRODUCIBILITY — a DECLARED, MEASURED LIMITATION

This release rebuilds from source to a **FUNCTIONALLY IDENTICAL** board but not a
**byte-identical** one. The generator mints fresh random UUIDs, KiCad serialises
footprints in UUID order, the zone filler therefore walks zones in a different
order, and Clipper tessellates pour boundaries differently; island rescue keys
off those islands and inherits it. Measured across three from-source
regenerations at v1.8: footprints, tracks, total track length, zones, pads and
nets all IDENTICAL; via count 292 / 294 / 293, the entire delta additive
island-rescue bonding.

**What you order is the STAGED ARTIFACT in `fab/`** — fixed, hashed in
`MANIFEST.txt`, and verified. The check that decides whether the variance can
harm the board is stranded copper, which **DRC cannot answer**: a floating
SAME-NET island is not "unconnected" in the netlist sense. That check is in
`verification/` for this release's own bytes.

A deterministic-UUID fix is a fleet task in progress. This is canon M3 honoured
in its durable form rather than pretended.

## 7. Fixed since v1.5 — the two "next-rev" items its own review raised

- **B2** — "the 5 A USB-C path crosses Q6 -> F2 through TWO 0.30 mm vias in
  series, with no redundancy." **Fixed:** PMID now carries **13** vias.
- **B3** — "J5's four VBUS contacts are unequally fed." **Fixed:** **3 vias per
  VBUS contact pair**; VBUSC total 5 -> **15**.

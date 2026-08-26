# Changelog — smc0985-cooksense (MAIN board: cooksense)

Multi-board project (ADR-0007): per-board releases `07_releases/cooksense-v*`.
INTERPOSER (Board C) is deferred (coupon-gated) and has no release yet.

---

## cooksense-v1.7-2026-07-30 — **SEALED.** The relay land is fixed, the board has a DECLARED AMBIENT for the first time, and the part that binds it is not the one anyone was arguing about.

**A REAL BOARD REVISION, the first since v1.3.** `source/cooksense.kicad_pcb` md5
`9f4fd5fae810f40a52b1035df727243c`; v1.3–v1.6 all carried
`420445b5141dd1111eccab038c68511b`. Gerbers, drills, BOM and CPL all move.

**WHAT IT FIXES vs v1.6** — the `pinout12` → `pinout13` reed-relay land (the
defect that makes all six earlier sealed releases DO-NOT-ORDER); the eFuse OVLO
divider (100k/15k = 9.200 V nominal, above BOTH the 5.25 V nuisance-trip bound
and the SMBJ5.0A's 6.40 V minimum breakdown → 100k/26.1k = 5.798 V); `R_OPENT`
62 kΩ (`C37825`); the supply specified rather than advised (D11/ADR-0021); and
the 3V3 rail's declared load, thermal ceiling and series resistance all
re-derived (ADR-0026/0027/0028).

**WHAT IS NEW AND HAS NO PRECEDENT IN ANY EARLIER RELEASE — A DECLARED OPERATING
AMBIENT.** User decision 2026-07-30, ADR-0029 + ADR-0030, BRIEF D12:

    DECLARED OPERATING AMBIENT   Ta = 65 C    SURVIVE CORNER   Ta = 75 C
    MANDATORY BENCH GATE B1-B6 BEFORE USE ABOVE BENCH CONDITIONS (ORDER_README §7b)

At 65 °C the `U_LDO` junction margin is **17.92 °C citable / 13.3…16.4 °C**
carrying the board's other 0.958 W; at 75 °C the same two forms are **7.92 and
3.3…6.4**. **The 7.92 °C earlier v1.7 staging published was wrong regardless of
the envelope** — the arithmetic was right and the FORM omitted a term worth
20–59 % of itself. `pdiss_max_mw` is deliberately HELD at the 75 °C derating
(497 mW) so that narrowing a declaration cannot relax a gate.

**AND THE PART THAT ACTUALLY BINDS IS THE REED RELAY, NOT THE LDO** (ADR-0030,
found independently by THREE of four fresh-context lenses). `DIP05-1A72-13L` is
rated **−20…+70 °C** and twelve are fitted — the UNIQUE minimum across all 47
dossiers, 15 °C tighter than the `F1` figure ADR-0028/0029 had named. **65 °C is
the only rung on the BRIEF's ladder that fits them at all**, with 5.00 °C of
margin; 75 °C was never inside the rating. Consequently ADR-0029's "passing
B1–B6 may reopen 75 °C" is **WITHDRAWN**: B1–B6 can reopen at most 65 → 70 °C,
and above 70 °C needs a BOM change, i.e. a new board revision. §7b item B5 is
also corrected — the two SN74HC238 1-of-8 decoders permit **four** simultaneous
coils, not twelve, so "all 12 energised" was a state the hardware forbids.

**REVIEWS — four fresh-context lenses, four distinct filenames, all re-gated
against this archive because the envelope change is MATERIAL:**

    redteam_topology  design_verdict: SOUND   order_verdict: BLOCKED-SOURCING   0 P0
    redteam_layout    design_verdict: SOUND   order_verdict: BLOCKED-SOURCING   0 P0
    pin_review        design_verdict: SOUND   order_verdict: BLOCKED-SOURCING   0 FAIL (243/243)
    render_review     design_verdict: SOUND   order_verdict: BLOCKED-SOURCING   0 P0

**⛔ SEALED IS NOT ORDERABLE.** `SOURCING: BLOCKED-1` — `C265111` (JST
SM08B-GHS-TB, `J_THERM_A`/`J_THERM_B`) reads **stock 5 against minPurchaseNum
21**, measured 2026-07-30 21:29 local with both controls. Five readings in 48 h
(0→5→0→5→5) and **MOQ 21 at every one**: the blocker has never been the stock.
Watch item: `C587657` (Molex `J_PWR`) 130→80→70→70, single-source, no drop-in
fallback. Re-measure on order day.

Gates, UNPIPED: DRC 0/0/0 exit 0 with `--exit-code-violations` (both halves) ·
standalone-archive DRC 0/0/0 exit 0 outside the repo · ERC 0 errors / 411
warnings · policy_audit FAIL=0 · E-TOPO / E-INV 168/168 / E-ADR 12/12 / M-BOUND /
G-ORPHAN 315/315 / A-POP / A-BODY 206/206 / F-LEGIBLE / M-DEPEND / M4 all exit 0.
**M4 (`waiver_provenance`) grades this board explicitly for the first time**
after skills commit `1b70262a`: PASS, 16 waivers graded, all OWED-for-evidence
under a 22 ceiling — named debt, not a green verdict.

---

# ⛔ DO-NOT-ORDER — ALL SIX SEALED cooksense RELEASES: v1.0, v1.1, v1.3, v1.4, v1.5, v1.6

## THE SCOPE OF THIS BANNER, IN ONE SENTENCE EACH — read all four lines

1. **EVERY cooksense release that has ever been SEALED is DO-NOT-ORDER.** There
   are exactly six of them in `07_releases/` — **v1.0, v1.1, v1.3, v1.4, v1.5,
   v1.6** — and this banner covers all six with no exceptions. **THERE IS NO
   GOOD SEALED ONE.**
2. **`v1.7` IS NOT ON THAT LIST BECAUSE IT FIXES THE DEFECT.** ⚠️ **UPDATED
   2026-07-30: `cooksense-v1.7-2026-07-30` IS NOW SEALED.** It carries the
   correct `pinout13` relay land and is the first cooksense release that is not
   DO-NOT-ORDER by construction. **It is SEALED and it is NOT ORDERABLE TODAY** —
   one BOM line (`C265111`, stock 5 / MOQ 21) cannot be bought at any quantity.
   Those are two different statements; see its MANIFEST and ORDER_README §5-0.
3. **`interposer` IS A DIFFERENT BOARD AND IS COMPLETELY UNAFFECTED.**
   `interposer-v1.1-2026-07-27` **remains ORDERABLE.** Nothing in this banner
   touches it.
4. **If you are looking for a cooksense board to build today, there is not one.**

**Why the six are DO-NOT-ORDER:** they carry the **pin-out-12** reed-relay land
(`Relay_StandexDIP_1A_pinout12`) and the part that exists is pin-out **13**. This
is not a paperwork verdict — the key-matrix relay array as drawn cannot work. Do
not fabricate or hand-build a cooksense board from any sealed release.

> ## STATUS UPDATE 2026-07-30 (LATEST) — **THE SOURCING BLOCKER WAS REMOVED AND THE SEAL STILL DID NOT HAPPEN. NINTH DECLINE, AND THE FIRST ONE THAT FOUND SOMETHING.**
>
> Commit `217ea175` split the release verdict into `design_verdict` and
> `order_verdict`, so the sourcing red (`C265111`, stock 5 / MOQ 21) stopped
> being able to veto the design claim. The topology lens, re-gated fresh-context,
> returned the sentence eight passes had had no field for:
> **`design_verdict: SOUND` + `order_verdict: BLOCKED-SOURCING`.**
>
> **The LAYOUT lens was re-gated too — and THAT is where the seal died.** It had
> to be re-asked for a purely bookkeeping reason (its old legacy `verdict: ORDER`
> retrofits to `order_verdict: ORDER`, which M-REV refuses on a release measured
> `SOURCING: BLOCKED`). Nobody suspected its design content. It came back
> **`design_verdict: DEFECTIVE` with two P0s**, both re-measured independently
> before the stand-down and both CONFIRMED:
>
> 1. **The LDO is graded at 0.30 A while `power_tree.yaml` declares 0.40 A of
>    switched sensor rails downstream of it.** Measured on the board: all four
>    `AO3401A` load-switch SOURCE pads sit on net `3V3`. Declared load is 0.70 A;
>    the graded 0.3 is 43 % of it. At the file's own constants PD becomes 120 %
>    of the package ceiling and dropout headroom goes to −15 mV.
> 2. **`pdiss_max_mw: 1200` is a 25 °C figure used with no ambient term**, on a
>    board the BRIEF places in a 50–75 °C enclosure. At the 75 °C hard limit the
>    ceiling is 0.600 W — under the release's own 615 mW. And the file's θ_JA
>    justification ("the tab is flooded with 3V3 copper") is refuted: **the only
>    `3V3` zone on the board is on `In2.Cu`; there is no F.Cu `3V3` zone at all.**
>
> **Neither is copper.** Both are declarations in `power_tree.yaml`, and one bench
> measurement at bring-up retires both. But a P0 blocks a release, so v1.7 stays
> in `06_build/staging/`, `07_releases/` was left untouched, and **v1.6 got no
> `SUPERSEDED.md` because nothing superseded it.**
>
> Everything else in the ninth pass measured green and is recorded in the
> candidate's `verification/build_gates.md`: DRC **0/0/0** (and **0/0/0 again on
> `source/` copied outside the repository** — the archive now stands alone, which
> it did not at the start of the pass), `policy_audit` FAIL=0, ERC 0 errors,
> E-INV 167/167, `jlc_twin` exit 0 with 206/206 bodies, A-RENDER exit 0.

> ### STATUS UPDATE 2026-07-30 — THE FRESH FOUR-LENS BATTERY RAN ON THE REAL BOARD. **THREE ORDER, ONE DO-NOT-ORDER. v1.7 STILL DOES NOT SEAL, AND THE BLOCKER IS A PART YOU CANNOT BUY.**
>
> **The previous statement of this banner is WITHDRAWN as STALE, not as wrong.**
> It said the fresh battery returned *"DO-NOT-ORDER / DO-NOT-ORDER /
> DO-NOT-ORDER / FAIL"*. That was the **2026-07-29T18:04** battery, and it graded
> a board that no longer exists: `J_DOOR` was still in the netlist, the SE-corner
> silk ownership fix had not landed, the four plane-pad bonds had not been made
> and the fab set was `fab_v21`. Those four verdicts are HISTORY.
>
> **The 2026-07-30 battery graded the current candidate** — board md5
> `9f4fd5fae810f40a52b1035df727243c`, `fab_v22`, PDFs/3D/bare renders regenerated
> the same day — with `08_reviews/`, the journals, this CHANGELOG and the STATUS
> beacon **denied to every lens**, so no lens could grade its own or a
> predecessor's verdict:
>
> | lens | verdict |
> |---|---|
> | topology / protection / ratings | **DO-NOT-ORDER** |
> | layout / thermal / power-integrity | ORDER |
> | pin review (53/53 dossiers, 47 against a datasheet figure) | ORDER |
> | render review | ORDER |
>
> **THE ONE P0 IS NOT COPPER — IT IS A CATALOGUE.** `J_THERM_A`/`J_THERM_B`
> specify `C265111` (SM08B-GHS-TB). LCSC reads **stock 5** (it read **0** on
> 2026-07-29 — the part is restocking, not discontinued); `build_quantity` is 5
> and the part is ×2 per board, so **10 pieces are needed** and
> `jlc_stock_check` exits 1. **The release cannot be PLACED as it stands**, and
> "orderable" is the only claim a seal makes that matters. All three remedies —
> re-query at order time, substitute the land-pattern-measured `C42376901` whose
> **plug-mate compatibility is explicitly unverified**, or declare the refs
> not-assembled and hand-fit — need a decision or a revision that is the user's,
> not the design's.
>
> **THE BOARD ITSELF CAME BACK SOUND, and that is worth saying plainly.** DRC
> **0/0/0**; `policy_audit` **FAIL=0, PASS=28, WAIVED=6, HUMAN=6**; E-INV
> **167/167**; `jlc_twin` exit 0 with **208/208** bodies. The topology lens
> hunted specifically for a consistently-wrong-together artifact set and did not
> find one. The layout lens re-derived the headline safety property with its own
> polygon engine, never running the DRU: **the 6 mm keypad-contact barrier holds
> at 6.3100 mm with ZERO domain crossings**, and it checked the rule's
> `J_KEY_MATRIX` exemption rather than trusting it. The pin lens graded 53/53
> dossiers with **no FAIL**, confirming the new TBD62083AFWG coil driver maps
> 18/18 and that the twelve reed coil and contact domains are provably disjoint.
>
> **24 P1s and 6 P2s are recorded in `08_reviews/DISPOSITIONS.md`** with their
> verification and disposition, including three that must close before ANY seal:
> the release-identity mismatch (the archive says v1.7, the `.tsx` says v1.8 in
> 12 places, the artifacts say `rev "dev"`), the commission fact-lock still
> naming the superseded `DIP05-1A72-12L`, and the missing MANIFEST.

> ## STATUS UPDATE 2026-07-29 (fifth) — THE SCOPE DECISION LANDED. **ALL THREE ORDER-BLOCKERS ARE NOW CLOSED IN SOURCE; v1.8 IS STILL NOT SEALED AND THE DRC GATE IS NOT YET 0/0/0.**
>
> **Nothing in `07_releases/` changed. v1.0-v1.6 remain DO-NOT-ORDER, v1.7 remains
> an unsealed candidate, and v1.8 is a work-in-progress. If you are looking for a
> cooksense board to build, the answer today is still that there is not one.**
>
> ### CLOSED — the THIRD blocker (the SE-corner label-ownership P0), and MEASURED
>
> `J_ISOLOOP` is the NOT-SELV **30 V** isolated contactor loop and its designator
> was printed 0.141 mm from a JST-GH **humidity-sensor** header. The v1.8 pass
> proved no silk-only fix existed: all four directions out of its courtyard were
> closed, and the one candidate pocket lost to `J_DOOR`'s courtyard by 1.100 mm
> against 2.680 mm. **ADR-0025 (accepted) removes `J_DOOR` from the NETLIST** — the
> user has no door signal and never will — and adds `J_ISOLOOP` to the silk pass's
> `OWNERSHIP_FIX` list, which had never contained it, so nothing had ever tried.
> Measured on the rebuilt board by the pass's own VERIFY line:
>
>     J_ISOLOOP  label centre 8.000 mm from own part
>                vs 13.656 mm from J_RH_EXHAUST   (lead +5.656 mm)  -> OWNS ITS LABEL
>
> against a 1.500 mm requirement. The three hazard captions also improved and are
> now all AT the block body (`ISO 30V` 0.085 mm, `NOT SELV` 0.117 mm, pole map
> 0.085 mm) — the earlier claim that `NOT SELV`'s nearest site measured 11.086 mm
> is WITHDRAWN, it was true only while `J_DOOR` held the pocket.
>
> ### THE SCOPE REDUCTION, and it is a BRIEF AMENDMENT stated in full (ADR-0025)
>
> The user has **no access to the appliance's door signal and no E-stop signal**.
> The resolution is deliberately ASYMMETRIC:
>
> * **`J_DOOR` is DELETED from the netlist** with `R_DOORPD`, `R_DOORS`, `D_DOOR`
>   and `R_DOOROKPD`. `BRIEF.md` §3's "Door:" clause is WITHDRAWN. Marking the
>   parts not-assembled would NOT have worked and that was measured: the silk pass
>   has no population concept, so DNP frees zero silk.
> * **`J_ESTOP` STAYS POPULATED**, satisfied by a **REMOVABLE SHORTING PLUG**, so a
>   real E-stop can be fitted later with no copper revision. **THE BOARD DOES NOT
>   FUNCTION WITHOUT THAT PLUG** — with `J_ESTOP` open the board is inert by
>   design, which is correct and is also indistinguishable from a dead board to a
>   technician who has not read this. It is a REQUIRED BUILD STEP.
> * **`J_ESTOP` moves from JST GH-5 to JST SH-3** (`SM03B-SRSS-TB`, `C160403`)
>   because the plug is itself a new hazard: a GH-5 shorting plug bridging circuits
>   1-2 lands on switched-3V3-to-GND on all four sensor-pod housings, a dead short
>   behind a load switch. 1.00 mm pitch appears exactly ONCE on this board, and the
>   sense node sits on **circuit 3** — the one circuit that cannot align in any
>   foreign shroud — so the plug bridges 2-3 and its short cannot be COMPLETED
>   anywhere else. Both mating directions are measured in ADR-0025 D5.
> * **`DOOR_OK` was never a term of `KEY_RELAY_ALLOWED`** (`BRIEF.md`:82 has no door
>   term); its only consumer was the PRESS one-shot's reset. That input now carries
>   **`ESTOP_OK`**, which is what `BRIEF.md`:89's "hardware key-relay inhibit" asks
>   for and the board did not have. **No AND input is tied off permissive.**
>
> ### NOT YET DONE — stated because a banner that overstates is worse than none
>
> The board rebuilds, stage 1b/7 passes, schematic parity is **0**, the netlist
> gate is **22/22** and E-INV is **167/167** (all seven new ADR-0025 asserts
> RED-VERIFIED against the immutable sealed v1.6 netlist). **The DRC gate is NOT
> 0/0/0 yet**: a small number of trapped plane pads need deterministic seed-stub
> bonds, and the fab/assembly battery and the FRESH four-lens review battery have
> not been run. **v1.8 IS NOT SEALED.**

> ## STATUS UPDATE 2026-07-29 (fourth) — TWO OF THE THREE ORDER-BLOCKERS ARE CLOSED IN SOURCE. **v1.8 IS NOT SEALED AND THE THIRD BLOCKER IS STILL OPEN.**
>
> **Nothing in `07_releases/` changed. v1.0-v1.6 remain DO-NOT-ORDER, v1.7 remains
> an unsealed candidate, and v1.8 is a work-in-progress in `03_src/` +
> `03_tscircuit/` + `04_kicad/`. If you are looking for a cooksense board to
> build, the answer today is still that there is not one.**
>
> ### CLOSED — the SAFETY blocker (ADR-0024)
>
> `J_DOOR` pin 4 was `DOOR_RAW`. On the two POD housings, which are the SAME PART
> (`C189896`, physically cross-mateable), pin 4 is `SCL_*`. A cross-plugged SHT45
> pod put its pulled-up clock on the door sense node: **2.705 V** at this board's
> own 2.2 kOhm pull-up value, against an SN74HC14 on 3V3 whose interpolated
> V_T+ MAX is **2.348 V** — a GUARANTEED logic high. **The board read the door
> CLOSED with no door attached, on a cooking appliance's interlock.** Re-derived
> from the netlist it is 1.055 V worse than the review lens reported and crosses
> from "a conforming part MAY read it high" to "does".
>
> **Fixed by removing the path, not by attenuating it**: pin 4 is GND, so all four
> cross-mateable housings now present GND on every pin a pod can source current
> into. All 12 ordered cross-plug pairs are enumerated in ADR-0024 and **zero
> cells remain in which a cross-plug asserts a permission** — ADR-0018's own
> matrix had left four such cells explicitly untouched.
>
> **And the remedy did NOT transfer at its published value.** ADR-0018 closed this
> class on `COIL_EN_IN` with 680 Ohm; at 686.8 Ohm worst case that gives 0.791 V,
> which FAILS the SN74HC14's V_T+(MIN) of **0.700 V** (SCLS085L sec.5.5, the
> V_CC = 2.0 V row — the only bound TI publishes that holds at 3.3 V without
> interpolation) by 91 mV. Its receiver was a 2N7002 with a 1.000 V threshold.
> `R_DOORPD`/`R_ESTOPPD` are **470 Ohm** (C25117), giving 0.591 V, +92 mV.
> A straight carry-across would have looked like the proven fix and would not have
> closed the case.
>
> ### CLOSED — the eFuse input blocker
>
> **`5V_IN`, `5V_FUSED` and `5V_RPP` carried ZERO capacitors** for five releases;
> `C_IN1`/`C_IN2` are both on the OUTPUT. `C_EFIN` 100nF is now on `5V_RPP`
> (SLVSE57C sec.10 Fig.67 / sec.11 Fig.68; Eq.18 names the function — it bounds
> the short-circuit interrupt transient). **The gate that should have caught it was
> addressed to `5V_SELV`, which is not a net on this board**, so P-ADJ could never
> evaluate it and the row read as covered. An unenforceable budget is not a weak
> check; it is a check that cannot fail. Budget re-pointed at `5V_RPP`, and three
> more ghosts on the same dossier (`EN_OVLO_N`/`ILM`/`dVdt`) re-pointed at
> `EF_OVLO`/`EF_ILM`/`EF_DVDT`. Full ghost census, 14 names / 22 rows with a
> disposition each: `03_tscircuit/verification/ghost_net_census.md`.
>
> ### STILL OPEN — label ownership on cross-mateable SAFETY connectors
>
> Not fixed, and not papered over. Measured on the v1.7 board, box-to-courtyard:
> the string `J_ISOLOOP` prints **0.141 mm** from `J_RH_EXHAUST` and 2.719 mm from
> the 30 V terminal it names; `J_ESTOP`'s designator is **0.141 mm from BOTH**
> `J_ESTOP` and `J_DOOR`, an exact tie. Re-derived here: **there is no owned site
> for `J_ISOLOOP`'s designator anywhere on this placement** — east and south are
> the board edge, north is `J_DOOR`'s courtyard, west is `U_OPTO` then
> `J_RH_EXHAUST`, and the generator's own "nearest legal site inf mm away" is
> literally true. The real remedy for the `J_ESTOP`/`J_DOOR` half is **a mechanical
> key** (ADR-0018 decision C applied again), because those two are the same part,
> are cross-mateable, and their transposition de-latches the E-stop — silk cannot
> fix a connector that mates. That is a part change plus an east-column repack, and
> it is written up as the open blocker rather than approximated.
>
> ### Also in this revision
>
> * **The relay count is TWELVE, not thirteen.** Corrected in the three files that
>   said 13: this CHANGELOG, ADR-0023, and `journal/verify_cooksense.md`.
> * `SCLS085L` is COMMITTED with its `sha256` (the v1.7 pin lens graded this
>   dossier an evidence FAIL), and its threshold table is transcribed into an
>   `electrical:` block, because a published safety margin now depends on it.
> * The 2.2 kOhm I2C pull-up codes are PINNED (`C25879`) — not for the bus, but
>   because 2.2 kOhm is the declared worst-case injection value in two ADRs.
> * **E-INV 151/151 -> 180/180, E-ADR 9/9 -> 10/10**, all four new assert families
>   RED-verified (`06_build/proof/einv_red_verification_adr0024.txt`).
> * `node_level` could NOT express the cross-plug outcome assert, and the reason is
>   measured rather than assumed: a resistor's netlist `value` is its resistance,
>   never an LCSC code, so no resistor dossier can resolve as a `contended`
>   aggressor or defender — and a correct pull-down-only safety input has no
>   on-board resistive path to a rail for the `released` form to walk. Three ways
>   to force it were rejected as worse than the gap (ADR-0024, last section). The
>   one-field schema patch is reported upstream.

> ## STATUS UPDATE 2026-07-29 (third) — ALL FOUR P0s CLOSED, THE BATTERY RUN, AND TWO NEW ORDER-BLOCKERS
>
> **The four P0s this board carried for a week are closed. It still does not
> seal, and the reason is now different: the fresh four-lens battery — deferred
> twice while a P0 was open, correctly — was finally run, and all four lenses
> came back negative.** Render **DO-NOT-ORDER** (2 P0), topology
> **DO-NOT-ORDER** (7 P1), layout/thermal **DO-NOT-ORDER** (7 P1, one of them
> order-blocking), pin review **FAIL** (zero pin-map FAILs, two evidence-grade
> FAILs). Full ledger with every number:
> `08_reviews/DISPOSITIONS_v1.7.md`, section 2026-07-29 (third).
>
> ### The two things that block, and neither is fixable after fabrication
>
> 1. **LABEL OWNERSHIP ON CROSS-MATEABLE SAFETY CONNECTORS.** The string
>    `J_ISOLOOP` — the 30 V NOT-SELV terminal's own designator — is printed
>    **0.161 mm from `J_RH_EXHAUST`**, a humidity-sensor header, and 2.739 mm
>    from the terminal it names. `J_ESTOP`'s designator is **0.161 mm from BOTH
>    `J_ESTOP` and `J_DOOR`**, which are the SAME part (C189896) and therefore
>    physically cross-mateable — two of the four such headers are safety
>    inputs. `J_DOOR`'s own designator is nearer `D_DOOR` than J_DOOR. This is
>    the SAME defect v1.7's battery raised as RENDER P0-A and marked FIX
>    REQUIRED; an ownership-aware silk pass landed and demonstrably does not
>    reach these refs — the generator prints `WARN silk ownership ... no owned
>    slot in the 4x84 search` for 56 refs and places them anyway. The cause is
>    PLACEMENT DENSITY in the SE corner, so it is a floorplan change and a
>    re-race, not a silk tweak, and it was deliberately NOT attempted here.
> 2. **NO CAPACITOR ANYWHERE ON THE eFUSE INPUT SIDE.** `5V_IN` / `5V_FUSED` /
>    `5V_RPP` carry **zero** capacitors; `C_IN1` and `C_IN2` are on the eFuse
>    OUTPUT. The layout rule written to hold that cap local is addressed to net
>    **`5V_SELV`, which is not a net on this board** — so the budget has been
>    grading nothing. A missing input capacitor on the protection stage of a
>    mains-adjacent board cannot be added to a fabricated panel.
>
> ### What DID close, with the measurement
>
> - **The comb slots were a real P0 and are FIXED.** JLCPCB publishes
>   **"Min. Non-Plated Slots: 1.0mm"**; the twelve unplated isolation slots were
>   **0.600 mm** — 40% under the fabricator's own floor, sighted four times
>   across four sessions and carried each time. Widened to **1.000 mm** after
>   measuring it free: nearest copper 2.5500 mm at worst, four layers, pours
>   filled, against the 0.200 mm JLC asks. Creepage only improves — a wider void
>   lengthens the path around it. DRC **0 / 0 / 0**.
> - **The reed-coil pull-in margin is now a MACHINE CHECK, not a table in an
>   ADR.** Eleven `node_level` asserts, one per DMOS-driven reed; **E-INV
>   140/140 -> 151/151**; RED-verified in place at both Darlington corners
>   (0.714 V typical and 0.895 V worst case against a 0.540 V pull-in budget,
>   11 FAILs each). Landing it caught that ten of the eleven would have graded
>   at the optimistic 25 C resistance.
> - **The silk printed `GND_ISO ONLY` — a net that does not exist** (`grep -c`
>   = 0). So did `parity_padmap.txt`, which is why a parity gate has FAILed
>   1/169 here and 1/161 on sealed v1.6. The BOARD was right both times: the
>   isolated keypad connector's shell tabs are unbonded BY DESIGN, measured
>   19.407 mm from the nearest SELV copper. A sweep then found **10 of 123 net
>   names referenced by this board's rule files and dossiers do not exist in the
>   netlist** — 8% of its layout budgets grade nothing.
> - **A 30 V pole legend was printed 0.161 mm from a sensor connector** and is
>   now refused rather than misplaced.
> - **A-RENDER had never run on this board.** Its first run FAILED twice; both
>   were artifacts of an 8.34 px/mm render, proven by re-measuring at 15.40
>   px/mm (U_LDO 1.248 -> 0.111 mm).
>
> `07_releases/` was NEVER TOUCHED. The candidate lived in
> `06_build/staging/cooksense-v1.7/` for the whole pass.
>
> ## STATUS UPDATE 2026-07-29 (second) — THREE P0s CLOSED, A FOURTH FOUND, v1.7 STILL NOT SEALED
>
> **v1.0 through v1.6 remain DO-NOT-ORDER and that does not change.** Every one
> of them carries the pin-out-**12** land described below. There is no sealed
> release of this board that can be built.
>
> **v1.7 WILL BE THE FIRST RELEASE WITH A CORRECT RELAY LAND.** The part is
> `DIP05-1A72-`**`13L`** (pin-out CODE 13, LCSC C1524853) on
> `03_src/lib/cooksense.pretty/Relay_StandexDIP_1A_pinout13.kicad_mod`; the
> pinout12 file is DELETED. Three independent zero-context lenses re-rendered
> datasheet p.3 at 400 dpi and confirmed sub-figure 13 has FOUR leads (contact
> 14↔8 on one row, coil 2↔6 on the other, rows 7.62 mm apart); the netlist
> confirms the coil and contact node sets are **DISJOINT** — minimum
> coil-to-contact pad distance **8.032 mm** over all 48 pads — and the land is
> CHIRAL, so a relay cannot be seated backwards. The ≥6.0 mm keypad↔SELV
> barrier was measured independently WITH POURS FILLED at **6.2200 mm**.
> ADR-0002's isolation claim is TRUE under code 13, where under code 12 it was
> false. **That defect is closed and is not revisited.**
>
> ### The three blockers this session closed
>
> 1. **The `U_EXP` eFuse fault readback was DEAD** (found by two lenses with no
>    shared method). The divider v1.7 added was sized as if `EFUSE_FLT_N` were a
>    stiff 5 V source; its only source of high is `R_PG` 100 kΩ, so the real
>    ratio was 22/132 and the pin sat at **0.833 V** against V_IH(min)
>    **2.640 V** — the indeterminate band. **ADR-0022**: `R_PG`'s pull-up moves
>    to **3V3** and both divider resistors are DELETED. The node now idles at
>    **3.300 V**, inside the MCP23017's 3.6 V abs-max AND above V_IH, with two
>    fewer parts. Verified by the gate, not by argument: the `node_level`
>    invariant went RED→GREEN and five new asserts were RED-verified.
>    *`TP_PGOOD`'s v1.7 rationale — "the instrument must see the real node" —
>    was FALSE AS BUILT: the divider loaded the 100 kΩ pull-up, so the "raw"
>    node a probe would have touched rested at 1.212 V, not 5 V. Recorded as
>    refuted, not deleted.*
> 2. **`J_ISOLOOP`, the NOT-SELV 30 V terminal, had no artwork.** It now carries
>    **`ISO 30V` printed 0.085 mm from the block body** and `NOT SELV` at
>    7.892 mm, both at h 0.600 / stroke 0.150. *The recorded "SE corner is
>    saturated, nearest site 33.6 mm" claim did not reproduce — and neither did
>    the 6.46 mm re-run that superseded it (that site is blocked by `U_OPTO`'s
>    and `J_RH_EXHAUST`'s bodies; the clear band there is 0.87 mm and a 0.45 mm
>    text needs 0.92 mm). What blocked the corner was never geometry: it was a
>    0402's designator parked there first-come-first-served.* A per-pole legend
>    at the terminal is genuinely impossible — the pads sit at the CENTRE of the
>    KF350 body in x, so anything either side of a pole is under the moulding
>    once it is fitted — so the pole map rides the north-stack caption as
>    `POLES 1=C 2=LOOP 3=LOOP 4=E`.
> 3. **Six safety designators printed at 0.130 mm stroke**, thinner than the
>    other 243 texts, emitted by v1.7's own silk-repair pass. Fixed at the root:
>    every silk stroke is now `0.25 × height` (KiCad's own clamp) and every
>    SAFETY text is h 0.600 / stroke 0.150 — JLC's published floor. **250 texts
>    re-measured: 0 below the 0.1125 mm tier floor, 0 storing a stroke KiCad
>    would clamp away, 11/11 safety texts at 0.600/0.150.** Three waivers that
>    misstated this were CORRECTED in place with the replacement measurement.
>
> ### Why there is still no seal: THE REED COILS MAY NOT CLOSE WHEN HOT
>
> The pull-in margin was computed for the first time in this tree, and it is
> **NEGATIVE inside the board's own −20…+70 °C envelope.** The ULN2803A
> datasheet is now committed; its V_CE(sat) at the ~7 mA coil current is
> 0.67 V typ. With `V_PI(T) = 3.500 × (1 + 0.004 × (T − 20))` and the
> `5V_KEY_RELAY` floor of 4.740 V:
>
> | T | V_PI | margin (typ 0.67 V) | margin (worst 0.88 V) |
> |---|---|---|---|
> | −20 °C | 2.940 V | +1.130 V | +0.920 V |
> | +25 °C | 3.570 V | +0.500 V | +0.290 V |
> | +50 °C | 3.920 V | +0.150 V | **−0.060 V** |
> | +70 °C | 4.200 V | **−0.130 V** | **−0.340 V** |
>
> The ampere-turn view agrees: must-operate is 7.00 mA and delivered current
> falls to **6.81 mA at +70 °C**. **−20 °C is comfortable, so a bench test at
> room temperature will not find this.** `K_STOP` is the one relay not exposed
> (a 2N7002, not a Darlington: +0.454 V at +70 °C).
>
> **Twelve reed relays on a cooking appliance are not guaranteed to close hot.
> Until that is fixed, there is still nothing to order.** The remedy — raise the
> coil rail, replace the Darlington with a MOSFET array, or narrow the declared
> envelope — is a topology decision and is not made unilaterally.
>
> ### Also new, and a real order blocker in its own right
>
> **`C506653` (MCP23017-E/SS, `U_EXP`) reads ZERO LCSC stock** as of
> 2026-07-29. The same gate read 56/56 PASS the previous session, so this is a
> live change, not an inherited number. 55/56 coded BOM lines clear the 5×
> floor; this one has nothing.
>
> ### Copper moved. Real numbers.
>
> The board is a full from-source rebuild with a fresh KRT race, not a patch:
> **243 → 241 refdes** (`R_FLTDIVT`, `R_FLTDIVB` deleted, and the net
> `EFUSE_FLT_DIV` with them); `R_PG` pad 2 moves off the `5V_PROTECTED` pour
> onto `3V3`; 17 silk designators relocated and 218 re-stroked; four new
> deterministic plane-bond vias (`Q_SWDRVB.2`, `U_TC.5`, `U_LATCHB.5`,
> `C_LATCHB.1`) and one new routing reservation for the `U_TC.8` stub.
> Measured after the rebuild: **DRC 0 violations / 0 unconnected / 0 schematic
> parity**, E-INV 136/136, E-ADR 9/9, E-TOPO PASS, audit_board PASS
> (I-ISO 6.22 mm), placement_gates PASS, count_parity 4/4 over 241,
> A-ROT 208/208, F-LEGIBLE 59/59, jlc_twin 210/210 bodies mounted,
> ERC 0 errors / 417 warnings.
>
> `07_releases/` is UNTOUCHED. The staged archive lives at
> `06_build/staging/cooksense-v1.7/`, where it cannot make itself the live
> release.

## The defect
`03_src/lib/cooksense.pretty/Relay_StandexDIP_1A_pinout12.kicad_mod` carries
**4 pads** at DIP positions 1/7/8/14. Standex DIP-series datasheet (Version 03,
01 Aug 2025) p.3 "Pin-Out (Top View)" **sub-figure 12** — re-rendered at 300 dpi
and read directly — shows **8 leads and 4 electrical nodes**:

| node | DIP pins |
|---|---|
| CONTACT_A | **1 ↔ 14** (tied by an internal vertical conductor) |
| CONTACT_B | **7 ↔ 8** (tied) |
| COIL_A | **2 ↔ 13** (tied; junction dot on the figure) |
| COIL_B | 6 |
| — | 9 = bare circle, mechanical lead, no internal connection |

The previous map (4 leads: 1 COIL_A / 7 COIL_B / 8 CONTACT_B / 14 CONTACT_A)
describes **sub-figure 13**, the genuinely-4-lead variant at 14/8/2/6. The wrong
sub-figure was read.

## Measured consequence, cross-checked against `06_build/netlists/cooksense.net`
| pad | DIP | true node | net |
|---|---|---|---|
| 1 | 1 | contact A | `5V_KEY_RELAY` |
| 4 | 14 | contact A — **same node** | `U_SEL_BUS` |
| 2 | 7 | contact B | `COIL_U1_N` |
| 3 | 8 | contact B — **same node** | `KP_U1` |

- `5V_KEY_RELAY` is **hard-shorted to the select bus**. On `K_STOP` this puts
  `5V_STOP` onto `KP_U6`, a membrane-matrix line that leaves the board.
- **Every ULN2803 output is shorted to its keypad line.**
- **The coil has no holes at all** (DIP 2/6/9/13) — the part cannot be seated and
  is never energised. The array is non-functional.
- ×12 relays: `K_U1..U6`, `K_D1..D4`, `K_PRESS`, `K_STOP`.

## Why this is an architecture question, not a footprint swap
Coil and contact **interleave along the package** — CONTACT_A at 1, COIL_A at 2,
COIL_B at 6, CONTACT_B at 7. Coil-to-contact separation on the land is therefore
**2.54 mm between adjacent pins**, not the **7.62 mm row separation** ADR-0002
and the part's `layout:` block both assert. Every pour-relief and routing rule
derived from "the isolation boundary runs between the rows" is unsupported — and
so is the shape of the board, since the v1.1 isolation-comb repack (contact
columns facing shared keypad pockets, coil-coil gaps carrying logic, 12 milled
slots, 25 DRC deny rects) was designed around that boundary.

Fixing the footprint alone would clear the short and leave the isolation
rationale void — a board that passes every gate while its central geometric
argument is false. That is a worse defect than the one it replaces.

## Mitigating, and the reason no built board was ever wrong at the factory
The relays are `not_on_assembly_bom` (hand-soldered, `not_in_catalog`) and carry
`exclude_from_pos_files`, so **JLC never placed them** and no CPL row was ever
wrong. The defect lands on the PCB **holes** and the **netlist**, i.e. at hand
assembly and bring-up on the mains-switching stage.

## Three routes, none of them mine to choose
1. Re-author the land to sub-figure 12 (8 pads) **and re-derive the isolation
   comb** against the true 2.54 mm boundary — a placement/route/architecture pass.
2. Change the part to the **-13 pin-out code**, which is genuinely 4-lead, and
   re-derive against ITS geometry.
3. Re-spec the isolation approach entirely.

## Immutability
Nothing was written into any sealed release directory. `07_releases/` is
untouched; this notice lives in the CHANGELOG and the STATUS beacon, which is how
this fleet records an orderability verdict (see `usb-hub-3s-v3` v1.6–v1.8).

## Found by
The v1.7 pre-seal review battery, fresh-context PIN lens, 2026-07-28 —
independently re-verified from the datasheet figure and the netlist before being
recorded. Full evidence: `08_reviews/2026-07-28_v1.7_pin-review_FRESH-LENS.md`
and `08_reviews/DISPOSITIONS_v1.7.md`.

---

## cooksense-v1.0 — 2026-07-23

Released: `07_releases/cooksense-v1.0-2026-07-23/`. First orderable release of
the MAIN board (252 x 92 mm, 4-layer, JLC advanced small-via).

Pre-seal batch folded in ONE rebuild (full KRT reroute race + deterministic
promoted-chain reuse): SN74HC238 decoder E3 pull-downs (safety: tri-state
float), J_MODE re-pin to the sibling 3V3/GND convention (cross-plug fail-safe),
J_TC footprint 4x dia-1.77 holes per the Omega drawing, PWR_GOOD_N -> EFUSE_FLT_N
honest rename, D_REVCLAMP moved downstream of F1. Ten review findings closed in
`verification/dispositions.md`.

Gates at seal: DRC 0/0/0 + M-REPRO, ERC 0, count_parity 191x4, audit_board PASS
(I-ISO 6.12 mm), policy_audit 0 FAIL (5 evidenced waivers), E-INV 17/17, twin
exit 0 (121 OK / 353), bom_source PASS, stock PASS, fresh zero-context lens
ORDER-OK-WITH-NOTES (both conditional P0s measured green — see
`verification/fresh_lens.md`).

Hand-solder / DO-NOT-SUBSTITUTE: 12x Standex DIP05-1A72-12L + Omega PCC-SMP-K
(ORDER_README). First-power ritual and harness labeling discipline are
NORMATIVE — read ORDER_README before ordering or powering.

## cooksense v1.1 — mechanical repack: rot0 isolation comb, 252x92 -> 188x92 mm
Released: 07_releases/cooksense-v1.1-2026-07-24
Supersedes: cooksense-v1.0-2026-07-23 (v1.0 remains electrically valid)

User directive (BRIEF D7, verbatim): "please schedule a v1.1 revision for
cooksense , lets make the board smaller." The rot90 single row was pitch-bound
at 20mm (19.90mm courtyard ALONG the row — measured, zero shrink available);
user selected the vertical-relay redesign. v1.1: relays rot0/rot180
alternating in pairs @ 15.24mm pitch — the exact orientation the DIP05
"super-column pitch" coupling figure was vetted in, with anti-parallel
adjacent coils (datasheet's own mitigation). The straight barrier becomes an
ISOLATION COMB: contact columns face shared keypad pockets (5 inter-pair + 2
ends), coil-coil gaps carry logic, 12 milled 0.6mm slots, 25 DRC deny rects.
Schematic/netlist BYTE-IDENTICAL to v1.0 (semantic_battery.txt) — placement/
outline only. Board 188x92 (was 252x92), -25% area.

Gates at seal: DRC --severity-all --refill-zones --schematic-parity 0/0/0 +
M-REPRO (2nd deterministic rebuild 0/0/0), ERC 0 err, count_parity 191x4,
audit PASS (I-ISO 6.12mm track-aware on the comb; selftest RED-capable),
placement gates P-OUT 0.30mm / P-CAP 0.21, tier_preflight 0 FAIL, E-INV
17/17 + E-ADR, net_label_survival 155/155, twin exit 0 (121 OK / 353),
bom_source PASS, stock PASS (C25744 order-day recheck noted), policy_audit
0 FAIL. Scoped re-verify per canon: carried v1.0 pin/render reviews
(netlist+parts untouched) + ONE zero-context fresh lens incl. explicit
isolation-comb review — see verification/fresh_lens.md.

NEW in ORDER_README: relay-coupling bench measurement (U+D+PRESS triple
energize, adjacent-relay operate-voltage shift) — a clean result licenses a
future <15.24mm-pitch or two-row revision.

## interposer-v1.0-2026-07-24 (Board C DESIGN SEAL — fab NOT ordered)

First release of the passive keypad interposer (ADR-0009 Path A: rigid board,
two self-supplied JST 10FDZ-BT top-entry ZIFs, GH breakout 1:1 to the main
board's J_KEY_MATRIX, 20 labeled TPs, floating keypad domain — no GND).
54x46mm 2-layer jlc_2layer_default. All gates green (DRC 0/0/0 + M-REPRO,
policy 0 FAIL, PIN/RENDER/2 red-team lenses: ORDER). USER-HELD order gates:
physical 10FDZ-BT land-pattern confirm (datasheet-derived footprint) and the
flex-jumper G1/G2 coupon (separate part). Source commit S = 3e37a02.

## cooksense-v1.3-2026-07-26 (SEAL)

Third electrical revision and the safety-chain revision. Supersedes v1.1 and
v1.0, **both now DO-NOT-ORDER** — see their SUPERSEDED.md for the seven defects
they carry, of which four are missing or inverted safety behaviour.

**Board:** 188 x 92 mm, 4 layer, 222 components + 4 holes, 3925 tracks /
1047 vias. DRC 0/0/0. E-INV 83/83. A-ROT 189/189 from measured rows. A-POS
189/189 on datum, worst 0.00000 mm.

**Safety changes.** The opto-isolated 30 V contactor loop left the SELV JST-GH
housing (0.650 mm from ESTOP_RAW in one harness) and now lands on ONE 4-pole
isolated block, `J_ISOLOOP`, with a 2.0 mm moat enforced as pour geometry
(measured 2.0000 mm over all copper on all layers). The door interlock became
fail-restrictive (`R_DOORPU` -> `R_DOORPD`). A hardware open-thermistor detect
was added so a broken or unplugged head reads OVER-TEMP. `R_WDPETPD` gives the
watchdog a real hold-down. `R_TEMPOK` moved to `3V3_ANALOG` so the temperature
verdict is powered by the rail whose health it reports. H4 gained an isolation
notch for mounting-hardware creepage.

**Three P0s were caught inside this cycle and none shipped:** `J_ESTOPLOOP`
placed inside `J_DOOR`; `R_OPENT` ordered at 6.2k where the design needs 62k;
`R_WDPETPD` ordered at 100k where it needs 1k. The last two were the same root
cause — a value-authored passive with no pinned LCSC, resolved by a picker that
returned a wrong decade. All four resistors of the open-detect divider and
R_WDPETPD are now pinned and ledger-verified.

**Deferred to v1.4, declared in the release:** door EOL supervision (a shorted
cable still reads "closed"); R_HYS negative feedback on the open-detect
comparator; TH_CAM sense-net span vs its declared 8 mm budget; the SOD-323
cathode band drawn on a bidirectional part.

Source commit S = 595d197.

## cooksense-v1.4-2026-07-26 (SEAL — documentation-only supersede of v1.3)

Released: `07_releases/cooksense-v1.4-2026-07-26/`.
Supersedes: `cooksense-v1.3-2026-07-26`.

**WRITTEN LATE, 2026-07-27, AND THAT IS THE FIRST THING THIS ENTRY RECORDS.**
v1.4 sealed on 2026-07-26 and this changelog carried NO entry for it — the LIVE
release was missing from its own project changelog for a day, while entries
existed for v1.0, v1.1, interposer-v1.0, v1.3 and interposer-v1.1. `policy_audit`
M-REL had been reporting it as a FAIL (`CHANGELOG missing entry for
cooksense-v1.4-2026-07-26`) and the STATUS beacon carried it under `next:` as
"OWED IN THE TREE, not order-blocking". It is written here, at the v1.5 seal,
rather than backdated into the v1.4 archive — a sealed directory does not gain
files after the fact, and the changelog is a PROJECT document, not part of the
release payload.

**THE BOARD REVISION DID NOT CHANGE.** The F.Silkscreen still reads
`cooksense SMC0985KS sidecar v1.3`, and that is correct: `fab/`, `source/`,
`3d/` and `pdf/` are byte-identical to v1.3's, and v1.3's gerbers remain correct
and orderable. v1.4 exists to correct v1.3's **MANIFEST assembly warning at H4**,
which named the NEAR (south) notch bank at 2.200 mm where the FAR (north) bank at
3.200 mm governs, and quoted the straight-line 3.8286 mm under a *creepage*
claim. The corrected numbers: H4 creepage 6.5984 mm (surface path around the
notch), and a **REQUIRED FASTENER SPEC — max conductive OD 6.0 mm (DIN 125 A2.7),
HARD LIMIT 6.3 mm**, because at OD 6.40 the fastener bridges the notch and
creepage collapses 6.3811 -> 4.7195 mm invisibly. Never a shakeproof washer
(6.5), a DIN 9021 (8.0), or a 6 mm A/F hex standoff (6.93 across corners). The
distinction is written up in `verification/ADR-0015-creepage-is-not-clearance.md`.

**Gates at seal** (quoted from the sealed archive's own MANIFEST): DRC
`--severity-all --refill-zones --schematic-parity` 0/0/0; ERC 0 errors,
1303 warnings; P-COLLIDE 0 pad shorts / 0 courtyard overlaps; E-INV 83/83;
A-ROT 189/189 from authority-table rows; A-POS 189/189 pad-centre-bbox datum,
worst 0.00000 mm; A-POP 226 board / 189 CPL / 37 unpopulated.

v1.1 and v1.0 remain **DO-NOT-ORDER** (22 wrong CPL rotations).

## cooksense-v1.5-2026-07-27 (SEAL — a BUYABLE BOM, and the LDO rail nobody had graded)

Released: `07_releases/cooksense-v1.5-2026-07-27/`.
Supersedes: `cooksense-v1.4-2026-07-26`.

**THE COPPER DID NOT MOVE, AND ON THIS BOARD THAT CLAIM CARRIES NUMBERS.** The
`.kicad_pcb` is md5-identical (`420445b5141dd1111eccab038c68511b`) to v1.4's, to
v1.3's, and to `04_kicad/`'s. Re-plotted from that same board, 11 of 13 gerber /
drill members are GEOMETRICALLY IDENTICAL under an aperture-resolved,
order-independent comparator that shares no method with the plotter; the two
copper layers that differ do so by **3 duplicate / sub-nanometre-collinear G36
vertices out of 29 587**, and the poured-copper AREA is equal to 6 decimal places
on all four copper layers (B 7379.912432, F 2838.968914, In1 8475.761683,
In2 8435.827928 mm², 13/106/1/1 regions on both). `fab/cpl.csv` is byte-identical,
so every A-ROT rotation and A-POS coordinate carries forward untouched.

**HALF ONE — TWO BOM LINES JLC CANNOT SUPPLY.** Read live 2026-07-27
(`selectSmtComponentList`, exact `componentCode` match):

| out | in | why |
|---|---|---|
| `C25744` 0402WGF1002TCE UNI-ROYAL, **stockCount 0** (17 refs: R_BID0/1, R_DOORPD, R_ESTOPPD, R_EXPRST, R_MODEPD, R_OE, R_OS2, R_REF0-7, R_TEMPOK) | `C60490` **RC0402FR-0710KL** YAGEO, stock 8 404 363 | the SAME code and the SAME shortage that forced usb-hub-3s-v3 v1.11 hours earlier, on a different board — a CATALOG event, not a cooksense one |
| `C25862` 0402WGF1201TCE UNI-ROYAL (R_ILM) | `C138040` **RC0402FR-071K2L** YAGEO, stock 472 208 | not out of stock — **unorderable in this quantity**: `minPurchaseNum` 7463 against a `stockCount` that read 25 / 65 / 90 across one afternoon, and the naive `stock >= 5 x qty` test PASSES it |

Both replacements' catalog `describe` strings are **CHARACTER-IDENTICAL** to the
parts they replace, compared AS STRINGS; `componentSpecificationEn` 0402 on both
sides; `leastPatchNumber` 20 on both sides. Both are EXTENDED parts — C25744 was
the only basic-library 10k 0402, so the one-time feeder fee is a property of the
shortage, not of the choice. **CHANGED AT SOURCE, NEVER IN THE CSV** (canon M3):
12 `supplierPartNumbers` sites in `03_tscircuit/src/cooksense.tsx`, `circuit.json`
regenerated by `tsci build`, the BOM regenerated by `export_jlc_package.py`.
v1.0-v1.4 left these refs as bare `<resistor>` for tscircuit's parts engine to
resolve, which is how a catalog snapshot became a BOM line nobody decided; they
are pinned now. New dossiers: `02_parts/RC0402FR-0710KL/`, `RC0402FR-071K2L/`.

**HALF TWO — A BOM ITS RECIPIENT CAN READ.** v1.4's `fab/bom.csv` graded
**F-LEGIBLE FAIL, 83 findings, 0 checks passed**: 55 F-MPN (every coded row ships
a BLANK MPN, so JLC's matcher leaves it at "No Part Selected"), 26 F-WORDS (the
Comment is the LCSC code again), 2 F-ENCODE (`Ω` with no UTF-8 byte-order-mark —
a reader defaulting to cp936 sees `惟`). v1.5: **0 findings, 56 checks**. Nothing
was invented: 54/54 coded rows resolve their MPN against 40 dossiers + 146 vetted
ledger codes, both of which already held the answer.

**HALF THREE — THE 3V3 RAIL, GRADED FOR THE FIRST TIME, AND IT DOES NOT PASS.**
`power_topology.py` gained `LINEAR` on 2026-07-27. v1.4 declared `rails: []` with
the envelopes parked in a parallel `linear_rails:` key the checker ignores by
design, so E-TOPO graded **0 of 1** converters — an LDO-only board reached a green
gate by showing it nothing. v1.5 moves the AMS1117-3.3 rail into `rails:` with
both required numbers CITED to AMS ds1117 (2009-08 RoHS):

- **dropout 1300 mV** — p.3, "Dropout Voltage (VIN - VOUT)", MAX, at **IOUT = 0.8 A**
  (Note 4). Corroborated by C6186's catalog `describe`: `1.1V@(800mA)`.
- **PD 1200 mW** — p.3 Note 2, "maximum power dissipation of 1.2 W for SOT-223".
- **Vout 3.201 / 3.399 V** — p.2, AMS1117-3.3 at VIN = 4.8 V, boldface (full
  operating temperature range). v1.4 carried 3.234/3.366, which is nominal ±2% —
  a plausible-looking number that is not in the datasheet.

  DISSIPATION  PD 690 mW / 1200 mW = **57%, PASS**
  DROPOUT      headroom 1101 mV (Vin_min 4.500 − Vout_max 3.399) vs 1300 mV
               → **FAIL, short by 199 mV**

**THIS RAIL DRAWS 0.3 A AND THE DATASHEET PUBLISHES NO DROPOUT FIGURE THERE.**
p.1 says only that dropout is "guaranteed maximum 1.3V, **decreasing at lower
load currents**"; Note 4 bounds the HIGH side only; and the TYPICAL PERFORMANCE
CHARACTERISTICS page (p.6) has six curves, none of them dropout-vs-load. So the
0.3 A dropout is **OWED** (canon M-OWED), the number declared is the only CITED
one at **2.67× this rail's load**, and `vin_min` was deliberately LEFT at 4.5 —
raising it to 4.75 makes E-TOPO pass with 51 mV to spare, which would be fitting
a number to a gate. **What the arithmetic actually says, and what a human must
decide:** for guaranteed regulation the LDO input needs ≥ 3.399 + 1.300 =
**4.699 V**, so "5 V SELV" (BRIEF §3.5, no tolerance stated) is an
UNDER-SPECIFICATION of this board's supply. Even a ±5% supply (4.75 V) lands at
~4.67 V after the F1/Q_REV/eFuse chain drop. **This is a supply-specification
decision, not a copper defect, and it is not order-blocking** — the boards are
fabbable and assemblable exactly as v1.4 was. It is written into ORDER_README
§0 and it is the ONE `policy_audit` row that does not pass.

**ALSO CLOSED.** M-BOM `UNVERIFIABLE-VALUE` on `220uF [CE1]` (`C2887273`): the
2026-07-23 ledger seed missed it while its own one-digit-away sibling
`C2887276` was already there; the catalog `describe` says `220uF` verbatim and
now so does the ledger. A-BODY: v1.4's `missing_models.txt` was generated with no
`--cpl`, so its denominator was 186 BOARD footprints rather than the 189 CPL
placements, and it counted `J_ISOLOOP` — which is `not_assembled` /
`exclude_from_pos_files` and **is not on the CPL at all**. Regenerated against
`fab/cpl.csv`, the population is the placements JLC will actually run.
`C42400616` (KF350-3.5-4P, J_ISOLOOP) is **still stockCount 0 and still not
substituted**: it is self-supplied, hand-soldered, off the CPL, and the board
would need a footprint change to take any other 3.5 mm 4-pole block — see
ORDER_README.

## interposer-v1.1-2026-07-27 (Board C RE-SEAL — supersedes v1.0, fab NOT ordered)

Released: `07_releases/interposer-v1.1-2026-07-27/`.
Supersedes: `interposer-v1.0-2026-07-24`, which is **DO-NOT-ORDER**.

**The P0.** v1.0's CPL shipped `J_KEY_MATRIX` (C2683602, JST GH) at rotation
**90.0** where the measured authority says **270.0** — 180 degrees out. It fails
SILENTLY: the GH pad array is symmetric about its own centre, so at 180 every pad
still lands on a pad and the part solders perfectly, while pin 1 <-> pin 10 swaps
and **the whole ten-line keypad ribbon reverses**. The 90 came from the
footprint-NAME rule `^JST_GH_SM,180`, refuted on 2026-07-25 — the day after v1.0
sealed. v1.1 derives 270.0 from the EXACT PAD-FIT path: the measured per-LCSC row
for C2683602 is offset 0 at rms 0.0049 mm vs 5.0792 mm next-best = 1037x
separation, board_rot 270 + 0 = 270.0, re-fitted independently here by `jlc_twin`
at 0.01 mm and matching the sealed main board's own CPL.

**The second P0, and the root cause of both.** Both self-supplied through-hole
10FDZ-BT ZIFs shipped ON v1.0's CPL with a blank LCSC and no declaration
anywhere — the only defence was README prose telling a human to delete two rows.
Root cause: **the entire assembly gate family never ran on v1.0** — its
`policy_audit.md` has no A-* row at all. An absent verdict is not a pass. v1.1
carries A-POP / A-POS / A-ROT / A-POL / A-BODY / A-STOCK / A-EVID / A-RENDER,
all green, plus a new `03_src/interposer/rules/assembly.yaml` with a DATED JLC
catalog query, `exclude_from_pos_files` on the board, and a GENERATED MANIFEST
`not_assembled:` line.

**Also folded in:** a legible BOM (F-LEGIBLE FAIL -> OK: MPN resolved from the
dossier, Comment a real value, UTF-8 byte-order-mark); a `pourless:` declaration
so F-POUR can tell a deliberately pourless board from one that lost its zones;
and a SELF-CONTAINED archive — `kicad-cli pcb drc --severity-all --refill-zones
--schematic-parity` from `source/` alone returns **0/0/0** where v1.0's returns
**29** (its fp-lib-table pointed outside itself and the two unresolvable
footprints were the two ZIFs, the entire point of the board).

**The copper did not move**, measured with an aperture-resolved, order-independent
gerber comparator that shares no method with the plotter: both copper layers, both
masks, both pastes and both drill files IDENTICAL; the profile identical as an
undirected segment set; F.Silkscreen differing by 50 of 5368 atoms, all inside one
0.514 x 0.900 mm cell — the version digit.

**Board:** 54 x 46 mm, 2 layer, 23 parts + 4 holes, 183 segments / 35 vias,
0 zones. DRC 0/0/0. ERC 0/102. policy_audit FAIL=0. E-INV 50/50.

**USER-HELD, unwaived, in ORDER_README section 0:** the 10FDZ-BT POLARITY read
(M9/M10 UNMEASURED — if reversed the board still works and only the TP/KP NAMING
is wrong) and the M3 boss offset (0.190 mm of error against 0.23 mm of clearance,
and it would interfere at the boss's nominal diameter — dry-fit every connector).
The user has measured the part and decided to build with the current footprint.

Source commit S = ee5632a.

## cooksense-v1.6-2026-07-27 (SEAL — documentation-only supersede of v1.5: a cross-plug that is NOT fail-safe, and the claim that said it was)

Released: `07_releases/cooksense-v1.6-2026-07-27/`.
Supersedes: `cooksense-v1.5-2026-07-27`.

**THE COPPER DID NOT MOVE, AND THIS TIME THE PROOF IS SHORTER THAN v1.5'S,
BECAUSE NOTHING WAS PRODUCED.** v1.5 re-plotted its gerbers from its own
`source/`, so it needed an aperture-resolved, order-independent comparator and a
shoelace area integrator to show that 11 of 13 members were geometrically
identical and the poured area equal to six decimal places
(`verification/copper_did_not_move.md`). **v1.6 regenerates nothing at all.**
`fab/` (19 files), `source/` (11), `3d/` (2) and `pdf/` (3) — **35 files, all
byte-identical to v1.5's**, carried across unopened, measured here by directory
sha256 in both directions: 35 identical, **0 differing, 0 added, 0 missing**.
`source/cooksense.kicad_pcb` is still md5 `420445b5141dd1111eccab038c68511b` —
the same file `04_kicad/`, v1.3, v1.4 and v1.5 carry. The identity is not merely
measured, it is **ASSERTED by the gate**: `release_freshness_check.py
--docs-only-supersede cooksense-v1.5-2026-07-27` sha256s every file under those
three trees in both directions and FAILs on any difference, addition or
omission. Per the `07_releases/` contract that mode is REQUIRED here rather than
the six file-by-file identity waivers v1.5 legitimately needed — "the mode
asserts the identity instead of flagging it" — so `freshness_exceptions.txt`
lists **zero paths** and says why.

**v1.6 EXISTS BECAUSE THREE OF THIS BOARD'S OWN SAFETY DOCUMENTS WERE WRONG.**
The 2026-07-27 adversarial audit (f8427c5, report-only, 0 new P0 / 7 P1) left
three open; A12 was closed without a reseal in 539ecf0; A1, A2 and A3 are closed
here. Every one was RE-VERIFIED against this archive's own `source/cooksense.net`
before acceptance — by a hand-written s-expression parser and set arithmetic,
which shares no code with the tsx author, the board generator or `policy_audit`
(canon M1) — and **two of the three re-verifications disagreed with the audit in
detail.** Both disagreements are recorded rather than smoothed away, in
`verification/crossplug_and_permission_defaults.md`.

Cross-check that licenses all of it: the working netlist
(`06_build/netlists/cooksense.net`, md5 `60a3326…`) and the sealed one
(`v1.5/source/cooksense.net`, md5 `8ebed11…`) differ in bytes only in the export
header — **192 nets both sides, the same net-name set, 0 nets with differing
membership, 222 refdes, 0 with a differing value.**

**A1 — `J_MODE` IS A CROSS-PLUG HAZARD, AND ORDER_README SAID THE OPPOSITE.**
Confirmed, every number. `fab/bom.csv` line 45 ships **five** `C189896`
SM05B-GHS-TB housings — `J_DOOR, J_ESTOP, J_MODE, J_RH_AMBIENT, J_RH_EXHAUST` —
one part, one footprint, nothing mechanical to tell them apart. §10 analysed
**three** and concluded "Pinouts are arranged so any single cross-plug is
fail-safe". **That claim is now WITHDRAWN in terms.** `COIL_EN` has exactly three
nodes — `J_MODE.4`, `Q_COILDRV.1`, `R_COILENPD.1` — no ESD device, no series
element, and its **only** hold is 100 kΩ, against 10 kΩ on `R_DOORPD` /
`R_ESTOPPD` / `R_MODEPD`: the one pin that directly enables the relay rail is
held ten times more weakly than the pins that merely report a switch. An SHT45
pod harness plugged into `J_MODE` powers up normally from pin 1 and lands its
module SCL pull-up on `COIL_EN` — **3.000 V** at the documented 10 kΩ
(`DETAIL_DESIGN.md:114`), **3.152 V** at BRIEF C7's 4.7 kΩ, both above the
2N7002's 2.5 V max `V_GS(th)`, so no subthreshold argument is needed. The rail
comes up with **all seven AND-chain terms and the Manual rail-cut bypassed** —
the rail cut *is* the pin 3→4 pole, and this drives pin 4 directly.
`J_MODE` (196.75, −60.00) is **38.29 mm** from `J_RH_EXHAUST` (186.00, −96.75),
same cable, same connector.

*Where the re-verification differs from the audit:* the audit's general bound
`R ≤ 175 kΩ` is correct arithmetic but rests on a 1.2 V minimum-threshold
subthreshold assumption — it is a worst-case-hazard figure and is now published
as such, weaker than the 10 k/4.7 k result beside it. *And the ROOT CAUSE is
new:* the 2026-07-23 pin-review-Q re-pinning (DISPOSITIONS #6) reasoned that
"any cross-plug **bridge** either applies the intended gating or holds the rail
OFF". **That models a cross-plug as a passive bridge between pins** — right for
three dry-contact harnesses, wrong for a harness that *sources* current. The
re-pinning was a genuine improvement and is not reversed; its conclusion was
generalised past its evidence, and §10 inherited the generalisation.

§10 is rewritten: five housings, the withdrawn claim, the **complete 20-cell
cross-plug matrix** (1 cell energises the coil rail, 6 are rail shorts, 3 are
permissive mis-reads), a mandatory discipline, and §10.6 naming the copper fixes
— including the measurement that the obvious `R_COILENPD` 100k→10k trim is **not
sufficient on its own** (3.3·10/20 = 1.65 V still turns the FET on).

**A2 — FOUR PERMISSIONS HAVE NO PULL, AND THE SOURCE'S CLAIM IS WRONG IN SCOPE,
NOT IN ARITHMETIC.** `WD_OK`, `ESTOP_OK`, `MODE_AUTO_HW` and `DOOR_OK` carry no
pull resistor of any kind — confirmed. **Extended:** of the **18** nets feeding a
permission/gating input, **7 carry a pull and 11 carry none** (the four, plus
`AND1`, `AND2`, `CTR_SAFE`, `FAULT`, `FAULT_SET_N`, `FAULT_LATCH_CLEAR`,
`STOP_REQ_N`). Sharpest single-part cases: a dead **`U_SCHM`** floats
`ESTOP_OK` + `MODE_AUTO_HW` + `DOOR_OK` at once — the E-stop can read clear with
the mushroom pressed, and the expander readbacks sample the SAME nets so
software has no independent cross-check; a dead **`U_LATCHB`** (SOT-23-5) floats
`FAULT_LATCH_CLEAR` into both `U_AND3.6` and `U_CAND2.3`, removing the
fault-latch permission from the coil rail and the contactor together. **No single
part floats all four** — `U_SCHM` gives three, `U_WD` the fourth.

*Where the re-verification differs from the audit:* the audit calls the tsx's
"the other twelve are pulled restrictive" FALSIFIED. Checked, that is not the
right verdict. **The twelve are exactly BRIEF D10 item 8's Pi/expander
authorization lines** — `HOST_AUTH`, `MCU_RELAY_ENABLE`, `CONTACTOR_REQ`,
`KEY_RESET_N`, `STOP_REQ`, `RAIL_EN_A/B/RHA/RHE`, `DECU_G1_RAW`, `DECD_G1_RAW`,
`REARM_N` — **and all twelve genuinely ARE pulled restrictive** (11 × 100 kΩ to
GND plus `REARM_N` 100 kΩ to 3V3 on an active-low line). The sentence is not
wrong about its twelve; it is wrong as a statement about "the safety chain",
because it counts only the SOFTWARE-driven lines and the four HARDWARE-derived
permissions are in neither group. "FALSIFIED" would send a reader hunting for a
missing pull-down among the twelve, and there isn't one.

**NEW FINDING, from the re-verification and not in the audit:** all four
permissions are read back on MCP23017 port B (`GPB7` = `WD_OK`, `GPB2` =
`ESTOP_OK`, `GPB1` = `MODE_AUTO_HW`, `GPB3` = `DOOR_OK`), and DS20001952C §3.5.7
— read from the PDF in `02_parts/MCP23017-E-SS/` — says a set `GPPU` bit pulls
an input pin up with a **100 kΩ** resistor. POR is `0x00`, so the default is
safe; but **one register write converts the indeterminate float into a
deterministic PERMISSIVE** on all four, including "E-stop clear" with the
mushroom pressed, and it is invisible while the board is healthy because a
push-pull driver beats 100 kΩ. There is no software way to add a pull-DOWN — the
register can only make the default worse. Shipped as a REQUIRED firmware
invariant, §7a-2: write `GPPUB = 0x00` explicitly.

**A3 — `REARM_N` HELD LOW DEFEATS THE FAULT LATCH, AND IT SURVIVES EVERY PI
REBOOT.** Confirmed. `REARM_N = {R_REARMPU.1, U_EXP.26 (GPA5), U_LATCHB.1}` —
**one driver**, no button, no connector pin, no test point. Held low, /R is
asserted forever: `FAULT_LATCH_CLEAR` is permissive at `U_AND3.6` and
`U_CAND2.3` at all times, a live fault puts the NAND latch in its forbidden
state (Q = /Q = 1), and `U_LATCHA` degenerates to `FAULT` = NOT(`FAULT_SET_N`) —
a combinational repeater. The live terms still gate; **the memory is gone**, so a
fault that clears re-permits cooking with no re-arm. ORDER_README §7 said "Pulse
REARM_N low" and nothing in hardware enforces a pulse.

The elegant property the audit credits is **confirmed with its two datasheet
facts, neither of which was written down anywhere before now**: `WD_OK` is low
for the TPS3823 reset delay (t_d 120/200/300 ms) so the latch is FORCED SET at
every power-up, and MCP23017 `IODIR` POR is `1111 1111` so GPA5 is an INPUT at
power-on and `R_REARMPU` holds the line high. **New, and worse than the audit
stated:** `EXP_RST_N = {R_EXPRST.1, U_EXP.18}` has **no driver** — nothing on
this board can reset the expander — so a held-low `REARM_N` does not survive a
3V3 power cycle but **does survive every Pi reboot**. This board's own
`electrical_invariants.yaml` already recorded that retention mechanism, in the
`why:` for `R_WDPETPD`, and had never applied it to `REARM_N`. §7a-1 now carries
the driver invariant, the analysis, and a **REQUIRED negative bring-up test**
that this revision is expected to FAIL — the tester is told so and told to record
it.

**WHAT IS NOW MACHINE-CHECKED THAT WAS NOT.** E-INV goes **83/83 → 85/85**: two
`part_value` asserts pin `R_COILENPD` = 100k and `R_REARMPU` = 100k, the two
numbers §10.2's cross-plug bound and §7a-1's power-up property are computed
from. A silent decade change would have moved a published number while every
existence and direction assert stayed green. **RED-VERIFIED**: substituting
`10k` for either makes the checker report `E-INV FAIL: 2/85`, naming both parts
and both actual values.

**TWO MORE, FOUND BY THE RE-VERIFICATION ITSELF** (declared gaps 22 and 23):
`02_parts/SN74HC14DR/part.yaml` still says "unused inputs 3A/4A/5A/6A tied GND"
when all six gates are used (E-stop, mode, door); and `cooksense.tsx:632`
contradicts `cooksense.tsx:637-638` about which `J_MODE` pole is which — the
netlist says line 632 is the pre-re-pin survivor, and a harness built from it
would leave `COIL_EN` open and the machine permanently unable to arm. §10.1's
table is now named as the harness authority in place of the source comment.

**WHAT IS NOT CLOSED, NAMED RATHER THAN HIDDEN.**

1. **All three hardware fixes are USER DECISIONS** and are deferred to the next
   ELECTRICAL revision: a keyed/different housing for `J_MODE` (or `COIL_EN` off
   a field connector), four-to-eleven 0402 pull-downs, and an edge-detect on
   `REARM_N`. This release ships the board v1.5 shipped.
2. **`03_tscircuit/src/cooksense.tsx:551` still carries the falsified clause**,
   and that is a deliberate, argued choice rather than an oversight.
   `source/cooksense.tsx` is inside the docs-only supersede's byte-identity set,
   so a comment-only edit would make v1.6 *not a docs-only supersede* by the
   gate's own definition, and the `07_releases/` contract forbids the
   alternative ("never waive fab-identical files one-by-one for this case").
   **The considered alternative was to extend `release_freshness_check.py` with
   an asserted comment-only-source relaxation, and it was rejected on the
   merits:** such a mode must strip TypeScript/JSX comments correctly in the
   presence of strings, template literals and regex literals, and a
   subtly-wrong comment-stripper in a shared fleet gate would let a real value
   change through — a worse outcome than a deferred comment. The clause is
   corrected in ORDER_README §13 gap 20 and in
   `verification/crossplug_and_permission_defaults.md` §2.3, and its correction
   in the tsx is OWED to the revision that adds the pull-downs — **the same
   change that makes the sentence true.**
3. **`verification/redteam_topology.md:58` carries the same claim and is NOT
   edited.** A dated review is a record of what a reviewer said, not a wiki. The
   INDEX now flags that line and points at the correction.

**GATES AT SEAL** — every number measured on the artifacts in this archive:
DRC `--severity-all --refill-zones --schematic-parity` **0 / 0 / 0**; ERC
**0 errors, 1303 warnings**; **E-INV 85 / 85** against `source/cooksense.net`;
`policy_audit --board cooksense` **FAIL=1 HUMAN=6 N-A=4 PASS=25 WAIVED=4** — the
one FAIL is **E-TOPO**, unchanged and deliberate: the AMS1117-3.3 3V3 rail is
short **199 mV** on dropout at `Vin_min` (headroom 1101 mV vs 1300 mV required),
mitigated as a USER-HELD order gate in ORDER_README §0 (hold ≥ 4.85 V at `J_PWR`
and it passes by **59 mV**). A-POP 226 board / 189 CPL / 37 unpopulated; A-BODY
189/189; A-ROT 189/189; A-POS worst 0.00000 mm; A-EVID 32 required artifacts, 0
missing; freshness **PASS in `--docs-only-supersede` mode with zero exceptions**;
`contracts_audit` 0 violations.

## cooksense-v1.7 — **ATTEMPTED 2026-07-28, NOT SEALED. BLOCKED ON TWO CONFIRMED P0s.**

**THERE IS NO v1.7 RELEASE.** `06_build/tmp/cooksense-v1.7-BLOCKED-2026-07-28/` exists as
**MUTABLE STAGING** and is deliberately **not committed**. The live sealed
release is still `cooksense-v1.6-2026-07-27`, its fab set is unchanged, and v1.6
therefore carries **no `SUPERSEDED.md`** — nothing supersedes it yet.

This entry is kept because the work is real and the blockers are the most
valuable thing the pass produced. **Everything below the two P0s was completed
and every gate passed** — which is precisely the argument for running the review
battery against staging rather than after a seal.

### THE TWO BLOCKERS

**P0-A — the eFuse OV cutoff is at 9.200 V (8.492–9.933 V worst case) on a rail
feeding 7.5 V reed coils.** `R_OVT` 100 kΩ / `R_OVB` 15 kΩ ⇒ ratio 0.130435
against SLVSE57C's `V_OVLO(R)` = 1.13/1.20/1.27 V. Four documents state the
intent as 5.5–6 V. **Found INDEPENDENTLY by BOTH red-team lenses** (layout P0-1
reported it UNVERIFIED because it could not open the PDF; topology RT-02 read the
PDF and reported it WRONG) and confirmed by the lead from
`02_parts/TPS259573DSGR/SLVSE57C.pdf`. Exposure: 12 DIP05-1A72-12L coils rated
7.5 V max, and `D_TVS` SMBJ5.0A whose V_BR starts at **6.40 V** — so on a
sustained OV the 600 W transient part becomes the DC regulator. **Both lenses
proposed a fix and neither is correct:** `R_OVB`→22 k tops out at 7.159 V (above
the TVS); `R_OVT`→57.6 k puts V_pin at 1.1545 V against a 1.13 V threshold at the
declared `vin_max` 5.5 V (nuisance trip). The admissible ratio window at
`vin_max` 5.5 is **1.0354× wide against a 1.0404× ±1 % spread — no ±1 % divider
fits.** The supply envelope, the TVS standoff and the OVLO requirement are
mutually incompatible as declared, and the root cause is the same undeclared
supply tolerance behind the E-TOPO dropout gap. **Escalated, not patched.**

**P0-B — one I²C register write defeats the watchdog in both gating chains, and
v1.7 made it worse.** `WD_OK` carries `U_EXP.8` (GPB7, a **bidirectional**
MCP23017 I/O rated 25 mA) alongside `U_WD.1` (TPS3823, V_OL specified only at
1.2 mA) and — **since ADR-0020** — `U_EXP.18` (`RESET_N`). `IODIRB.7=0,
OLATB.7=1` forces the net high; recovery needs the node below 0.66 V, so the
contention is **self-sustaining**. It removes the watchdog term from `U_AND1.3`,
`U_CAND1.1`, `U_FAULTAND.1` and `U_OENAND.2` at once. v1.6 had `U_EXP.18` on
`EXP_RST_N`, so **ADR-0020 is what put the reset on the net its own defeat
disables**, falsifying Decision B's claim in exactly its own case. Fix is one
0402 on an existing BOM line — 10 kΩ (C60490) in series to `U_EXP.8` **only**.
**Escalated, not patched** (electrical setpoint on a protection path; the
`R_OPENT` precedent).

### WHAT WAS COMPLETED AND IS COMMITTED

1. **ADR-0018 — `J_MODE` leaves the JST-GH family.** Now a JST ZH
   S4B-ZR-SM4A-TF, 4 circuits on 1.50 mm pitch (`C485354`) — a GH harness
   physically cannot enter it, closing v1.6 §10's one non-fail-safe cross-plug
   cell as a MECHANICAL interference rather than a label. Plus `R_COILENS`
   680 Ω in series, `R_COILENPD` moved **to the connector pin** at 680 Ω (was
   100 kΩ on the gate), and `D_COILEN` (PESD5V0S1BA). Measured: legitimate drive
   still passes at **2.982 V** (+482 mV over the 2N7002's 2.5 V max `V_GS(th)`)
   while injected pull-ups give **0.210 / 0.417 / 0.779 V** at 10 k / 4.7 k /
   2.2 k — all below the 1.0 V min threshold. Rejection bound moves from
   *R ≥ 230 kΩ* to **R ≥ 1564 Ω**.
2. **ADR-0019 — all eleven undefaulted safety-chain nets get a restrictive
   default.** Ten pull-DOWN, one pull-UP. `R_FAULTPU` is UP on purpose and is the
   evidence the direction was derived: a pull-down on `FAULT` is the PERMISSIVE
   state with `U_LATCHA` dead.
3. **ADR-0020 — `REARM_N` becomes an EDGE**, using the CD74HC221's already-fitted
   second section (one 1 µF cap, zero new ICs), and `U_EXP.18` moves off the
   driverless `EXP_RST_N` onto `WD_OK` — **which is what created P0-B.**

Plus the three stale statements v1.6 could not touch, and `J_ISOLOOP` re-authored
by MPN so its BOM line stops naming a code JLC cannot source.

**THE SILKSCREEN REVISION MOVED, AND IT WAS OWED.** The board read `sidecar v1.3`
through v1.4/v1.5/v1.6 — honest, because it was v1.3's board. v1.7 moves copper,
so it was bumped at source and the board **rebuilt from scratch**. The rebuild is
a **copper IDENTITY**: tracks 4166 hash `16d81d6b2d1634d6`, vias 1104
`5cc95d962b455a39`, footprints 239 `a4cfa2956c816c70` — all three byte-identical
by value before and after, DRC still 0/0/0. M-REPRO evidence obtained for free.

**COPPER DELTA v1.6 → staging**, measured: footprints 226 → **239**, track
segments 3925 → **4166**, vias 1047 → **1104**, poured GND on F.Cu 2838.969 →
**3080.104 mm²**, total track length 9073.908 → **9017.754 mm** (down, because
`R_COILENPD` moved off a long haul onto the pin it defends and `EXP_RST_N` was
deleted). BOM: 14 refdes added, 1 removed, 3 changed in place.

**GATES — all green, and they were not enough.** DRC 0/0/0; ERC 0 errors / 411
warnings; **E-INV 109/109** RED-verified with four NEW mutations, one per new
invariant family, each restored byte-identically; E-ADR 8/8; S-COUNT 4/4 over 235
refdes; net_label_survival 162/162; **A-ROT 202/202**; A-POS worst **0.00000 mm**;
A-BODY 204/204; **A-RENDER OK**; **A-STOCK PASS 55/55**; F-LEGIBLE OK 0 findings;
M-BOM PASS; P-FACT OK; `jlc_twin` exit 0; `audit_board` PASS (I-ISO 6.12 mm);
`placement_gates` PASS. E-TOPO remains the one deliberate FAIL on unchanged terms.

### OTHER FINDINGS WORTH THE NEXT AGENT'S TIME

- **A clean v1.7 regression the lead confirmed:** the `J_MODE` and `D_COILEN`
  refdes print **into the east-edge milled notch** (void x[191.50..200.05]
  y[48.80..49.80]; J_MODE's bbox x[194.099..197.801] y[48.386..49.614] entirely
  inside). ADR-0018's two headline parts would ship with no designator.
  `silk_edge_clearance` — the exact rule — is one of four silk DRC checks this
  board sets to `ignore`.
- **The render lens's P0 (identical unkeyed `J_ESTOP`/`J_DOOR`) is downgraded to
  P1 with evidence**: ORDER_README §10.4 already grades both cells
  `✗ FALSE-CLEAR` in a published 20-cell matrix, and the reviewer was
  deliberately denied it. What IS new is that the mitigation §10.5 leans on is
  broken — `J_DOOR`'s silk label sits **2.80 mm from J_ESTOP and 2.87 mm from
  J_DOOR**, i.e. closer to the wrong connector.
- **A new `policy_audit` check landed the same day** (`P-ADJ-UNREACHED`) and
  reports that **25 of 37 declared `keep_short` budgets name nets that do not
  exist on this board**. Waived with a full 37-row census rather than faked by
  re-pointing local pin budgets at 76-pad rails. The topology lens then landed
  the same class on the only protection IC.
- **Six checker defects reported upstream**, none of them board defects:
  `pin_audit.py`'s literal MPN→directory join (**16 of 54 dossiers blank,
  including `U_EXP`**); `jlc_twin.py`'s PAD-GEOM knife edge and its
  `marker_side()` frame bug (same class as 772b152, still live); A-RENDER's
  absolute 20-px floor against a hard-coded 1600×1000 render; `count_parity.py`'s
  first-glob multi-board mis-targeting; and `jlc_twin --adjudications <missing
  path>` running silently with zero adjudications.

**The full finding ledger with the lead's independent re-derivation of every
claim is `08_reviews/DISPOSITIONS.md` (v1.7 section) and the staging archive's
`verification/dispositions.md`.**

---

## cooksense-v1.7 — 2026-07-30, **NINTH SEAL ATTEMPT, DECLINED. NOT SEALED.** And this is the first decline that found something.

**THE SOURCING BLOCKER WAS REMOVED AND THE SEAL STILL DID NOT HAPPEN — because
re-gating BOTH lenses on the new vocabulary surfaced two design P0s that eight
previous passes had not found.** The candidate stays in
`06_build/staging/cooksense-v1.7/`; `07_releases/` is untouched;
`cooksense-v1.6-2026-07-27` remains the newest sealed release and carries no
`SUPERSEDED.md`, because nothing superseded it. **There is still no orderable
cooksense board.**

    DESIGN:   BLOCKED — verification/redteam_layout.md design_verdict: DEFECTIVE
    SOURCING: BLOCKED-1 (C265111; measured 2026-07-30)

### The two P0s — neither of them copper, both independently re-measured

**P0-1 — the LDO is graded at 0.30 A while the same file declares 0.40 A of
rails downstream of it.** `power_tree.yaml`'s `rails:` key (the only one
`power_topology.py` reads) declares the AMS1117-3.3 at `iout_max_A: 0.3`,
enumerating only the logic. Seventy-three lines lower, under a `linear_rails:`
key the file itself labels *"Documentation-only (ignored by
power_topology.py)"*, it declares four switched sensor rails at 0.1 A each.
MEASURED on the board with `pcbnew` — not read from the yaml — **all four
`AO3401A` load switches have their SOURCE pad on net `3V3`** (`Q_SWA`, `Q_SWB`,
`Q_SWRHA`, `Q_SWRHE`), and all four drains leave the board on a sensor
connector. The declared LDO load is **0.70 A, and the graded 0.3 is 43 % of
it.** At the file's own constants both graded numbers flip: PD 1.434 W = **120 %
of the 1200 mW ceiling** (graded 51 %), dropout headroom **−15 mV** (graded
+55 mV). Even at a *realistic* 0.36 A the dissipation is 20 % above what the
release reports — and the dropout argument is a +55 mV pass the file itself
calls "the fully-stacked worst case". A 20 % load error does not fit inside
55 mV.

**P0-2 — `pdiss_max_mw: 1200` is a 25 °C figure used as an ambient-independent
ceiling, on a board the BRIEF places in a 50–75 °C enclosure.** Inverting it
gives θ_JA = (125−25)/1.2 = 83.3 °C/W at Ta 25 °C. Re-derived at the brief's own
commissioned ambients: 0.900 W at 50 °C, 0.720 W at 65 °C, **0.600 W at the
75 °C hard limit — under the release's own 615 mW figure.** And the θ_JA
justification in the file ("the tab is flooded with 3V3 copper → 55–65 °C/W") is
REFUTED by measurement: I enumerated every zone on the board and **the only zone
on net `3V3` anywhere is on `In2.Cu`; there is no F.Cu `3V3` zone at all.** The
tab is a 7.39 mm² island in a GND pour with two 0.15 mm vias — a different heat
path from the one cited, and one the datasheet's single-layer Table 1 does not
describe. Whether the real θ_JA is better or worse than 83 °C/W is genuinely
unknown.

**Neither is a layout change.** The fix is to state the LDO's real total load
with cited sensor currents, add an ambient term, and re-run E-TOPO — it may well
pass at a defensible 0.36–0.40 A. It has not been asked. One bench session at
bring-up (load `3V3` to its real total; measure the tab temperature against a
known ambient and `V_IN − V_OUT` at `U_LDO`) retires both.

### What DID change, and it is the thing that let the ninth pass find them

### What the board fixes — the defect that made all six predecessors dead

Every cooksense release sealed before this one — **v1.0, v1.1, v1.3, v1.4, v1.5,
v1.6** — carries `Relay_StandexDIP_1A_pinout12` on the twelve DIP05 reed relays.
The part that exists is pin-out **13**. Under the pin-out-12 land `5V_KEY_RELAY`
is hard-shorted to the select bus, every ULN2803 output is shorted to its keypad
line, the coil has no holes at all, and the 1.5 kVDC coil/contact isolation
boundary the safety case rests on does not exist.

**Nothing mechanical in this repository could see it.** DRC, ERC, schematic
parity, netlist parity and the digital twin all passed on v1.6, because a wrong
land pattern is consistently wrong across every artifact derived from it. It was
found by a FRESH-CONTEXT PIN REVIEW that re-derived the land from the datasheet
FIGURE without reference to the footprint — canon M1, checker and checked must
not share a method — and it is the same failure shape as the usb-hub-3s D1
reverse-polarity TVS.

MEASURED refdes delta v1.6 -> v1.7, from both boards' own `.kicad_pcb` text:
**226 refs -> 243**. REMOVED (4): `D_DOOR`, `J_DOOR`, `R_DOORPD`, `R_EXPRST` —
`J_DOOR` because an identical-housing pod harness plugged into it could assert
`DOOR_OK` with no door attached. ADDED (21): seven series elements
(`R_ESTOPOKSER`, `R_FAULTSER`, `R_MODEHWSER`, `R_TEMPOKSER`, `R_WDOKSER`,
`R_COILENS`, `R_ESTOPS`) so one I2C transaction on the expander can no longer
defeat four safety terms at once, eleven `*PD`/`*PU` elements pinning the
restrictive defaults the review battery found missing, plus `C_EFIN`, `C_OS2`,
`D_COILEN`.

### What changed in the REPOSITORY, and why this pass sealed when eight did not

**Nothing physical was ever in dispute.** v1.7 reached DRC 0/0/0,
`policy_audit` FAIL=0, ERC 0 errors, E-INV 167/167 and four graded review lenses
— and eight successive full agent passes declined to seal it, every one of them
on ONE BOM line whose `minPurchaseNum` (21) exceeds its entire `stockCount` (5).
Zero design defects in all eight. The last of them wrote it out loud:

> *"I would accept the seal — the M4 argument is sound — but sealing is not the
> question this verdict field asks."*

Commit **`217ea175`** split the release verdict into the two claims a seal
actually makes:

- `release_freshness_check.py` now prints and grades `DESIGN: PASS|FAIL` and
  `SOURCING: CLEAR|PLANNED-<n>|BLOCKED-<n>` separately, with new check
  **(f) A-BUY** — a non-orderable release MAY seal, and ONLY OUT LOUD: the
  count, every blocked LCSC and the measurement DATE must appear in the MANIFEST
  gate summary AND on ORDER_README.md's FIRST SCREEN, cross-checked against the
  shipped measurement **in both directions**. A release may neither hide a
  blocked line nor invent one.
- the `08_reviews` contract now declares `design_verdict: SOUND|DEFECTIVE` and
  `order_verdict: ORDER|DO-NOT-ORDER|BLOCKED-SOURCING`, graded by check
  **(g) M-REV**. The SEAL gate reads `design_verdict`; the ORDER_README reads
  `order_verdict`.

The reason the distinction is real and not bookkeeping: every other gate here
grades an artifact WE CONTROL, so a red means *there exists an edit that turns it
green*. **A-STOCK grades the WORLD** — it read 0 on 2026-07-29 and 5 on
2026-07-30 on this same unchanged board — and no edit to the design changes it.

**The split is a NET TIGHTENING.** Before it, a `sourcing_plan:` entry silently
cleared its line whatever its own measured number said, so a release could seal
unbuyable with nothing anywhere saying so. Now an unclassified shortfall is a
FAIL and this one classifies itself `order_status: BLOCKED`.

### BOTH lenses were re-gated, not just the one that declined

The topology lens was re-gated because it is the one that declined. The **layout**
lens was re-gated because its previous legacy `verdict: ORDER` retrofits to
`order_verdict: ORDER`, and M-REV cross-checks that against the measurement:
grading ORDER on a release measured `SOURCING: BLOCKED` fires
`REVIEW-ORDER-CONTRADICTS-EVIDENCE`. A lens may not certify an order the archive
it graded cannot place. Both ran fresh-context, concurrently, neither handed a
conclusion, with journals / learnings / STATUS / `08_reviews` denied.

    verification/redteam_topology.md   design_verdict: SOUND       order_verdict: BLOCKED-SOURCING
    verification/redteam_layout.md     design_verdict: DEFECTIVE   order_verdict: BLOCKED-SOURCING

**And that is the finding.** The layout lens was re-gated only because M-REV
would have refused its old `verdict: ORDER` against a release measured
`SOURCING: BLOCKED`. Nobody suspected its design content. Re-asking it under a
vocabulary that could express the sourcing answer is what got it to look at the
board again — and it came back with two P0s. **Widening the re-gate from "the
lens that declined" to "both lenses" is what this pass is actually worth.**

### What is NOT orderable, and the number that is NOT 10

`C265111` (JST SM08B-GHS-TB, on `J_THERM_A`/`J_THERM_B`) reads **stock 5 against
MOQ 21**. You cannot order 21 when 5 exist, and you cannot order 5. The build
needs 10 and the stock gate's floor is 10 — **ignore both; the threshold that
unblocks a purchase is 21.** Read at 2026-07-30T23:46:46Z by the sealing agent's
own HTTP client with a live control (`C5620` = 5212). ORDER_README §5-0 carries
the substitute, the exact source change, and the one physical check a
substituting buyer owes.

**§5-0's remedy is the CORRECTED one.** An earlier draft told the buyer to "edit
one cell of `fab/bom.csv`" — **a file JLC never receives.** The assembly step
takes `bom_jlc.csv` / `cpl_jlc.csv`, and the CPL `Val` column carries the LCSC
code too because `fp.GetValue()` on these two footprints *is* the string
`C265111`. Following that instruction exactly would have ordered the unbuyable
part. The remedy now says: change `03_tscircuit/src/cooksense.tsx` lines 1216 and
1218 and REGENERATE (canon M3).

### Gate state: THREE non-zero exits, none of them copper

`A-STOCK` (the sourcing claim, above), `E-NETREF` (21 ghost `keep_short` budget
references in `02_parts/`, no board exposure) and `A-AMP` in `rules_audit` (two
`nets.yaml` DECLARATION defects predating v1.6 — one class declaring
`current: 'uA-level sense'`, prose where the gate needs a magnitude, so its
width was never graded; and `PWR_IN` declaring 2.0 A against a 0.5 mm tap-run
floor whose trunk rides pours). **Every gate that grades the BOARD exits 0** —
DRC both halves plus the standalone-archive DRC, ERC, schematic parity, S-COUNT,
E-INV, E-ADR, placement_gates, audit_board, jlc_twin, A-RENDER, A-POP, A-POS,
A-ROT/A-POL, M-BOM, F-LEGIBLE, F-PAYLOAD, P-FACT, M-DEPEND, M4, contracts_audit,
M-BEACON. Full table with every raw exit code: `verification/build_gates.md`.

### Three declared gaps added at this seal

1. **The mechanical tab pads match the CLONE, not the genuine part** — board
   `1.000 x 2.700`, genuine JLC land `1.210 x 2.700`, clone `1.000 x 2.500`. The
   board's retention tab is 17.4% narrower than JLC recommends for the part the
   BOM names, on the exact axis §5-0 declares unverified. UNRESOLVED. And the
   inherited "0.01 mm measured drop-in" for the clone **was not evidence** — its
   whole triple is verbatim the genuine part's own `twin_run.log` rows and
   `fit=` prints 0.01 for the genuine part too, so it cannot discriminate them.
   Re-derived by a non-`jlc_twin` method: genuine 0.0002 mm, clone 0.0100 signal
   / **0.0399 tabs**.
2. **E-NETREF exit 1 — 21 ghost net references**, all kind K7
   (`layout.keep_short[].net`), all already inside `policy_audit`'s evidenced
   `P-ADJ-UNREACHED` waiver. No ghost reaches copper, silk, netlist or BOM.
   First COUNTED here; the gate landed 2026-07-29/30 so v1.6 ships no netref
   evidence at all.
3. **A-RENDER's verdict moves with its input's resolution** — same board, three
   renders: FAIL on `U_LDO`+`Q_SWDRVRHA` at 5.1356 px/mm, FAIL on a DIFFERENT
   ref (`J_KEY_MATRIX`) at 9.7448 px/mm, PASS at 15.3907 px/mm. Both reports
   ship; deleting the failing one would be choosing the resolution that gives
   the answer you want.

### And the archive stands alone, which it did not two hours before the seal

`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` returns
**0/0/0, exit 0** on `source/` copied to a directory OUTSIDE the repository.
An earlier v1.7 staging had `source/fp-lib-table` pointing at
`${KIPRJMOD}/../03_src/lib/…` and returned **14 `lib_footprint_issues`** standing
alone. A fleet sweep finds the same defect in **5 of 33** sealed archives
(cooksense-v1.1, interposer-v1.0, usb-hub-3s-v3 v1.3/v1.4/v1.6) — immutable,
recorded, not repaired. Nothing in the repo gates this property; filed as an owed
skill patch.

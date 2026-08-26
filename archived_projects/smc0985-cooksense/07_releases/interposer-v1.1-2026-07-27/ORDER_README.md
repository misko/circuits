# ORDER — interposer (Board C) v1.1, 2026-07-27

Passive keypad interposer for the SMC0985KS (project smc0985-cooksense,
ADR-0007 multi-board; this is the SECOND board — the main board is the
`cooksense-*` release line). OEM membrane tail -> `J_MEMBRANE` (10FDZ-BT ZIF)
-> ten straight-through lines -> `J_CN1_JUMPER` (10FDZ-BT ZIF) -> flex jumper
(SEPARATE part, NOT in this release) -> OEM CN1; the ten lines break out on
`J_KEY_MATRIX` (JST GH) to the main board. Floating keypad domain: NO ground,
NO power, NO chassis bond, NO copper pour anywhere on this board — that is the
spec, not an omission (BRIEF §5, ADR-0009; declared as `pourless:` in
`source/assembly.yaml` and graded by F-POUR).

**THIS RELEASE SUPERSEDES `interposer-v1.0-2026-07-24`, WHICH IS
DO-NOT-ORDER.** v1.0's CPL shipped `J_KEY_MATRIX` at rotation **90.0** where
the measured authority says **270.0** — 180° out. That failure is silent by
construction: the GH pad array is symmetric about its own centre, so at 180°
every pad still lands on a pad and the part solders perfectly, while pin 1 ↔
pin 10 swaps and **the whole ten-line keypad ribbon reverses**. Nothing
electrical or visual catches it. See §3b.

---

## 0. ORDER GATES — read BEFORE spending money

### Gate 1 — 10FDZ-BT physical confirm: **MEASURED, PASS WITH TWO OPEN ITEMS**

The user has the part in hand and has measured it. The land pattern is
CONFIRMED and **the decision is to build with the current footprint.**

| # | measure | expected | MEASURED | verdict |
|---|---|---|---|---|
| M11 | pin count | 10 | **10** | PASS |
| M1 | end pin → end pin, 9 pitches | 22.86 c-c | **23.50 outside-to-outside** → 22.86–22.90 c-c | PASS (band 22.71–23.01) |
| M2 | pitch, from the 9-pitch span | 2.540 | **2.540–2.544** | PASS (band 2.52–2.56) |
| M5 | pin cross-section | ~0.6 | **0.60–0.64** | PASS go/no-go (≤0.80) |
| M4 | boss diameter | ~1.70 into a ø1.80 hole | **1.60** | PASS go/no-go (≤1.75); 0.10 mm RADIAL clearance, double nominal |
| M3 | boss centre → nearest pin centre | 2.54 | **2.35** | **0.04 mm LOW of the 2.39–2.69 band — OPEN ITEM 1** |
| M9/M10 | which housing end carries circuit 1 | 5.30 / 8.10 | **NOT MEASURED** | **OPEN ITEM 2** |

M1/M2/M5 are ONE measurement, not three. The raw reading is **23.50 mm
outside-to-outside** across the row, which is `9 × pitch + one pin width` — two
unknowns from one number, so the split is under-determined:

    assume pitch 2.5400 (nominal) -> c-c 22.860, pin width 0.640
    assume pin width 0.600        -> c-c 22.900, pitch  2.5444

**Both readings sit inside their PASS bands, and open item 1's conclusion below
is the same under either** — so nothing turns on resolving it. Recorded as a
range rather than collapsed to one number, because collapsing it would be an
assumption wearing a measurement's clothes.

#### OPEN ITEM 1 — M3 reads 2.35 mm. It fits, by 0.04 mm. Here is the arithmetic.

The measurement reference was not stated, so treat 2.35 as real and worst-case.

    BOARD holes, relative to the boss hole (from fab/interposer-{PTH,NPTH}.drl):
        boss     0.000        pin 1   2.540        pin 10  25.400
    PART, relative to the boss, using the MEASURED numbers:
        boss     0.000        pin 1   2.350
        pin 10 = 2.350 + 9 x pitch = 25.246 (pitch 2.544)  or  25.210 (pitch 2.540)

    Register the boss in its hole and the pin misregistration is
        pin 1   2.350 -  2.540 = -0.190 mm      <- the worst pin, EITHER WAY
        pin 10 25.246 - 25.400 = -0.154 mm      (pitch 2.544: the +0.004 mm/pitch
                                                 HELPS across the row)
               25.210 - 25.400 = -0.190 mm      (pitch 2.540: the whole row is
                                                 simply offset by the boss error)
    Worst-case pin misregistration is -0.190 mm under BOTH readings of M1/M2/M5.

    Available slack along the row axis
        boss in a ø1.80 hole, boss ø1.60   ->  (1.80-1.60)/2 = 0.10 mm of bodily shift
        pin  in a ø0.90 hole, pin  ø0.64   ->  (0.90-0.64)/2 = 0.13 mm per pin
                                               (the CONSERVATIVE reading; at pin
                                                ø0.60 it is 0.15 mm)
        TOTAL                                                = 0.23 mm

    0.190 mm of error against 0.23 mm of slack. **MARGIN 0.04 mm.** Shift the
    part 0.10 mm toward pin 10 (the boss will do this on its own as the pins
    find their holes) and pin 1's residual is 0.09 mm inside its 0.13 mm.

**READ THE NUMBER THAT MATTERS: THE ERROR IS 0.190 mm AGAINST 0.23 mm OF TOTAL
CLEARANCE.** "0.04 mm low" describes only the distance to the PASS-band edge and
under-states it; the margin that decides whether the part seats is 0.04 mm out
of 0.23 mm, i.e. the measured error consumes **83%** of the available slack.

**AND THE MARGIN DEPENDS ON THE BOSS ACTUALLY BEING ø1.60.** That is the
measured value on the connector in hand, and it is 0.10 mm UNDER the ø1.70
nominal for a ø1.80 hole. Redo the arithmetic at nominal:

    boss ø1.70 -> (1.80-1.70)/2 = 0.05 mm  +  pin 0.13 mm  =  0.18 mm  <  0.190 mm
                                                              -> INTERFERENCE

So a connector from a different lot, sitting at its ø1.70 nominal, would bind by
~0.01 mm. **Dry-fit EVERY connector before soldering it** (§4 step 3), not just
the first, and treat a tight one as expected rather than as a surprise.

**THE BOSS IS A LOCATOR, NOT A CONTACT.** It carries no circuit, no current and
no mechanical load — it exists to stop the connector going in backwards. If it
interferes on the bench, the fix is five minutes and does not touch a net:
ream the ø1.80 NPTH one drill size, or nip 0.2 mm off the boss with side
cutters. **It is not a scrap condition.** Do this on ONE board first and
report — do not modify all five.

#### OPEN ITEM 2 — polarity (M9/M10) is UNMEASURED

The convention this board declares stands:

> **Pin 1 = the contact at the BOSS end.** That is the square (RECT) pad, the
> silk numeral "1", and it carries `KP_U1`. Pin 10 (`KP_D4`) is at the far end.

It has **NOT** been confirmed against the OEM's CN1. The discriminator costs
one caliper measurement on the housing: the boss end overhangs the end pin by
**5.30 mm**, the far end by **8.10 mm** (B − A − 5.3 = 36.26 − 22.86 − 5.30).

If the convention turns out reversed, **the board still works** — all ten lines
pass through, the OEM tail is self-keying (contacts on one side of the slot
only), and the pass-through is 1:1 whichever way you read it. What breaks is
NAMING: `TP_M_U1 … TP_M_D4` and the `KP_U*/KP_D*` labels would identify the
wrong physical conductors, and the main board's key-matrix scan would map
wrong. That is a firmware/label correction, not a board respin.

**Record the answer before bring-up** (`01_docs/10fdz-bt-land-pattern-confirm.md`
§4, P1/P2), and re-check the §4 continuity map against the OEM panel (G6) before
anything connects to `J_KEY_MATRIX` (G7).

#### Settled today, for the record

The **OEM keypad tail is PLAIN — no punched lock slots.** CITED from user
photographs, not MEASURED. This resolves the ADR-0008 / ADR-0005-D5 conflict
without overturning either: JST's eFDZ p.3 *recommends* two 1.2 × 3 mm slots
3.81 mm inboard of each outer conductor for retention, and this OEM did not use
them. Both facts are true. It does not affect this board's copper; it decides
whether the **flex jumper** (separate part, `01_docs/flex-jumper-spec.md`) is
built slotted or plain — build it PLAIN, to match the tail the ZIF is already
holding.

### Gate 2 — flex-jumper G1/G2 coupon discipline (USER-HELD, unchanged)

≥100 insertion cycles on a sacrificial coupon, never first-fit on the OEM CN1
(T5, ADR-0008/0009). This board itself is rigid and in-pipeline, but its system
role is exercised only through that jumper.

---

## 1. JLC order options

- **2-layer, 1.6 mm FR-4** (10FDZ-BT applicable PCB thickness is 1.6 mm — do
  NOT order 0.8/1.0 mm), tier `jlc_2layer_default`: NO advanced options needed.
- Board **54 × 46 mm**. Quantity **5** (JLC minimum; 1 build + spares for the
  G2 fit trials and for open item 1's ream-one-board test).
- Surface finish: HASL fine (hand-solder THT + one 1.25 mm SMD connector);
  ENIG optional.
- Upload `fab/interposer_gerbers.zip` on the PCB page.

## 1b. Assembly — the BOM and CPL are UPLOAD-READY AS SHIPPED

**Do not hand-edit them.** v1.0's README told you to delete two rows before
uploading; that instruction is gone because the artifacts now carry the
decision themselves.

- `fab/cpl.csv` has **one** row: `J_KEY_MATRIX`, the only machine-placed part.
- `fab/bom.csv` has **two** rows. The `10FDZ-BT` row is a **self-supplied
  line with a deliberately blank LCSC** — it tells you what to buy and is not
  a placement instruction, because its designators are not on the CPL.
- The population decision is declared in `source/assembly.yaml`
  (`not_assembled: J_CN1_JUMPER, J_MEMBRANE`, reason `not_in_catalog` with the
  dated catalog query), the board footprints carry `exclude_from_pos_files`,
  and the MANIFEST's `not_assembled:` line is GENERATED from that file.
  `assembly_coverage.py` (A-POP) checks all three agree.
- You may equally order **bare boards** and hand-solder all three connectors —
  `J_KEY_MATRIX` is a 1.25 mm-pitch GH and is hand-solderable with a fine tip.

## 2. Hand-solder list (self-supplied, DO-NOT-SUBSTITUTE)

| Ref | Part | Source | Note |
|---|---|---|---|
| `J_MEMBRANE`, `J_CN1_JUMPER` | JST **10FDZ-BT(S)(LF)(SN)** | Mouser / RS / DigiKey — **not on LCSC** | TOP entry ("BT"). **Never 10FDZ-ST** (side entry; its row sits 8.2 mm from the outline, not 2.6 — different land pattern, the boards would be scrap). Boss NPTH sets orientation; "1"/"10" silk numerals stay visible with the connector seated. Buy 2 + spares |
| `J_KEY_MATRIX` | JST SM10B-GHS-TB, LCSC **C2683602** | JLC stock **8559**, re-queried 2026-07-27 | SMD; machine-placed by default, hand-solderable if ordering bare boards |

**Catalog evidence for the blank LCSC** (`source/assembly.yaml`, 2026-07-27):
`10FDZ-BT` → 1 hit, C593708 `10FDZ-BT-M(S)(LF)(SN)`, stock **0** — and that is
the "-M" variant, not the specified part. `FDZ-BT` → 7 hits: 08FDZ-BT stock 954,
06FDZ-BT 1366, 05FDZ-BT 100 (live numbers the same minute, so the zeros are the
library's answer and not a dead field) while every 10-circuit-or-larger line
reads 0. No orderable 10-circuit line exists.

## 3. KEYPAD RIBBON — harness spec (silent-reversal trap)

Interposer `J_KEY_MATRIX` ↔ main-board `J_KEY_MATRIX`: **10-way JST GHR-10V-S
housings BOTH ends, SSHL-002T-P0.2 contacts, wired contact-k → contact-k
(1→1 … 10→10).** Both boards carry the SAME part at the SAME rotation (mouth
off-board), so for a flat cable both housings must be crimped on the SAME
conductor face with pin 1 on the SAME cable edge, mated via a planar U-bend.
A premade "opposite-side" GH jumper SWAPS pin 1 ↔ pin 10 (U-bank ↔ D-bank) with
zero electrical symptom until the key matrix scans wrong.

**Before first use: continuity-beep interposer `TP_M_U1` → main-board `KP_U1`
(`J_KEY_MATRIX` pin-1 side) and `TP_M_D4` → `KP_D4`.**

## 3b. ROTATION — check it in JLC's placement preview anyway

`fab/cpl.csv` ships `J_KEY_MATRIX` at **Rotation 270.0**, `Mid X 15.25`,
`Mid Y -33.0`, top. Both numbers changed from v1.0 and both changes are
load-bearing:

- **270.0, not 90.0.** Derived from the EXACT PAD-FIT path, not the footprint-
  name DB. The measured per-LCSC row for C2683602 (`jlc_lcsc_rotations.csv:17`)
  records offset **0** from a pad-by-number fit against JLC's own cached model:
  **rms 0.0049 mm vs 5.0792 mm for the next-best angle = 1037× separation**,
  measured 2026-07-25 with an operator verified against pcbnew itself. The board
  places the part at orientation −90 ⇒ board_rot 270, so CPL = 270 + 0 = **270.0**.
  Independently re-fitted for THIS release by `jlc_twin` against JLC's model:
  `fit=0.01 mm jlc_offset=0 src=lcsc`. The sealed main board ships the same code
  at the same board orientation at CPL 270.0. **v1.0's 90.0 came from the
  footprint-NAME rule `^JST_GH_SM,180`, which was REFUTED on 2026-07-25 — the
  day after v1.0 sealed — after putting EIGHT connectors 180° out across two
  sealed releases. A name is not a part.**
- **Mid X 15.25, not 15.00.** JLC places a part so its OWN origin lands on the
  CPL coordinate, and that origin is the centre of the bounding box of the PAD
  CENTRES — not KiCad's footprint anchor. Measured 227/228 on JLC's own models
  across this fleet. `assembly_coverage.py` re-derives it from the board text
  independently: worst residual **0.00000 mm**.

**Still eyeball it.** Open JLC's placement preview and confirm the GH mouth
points OFF the west board edge (away from the pads), same as
`verification/twin_top.png`. A-POL raises no single-channel human gate for this
board — C2683602's rotation has a numbering-free second channel (the unnumbered
MP mounting tabs) — but a five-second look is free and this is the exact defect
this release exists to fix.

## 3c. F-ECHO — after uploading, diff JLC's resolved BOM back against ours

JLC resolves our codes on their side and can REDIRECT one. `C82317 → C131025`
happened on a sibling board and nothing in this repo could see it. Save JLC's
own resolved/matched part table out of their UI and run:

    bom_legibility_check.py fab/bom.csv --echo SAVED.csv

The worklist is `verification/bom_echo_gate.txt` (1 coded line to confirm).
**A code JLC redirects is a SUBSTITUTION and is a finding, not a convenience.**

## 4. Bring-up ritual (G6 continuity map)

1. Bare board, nothing inserted: beep each of the 10 lines
   `J_MEMBRANE.k ↔ J_CN1_JUMPER.k ↔ J_KEY_MATRIX.k ↔ TP_M_* ↔ TP_C_*`
   (labels on silk; pins count 1..10 west→east between the "1" and "10"
   numerals). Confirm **NO** continuity between any two different lines, and
   **NO** continuity from any line to the four mounting holes (they are NPTH —
   floating by design).
2. ZIF handling: slider OPEN before inserting a tail (12.7 mm overhead when
   open); tail is a plain 0.125 mm membrane lead with NO lock slots (§0),
   contact face per the OEM tail's existing orientation in CN1.
3. **First fit of a real connector:** seat one 10FDZ-BT dry (no solder) and
   confirm the boss and all ten pins drop in together without forcing — that is
   open item 1's 0.04 mm margin cashed on the bench. If the boss binds, ream
   that ONE board's NPTH or nip the boss; report before touching the others.
4. With the OEM membrane tail seated in `J_MEMBRANE` and the (coupon-passed)
   flex jumper to CN1: the OEM panel must remain FULLY operational through the
   interposer before anything connects to `J_KEY_MATRIX` (G6 before G7).
5. D4 (T3): present on `TP_M_D4`/`TP_C_D4` and `J_KEY_MATRIX.10`, passed through
   unchanged; its function is uncharacterized — downstream lockout owns it.

## 5. Isolation reminder

Do not "improve" this board with a ground pour, shield, or chassis strap. The
keypad domain floats (BRIEF §5); the sealed main board enforces its own
isolation comb on its side of the ribbon. The pourless state is DECLARED in
`source/assembly.yaml` and machine-graded — a future respin that quietly adds a
zone will not pass F-POUR without saying so.

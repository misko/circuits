# Board C-flex — the CN1 flex jumper, buildable spec

status: **SPEC COMPLETE — NOT ORDERABLE YET.** One number is missing and only
a physical measurement can supply it: the installed path length (§4).
part: Board C-flex — double-ended 10-way membrane tail
role: interposer `J_CN1_JUMPER` (10FDZ-BT) ⟷ appliance `CN1` (10FDZ-BT)
governs: ADR-0009 (Path A), ADR-0016 (custom FPC, buy-vs-build), ADR-0017 (lock slots)
written: 2026-07-27

---

## 0. The verdict up front

**There is no cable to buy.** 2.54 mm-pitch FFC is a legacy membrane-switch
pitch; nothing at LCSC, and the specialist options either miss the JST mating
window on a number (FlexConnection 2.54 mm FFC = **0.26 mm** vs a **0.075 …
0.200 mm** window) or exist only as unterminated 500 ft spools (Parlex PSR1635,
$650+). The search and the rejections are recorded in **ADR-0016**.

**What we build instead**: a custom **single-layer polyimide FPC, 0.12 mm
finished** — 0.005 mm from JST's 0.125 mm nominal — from **JLCPCB's flex
service** (MOQ 5, 4-5 day lead). It is orderable. It is **not** in this repo's
proven pipeline: there is no flex entry in `fab_tiers.yaml`, no flex DRC, no
escape check, no twin render. Its only gate is the **G1/G2 coupon** (T5).

**The one thing that will get "helpfully" fixed and must not be**: there is
**NO STIFFENER**. JLC's thinnest is PI 0.10 mm; 0.12 + 0.10 + adhesive ≈
**0.23 mm**, which is **over the 0.200 mm maximum**. A stiffener makes this part
not fit. See ADR-0016.

---

## 1. Stack-up

| item | spec | why |
|---|---|---|
| layers | **1** — copper on ONE face only | 2-layer with both faces windowed is ≈0.05 mm in the contact zone, **below** the 0.075 mm minimum (ADR-0016 option D) |
| dielectric | **50 µm polyimide** | gives the 0.12 mm build |
| finished thickness | **0.12 mm** | eFDZ p.1 mating part thickness 0.125 +0.075/−0.05 ⇒ window **0.075 … 0.200**. 0.12 sits +0.080 from the max, −0.045 from the min |
| alternate | 0.11 mm (25 µm dielectric) acceptable | also in window |
| **forbidden** | **0.07 mm** (25 µm dielectric, 1-layer) | **0.005 mm BELOW the minimum** |
| copper | **0.5 oz (18 µm)** | 0.735 Ω/m at 1.3 mm width; 150 mm ⇒ **0.11 Ω**. Current is keypad scan, µA-mA, against a 50 mA contact rating |
| coverlay | yellow PI on the **copper** face, **windows opened over both contact zones** | the opposite face is bare base PI |
| surface finish | **ENIG** (JLC's only FPC finish) | wiping ZIF contact; gold on tin-plated FDZ contacts |
| **stiffener** | **NONE, EITHER END. FORBIDDEN.** | see above and ADR-0016 |
| min static bend radius | 10 × 0.12 = **1.2 mm**; design to **≥ 3 mm** | install-once, no dynamic flexing |
| MOQ / lead | 5 pcs / 4-5 days (JLC published, 2026-07-27) | the G1 coupon is therefore free |

Nothing else on the flex: **no shield, no drain wire, no ground conductor, no
metal stiffener, no metal clip**. The keypad domain floats (BRIEF §5) and this
part is inside it.

---

## 2. Conductor geometry — both ends identical

From eFDZ p.3, *"Recommended dimensions for membrane switch lead"*, N = 10.
Origin: x from the tail's **conductor-1 edge**, y from the tail's **leading
(insertion) edge**.

| dim | value | note |
|---|---|---|
| tail width | **27.94 ±0.1** | (N+1) × 2.54 |
| conductors | **10** | |
| conductor width | **1.30 ±0.1** | in the contact zone |
| pitch | **2.54 ±0.05**, non-accumulating | eFDZ p.3 note 2 caps accumulation at ±0.05 |
| conductor 1 centre | x = **2.54 ±0.05** | edge margin |
| conductor 10 centre | x = **25.40** | ⇒ outer span **22.86 ±0.05** = the connector's A |
| contact zone (coverlay window) | y = 0 … **5.0 (+0.5/−0)** | matches eFDZ's own 5 ±0.2; never under-expose |
| leading-corner chamfer | 0.5 × 45°, both corners | insertion lead-in |
| **lock slot** ×2 | **1.2 ±0.1 wide × 3 ±0.2 long**, y = **5.0 … 8.0**, centres at x = **6.35** and **21.59** | = 3.81 ±0.1 inboard of each outer conductor centreline (ADR-0017) |
| conductor necking | conductors **2, 3, 8, 9** necked to **0.8 mm** over y = 4.7 … 8.3 only | the 1.2 mm slot exactly fills the 1.24 mm inter-conductor gap; necking buys **0.27 mm** copper-to-slot-edge. Necking is *below* the contact zone, so contact area is untouched |
| polarity notch | **2.0 × 1.0 mm** notch in the **conductor-1 edge at mid-length** | geometric, unrubbable, readable from both faces — see §5 |

```
        conductor-1 edge                                   conductor-10 edge
        |                                                                 |
   y=0  +---------------------------------------------------------------+   leading edge
        | ####  ####  ####  ####  ####  ####  ####  ####  ####  ####     |   contact zone,
        | ####  ####  ####  ####  ####  ####  ####  ####  ####  ####     |   coverlay OPEN
   y=5  | ####  ##[]##  ####  ####  ####  ####  ##[]##  ####  ####       |   0 .. 5.0 mm
        | ####  ##[]##  ####  ####  ####  ####  ##[]##  ####  ####       |   [] = lock slot
   y=8  | ####  ####  ####  ####  ####  ####  ####  ####  ####  ####     |   1.2 x 3.0
        :                       (coverlay from y=5.0)                    :
        x=2.54  5.08  7.62  ...                              25.40
             slot centre 6.35 ---^                    ^--- slot centre 21.59
        tail width 27.94
```

**The slots are the open question.** ADR-0017: JST's recommended lead *has*
them; ADR-0008 said an FDZ neither uses nor needs them; ADR-0005/D5 photographed
them on the OEM tail. The coupon (§6) settles it with one part.

---

## 3. Pin mapping — 1:1, and how "conductor 1" is defined

Conductor **k at end A = conductor k at end B**. Straight through, no crossover,
no reversal, on the same face.

| conductor | net | interposer `J_CN1_JUMPER` pin | notes |
|---|---|---|---|
| 1 | `KP_U1` | 1 | boss-end contact |
| 2 | `KP_U2` | 2 | |
| 3 | `KP_U3` | 3 | |
| 4 | `KP_U4` | 4 | |
| 5 | `KP_U5` | 5 | |
| 6 | `KP_U6` | 6 | |
| 7 | `KP_D1` | 7 | |
| 8 | `KP_D2` | 8 | |
| 9 | `KP_D3` | 9 | |
| 10 | `KP_D4` | 10 | function uncharacterised, T3 — passes through, locked out downstream |

(Verified against `07_releases/interposer-v1.0-2026-07-24/source/interposer.net`.)

**Conductor 1 = the conductor that lands on the BOSS-END contact**, at both
ends. That is the same convention the interposer uses (square pad, silk "1",
boss 2.54 mm outside it) and the same one
`01_docs/10fdz-bt-land-pattern-confirm.md` §4 asks the user to confirm at CN1.
JST's own circuit numbering is not needed and is not used.

---

## 4. Length — the one number that is missing

`L_tail = P + 40 mm`, where **P** = the measured path from the interposer's
`J_CN1_JUMPER` mouth to the appliance's `CN1` mouth, along the route the tail
will actually take (over the bend, not through the metal).

The +40 mm covers: two 3 mm bend radii, insertion depth at both ends (~8 mm
each), a service loop, and the flip-fold allowance of §5.

**Long is free; short is fatal.** Excess folds into a service loop. If P cannot
be measured before ordering, order at **L_tail = 150 mm** and fold — a 0.12 mm
flex with a 1.2 mm minimum radius tolerates it, and the whole part costs less
than the shipping.

Cannot be finalised from this repo. **This is the blocking input.**

---

## 5. Contact face and orientation — the silent-reversal trap

A 1-layer flex has contacts on **one** face. Which face must present at each
connector depends on how `CN1` sits in the appliance relative to
`J_CN1_JUMPER` on the interposer — geometry we do not have.

The design is **contacts on the SAME face at both ends** (a plain "straight"
tail). If fit-up shows the opposite handedness is needed:

> **Add ONE 180° TRANSVERSE fold** — fold axis running **across the tail's
> width**. A transverse fold flips the contact face and **preserves** the
> conductor order.
>
> **NEVER fold longitudinally** (axis along the tail's length). That flips the
> face **and reverses conductor order** — `KP_U1` ⟷ `KP_D4`, the exact
> zero-symptom bank swap `ORDER_README` §3 exists to prevent.

Self-identification without relying on a legend (JLC FPC legend availability is
not published — confirm at order, and if unavailable this still works):

- **which face** — the exposed **gold contacts are visible**. That face is the
  contact face.
- **which edge is conductor 1** — the **2.0 × 1.0 mm notch at mid-length** is on
  the conductor-1 edge. It is a cut in the outline: readable from both faces,
  cannot rub off, cannot be applied to the wrong side.

Insertion is self-keying: an FDZ has contacts on one side of its slot, so a
one-face tail physically cannot be inserted flipped and still conduct. Only the
*naming* is at risk, and §7's continuity map is what catches it.

---

## 6. What must be COUPON-TESTED before this ever touches the appliance

Binding, from ADR-0008/0009 and spec tension **T5**: **≥100 insertion cycles on
a sacrificial coupon, and NEVER a first fit on the OEM CN1.**

**The coupon is producible from the same order.** JLC's FPC MOQ is 5, so add
one extra design to the order (or panelise it beside the jumper): a **60 mm
double-ended tail, identical stack-up and end geometry, with ONE END SLOTTED and
ONE END PLAIN.** One part, one order, answers ADR-0017 against the real
connector.

Test on a **spare 10FDZ-BT soldered to scrap board** — not on the interposer,
and under no circumstances on CN1.

| # | test | instrument | PASS | FAIL / flag |
|---|---|---|---|---|
| C1 | contact-zone thickness, before anything | micrometer, 3 points per end | **0.075 … 0.200 mm**, target 0.12 | outside ⇒ scrap the batch, the stack-up was built wrong |
| C2 | tail width, conductor pitch, outer span | caliper / optical | 27.94 ±0.1 · 2.54 ±0.05 · 22.86 ±0.05 | outside ⇒ fab tolerance problem, re-order |
| C3 | slider closes and **locks** — slotted end | by hand | closes fully, tail does not walk out under light pull | if it will not close, the slot geometry is wrong |
| C4 | slider closes and holds — plain end | by hand | closes fully | **C3 vs C4 is the ADR-0017 answer** |
| C5 | axial pull-out force, both ends, slider locked | spring gauge | *record the number*, both variants | no threshold published by JST — the comparison is the result |
| C6 | **≥100 insertion / extraction cycles** | count them | completes without delamination, conductor lift, or coverlay peel | any of those ⇒ redesign |
| C7 | 10-line end-to-end resistance at cycle 0, 10, 25, 50, 75, 100 | 4-wire if available, else record probe offset | every line **≤ 2 Ω** and stable | **> 5 Ω on any line ⇒ FLAG**: eFDZ specs 10 Ω initial / 15 Ω after test per contact, and the full interposer path is ~5 contacts in series with a **20-100 Ω** key press (T1). If the measurement is genuinely tens of ohms, the RKEY solder-select field (ADR-0006) must be re-qualified with the interposer path in circuit |
| C8 | insulation between adjacent conductors after C6 | meter, 10 pairs | no continuity between any two lines | any short ⇒ redesign |
| C9 | visual on the ENIG after C6 | loupe | no wear-through to copper | wear-through ⇒ 2 µm ENIG instead of 1 µm |

Only after **C1-C9 pass** does the real jumper go into `J_CN1_JUMPER`, and only
after that does anything go into CN1 — G2, then the `ORDER_README` §4 continuity
map, then the OEM panel must still be fully operational through the interposer
(G6) before the main board is connected (G7).

---

## 7. Before the appliance — the continuity map

With the real jumper fitted between the interposer and a bench 10FDZ-BT (not
CN1): beep conductor k of the jumper against interposer `TP_C_U1 … TP_C_D4` and
confirm the mapping in §3 exactly. Then confirm **no** continuity between any
two different lines, and **no** continuity from any line to the interposer's
mounting holes (NPTH, floating by design).

A reversed jumper passes every electrical test except this one. That is why it
runs before the appliance, not after.

---

## 8. What is NOT done here

- **The gerber / fab drawing.** It is a mechanical transcription of §2 plus one
  length, and the length (§4) does not exist yet. It must contain: outline
  (incl. both lock slots, both chamfers, the polarity notch), the single copper
  layer, the coverlay layer with both contact windows, and a dimensioned drawing
  carrying the §1 stack-up, the ENIG call-out, and **"NO STIFFENER"** in bold.
- **Ordering.** Blocked on §4, and on nothing else.
- **The FDZ land-pattern gate** (`01_docs/10fdz-bt-land-pattern-confirm.md`) is
  independent of this part — it blocks the interposer *board*, not the jumper.
  Answering its **S1/S2** items does feed §2's slot question.

# Red-team topology RE-REVIEW — usb-hub-3s-v3 (internal usb_hub_3s_v2)

- reviewer: independent power-electronics red-team (zero-context, fresh judgement)
- date: 2026-07-22
- scope: POWER TOPOLOGY ONLY (input protection, converter, ratings/derating,
  output/USB-C). Physical placement / DRC excluded (separate layout review).
- sources read (design source, no prior memo): BRIEF.md, ARCHITECTURE.md,
  decisions/0001, power_tree.yaml, nets.yaml, electrical_invariants.yaml,
  03_tscircuit/src/usb_hub_3s_v2.tsx (schematic ground truth),
  06_build/netlists/usb_hub_3s_v2.net (netlist ground truth), and every
  power-path part.yaml (fuse 3568, LM5116, AON6403, AON6354, MWSA1206S,
  SMBJ15A, BZT52C12, TPS2557, TPS2513A, KNM2/C2982822, 25121WF/C127692,
  TYPE-C-31-M-12A).

---

## HEADLINE VERDICT: **ORDER**

The power topology is sound and buildable. No P0. No hard P1. The one deviation
from the written spec (buck UVLO turn-on above the stated 9.0 V floor) is a
low-battery-corner note, not a function/safety killer — see F-2.1 (rated P2,
conditional P1 only if 9.0 V cold-start is a firm requirement). Everything else
is P2 derating headroom or stale-doc hygiene. Order it; fold the P2s into the
next rev.

## RT-T1 fuse verdict: **YES — 10 A is correctly sized.**

- **Derived worst-case input trunk current:** 6.8 A continuous.
  - Rails (power_tree.yaml): USB-A 5 V x 6 A = 30 W; USB-C 5 V x 5 A = 25 W;
    total out = 55 W. Input = 55 / 0.9 = 61.1 W. At Vin_min 9.0 V:
    **I_trunk = 61.1 / 9.0 = 6.79 A ≈ 6.8 A** (matches ARCHITECTURE "6.8 A @ 9 V").
  - At the true running floor (LM5116 UVLO falling ≈ 8.84 V): 61.1 / 8.84 = 6.9 A.
  - Transient all-burst corner (3x USB-A @ 2.5 A + USB-C @ 5 A = 62.5 W out,
    69.4 W in): 69.4 / 9.0 = **7.7 A** — a plug-in transient, not a rated
    steady state (declared USB-A steady max is 6 A).
- **Too-small direction (nuisance trip): NO.**
  - Continuous loading 6.8 / 10 = 68 % (7.7 / 10 = 77 % even at all-burst). A
    MINI blade fuse carries 100 % of rating indefinitely and 110 % (11 A) for
    100+ h, so neither the 6.8 A steady nor the 7.7 A burst approaches opening.
  - Inrush: VIN bulk is only ~240 µF effective (2x100 µF/35 V polymer + ~40 µF
    DC-biased ceramic — NOT the 2100 µF the MPN string suggests; the part is
    100 µF). The two bucks are soft-started (CSS = 10 nF), and Q1's gate charges
    through a 100 k pulldown so its turn-on is gentle. Inrush I²t (charging
    240 µF from 12.6 V through a few-mΩ-to-tens-of-mΩ loop) ≈ 1–2 A²s, far below
    a 10 A MINI blade's melting I²t (tens of A²s). No inrush trip.
- **Too-large direction (fails to protect): NO — 10 A is the *right* size.**
  - 10 A = 1.47x continuous-max — a textbook 1.25–1.5x fuse ratio. It opens on
    sustained overloads in the ~10–20 A+ band. The prior 20 A element (2.9x the
    6.8 A worst case, a stale carry-over of v1/v2's 15.5 A buck-boost trunk) left
    the ~8–27 A overload band effectively unprotected on this 6.8 A board; 10 A
    closes it while still clearing steady + burst + inrush.
  - Protected element: XT60 (60 A+), Q1 AON6403 (Id 85 A), and the VIN
    F.Cu-pour + In2-plane trunk all sit far above 10 A, so the fuse's job is to
    interrupt a downstream fault before the wiring/pack path is stressed. A 3S
    LiPo can source 100 A+ into a hard fault; that is within a MINI blade's
    32 V-DC interrupt rating, and 12.6 V << the 32 V holder/element voltage.
- **Class:** hand-inserted MINI blade element (e.g. Littelfuse 0297010,
  fast-acting automotive time-current) in a machine-placed Keystone-3568 holder.
  Protection depends on the correct blade being fitted — see F-4.4.

**Net: 10 A sits correctly between the 6.8–7.7 A continuous/burst band and the
protected-element limits. Confirmed independently.**

---

## Area 1 — INPUT PROTECTION CHAIN

Chain (tsx + netlist): XT60 (J1) -> F1 10 A MINI blade -> Q1 reverse-polarity
P-FET -> D1 TVS on VIN -> VIN bulk -> both buck inputs. Verified in the netlist.

**F-1.1 — Fuse 10 A — CORRECT (verdict above, RT-T1).** Not a defect.

**F-1.2 — Reverse-polarity P-FET — CORRECT. [no action]**
Q1 AON6403 high-side P-FET: D = VBAT_F (battery side), S = VIN, G = RPP_G with
R1 100 k gate pulldown and D2 BZT52C12 (12 V) source-gate clamp. On correct
polarity the body diode conducts on first contact, then Vgs = -Vin (~-12 V)
enhances it (Rds 3.1 mΩ). On a reversed pack the body diode is reverse-biased
and Vgs ≈ 0 → Q1 off, VIN isolated near 0 V. I traced every VBAT_F node: the
only path to GND is Q1's blocked body diode — **no crowbar path** on reversal.
Ratings: Vds -30 V vs -12.6 V reverse (2.4x); Vgs clamped -12 V vs ±20 V.

**F-1.3 — TVS placement (D1 on VIN, after Q1) — CORRECT. [no action]**
SMBJ15A cathode on VIN, anode to GND, behind Q1's blocking body diode. This is
the "D1-corrected" arrangement: a reversed pack cannot forward-bias the TVS into
a crowbar (which it would if the TVS were on VBAT_F). Standoff 15 V > 12.6 V max
(2.4 V headroom, fine for a battery input with no load-dump source);
Vbr(min) 16.7 V; the pack physically cannot exceed 12.6 V so the TVS only fires
on hot-plug inductive transients.

**F-2.1 — UVLO turn-on (9.65 V rising / 8.84 V falling) is ABOVE the 9.0 V spec
floor — P2 (conditional P1).**
- Divider 49.9 k / 6.98 k on VIN into the LM5116 UVLO pin (1.215 V ref + 5 µA
  hysteresis). Rising ≈ 9.65–9.9 V, falling ≈ 8.84 V.
- Scenario: BRIEF states the input range is 9–12.6 V. A pack presented at
  9.0–9.65 V at rest will **not cold-start** the bucks. (Once running it holds
  down to 8.84 V via hysteresis.) Near the bottom of charge a load-sag dip
  below 8.84 V would UVLO-hiccup.
- Why it's P2, not worse: a 3S LiPo only reaches ~9.65 V at ~90 %+ discharge and
  should not be taken below 3.0–3.3 V/cell (9.0–9.9 V) anyway, so the UVLO
  doubles as a healthy over-discharge cutoff and the board works across the
  entire useful battery life. It is a spec-corner deviation, not a failure.
- Fix / decision: if 9.0 V cold-start is a firm requirement, this is a P1 — drop
  the top divider (~44.2 k / 6.98 k → ~8.9 V rising). Otherwise document that
  true min operating voltage is ~9.65 V (cold) / 8.84 V (running). **Confirm the
  9.0 V requirement with the user.**

**F-3.1 — TVS clamp corner (24.4 V) vs input ceramics (25 V) — P2.**
The 10 µF/25 V (C77100) VIN ceramics sit at 24.4 V = 98 % of rating during a
worst-case SMBJ15A clamp event (and the clamp rises further above rated Ipp).
Mitigating: normal max is only 12.6 V; the 35 V polymer bulk (C1/C2) absorbs
most surge energy; the event is transient/rare. Acceptable now; prefer 50 V
input ceramics next rev for clean coordination under the clamp corner.

No active over-voltage cutoff — not required (fixed 3S pack, no sustained OV
source). [no action]

---

## Area 2 — CONVERTER TOPOLOGY

**F-2.2 — LM5116 synchronous buck x2 — CORRECT for the Vin/Vout relation. [no action]**
Vin 9–12.6 V is always > Vout 5 V → step-down BUCK is right (E-TOPO all-buck).
Two independent controllers: U2 → 5VA (USB-A, 6 A), U11 → 5VC (USB-C VBUS, 5 A).
Each: HS + LS AON6354 (synchronous, efficient), 6.8 µH inductor, 10 mΩ shunt.

Config sanity (all present and correct):
- FB 3.74 k / 1.21 k → Vout = 1.215 x (1 + 3.74/1.21) = **4.97 V ≈ 5.0 V**. OK.
- Compensation: 18 k + 3.3 nF (Type-II) + 100 pF on COMP — present. OK.
- Slope comp / ramp: 330 pF on RAMP + 12.4 k RT — present. OK.
- Soft-start: 10 nF on SS — present (also softens turn-on inrush). OK.
- Boot diode VCC→HB (1N4148WS) + 1 µF boot cap + 1 µF VCC cap — present
  (LM5116 has no internal boot diode). OK.
- Current limit: 110 mV / 10 mΩ ≈ **11 A valley → ~12.5 A peak**, below inductor
  Isat 15.2 A; comfortably above the 5–6 A rail loads. OK.
- CS/CSG Kelvin across the LS-source→PGND shunt via 0 Ω links — faithfully
  reproduces TI SNVS499I Fig 7-1 (5 V/7 A worked design). OK.
- Capability: a 100 V controller on a 12.6 V app is over-margined but correct;
  VCC LDO has enough headroom at Vin 9 V. OK.

**F-2.3 — VCCX tied to GND — P2 (minor efficiency).**
Safe default (internal LDO always runs from VIN). Since Vout is 5 V, tying VCCX
to the buck's own 5 V output would offload the VCC LDO and cut a fraction of a
watt of controller dissipation. Optional next-rev efficiency tweak; not a defect.

---

## Area 3 — RATINGS & DERATING

**F-3.2 — Buck FETs AON6354 correctly rated, but part.yaml doc is CONTAMINATED — P2 (doc hygiene).**
- Electrically correct: Vds 30 V vs 12.6 V + switch-node ring (~2.4x nominal;
  vspike_10us 36 V covers ring); logic-level, fully enhanced by the 7.4 V VCC
  gate drive (Rds spec'd at 4.5 V); Id 83 A ≫ 8.4 A peak. HS Vgs via bootstrap
  ~6.7 V, also fine. No snubber needed for a 30 V FET on a 12.6 V rail.
- Doc defect: `02_parts/AON6354/part.yaml` gotchas/layout carry **IP6559
  buck-boost** references from a different design — "IP6559 ~5 V gate drive",
  "30 V vs 21 V max VOUT_PD", "LX snubbers + SMAJ30A clamps per IP6559 Fig.8",
  "IP6559 H-bridge 4 units", "7 pcs/board". v3 has **4** AON6354 (Q2–Q5,
  confirmed in netlist), an LM5116 not an IP6559, and **no** SMAJ30A/LX snubbers
  exist in the tsx. Stale, misleading text — scrub it. Not electrical.

**F-3.3 — Reverse P-FET AON6403 dissipation — OK (stale number in doc).**
At 6.8 A: 6.8² x 3.1 mΩ = 0.14 W. The part.yaml "at 15.5A worst: ~0.75W" is a
stale v1/v2 (buck-boost, 15.5 A) figure. Cosmetic; roll into F-3.2 hygiene.

**F-3.4 — Inductor MWSA1206S-6R8 (6.8 µH) — OK.**
Isat 15.2 A (20 % rolloff) vs 8.4 A normal peak (USB-A burst, 1.8x) and vs the
~12.5 A current-limit peak (1.2x); Irms 10 A vs ~7.5 A. Saturation is not
reached even in current limit. OK.

**F-3.5 — Output ceramics 100 µF/6.3 V on the 5 V rails — P2 (derating).**
6.3 V rating at 5 V = 79 % (within the <80 % guideline, but thin on overshoot);
a 6.3 V 1210 X5R at 5 V DC bias loses well over half its capacitance. Functional
because 4x are paralleled per rail (nameplate 400 µF → still ample effective).
Prefer 10 V/16 V next rev for overshoot margin and less bias loss.

**F-3.6 — VIN bulk / shunt — OK.**
VIN: 2x100 µF/35 V polymer (35 V ≫ 24.4 V clamp) + 4x10 µF/25 V ceramic per buck
hot-loop. Adequate; no oversized electrolytic needed at this current (the 2100 µF
MPN string is misleading — the part is 100 µF). Shunt 10 mΩ/1 W 2512: 0.49 W at
7 A < 1 W. OK.

---

## Area 4 — OUTPUT / USB-C (5 V/5 A, plain, no PD)

**F-4.1 — 5 V/5 A delivery — CORRECT. [no action]**
Buck C (5 A) → VBUS across **all four** connector VBUS contacts
(J5 A4/A9/B4/B9 all on net 5VC, confirmed in netlist) = 1.25 A/contact, within
the TYPE-C-31-M-12A 5 A-across-4-pins rating; 4 GND contacts likewise. VBUS bulk
C49/C50 (2x10 µF) at the receptacle. This is the intended plain-rail path.

**F-4.2 — CC advertisement (Rp = 10 k x2 to 5VC) — CORRECT per ADR-0001. [no action]**
R28/R29 = 10 k from CC1/CC2 to 5VC (VBUS) advertises a **3.0 A** source-present +
orientation (10 k is the max legal Rp band). The Pi with PSU_MAX_CURRENT=5000
skips PD and draws the full 5 A; a generic USB-C sink would cap at 3 A. Roles are
correct (board = source/DFP with Rp; Pi = sink/UFP with Rd). Matches the ADR
exactly. USBLC6 data ESD (U12) + BC1.2 DCP short (R27) present for completeness.

**F-4.3 — No output current-limit / e-fuse on USB-C VBUS — P2.**
ARCHITECTURE lists an "optional simple e-fuse" on VBUS; it is **not populated**.
A hard VBUS short is caught only by buck-C's hiccup current limit (~11 A) plus
the 10 A input fuse — i.e. the buck self-protects, but there is no per-port fast
limiter and a short pulls ~11 A until hiccup. Acceptable for a dedicated supply;
populate a current-limit switch (single part) next rev to harden the Pi port.

**F-4.4 — No output OVP on the 5 V rails — P2.**
A buck HS-FET short puts ~12.6 V onto whatever is attached (the Pi on 5VC, USB
devices on 5VA). Single-fault, and a common accepted tradeoff, but worth noting
for the 5 A Pi port — an OV clamp/crowbar on 5VC would make it single-fault safe.

**F-4.5 — Always-on VBUS (not gated on CC attach) — P2 (compliance note).**
The buck output is always live on the connector rather than switched on after CC
detects a sink. Safe (5 V, current-limited) and consistent with this port being
explicitly Pi-dedicated / non-PD-compliant per ADR-0001; noted for completeness.

**F-4.6 — USB-A ports — OK.**
TPS2557 per-port switch, ILIM = 36.5 k → 2.72–3.29 A current limit (above the
2.5 A burst spec — correct); per-port USBLC6 ESD; TPS2513A DCP for BC1.2/Apple
charging advertisement. Aggregate: 3x max-limit (9.9 A) still < buck-A limit
(~11 A). OK.

**F-4.7 — Fuse element is hand-inserted — P2 (assembly).**
The 10 A protection only exists if the correct MINI blade is fitted into the
holder (element is a hand-solder/insert item, not machine-placed). Ensure the
ORDER_README + silk call out "10 A MINI" and the holder is not shipped empty or
with a wrong-value blade.

---

## Findings summary

| id | area | severity | one-liner |
|----|------|----------|-----------|
| RT-T1 | fuse | verdict | **10 A correct** (6.8 A cont / 7.7 A burst worst case; 1.47x; closes the band the 20 A left open) |
| F-1.2 | input | OK | reverse-polarity P-FET correct, no crowbar path on reversal |
| F-1.3 | input | OK | TVS on VIN behind Q1 — correct (no reverse crowbar) |
| F-2.1 | input/conv | **P2 (cond. P1)** | UVLO turn-on 9.65 V > 9.0 V spec floor — confirm 9.0 V cold-start need |
| F-3.1 | derating | P2 | 25 V input ceramics at 98 % of rating at the 24.4 V TVS clamp corner |
| F-2.2 | converter | OK | LM5116 buck config sane (FB=5.0 V, comp/slope/SS present, Ilim<Isat) |
| F-2.3 | converter | P2 | VCCX to GND — safe; tie to 5Vout for minor efficiency next rev |
| F-3.2 | ratings | P2 | AON6354 correct but part.yaml doc contaminated with IP6559/snubber/7-pcs text |
| F-3.4 | ratings | OK | inductor Isat 15.2 A vs 8.4 A peak / 12.5 A limit — margin fine |
| F-3.5 | derating | P2 | 100 µF/6.3 V output ceramics on 5 V — thin margin + heavy bias loss (4x parallel saves it) |
| F-4.1 | USB-C | OK | 5 A over 4 paralleled VBUS pins — correct, netlist-confirmed |
| F-4.2 | USB-C | OK | CC Rp 10 k advertises 3 A source; Pi override draws 5 A — per ADR |
| F-4.3 | USB-C | P2 | no VBUS e-fuse/current-limit — buck hiccup is the only short protection |
| F-4.4 | USB-C | P2 | no output OVP — buck FET short → 12.6 V to the Pi (single-fault) |
| F-4.5 | USB-C | P2 | always-on VBUS (not CC-gated) — safe, minor compliance deviation |
| F-4.7 | assembly | P2 | 10 A protection depends on the correct hand-inserted blade |

**No P0. No unconditional P1.** Order the board; address the P2s (and decide
F-2.1) in the next rev.

---

## Reconciliation vs prior review (2026-07-22_v1.0_redteam_topology.md)

Read only **after** writing everything above. The prior review was taken at an
**earlier commit (526f98f)** against the routed board; mine is at the current
source state. The delta between them is exactly the two fixes that have since
landed — so the two reviews **agree**, and the disagreement in headline verdict
is a state change, not a difference of judgement.

**On the fuse (the reason for this re-review) — full agreement, and my derivation
is independent of theirs.** The prior review returned **DO-NOT-ORDER** on RT-T1
because at commit 526f98f the fuse was *doubly specified* — silk "10A" vs
`part.yaml` "20A / 0297020 / 20A > 15.5A" — and it judged the 20 A element
oversized (stale v1 15.5 A) and leaving the ~8–27 A overload band unprotected,
prescribing **reconcile to 10 A**. That fix has since landed: `02_parts/3568`
now specifies a **10 A** blade (0297010) with a matching RT-T1 note. I derived
10 A as correct from first principles (6.8 A worst-case trunk, 1.47x, no nuisance
trip, closes the 8–27 A band) **before** reading their memo, and reached the same
number and the same reasoning. The prior P1 is therefore **CLOSED**, which is why
my headline is **ORDER** rather than DO-NOT-ORDER. Same call, updated state.

**RT-T6 (their P2) is also now CLOSED.** The prior review flagged
`03_src/rules/electrical_invariants.yaml` as *absent* (ADR-0001's promised
machine guard missing). That file now **exists** and asserts J5 VBUS pads on
5VC + CC1/CC2 Rp pull-ups on 5VC (with an in-file "RT-T6 fix" note). The no-PD /
VBUS==5VC / CC-Rp intent is now machine-checkable, as they asked.

**Where we agree (unchanged, both P2):**
- Input ceramics 25 V vs 24.4 V TVS clamp corner — their RT-T2 = my F-3.1.
- UVLO 9.65 V vs 9.0 V spec floor — their RT-T3 = my F-2.1 (both note "amend
  spec or lower divider"; I add the conditional-P1 framing).
- Output ceramics 100 µF/6.3 V on 5 V — their RT-T5 = my F-3.5.
- No USB-C port-local current limit — their RT-T4 = my F-4.3/F-4.4.
- AON6354 part.yaml IP6559/snubber stale text — their "stale-text hygiene" =
  my F-3.2 (both: ratings correct, prose wrong).
- All PASS items: reverse-polarity FET + Vgs clamp, TVS directionality/placement,
  VBUS==5VC, CC Rp 10 k = 3.0 A on the 5 V pull-up, FB → 4.97 V, current limit
  ~11 A within FET/inductor SOA.

**Where they add something I under-weighted (I concede the point):** RT-T4's
**reverse back-feed** path — because VBUS is a raw synchronous-buck output with no
ORing/blocking, a *powered* source mistakenly plugged into this **output** port
can sink current 5VC → L2 → SW → HS body diode → VIN, back-feeding the pack.
Bounded (low single-amp, and it requires misusing a Pi-*dedicated* output), so it
stays P2 — but it strengthens the case for populating the ADR-optional VBUS
current-limit switch **with reverse blocking** (my F-4.3). Good catch by the prior
pass; folded in.

**Scope difference (not a disagreement):** the prior review dumped the immutable
routed board (pad→net via pcbnew, DRC 0/0/0, silk census) to confirm board==netlist;
I worked from the design source + exported netlist (layout/DRC is out of my scope).
Our netlist-level facts match on every spot-check (input chain, both bucks, all
ports, USB-C VBUS/CC).

**Net:** independent agreement. The prior review's sole order-blocker (RT-T1) and
its process P2 (RT-T6) are both fixed in the current source; the remaining items
are the same P2 set both passes identified. **Headline stays ORDER.**

# ADR-0016 — The CN1 flex jumper is a CUSTOM 1-layer FPC, because no cable you can buy fits

status: accepted
date: 2026-07-27
tags: flex, connectors, sourcing, out-of-pipeline, coupon
depends-on: 0008 (CN1 = 10FDZ-BT), 0009 (Path A — the jumper is a separate part)
spec-tension: T5 (flex fabrication outside the proven rigid pipeline)

## Context

ADR-0009 (Path A, user-chosen 2026-07-24) names a "dumb double-ended 10-finger
flex jumper" as the only out-of-pipeline item in Board C: interposer
`J_CN1_JUMPER` (10FDZ-BT) → jumper → appliance `CN1` (10FDZ-BT). It was never
designed. This ADR decides **what it physically is** and, first, whether it has
to be custom at all.

The FDZ is unforgiving in exactly one dimension. eFDZ p.1:

> Compatible membrane switch lead: conductor pitch **2.54 mm**, conductor width
> **1.3 mm**, mating part thickness **0.125 +0.075 / −0.05 mm**.

That is a hard mating window of **0.075 … 0.200 mm**. Everything below is
decided by whether a candidate lands inside it.

Second constraint, from this repo rather than from JST: `skills/kicad-pcb/
references/fab_tiers.yaml` has **no flex tier**. There is no flex DRC, no
escape check, no twin render, no ampacity model. Whatever we choose is
out-of-pipeline by construction (T5) and its only gate is the G1/G2 coupon.

## Options

**A. Buy a ready-made FFC jumper (the outcome we wanted).**
Searched LCSC, DigiKey, Mouser and two specialist FFC houses, 2026-07-27.
2.54 mm pitch is a legacy membrane-switch pitch; the volume market is
0.5 / 1.0 / 1.25 mm.
- **LCSC** — 10-way FFC stocked at 0.5 mm pitch (e.g. C47686). **Nothing at
  2.54 mm.** No LCSC code exists to give.
- **FlexConnection 2.54 mm FFC** (configure-to-order): conductor 0.1 × 1.27 mm,
  2-33 ways, 25-1000 mm — **total thickness 0.26 mm**. That is **0.06 mm over
  the FDZ maximum, 30 % out of spec**. REJECTED on a number.
- **WPP 599** (configure-to-order): 2.54 mm pitch, conductor 1.27 × 0.100 mm,
  PET 2 × 45 µm ⇒ ≈ 0.19 mm body. *Inside* the window, with 0.01 mm to spare,
  but the contact-zone thickness is not a published controlled dimension, there
  is no stock code, no MOQ and no lead time, and the end style (which face the
  stripped conductors present) is a catalogue variable we would be guessing at.
  REJECTED as unquotable.
- **Parlex PSR1635 family** (DigiKey): 2.54 mm pitch flat flex, ≈ 0.18 mm total,
  but sold **unterminated on 500 ft spools at $650+**. Ends would be
  hand-stripped. REJECTED on form factor and cost.

There is no "buy this cable instead" answer. That was checked, not assumed.

**B. Membrane-switch house — printed silver-on-PET tail, the OEM construction.**
Exactly right technically (it is literally what the OEM tail is) and exactly
what JST specifies as the compatible lead. Vendor-assisted CAD, screen-print
tooling, minimum runs in the hundreds. REJECTED for a one-off: cost and lead
time dominated by tooling we would use once.

**C. Custom 1-layer FPC from JLCPCB's flex service.** Published capability
(fetched 2026-07-27): 1-4 layers; 1-layer finished thickness **0.07 / 0.11 mm**
at 25 µm dielectric and **0.12 mm** at 50 µm dielectric; copper 0.5 oz / 1 oz;
ENIG only; coverlay yellow/black/white/transparent; **MOQ 5 pcs, 4-5 day lead**.
- **0.12 mm lands 0.005 mm from JST's 0.125 nominal.** Margin to the window:
  +0.080 to the maximum, −0.045 to the minimum.
- 0.07 mm is **0.005 mm below the 0.075 mm minimum** — rejected.
- MOQ 5 makes the sacrificial G1 coupon free.
- Same vendor as the rigid boards, but **not the same pipeline** — none of the
  rigid gates apply.

**D. Custom 2-layer FPC with contacts mirrored on both faces**, to make the
contact-face handedness a non-issue. Attractive until you do the arithmetic: a
2-layer flex with the coverlay opened on **both** faces in the contact window is
12 µm + 25 µm + 12 µm ≈ **0.05 mm** there — **below the 0.075 mm minimum**, so
the ZIF would not grip. The window that makes the trick work is the window that
breaks the fit. REJECTED on a number.

## Decision

**Option C.** Board C-flex is a **custom single-layer polyimide FPC**,
50 µm dielectric, **0.12 mm finished thickness**, 0.5 oz copper, coverlay on the
copper face with windows opened over both contact zones, **ENIG**, and
**NO STIFFENER AT EITHER END**.

The no-stiffener rule is the counter-intuitive one and it is not negotiable:
JLC's thinnest stiffener is **PI 0.10 mm**, which with adhesive puts the tail at
**≈ 0.23 mm — over the 0.200 mm maximum**. Every instinct and every FFC
datasheet says "stiffen the insertion end". Here it is exactly the thing that
makes the part not fit. The FDZ is a *membrane-switch* ZIF: it is built to clamp
a bare 0.125 mm film, and it supplies its own clamping force.

Full geometry, mapping, length rule and coupon plan: `01_docs/flex-jumper-spec.md`.

## Consequences

- **Out-of-pipeline, permanently.** No `fab_tiers.yaml` entry, no DRC, no
  escape check, no twin, no CPL. The deliverable is a hand-authored gerber +
  fab drawing, and its only real gate is the **G1/G2 coupon** (ADR-0008/0009,
  T5). It must never be graded as if a rigid release had passed.
- **Self-supplied, DO-NOT-SUBSTITUTE**, same posture as the 10FDZ-BT itself:
  never on a JLC assembly BOM, never substituted by "an FFC of about the right
  size". An 0.26 mm FFC will physically enter the connector and appear to work
  while over-stressing the clamp — a substitution here fails quietly.
- **Series resistance enters the keypad path.** The jumper adds two more FDZ
  contact interfaces per line. eFDZ p.1 specs **10 Ω initial / 15 Ω after test
  per contact**; the full interposer path puts ~5 connector interfaces in series
  with a key press the brief measures at **20-100 Ω** (T1). Worst-case-to-spec
  that is 50-75 Ω added to a 20-100 Ω signal. Real tin contacts are milliohms,
  so this is very likely a non-event — but it is now a **measured** number on the
  coupon, not an assumption, and if the measurement is more than a few ohms the
  RKEY solder-select field (ADR-0006) must be re-qualified with the interposer
  path in circuit.
- **The stiffener prohibition must survive review.** Anyone reviewing this part
  against normal FFC practice will flag the missing stiffener as a defect. It is
  recorded here so the "fix" cannot be applied silently.
- **Keypad-domain isolation carries over unchanged**: 10 conductors and nothing
  else. No shield, no drain, no ground, no metal stiffener, no metal P-clip, no
  chassis bond (BRIEF §5).
- Ordering the flex needs a length, and the length needs a physical measurement
  the user has not taken yet. The part cannot be ordered today; the spec can be
  finished today.

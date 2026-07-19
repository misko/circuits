# ORDER_README — crow-array-pod v1.1 (2026-07-19)

v1.1 supersedes v1.0 (never ordered-assembled in anger): J1 is now an
RJ45 jack (RJHSE-5384, same part as every crow-array-central port) per
the user's A4 request — see 01_docs/decisions/0004-rj45-termination.md.

## JLC order options (PCB)

- 2 layers, 94.5 x 44.5 mm, STANDARD options only (min drill 0.3mm,
  0.6/0.3 vias — NO advanced/small-via option needed).
- Qty: **10** boards (6 pods + spares). 1.6mm thickness REQUIRED (the
  ADR-0004 lid-clearance math assumes 1.6mm), any color (black hides best
  outdoors), HASL or ENIG (ENIG preferred outdoors).
- Upload `crow_array_pod_gerbers.zip` to the PCB order; `bom.csv` +
  `cpl.csv` to SMT assembly (top side, 15 coded lines / 25 placements).

## Order-day checklist (before paying)

1. **Stock re-check**: `python3 jlc_stock_check.py bom.csv --min-stock 10`
   — especially **C22359707 (CMT-8504 transducer): stock was 182 on
   2026-07-19** (need 10). If it dropped below need: mark the BZ1 line
   Do-Not-Place and hand-solder from Digi-Key (list below).
2. **U1 rotation in the 3D preview** (MANDATORY, adjudicated ROT-DB item):
   OPA1678 pin-1 dot must sit at the chip's TOP-LEFT (NW) corner when the
   NOT ETHERNET banner reads upright (pin columns run N-S). The rotations-db
   applied 270; the twin's EDA-frame fit suggested 90 — the preview is the
   tie-breaker. If the preview shows pin 1 SE, rotate the CPL entry 180.
3. **D2 (SS14) cathode band**: band = pad 1 = the pad marked with the
   silk "K". Preview diode band orientations vary per reel — eyeball it.
4. **C1 electrolytic**: negative stripe must be on the pad AWAY from the
   silk "+" mark.
5. Qty > refs on small passives = attrition padding, normal.
6. Layer count 2 in the order form.

## Hand-solder list (uncoded lines, Digi-Key order)

| Ref | Part | Digi-Key | Note |
|---|---|---|---|
| J1 | Amphenol RJHSE-5384 RJ45 jack | RJHSE-5384-ND ($2.14, 9.8k stock 2026-07-17) | THT: 8 contacts + 4 LED tails + 2 shield tails + 2 snap-in posts. JLC consign-only (stock 0) by design. The CENTRAL board orders 8 of the same part — combine the Digi-Key line. |
| J2 + mic | PUI AOM-5024L-HD-R electret capsule | 668-1538-ND | capsule mounts in the enclosure cavity on ~40mm twisted leads to the MIC+/MIC- pads. SOLDER THE CAPSULE FAST: <=2s per terminal, <=360C (datasheet handling limit) |
| BZ1 fallback | CMT-8504-100-SMT-TR | 102-CMT-8504-100-SMT-TR-ND | ONLY if JLC stock ran out (see checklist 1) — hand-reflow, watch the + pad (top-left, silk +) |
| D3 (optional) | SMAJ6.0A TVS | SMAJ6.0ALFCT-ND | DNP by design; fit only when trialing the TVS clamp (remove D2 first — ADR-0002) |
| L1 (optional) | Wuerth 744227S WE-SL2 CM choke | 732-1591-1-ND | DNP EMI reserve; to fit: remove R13/R14 (0R), reflow choke (D7) |

Per-pod hand work: 16 jack joints (8 contacts + 4 LED tails soldered for
mechanical retention even though NC + 2 shield tails; the 2 posts snap in)
+ 2 mic-lead joints.

## RJ45 fit + orientation inside the 1551WY (ADR-0004 — READ IT)

- Jack opening faces WEST (the gland wall). The jack + any inserted plug
  sit inside the lid's 81x31 full-height recess; nominal clearance to the
  lid is only **0.24mm** over the jack body, and the jack's sprung top
  EMI tabs will TOUCH the polycarbonate lid and compress — normal.
- **FIRST-ARTICLE GATE: assemble ONE pod, insert a crimped plug, and
  close the lid fully (gasket seated, 4 cover screws) BEFORE building
  the fleet.** If the lid binds on the jack: flatten or trim the two top
  EMI tabs (shield bond is DNP anyway); documented fallback part is the
  RJHSE-L384 low-profile (12.70mm) — verify its hole pattern first.
- Cable entry sequence (per pod): pass the UNTERMINATED Cat5e through
  the M12 gland, THEN crimp the plug inside, then insert (the plug does
  not fit through the gland). **Solid-core-rated RJ45 plugs REQUIRED**
  (24AWG solid Cat5e; standard stranded-only plugs make intermittent
  contact on solid core). Use BOOTLESS or slim-boot plugs — a full boot
  fouls the lid's perimeter band (only 7.9mm headroom west of the jack).
  Crimp T568B (straight-through); the silk legend west of the jack gives
  the function map.
- Leave a small service loop between gland and plug before tightening
  the gland nut.

## Known cosmetic issue

pdf/assembly_top.pdf has overlapping VALUE texts in dense clusters (F.Fab
layer auto-positions). Silkscreen on the physical board is clean
(DRC-checked); use pdf/pcb_layers.pdf page 3 for silk truth.

## Conformal coating (source doc §3A)

Coat the assembled board EXCEPT (keep-out list — mask before spraying):
- the microphone capsule and its J2 pads/leads,
- BZ1 transducer (sound port on top!),
- J1 RJ45 jack (mask the whole body — contacts + springs must stay dry),
- all test points TP1-TP6,
- D3/L1/R15 empty reserve pads (they must stay solderable).

## First-power ritual (per pod, BEFORE mic connect) — unchanged from v1.0

1. Bench 5V into RJ45 contact 4 or 7 (+) and 5 or 8 (GND) — easiest via
   a sacrificial patch cable stub crimped T568B: blue/brown-stripe = +,
   blue-stripe/brown = GND. Current draw must be < 10 mA.
2. TP3 (2V5) = 2.47 V ±2%. TP4 = 5V. Bias voltage at the MIC+ pad
   (J2 pin 1) = ~4.9 V open-circuit (through 3.9k, no capsule yet).
3. Only then solder/plug the capsule; MIC+ settles to ~2.9 V with the
   capsule drawing ~0.5 mA.
4. Beeper check: 5V across contacts 3 (+) and 6 (return) beeps it
   (do not hold DC > a few seconds; it is rated for 4 kHz switching).
5. NOT-ETHERNET rule: never patch these runs into network gear; label
   both cable ends. Storm policy: disconnect pods in lightning weather
   (ESD parts are not lightning protection — ADR-0001).

## Field-test gates that stay OPEN after this order (source doc §3A/§10)

Ordering these boards does NOT freeze the mechanical design: the coded
transducer must still prove detectable at 25/50 ft through the hood in
wind (FIELD-TEST GATE), and the pod prototype -> cable test -> range test
sequence gates the CENTRAL board order, not this one (commission A1/D2).
The ADR-0004 first-article lid-close check is part of the pod prototype
step.

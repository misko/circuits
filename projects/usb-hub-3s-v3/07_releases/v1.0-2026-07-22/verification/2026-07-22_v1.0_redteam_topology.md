subject: usb-hub-3s-v3 v1.0 @ git 526f98f (board sha256:71fdf67958d79224, DRC 0/0/0)
date: 2026-07-22
reviewer: redteam-agent (claude-opus-4-8, topology/protection/ratings lens)
context-given: zero-context (01_docs + 02_parts + 03_src + the routed board only; no prior-review or chat context)
verdict: DO-NOT-ORDER

---

# Red-team review — topology / protection / ratings lens

Zero-context adversarial pass. Mandate: trace the input protection chain from the
netlist, verify TVS directionality and clamp-vs-abs-max at worst-case corners,
check both LM5116 buck rails, and scrutinize the v3 USB-C simplification (is VBUS
really the 5VC rail? are the CC Rp pull-ups the right value/rail for a 5V source?
what happens when a NON-Pi USB-C device is plugged in?). Every claim below is
verified against the netlist (`03_tscircuit/src/usb_hub_3s_v2.tsx`), the immutable
board (`04_kicad/usb_hub_3s_v2.kicad_pcb`, read-only via pcbnew), and the part
limits in `02_parts/*/part.yaml`.

## Verdict rationale

The core protection topology is **correct** and the v3 USB-C change is **sound and
non-hazardous** (a plain, current-correct 5 V rail). DRC is genuinely 0/0/0 and the
board matches the netlist. **No P0 exists.** I am nonetheless returning
**DO-NOT-ORDER** because of **one P1 that lands directly on the single overcurrent
protection element** — the input fuse is specified as *two different, contradictory
ratings* in the release-governing source, and the authoritative part-fact points at
a value that is ~2x too large and justified by a current from a superseded design.
On a 3S LiPo (a source that will happily deliver 100 A+ into a fault), you do not
seal a release while the sole battery-branch fuse is self-contradictory. The fix is
a one-line correction; re-gate after it and after the P2 margins are dispositioned.

---

## PART 1 — Input protection chain (XT60 -> fuse -> reverse-pol FET -> TVS)

Netlist + board agree on the chain:

    J1(XT60) pin2 -> VBAT -> F1 -> VBAT_F -> Q1(D=VBAT_F, S=VIN) -> VIN
                                              Q1 gate: R1 100k -> GND ; D2 12V zener S->G clamp
                                              VIN: D1 SMBJ15A (K->VIN, A->GND) + C1/C2 100uF/35V polymer

Verified on the immutable board (pcbnew pad->net dump):
- `Q1`: pads 1/2/3 (S) = VIN, pad 4 (G) = RPP_G, pad 5 (D) = VBAT_F.
- `R1`: RPP_G -> GND. `D2`: pad1(K) = VIN, pad2(A) = RPP_G.
- `D1`: pad1(K) = VIN, pad2(A) = GND. `C1`/`C2`: pad1(+) = VIN, pad2 = GND.
- `F1`: VBAT -> VBAT_F.

### 1a. Reverse-polarity P-FET (Q1, AON6403) — CORRECT (PASS)

Topology is the canonical high-side P-FET reverse-polarity gate: **drain on the
battery side (VBAT_F), source on the load side (VIN), gate pulled to GND through
R1 = 100 k.** On correct polarity, the body diode (anode=drain=VBAT_F,
cathode=source=VIN) conducts battery->load on first contact; the source rises to
~Vbat, Vgs = 0 − Vbat = −Vbat (well below Vth(p)), the channel enhances and shorts
the body diode. On reverse polarity, VBAT_F is driven negative, the body diode is
reverse-biased (blocks), Vgs ~ 0, the FET stays off, and **VIN never sees the
reversal** — downstream is protected. Correct.

Vgs stress: at Vbat_max = 12.6 V, Vsg = 12.6 V < AON6403 Vgs abs-max ±20 V (37 %
margin). D2 (BZT52C12, 12 V) clamps Vsg to ~12 V, keeping Vgs inside ±20 V under
transients; at 12.6 V the zener passes only ~(12.6−12)/100 k ≈ 6 µA through R1
(negligible), FET stays fully enhanced. PASS.

### 1b. TVS directionality (D1, SMBJ15A) — CORRECT (PASS)

Unidirectional SMBJ15A, **cathode -> VIN, anode -> GND** — the correct orientation
for a positive rail (blocks up to the standoff, clamps positive surges to GND). The
part is placed on VIN **behind Q1's blocking element** (not on VBAT_F). This is the
right choice and the part.yaml records why: on VBAT_F a reversed pack would
forward-bias the TVS into a crowbar through the fuse. On VIN, a reversed pack cannot
forward-bias it (VIN stays ~0). Directionality PASS; placement PASS.

Standoff vs operating: SMBJ15A VR = 15 V > Vbat_max 12.6 V (19 % headroom); VBR(min)
= 16.7 V. The TVS does **not** conduct at normal battery voltage (no standing leakage
/ heat), and it begins clamping only above ~16.7 V. Even a LiHV 3S pack (4.35 V/cell
= 13.05 V) stays under the 15 V standoff. PASS.

### 1c. Clamp vs every downstream abs-max — PASSES numerically, but ONE thin margin (P2)

SMBJ15A worst-case clamp = **24.4 V @ Ipp 24.6 A** (600 W, from the Littelfuse
table quoted in the part.yaml). Recomputed against every abs-max on the VIN node:

| VIN-node part | Ref(s) | Abs-max on VIN | TVS clamp (worst) | Margin | Verdict |
|---|---|---|---|---|---|
| Buck **input ceramics 10 µF / 25 V** | C9-C12, C24-C27 (C77100) | **25 V** | 24.4 V | **+0.6 V (2.4 %)** | PASS — thin |
| HS FET drain (AON6354 Vds) | Q2, Q4 | 30 V cont / 36 V 10 µs spike | 24.4 V | +5.6 V (23 %) | PASS |
| VIN bulk polymer 100 µF / 35 V | C1, C2 (C2982822) | 35 V | 24.4 V | +10.6 V (43 %) | PASS |
| LM5116 VIN pin | U2, U11 | 100 V | 24.4 V | +75.6 V | PASS |

The TVS clamps below *every* downstream abs-max, so the strict test passes. **But the
tightest pair — the 25 V input ceramics against a 24.4 V worst-case clamp — has only
2.4 % margin, and this is a hot-plugged battery input.** Plugging an XT60 into
low-ESR ceramic through the lead inductance is an LC step that rings toward ~2xVbat
(~25 V); the 25 V ceramics are the parts directly exposed to that ring. Mitigating
facts that keep this at **P2, not P1**: (i) the 24.4 V figure is the datasheet corner
at the full 24.6 A / 600 W surge — a battery hot-plug dumps far less energy, so the
realistic clamp sits near VBR ≈ 17-19 V, comfortably under 25 V; (ii) the two
100 µF / 35 V polymers in parallel add ESR that damps the ring. **Recommendation:**
move the buck input ceramics to **50 V** (best practice on a hot-plugged battery
input) so the clamp corner is not resting on the cap rating; or explicitly document
the hot-plug SOA. Steady-state is healthy (12.6 V on 25 V = 50 % derate).

### 1d. Input FUSE — CONTRADICTORY / OVERSIZED spec (P1) [order-blocking]

The primary — and only — overcurrent protection for the whole board is F1, a
Keystone 3568 MINI-blade **holder** (C5249699 on the BOM). The blade fuse itself is
a hand-solder item and is **NOT on the BOM**, so the only rating the assembler is
given comes from (a) the board silk and (b) the part.yaml. **These disagree:**

- Board silk (`04_kicad` gr_text, from `floorplan.yaml:241`): **"FUSE 10A MINI"**.
  tsx comment (line 167): "F1 10A MINI blade fuse holder".
- `02_parts/3568/part.yaml` (the governing part-fact-of-record):
  - line 18-19: "pairs with a **20A** MINI blade fuse (e.g. Littelfuse **0297020**)"
    — 0297020 is a 20 A blade.
  - line 21: "**20A > 15.5A** worst-case input (ADR 0001)".

The "15.5 A worst case" is **stale from v1's IP6559 buck-boost.** v3's power tree
(`power_tree.yaml`, and `nets.yaml` PWR_IN) is **7 A worst case** (55 W / 0.9 / 9 V =
6.8 A). So the part.yaml sizes the fuse to a current that no longer exists on this
board, and lands 2x too high.

Why this matters on a LiPo: correct branch protection for a 7 A continuous input is
a ~10 A blade (carries 7 A without nuisance-blow; opens on a sustained >~13.5 A
fault). A **20 A** blade carries 7 A fine but will not open until ~27 A — so the
entire intermediate-overload band (a stuck buck / partial short pulling 8-27 A,
enough to drive the inductor past its 15.2 A Isat and cook FETs/traces) passes
**unprotected**. The catastrophic dead-short case (hundreds of A) is still covered
even by 20 A, which is the only reason this is P1 and not P0 — but an adversarial
review does not sign off a protection element that the governing source specifies as
both 10 A (silk) and 20 A (part-fact), with the part-fact wrong for v3.

**Fix (one-line):** reconcile to **10 A** (matches silk + v3's 7 A) in
`02_parts/3568/part.yaml`, and correct the stale "20A > 15.5A" justification to
"10A > 7A worst-case (v3, ADR-0001)". Put the exact blade MPN in the hand-solder
list of the release ORDER_README. Re-gate after.

---

## PART 2 — The two LM5116 buck rails (Buck A -> 5VA, Buck C -> 5VC)

Both cells are identical LM5116 synchronous bucks (AON6354 HS/LS pair, 6.8 µH
Sunlord L, 10 mΩ 2512 shunt in the LS source). Board confirms: HS drain = VIN, LS
drain = SW, inductor SW->5Vx, shunt CS->GND, EP->GND, VCCX(pin17)->GND.

- **Output setpoint:** FB divider 3.74 k / 1.21 k, LM5116 FB ref 1.215 V ->
  Vout = 1.215 x (1 + 3.74/1.21) = **4.97 V**. Correct 5 V. (PASS)
- **Current limit / short-circuit ceiling:** datasheet VCS(TH) = 110 mV typ
  (94-126 mV, VCCX = 0) across the 10 mΩ shunt -> peak-current limit ≈ **11 A typ
  (9.4-12.6 A)**. This sits above both rails' rated output (6 A / 5 A) and below the
  AON6354 Id (83 A) and the inductor Isat (15.2 A @20 % / 19 A @30 %). The FETs and
  inductor survive the limit current; the buck hiccups. (PASS) — note this same
  ~11 A foldback is the *only* short-circuit protection the USB-C port has; see 3c.
- **Gate drive:** LM5116 VCC ≈ 7.4 V -> Vgs(FET) ≈ 7.4 V, inside AON6354 ±20 V and
  above the logic-level threshold (Rds spec'd at 4.5 V). Boot diode 1N4148WS
  (75 V) with HB node ≈ SW + ~6.8 V ≤ ~19-31 V << 75 V. (PASS)
- **UVLO — startup floor above the stated input range (P2).** Divider 49.9 k /
  6.98 k with the 1.215 V UVLO ref + hysteresis gives **9.65 V rising / 8.84 V
  falling** (part.yaml gotcha + DETAIL_DESIGN sec.2; basic divider alone = 9.90 V
  rise, hysteresis current pulls it to 9.65 V). **The brief and the board silk
  ("9-12.6V XT60 IN") claim a 9.0 V floor, but the board will not cold-start below
  9.65 V.** Between 9.0 and 9.65 V (a sagging or partly-depleted pack) the bucks stay
  off. This is arguably *desirable* LiPo over-discharge protection (9.65 V = 3.22
  V/cell start, 8.84 V = 2.95 V/cell cutoff), but it **contradicts the advertised
  9.0 V minimum.** Disposition: either amend the spec/silk to a 9.65 V start (declare
  it intended battery protection) or lower the divider for a true 9.0 V start. P2.

Stale-text hygiene (not electrical): the AON6354 part.yaml gotchas still reference
"IP6559 ~5V gate drive", "H-bridge", "21V VOUT_PD", "SMAJ30A clamps" — all carried
from the superseded v1 buck-boost and inapplicable to this LM5116 buck. The device
*ratings* used here are correct; only the prose is stale. Recorded.

---

## PART 3 — The v3 USB-C simplification (the delta under scrutiny)

### 3a. Is VBUS actually the 5VC rail? — YES, CONFIRMED (PASS)

Board pad->net dump of J5 (TYPE-C-31-M-12A): all four VBUS contacts
**A4 = A9 = B4 = B9 = net 5VC**. GND on A1/A12/B1/B12 + shield. CC1 = A5, CC2 = B5.
D+/D- (A6/B6, A7/B7) = DPC/DMC. SBU1/SBU2 (A8/B8) correctly no-connect. The buck-C
output (L2 pin2 = 5VC, U11 pin10 = 5VC) pours straight into the VBUS pads with no
pass element between — VBUS == 5VC exactly as ADR-0001 requires. (ADR-0001
executable-invariant #2 satisfied.)

### 3b. Are the CC Rp pull-ups the right value/rail for a 5 V source? — YES (PASS)

R28 (CC1 -> 5VC) and R29 (CC2 -> 5VC), each **10 kΩ**, pull-up referenced to VBUS
(= 4.97 V, inside the USB Type-C "pull-up to 4.75-5.5 V VBUS" window). Per the Type-C
Rp table for a **pull-up to VBUS**:

| Rp to VBUS | Advertised |
|---|---|
| 56 kΩ | Default USB |
| 22 kΩ | 1.5 A |
| **10 kΩ** | **3.0 A** |

So **10 kΩ correctly advertises a 3.0 A source at 5 V** — the right value on the
right rail. Cross-check with a standard sink (Rd = 5.1 k): V(CC) = 4.97 x 5.1/(10+5.1)
= **1.68 V**, which falls in the sink's vRd-3.0 band (1.31-2.04 V) -> a generic sink
reads "3.0 A available". The Pi, with `PSU_MAX_CURRENT=5000`, ignores CC and draws
up to 5 A, which the 5 A-rated buck physically delivers. Both CC lines carry only the
Rp (no Rd, no VCONN, no cap) — correct for a source-only port. (ADR-0001 invariant
#3 satisfied.) PASS.

### 3c. Hazard if a NON-Pi USB-C device is plugged in? — no destructive/OV hazard; three bounded caveats

The question the task foregrounds. Answer: **the v3 plain-5 V port is the SAFE
outcome — there is no overvoltage path to a plugged device**, because the port can
only ever present a fixed ~5 V (there is no PD, no higher PDO, nothing that can raise
VBUS above the buck setpoint). A non-Pi **sink** (phone, laptop, another device)
sees vSafe5V and a 3 A advertisement, draws what it needs, and is never exposed to
more than 5 V. Not a hazard. Three bounded caveats, all P2:

1. **Non-compliant always-on VBUS.** A compliant Type-C source applies VBUS only
   after detecting a sink's Rd on CC. Here VBUS = 5VC is **energized unconditionally**
   whenever the battery is present. This is tolerable (5 V is the safe default any
   Type-C port must survive on VBUS) and is already accepted by ADR-0001 ("out of
   strict USB-C compliance"). Recorded, not a new defect.

2. **No per-port current limit on the 5 A USB-C port + no reverse blocking.** Unlike
   the three USB-A ports (each behind a TPS2557 e-fuse limiting at 2.72-3.29 A), the
   C-port VBUS is the raw buck output. A shorted/faulty C-port load is caught **only**
   by the buck's ~11 A foldback (3c above) and the input fuse — no fast, port-local
   protection. Furthermore, because VBUS is an always-on output with **no ORing /
   reverse-blocking diode**, if a *powered* USB-C source (a charger/laptop, >~5 V) is
   mistakenly plugged into this **output** port, the synchronous buck-C can sink
   reverse current (5VC -> L2 -> SW -> HS FET/body diode -> VIN), back-feeding the VIN
   rail / battery. Bounded (a ~5.25 V external source across the ~13 mΩ DCR + Rds path
   is a low-single-amp back-feed, not a destructive event) and it requires misuse
   (this is a Pi-dedicated output, not a receptacle you feed). ADR-0001 listed the
   e-fuse as "optional"; **recommend fitting the optional current-limit/e-fuse (with
   reverse blocking) on VBUS** to (i) give the 5 A port the same fault protection the
   2 A USB-A ports already have and (ii) close the back-feed path. P2.

3. **USB-A-rated contact vs limit.** A stuck USB-A port current-limits at up to
   3.29 A (TPS2557 RILIM 36.5 k) through a USB-A contact the datasheet only rates
   1.5 A-class — a fault-mode thermal load at the connector until the TPS2557 folds
   back / thermally shuts down. Pre-dispositioned by ADR-0006 (2 A cont / 2.5 A burst
   is universal DCP practice). Recorded.

### 3d. C-port ESD array now VALID in v3 (PASS — a v2 hazard that v3 removed)

U12 = USBLC6-2SC6, pin5 (VBUS) = 5VC. The part.yaml carries a loud warning:
"VBUS pin rated 5.25 V — usable on USB-A ports ONLY; NOT on the 20 V C port." **In v3
that warning no longer bites**: the C port is a 5 V rail, not the v1/v2 20 V PD rail,
so the USBLC6 VBUS pin sees ~4.97 V < 5.25 V. Dropping the PD cell turned a former
mis-rating into a valid one. Only caveat: a 5 A->0 load-dump transient on 5VC could
briefly approach/exceed the 5.25 V *recommended-max* (not abs-max; the clamp/breakdown
is higher), so keep the buck-C compensation conservative. PASS, minor note.

---

## PART 4 — Capacitor voltage margins (ratings sweep)

| Cap | Ref(s) | Rating (design annotation) | Rail | Margin | Note |
|---|---|---|---|---|---|
| 10 µF / 25 V (C77100) | buck Cin C9-12/C24-27 | 25 V | VIN (≤24.4 V clamp) | 2.4 % @ clamp corner | see 1c (P2) |
| 10 µF / 25 V (C77100) | C49/C50 USB-C VBUS | 25 V | 5VC | 5x | fine |
| 100 µF / 35 V (C2982822) | C1/C2 VIN bulk | 35 V | VIN | 1.4x @ clamp | fine |
| **100 µF / 6.3 V (C49066)** | buck Cout C14-17/C29-32 | 6.3 V | 5.0 V rail | **26 %** | P2 below |
| 22 µF (C29277) | USB-A Cout | (≥16 V typ) | VBUSA (5 V) | ok | fine |

**Buck output ceramics 100 µF / 6.3 V on the 5.0 V rails (P2).** 6.3 V on 5.0 V is
only 26 % voltage margin, and Class-II ceramics lose large capacitance under DC bias
(a 6.3 V X5R at 5 V delivers well under its nominal µF), which both erodes transient
headroom and shifts the control-loop double-pole. Common and DRC-legal, but marginal;
**recommend 10 V or 16 V** output ceramics for overshoot headroom and a stable loop.
Recorded.

---

## PART 5 — Cross-checks (topology sanity, verified — all PASS)

- **No PD source controller on the board** (ADR-0001 invariant #1): footprint census
  = 11x U (2 LM5116 + 2 TPS2513A + 3 TPS2557 + 4 USBLC6), 5x Q (Q1 + 2 buck pairs),
  4x D, 2x RS, 2x L, 5x J, 1x F, 45x C, 25x R. No TPS25740A / no QFN. Confirmed.
- **DRC** `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` =
  **0 violations / 0 unconnected / 0 schematic-parity** (06_build/drc/gate.json).
  Confirmed clean.
- **Board == netlist**: every pad->net spot-check (input chain, both bucks, all
  ports, USB-C) matches the tsx. audit_board.py polarity/proximity gate passes.
- **Pi silk hint present**: "USB-C 5V/5A Pi" on F.SilkS (plus "PROTECTED 3S PACK",
  "9-12.6V XT60 IN", 3x "USB-A 5V 2A", "usb-hub-3s-v3"). Note: the silk marks the
  port Pi-dedicated but does **not** carry the literal `PSU_MAX_CURRENT=5000` key —
  that must live in the release ORDER_README (T3). Minor.

### Traceability gap (process, not electrical — P2)

ADR-0001 states it "emits assertions into `03_src/rules/electrical_invariants.yaml`"
with three named executable invariants (no pd_source_controller part; J5 VBUS on
5VC; CC1/CC2 on Rp). **That file does not exist.** The invariants are only partially
and implicitly covered: audit_board.py checks input-chain polarity and R28/R29
*physical* proximity to J5, but does not assert (a) absence of a pd_source_controller
type, (b) J5 VBUS pads on the 5VC *net*, or (c) CC1/CC2 terminating on an Rp to the
source rail. All three hold *today* (verified by hand above), but the ADR's promised
machine guard is absent — a regression that re-added a PD part or moved VBUS off 5VC
would not be automatically caught. Recommend emitting the named file (or extending
audit_board.py) so the invariants are enforced, not just asserted in prose.

---

## Findings ledger (this review)

| id | severity | finding | verification | recommended disposition |
|----|----------|---------|--------------|-------------------------|
| RT-T1 | **P1** | Input fuse doubly-specified: silk "10A" vs part.yaml "20A/0297020"; the 20A value is justified by v1's stale 15.5A (v3 = 7A) and leaves the 8-27A overload band unprotected on a LiPo. | confirmed (silk gr_text; 02_parts/3568/part.yaml:16-21; power_tree.yaml 7A) | **fix before order** — reconcile to 10A + correct the 15.5A→7A justification; blade MPN into ORDER_README hand-solder list |
| RT-T2 | P2 | Buck input ceramics 10µF/**25V** vs SMBJ15A worst-case clamp 24.4V = 2.4% margin on a hot-plugged battery input. | confirmed (SMBJ15A vclamp_max 24.4V; C77100 25V; VIN hot-plug) | recommend 50V input ceramics, or document hot-plug SOA (realistic clamp ≈17-19V) |
| RT-T3 | P2 | LM5116 UVLO 9.65V rise / 8.84V fall — board won't cold-start below 9.65V, contradicting the "9-12.6V" brief/silk. | confirmed (divider 49.9k/6.98k; part.yaml + DETAIL_DESIGN) | amend spec/silk to 9.65V start (declare LiPo protection) or lower divider |
| RT-T4 | P2 | USB-C 5A port has no port-local current limit and no reverse blocking (raw buck output); relies solely on ~11A buck foldback; powered-source misuse can back-feed VIN. | confirmed (netlist: no e-fuse on 5VC; sync-buck reverse path) | fit the ADR-optional current-limit/e-fuse w/ reverse blocking on VBUS |
| RT-T5 | P2 | Buck output ceramics 100µF/**6.3V** on 5.0V rails — 26% margin + heavy DC-bias derating. | confirmed (C49066 6.3V; 4.97V rail) | move to 10V/16V |
| RT-T6 | P2 | ADR-0001's named executable-invariant file `electrical_invariants.yaml` is absent; the three PD/VBUS/CC invariants are not machine-enforced (hold today by manual check). | confirmed (file absent; audit_board.py scope) | emit the file or extend audit_board.py |

**PASS (verified correct, stated so the reader can trust the scope):** reverse-polarity
FET orientation + Vgs clamp; TVS directionality + behind-Q1 placement; TVS clamps
below all downstream abs-max (numerically); VBUS == 5VC; CC Rp = 10k = 3.0A at a 5V
pull-up (correct value/rail); no OV hazard to any non-Pi device (fixed 5V); USBLC6
now valid on the 5V C-port; both buck setpoints 4.97V; current limit ~11A within
FET/inductor SOA; DRC 0/0/0; board == netlist; no PD controller present.

## Bottom line

Electrically the design is sound and the v3 simplification is correct — a non-Pi
device on the USB-C port is safe, capped at the honestly-advertised 3 A, with no
overvoltage path. **DO-NOT-ORDER stands on one narrow, safety-relevant, one-line
issue: the input fuse must be specified as a single correct value (10 A) before the
release seals.** Fix RT-T1, disposition RT-T2..T6 (all acceptable-with-rationale),
re-gate. There are no P0 findings.

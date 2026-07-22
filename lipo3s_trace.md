# lipo3s v4 clean-room — predicted execution trace

_A hand-walk of `skills/pcb-design/SKILL.md` against the amended brief
(3S LiPo XT60 → 3× USB-A **2A cont / 2.5A burst** + 1× USB-C **5A
PD-compliant**), written BEFORE the run. Each stage: pseudo-code of what the
skill instructs, the predicted resolution for this board, and a confidence
call. Untracked working document — compare against the real run afterwards._

Legend: 🟢 expect smooth · 🟡 expect friction, gates should catch ·
🔴 genuine uncertainty, may end in an honest-stop ADR

---

## Stage 0 — Commission 🟢

```
name        = usb-pd-hub-3s (or similar kebab pick)
mkdir 01_docs..07_releases
copy contracts from skills/pcb-design/templates/  (incl. NEW journal/, learnings/)
BRIEF.md    = verbatim prompt + 2 directives, sha256, G# criteria
D-SPEC pass = test every number against standard + parts envelope
journal/commission.md ← first entries (NEW discipline, first live use)
```

Predicted resolutions:
- **T1 (spec tension)**: "USB-C 5A compliant" → Rp signaling caps at 3A;
  5A requires a PD source (fixed 5V/5A PDO + e-marker read + 3A fallback).
  → ADR + flagged row. The directive already concedes this, so no drama.
- **T2**: USB-A 2A cont / 2.5A burst vs ~1.5–2A receptacle contact ratings
  → resolved as "2A continuous + polyfuse-limited burst"; ADR row.
- Risk: agent forgets journal entries mid-flow → M-JRNL fails later and
  forces backfill. First live use of the discipline; expect 1 reminder loop.

## Stage 1 — Architecture + design math 🟢

```
power tree: XT60 → P-FET RPP → fuse(~12A) → buck 5V → {3×USB-A, USB-C/PD}
worst case: 3×2A + 5A = 11A continuous (was 13.5A — the directives helped)
stackup: 4-layer; In1 = solid GND; In2 = VIN plane; 5V as F.Cu pours
protection ADR (mandatory): RPP + fuse + TVS(SMBJ15A-class) + UVLO ~9.0V
```

Predicted: same architecture family as v3 (it was sound). 11A lets the buck
target ~13A instead of 15A — slightly easier magnetics/thermals. The
mandatory-protection gate has fired correctly in both prior runs; no risk.

## Stage 2 — Parts + D-ESC/D-TIER/D-ADJ gates 🟡→🔴 (the PD part is the wildcard)

```
for each candidate: escape_check --style S --pitch P → escape block in part.yaml
fab_tier: start jlc_4layer_standard (cost ceiling)
buck controller: prefer controller+FETs, leaded
  NEW escape-budget check: count escapes/side; ≤0.65mm & ≥6/side ⇒
  corridor plan at placement OR wider part OR advanced tier
PD source controller: standalone, fixed 5V/5A PDO, e-marker, no host MCU
```

Predicted resolutions:
- **Buck controller** 🟡: HTSSOP-20-class again is likely — but the NEW
  escape-budget rule now forces the ADR-0008 lesson at *selection* time:
  expect either (a) explicit corridor reservation noted in the part.yaml +
  floorplan, or (b) a package with fewer loaded escapes. This run is the
  calibration experiment for exactly this rule.
- **PD controller** 🔴: the genuine unknown. Standalone 5V/5A source
  controllers with e-marker handling are scarce; many live in 0.5mm-pitch
  QFN — which `escape_check` will grade `needs jlc_4layer_advanced`, and
  P-TIER will then force a real decision: raise the tier (D-TIER ADR +
  ORDER_README line) or keep hunting. Three plausible outcomes:
  1. finds a suitable part at ≥0.65mm/leaded → stays standard tier (~35%)
  2. finds only 0.5mm QFN → justified ADVANCED-tier ADR (~40%)
  3. no sourceable compliant 5A part → honest spec-tension ADR proposing
     5V/3A-compliant + documented 5A ceiling, flags the user (~25%)
  All three are PASS outcomes for the process — what must NOT happen
  (and is now gated) is discovering this at DRC.
- 14–17 part.yamls, TSX-PRE preflight will demand padmap coverage for the
  USB-C A1..B12 pads up front (last run it was discovered mid-build).

## Stage 3 — nets.yaml + rules 🟢

```
classes: BATT_IN(~9A@9V), VBUS_A(6A), VBUS_C(5A), SWNODE, SIG
fab_tier declared; tier-derived floors (NEW: no hand numbers to get wrong)
scoped_floors: likely 1 entry for the SW-island sense taps (NEW schema —
  what was a bespoke script last run is config now)
```

Predicted: smooth; the emitter now errors on sub-floor explicit values
instead of silently clamping, so a config typo surfaces at generation.

## Stage 4 — Schematic (tscircuit) 🟢 (newly gated where it burned us)

```
manifest.yaml  = declared refdes list (NEW)
tsx_preflight  BEFORE first tsci build (NEW) → padmap for A1..B12/SH
author tsx     (CC wiring = PD controller + VCONN caps, not bare Rp)
tsci build → converter .kicad_sch → ERC --severity-all = 0 errors
count_parity   (NEW) — circuit.json/sch/netlist/board vs manifest
```

Predicted: 1–2 iterations. The silent-connector-drop trap that cost session
1 a hand-count discovery is now two machine gates. ERC 0 was reached in one
session last time with a *harder* CC scheme.

## Stage 5 — Placement 🟡

```
floorplan.yaml: ports on edges, buck island, D-ADJ adjacency:
  bootstrap/FB/CC/VCONN passives HARD against pins
  NEW: reserved escape corridor on the controller's loaded side
audit_board: XT60 pad1='−' polarity assert, mouth directions, proximity
```

Predicted: 2–4 floorplan iterations (normal). The corridor reservation is
the untested judgment — if honored, stage 6 gets dramatically easier; if
skipped, M-JRNL at least records *when* it was skipped.

## Stage 6 — Route → stitch → DRC 0/0/0 🟡 (the long pole, but shorter than last time)

```
generate_rules (pre) → prep → KRT waves (power first, hardest first)
→ import → taps (NEW: config step, was bespoke script)
→ stitch  (NEW: pad_rescue skips footprint thermal grids;
           NEW: dangling stitch vias auto-pruned)
→ generate_rules LAST → DRC --severity-all --refill-zones --schematic-parity
loop: classify → fix config → full rebuild → re-measure
```

Predicted first-DRC composition vs v3's ~90: the four classes that consumed
v3's iterations are now impossible-by-construction (silk text_height ×58 —
tier-derived heights; EP hole_to_hole — thermal-grid credit; via_dangling —
auto-prune; taps — pipeline step). Realistic first count: **15–35**, mostly
clearance + the controller escape region. Grind estimate: 45–90 min.
- 🔴 residual: the ADR-0008 question itself. If the corridor plan works,
  standard tier closes; if the same via-cluster wall appears, the correct
  exit is the ADVANCED-tier ADR (a legitimate, documented outcome — and
  either way it CALIBRATES escape_check in the harvest).

## Stage 7 — Verify + release 🟡 (long, mostly mechanical)

```
bom_seed → jlc_stock (≥5× need) → jlc_twin vs JLC's own CAD
→ fresh-context pin review (zero FAIL) → fresh-context render review
→ export_pdfs → policy_audit: 0 FAIL
   (now includes P-ESC/P-TIER, S-COUNT artifacts, M-JRNL, M-LEARN)
→ learnings/<stage>.md per completed stage (NEW — required before release)
→ 07_releases/v1.0-<date>/ : fab/ pdf/ source/ 3d/ verification/ +
   ORDER_README (+ ADVANCED line iff tier raised) + MANIFEST (clean tree)
```

Predicted friction: jlc_twin on the PD controller + USB-C (twin deltas
needing evidence-backed adjudication are common on connectors); the
fresh-context reviews each cost an agent run. M-LEARN forces the learnings
files — expect the run to backfill them from journals at this point.

---

## Overall forecast

- **Reaching a compliant, released board**: ~60% in one session, ~85%
  within two (the resume-from-tree discipline is proven; nothing is lost
  at a session boundary).
- **Most likely honest-stop point**: the PD-controller sourcing decision
  (stage 2) or the controller escape at standard tier (stage 6) — both now
  end in *named, documented decisions* rather than stalls.
- **The real change vs yesterday**: every failure mode this project has
  ever paid for now fails LOUDLY at its cheapest stage. What remains
  uncertain is only what we haven't paid for yet — which is exactly what a
  canary run is for.
- **Watch items for the post-run harvest**: (1) does the escape-budget
  rule change the controller choice or the floorplan? (2) does the PD part
  force the tier? (3) do journals actually get written as-you-go or
  backfilled? (4) first-DRC count vs the 15–35 prediction.

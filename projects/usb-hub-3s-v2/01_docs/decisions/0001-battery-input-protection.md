---
id: 0001
date: 2026-07-22
status: accepted
---
# 0001 — Battery/input protection: fuse + reverse-polarity P-FET + UVLO + TVS

MANDATORY ADR (skill: battery/input protection). Input is a 3S LiPo
(9.0–12.6 V envelope, D1) on an XT60. Carried forward from usb-hub-3s v1
ADR-0001 (including its v1.1 D1-position fix), **re-sized for v2's ~7 A trunk**
— v1 sized every input part for the 15.5 A buck-boost draw that no longer
exists.

## Worst-case input current (the v2 correction)
All rails are 5 V bucks (E-TOPO): Sum Pout = 6 A·5 V (USB-A) + 5 A·5 V (USB-C)
= 55 W; at Vin_min 9 V, eff 0.9 → **6.8 A worst case** (power_topology.py).
v1's figure was ~15.5 A. Every input part below is sized to 6.8 A continuous
with margin, not 15.5 A.

## Decisions

- **Overcurrent: 10 A MINI blade fuse in THT holder (Keystone 3568).**
  6.8 A / 10 A = 68 % of rating — under the 75 % blade-practice line (v1 ran
  78 % on a 20 A fuse). Hand-solder BOM line, user-replaceable. CHOSEN over
  SMD chip fuse (harder to source >10 A, not replaceable) and no fuse
  (REJECTED: a hard fault on a LiPo is a fire). Exact MPN chosen at parts
  stage; a 10 A 32 VDC MINI blade with IR ≥ 1000 A.
- **Reverse polarity: P-FET high-side ideal-diode style (AON6403).**
  Drain = VBAT_F (battery side), Source = VIN, Gate → GND via R (RPP_G), zener
  clamp on Vgs. On correct polarity the body diode conducts on first contact,
  then the FET enhances (Vgs = −Vin) and carries the trunk at ~mΩ. On reversal
  the body diode is reverse-biased and BLOCKS — nothing conducts, nothing is
  consumed. AON6403 (Vgs ±20 V covers 12.6 V direct, Rds(on) ~7 mΩ) reused from
  v1 ledger. Dissipation at 6.8 A: 6.8²·0.007 ≈ **0.32 W** (v1: ~1.2 W at
  15.5 A) — a modest copper pour suffices; thermal-via burden much lighter.
  CHOSEN over series Schottky (REJECTED: 0.4 V·6.8 A = 2.7 W) and over an
  ideal-diode controller + NFET (more parts, controller stock risk).
- **Over-discharge/UVLO: each LM5116's precision UVLO pin.** Both bucks see
  VIN and each carries the v1 divider (R 49.9 k / 6.98 k → ~9.65 V rising /
  ~8.84 V falling, 0.8 V hysteresis; DETAIL_DESIGN). Below the falling
  threshold both converters shut their outputs, so both the USB-A rail (5VA)
  and the USB-C rail (5VC, hence the PD controller downstream) collapse
  together — no separate board-authority comparator is needed because there is
  no single downstream converter to gate (v1 needed the IP6559 EN detector;
  v2 does not). Thresholds: cutoff 8.84 V falling (2.95 V/cell), re-enable
  9.65 V rising.
  KNOWN RESIDUAL (from v1 X12): R holding LM5116 EN high keeps the part in
  STANDBY below UVLO (VCC regulator running), not 10 µA shutdown. Two LM5116s
  → ~2× the standby drain (~3–8 mA total). "Do not store the pack connected"
  is a HARD ORDER_README rule + a first-power measurement. v2 improvement
  candidate carried to the routing/next rev: drive EN from the UVLO divider
  for true shutdown.
- **OV/transient: SMBJ15A TVS across VIN, AFTER Q1 (cathode → VIN, anode →
  GND).** Standoff 15 V > 12.6 V max battery; clamp ≤ 24.4 V < LM5116 abs max
  (100 V) and every downstream rating. Placed on VIN, behind Q1's blocking body
  diode (the v1.1 D1-position fix, INCIDENT below) — a reversed pack does NOT
  forward-bias it, so reversal is non-destructive. Hot-plug clamping is
  equivalent: the surge reaches VIN through the enhanced Q1 and D1 clamps there.
- **Inrush:** bulk input capacitance (2× 100 µF polymer at entry + ceramics);
  XT60 hot-plug inrush accepted (LiPo + XT60 standard practice; both bucks
  soft-start via SS caps).

## The D1-position fix (carried verbatim from v1 ADR-0001 amendment v1.1)
INCIDENT (v1.0): the netlist placed D1 (unidirectional SMBJ15A) on VBAT_F,
cathode to the battery side of Q1, while the ADR flow said "→ VIN rail". A
reversed pack forward-biases that D1 through F1: hundreds of amps until the
fuse melts, consuming F1 and possibly D1 on every reversal. It passed ERC,
DRC, parity, twin and pin review (every artifact consistently wrong together)
and was caught only by external review. **v2 builds the corrected topology
from the start: D1 on VIN, after Q1 — non-destructive reversal.** Machine-
stated in electrical_invariants.yaml (INV-D1-PLACEMENT, INV-Q1-ORIENTATION,
INV-FUSE-FIRST).

## Decision (flow)
XT60 → 10 A blade fuse (holder, hand-solder) → reverse-polarity P-FET (Q1) →
TVS SMBJ15A (D1) + bulk caps → VIN rail → fanned to both buck inputs.
Board-level UVLO ~8.8 V falling / ~9.65 V rising via each LM5116 UVLO pin.

## Consequences
- Fuse + holder are hand-solder BOM lines (JLC THT catalog gap accepted).
- ~3–8 mA post-UVLO standby (two LM5116 in standby) documented; no hard cutoff
  in v2 (candidate for next rev).
- Q1 dissipates ~0.32 W at 6.8 A — light copper pour; verified at R-THERM.

---
id: 0001
date: 2026-07-21
status: accepted (amended 2026-07-21 for v1.1 — see "Amendment v1.1")
---
# 0001 — Battery/input protection: fuse + reverse-polarity P-FET + board UVLO + TVS

## Context
Input is a 3S LiPo (9.0–12.6 V envelope, A1) on XT60. The skill mandates this
ADR: reverse polarity, overcurrent, over-discharge (UVLO), overvoltage/transient.
Worst-case input current: USB-C 100 W (0004) + USB-A 30 W at Vin=9.0 V,
eff ~0.93 → ~15.5 A; at 12.6 V → ~11.1 A.

## Options
- **Overcurrent: 20 A MINI blade fuse in THT holder** — hand-solder line, user
  replaceable. CHOSEN over SMD chip fuse (hard to source >15 A, not
  replaceable) and no fuse (REJECTED: hard fault on a LiPo is a fire).
- **Reverse polarity: P-FET high-side ideal-diode-style** (source to load,
  drain to battery, gate to GND via R, zener clamp on Vgs) — ~mΩ loss.
  CHOSEN over series Schottky (REJECTED: ~0.4 V × 15 A = 6 W) and over
  ideal-diode controller + NFET (more parts, controller stock risk).
  FET must be ≥30 V, Rds(on) ≤ 5 mΩ at Vgs = −8 V (worst at UVLO floor ~8.7V),
  continuous ≥ 20 A.
- **Over-discharge/UVLO: LM5116's precision UVLO pin as the SINGLE board
  authority** (divider 49.9k/6.98k → 9.65 V rising / 8.84 V falling, derived
  in DETAIL_DESIGN §2), with the IP6559 EN (GPIO18) gated by 5VA presence
  (10k/10k divider from the 5VA rail): when the buck is UVLO'd, 5VA collapses
  and the PD stage disables too. CHOSEN over a separate TLV431 comparator
  (rejected: its hysteresis needs feedback from a rail with full swing; every
  candidate node here has a weak or ambiguous pull-up — more parts, less
  certainty) and over a hard P-FET load cutoff (rejected for v1: residual
  draw after UVLO ≈ 0.5 mA — IP6559 standby 200 µA + UVLO divider 221 µA +
  LM5116 standby — acceptable; ORDER_README says "do not store the pack
  plugged in").
  Thresholds: cutoff 8.84 V falling (2.95 V/cell), re-enable 9.65 V rising
  (0.8 V hysteresis prevents chatter on load-shed recovery).
  KNOWN RISK (documented): IP6559 GPIO18/EN semantics differ between the _AC
  variant (power-share input, "ground when unused") and the base EN function;
  for the _C variant the EN PIN Function section governs (enabled high,
  internal pull-up). The 10 kΩ pull-down + 10 kΩ feed from 5VA asserts a
  clean logic level either way; first-power ritual verifies UVLO behavior
  with a bench supply BEFORE a pack is connected.
- **OV/transient: SMBJ15A TVS across input after the fuse** — standoff 15 V >
  12.6 V max battery; clamp ≤ 24.4 V < IP6559 abs max 34 V and LM5116 100 V
  rating. CHOSEN. (3S packs cannot legitimately exceed 12.6 V; the TVS guards
  hot-plug inductive spikes, which XT60 hot-plug + wire inductance produces.)
- **Inrush**: bulk input capacitance is large (≥ 300 µF); XT60 hot-plug inrush
  is accepted (LiPo + XT60 standard practice; both converters soft-start).

## Decision
20 A blade fuse (holder, hand-solder) → P-FET reverse-polarity switch →
TVS SMBJ15A + bulk caps → VIN rail. Board-level UVLO ~8.8 V falling /
~9.4 V rising gates both converters (LM5116 UVLO pin; IP6559 EN pin via
detector). Exact values derived in DETAIL_DESIGN.md.

## Consequences
- Fuse + holder are hand-solder BOM lines (JLC THT catalog gap accepted).
- ~0.3 mA post-UVLO standby documented; no hard cutoff in v1.
- P-FET dissipates ≤ 1.2 W at 15.5 A worst case (5 mΩ) — needs copper pour +
  thermal vias at placement; verified at R-THERM.

---

## Amendment v1.1 (2026-07-21) — D1 position, exact fuse, standby-drain correction

INCIDENT (recorded per canon — this is why the amendment exists): the v1.0
NETLIST placed D1 (unidirectional SMBJ15A) on VBAT_F, cathode to the battery
side of Q1, while this ADR's flow line said "→ VIN rail" and its options text
said "after the fuse" — the ADR was internally self-contradictory and no gate
owned the topology intent. A reversed pack forward-biases that D1 through F1:
~250–600 A until the fuse melts, consuming F1 and likely D1 (which can fail
short) on every reversal. The defect passed ERC, DRC, parity, twin and pin
review — every artifact was consistently wrong together — and was caught only
by external review (08_reviews X1) and red-team A (X29, which graded the
as-built behavior a sacrificial-but-protective crowbar). Both readings agree
the downstream was protected (Q1 blocks); they differ on whether reversal
consumes parts.

DECISION (explicit, citing both reviews): **non-destructive reversal.** D1
moves to VIN, after Q1 (cathode → VIN, anode → GND). On reversal Q1's body
diode blocks and nothing conducts, nothing is consumed. Hot-plug clamping is
equivalent: the surge reaches VIN through the conducting/enhanced Q1 and D1
clamps it there (≤24.4 V, inside every downstream rating). The
coordinated-crowbar alternative (keep D1 on VBAT_F, document sacrificial
F1+D1 per reversal) was REJECTED: it spends a hand-replaceable fuse AND a
soldered TVS on a trivially probable user error, for no protection gain.
The topology is now machine-stated in
`03_src/rules/electrical_invariants.yaml` (INV-D1-PLACEMENT,
INV-Q1-ORIENTATION, INV-FUSE-FIRST) — the checker is pending, the red-team
diffs against it meanwhile.

**Exact fuse (X1/X13 — v1.0 shipped "20 A MINI" with no MPN):
Littelfuse 0297020.WXNV** (297 MINI series, 20 A, 32 VDC, IR 1000 A @32 VDC;
LCSC C151096; alt Eaton BK/ATM-20). Coordination, quoted from the 297 DS
(02_parts/0297020WXNV/):
- I²t (melt) = 380 A²s; opening: 135% → 0.75–600 s; 200% → 0.15–5 s;
  350% → 0.08–0.5 s; 600% → 0.03–0.1 s; 110% → no open.
- vs load: worst continuous 15.6 A = 78% of rating — above the 75%
  blade-practice line, ACCEPTED because both converters current-limit (the
  IP6559 input-CC via RS2 and the LM5116 11 A peak limit cap the natural
  draw ≈ 15.6 A); there is no natural 17–26 A operating point.
- vs copper (16 A floors): a sustained 135% overload (27 A) could take
  minutes to open — no natural source of that current exists on this board
  (residual risk recorded, X13); true faults (shorted FET/rail ≈ hundreds
  of amps, < 1000 A IR ✓) open in ≤ 10 ms (t ≈ 380/I²).
- vs D1: a full SMBJ15A clamp event (≤24.6 A, ≤1 ms) is ~0.6 A²s ≪ 380 —
  the fuse rides through clamp events; and with D1 on VIN, reversal is no
  longer a fuse event at all.
- vs Q1: reverse blocking means Q1 sees no fuse-coordination duty; forward
  it is a 40 A-class part behind a 20 A fuse.
- User harness: ≥ 12 AWG leads required (ORDER_README).

**Standby-drain correction (X12, red-team A):** the v1.0 claim "~0.5 mA
below UVLO" was wrong. R9 holds LM5116 EN high, so below UVLO the part is in
STANDBY (VCC regulator running; the 10 µA shutdown spec requires EN low).
Realistic drain is 1.5–5 mA (DETAIL_DESIGN §2 has the corrected budget).
Consequences: "do not store the pack connected" is a HARD rule in
ORDER_README, plus a measure-at-first-power step. v2 candidate: drive EN
from the UVLO divider (true 10 µA shutdown) or a hard P-FET cutoff.

# Journal — 00 commission (usb-hub-3s-v2)

## 2026-07-22 — start
- did: Scaffolded projects/usb-hub-3s-v2 (numbered stage folders + contracts from
  the skill's canonical set, NOT copied from v1). Wrote BRIEF.md with the verbatim
  prompt (sha256 dee57360…) + parsed requirements G1-G6, spec tensions T1-T3,
  decision register D1-D4.
- result: Tree created; 15 contracts.md in place; BRIEF recorded D1 (USB-C is
  fixed 5 V ONLY -> all-buck) as the founding decision.
- next: D-SPEC voltage envelope + E-TOPO gate.

## 2026-07-22 — D-SPEC / E-TOPO (finish, gate GREEN)
- did: Emitted 03_src/rules/power_tree.yaml (2 rails, both fixed 5 V out) +
  preliminary nets.yaml (PWR_IN trunk = 7 A, fab_tier jlc_4layer_standard).
  Copied the ledger-verified reusable multi-pin parts from v1 into 02_parts
  (XT60, fuse 3568, AON6403/AON6354, LM5116, TPS2557, TPS2513A, USBLC6,
  KH-AF90DIP, TYPE-C-31-M-12A, BZT52C12, SMBJ15A, 1N4148WS). Ran
  power_topology.py.
- result: **E-TOPO OK: 2 rails topology-correct.** Both USB-A and USB-C derived
  required=BUCK, declared=BUCK (LM5116, type buck_controller). Derived
  worst-case input-trunk current = **6.8 A at Vin_min 9 V** (Sum Pout 55 W /
  0.9 / 9 V). PWR_IN declared 7 A consistent. Contrast v1: ~15.5-16 A trunk +
  a buck-boost that E-TOPO would have FAILed as over-engineered. This board is
  the E-TOPO green-case proof.
- next: D-SPEC sourcing spike for the fixed-5V/5A PD source controller
  (background research agent running); then architecture + ADRs.

## 2026-07-22 — sourcing spike (start)
- did: Launched a timeboxed background research agent to re-test v1 ADR-0004's
  claim that "no stocked simple fixed-5V/5A PD source controller exists" — the
  claim that defaulted v1 to the IP6559 buck-boost. Candidates: Injoinic/WCH/
  Southchip fixed-PDO source controllers, TI TPS25730, PD-source PHY + buck.
- result: pending (agent in background).
- next: on return, D-ESC the chosen package, write ADR-0004-v2, add its part.yaml.

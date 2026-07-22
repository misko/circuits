# usb-hub-3s-v2 — Architecture

A 3S-LiPo powered charging hub: 3× USB-A (5 V / 2 A cont, DCP) + 1× USB-C
(5 V / 5 A PD source). **All-buck, correctly scoped** — the v2 correction of
v1's IP6559 buck-boost over-engineering.

## Power tree (E-TOPO GREEN)

```
XT60 (3S LiPo, 9.0-12.6V)
  └─ F1  10A MINI blade fuse (hand-solder)
      └─ Q1  reverse-polarity P-FET (AON6403, D=VBAT_F S=VIN)   [ADR-0001]
          └─ D1  TVS SMBJ15A on VIN (after Q1 — non-destructive reversal)
              └─ VIN rail  (bulk 2×100µF polymer + ceramics)   ~6.8A worst case
                  ├─ BUCK A  LM5116 + AON6354 pair + 6.8µH  →  5VA (≤6A)   [ADR-0010]
                  │     └─ 3× TPS2557 current-limit (2A cont / 2.5A burst)
                  │         + TPS2513A DCP auto-detect (2 chips: ports 1+2, 3)
                  │         + USBLC6 ESD  →  3× USB-A receptacle (5V/2A)
                  └─ BUCK C  LM5116 + AON6354 pair + 6.8µH  →  5VC (≤5A)   [ADR-0010]
                        └─ TPS25740A PD SOURCE PHY (fixed 5V/5A, e-marker)  [ADR-0004-v2]
                            + external high-side path NMOS (VBUS switch)
                            + USB-C data ESD  →  USB-C receptacle (5V/5A)
```

Derived worst-case input-trunk current = **6.8 A at Vin_min 9 V**
(Sum Pout 55 W / 0.9 / 9 V). Contrast v1: ~15.5 A + a buck-boost.
E-TOPO: both rails required=BUCK, declared=BUCK → **PASS**.

## Why every stage is a BUCK (the founding correction)

Vout is fixed 5 V on both rails; Vin is 9.0–12.6 V. Since Vout_max (5) <
Vin_min (9) ALWAYS, the required topology is step-down BUCK on both rails
(power_topology.py derives this mechanically). v1 read "5 A compliant USB-C" as
full-range PD (5–20 V), which overlaps Vin and needs a buck-boost; but the port
is 5 V ONLY (D1, user-confirmed), so the buck-boost — plus its 4 H-bridge FETs,
30 V-FET/TVS coordination, 10 µH/15 A inductor, and 16 A input trunk — was pure
over-engineering. v2 deletes the entire PD power stage and replaces it with a
second copy of the proven 5 V buck + a PD *signalling* PHY.

## The two bucks (ADR-0010)

Identical, each = v1's proven LM5116 5 V/7 A buck reused verbatim (6 A and 5 A
both fit inside 7 A → no re-derivation). Fault-isolated: they share only VIN and
GND. Each has its own UVLO divider gating it off below ~8.8 V. See
DETAIL_DESIGN.md for the component values (carried from v1 §2).

- **Controller:** LM5116MHX/NOPB (HTSSOP-20, standard tier, external boot diode).
- **FET pair:** AON6354 (DFN 5×6, logic-level, 30 V) — HS + LS.
- **Sense:** 10 mΩ 2512 shunt, Kelvin CS/CSG via 0 Ω links.
- **Inductor:** 6.8 µH (v1 L2 part).
- **Output:** 4× 100 µF/6.3 V 1210 ceramic per rail.

## USB-A side (carried from v1, unchanged — "this half works")

Per port ×3: TPS2557 current-limit switch (RILIM 36.5 k → ~2.7–3.3 A window,
ADR references v1 DETAIL §3), USBLC6 D+/D- ESD, KH-AF90DIP-112 receptacle.
Two TPS2513A DCP controllers cover the three ports (dual-channel: U6 ports 1+2,
U7 port 3) so each port auto-advertises DCP/Apple charging currents. 5VA feeds
all three via the buck-A pour.

## USB-C side (v2's new, simple PD cell — ADR-0004-v2)

5VC (from buck C) → TPS25740A. The TPS25740A is a PURE PD SOURCE PHY: it
monitors CC1/CC2, runs BMC PD communication, and gate-drives ONE external
high-side NMOS that connects 5VC to the USB-C VBUS when a sink attaches and
negotiates. Config is resistor pin-strap: HIPWR→GND advertises 5 A; EN9V/EN12V
low keep it 5 V-only. An e-marked cable is required for the 5 A contract
(the sink reads the cable's e-marker; the source advertises 5 A). USB-C D+/D-
carry ESD clamps. No buck-boost, no H-bridge, no coil in the PD path.

## Protection (ADR-0001)

Fuse (10 A) → reverse-polarity P-FET → TVS on VIN → per-rail UVLO. The v1.0 D1
reverse-polarity defect (TVS on VBAT_F crowbarring through the fuse on reversal)
is built CORRECTLY from the start in v2: D1 on VIN, behind Q1 — reversal is
non-destructive. Machine-checked by electrical_invariants.yaml.

## Fab tier (ADR-0011)

jlc_4layer_advanced — forced by the single TPS25740A VQFN-24 0.5 mm (via-in-pad
escape), NOT by any over-capable converter. A 5 V/3 A downgrade (plain Rp, no PD
chip) would return the board to STANDARD tier (flagged, BRIEF T4).

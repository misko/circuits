# journal: 02_parts

## 2026-07-21 — start
- did: JLC API stock sweeps (FETs, inductors, receptacles, ESD, diodes,
  shunts, polymer caps); datasheets fetched + figures rendered for pin-map
  verification (AON6354/AON6403/AO3401A/2N7002 SOT/DFN figures, TPS2557 DRB
  table, TPS2513 DBV, USB-A receptacle drawings x4, Sunlord series tables).
- result: 16 part dirs with part.yaml + PDF. Key selections:
  * NFET all-slots: AON6354 (30V 5.2mOhm@4.5V LOGIC-LEVEL, C404363) — NCEP40T15AGU
    REJECTED: Vth max 4V, no 4.5V Rds spec vs IP6559 ~5V gate drive.
  * P-FET: AON6403; Vconn: AO3401A + 2N7002 (both JLC basic).
  * L1: MWSA1707S-100MT (10uH 9.9mOhm Isat 16.5A) after APH1265T100M REJECTED
    (DCR 16.5mOhm, Isat 12.5A < 15.5A requirement).
  * L2: MWSA1206S-6R8MT (Isat 15.2A).
  * USB-A: CNC Tech 1001-011-01101 pattern, hand-solder (JLC receptacles all
    rated 1.5A and mostly vertical; T1 deviation recorded in yaml + ADR 0002).
  * C-port data ESD: LESD5D5.0CT1G (USBLC6 VBUS pin 5.25V < 20V rail).
  * escape blocks all emitted by escape_check runs (qfn0.5/dfn0.65/dfn1.27/
    leaded0.65/leaded0.95/connector/passive).
- next: commit; 03_src config (nets.yaml floors, floorplan) + 03_tscircuit TSX.

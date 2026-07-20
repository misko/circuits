# ORDER_README — lipo3s-usb-hub v1.0 (2026-07-20)

3S LiPo (XT60) → 3× USB-A (2.5 A) + 1× USB-C (6 A) power/charging board.
4-layer, 100 × 60 mm. Built by the tscircuit-native pipeline; DRC 0/0/0; board-netlist
parity 0 vs the sealed usb-power-3s. Files in this release are IMMUTABLE.

## JLCPCB order options (must match)

| Option | Value | Why |
|---|---|---|
| Layers | **4** | In1 GND plane + In2 power planes |
| Impedance / stackup | JLC default 4-layer | no controlled-impedance nets |
| **Min via / hole — ADVANCED (small-via)** | **REQUIRED** | KRT fanout uses 0.25/0.15 mm vias in the VQFN region; the standard tier will reject or drift them |
| Surface finish | HASL or ENIG (installer's choice) | no fine-pitch BGA |
| Assembly | Top side only | all SMD parts on F.Cu |

## Upload

- **PCB**: `gerbers/lipo3s_usb_hub_gerbers.zip` (13 files: F/B/In1/In2 copper, F/B mask,
  F/B silk, F/B paste, Edge_Cuts, PTH + NPTH drills). Nothing else in the zip.
- **Assembly BOM**: `bom.csv` (columns Comment,Designator,Footprint,MPN,LCSC).
- **Assembly CPL**: `cpl.csv` (Designator,Val,Package,Mid X,Mid Y,Layer,Rotation).

## Hand-solder / not-assembled (consigned or THT)

| Ref | Part | Note |
|---|---|---|
| J2, J3, J4 | CNCTech 1001-011-01101 USB-A (THT) | not in JLC SMT catalog — hand-solder or consign (proposals C2943127 are zero-stock consigned). LEFT UNCODED in the BOM on purpose. |
| J1 | XT60PW-M (THT) | coded C98732; if JLC can't place the THT part, hand-solder. |
| F1 | 178.6165 ATO fuse holder + a 15 A ATO blade fuse | holder coded C207061; **the blade fuse itself is a user-supplied insert**, not on the BOM. |
| LA1, LB1 | Sunlord MWSA1005S-3R3 inductor | coded C17700181 but no EasyEDA 3D model — eyeball orientation in the JLC preview. |

## Stock re-check on order day (low-ish stock parts)

Re-run `jlc_stock_check.py bom.csv` the day you order. Two parts had modest stock
2026-07-20 (both ≥ 5× need then): **C17700181** inductor (303) and **C207061** fuse
holder (299). LM74800 C3215600 (458) and LM5145 C485912 (569) also worth a glance.

## JLC preview checklist (before paying)

1. **Rotations** — SMD rotation in the preview is exactly what the machine does. The
   exporter auto-corrected the DPAK/VSON/VQFN/e-cap families; still eyeball the diodes
   (D1/D2/D3 SMB), the two LEDs (D4/D5), and both electrolytics (CE1, CA7/CB7) for
   reel-orientation.
2. **THT connectors** — XT60 (J1) opening faces the WEST board edge; the 3× USB-A
   (J2/J3/J4) openings face the EAST edge; USB-C (J5) opening faces NORTH. Confirm each
   in the preview (THT offset is cosmetic, but orientation is an operator instruction).
3. **Advanced (small-via) option is ticked.**
4. **Missing 3D models** (Sunlord inductors) render as empty space — cosmetic, the part
   still mounts.

## FIRST-POWER RITUAL (do this before the first real pack)

The board has NO functional silk on this rev (see the two silk items in
`verification/policy_audit.md` — deferred to next spin). So mark/verify by meter:

1. **XT60 polarity — the single most important check.** On J1, **pad 1 = the "−"
   (negative/GND) blade, pad 2 = the "+" (VBATT) blade.** Multimeter-continuity the "−"
   blade to a GND point and the "+" blade to the fuse F1 input before applying any pack.
   A reversed pack is blocked by the LM74800 + back-to-back FETs, but confirm polarity
   anyway — polarity bugs are electrically self-consistent and invisible to every
   automated check.
2. Confirm the **15 A ATO blade fuse** is inserted in F1.
3. Power the board with a current-limited bench supply at 12.6 V first; verify both
   5 V rails come up (~5.08 V, D4/D5 LEDs lit) and the UVLO cuts off below ~8.8 V.

## Port ratings (label your enclosure accordingly — no silk this rev)

- **USB-A ×3 (J2/J3/J4)**: 5 V, hard-limited **2.5 A each** (TPS2557, auto-retry + thermal).
- **USB-C (J5)**: 5 V, **advertises 3 A** (dual 10k Rp, no PD). Copper + regulator carry
  up to ~6 A for loads that draw past advertisement, BUT the USB4105 receptacle's VBUS
  pins are rated 5 A collectively — treat 6 A as short-term headroom, not continuous, or
  fit a higher-rated receptacle next spin. See `verification/notes.md`.

## Protection recap (all hardware, no firmware)

15 A fuse → LM74800 reverse-polarity block + HW UVLO (9.33 V on / ~8.8 V off) + OV
(15.25 V) → input TVS (SMBJ16A) → dual synchronous bucks (valley OCP) → per-port TPS2557
(2.5 A) → rail TVS (SMBJ5.0A). Safe from first power-up.

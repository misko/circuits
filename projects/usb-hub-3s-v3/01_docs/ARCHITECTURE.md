# architecture: usb-hub-3s-v3 (rev v1.3)

**What this board IS:** a PROPRIETARY 3S-LiPo POWER-DISTRIBUTION board - NOT a
USB hub, NOT USB-PD / USB-standards-compliant. It fans a protected 3S pack out
to 3x USB-A **charging** ports (5V, dumb DCP advertisement, NO data hub) and 1x
USB-C **power** port that is a proprietary Pi-dedicated 5V/5A rail (Raspberry Pi
5 with `PSU_MAX_CURRENT=5000`; a standards sink sees only the 3A CC-Rp offer).
Input is a PROTECTED 3S pack + balance charger ONLY.

v3 = v2 with the USB-C PD cell removed (ADR-0001). v1.2 replaced the v1.1 TPS26631
eFuse with a DISCRETE protection chain (ADR-0002): Q6 (AON6403 enable-gated P-FET,
reverse-block) -> F2 (PPTC polyfuse, over-current) -> VBUSC with D5 (SMBJ6.0A
uni-directional TVS) as SECONDARY over-voltage mitigation. The buck-C loop senses
the LOCAL 5VC node, a master-off slide switch gates both bucks (and opens Q6), and
input/output MLCC ratings are raised. v1.3 fixes the v1.2 DO-NOT-ORDER blockers:
R12 catalog-verified 4.12k (C2984354, code baked so it can't value-resolve to 3.74k),
the buck-C setpoint re-derived against the actual Q6+F2 path, and D5 moved to a
catalog-confirmed UNIDIRECTIONAL code (C113976; C140903 was catalog-bidirectional).
All other cells carry forward from v2 unchanged and proven-routable.

**Over-voltage posture (HONEST, ADR-0002 A3/D3):** the discrete chain protects
against short/overload (F2) and reverse-feed in the OFF state (Q6). It is NOT a
guaranteed cutoff against a sustained buck high-side short — D5 clamps ~10.3V and F2
must trip (a best-effort crowbar). Acceptable for a supervised prototype with a
replaceable Pi. Escalation boundary (verbatim): "add active OVP if the system becomes
unattended, hard-access, carries valuable storage, or powers expensive SDR".

## Block diagram

    3S LiPo (9-12.6V)
      XT60 -> F1 fuse -> Q1 reverse-polarity P-FET -> D1 TVS(on VIN) -> VIN
        |
        +--> BUCK A (LM5116 + Q2/Q3 + L + shunt) --> 5VA rail (<=6A)
        |       -> 3x [TPS2557 switch + USBLC6 ESD] -> 3x USB-A receptacle (5V/2A)
        |       -> 2x TPS2513A DCP (data-line charging advertisement)
        |
        +--> BUCK C (LM5116 + Q4/Q5 + L + shunt) --> 5VC rail (<=5A)
                -> Q6 (AON6403 enable-gated P-FET, reverse-block) -> PMID
                -> F2 (SMD2920-700 PPTC polyfuse, 7A hold, over-current) -> VBUSC
                     -> D5 (SMBJ6.0A uni-dir TVS to GND, SECONDARY over-voltage)
                     -> USB-C VBUS (5V/5A, PLAIN)
                -> buck-C FB SENSES LOCAL 5VC (5.352V; connector = 5VC - Q6+F2 IR)
                -> CC1/CC2 Rp pull-ups (source-present advertisement)
                -> VBUS bulk caps + ESD
     (master-off: SS12D07 slide switch grounds ENKILL -> both LM5116 EN + Q6 off)

## Power tree
See `03_src/rules/power_tree.yaml` — both rails step-down bucks, E-TOPO PASS,
worst-case input 7.1A @ 9V (57.15W out / 0.9 eff = 63.5W in).

## The USB-C port (v3 no-PD; v1.2/v1.3 DISCRETE-PROTECTED — ADR-0002)
- VBUS = **VBUSC**, fed from the 5VC buck through the discrete chain: Q6 (AON6403
  P-FET, D=5VC/S=PMID, ENABLE-GATED via Q7 BSS138 off ENKILL) -> PMID -> F2
  (SMD2920-700 PPTC 7A-hold polyfuse) -> VBUSC. No PD source controller, no eFuse.
- Protection: over-current = F2 (resettable polyfuse, also bounds sustained
  back-feed); reverse-feed in the OFF state = Q6 body diode (blocks PMID->5VC when
  Q6 is off, RT-T4); over-voltage = D5 (SMBJ6.0A uni-dir TVS) — SECONDARY/best-effort
  crowbar, NOT a guaranteed fail-high cutoff (see the honest posture above).
- Setpoint (v1.2 LOCAL-SENSE, kept): the buck-C FB senses the LOCAL 5VC node, so the
  loop regulates 5VC = 1.215*(1+4.12/1.21) = 5.352V nom (5.27V @Vref-1.5%). The
  connector = 5VC minus the Q6+F2 delivery IR (Q6 ~4.3 mOhm + F2 R1max 18 mOhm cold /
  ~31 mOhm hot). E-MARGIN PASS (see power_tree.yaml). R12 = 4.12k 0.1% (C2984354,
  CATALOG-VERIFIED); buck-A R3 stays 3.92k (C728591, no series delivery drop).
- CC1/CC2: Rp pull-up resistors so the Pi detects an attached source +
  orientation. The Pi is configured `PSU_MAX_CURRENT=5000` (bootloader EEPROM)
  to skip PD negotiation and draw its full 5A — see ADR-0001.
- This port is Pi-DEDICATED and NON-standards-compliant by design; a generic
  USB-C device would see a non-PD source (cap at 3A). Silk + README say so.

## Fab tier
STANDARD target — the advanced-tier driver (the TPS25740A 0.5mm QFN) is gone.
Every remaining IC is leaded (HTSSOP / SOT / SOIC), all proven-routable on v2.

## What carries forward from v2 (do not redesign)
- Input protection chain (D1-corrected: TVS after Q1 on VIN).
- Both LM5116 5V buck cells (control cluster + FET pair + inductor + shunt).
- 3x USB-A port cells (TPS2557 + USBLC6 + connector) + the DCP.
Only the PD cell is removed and replaced by the simple USB-C port above.

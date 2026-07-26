# Pin review — cooksense v1.3, 2026-07-26

**Status: dossiers REGENERATED for v1.3; the narrative group review is CARRIED
from v1.0 and is NOT re-run.** That is a declared gap, not a silent one — see
the limits section.

## What is current

`pin_audit.py` re-run against this archive's board and BOM on 2026-07-26:
**74 dossiers**, one per multi-pin part, including the parts that did not
exist when the v1.0 narrative review was written — `J_ISOLOOP` (the merged
isolated block) and `U_COMP2` (the open-thermistor comparator).

```
D_DOOR D_ESD_IN D_ESTOP D_LCCLK D_LCDAT D_REVCLAMP D_TVS F1 J_DOOR J_ESTOP J_ISOLOOP J_KEY_MATRIX J_LOADCELL J_MODE J_PI J_PWR J_RH_AMBIENT J_RH_EXHAUST J_TC J_THERM_A J_THERM_B K_D1 K_D2 K_D3 K_D4 K_PRESS K_STOP K_U1 K_U2 K_U3 K_U4 K_U5 K_U6 Q_COIL Q_COILDRV Q_REV Q_SWA Q_SWB Q_SWDRVA Q_SWDRVB Q_SWDRVRHA Q_SWDRVRHE Q_SWRHA Q_SWRHE U_ADC U_AND1 U_AND2 U_AND3 U_CAND1 U_CAND2 U_COMP U_COMP2 U_DECD U_DECDEN U_DECU U_DECUEN U_EFUSE U_EXP U_FAULTAND U_LATCHA U_LATCHB U_LATCHG U_LDO U_OENAND U_ONESHOT U_OPTO U_OSCLR U_SCHM U_SR1 U_STOPINV U_TC U_ULNA U_ULNB U_WD
```

Machine pin checks that DO cover every part on this board and are green:
- `audit_board.py` I-POL: **18 polarity checks** pass (pad-1 net vs the
  footprint's polarity marker, every 2-pad polarized part).
- P-FACT `pad1_net_polarity` on CE1 — the part that shipped REVERSED on v1.0
  and v1.1 — **executes and passes** against this archive's netlist.
- schematic-parity (kicad-cli): **0**, so no pin is connected differently on
  the board than in the schematic.
- E-INV: **83/83**, including per-pin `pin_on_net` asserts on the isolated
  loop (J_ISOLOOP.1-.4) and the safety chain.

## The v1.0 narrative review, and why it is not reproduced here

The v1.0 review was 5 fresh zero-context group agents over ~50 parts and it
reported `INCOMPLETE — awaiting 4 group reports`. Carrying an INCOMPLETE
review forward onto a later board would be worse than not carrying it: it
would read as coverage. It is therefore NOT shipped as a v1.3 result.

Its one undispositioned finding — the '238 floating-enable concern — HAS been
resolved, by measurement, and the resolution is in `dispositions.md`: the
board carries R_DECUPD/R_DECDPD 100k pull-downs AND gates E3 through
SN74LVC1G11 ANDs, so a 595 Hi-Z drives the enables LOW, not high.

## Limits, stated

No fresh human-equivalent narrative pin review was run for v1.3. The parts
whose pin maps changed since v1.0 (J_ISOLOOP, U_COMP2, R_OPENT/R_OPENB,
R_CLMPA/B, R_DOORPD, R_WDPETPD, R_TEMPOK) are covered by the machine checks
above and by their 02_parts dossiers, not by a second human reading.
**If a narrative pin review is a release requirement for this board, this
release does not satisfy it and should not be read as doing so.**

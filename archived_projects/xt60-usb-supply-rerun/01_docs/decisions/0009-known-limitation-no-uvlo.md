# ADR 0009 — KNOWN LIMITATION: no battery under-voltage lockout (accepted, must be mitigated externally)

Status: accepted 2026-07-17 (portfolio policy audit finding M7)

The board has NO low-battery cutoff. The SY8368QNC bucks operate down to
~3.9V input — far below the 3S LiPo safe floor (~9.0V, 3.0V/cell) — and
the always-on power LED draws continuously. A pack left connected WILL be
over-discharged and damaged (fire risk on re-charge).

Decision: accepted for v1.0.x as-built; MITIGATION REQUIRED at system
level — use a pack with a BMS that includes discharge protection, or an
external low-voltage alarm/disconnect. Any future copper spin SHOULD add
a UVLO front end (see usb-power-3s ADR-0004: LM74800 EN/OV ladder, 9.33V
disconnect, ~$3).

This limitation was identified in the independent design cross-audit
(2026-07-17) and was previously documented nowhere in the project — that
absence is the defect this ADR corrects. Carry a warning forward into
every future ORDER_README.

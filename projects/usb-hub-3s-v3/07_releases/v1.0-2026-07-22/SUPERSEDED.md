# SUPERSEDED

This release **v1.0-2026-07-22** is superseded by
**`07_releases/v1.1-2026-07-23/`**.

**Reason:** v1.1 is the review-driven revision — it adds the protected-VBUS eFuse
cell (TPS26631 + Q6/Q7 reverse-current block, 5.83 A current-limit, 5.91 V input-OV
cutoff), moves the USB-C setpoint to **5.151 V sensed at the connector** (resolving
the Blocker-2 4.97 V finding), adds a **master-off switch (SW1)**, and raises the
buck caps to **50 V input / 10 V output** (RT-T2/RT-T5). See
`../v1.1-2026-07-23/ORDER_README.md` and
`../v1.1-2026-07-23/verification/2026-07-23_v1.1_fix_confirmation.md`.

v1.0 remains a valid historical record of what was sealed on 2026-07-22 and is
otherwise unchanged (immutable). This file is the only addition.

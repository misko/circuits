# SUPERSEDED — DO NOT ORDER FOR PCBA

**Superseded by:** `crow-recorder-central-v2-v1.5-2026-07-25`

**Reason: this release's `fab/cpl.csv` places J2, the board's ONLY USB-C
connector, 1.3025 mm off its own pads.**

J2's contacts are 1.150 mm long, so the pad overlap at the shipped coordinate
is **0.000 mm** — not a marginal joint, no joint at all — and the four shell
posts miss their holes, so the part cannot physically seat. A board assembled
from this release has **no USB power and no USB data**, which on this design is
the entire host link.

**Root cause:** the CPL emitted KiCad's **footprint ANCHOR**, an authoring
convenience with no fab meaning. JLC places a part so that *its own* origin
lands on `Mid X/Y`, and that origin is the **centre of the bounding box of the
pad centres** — measured on 227 of 228 cached JLC-native footprints across six
boards (99.6 %). The anchor and the datum coincide for most parts, which is why
this survived undetected; they diverge on connectors. The same release also put
J1 — a true THT barrel jack, and the board's only power inlet — on a
top-side-SMT-only CPL, and populated R_inj1/R_inj2, which bridge ADC channel 1
to channel 5 through 2 kΩ.

**What is still good here.** This release's **bare PCB is fine**: its gerbers,
drills, `fab/bom.csv`, PDFs, STEP and all `source/` files are byte-identical to
v1.5's, and that identity is proven by re-plot, not by copying. Its
**rotations are correct** and are carried forward into v1.5 unchanged — the
rotation defect belongs to v1.3, which carries its own SUPERSEDED.md.

Nothing in this directory has been altered; this file is the only addition, as
the release contract requires. See
`../crow-recorder-central-v2-v1.5-2026-07-25/ORDER_README.md` and its
`verification/replot_identity.txt`.

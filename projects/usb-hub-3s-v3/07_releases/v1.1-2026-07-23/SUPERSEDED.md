# SUPERSEDED

This release **v1.1-2026-07-23** is superseded by
**`07_releases/v1.2-2026-07-23/`**.

**Reason:** v1.2 DROPS the TPS26631 eFuse and replaces it with a simple discrete
VBUS protection chain (ADR-0002; BRIEF A2/D2 user decision). The eFuse was
over-built for a 5 V/5 A Pi-dedicated rail and was the root cause of BOTH v1.1's
board routing wall (its 20-pin HTSSOP IN_SYS pin could not escape the fine-pitch
row) AND v1.1's two electrical order-blockers (post-eFuse FB runaway + SHDN 5.5 V
abs-max). v1.2 protection: `5VC → Q6 (AON6403 P-FET, ENKILL-gated reverse-block
via Q7 BSS138) → F2 (PPTC polyfuse) → VBUSC`, with a D5 (SMBJ6.0A) TVS clamp;
buck-C FB kept on LOCAL 5VC (the v1.1 runaway fix). See
`../v1.2-2026-07-23/ORDER_README.md`,
`../v1.2-2026-07-23/MANIFEST.txt`, and `../../01_docs/decisions/0002-discrete-vbus-protection.md`.

v1.1 remains a valid historical record of what was sealed on 2026-07-23 and is
otherwise unchanged (immutable). This file is the only addition.

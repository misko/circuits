# ADR-0001 — Input protection (mandatory ADR)

Context: board is powered ONLY from cook-hub J6 (5VP + 3V3, both behind
the hub's polyfuse + reverse-PFET + TVS chain, ADR-0001 of cook-hub) over
a short captive XH-to-XH cable. No battery, no external supply, no mains.

Decision: no repeated fuse/reverse/TVS stage (double-fusing a 20 mA load
adds drop and parts, protects nothing new). Local: 10u + 100n per rail;
PESD5V0S1BA on DAT/CLK at J6 (the cable is the exposed surface); shield
bond per D4 keeps drain currents out of AGND.
Residual risk (recorded): hot-plugging J6 while the hub is powered can
glitch AVDD — bring-up checklist orders connections power-off.
UVLO/OV: N/A (SELV, hub-protected).

# ADR-0006 — electronics power architecture (buck + USB co-power)

Status: accepted 2026-07-18

## Context

12–24 V (clamped ≤53 V transient) → 3.3 V at ≤0.4 A peak. Commission
prefers a 60 V-tolerant buck for load-dump margin. USB flashing needs
the MCU alive with no bus connected.

## Decisions

1. **LMR16006XDDCR** (C87080, 21 968 stock, $0.62): 60 V operating /
   65 V abs-max VIN — survives the SMCJ33A clamp (53.3 V) WITHOUT
   depending on the TVS being fast; 0.6 A output vs 0.4 A peak load;
   fixed 0.7 MHz (X version — the 2.1 MHz Y version violates min-on-
   time at 24 V→3.3 V, DETAIL_DESIGN §5); TSOT-23-6, five external
   passives. REJECTED: TPS54202 (28 V — under the clamp), LMR51430
   (36 V abs-max 40 V — under the clamp), TPS54360B (60 V 3.5 A,
   $0.84, 17 k stock — fine part, but 6× the needed current, bigger
   inductor, SO-8 PowerPAD thermal via requirements; kept as the named
   alternate if LMR16006 stock dies), MP2459 (55 V, ok, but genuine-
   MPS stock is the $0.35 clone pool — provenance risk in the one
   part that must survive transients).
2. **Async topology accepted** (external SS310 catch diode): at 0.4 A
   the sync-buck efficiency delta is ~mW-class against a 60–1440 W
   load board; robustness and stock beat it.
3. **UVLO on SHDN** (560 k/100 k, on ≈8.25 V) — ADR-0001 §5.
4. **USB co-power**: AMS1117-3.3 (C6186, JLC Basic, 1.4 M stock) from
   VUSB, diode-OR'd into the rail through B5819W; buck side needs no
   OR-diode (its output stage tolerates the 3.0 V back-bias; the
   SS310 series input diode isolates the bus). Rail = 3.29 V on bus
   power, ≈3.0 V USB-only — all loads in range. REJECTED: powering
   the buck from USB 5 V (LMR16006 min VIN 4.5 V is too close to a
   sagging USB 4.4 V); a second buck (cost, area for a bench-only
   path); no USB power at all (would make every firmware iteration
   need a live 60 A bench supply — unacceptable bring-up ergonomics).

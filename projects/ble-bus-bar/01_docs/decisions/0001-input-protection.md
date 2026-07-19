# ADR-0001 — input protection at a 60 A bolted bus (MANDATORY ADR)

Status: accepted 2026-07-18

## Context

12–24 V battery/automotive-class feed, 60 A aggregate, bolted ring lugs
(ADR-0005). Threats: load-dump/inductive transients, reverse-polarity
hookup at first install, downstream shorts, brown-out corrupting the
stats log. The pipeline mandates this ADR; the honest part is reverse
polarity at 60 A.

## Decisions

1. **No series protection element in the main bus.** A reverse-blocking
   FET or diode passing 60 A continuous costs board area, heat
   (≥0.5 mΩ ideal-diode FET ≈ 1.8 W at 60 A, real ones worse), and money
   — and the industry norm for lug-fed distribution blocks (Blue Sea,
   Eaton, automotive fuse boxes) is unprotected + marked polarity. The
   bus itself is fuse-per-load protected (the ATO fuses), not
   reverse-protected. REJECTED alternatives: 60 A ideal-diode controller
   + paralleled FETs (cost/complexity, +1 failure mode in the main
   current path); series schottky bank (≈30 W at 60 A — absurd).

2. **Protect the ELECTRONICS BRANCH, not the bus** (commission
   directive): VBUS → F7 (2 A SMD fuse, 63 V) → D7 SS310 series
   schottky (reverse blocking, 100 V) → SMBJ33A local clamp → buck.
   A reversed feed leaves the entire electronics chain untouched (D7
   blocks); a failed-short TVS or buck blows F7, not the bus.

3. **Bus TVS = SMCJ33A** (D9): standoff 33 V > 28.8 V (24 V lead-acid
   absorb charging), V_BR 36.7 V, clamp ≤53.3 V at 1500 W/10 ms.
   Chosen against the downstream ratings, all of which exceed the
   clamp: INA238 85 V, LMR16006 65 V abs-max, SS310 100 V (the
   commission's "SMCJ33A-class, respect 24 V operating" instruction,
   satisfied). This is exactly why INA238 was selected over INA226/
   INA3221 (ADR-0003) — 36 V/26 V parts die at the clamp voltage.

4. **Reverse polarity residual risk — documented, not solved.** When
   the feed is reversed, D9 conducts FORWARD and holds the bus near
   −1 V (until D9 or the source dies; D9 fails short = crowbar, which
   is the protective direction). The INA238 IN±/VBUS pins see ≈−1 V
   through their 10 Ω series resistors → ≈70 mA into the ESD rails:
   above the 5 mA abs-max, survivable for a seconds-long mistake,
   fatal if left connected. Mitigations that ARE shipped: (a) large
   silk "+12-24V IN" / "GND" polarity marks at the studs (P5 silk),
   (b) different stud sizes (+ = M5, GND-ref = M4) so lugs don't swap
   silently, (c) ORDER_README first-power ritual: meter the feed
   polarity against the marked studs BEFORE bolting the battery.

5. **UVLO for clean logging shutdown**: buck SHDN divider 560 k/100 k →
   converter enables at ≈8.25 V (math in DETAIL_DESIGN §4); firmware
   flushes the flash ring below 10 V bus (INA VBUS telemetry) and the
   ESP32-C3 internal brown-out closes the last gap. No separate
   supervisor IC — the buck's enable divider + 22 µF×2 output hold-up
   (≈ms at 0.1 A) cover the write-in-flight window for a 256-byte page.

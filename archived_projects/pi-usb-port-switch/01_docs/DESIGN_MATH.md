# Design calculations — Pi USB port switch

This note records the quantitative claims carried into the v0.1.0 hardware
archive. Machine-readable limits remain authoritative in `03_src/rules/`.

## External 5 V distribution

The design load is four ports at 0.9 A plus up to 0.45 A for local 3.3 V loads:

```text
I_total = 4 x 0.9 A + 0.45 A = 4.05 A
```

The required supply is regulated 5.15-5.25 V at the board terminal and rated
at least 5 A. The extra source rating covers wiring and transient margin; it is
not permission to exceed the 0.9 A continuous per-port design limit.

Each output path has a 400 mV / 444 mOhm total drop budget at 0.9 A:

```text
R_budget = (5.15 V - 4.75 V) / 0.9 A = 0.444 ohm
allocated = 265 mOhm protection/switch + 35 mOhm PCB/joints
          + 100 mOhm mated contacts = 400 mOhm
margin = 44 mOhm = 40 mV at 0.9 A
```

The allocation is a design bound, not a substitute for measurement. The first
article must close it by four-wire measurements at operating temperature.

TPS2557 programming is bounded at 0.926-1.273 A, which contains the 0.9 A
continuous target while retaining fault-current limiting. A 7.5 A user-fit
input fuse protects the shared feed; it does not replace the four electronic
port limiters.

## Copper and vertical transfers

Rules-audit minimum widths and independent 10 C-rise screens are:

| Class | Current | Routed floor | Screened minimum | Result |
|---|---:|---:|---:|---|
| protected input trunk | 4.05 A | 2.50 mm plus pours | 2.068 mm | pass |
| switched port VBUS | 0.90 A | 0.50 mm plus pours | 0.260 mm | pass |
| local 3.3 V | 0.45 A | 0.40 mm, with declared package necks | 0.100 mm | pass |

The via screen uses TI SLVA959B Table 3-1 / IPC-2152 capacity with no credit
for fill material. All nine declared transfers pass. The tight per-port output
transfer uses two 0.20 mm finished holes credited at 1.10 A total versus
0.90 A required. The protected trunk bank uses eight 0.30 mm holes credited at
6.72 A versus 4.05 A required.

## Local 3.3 V rail

The TLV76133 rail covers four redrivers at 98 mA typical each plus the USB 2
switches and logic allowance, for a 0.45 A design bound. Its specified output
range under the recorded accuracy assumption is 3.242-3.358 V. The regulator
dissipation ceiling used for review is 940 mW at 35 C ambient; first-article
temperature, startup and brownout measurements remain mandatory.

## USB differential geometry

All 56 declared USB 2 and SuperSpeed P/N segments are connected. The source
contract fixes 0.25 mm trace width, 0.18 mm pair gap, short stub-free routing,
and an adjacent uninterrupted ground reference. DRC and realized-copper checks
prove geometry and connectivity, but not absolute impedance. Before ordering,
JLCPCB must confirm a named four-layer stackup and a 90-ohm differential solve
for the shipped copper. USB 3 Gen 1 remains a first-article performance target;
USB 2 is the accepted fallback.

## Via process selection

The board contains 749 vias. Exactly 61 realized 0.35/0.25 mm via-in-pad
barrels are marked filled and capped. The remaining 688 vias use disjoint
0.20 mm or 0.30 mm drill families and must remain ordinary. The order must
select copper-paste fill and copper cap for the complete 0.25 mm drill family
only; the JLC preview must echo that selection before payment.

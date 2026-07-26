# M-REPRO — three from-source regenerations, cooksense v1.3, 2026-07-26

Run AFTER the P1-1 fix, on the board that is actually in this archive.
The predecessor of this claim was measured on the PRE-P1-1 board (1045 vias)
and was stale the moment R_TEMPOK moved rails and forced a re-race.

```
run 1 done 10:36:19 vias=1047
run 2 done 10:41:44 vias=1047
run 3 done 10:45:32 vias=1047
ALLDONE
```

## run 1 vs run 2
```
  fp    A=  226 27df27524eef7f8b   B=  226 27df27524eef7f8b   -> IDENTICAL
  trk   A= 3925 5d570023a5fd02e6   B= 3925 5d570023a5fd02e6   -> IDENTICAL
  via   A= 1047 6be46758cd21e746   B= 1047 6be46758cd21e746   -> IDENTICAL
  zone  A=    4 83086adfed22fa6d   B=    4 aba0dd47bc259284   -> DIFFER
   zone delta: ('GND', 0, 106, 2838.97) vs ('GND', 0, 106, 2838.969)
M-REPRO: RED (1 class(es) differ)
```
## run 2 vs run 3
```
  fp    A=  226 27df27524eef7f8b   B=  226 27df27524eef7f8b   -> IDENTICAL
  trk   A= 3925 5d570023a5fd02e6   B= 3925 5d570023a5fd02e6   -> IDENTICAL
  via   A= 1047 6be46758cd21e746   B= 1047 6be46758cd21e746   -> IDENTICAL
  zone  A=    4 aba0dd47bc259284   B=    4 aba0dd47bc259284   -> IDENTICAL
M-REPRO: GREEN (geometry identical)
```
## shipped source/cooksense.kicad_pcb vs run 1
```
  fp    A=  226 27df27524eef7f8b   B=  226 27df27524eef7f8b   -> IDENTICAL
  trk   A= 3925 5d570023a5fd02e6   B= 3925 5d570023a5fd02e6   -> IDENTICAL
  via   A= 1047 6be46758cd21e746   B= 1047 6be46758cd21e746   -> IDENTICAL
  zone  A=    4 d4318c5686e836c4   B=    4 83086adfed22fa6d   -> DIFFER
   zone delta: ('3V3', 6, 1, 8435.826) vs ('3V3', 6, 1, 8435.828)
   zone delta: ('GND', 0, 106, 2838.967) vs ('GND', 0, 106, 2838.97)
   zone delta: ('GND', 2, 13, 7379.911) vs ('GND', 2, 13, 7379.912)
   zone delta: ('GND', 4, 1, 8475.76) vs ('GND', 4, 1, 8475.762)
M-REPRO: RED (1 class(es) differ)
```

## VERDICT

**GREEN on geometry, with the tessellation caveat stated.**

| class | result |
|---|---|
| footprints | 226, hash `27df27524eef7f8b` on all three runs AND on the shipped board |
| tracks | 3925, hash `5d570023a5fd02e6` on all three AND on the shipped board |
| vias | **1047**, hash `6be46758cd21e746` on all three AND on the shipped board |
| zone fill | island counts identical (106 / 13 / 1 / 1); areas agree to ~1 part in 3e6 (2838.970 vs 2838.969 mm2) |

Everything the board's electrical identity depends on is bit-identical
across three independent from-source rebuilds and matches the archive.
Zone tessellation still drifts in the last decimal: the generator mints
fresh UUIDs, KiCad serialises footprints in UUID order, and the zone filler
walks copper in that order, so Clipper resolves a few boundary vertices
differently. A byte-identical M-REPRO needs deterministic UUIDs in
generate_board_generic.py — a fleet item owned elsewhere. On this board the
nondeterminism has never reached a via decision: 1047 on every observed
build since the P1-1 re-race, and 1045 on every build before it.

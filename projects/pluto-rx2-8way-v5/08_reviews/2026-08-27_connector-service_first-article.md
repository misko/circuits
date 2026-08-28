# Pluto RX2 eight-way v5 connector-service first-article observation

- recorded: 2026-08-27
- evidence grade: qualitative first-article observation
- affected design lineage: Pluto RX2 eight-way v5
- immutable design authority inspected: PCB release `v0.2.1-2026-08-14`
- physical article identity: reported as a fabricated v5 board; serial number,
  exact cable/antenna MPN, tool, torque, and enclosure revision were not bound
- readiness effect: connector mate/tighten/service access is `INCOMPLETE`

## Reported behavior

The fabricated board is difficult to hand-tighten at the SMA ports. The
connectors are close side by side, and their mating faces do not project far
enough beyond the PCB edge to provide a comfortable grip. This is valid
negative evidence against the prior access assumption. It is not a dimensional
measurement and does not establish a replacement pitch or overhang.

## Exact design facts

The board uses nine Amphenol RF `901-143-6RFX` right-angle THT SMA jacks. The
five north connectors are on 15.0 mm pitch and the two connectors on each side
are on 18.0 mm pitch. The part dossier records a 7.0 mm body width and an
11.6 mm RF-pin-datum-to-mating-face dimension. The floorplan intentionally
places that mating face exactly on `Edge.Cuts`, giving 0.0 mm nominal positive
exposure beyond the PCB profile.

Those facts prove that the bare connector bodies fit. They do not prove room
for the male coupling nut, fingers, wrench head, wrench rotation, cable boot,
bend, or a populated neighboring port. The current enclosure design can
further recess the nominal mating face behind its exterior wall.

## Superseded access conclusion

The 2026-08-13 render review said that 15 mm and 18 mm pitch provided clear
barrel, mating, and coupling-nut access, and later reported no connector-access
or tool-space defect. That evidence consisted of registered bare connector
models and unobstructed outward axes. It did not include a selected mating
part, coupling nut, fingers, tool, torque operation, neighboring cables, or the
final enclosure. The fabricated feedback therefore supersedes those access
claims without changing the review's valid body-registration and orientation
findings.

## Failure classification

This is a connector-assembly/service-cell failure, not one transferable
"SMA tolerance":

- exact mating hardware was not commissioned before placement;
- no positive grip exposure was required beyond PCB and enclosure surfaces;
- the compact pitch was graded from receptacle bodies/courtyards rather than
  installed coupling hardware and its operation;
- hand-start, final tightening, anti-rotation, and removal were not modeled as
  separate operations;
- no all-neighbors-populated service test was required;
- no installation-torque reaction path or PCB-flex acceptance was declared.

## Required evidence before choosing new dimensions

1. Bind the exact supported cable, antenna, or adapter MPN and drawing.
2. Record coupling-nut diameter/across-flats, axial grip length, fully mated
   position, specified torque, selected tool geometry, and approach/sweep.
3. Measure actual face-to-PCB-edge exposure on several fabricated ports.
4. Test hand-start, final tightening, loosening, and removal with both neighbors
   populated, first bare and then with the final enclosure.
5. Observe connector rotation, PCB deflection, solder-joint movement, cable
   chafe, and bend clearance.
6. Use a connector-bank coupon to compare candidate pitch and positive exposure
   before routing another dense RF board.

Until those facts exist, this observation may reject the existing access
assumption and cap readiness, but it must not be converted into a guessed
millimeter allowance.

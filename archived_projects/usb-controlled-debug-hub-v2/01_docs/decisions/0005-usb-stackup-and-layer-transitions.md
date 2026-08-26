# ADR 0005 — USB stackup and layer transitions

Status: accepted for pre-route; order-time impedance confirmation remains open

## Context

The reviewed placement puts each connector-side PESD2USB3UX shunt array and
each FSUSB42 data switch on B.Cu to meet mechanical and proximity constraints. The
earlier prose expectation that every USB pair would remain on F.Cu with no vias
therefore contradicted the actual board. Routing against that fiction would
either move accepted placement silently or create unreviewed layer changes.

JLCPCB publicly documents the JLC04161H-7628 four-layer construction and an
order-time impedance-calculator workflow. A current public JITX implementation
of that construction gives a preliminary 90-ohm differential outer-layer
geometry of 0.2332 mm trace width, 0.15 mm pair gap and 0.30 mm clearance. This
implementation is corroborating input, not manufacturer approval.

Sources:

- https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator
- https://jlcpcb.com/quote/pcbOrderFaq/PCB%20Stackup
- https://docs.jitx.com/en/4.0/_modules/jitxlib/jlcpcb/JLC04161H_7628.html
- https://ww1.microchip.com/downloads/en/DeviceDoc/USB2517-Hardware-Design-Checklist-00004211.pdf
- https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ApplicationNotes/ApplicationNotes/en562810.pdf
- https://www.ti.com/lit/an/spraar7a/spraar7a.pdf
- https://www.nexperia.com/product/PESD2USB3UX-T

## Decision

Use the four-layer JLC04161H-7628 construction with both inner layers as
continuous GND references in USB corridors. F.Cu references In1.Cu; B.Cu
references In2.Cu.

- `P1..P4_PORT` route on B.Cu with no vias.  Microchip's USB2517 checklist says
  never to branch the USB signals to reach protection and instead to place the
  protection device directly on the differential traces.  The connector
  traces therefore land on PESD2USB3UX pins 1/2 and continue along either side
  of pin 3; the shunt device does not divide either signal net.  Pin 3 receives
  the shortest available low-inductance connection to the adjacent GND plane.
- `MGMT` routes on F.Cu with no vias.
- `UP_HUB` and `P1..P4_HUB` may use F.Cu and B.Cu. Each conductor is intended
  to make one matched transition; paired signal vias receive nearby GND return
  vias and neither trace crosses a reference-plane void.
- Route the differential pairs before power and control copper.
- Keep each receptacle-to-ESD fan-in at 1.963 mm and preserve the direct-through
  topology.  A three-pin SOT23 necessarily widens the pair around its grounded
  land before the 0.2332/0.15 mm field geometry can begin.  The deterministic
  connector-side routes measure 7.130 mm worst uncoupled length in KiCad DRC,
  so those connector/protector nets alone use `USB_HS_PROTECTED` with a
  7.50 mm ceiling.  The first authenticated internal transition route then
  falsified the provisional 2.0 mm internal ceiling: KiCad measured
  4.6536--6.1951 mm before conductor matching and 4.6536--8.0795 mm after the
  required P/N compensation.  The spans are localized to the USB2517I and
  FSUSB42 escapes, one symmetric layer transition per conductor, and the two
  compensation regions; the field routes remain coupled.  Microchip AN15.17
  and TI SPRAAR7A require the discontinuities and via count to be minimized
  but specify no numeric uncoupled-length maximum.  `USB_HS` therefore uses a
  measured 8.50 mm ceiling (0.4205 mm margin), while the independent realized
  copper contract still limits end-to-end P/N spread to 1.00 mm.  These are
  source-owned topology bounds, not DRC waivers or permission for arbitrary
  single-ended routing.
- Measure P/N skew for every segment and every complete functional link from
  realized copper. Segment spread must not exceed 0.50 mm; end-to-end spread
  must not exceed 1.00 mm.  The four deterministic connector-side routes
  measure 0.305 mm P/N spread each.  The routed end-to-end spreads after KRT's
  conductor-level compensation are 0.3054, 0.2139, 0.4983 and 0.0210 mm for
  ports 1--4 respectively.

The preliminary route geometry is 0.2332/0.15/0.30 mm. The release remains
blocked until the actual JLC order flow confirms the chosen stackup, 90-ohm
differential geometry and coupon/impedance option. If the order-time solve
differs, update the source contract and reroute before minting a release.

## Consequences

The bottom-side USB components no longer force unreferenced routing. The board
uses In2 as a reference plane rather than a general power plane; 5 V and 3.3 V
distribution remain on outer-layer pours/tracks.  The SOT23 discontinuity is
bounded and explicit rather than hidden by a false in-line-series model.  A
route that adds a TVS signal stub, gratuitous USB vias, asymmetric transitions,
excessive uncoupled length, reference-plane breaks, or unmeasured skew fails
review even if ordinary DRC is green.

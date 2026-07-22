# Learnings — routing stage (usb-hub-3s, 2026-07-21)

Candidate-canon findings from taking a 112-part 4-layer board from
track-free to DRC 0/0/0. Each was paid for in cycles.

## R-KEEPOUT-LEAK (candidate canon)
KRT keepout rects are centerline-based: a 0.3 track whose centerline sits
0.05 outside the rect juts 0.1 of copper INTO it. A protected corridor
must be inflated by (track_width/2 + clearance) beyond the copper you
need, or the router will hug the fence and kill the corridor by
0.005 mm. Two re-route cycles were lost to exactly this.

## R-TAP-ENDPOINT-PAD (candidate canon)
A tap whose `to` is a bare [x,y] inside a pour is a fill-void lottery:
clearance shaving around unrelated copper can leave the endpoint dry
(observed: endpoint landed in a void framed by PATH_G + SNS_OUT_N and
DRC'd as track_dangling). When a same-net PAD exists on the far side,
target the pad (`to: Q6.3`) — pads cannot be shaved away.

## R-HOLE-CLR (fixed in pcb_toolkit)
Hole probes must use hole-to-copper clearance (tier: 0.2), not routing
clearance (0.13). The toolkit accepted paths 0.14 mm from J5's NPTH
alignment holes twice before the root fix in `collides()`.

## R-SWIG-INTRA-PASS (fixed in route_and_stitch_generic)
The stitch driver's fresh-interpreter barrier only fires BETWEEN passes.
`drop_dangling` removed tracks between its own sweeps and re-read the
board in-interpreter → `GetStart()` returned a bare SwigPyObject. Any
pass that iterates remove→re-read must model the fixpoint in Python and
remove once at the end. Earlier boards passed only because sweep 1 found
nothing.

## R-RESCUE-SILENT-SKIP
`pad_rescue` skips a pad whose via site is blocked (CC2's B.Cu diagonal
0.27 mm under R14.1) and the failure surfaces only as a DRC unconnected
item. A named plane tap per rescue-critical sense pad is cheap insurance;
better: check `pending` after stitch.

## R-TAP-ORDER-COUPLING
Taps are order-dependent in BOTH directions: an early tap can block a
later one (LX1's long F leg vs the VOUT_PDS rendezvous), and reordering
can flip which one fails. When two taps contest a corridor, give the
constrained one (fewest viable paths) the earlier slot, or move the
contested geometry to a rendezvous point.

## R-ZONE-SLOT-BACKFIRE
Cutting a slot in a pour to kill a fill pocket can sever the pour's only
connecting band and orphan a whole lobe (VBUSC east lobe with 4 VBUS
pins). Measure the islands (ZONE_FILLER + OutlineCount) before surgery;
prefer a bonder tap over zone surgery when the pocket contains pads.

## R-VIA-DANGLING-RENDEZVOUS
via_hop rendezvous points where ALL legs arrive on the hop layer leave
the shared via with no top-side copper → DRC via_dangling. Give the
rendezvous an F.Cu same-net patch (0.6×0.6 was enough) or land one leg
on F.

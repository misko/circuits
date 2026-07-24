# learnings — cooksense v1.1 placement (rot0 isolation comb), 2026-07-24

1. **A coupling pitch is not a fit claim.** The part.yaml "15.24mm
   super-column pitch" was vetted for MAGNETICS in the rot0/vertical
   orientation; commissioning it for a rot90 row (19.90mm courtyard ALONG the
   row) was mechanically impossible (−4.66mm courtyard overlap), found only by
   measuring the footprint before editing the floorplan. Avoid next time:
   every pitch/spacing figure in a part.yaml should name its ORIENTATION.
   candidate-canon: yes (P-LAYOUT addendum: layout figures carry orientation)
2. **The isolation comb worked first-try electrically.** Pairing rot180/rot0
   so contact columns share pockets kept 0 logic-through-pocket crossings and
   measured I-ISO 6.12mm (the intra-relay pad-column floor, identical to
   v1.0's straight barrier). The DRC deny-comb (25 rects) + wave keepouts
   (User.2/User.3 comb) machine-enforce it. candidate-canon: yes (archetype:
   "isolation comb" for vertical 2-column isolation parts, harvest to
   floorplan-archetypes.md)
3. **The legalizer RIPPLES: moving one floating part can displace a routed
   neighbour.** C_WD's relocation swallowed R_MR's spot and broke its routed
   net; the fix discipline is: diff footprint positions chain-vs-board after
   ANY seed change, and PIN displaced routed parts at their chain positions.
   candidate-canon: yes (suggested check: R-CHAINPIN — reuse rebuild fails if
   any footprint with a routed pad moved vs the promoted chain)
4. **Plane-net passives must be seeded INSIDE the plane band.** The comb
   pushes the plane edge to y53; near-patterns dropped decouplers north of it
   (C_ULNB y51.6) where NO GND service exists. Seed rule: any cap whose only
   nets are plane nets belongs in plane-covered area. candidate-canon: yes

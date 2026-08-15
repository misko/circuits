# Commission learnings

## Host port count must be separated from channel capability
- what happened: the user requested four controlled paths and preferred USB 3, while both named Pi hosts expose only two USB 3 ports.
- root cause: “four USB ports” describes connector count, not the simultaneous host-speed envelope.
- avoid next time: commission templates for host-attached fixtures should separately lock channel count, per-channel capability and simultaneous host capability.
- candidate-canon: yes + suggested check ID D-HOST-ENVELOPE

## Power-only is not automatically a charging-port claim
- what happened: VBUS-on/data-off can supply 0.9 A electrically, but a device may not choose or be permitted to draw it without enumeration or charger advertisement.
- root cause: source capability and sink negotiation behavior are independent USB requirements.
- avoid next time: USB fixture briefs should ask whether “power-only” means raw VBUS, BC1.2/DCP behavior, or a specific charging protocol.
- candidate-canon: yes + suggested check ID D-USB-POWER-MODE

## The power-tree schema does not yet express unregulated distribution rails
- what happened: D-SPEC/E-PATH requires each external output in `power_tree.yaml`, while E-TOPO later requires every rail to name a buck/boost/linear converter; this board uses a current-limited pass-through switch that intentionally converts nothing.
- root cause: the two gates share one `rails:` list but model different subsets of power paths.
- avoid next time: add an explicit `stage: distribution` or `converter: none` schema with voltage-drop/reverse-current grading, and make E-TOPO skip only that declared, checked class.
- candidate-canon: yes + suggested check ID E-DISTRIBUTION

## USB 3 inline fixtures need a qualification claim, not optimistic compliance language
- what happened: the required disconnect fixture adds a cable segment, connectors, protection and signal conditioning to the normal channel.
- root cause: functional switching and 5 Gb/s channel compliance are different proof obligations.
- avoid next time: any inline high-speed fixture should lock cable lengths, insertion-loss strategy and first-article negotiated-speed/throughput evidence during commission.
- candidate-canon: yes + suggested check ID D-INLINE-SI

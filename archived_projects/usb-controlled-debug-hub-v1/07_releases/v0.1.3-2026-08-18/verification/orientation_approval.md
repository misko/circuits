# Connector orientation approval

approval_date: 2026-08-17
approver: user / product owner
approval_quote: "connectors look great!"
decision: APPROVED
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
orientation_subject_sha256: 8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97
machine_verdict: PASS (5/5 edge-facing connectors)
approved_refs: J_PORT1, J_PORT2, J_PORT3, J_PORT4, J_UP

The approval applies only to the exact hash-bound orientation image bundle in
`orientation/`: the four top-mounted USB-A mouths face north/outboard and the
top-mounted USB-B upstream mouth faces west/outboard. It confirms visible
mouth, mounting side, keying, and intended cable approach. Any board or subject
hash change invalidates this approval and requires new rendered views.

JLC placement rotation, THT side/mapping, `C_TRUNK_USB` polarity, stackup,
impedance, and selective-via previews remain separate order-time gates.

# RF fabrication-output review protocol

Run on the **exact plotted Gerber/drill archive**, after fabrication export and
before prototype-order authorization. It verifies that plot/export and order
settings preserve the RF PCB that was reviewed; it is not delegated to JLC.

Inspect the Gerbers in an independent viewer and verify stackup name/order,
copper width/gap at each launch and representative path, mask openings, paste
apertures, plane continuity, via-fence drill/annulus/pitch, board-edge geometry,
and absence of plot clipping or unintended copper/mask merges. Cross-check the
order form's finished copper, impedance-control request/coupon, material,
thickness, and stackup against `rf.yaml` and the solver evidence.

Archive an exact-artifact review:

    review_kind: RF_FAB
    subject: <project + release>
    reviewer: <identity/model>
    independence: independent-from-design-author
    source_commit: <full 40-character SHA>
    artifact_sha256: <SHA256 of exact Gerber/drill zip>
    fab_package_verdict: READY | NOT-READY
    requirement: RF-FAB-... PASS | FAIL

`rf_contract_check.py --require-review fab` verifies the hash and complete
requirement set. `READY` means the package represents the reviewed design and
can be used for a **prototype** order. It is not a production-release claim:
production remains HOLD until the first-article VNA/TDR measurements meet the
numeric `first_article.acceptance` entries.

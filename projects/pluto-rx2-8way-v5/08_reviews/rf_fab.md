review_kind: RF_FAB
subject: pluto-rx2-8way-v5 v0.2.1 exact Gerber and Excellon package
date: 2026-08-14
reviewer: Codex exact-artifact RF fabrication reviewer
independence: independent-from-design-author
context-given: staged release archive and retained RF/assembly contracts
source_commit: 798ef9812019efb9e9857332736926d099192a03
artifact: 06_build/fab/pluto_rx2_8way_v5_gerbers.zip
artifact_sha256: 4e5fe8a6e4da3ec791f1abd1954eb9840399e826c212871c71b3d4285da285ef
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
rf_contract_sha256: 625acbc4c6f40b1a521c011399c0617fa5ec02817a3bccac31f2b149918b00bb
assembly_contract_sha256: 32010672589d173592fa3466def51be65d145002650f5577d9ec21aa571701ac
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
fab_package_verdict: READY
physical_rf_performance_verdict: NOT_YET_MEASURED
requirement: RF-FAB-STACKUP PASS
requirement: RF-FAB-COPPER PASS
requirement: RF-FAB-DRILLS PASS
requirement: RF-FAB-FIRST-ARTICLE PASS
p0_findings: 0
p1_findings: 0
p2_findings: 0

# Exact staged RF fabrication review

The archive contains exactly 13 expected fabrication members: four copper,
two mask, two paste, two silkscreen, one outline, PTH and NPTH. The shipped-byte
payload gate opens the archive, finds pours on all four zone-bearing copper
layers and confirms the copper layers are distinct (with the symmetric inner
planes explicitly accepted). A clean export from the archived board reproduces
all 13 members identically after removing only KiCad creation timestamps.

The PTH data preserves 615 ordinary 0.20 mm vias and the nine protected U1
0.25 mm drills as disjoint families, plus the exact Amphenol SMA holes. The
order remark limits fill/cap to the complete 0.25 mm family. Gerbers preserve
the locally reviewed top CPWG and solid reference planes, but cannot compel a
laminate or assembly service; the uploader echo is therefore mandatory.

The local fabrication package is READY for a prototype uploader review. This
is not permission to order, does not prove C429844 through-hole allocation,
and does not claim RF performance. Production remains HOLD until every path
and required off state passes the retained first-article VNA plan.

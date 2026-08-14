review_kind: RF_FAB
subject: pluto-rx2-8way-v5 v0.1.0 exact Gerber and Excellon package
date: 2026-08-13
reviewer: Codex exact-artifact RF fabrication reviewer
independence: independent-from-design-author
context-given: staged release archive and retained RF/assembly contracts
source_commit: 798ef9812019efb9e9857332736926d099192a03
artifact: 07_releases/v0.1.0-2026-08-13/fab/pluto_rx2_8way_v5_gerbers.zip
artifact_sha256: 71eaba992c478faf33c75ff0d91a1767072fda4eecfa8bd794d5bc232ce42fc7
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
rf_contract_sha256: 101112345ca8b3f6e004b793badb92ae4891da3f54a83a6c42ecb8ddcd37d1c1
assembly_contract_sha256: 993fa63cfbb85f64d1b573a4131d880630a16278226558e597f357f294ce0c4d
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

The PTH data preserves 629 ordinary 0.20 mm drills and the nine protected U1
0.25 mm drills as disjoint families, plus the exact Amphenol SMA holes. The
order remark limits fill/cap to the complete 0.25 mm family. Gerbers preserve
the locally reviewed top CPWG and solid reference planes, but cannot compel a
laminate or assembly service; the uploader echo is therefore mandatory.

The local fabrication package is READY for a prototype uploader review. This
is not permission to order, does not prove C429844 through-hole allocation,
and does not claim RF performance. Production remains HOLD until every path
and required off state passes the retained first-article VNA plan.

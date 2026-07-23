#!/usr/bin/env bash
# Test runner. Fast tier by default; --slow adds the e2e board rebuilds.
#
#   ./tests/run_tests.sh              # fast: T0 fixtures + T1 unit tests
#   ./tests/run_tests.sh --slow       # + e2e real-board regeneration
#   ./tests/run_tests.sh --only=fpid  # filter by test name (regex)
#   ./tests/run_tests.sh --net        # opt-in: the live-network tier
#
# Everything in the default tiers is hermetic: the network is mocked
# (jlc_twin drives a stub $EASYEDA2KICAD and a seeded per-code cache), and
# no sealed 04_kicad board, release, or project file is ever written.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KPY=/usr/bin/python3          # the interpreter with pcbnew

SLOW=0; NET=0; ARGS=()
for a in "$@"; do
  case "$a" in
    --slow) SLOW=1; ARGS+=("$a") ;;
    --net)  NET=1 ;;
    *)      ARGS+=("$a") ;;
  esac
done

if [ ! -x "$KPY" ]; then
  echo "FATAL: $KPY not found — the checkers need the KiCad-bundled python" >&2
  exit 2
fi
if ! "$KPY" -c 'import pcbnew' 2>/dev/null; then
  echo "FATAL: $KPY cannot import pcbnew" >&2
  exit 2
fi

# T1 suites, in rough dependency order (converter -> board -> checkers),
# then T4 — the regression corpus, one named test per incident this project
# has already paid for.
SUITES=(
  t1_converter.py
  t1_generate_board.py
  t1_audit.py
  t1_contracts.py
  t1_counting.py
  t1_escape_tier.py
  t1_rules_bom.py
  t1_bom_source.py
  t1_electrical_invariants.py
  t1_power_topology.py
  t1_release_git_dirty.py
  t1_status.py
  t1_jlc_twin.py
  t2_route_stitch.py
  t2_grind.py
  t4_regressions.py
)
[ "$SLOW" = 1 ] && SUITES+=(e2e_boards.py t3_acceptance.py)
[ "$NET" = 1 ] && SUITES+=(net_live.py)

rc=0; TP=0; TF=0; TK=0
declare -a SUMMARY
for s in "${SUITES[@]}"; do
  [ -f "$HERE/$s" ] || { echo "  (skipping missing $s)"; continue; }
  echo
  echo "=== $s ==="
  out="$("$KPY" "$HERE/$s" "${ARGS[@]+"${ARGS[@]}"}" 2>&1)"
  srh=$?
  echo "$out"
  [ $srh -ne 0 ] && rc=1
  line="$(printf '%s\n' "$out" | grep -E '^[[:space:]]+[0-9]+ passed' | tail -1)"
  p=$(printf '%s\n' "$line" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
  f=$(printf '%s\n' "$line" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
  k=$(printf '%s\n' "$out" | grep -oE '^[[:space:]]+[0-9]+ of those' \
        | grep -oE '[0-9]+' | tail -1 || echo 0)
  TP=$((TP + ${p:-0})); TF=$((TF + ${f:-0})); TK=$((TK + ${k:-0}))
  SUMMARY+=("$(printf '%-24s %-28s %s known-bad' "$s" "${line:-no result}" "${k:-0}")")
done

echo
echo "================ SUMMARY ================"
for l in "${SUMMARY[@]}"; do echo "  $l"; done
echo "  ----------------------------------------------------------------"
printf '  %-24s %d passed, %d failed, %d known-bad fixtures made their checker fail\n' \
       "TOTAL" "$TP" "$TF" "$TK"
echo
# A suite of only-clean tests proves nothing: a gate that cannot fail is
# worthless. Refuse to report success if no known-bad fixture ran.
if [ "$TK" -eq 0 ]; then
  echo "FAILED: no known-bad fixture ran — this run proved nothing about the gates"
  exit 1
fi
if [ $rc -eq 0 ]; then
  echo "ALL SUITES PASSED"
  [ "$SLOW" = 0 ] && echo "(fast tier — run with --slow for the e2e board rebuilds)"
else
  echo "FAILURES PRESENT"
fi
exit $rc

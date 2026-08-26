#!/usr/bin/env bash
# rebuild_all.sh — ADR-0007 multi-board DISPATCHER.
#
# cooksense is the repo's first project with >1 fabricated board (ADR-0007), so
# each board carries its own driver at 03_src/<board>/rebuild_all.sh. The shared
# M-REPRO gate + the standard "one command rebuilds the board" convention both
# look here at 03_src/rebuild_all.sh, so this thin dispatcher forwards to the
# per-board driver(s). The MAIN board (cooksense) is the critical path; the
# interposer (Board C) is coupon-gated / deferred (ADR-0007), so it is not built
# here yet — add its line when it is unblocked.
#
# Usage:  bash 03_src/rebuild_all.sh [--reuse-route]   (forwarded to cooksense)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/cooksense/rebuild_all.sh" "$@"

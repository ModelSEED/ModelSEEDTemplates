#!/bin/bash
# Launch the tmpl7-chain unit: stage a (draft-level scan, 4 workers) then stage b (the
# 200-genome gapfilled pass, 10 workers), body in validation/chain_tmpl7.sh.
# NOT run by the session that wrote it; the orchestrator launches it on a memory-aware
# schedule. Estimates and how they were made: validation/README.md, "Resources".
#
#   bash /home/freiburger/Documents/ModelSEEDTemplates-draftloops/validation/launch_tmpl7.sh
#
# Refuses to start if the unit already exists or MemAvailable is below MEMMAX_GB + 12
# (12 GB is the floor below which the GTDB-Tk job on this machine pauses itself); set
# TMPL7_FORCE=1 to skip the memory check.
set -eu
UNIT=tmpl7-chain
MEMMAX_GB=77
WT=/home/freiburger/Documents/ModelSEEDTemplates-draftloops
LOG=$WT/validation/logs/tmpl7_chain.log
mkdir -p "$WT/validation/logs"
if systemctl --user status "$UNIT.service" > /dev/null 2>&1; then
  echo "unit $UNIT already exists"; exit 1
fi
avail_gb=$(awk '/^MemAvailable:/ {printf "%d", $2 / 1048576}' /proc/meminfo)
need_gb=$((MEMMAX_GB + 12))
echo "MemAvailable ${avail_gb} GB; MemoryMax ${MEMMAX_GB} GB; need ${need_gb} GB"
if [ "$avail_gb" -lt "$need_gb" ] && [ "${TMPL7_FORCE:-0}" != 1 ]; then
  echo "not enough memory available; not launching"; exit 1
fi
[ -e "$LOG" ] && mv "$LOG" "$LOG.$(date +%Y%m%d-%H%M%S)"
systemd-run --user --unit=$UNIT --collect -p MemoryMax=${MEMMAX_GB}G -p MemorySwapMax=0 \
  -p WorkingDirectory=/home/freiburger/Documents/prFBA/region_validation/shared_reference \
  -E PYTHONPATH=/home/freiburger/Documents/ModelSEEDpy-c2e31a0 \
  /bin/bash -c "$WT/validation/chain_tmpl7.sh > $LOG 2>&1; echo EXIT=\$? >> $LOG"
echo "launched $UNIT; log $LOG"

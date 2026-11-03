#!/bin/bash
# The tmpl7-chain unit's body (launched by validation/launch_tmpl7.sh; do not run by hand
# outside a systemd unit). Stage a, the draft-level scan, then stage b, the 200-genome
# gapfilled pass, both through prFBA's harness, on this branch's templates; then the cheap
# summaries. A failure in stage a does not skip stage b; the chain exits non-zero if any
# step failed.
#
# Expects (set by the unit): working directory
# /home/freiburger/Documents/prFBA/region_validation/shared_reference and
# PYTHONPATH=/home/freiburger/Documents/ModelSEEDpy-c2e31a0. TMPL7_PRECHECK_ONLY=1 runs the
# pre-checks alone and exits.
set -u
WT=/home/freiburger/Documents/ModelSEEDTemplates-draftloops
V=$WT/validation
SR=/home/freiburger/Documents/prFBA/region_validation/shared_reference
D=$SR/data
TNEW=$WT/templates/v7.0
TOLD=/home/freiburger/Documents/ModelSEEDTemplates-c12run/templates/v7.0     # 21a8084
TEMPLATE_COMMIT=7fd1ab19a866ce0f85a8a192773cbfb2bc00175f
PY="/home/freiburger/Documents/py_venv/bin/python -W ignore::SyntaxWarning"
IN="--cells $D/cells.csv.gz --fold-plan $D/fold_plan.json --panel $D/panel_eligible.json --prfba $D/prfba --picrust2 $D/picrust2"
cd "$SR" || exit 2
mkdir -p "$V/scan" "$V/gf_pass" "$V/logs"
echo "[chain] start $(date -Is) on $(hostname); PYTHONPATH=${PYTHONPATH:-}"

# ---- pre-checks: what runs is what PROVENANCE.md records -------------------------------
fail=0
[ "$(pwd)" = "$SR" ] || { echo "[chain] wrong working directory $(pwd)"; exit 2; }
[ "${PYTHONPATH:-}" = /home/freiburger/Documents/ModelSEEDpy-c2e31a0 ] || {
  echo "[chain] PYTHONPATH must be the c2e31a0 pin"; exit 2; }
git -C "$WT" diff --quiet "$TEMPLATE_COMMIT" -- templates/ || {
  echo "[chain] templates/ differ from $TEMPLATE_COMMIT (working tree or HEAD)"; exit 2; }
[ "$(git -C "$WT" rev-parse "HEAD:templates")" = "$(git -C "$WT" rev-parse "$TEMPLATE_COMMIT:templates")" ] || {
  echo "[chain] templates/ at HEAD differ from $TEMPLATE_COMMIT"; exit 2; }
[ "$(git -C /home/freiburger/Documents/ModelSEEDTemplates-c12run rev-parse HEAD)" = 21a808428560c1e3e11e304512d0baab6616ab78 ] \
  && git -C /home/freiburger/Documents/ModelSEEDTemplates-c12run diff --quiet -- templates/ || {
  echo "[chain] ModelSEEDTemplates-c12run is not a clean 21a8084"; exit 2; }
$PY "$V/apply_draft_loop_fix.py" --check > "$V/logs/precheck_templates.json" || {
  echo "[chain] apply_draft_loop_fix.py --check failed"; exit 2; }
sha256sum -c --quiet "$V/harness.sha256" || {
  if [ "${TMPL7_ALLOW_HARNESS_DRIFT:-0}" = 1 ]; then
    echo "[chain] WARNING harness files differ from validation/harness.sha256 (allowed by TMPL7_ALLOW_HARNESS_DRIFT=1)"
  else
    echo "[chain] harness files differ from validation/harness.sha256; update PROVENANCE.md or set TMPL7_ALLOW_HARNESS_DRIFT=1"; exit 2
  fi; }
echo "[chain] prFBA HEAD $(git -C /home/freiburger/Documents/prFBA rev-parse HEAD); templates HEAD $(git -C "$WT" rev-parse HEAD)"
grep -E "MemAvailable|MemTotal" /proc/meminfo
if [ "${TMPL7_PRECHECK_ONLY:-0}" = 1 ]; then echo "[chain] pre-checks passed (TMPL7_PRECHECK_ONLY=1)"; exit 0; fi

rc_a=0  # resume after the OOM kill at 22:54 on 10-29: stage a had already finished (exit 0)
# ---- stage b: 200-genome gapfilled pass, as amendment A-C13 but on the new templates ---
echo "[chain] stage b start $(date -Is)"
grep MemAvailable /proc/meminfo
$PY scripts/phenotype_fold.py $IN --templates "$TNEW" --integrate-reversals \
    --expect-modelseedpy c2e31a0 --outdir "$V/gf_pass" \
    --summary "$V/gf_pass/phenotype_summary.json" --n-genomes 200 \
    --readouts atp,growth,essentiality,structure --workers 10 --maxtasksperchild 3 \
    >> "$V/logs/stage_b_gf_pass.log" 2>&1
rc_b=$?
echo "[chain] stage b exit $rc_b $(date -Is)"
if [ $rc_b -eq 0 ]; then
  $PY "$V/compare_gf_to_c13.py" --after "$V/gf_pass/per_genome.jsonl" \
      --out "$V/gf_pass/compare_vs_c13.json" > "$V/logs/stage_b_compare.log" 2>&1 || fail=1
  # prFBA's own before/after report, as A-C13 used it (c13_finish.sh)
  $PY scripts/c12_compare.py --before "$D/phenotype_gf_c13/per_genome.jsonl" \
      --after "$V/gf_pass/per_genome.jsonl" --out "$V/gf_pass/c12_compare_vs_c13.json" \
      > "$V/logs/stage_b_c12_compare.log" 2>&1 || fail=1
else
  fail=1
fi
echo "[chain] done $(date -Is): stage a $rc_a, stage b $rc_b, post-steps failed: $fail"
[ $rc_a -eq 0 ] && [ $rc_b -eq 0 ] && [ $fail -eq 0 ]

# shared intro of every job script: the environment, a dated start line, and on exit one dated PASS or FAIL line with the
# duration in logs/chain_<date>.log, the record of the whole chain (STAGE and REFERENCE are set by the job script before sourcing).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
source env/paths.sh
STAGE_T0=$(date +%s)
STAGE_DATE=$(date +%Y-%m-%d)
CHAIN_LOG="logs/chain_$(date +%Y%m%d).log"
mkdir -p logs "$COS_ROOT/logs"
echo "$STAGE_DATE  ${STAGE:-job} starting: job ${SLURM_JOB_ID:-local} on $(hostname); root $COS_ROOT; python $(which python); cpus ${SLURM_CPUS_PER_TASK:-?} mem ${SLURM_MEM_PER_NODE:-?} MB"
nvidia-smi --query-gpu=name,memory.total --format=csv 2>/dev/null || true
stage_finish() {
  local code=$?
  local secs=$(( $(date +%s) - STAGE_T0 ))
  local st=PASS; [ "$code" -eq 0 ] || st=FAIL
  local line
  line=$(printf '%s  %-4s  %-9s %s: %d min %d s, job %s, %s cpus%s  (%d s)' "$STAGE_DATE" "$st" "${STAGE_ID:-JOB}" "${STAGE:-job}" $((secs / 60)) $((secs % 60)) "${SLURM_JOB_ID:-local}" "${SLURM_CPUS_PER_TASK:-?}" "${REFERENCE:+; reference in the document: $REFERENCE}" "$secs")
  echo "$line"
  echo "$line" >> "$CHAIN_LOG"
  exit "$code"
}
trap stage_finish EXIT

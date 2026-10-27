# shared intro of every job script
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
source env/paths.sh
echo "job ${SLURM_JOB_ID:-local} on $(hostname) at $(date); root $COS_ROOT; python $(which python); cpus ${SLURM_CPUS_PER_TASK:-?} mem ${SLURM_MEM_PER_NODE:-?} MB"
nvidia-smi --query-gpu=name,memory.total --format=csv 2>/dev/null || true

# Source this first in every shell & job on the supercomputer: source env/paths.sh
# Root is the project folder on the shared file system; replace the placeholder with its path.
export COS_ROOT=${COS_ROOT:-"[redacted project path]"}
export HF_HOME=$COS_ROOT/hf_cache
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 # compute nodes (no internet)
export TOKENIZERS_PARALLELISM=false
export PYTHONNOUSERSITE=1 # ignore ~/.local packages
export PYTHONUTF8=1 # every text file is UTF-8 
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
if [ -n "${JOBFS:-}" ]; then export TMPDIR=$JOBFS; fi
if [ -f "$COS_ROOT/venv/PYMOD" ] && command -v module >/dev/null 2>&1; then module load $(cat "$COS_ROOT/venv/PYMOD") 2>/dev/null || true; fi
if [ -f "$COS_ROOT/venv/bin/activate" ]; then source "$COS_ROOT/venv/bin/activate"; fi

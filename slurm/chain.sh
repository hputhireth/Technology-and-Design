#!/bin/bash
# The whole chain from scratch, submitted with afterok dependencies: prepare on the login node, then encode (GPU), the two heads,
# the adaptations, the linear and word controls, and last the integration test, which never runs on a partial tree.
#     source env/paths.sh && bash slurm/chain.sh
# Before it: bash tests/run_local.sh (the unit suite and the smoke chain on the login node).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/paths.sh
mkdir -p logs "$COS_ROOT/logs"
DATE=$(date +%Y-%m-%d)
CHAIN_LOG="logs/chain_$(date +%Y%m%d).log"
{
echo "chain log, $DATE"
echo "python $(python -c 'import sys; print(sys.version.split()[0])'), torch $(python -c 'import torch; print(torch.__version__)')"
echo "reference: encode 7 min 47 s; FinGPT head 1 h 17 min; dialogue head 2 h 22 min; adaptations 9 min 19 s; linear 6.3 and 27.6 min; words 6.5 + 0.6 + 17.9 min; integration 7.1 s"
printf -- '-%.0s' $(seq 1 100); echo
} >> "$CHAIN_LOG"
T0=$(date +%s)
python scripts/prepare.py --config finance
python scripts/prepare.py --config dialogue
printf '%s  PASS  CH-01     prepare finance and dialogue: %d s on the login node; reference in the document: seconds  (%d s)\n' "$DATE" $(( $(date +%s) - T0 )) $(( $(date +%s) - T0 )) | tee -a "$CHAIN_LOG"
E=$(sbatch --parsable slurm/encode.sh)
TF=$(sbatch --parsable --dependency=afterok:$E slurm/train.sh finance)
TD=$(sbatch --parsable --dependency=afterok:$E slurm/train.sh dialogue)
A=$(sbatch --parsable --dependency=afterok:$TF:$TD slurm/adapt.sh)
L=$(sbatch --parsable --dependency=afterok:$TF:$TD slurm/linear.sh)
W=$(sbatch --parsable --dependency=afterok:$TF:$TD slurm/words.sh)
I=$(sbatch --parsable --dependency=afterok:$A:$L:$W slurm/integration_test.sh)
echo "submitted: encode $E; train finance $TF, dialogue $TD; adapt $A; linear $L; words $W; integration test $I (afterok on all of them)" | tee -a "$CHAIN_LOG"
echo "watch with: squeue -u \$USER; the chain's record is $CHAIN_LOG, each job's own output logs/<stage>_<jobid>.txt, the test logs logs/<stage>_<date>.log"

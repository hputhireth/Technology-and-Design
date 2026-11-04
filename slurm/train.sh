#!/bin/bash
#SBATCH --job-name=train
#SBATCH --output=logs/train_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=16 --mem=16G --time=03:00:00
##SBATCH --account=[redacted account]
# The head of one config on the cached features: confirmation split, grouped folds x seeds, the final fit, calibration,
# the confirmation score, then its predictions on every prediction set.
#     sbatch slurm/train.sh finance
#     sbatch slurm/train.sh dialogue
# The config is the first argument (an environment variable is not carried into a job on every cluster).
C="${1:-${CONFIG:-finance}}"
if [ "$C" = finance ]; then STAGE_ID="CH-03" REFERENCE="1 h 17 min and 2.4 GB for the FinGPT head's job"; else STAGE_ID="CH-04" REFERENCE="2 h 22 min and 3.8 GB for the dialogue head's job"; fi
STAGE="train $C"
source slurm/_header.sh
python scripts/train.py --config "$C"
python scripts/predict.py --config "$C"

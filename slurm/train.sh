#!/bin/bash
#SBATCH --job-name=train
#SBATCH --output=logs/train_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=16 --mem=16G --time=02:00:00
##SBATCH --account=[redacted account]
# The head of one config on the cached features: confirmation split, grouped folds x seeds, the final
# fit, calibration, the confirmation score. Then its predictions on every prediction set.
#     CONFIG=finance sbatch slurm/train.sh
#     CONFIG=dialogue sbatch slurm/train.sh
source slurm/_header.sh
python scripts/train.py --config "${CONFIG:-finance}"
python scripts/predict.py --config "${CONFIG:-finance}"

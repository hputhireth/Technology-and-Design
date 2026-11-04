#!/bin/bash
#SBATCH --job-name=predict
#SBATCH --output=logs/predict_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=4 --mem=32G --time=02:00:00
#SBATCH --gres=gpu:1
##SBATCH --account=[redacted account]
# New files to predict: put them under data/raw/predict/, then this job prepares the tables, encodes what is not cached yet (GPU)
# and writes the predictions of the trained head.
#     sbatch slurm/predict.sh finance
C="${1:-${CONFIG:-finance}}"
STAGE="predict $C" STAGE_ID="CH-P" REFERENCE="minutes"
source slurm/_header.sh
python scripts/prepare.py --config "$C"
python scripts/encode.py --config "$C"
python scripts/predict.py --config "$C"

#!/bin/bash
#SBATCH --job-name=linear
#SBATCH --output=logs/linear_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=16 --mem=16G --time=04:00:00
##SBATCH --account=[redacted account]
# The two linear controls on the networks' own folds and confirmation rows. Needs results/<config>/train/ for both configs.
STAGE="linear" STAGE_ID="CH-06" REFERENCE="6.3 min (FinGPT) and 27.6 min (dialogue, both readings)"
source slurm/_header.sh
python scripts/linear.py --config finance
python scripts/linear.py --config dialogue

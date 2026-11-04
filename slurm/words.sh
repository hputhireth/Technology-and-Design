#!/bin/bash
#SBATCH --job-name=words
#SBATCH --output=logs/words_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=8 --mem=16G --time=02:00:00
##SBATCH --account=[redacted account]
# The three word logits: FinGPT on the network's split, SEntFiN on its own split, the dialogue emotions on the network's split.
STAGE="words" STAGE_ID="CH-07" REFERENCE="6.5 min (FinGPT), 0.6 min (SEntFiN), 17.9 min (dialogue)"
source slurm/_header.sh
python scripts/words.py --config finance --set train
python scripts/words.py --config finance --set sentfin
python scripts/words.py --config dialogue --set train --reading emotion

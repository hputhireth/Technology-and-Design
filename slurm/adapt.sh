#!/bin/bash
#SBATCH --job-name=adapt
#SBATCH --output=logs/adapt_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=8 --mem=16G --time=01:00:00
##SBATCH --account=[redacted account]
# The three adaptations:
#   the finance head on half of SEntFiN (the other half held out; FinGPT's confirmation rows score retention)
#   the dialogue head on FinGPT's development texts (its confirmation rows held out; SEntFiN scored as transfer)
#   that adapted dialogue head on half of SEntFiN (FinGPT's confirmation rows scored as transfer)
# Needs results/<config>/train/nn_model.json for both configs and the finance feature cache.
source slurm/_header.sh
python scripts/adapt.py --config finance  --adapt-set sentfin
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set train   --transfer-set sentfin --run finance_train
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set sentfin --transfer-set train \
       --model "$COS_ROOT/results/dialogue/adapt/finance_train/nn_model.json" --run finance_train_then_sentfin

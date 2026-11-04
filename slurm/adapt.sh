#!/bin/bash
#SBATCH --job-name=adapt
#SBATCH --output=logs/adapt_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=8 --mem=16G --time=01:30:00
##SBATCH --account=[redacted account]
# The adaptations, in the order the document names them. Needs results/<config>/train/nn_model.json for both configs and the finance cache.
#   FinGPT Network + SEntFiN: the closed form on all rows, the closed form on the misread rows only, GRPO on all rows
#     (half of SEntFiN held out by group; FinGPT's confirmation rows score retention)
#   Dialogue Network + FinGPT: the closed form (for the record) and GRPO (the shipped stage 1), on FinGPT's development texts,
#     its confirmation rows held out, SEntFiN scored as transfer
#   Dialogue Network + FinGPT + SEntFiN: the GRPO head taken on to half of SEntFiN, closed form on all rows, on the misread rows only, and GRPO
STAGE="adapt" STAGE_ID="CH-05" REFERENCE="9 min 19 s for 22 runs"
source slurm/_header.sh
python scripts/adapt.py --config finance --adapt-set sentfin
python scripts/adapt.py --config finance --adapt-set sentfin --rows wrong
python scripts/adapt.py --config finance --adapt-set sentfin --method grpo
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set train --transfer-set sentfin --run finance_train
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set train --transfer-set sentfin --method grpo --run finance_train_grpo
G="$COS_ROOT/results/dialogue/adapt/finance_train_grpo/nn_model.json"
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set sentfin --transfer-set train --model "$G" --run finance_train_then_sentfin
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set sentfin --transfer-set train --model "$G" --rows wrong --run finance_train_then_sentfin_mistakes
python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set sentfin --transfer-set train --model "$G" --method grpo --run finance_train_then_sentfin_grpo

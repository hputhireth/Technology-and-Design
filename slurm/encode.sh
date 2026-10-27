#!/bin/bash
#SBATCH --job-name=encode
#SBATCH --output=logs/encode_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=4 --mem=32G --time=02:00:00
#SBATCH --gres=gpu:1
##SBATCH --account=[redacted account]
# The encoder pass over every prepared table of both configs.
# Features go to the cache and are never recomputed. 
# Needs scripts/prepare.py to have run.
# for 30,209 finance texts, 64,566 dialogue windows and 10,686 headlines.
#     sbatch slurm/encode.sh # both configs
#     CONFIG=finance sbatch slurm/encode.sh # one config
source slurm/_header.sh
python -c "import torch; assert torch.cuda.is_available(), 'no GPU visible in the GPU job: check --gres and the partition'"
for c in ${CONFIG:-finance dialogue}; do python scripts/encode.py --config "$c"; done

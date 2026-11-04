#!/bin/bash
#SBATCH --job-name=encode
#SBATCH --output=logs/encode_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=4 --mem=32G --time=02:00:00
#SBATCH --gres=gpu:1
##SBATCH --account=[redacted account]
# The encoder pass over every prepared table of both configs: 30,209 FinGPT texts, 64,566 dialogue windows and 10,686 headlines,
# fp16 on one GPU. Features go to the cache and are never recomputed. Needs scripts/prepare.py to have run.
#     sbatch slurm/encode.sh                 # both configs
#     sbatch slurm/encode.sh finance         # one config
STAGE="encode" STAGE_ID="CH-02" REFERENCE="1.8 + 3.9 + 0.4 min of encoding, 7 min 47 s for the job"
source slurm/_header.sh
python -c "import torch; assert torch.cuda.is_available(), 'no GPU visible in the GPU job: check --gres and the partition'"
for c in ${1:-${CONFIG:-finance dialogue}}; do python scripts/encode.py --config "$c"; done

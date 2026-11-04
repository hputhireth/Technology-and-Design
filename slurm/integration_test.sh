#!/bin/bash
#SBATCH --job-name=integration
#SBATCH --output=logs/integration_%j.txt
#SBATCH --ntasks=1 --cpus-per-task=4 --mem=16G --time=00:30:00
##SBATCH --account=[redacted account]
# The last job of the chain: the 154 checks over every model's files, the document's bounds applied, then the five seeded faults
# on a copy of the tree to prove the checker still catches them. Its exit status is the test's.
#     sbatch --dependency=afterok:<adapt>:<linear>:<words> slurm/integration_test.sh
STAGE="integration test" STAGE_ID="CH-08" REFERENCE="154 checks in 7.1 s; the mutation run 8 FAIL lines, exit 1"
source slurm/_header.sh
python tests/integration/check_results.py
python tests/integration/mutate.py --out "$COS_ROOT/mutants"
set +e
python tests/integration/check_results.py --results "$COS_ROOT/mutants" --stage mutation
code=$?
set -e
n=$(awk '/^mutation log, /{c=0} /  FAIL  IT-/{c++} END{print c+0}' "logs/mutation_$(date +%Y%m%d).log")   # the last run in the day's log
echo "mutation run: exit $code with $n FAIL lines (expected exit 1 with 8)"
[ "$code" -eq 1 ] && [ "$n" -eq 8 ]

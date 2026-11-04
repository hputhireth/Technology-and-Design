# sentiment_heads
Sentiment and emotion classifiers built as small neural heads on the frozen output of a BERT model encoder,
trained and evaluated on a supercomputer, then adapted to a new corpus without losing what they already read well.
This repository only holds the pathway that gave the best results.

Replace `[redacted login detail]`, `[redacted project path]` and `[redacted account]` with your login, the project folder
and the allocation account of your supercomputer before running anything.

## The pathway

1. **Prepare.** 
2. **Encode once, frozen.** 
3. **Confirmation split first.** 
4. **The head.** 
5. **Train.** 
6. **Calibrate.**
7. **Score.** 
8. **Adapt.**
9. **Two controls on the same rows.** 

## Layout

```
configs/finance.json     the finance head: files, labels, the head, the protocol, the adaptation settings
configs/dialogue.json    the dialogue head: two readings (sentiment, emotion), grouping by conversation
common/paths.py          the folder layout under root $COS_ROOT
common/text.py           cleaning, label normalisation, duplicate keys, groups, grouped splits
common/cache.py          the content-hash feature cache
common/encoder.py        offline loading of the encoder, pooling, the windowed forward pass
common/head.py           the head, standardisation, the training loop, inference, the JSON form
common/metrics.py        accuracy, macro-F1, log-loss, AUC, confusion, the bootstrap, the corrected t-test, the temperature
common/sets.py           a prepared table with its cached features and its labels
common/runlog.py         the dated PASS/FAIL log the test layers and the chain write
scripts/prepare.py       step 1 (login node, seconds)
scripts/encode.py        step 2 (GPU job)
scripts/train.py         steps 3 to 7 (CPU job)
scripts/predict.py       a trained head on the prediction sets (CPU, seconds)
scripts/adapt.py         step 8, closed form or GRPO, all rows or the misread rows (CPU, minutes)
scripts/linear.py        the linear control on the network's folds and confirmation rows (CPU)
scripts/words.py         the word logit of one corpus with its trigger words (CPU)
slurm/                   the job scripts with their allocations: encode.sh, train.sh, predict.sh, adapt.sh, linear.sh, words.sh,
                         integration_test.sh; chain.sh submits them all with afterok dependencies
env/paths.sh             environment variables sourced by every shell and job; env/setup.sh builds the venv once
```
The test layers (the unit suite, the smoke chain on synthetic data, the integration checker the last job of the chain runs,
and the mutation run that proves it) and the logs of the run that produced the numbers below follow in the next update,
under `tests/` and `logs/`.

Everything under root `$COS_ROOT` on the supercomputer:

```
hf_cache/                       encoder weights and tokenizer (downloaded once on login)
data/raw/                       fs_train.csv, empathetic_training.csv, predict/sentfin.csv
data/cache/<config>/            prepared tables: id, text, one column per reading, group, source_row
features/<key>/                 pooled.npy (fp16), ids.csv, manifest.json
results/<config>/train/         nn_model.json, summary.json, cv_runs.csv, folds.csv, confirmation_ids.csv, confusion_<reading>.csv
results/<config>/<set>/         predictions.csv, metrics.json, confusion_<reading>.csv
results/<config>/adapt/<run>/   nn_model.json, summary.json, adapt_log.csv, predictions_<set>.csv, weight_changes.csv
results/<config>/linear/        linear_model.json, summary.json, cv_runs.csv, folds.csv, confirmation_ids.csv, <set>/predictions.csv
results/<config>/words/<set>/   words_model.json, summary.json, cv_runs.csv, trigger_words.csv, confirmation_ids.csv, folds.csv
results/integration_report.txt  the last job's verdict: 154 checks, PASS or FAIL per check, exit status
logs/                           one file per job with the timings and the peak memory, and the dated chain log
```

The result folders and the fourteen models of the design document:

| Model in the document | Folder under results/ |
|---|---|
| FinGPT Network | finance/train |
| FinGPT Network + SEntFiN, all rows / mistakes only / GRPO | finance/adapt/finance_sentfin, finance_sentfin_mistakes, finance_sentfin_grpo |
| Dialogue Network | dialogue/train |
| Dialogue Network + FinGPT (GRPO, the shipped stage 1; the closed form is kept beside it) | dialogue/adapt/finance_train_grpo (finance_train) |
| Dialogue Network + FinGPT + SEntFiN, all rows / mistakes only / GRPO | dialogue/adapt/finance_train_then_sentfin, ..._mistakes, ..._grpo |
| FinGPT Linear, Dialogue Linear | finance/linear, dialogue/linear |
| Word Logit, FinGPT / SEntFiN / Dialogue | finance/words/train, finance/words/sentfin, dialogue/words/train |

## How to run

```
ssh [redacted login detail]
cd [redacted project path]/sentiment_heads
module load <python module>
source env/paths.sh && bash env/setup.sh
```
Then, from the repository folder, the whole chain:
```
source env/paths.sh
bash slurm/chain.sh   
dependencies
```


```
python scripts/prepare.py --config finance
python scripts/prepare.py --config dialogue
sbatch slurm/encode.sh
sbatch slurm/train.sh finance
sbatch slurm/train.sh dialogue
sbatch slurm/adapt.sh
sbatch slurm/linear.sh
sbatch slurm/words.sh
sbatch slurm/integration_test.sh
```


## Requirements

Python 3.10 or later (3.11 was used) with the packages in `requirements.txt` (PyTorch, transformers, scikit-learn,
scipy, numpy, pandas, pytest for the unit suite). The encoder is `BAAI/bge-large-en-v1.5` from the Hugging Face hub, 1.3 GB,
fetched once by `env/setup.sh`.

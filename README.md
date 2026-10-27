# sentiment_heads
Sentiment and emotion classifiers built as small neural heads on the frozen output of a BERT model encoder, 
trained and evaluated on a supercomputer, then adapted to a new corpus without losing what they already read well. 
This repository only holds the best pathway that gave the best results (the alternatives it was chosen over are listed at the end).

Replace `[redacted login detail]`, `[redacted project path]` and `[redacted account]` with the login, the project folder 
and the allocation account of your supercomputer before running anything.

## The pathway

1. **Prepare.** Clean the text, put the labels on their configured names, fold exact duplicates of
   the training set, and give every row a group (groups never mount a split).
2. **Encode once, frozen.** bge-large-en-v1.5 (24 transformer layers, 335 million weights) reads
   every text in fp16 on one GPU; the [CLS] vector joined with the masked mean over tokens gives
   2,048 numbers per text. Texts longer than a 512-token window are read in overlapping windows and
   averaged. The output is cached under a content hash and never recomputed.
3. **Confirmation split first.** 15% of the training rows are held out by group before anything is
   fitted and scored once, at the end.
4. **The head.** Standardised features into a trunk of fully connected layers with one output layer
   per reading. Finance: 2048 > 256 leaky ReLU > 128 tanh > 3, 557,827 weights, dropout 0.3, input
   dropout 0.2, weight decay 0.01. Dialogue: 2048 > 256 ReLU > 128 SiLU > 32 ELU > [3 | 32], one
   trunk and two output layers (sentiment and emotion), 562,723 weights, weight decay 0.05.
5. **Train.** AdamW, batch 256, cosine decay to a tenth of the rate, moving average of the weights, 
   cross-entropy with label smoothing 0.05 (finance), early stopping on the validation cross-entropy. 
   Grouped 5-fold cross-validation with 3 seeds measures the scores and picks the number of epochs 
   (the median best epoch). The head is then fitted once on every development row.
6. **Calibrate.** One temperature per reading, fitted on the out-of-fold logits.
7. **Score.** Accuracy, macro-F1 with a bootstrap interval, log-loss, one-vs-rest AUC and confusion matrix
   (consistent on every prediction set).
8. **Adapt.** To move a head to a new corpus: the closed form of the leashed objective. On every
   labelled row of the new corpus the target is the starting head's distribution tilted towards the
   label, `softmax(log pi_ref + onehot(y) / beta)`, beta 0.3, fitted by cross-entropy; a retention
   term, the forward KL of every reading on the head's own training rows, holds its old readings.
   Half of the new corpus is held out by group and scored before and after, with the old corpus
   and the home rows.

## Layout

```
configs/finance.json     the finance head: files, labels, the head, the protocol, the adaptation settings
configs/dialogue.json    the dialogue head: two readings (sentiment, emotion), grouping by conversation
common/paths.py          the folder layout under root $COS_ROOT
common/text.py           cleaning, label normalisation, duplicate keys, groups, grouped splits
common/cache.py          the content-hash feature cache
common/encoder.py        offline loading of the encoder, pooling, the windowed forward pass
common/head.py           the head, standardisation, the training loop, inference, the JSON form
common/metrics.py        accuracy, macro-F1, log-loss, AUC, confusion... etc
common/sets.py           a prepared table with its cached features and its labels
scripts/prepare.py       step 1 (login node, seconds)
scripts/encode.py        step 2 (GPU job)
scripts/train.py         steps 3 to 7 (CPU job)
scripts/predict.py       a trained head on the prediction sets (CPU, seconds)
scripts/adapt.py         step 8 (CPU, seconds to minutes)
slurm/                   the job scripts with their allocations: encode.sh, train.sh, predict.sh, adapt.sh
env/paths.sh             environment variables sourced by every shell and job; env/setup.sh builds the venv once
tests/smoke.sh           the whole chain on synthetic data with a tiny random encoder, CPU, a few minutes
```
Everything under root file `$COS_ROOT` on the supercomputer:

```
hf_cache/                       encoder weights and tokenizer (downloaded once on login)
data/raw/                       fs_train.csv, empathetic_training.csv, predict/sentfin.csv
data/cache/<config>/            prepared tables: id, text, one column per reading, group, source_row
features/<key>/                 pooled.npy (fp16), ids.csv, manifest.json
results/<config>/train/         nn_model.json, summary.json, cv_runs.csv, confirmation_ids.csv, confusion_<reading>.csv
results/<config>/<set>/         predictions.csv, metrics.json, confusion_<reading>.csv
results/<config>/adapt/<run>/   nn_model.json, summary.json, adapt_log.csv, predictions_<set>.csv, weight_changes.csv
logs/                           one file per job, with the timings and the peak memory of each step
```

## How to run

Once, on a login node:

```
ssh [redacted login detail]
cd [redacted project path]/sentiment_heads
source env/paths.sh && bash env/setup.sh
```
Then, from the repository folder:
```
source env/paths.sh
python scripts/prepare.py --config finance
python scripts/prepare.py --config dialogue
sbatch slurm/encode.sh
CONFIG=finance  sbatch slurm/train.sh
CONFIG=dialogue sbatch slurm/train.sh
sbatch slurm/adapt.sh
```

New files to predict go under `data/raw/predict/`.
`CONFIG=finance sbatch slurm/predict.sh` prepares, encodes what is not cached and writes
the predictions.

Every script prints what it did with timings; the job scripts record the node, the allocation and
the peak memory, and the scheduler's report closes each log.

## Data
| Corpus | Rows | Used | Labels |
|---|---|---|---|
| FinGPT sentiment training set | 76,772 | 30,209 distinct texts after folding duplicates | nine shades mapped to negative / neutral / positive |
| EmpatheticDialogues windows | 64,591 | 64,566 | the sentiment read by the finance head, and the speaker's emotion (32 classes) |
| SEntFiN 1.0 | 10,686 headlines | 10,532 labelled | human consensus per headline |

The two training files are `data/raw/fs_train.csv` (columns `sentiment, text`) and
`data/raw/empathetic_training.csv` (`text, emotion, sentiment`, in conversation order, with a
`conv_id` column when available); `data/raw/predict/sentfin.csv` (`text, sentiment`) is the
external test of both heads.

## What this pathway produced

| Head | Cross-validated | Confirmation split | External test (SEntFiN, zero-shot) |
|---|---|---|---|
| finance | 0.8044 +/- 0.0058 over 15 runs | 0.798 [0.786, 0.809], accuracy 79.8%, ECE 0.009 | accuracy 73.5%, macro-F1 0.741 |
| dialogue, sentiment | 0.8555 +/- 0.0068 | 0.865 [0.852, 0.877], accuracy 94.75% | accuracy 74.5%, macro-F1 0.738 |
| dialogue, emotion | 0.3723 +/- 0.0051 (32 classes) | 0.364 [0.354, 0.374], accuracy 37.1% | no label |

| Adaptation with the closed form (beta 0.3, retention 1, all labelled rows) | New corpus, held-out half (accuracy) | Old corpus (accuracy) |
|---|---|---|
| finance head on SEntFiN | 73.5% to 81.9% | FinGPT confirmation rows 79.8% to 79.7% |
| finance head on its misread SEntFiN rows only | 73.5% to 80.9% | 79.8% to 79.7% |

The dialogue head's adaptation to FinGPT was measured with GRPO (71.6% to 78.6% on FinGPT's
confirmation rows, SEntFiN 74.5% to 74.6%, dialogue agreement 94.75% to 94.4%, emotion macro-F1
0.364 to 0.360) and with the closed form at beta 1 (72.9%). 

Timings on the supercomputer: encoding 30,209 texts in 1.8 min on one GPU (64,566 windows in
3.9 min). one cross-validation run of the finance head in about a few minutes on 16 cores, so the
15 runs and the final fit take about 10 minutes (the search over 34 configurations that chose this
one took an hour) an adaptation in a few minutes.

## Not recommended

| Alternative | Why it is not here |
|---|---|
| fine-tuning the encoder | 335 million weights per experiment computationally expensive and destablise the information structure of the transformer |
| prior corrections of the predictions (EM, BBSE, balanced) | 0.643 / 0.669 / 0.734 against 0.735 uncorrected on SEntFiN |
| sampled policy gradients (REINFORCE, GRPO, PPO) and a Q layer for the adaptation | tie with the closed form when every label is known. GRPO gained 1.6 points on the new corpus for 2.6 lost on the old, while the Q layer forgot most |

## Requirements

Python 3.10 or later with the packages in `requirements.txt` (PyTorch, transformers, scikit-learn,
scipy, numpy, pandas). The encoder is `BAAI/bge-large-en-v1.5` from the Hugging Face hub, 1.3 GB,
fetched once by `env/setup.sh`.

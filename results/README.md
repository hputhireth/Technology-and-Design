# results

The result files of the chain of 3 November 2026 (sentiment_heads), as the integration test passed them: 154 checks,
0 FAIL. Every path inside the files is relative to the project root.

| Folder | Holds |
|---|---|
| `finance/train/`, `dialogue/train/` | the two trained networks: `nn_model.json` (mean, sd, trunk, outputs, temperatures), `summary.json` (cross-validation, calibration, confirmation), `cv_runs.csv`, `folds.csv`, `confirmation_ids.csv`, `confusion_<reading>.csv` |
| `finance/sentfin/`, `dialogue/sentfin/` | the zero-shot readings of the 10,686 SEntFiN headlines: `predictions.csv`, `metrics.json`, `confusion_sentiment.csv` |
| `finance/adapt/<run>/` | FinGPT Network + SEntFiN: `finance_sentfin` (closed form, all rows), `finance_sentfin_mistakes` (closed form, misread rows), `finance_sentfin_grpo` (GRPO) and its seeds `_s1`, `_s2`; each with `nn_model.json`, `summary.json` (before and after on every corpus, KL, entropy, repaired and kept shares), `adapt_log.csv` (one row per epoch), `predictions_sentfin.csv` (every row before and after), `weight_changes.csv` |
| `dialogue/adapt/<run>/` | Dialogue Network + FinGPT: `finance_train` (closed form, kept for the record), `finance_train_grpo` (the shipped stage 1) and its seeds; the chained head on SEntFiN: `finance_train_then_sentfin`, `..._mistakes`, `..._grpo` |
| `finance/linear/`, `dialogue/linear/` | the linear control: `linear_model.json`, `summary.json` (with the corrected resampled t-test against the network), `cv_runs.csv`, `folds.csv`, `confirmation_ids.csv`, `sentfin/predictions.csv` |
| `finance/words/train/`, `finance/words/sentfin/`, `dialogue/words/train/` | the word logit: `words_model.json`, `trigger_words.csv`, `summary.json`, `cv_runs.csv`, `confusion.csv`, `folds.csv`, `confirmation_ids.csv`, the zero-shot `sentfin/predictions.csv` of the FinGPT model |
| `integration_report.txt` | the 154 checks of the last job, one dated PASS line each |
| `fd/train/nn/`, `ed/train/nn/` | the research pipeline's search records that chose the two configurations: `nn_selected.json` (the 34 configurations and the paired tests), `nn_confirmation.json`, `nn_folds.csv`; for the finance head also the inspection (`inside_summary.json`, `inside_control.json`: random-label control, Hessian, connectivity, probes) |

Where each number of the design document lives:

| Number | File |
|---|---|
| cross-validation, calibration, confirmation of a network | `<config>/train/summary.json` |
| zero-shot SEntFiN of a network | `<config>/sentfin/metrics.json` |
| an adaptation's before and after, KL, entropy, repaired and kept shares | `<config>/adapt/<run>/summary.json` |
| the linear control and its paired test | `<config>/linear/summary.json` |
| a word logit and its trigger words | `<config>/words/<set>/summary.json`, `trigger_words.csv` |
| the 154 checks | `integration_report.txt` |

## Using the models without training

`scripts/predict.py --config finance` reads `results/finance/train/nn_model.json` and the feature cache of the prediction
set; `scripts/adapt.py --model results/<config>/adapt/<run>/nn_model.json` starts from an adapted head. The emotion reading
of the dialogue model is served from `dialogue/train/nn_model.json` and its sentiment reading from
`dialogue/adapt/finance_train_grpo/nn_model.json`, two heads on the same features.

The feature caches (`features/<key>/pooled.npy`, `ids.csv`, `manifest.json`, 416 MB for the three corpora) drop the `features/` folder under the project root and the
encode job finds the three keys and skips the GPU.

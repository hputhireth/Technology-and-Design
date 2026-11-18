## Acknowledgements

I thank Dr. Viet Vo and Dr. Mengjiao Guo for their support throughout this work and for providing the supercomputer
compute capability on which the encoder, the heads and the full chain were run.

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


## Sources

The training follows these sources, grouped by the step of the pathway they shaped.

### Data (step 1)

1. H. Rashkin, E. M. Smith, M. Li, and Y.-L. Boureau, "Towards empathetic open-domain conversation models: A new benchmark and dataset," in Proc. ACL, 2019, pp. 5370 to 5381.
2. H. Yang, X.-Y. Liu, and C. D. Wang, "FinGPT: Open-source financial large language models," arXiv:2306.06031, 2023.
3. A. Sinha, S. Kedas, R. Kumar, and P. Malo, "SEntFiN 1.0: Entity-aware sentiment analysis for financial news," J. Assoc. Inf. Sci. Technol., vol. 73, no. 9, pp. 1314 to 1335, 2022.

### Frozen encoder (step 2)

4. J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of deep bidirectional transformers for language understanding," in Proc. NAACL-HLT, 2019, pp. 4171 to 4186.
5. Beijing Academy of Artificial Intelligence, "bge-large-en-v1.5," Hugging Face model card, 2023.
6. S. Xiao et al., "C-Pack: Packed resources for general Chinese embeddings," in Proc. 47th Int. ACM SIGIR Conf., 2024.
7. A. Kumar, A. Raghunathan, R. Jones, T. Ma, and P. Liang, "Fine-tuning can distort pretrained features and underperform out-of-distribution," in Proc. ICLR, 2022.
8. J. Dodge et al., "Fine-tuning pretrained language models: Weight initializations, data orders, and early stopping," arXiv:2002.06305, 2020.
9. M. Mosbach, M. Andriushchenko, and D. Klakow, "On the stability of fine-tuning BERT: Misconceptions, explanations, and strong baselines," in Proc. ICLR, 2021.

### Model selection (steps 3 and 7)

10. G. C. Cawley and N. L. C. Talbot, "On over-fitting in model selection and subsequent selection bias in performance evaluation," J. Mach. Learn. Res., vol. 11, pp. 2079 to 2107, 2010.
11. C. Nadeau and Y. Bengio, "Inference for the generalization error," Mach. Learn., vol. 52, pp. 239 to 281, 2003.

### Memorisation and noisy labels (step 5)

12. C. Zhang, S. Bengio, M. Hardt, B. Recht, and O. Vinyals, "Understanding deep learning requires rethinking generalization," in Proc. ICLR, 2017.
13. D. Arpit et al., "A closer look at memorization in deep networks," in Proc. ICML, 2017, pp. 233 to 242.
14. M. Toneva, A. Sordoni, R. Tachet des Combes, A. Trischler, Y. Bengio, and G. J. Gordon, "An empirical study of example forgetting during deep neural network learning," in Proc. ICLR, 2019.
15. C. G. Northcutt, L. Jiang, and I. L. Chuang, "Confident learning: Estimating uncertainty in dataset labels," J. Artif. Intell. Res., vol. 70, pp. 1373 to 1411, 2021.

### The head, training and calibration (steps 4 to 6)

16. I. Loshchilov and F. Hutter, "Decoupled weight decay regularization," in Proc. ICLR, 2019.
17. I. Loshchilov and F. Hutter, "SGDR: Stochastic gradient descent with warm restarts," in Proc. ICLR, 2017.
18. N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov, "Dropout: A simple way to prevent neural networks from overfitting," J. Mach. Learn. Res., vol. 15, pp. 1929 to 1958, 2014.
19. C. Szegedy, V. Vanhoucke, S. Ioffe, J. Shlens, and Z. Wojna, "Rethinking the Inception architecture for computer vision," in Proc. IEEE CVPR, 2016, pp. 2818 to 2826.
20. R. Müller, S. Kornblith, and G. Hinton, "When does label smoothing help?," in Advances in Neural Information Processing Systems, vol. 32, 2019, pp. 4694 to 4703.
21. B. T. Polyak and A. B. Juditsky, "Acceleration of stochastic approximation by averaging," SIAM J. Control Optim., vol. 30, no. 4, pp. 838 to 855, 1992.
22. P. Izmailov, D. Podoprikhin, T. Garipov, D. Vetrov, and A. G. Wilson, "Averaging weights leads to wider optima and better generalization," in Proc. UAI, 2018, pp. 876 to 885.
23. C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On calibration of modern neural networks," in Proc. ICML, 2017, pp. 1321 to 1330.

### Adaptation (step 8)

24. L. Ouyang et al., "Training language models to follow instructions with human feedback," in Advances in Neural Information Processing Systems, vol. 35, 2022, pp. 27730 to 27744.
25. T. Korbak, E. Perez, and C. L. Buckley, "RL with KL penalties is better viewed as Bayesian inference," in Findings of EMNLP, 2022, pp. 1083 to 1091.
26. R. Rafailov et al., "Direct preference optimization: Your language model is secretly a reward model," in Advances in Neural Information Processing Systems, vol. 36, 2023.
27. M. Norouzi et al., "Reward augmented maximum likelihood for neural structured prediction," in Advances in Neural Information Processing Systems, vol. 29, 2016.
28. R. J. Williams, "Simple statistical gradient-following algorithms for connectionist reinforcement learning," Mach. Learn., vol. 8, pp. 229 to 256, 1992.
29. J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, "Proximal policy optimization algorithms," arXiv:1707.06347, 2017.
30. Z. Shao et al., "DeepSeekMath: Pushing the limits of mathematical reasoning in open language models," arXiv:2402.03300, 2024.
31. G. Hinton, O. Vinyals, and J. Dean, "Distilling the knowledge in a neural network," arXiv:1503.02531, 2015.
32. I. Shenfeld, J. Pari, and P. Agrawal, "RL's Razor: Why online reinforcement learning forgets less," arXiv:2509.04259, 2025.
33. A. Karpathy, "Deep reinforcement learning: Pong from pixels," blog post, 31 May 2016. [Online]. Available: http://karpathy.github.io/2016/05/31/rl/
34. S. L. Brunton and J. N. Kutz, Data-Driven Science and Engineering: Machine Learning, Dynamical Systems, and Control, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2022, ch. 11, pp. 419 to 448.

### Controls (step 9)

35. T. Loughran and B. McDonald, "When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks," J. Finance, vol. 66, no. 1, pp. 35 to 65, 2011.

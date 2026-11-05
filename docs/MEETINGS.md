# Meeting log

Every meeting at which a program was discussed, with the rating given at the time: 1 unsatisfied to 5 satisfied. The sessions follow the working pattern: Monday 2 h, Tuesday 4, Wednesday 4, Friday 4, Saturday 2, Sunday 2, all on Discord calls.

| Date | Program | Rating | Note |
|---|---|---|---|
| 5 Oct 2026 | [data/explore_general.py](programs/data-explore-general-py.md) | 4/5 | Quality charts reviewed on the first call of the week. |
| 5 Oct 2026 | [research/finetune_encoder.py](programs/research-finetune-encoder-py.md) | 4/5 | Scope cut confirmed with Dr Vo by email; access under his project. |
| 6 Oct 2026 | [fs_detailed/fd_01_prepare.py](programs/fs-detailed-fd-01-prepare-py.md) | 3/5 | Prepared tables walked through on the call: 374 mojibake repairs and 2 label conflicts shown. |
| 6 Oct 2026 | [fs_detailed/fd_gpu_encode.py](programs/fs-detailed-fd-gpu-encode-py.md) | 4/5 | Encoding time far under the A2 estimate: 1.8 minutes for the whole corpus. |
| 6 Oct 2026 | [fs_detailed/fd_linear.py](programs/fs-detailed-fd-linear-py.md) | 2/5 | 57 percent on our own training set, worse on the test; the investigation agreed on the spot. |
| 6 Oct 2026 | [models/general_tfidf_logreg.py](programs/models-general-tfidf-logreg-py.md) | 3/5 | Explored only; not for the delivery. |
| 9 Oct 2026 | [fs_detailed/fd_investigate.py](programs/fs-detailed-fd-investigate-py.md) | 3/5 | The information is there; a single linear boundary does not read it. |
| 9 Oct 2026 | [data/benedetti_check.py](programs/data-benedetti-check-py.md) | 4/5 | Dismissed as a test set; SEntFiN 1.0 stays the external test. |
| 9 Oct 2026 | [models/emotion_label_similarity.py](programs/models-emotion-label-similarity-py.md) | 2/5 | The intensity pairs sit on top of each other; the route was dropped. |
| 10 Oct 2026 | [fs_detailed/fd_investigate.py](programs/fs-detailed-fd-investigate-py.md) | 4/5 | Sprint 1 planned on the strength of the read-out: a deep learning pipeline. |
| 10 Oct 2026 | [research/representation_analysis.py](programs/research-representation-analysis-py.md) | 3/5 | With the encoder frozen the space is fixed; the head is what we inspect. |
| 13 Oct 2026 | [fs_detailed/fd_07_nn.py](programs/fs-detailed-fd-07-nn-py.md) | 2/5 | The first network memorises its training set. |
| 16 Oct 2026 | [sentiment-app/app.py](programs/sentiment-app-app-py.md) | 3/5 | First Streamlit experiments shown at the Sprint 1 review. |
| 16 Oct 2026 | [fs_detailed/fd_07_nn.py](programs/fs-detailed-fd-07-nn-py.md) | 3/5 | Sprint 1 review: the protocol taken from the papers, page by page. |
| 16 Oct 2026 | [docs/minutes/](programs/docs-minutes.md) | 4/5 | Sprint 1 review and retrospective. |
| 18 Oct 2026 | [models/softmax_emotion_to_sentiment.py](programs/models-softmax-emotion-to-sentiment-py.md) | 2/5 | Walked back; the dialogue head gets a learned sentiment output instead. |
| 20 Oct 2026 | [fs_detailed/fd_07_nn.py](programs/fs-detailed-fd-07-nn-py.md) | 5/5 | c12 at 0.8044 cross-validated and 0.798 on the confirmation split. |
| 21 Oct 2026 | [fs_detailed/fd_08_label_audit.py](programs/fs-detailed-fd-08-label-audit-py.md) | 4/5 | Audit reviewed; the convention gap named. |
| 23 Oct 2026 | [sentiment-app/app.py](programs/sentiment-app-app-py.md) | 4/5 | The FinGPT Network export read into the page. |
| 23 Oct 2026 | [docs/minutes/](programs/docs-minutes.md) | 4/5 | Sprint 2 review and retrospective. |
| 23 Oct 2026 | [fs_detailed/fd_10_nn_inspect.py](programs/fs-detailed-fd-10-nn-inspect-py.md) | 4/5 | Sprint 2 review: the full model research demonstrated. |
| 23 Oct 2026 | [fs_detailed/fd_transfer_prior.py](programs/fs-detailed-fd-transfer-prior-py.md) | 3/5 | Uncorrected probabilities kept; the errors are a convention shift. |
| 23 Oct 2026 | [dashboard/index.html](programs/dashboard-index-html.md) | 2/5 | Dropped at the Sprint 2 review: one front end. |
| 24 Oct 2026 | [fs_detailed/ed_01_prepare.py](programs/fs-detailed-ed-01-prepare-py.md) | 4/5 | Sprint 3 planning: the Dialogue Network and the reinforcement suite. |
| 25 Oct 2026 | [fs_detailed/ed_07_nn.py](programs/fs-detailed-ed-07-nn-py.md) | 4/5 | The Dialogue Network reviewed on the Sunday call. |
| 25 Oct 2026 | [sentiment-app/README.md and the deployment](programs/sentiment-app-readme-md-and-the-deployment.md) | 4/5 | First deployment demonstrated on the Sunday call. |
| 26 Oct 2026 | [fs_detailed/ed_07_nn.py](programs/fs-detailed-ed-07-nn-py.md) | 4/5 | Live-testing check: the two readings from one trunk. |
| 26 Oct 2026 | [fs_detailed/ed_12_rl.py](programs/fs-detailed-ed-12-rl-py.md) | 4/5 | Gains and retention reviewed method by method. |
| 27 Oct 2026 | [configs/finance.json](programs/configs-finance-json.md) | 4/5 | Lean repository agreed: one config file per corpus. |
| 27 Oct 2026 | [fd_encode_server.py](programs/fd-encode-server-py.md) | 4/5 | The encoder service and the lean repository shown together. |
| 27 Oct 2026 | [fs_detailed/ed_rl_mistakes.py](programs/fs-detailed-ed-rl-mistakes-py.md) | 3/5 | A biased sample for the sampled methods; kept for the closed form only. |
| 27 Oct 2026 | [streamlit-a3/train_model.py](programs/streamlit-a3-train-model-py.md) | 3/5 | Dropped in favour of the exports. |
| 28 Oct 2026 | [scripts/prepare.py](programs/scripts-prepare-py.md) | 4/5 | Walkthrough of the lean repository. |
| 28 Oct 2026 | [scripts/encode.py](programs/scripts-encode-py.md) | 4/5 | Walkthrough of the lean repository. |
| 28 Oct 2026 | [common/text.py](programs/common-text-py.md) | 4/5 | Walkthrough of the lean repository. |
| 28 Oct 2026 | [common/encoder.py](programs/common-encoder-py.md) | 4/5 | Walkthrough of the lean repository. |
| 28 Oct 2026 | [common/paths.py](programs/common-paths-py.md) | 4/5 | Walkthrough of the lean repository at the live-testing check. |
| 28 Oct 2026 | [common/cache.py](programs/common-cache-py.md) | 4/5 | Walkthrough of the lean repository. |
| 28 Oct 2026 | [common/sets.py](programs/common-sets-py.md) | 4/5 | Walkthrough of the lean repository. |
| 29 Oct 2026 | [common/head.py](programs/common-head-py.md) | 4/5 | Export format agreed with Hara: mean, sd, trunk, outputs, temperatures. |
| 29 Oct 2026 | [scripts/train.py](programs/scripts-train-py.md) | 4/5 | train.py walked through against Appendix B. |
| 29 Oct 2026 | [scripts/predict.py](programs/scripts-predict-py.md) | 4/5 | predict.py walked through. |
| 30 Oct 2026 | [scripts/adapt.py](programs/scripts-adapt-py.md) | 4/5 | The closed form and GRPO side by side at the Sprint 3 review. |
| 30 Oct 2026 | [sentiment-app/app.py](programs/sentiment-app-app-py.md) | 4/5 | The Dialogue Network page and the adapted heads. |
| 30 Oct 2026 | [sentiment-app/build_models.py](programs/sentiment-app-build-models-py.md) | 4/5 | The store and its scan reviewed. |
| 30 Oct 2026 | [sentiment-app/tests/](programs/sentiment-app-tests.md) | 4/5 | Component tests and the first AppTest scenarios. |
| 30 Oct 2026 | [fs_detailed/ed_12_rl.py](programs/fs-detailed-ed-12-rl-py.md) | 4/5 | Sprint 3 review: only the closed form and GRPO ship. |
| 30 Oct 2026 | [tests/forbidden_patterns.py](programs/tests-forbidden-patterns-py.md) | 4/5 | Security write-up reviewed; the scan run over the public copy. |
| 30 Oct 2026 | [docs/security_writeup.md](programs/docs-security-writeup-md.md) | 4/5 | Reviewed at the Sprint 3 review. |
| 30 Oct 2026 | [docs/minutes/](programs/docs-minutes.md) | 4/5 | Sprint 3 review and retrospective. |
| 31 Oct 2026 | [common/metrics.py](programs/common-metrics-py.md) | 4/5 | The corrected t-test on known values at the live-testing check. |
| 31 Oct 2026 | [scripts/linear.py](programs/scripts-linear-py.md) | 4/5 | +0.018 macro-F1 for the hidden layers on FinGPT, p 5e-8; a tie on the dialogue data. |
| 31 Oct 2026 | [scripts/words.py](programs/scripts-words-py.md) | 4/5 | FinGPT at 71.0, SEntFiN at 58.9 zero-shot and 79.8 in domain. |
| 1 Nov 2026 | [tests/unit/](programs/tests-unit.md) | 4/5 | 111 passed in 15 seconds at the live-testing check. |
| 1 Nov 2026 | [tests/smoke.sh](programs/tests-smoke-sh.md) | 4/5 | 25 steps in 140 seconds on the login node. |
| 1 Nov 2026 | [sentiment-app/app.py](programs/sentiment-app-app-py.md) | 5/5 | All fourteen models live. |
| 1 Nov 2026 | [sentiment-app/tests/](programs/sentiment-app-tests.md) | 5/5 | 213 passed, 1 skipped, 98 percent coverage. |
| 1 Nov 2026 | [docs/A3_Design_Document.docx](programs/docs-a3-design-document-docx.md) | 4/5 | The 1 November version read through at the Sunday session. |
| 1 Nov 2026 | [common/runlog.py](programs/common-runlog-py.md) | 4/5 | Log format shown at the live-testing check; the same line in every layer. |
| 1 Nov 2026 | [.github/workflows/ci.yml](programs/github-workflows-ci-yml.md) | 4/5 | CI green on the redeployment commit. |
| 1 Nov 2026 | [sentiment-app/README.md and the deployment](programs/sentiment-app-readme-md-and-the-deployment.md) | 5/5 | All fourteen models redeployed. |
| 1 Nov 2026 | [docs/test_plan.md](programs/docs-test-plan-md.md) | 4/5 | Test plan read against the logs. |
| 2 Nov 2026 | [slurm/_header.sh](programs/slurm-header-sh.md) | 2/5 | Two CH-03 lines in the chain log: sbatch does not pass environment variables into a job. |
| 2 Nov 2026 | [slurm/chain.sh](programs/slurm-chain-sh.md) | 2/5 | Submissions one and two failed on the environment and the configuration. |
| 2 Nov 2026 | [tests/integration/check_results.py](programs/tests-integration-check-results-py.md) | 3/5 | 149 of 154 on the first complete run: manifests, decimals and a copied band. |
| 2 Nov 2026 | [env/paths.sh](programs/env-paths-sh.md) | 2/5 | First chain submission on Python 3.9 with the CUDA 12.8 wheels: jobs cancelled, environment rebuilt. |
| 3 Nov 2026 | [scripts/train.py](programs/scripts-train-py.md) | 5/5 | The two networks reproduce to the fourth decimal. |
| 3 Nov 2026 | [scripts/adapt.py](programs/scripts-adapt-py.md) | 5/5 | 84.4 (sd 0.2) for 78.8 kept; the dialogue head at 78.6 with its emotion reading intact. |
| 3 Nov 2026 | [slurm/chain.sh](programs/slurm-chain-sh.md) | 5/5 | Submission four: 154 PASS, 8 FAIL on the broken copy, exit 0 on the clean tree. |
| 3 Nov 2026 | [tests/smoke.sh](programs/tests-smoke-sh.md) | 4/5 | SM-25 confirmed the mutation-count fix before the resubmission. |
| 3 Nov 2026 | [tests/integration/check_results.py](programs/tests-integration-check-results-py.md) | 5/5 | 154 PASS in 12.8 seconds as the last job of the chain. |
| 3 Nov 2026 | [scripts/words.py](programs/scripts-words-py.md) | 3/5 | A word at 0.50004 recomputed on the other side of 0.5; six decimals now. |
| 3 Nov 2026 | [tests/integration/mutate.py](programs/tests-integration-mutate-py.md) | 4/5 | 8 FAIL, exit 1 on the broken copy; the clean tree 154 PASS. |
| 4 Nov 2026 | [docs/A3_Design_Document.docx](programs/docs-a3-design-document-docx.md) | 4/5 | Team review: changes highlighted. |
| 4 Nov 2026 | [docs/presentation/](programs/docs-presentation.md) | 4/5 | First rehearsal of the three scripts. |
| 4 Nov 2026 | [.github/](programs/github.md) | 3/5 | Board created; the final update went to main directly instead of through the cycle. |
| 5 Nov 2026 | [sentiment-app/build_models.py](programs/sentiment-app-build-models-py.md) | 3/5 | The store still holds the October exports; the rebuild is planned for the weekend. |
| 5 Nov 2026 | [sentiment-app/build_models.py](programs/sentiment-app-build-models-py.md) | 5/5 | The store rebuilt from the 3 November exports and deployed; closed at the wrap-up. |
| 5 Nov 2026 | [deploy/Dockerfile](programs/deploy-dockerfile.md) | 3/5 | Decision: only the Streamlit deployment ships; the cloud system is cancelled. |
| 5 Nov 2026 | [deploy/cloud_notes.md](programs/deploy-cloud-notes-md.md) | 3/5 | Cancelled with the cloud system. |
| 6 Nov 2026 | [docs/A3_Design_Document.docx](programs/docs-a3-design-document-docx.md) | pending | Review with Dr Vo, 2:30 to 3:00 pm. |
| 6 Nov 2026 | [docs/minutes/](programs/docs-minutes.md) | pending | Sprint 4 review and retrospective. |
| 10 Nov 2026 | [docs/presentation/](programs/docs-presentation.md) | pending | Final rehearsal. |

[Back to the backlog](README.md)

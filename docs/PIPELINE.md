# Pipeline map

One box per program file, from the encoding research to the front end; an arrow means the box on the left feeds the one on the right. Dashed boxes were cancelled, heavy borders are the open work, and a dotted box in a phase diagram belongs to another phase. Each box has its own page under `programs/`.

## The phases

```mermaid
flowchart LR
  A["Encoding research<br/><small>11 programs, 1 to 10 Oct</small>"]
  B["Model research<br/><small>8 programs, Sprints 1 to 3</small>"]
  C["Final pipeline<br/><small>19 programs, 27 Oct to 3 Nov</small>"]
  D["Test layers<br/><small>5 programs, 29 Oct to 3 Nov</small>"]
  E["Front end<br/><small>8 programs, 12 Oct to 9 Nov</small>"]
  F["Cloud system<br/><small>2 programs, after 6 Nov</small>"]
  G["Documents and process<br/><small>6 programs, whole project</small>"]
  A --> B
  B --> C
  C --> D
  D --> E
  E --> F
  C --> G
  D --> G
  E --> G
```

## Encoding research

First access to the SuperComputer, the first encoding pass, the first linear model and the data investigation.

```mermaid
flowchart LR
  c16["scripts/words.py<br/><small>Final pipeline</small>"]
  c15["scripts/linear.py<br/><small>Final pipeline</small>"]
  ed01["fs_detailed/ed_01_prepare.py<br/><small>Model research</small>"]
  fdtr["fs_detailed/fd_transfer_prior.py<br/><small>Model research</small>"]
  fd10["fs_detailed/fd_10_nn_inspect.py<br/><small>Model research</small>"]
  fd07["fs_detailed/fd_07_nn.py<br/><small>Model research</small>"]
  fd01["fs_detailed/fd_01_prepare.py"]
  fdgpu["fs_detailed/fd_gpu_encode.py"]
  fdlin["fs_detailed/fd_linear.py"]
  fdinv["fs_detailed/fd_investigate.py"]
  bened["data/benedetti_check.py"]
  jexp["data/explore_general.py"]
  jtfidf["models/general_tfidf_logreg.py"]
  jsim["models/emotion_label_similarity.py"]
  jsoft["models/softmax_emotion_to_sentiment.py"]
  fine["research/finetune_encoder.py"]
  repr["research/representation_analysis.py"]
  fd01 --> fdgpu
  fdgpu --> fdlin
  fdlin --> fdinv
  fdinv -.-> fd07
  fdgpu -.-> fd07
  jexp --> jtfidf
  jexp --> jsim
  jsim --> jsoft
  jsoft -.-> ed01
  bened -.-> fdtr
  fine --> fdgpu
  repr -.-> fd10
  fdlin -.-> c15
  jtfidf -.-> c16
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class jtfidf,jsim,jsoft,fine,repr cancelled
  class fd07,fd10,fdtr,ed01,c15,c16 other
```

## Model research

The research pipeline fs_detailed: the head search under the protocol, the audit, the inspection, the Dialogue Network and the reinforcement suite.

```mermaid
flowchart LR
  c14["scripts/adapt.py<br/><small>Final pipeline</small>"]
  c6["common/head.py<br/><small>Final pipeline</small>"]
  repr["research/representation_analysis.py<br/><small>Encoding research</small>"]
  jsoft["models/softmax_emotion_to_sentiment.py<br/><small>Encoding research</small>"]
  bened["data/benedetti_check.py<br/><small>Encoding research</small>"]
  fdinv["fs_detailed/fd_investigate.py<br/><small>Encoding research</small>"]
  fdgpu["fs_detailed/fd_gpu_encode.py<br/><small>Encoding research</small>"]
  fd07["fs_detailed/fd_07_nn.py"]
  fd08["fs_detailed/fd_08_label_audit.py"]
  fd10["fs_detailed/fd_10_nn_inspect.py"]
  fdtr["fs_detailed/fd_transfer_prior.py"]
  ed01["fs_detailed/ed_01_prepare.py"]
  ed07["fs_detailed/ed_07_nn.py"]
  ed12["fs_detailed/ed_12_rl.py"]
  edmis["fs_detailed/ed_rl_mistakes.py"]
  fdinv -.-> fd07
  fdgpu -.-> fd07
  jsoft -.-> ed01
  bened -.-> fdtr
  repr -.-> fd10
  fd07 --> fd08
  fd07 --> fd10
  fd07 --> fdtr
  fd07 --> ed01
  ed01 --> ed07
  ed07 --> ed12
  ed12 --> edmis
  fd07 -.-> c6
  ed12 -.-> c14
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class fdgpu,fdinv,bened,jsoft,repr,c6,c14 other
```

## Final pipeline

The final repository sentiment_heads: one configuration per corpus, nine common modules, seven scripts and the Slurm chain that ran end to end on 3 November.

```mermaid
flowchart LR
  e2["sentiment-app/build_models.py<br/><small>Front end</small>"]
  d3["tests/integration/check_results.py<br/><small>Test layers</small>"]
  d2["tests/smoke.sh<br/><small>Test layers</small>"]
  d1["tests/unit/<br/><small>Test layers</small>"]
  ed12["fs_detailed/ed_12_rl.py<br/><small>Model research</small>"]
  fd07["fs_detailed/fd_07_nn.py<br/><small>Model research</small>"]
  jtfidf["models/general_tfidf_logreg.py<br/><small>Encoding research</small>"]
  fdlin["fs_detailed/fd_linear.py<br/><small>Encoding research</small>"]
  c2["common/paths.py"]
  c3["common/text.py"]
  c4["common/cache.py"]
  c5["common/encoder.py"]
  c6["common/head.py"]
  c7["common/metrics.py"]
  c8["common/sets.py"]
  c9["common/runlog.py"]
  c0["configs/finance.json"]
  c10["scripts/prepare.py"]
  c11["scripts/encode.py"]
  c12["scripts/train.py"]
  c13["scripts/predict.py"]
  c14["scripts/adapt.py"]
  c15["scripts/linear.py"]
  c16["scripts/words.py"]
  c1["env/paths.sh"]
  c17["slurm/_header.sh"]
  c18["slurm/chain.sh"]
  fd07 -.-> c6
  ed12 -.-> c14
  fdlin -.-> c15
  jtfidf -.-> c16
  c2 --> c10
  c3 --> c10
  c4 --> c11
  c5 --> c11
  c6 --> c12
  c7 --> c12
  c8 --> c12
  c9 --> c17
  c0 --> c10
  c10 --> c11
  c11 --> c12
  c12 --> c13
  c12 --> c14
  c12 --> c15
  c12 --> c16
  c1 --> c17
  c17 --> c18
  c18 -.-> d3
  c6 -.-> d1
  d2 -.-> c18
  c14 -.-> d3
  c15 -.-> d3
  c16 -.-> d3
  c12 -.-> e2
  c14 -.-> e2
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class fdlin,jtfidf,fd07,ed12,d1,d2,d3,e2 other
```

## Test layers

Unit, smoke, integration and mutation, written before the step each one checks, plus the security scan.

```mermaid
flowchart LR
  g4["docs/security_writeup.md<br/><small>Documents and process</small>"]
  g2["docs/test_plan.md<br/><small>Documents and process</small>"]
  e2["sentiment-app/build_models.py<br/><small>Front end</small>"]
  c18["slurm/chain.sh<br/><small>Final pipeline</small>"]
  c16["scripts/words.py<br/><small>Final pipeline</small>"]
  c15["scripts/linear.py<br/><small>Final pipeline</small>"]
  c14["scripts/adapt.py<br/><small>Final pipeline</small>"]
  c6["common/head.py<br/><small>Final pipeline</small>"]
  d1["tests/unit/"]
  d2["tests/smoke.sh"]
  d3["tests/integration/check_results.py"]
  d4["tests/integration/mutate.py"]
  d5["tests/forbidden_patterns.py"]
  c18 -.-> d3
  c6 -.-> d1
  d1 --> d2
  d2 -.-> c18
  d3 --> d4
  c14 -.-> d3
  c15 -.-> d3
  c16 -.-> d3
  d5 -.-> e2
  d3 -.-> g2
  d5 -.-> g4
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class c6,c14,c15,c16,c18,e2,g2,g4 other
```

## Front end

The Streamlit application, its model store, the encoder service, its 213 tests, CI and the deployment.

```mermaid
flowchart LR
  g1["docs/A3_Design_Document.docx<br/><small>Documents and process</small>"]
  f1["deploy/Dockerfile<br/><small>Cloud system</small>"]
  d5["tests/forbidden_patterns.py<br/><small>Test layers</small>"]
  c14["scripts/adapt.py<br/><small>Final pipeline</small>"]
  c12["scripts/train.py<br/><small>Final pipeline</small>"]
  e1["sentiment-app/app.py"]
  e2["sentiment-app/build_models.py"]
  e3["fd_encode_server.py"]
  e4["sentiment-app/tests/"]
  e5[".github/workflows/ci.yml"]
  e6["sentiment-app/README.md and the deployment"]
  e7["streamlit-a3/train_model.py"]
  e8["dashboard/index.html"]
  d5 -.-> e2
  c12 -.-> e2
  c14 -.-> e2
  e2 --> e1
  e3 --> e1
  e1 --> e4
  e4 --> e5
  e5 --> e6
  e7 --> e2
  e8 --> e1
  e6 -.-> f1
  e3 -.-> f1
  e4 -.-> g1
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class e7,e8 cancelled
  class c12,c14,d5,f1,g1 other
```

## Cloud system

Containers for the application and the encoder service, the model store from the release asset, hosting notes.

```mermaid
flowchart LR
  e6["sentiment-app/README.md and the deployment<br/><small>Front end</small>"]
  e3["fd_encode_server.py<br/><small>Front end</small>"]
  f1["deploy/Dockerfile"]
  f2["deploy/cloud_notes.md"]
  e6 -.-> f1
  e3 -.-> f1
  f1 --> f2
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class f1,f2 cancelled
  class e3,e6 other
```

## Documents and process

The design document, the test plan, the presentation, the security write-up, the minutes and the repository protocol.

```mermaid
flowchart LR
  e4["sentiment-app/tests/<br/><small>Front end</small>"]
  d5["tests/forbidden_patterns.py<br/><small>Test layers</small>"]
  d3["tests/integration/check_results.py<br/><small>Test layers</small>"]
  g1["docs/A3_Design_Document.docx"]
  g2["docs/test_plan.md"]
  g3["docs/presentation/"]
  g4["docs/security_writeup.md"]
  g5["docs/minutes/"]
  g6[".github/"]
  d3 -.-> g2
  g2 --> g1
  e4 -.-> g1
  g1 --> g3
  d5 -.-> g4
  g5 --> g6
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class g1 live
  class d3,d5,e4 other
```

## The whole map

The same boxes and arrows in one picture. It is wide, so it is also kept as [pipeline.svg](pipeline.svg), which opens at full size.

```mermaid
flowchart LR
  subgraph A["Encoding research"]
    direction TB
    fd01["fs_detailed/fd_01_prepare.py"]
    fdgpu["fs_detailed/fd_gpu_encode.py"]
    fdlin["fs_detailed/fd_linear.py"]
    fdinv["fs_detailed/fd_investigate.py"]
    bened["data/benedetti_check.py"]
    jexp["data/explore_general.py"]
    jtfidf["models/general_tfidf_logreg.py"]
    jsim["models/emotion_label_similarity.py"]
    jsoft["models/softmax_emotion_to_sentiment.py"]
    fine["research/finetune_encoder.py"]
    repr["research/representation_analysis.py"]
  end
  subgraph B["Model research"]
    direction TB
    fd07["fs_detailed/fd_07_nn.py"]
    fd08["fs_detailed/fd_08_label_audit.py"]
    fd10["fs_detailed/fd_10_nn_inspect.py"]
    fdtr["fs_detailed/fd_transfer_prior.py"]
    ed01["fs_detailed/ed_01_prepare.py"]
    ed07["fs_detailed/ed_07_nn.py"]
    ed12["fs_detailed/ed_12_rl.py"]
    edmis["fs_detailed/ed_rl_mistakes.py"]
  end
  subgraph C["Final pipeline"]
    direction TB
    c2["common/paths.py"]
    c3["common/text.py"]
    c4["common/cache.py"]
    c5["common/encoder.py"]
    c6["common/head.py"]
    c7["common/metrics.py"]
    c8["common/sets.py"]
    c9["common/runlog.py"]
    c0["configs/finance.json"]
    c10["scripts/prepare.py"]
    c11["scripts/encode.py"]
    c12["scripts/train.py"]
    c13["scripts/predict.py"]
    c14["scripts/adapt.py"]
    c15["scripts/linear.py"]
    c16["scripts/words.py"]
    c1["env/paths.sh"]
    c17["slurm/_header.sh"]
    c18["slurm/chain.sh"]
  end
  subgraph D["Test layers"]
    direction TB
    d1["tests/unit/"]
    d2["tests/smoke.sh"]
    d3["tests/integration/check_results.py"]
    d4["tests/integration/mutate.py"]
    d5["tests/forbidden_patterns.py"]
  end
  subgraph E["Front end"]
    direction TB
    e1["sentiment-app/app.py"]
    e2["sentiment-app/build_models.py"]
    e3["fd_encode_server.py"]
    e4["sentiment-app/tests/"]
    e5[".github/workflows/ci.yml"]
    e6["sentiment-app/README.md and the deployment"]
    e7["streamlit-a3/train_model.py"]
    e8["dashboard/index.html"]
  end
  subgraph F["Cloud system"]
    direction TB
    f1["deploy/Dockerfile"]
    f2["deploy/cloud_notes.md"]
  end
  subgraph G["Documents and process"]
    direction TB
    g1["docs/A3_Design_Document.docx"]
    g2["docs/test_plan.md"]
    g3["docs/presentation/"]
    g4["docs/security_writeup.md"]
    g5["docs/minutes/"]
    g6[".github/"]
  end
  fd01 --> fdgpu
  fdgpu --> fdlin
  fdlin --> fdinv
  fdinv --> fd07
  fdgpu --> fd07
  jexp --> jtfidf
  jexp --> jsim
  jsim --> jsoft
  jsoft --> ed01
  bened --> fdtr
  fine --> fdgpu
  repr --> fd10
  fd07 --> fd08
  fd07 --> fd10
  fd07 --> fdtr
  fd07 --> ed01
  ed01 --> ed07
  ed07 --> ed12
  ed12 --> edmis
  fd07 --> c6
  ed12 --> c14
  fdlin --> c15
  jtfidf --> c16
  c2 --> c10
  c3 --> c10
  c4 --> c11
  c5 --> c11
  c6 --> c12
  c7 --> c12
  c8 --> c12
  c9 --> c17
  c0 --> c10
  c10 --> c11
  c11 --> c12
  c12 --> c13
  c12 --> c14
  c12 --> c15
  c12 --> c16
  c1 --> c17
  c17 --> c18
  c18 --> d3
  c6 --> d1
  d1 --> d2
  d2 --> c18
  d3 --> d4
  c14 --> d3
  c15 --> d3
  c16 --> d3
  d5 --> e2
  c12 --> e2
  c14 --> e2
  e2 --> e1
  e3 --> e1
  e1 --> e4
  e4 --> e5
  e5 --> e6
  e7 --> e2
  e8 --> e1
  e6 --> f1
  e3 --> f1
  f1 --> f2
  d3 --> g2
  g2 --> g1
  e4 --> g1
  g1 --> g3
  d5 --> g4
  g5 --> g6
  classDef cancelled stroke-dasharray: 4 3,opacity:0.55
  classDef live stroke-width:3px
  classDef other stroke-dasharray: 2 2,fill:none,color:#777
  class jtfidf,jsim,jsoft,fine,repr,e7,e8,f1,f2 cancelled
  class g1 live
```

## The boxes

| Phase | Program | Status | Page |
|---|---|---|---|
| Encoding research | `fs_detailed/fd_01_prepare.py` | Complete | [fs-detailed-fd-01-prepare-py.md](programs/fs-detailed-fd-01-prepare-py.md) |
| Encoding research | `fs_detailed/fd_gpu_encode.py` | Complete | [fs-detailed-fd-gpu-encode-py.md](programs/fs-detailed-fd-gpu-encode-py.md) |
| Encoding research | `fs_detailed/fd_linear.py` | Complete | [fs-detailed-fd-linear-py.md](programs/fs-detailed-fd-linear-py.md) |
| Encoding research | `fs_detailed/fd_investigate.py` | Complete | [fs-detailed-fd-investigate-py.md](programs/fs-detailed-fd-investigate-py.md) |
| Encoding research | `data/benedetti_check.py` | Complete | [data-benedetti-check-py.md](programs/data-benedetti-check-py.md) |
| Encoding research | `data/explore_general.py` | Complete | [data-explore-general-py.md](programs/data-explore-general-py.md) |
| Encoding research | `models/general_tfidf_logreg.py` | Cancelled | [models-general-tfidf-logreg-py.md](programs/models-general-tfidf-logreg-py.md) |
| Encoding research | `models/emotion_label_similarity.py` | Cancelled | [models-emotion-label-similarity-py.md](programs/models-emotion-label-similarity-py.md) |
| Encoding research | `models/softmax_emotion_to_sentiment.py` | Cancelled | [models-softmax-emotion-to-sentiment-py.md](programs/models-softmax-emotion-to-sentiment-py.md) |
| Encoding research | `research/finetune_encoder.py` | Cancelled | [research-finetune-encoder-py.md](programs/research-finetune-encoder-py.md) |
| Encoding research | `research/representation_analysis.py` | Cancelled | [research-representation-analysis-py.md](programs/research-representation-analysis-py.md) |
| Model research | `fs_detailed/fd_07_nn.py` | Complete | [fs-detailed-fd-07-nn-py.md](programs/fs-detailed-fd-07-nn-py.md) |
| Model research | `fs_detailed/fd_08_label_audit.py` | Complete | [fs-detailed-fd-08-label-audit-py.md](programs/fs-detailed-fd-08-label-audit-py.md) |
| Model research | `fs_detailed/fd_10_nn_inspect.py` | Complete | [fs-detailed-fd-10-nn-inspect-py.md](programs/fs-detailed-fd-10-nn-inspect-py.md) |
| Model research | `fs_detailed/fd_transfer_prior.py` | Complete | [fs-detailed-fd-transfer-prior-py.md](programs/fs-detailed-fd-transfer-prior-py.md) |
| Model research | `fs_detailed/ed_01_prepare.py` | Complete | [fs-detailed-ed-01-prepare-py.md](programs/fs-detailed-ed-01-prepare-py.md) |
| Model research | `fs_detailed/ed_07_nn.py` | Complete | [fs-detailed-ed-07-nn-py.md](programs/fs-detailed-ed-07-nn-py.md) |
| Model research | `fs_detailed/ed_12_rl.py` | Complete | [fs-detailed-ed-12-rl-py.md](programs/fs-detailed-ed-12-rl-py.md) |
| Model research | `fs_detailed/ed_rl_mistakes.py` | Complete | [fs-detailed-ed-rl-mistakes-py.md](programs/fs-detailed-ed-rl-mistakes-py.md) |
| Final pipeline | `common/paths.py` | Complete | [common-paths-py.md](programs/common-paths-py.md) |
| Final pipeline | `common/text.py` | Complete | [common-text-py.md](programs/common-text-py.md) |
| Final pipeline | `common/cache.py` | Complete | [common-cache-py.md](programs/common-cache-py.md) |
| Final pipeline | `common/encoder.py` | Complete | [common-encoder-py.md](programs/common-encoder-py.md) |
| Final pipeline | `common/head.py` | Complete | [common-head-py.md](programs/common-head-py.md) |
| Final pipeline | `common/metrics.py` | Complete | [common-metrics-py.md](programs/common-metrics-py.md) |
| Final pipeline | `common/sets.py` | Complete | [common-sets-py.md](programs/common-sets-py.md) |
| Final pipeline | `common/runlog.py` | Complete | [common-runlog-py.md](programs/common-runlog-py.md) |
| Final pipeline | `configs/finance.json` | Complete | [configs-finance-json.md](programs/configs-finance-json.md) |
| Final pipeline | `scripts/prepare.py` | Complete | [scripts-prepare-py.md](programs/scripts-prepare-py.md) |
| Final pipeline | `scripts/encode.py` | Complete | [scripts-encode-py.md](programs/scripts-encode-py.md) |
| Final pipeline | `scripts/train.py` | Complete | [scripts-train-py.md](programs/scripts-train-py.md) |
| Final pipeline | `scripts/predict.py` | Complete | [scripts-predict-py.md](programs/scripts-predict-py.md) |
| Final pipeline | `scripts/adapt.py` | Complete | [scripts-adapt-py.md](programs/scripts-adapt-py.md) |
| Final pipeline | `scripts/linear.py` | Complete | [scripts-linear-py.md](programs/scripts-linear-py.md) |
| Final pipeline | `scripts/words.py` | Complete | [scripts-words-py.md](programs/scripts-words-py.md) |
| Final pipeline | `env/paths.sh` | Complete | [env-paths-sh.md](programs/env-paths-sh.md) |
| Final pipeline | `slurm/_header.sh` | Complete | [slurm-header-sh.md](programs/slurm-header-sh.md) |
| Final pipeline | `slurm/chain.sh` | Complete | [slurm-chain-sh.md](programs/slurm-chain-sh.md) |
| Test layers | `tests/unit/` | Complete | [tests-unit.md](programs/tests-unit.md) |
| Test layers | `tests/smoke.sh` | Complete | [tests-smoke-sh.md](programs/tests-smoke-sh.md) |
| Test layers | `tests/integration/check_results.py` | Complete | [tests-integration-check-results-py.md](programs/tests-integration-check-results-py.md) |
| Test layers | `tests/integration/mutate.py` | Complete | [tests-integration-mutate-py.md](programs/tests-integration-mutate-py.md) |
| Test layers | `tests/forbidden_patterns.py` | Complete | [tests-forbidden-patterns-py.md](programs/tests-forbidden-patterns-py.md) |
| Front end | `sentiment-app/app.py` | Complete | [sentiment-app-app-py.md](programs/sentiment-app-app-py.md) |
| Front end | `sentiment-app/build_models.py` | Complete | [sentiment-app-build-models-py.md](programs/sentiment-app-build-models-py.md) |
| Front end | `fd_encode_server.py` | Complete | [fd-encode-server-py.md](programs/fd-encode-server-py.md) |
| Front end | `sentiment-app/tests/` | Complete | [sentiment-app-tests.md](programs/sentiment-app-tests.md) |
| Front end | `.github/workflows/ci.yml` | Complete | [github-workflows-ci-yml.md](programs/github-workflows-ci-yml.md) |
| Front end | `sentiment-app/README.md and the deployment` | Complete | [sentiment-app-readme-md-and-the-deployment.md](programs/sentiment-app-readme-md-and-the-deployment.md) |
| Front end | `streamlit-a3/train_model.py` | Cancelled | [streamlit-a3-train-model-py.md](programs/streamlit-a3-train-model-py.md) |
| Front end | `dashboard/index.html` | Cancelled | [dashboard-index-html.md](programs/dashboard-index-html.md) |
| Cloud system | `deploy/Dockerfile` | Cancelled | [deploy-dockerfile.md](programs/deploy-dockerfile.md) |
| Cloud system | `deploy/cloud_notes.md` | Cancelled | [deploy-cloud-notes-md.md](programs/deploy-cloud-notes-md.md) |
| Documents and process | `docs/A3_Design_Document.docx` | Under review | [docs-a3-design-document-docx.md](programs/docs-a3-design-document-docx.md) |
| Documents and process | `docs/test_plan.md` | Complete | [docs-test-plan-md.md](programs/docs-test-plan-md.md) |
| Documents and process | `docs/presentation/` | Complete | [docs-presentation.md](programs/docs-presentation.md) |
| Documents and process | `docs/security_writeup.md` | Complete | [docs-security-writeup-md.md](programs/docs-security-writeup-md.md) |
| Documents and process | `docs/minutes/` | Complete | [docs-minutes.md](programs/docs-minutes.md) |
| Documents and process | `.github/` | Complete | [github.md](programs/github.md) |

[Back to the backlog](README.md)

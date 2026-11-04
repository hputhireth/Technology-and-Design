#!/usr/bin/env python3
"""words: the control for the encoder. A text is the set of distinct words it contains ([a-z]+(?:'[a-z]+)? in the lower-cased text); a multinomial logit
on the word indicators, L2 penalty, intercepts unpenalised, by L-BFGS. The penalty identifies the model: adding a constant to every class leaves the
probabilities unchanged, so the smallest-norm member is the one fitted and every class keeps its own coefficients. A word's meaning is its reading as a
one-word text, softmax(b + beta_w); a word whose top class passes 50% is a trigger word. Unknown words add nothing; a text with no known word reads N/A, never the prior.
One model per corpus: the network's confirmation split and folds for a training set, an own grouped 85/15 split and folds for a prediction set.
    python scripts/words.py --config finance --set train
    python scripts/words.py --config finance --set sentfin
    python scripts/words.py --config dialogue --set train --reading emotion
Writes $Root/results/<config>/words/<set>/: words_model.json, summary.json, cv_runs.csv, confirmation_ids.csv, folds.csv, confusion.csv, trigger_words.csv
and, for a training set, the zero-shot readings of every prediction set under <set>/predictions.csv with metrics.json.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import resource
import sys
import time
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import metrics, paths, text

WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")

def log(*a):
    print("[words]", *a, flush=True)

def words_of(s: str) -> list[str]:
    return sorted(set(WORD.findall(str(s).lower())))

def indicators(texts, index: dict) -> sp.csr_matrix:
    rows, cols = [], []
    for i, t in enumerate(texts):
        for w in words_of(t):
            j = index.get(w)
            if j is not None:
                rows.append(i)
                cols.append(j)
    return sp.csr_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(len(texts), len(index)))

def fit_logit(X: sp.csr_matrix, y: np.ndarray, K: int, C: float, max_iter: int):
    from sklearn.linear_model import LogisticRegression
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = LogisticRegression(C=C, solver="lbfgs", max_iter=max_iter, tol=1e-5).fit(X, y)
    W, b = np.zeros((K, X.shape[1]), np.float64), np.zeros(K, np.float64)
    if len(m.classes_) == 2 and m.coef_.shape[0] == 1:
        W[m.classes_[1]], b[m.classes_[1]] = m.coef_[0], m.intercept_[0]
    else:
        W[m.classes_], b[m.classes_] = m.coef_, m.intercept_
    return W, b, int(np.max(m.n_iter_))

def read(W: np.ndarray, b: np.ndarray, X: sp.csr_matrix) -> tuple[np.ndarray, np.ndarray]:
    """Probabilities per row and the rows that carry at least one known word; a row without one reads N/A (prediction -1)."""
    covered = np.asarray(X.sum(1)).ravel() > 0
    P = metrics.softmax(np.asarray(X @ W.T) + b)
    return P, covered

def predict(P: np.ndarray, covered: np.ndarray) -> np.ndarray:
    pred = P.argmax(1)
    pred[~covered] = -1
    return pred

def score(y: np.ndarray, P: np.ndarray, covered: np.ndarray, K: int) -> dict:
    """Accuracy and macro-F1 over every row (N/A counts as wrong); log-loss, AUC and ECE over the covered rows."""
    pred = predict(P, covered)
    out = {"accuracy": float((pred == y).mean()), "macro_f1": metrics.macro_f1(y, pred, K), "rows": int(len(y)), "covered": int(covered.sum()), "na": int((~covered).sum())}
    if covered.sum() > 1 and len(set(y[covered])) > 1:
        ev = metrics.evaluate(y[covered], P[covered])
        out.update({k: ev[k] for k in ("log_loss", "auc_ovr_macro", "ece_15")})
    return out

def trigger_words(words: list[str], W: np.ndarray, b: np.ndarray, classes: list[str]) -> pd.DataFrame:
    P = metrics.softmax(W.T + b)
    top = P.argmax(1)
    return pd.DataFrame({"word": words, "class": np.array(classes)[top], "probability": P.max(1)})

def own_split(y: np.ndarray, groups: np.ndarray, P: dict, seed: int):
    dev, conf = text.confirmation_split(y, groups, float(P["confirmation_fraction"]), seed)
    conf_mask = np.zeros(len(y), bool)
    conf_mask[conf] = True
    folds = []
    for s in range(int(P["seeds"])):
        for f, (tr, va) in enumerate(text.grouped_folds(y[dev], groups[dev], int(P["folds"]), seed + s)):
            folds.append((s, f + 1, dev[tr], dev[va]))
    return conf_mask, folds

def network_split(train_dir: Path, ids: np.ndarray):
    conf_ids = set(pd.read_csv(train_dir / "confirmation_ids.csv", dtype=str)["id"])
    tab = pd.read_csv(train_dir / "folds.csv", dtype={"id": str})
    pos = {i: k for k, i in enumerate(ids)}
    conf = np.array([i in conf_ids for i in ids])
    dev = np.where(~conf)[0]
    folds = []
    for (s, f), part in tab.groupby(["seed", "fold"], sort=True):
        va = np.array(sorted(pos[i] for i in part["id"]))
        folds.append((int(s), int(f), np.setdiff1d(dev, va), va))
    return conf, folds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--set", default="train")
    ap.add_argument("--reading", default=None, help="default: the first reading of the config")
    ap.add_argument("--C", type=float, default=None, help="default 1.0, 0.3 for the emotion reading")
    ap.add_argument("--max-iter", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=0)
    args = ap.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", str(args.threads or int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) or os.cpu_count() or 1))
    t_all = time.time()
    cfg = paths.load_config(args.config)
    P = cfg["protocol"]
    reading = next(r for r in cfg["readings"] if r["name"] == (args.reading or cfg["readings"][0]["name"]))
    classes, K, seed = reading["labels"], len(reading["labels"]), int(P.get("seed", 0))
    C = args.C or (0.3 if reading["name"] == "emotion" else 1.0)
    out = paths.results_dir(cfg, "words", args.set)
    df = pd.read_csv(paths.cache_dir(cfg) / f"{args.set}.csv", dtype=str, keep_default_na=False)
    idx = {c: k for k, c in enumerate(classes)}
    y = np.array([idx.get(v, -1) for v in df[reading["name"]]]) if reading["name"] in df.columns else np.full(len(df), -1)
    keep = y >= 0
    df, y = df[keep].reset_index(drop=True), y[keep]
    ids, texts = df["id"].to_numpy(), df["text"].tolist()
    train_dir = paths.p("results", cfg["name"], "train")
    if args.set == "train" and (train_dir / "folds.csv").exists():
        conf, folds = network_split(train_dir, ids)
        how = "the network's confirmation split and folds"
    else:
        conf, folds = own_split(y, df["group"].to_numpy(), P, seed)
        how = f"an own grouped split of {float(P['confirmation_fraction']):.0%} and {P['folds']}-fold x {P['seeds']} seeds"
    dev = np.where(~conf)[0]
    pd.DataFrame({"id": ids[conf], reading["name"]: df[reading["name"]].to_numpy()[conf]}).to_csv(out / "confirmation_ids.csv", index=False)
    pd.concat([pd.DataFrame({"id": ids[va], "seed": s, "fold": f}) for s, f, _, va in folds]).to_csv(out / "folds.csv", index=False)
    log(f"{cfg['name']}/{args.set}, reading {reading['name']} ({K} classes): {len(df)} labelled rows, {len(dev)} development and {int(conf.sum())} confirmation by {how}; C {C}")

    runs = []
    for s, f, tr, va in folds:
        t0 = time.time()
        vocab = sorted({w for i in tr for w in words_of(texts[i])})
        index = {w: j for j, w in enumerate(vocab)}
        W, b, it = fit_logit(indicators([texts[i] for i in tr], index), y[tr], K, C, args.max_iter)
        Pv, cov = read(W, b, indicators([texts[i] for i in va], index))
        ev = score(y[va], Pv, cov, K)
        runs.append({"seed": s, "fold": f, "rows_train": int(len(tr)), "rows_valid": int(len(va)), "words": len(vocab), "iterations": it, "seconds": round(time.time() - t0, 1), **ev})
        log(f"  seed {s} fold {f}: macro-F1 {ev['macro_f1']:.4f} acc {ev['accuracy']:.4f}, {len(vocab)} words, {ev['na']} N/A, {it} iterations, {time.time() - t0:.0f} s")
    tab = pd.DataFrame(runs)
    tab.to_csv(out / "cv_runs.csv", index=False, float_format="%.8g")
    cv = {"runs": int(len(tab)), "C": C, "mean": {k: float(tab[k].mean()) for k in ("accuracy", "macro_f1")}, "sd": {k: (float(tab[k].std(ddof=1)) if len(tab) > 1 else 0.0) for k in ("accuracy", "macro_f1")}}
    log(f"cross-validation: macro-F1 {cv['mean']['macro_f1']:.4f} +/- {cv['sd']['macro_f1']:.4f}, accuracy {cv['mean']['accuracy']:.4f}")

    # the final fit on every development row, the word table, the confirmation score
    t0 = time.time()
    vocab = sorted({w for i in dev for w in words_of(texts[i])})
    index = {w: j for j, w in enumerate(vocab)}
    W, b, it = fit_logit(indicators([texts[i] for i in dev], index), y[dev], K, C, args.max_iter)
    log(f"final fit: {len(vocab)} words from {len(dev)} rows, {it} iterations, {time.time() - t0:.0f} s")
    table = trigger_words(vocab, W, b, classes)
    counts = pd.Series([w for i in dev for w in words_of(texts[i])]).value_counts()
    table["count"] = table["word"].map(counts).fillna(0).astype(int)
    trig = table[table["probability"] > 0.5].sort_values("probability", ascending=False)
    trig.to_csv(out / "trigger_words.csv", index=False, float_format="%.6f")
    Pc, cov = read(W, b, indicators([texts[i] for i in np.where(conf)[0]], index))
    yc = y[conf]
    pred = predict(Pc, cov)
    ev = score(yc, Pc, cov, K)
    boot = metrics.bootstrap_macro_f1(yc, pred, K, seed=seed)
    M = confusion_with_na(yc, pred, K)
    pd.DataFrame(M, index=[f"true {c}" for c in classes], columns=[f"pred {c}" for c in classes] + ["pred N/A"]).to_csv(out / "confusion.csv")
    confirmation = {"rows": int(conf.sum()), "metrics": ev, "macro_f1_ci": [boot["ci_low"], boot["ci_high"]], "recall": [float(M[k, k] / max(1, M[k].sum())) for k in range(K)], "confusion": M.tolist()}
    log(f"confirmation: macro-F1 {ev['macro_f1']:.4f} [{boot['ci_low']:.4f}, {boot['ci_high']:.4f}], accuracy {ev['accuracy']:.4f}, {ev['na']} of {ev['rows']} rows N/A; "
        f"{len(trig)} trigger words of {len(vocab)}")

    # zero-shot readings of every prediction set of a training-set model
    predictions = {}
    if args.set == "train":
        for s in sorted(p.stem for p in paths.cache_dir(cfg).glob("*.csv") if p.stem != "train"):
            dfs = pd.read_csv(paths.cache_dir(cfg) / f"{s}.csv", dtype=str, keep_default_na=False)
            Ps, covs = read(W, b, indicators(dfs["text"].tolist(), index))
            preds = predict(Ps, covs)
            sdir = out / s
            sdir.mkdir(exist_ok=True)
            tab_s = {"id": dfs["id"], "text": dfs["text"], f"{reading['name']}_reading": np.array(classes + ["N/A"])[np.where(preds < 0, K, preds)],
                     "confidence": np.where(covs, Ps.max(1), np.nan)}
            for k, c in enumerate(classes):
                tab_s[f"p_{c}"] = np.where(covs, Ps[:, k], np.nan)
            pd.DataFrame(tab_s).to_csv(sdir / "predictions.csv", index=False, float_format="%.5f")
            ys = np.array([idx.get(v, -1) for v in dfs[reading["name"]]]) if reading["name"] in dfs.columns else np.full(len(dfs), -1)
            ok = ys >= 0
            if ok.any():
                evs = score(ys[ok], Ps[ok], covs[ok], K)
                Ms = confusion_with_na(ys[ok], preds[ok], K)
                predictions[s] = {"labelled_rows": int(ok.sum()), **evs, "recall": [float(Ms[k, k] / max(1, Ms[k].sum())) for k in range(K)], "confusion": Ms.tolist()}
                (sdir / "metrics.json").write_text(json.dumps({"set": s, "reading": reading["name"], **predictions[s]}, indent=2), encoding="utf-8")
                log(f"{s}: {int(ok.sum())} labelled rows, accuracy {evs['accuracy']:.4f}, macro-F1 {evs['macro_f1']:.4f}, {evs['na']} N/A")

    minutes = (time.time() - t_all) / 60
    f5 = lambda a: [float(f"{v:.5g}") for v in a]
    model = {"config": cfg["name"], "set": args.set, "reading": reading["name"], "classes": classes, "pattern": WORD.pattern, "C": C, "penalty": "l2, intercepts unpenalised",
             "n_words": len(vocab), "n_trigger_words": int(len(trig)), "words": vocab, "intercept": f5(b), "coef": [f5(row) for row in W],
             "trigger_words": trig["word"].tolist(), "n_params": int(W.size + b.size)}
    summary = {"config": cfg["name"], "set": args.set, "reading": reading["name"], "classes": classes, "C": C, "split": how, "rows": int(len(df)), "rows_development": int(len(dev)),
               "rows_confirmation": int(conf.sum()), "n_words": len(vocab), "n_trigger_words": int(len(trig)), "n_params": model["n_params"], "cv": cv, "confirmation": confirmation,
               "predictions": predictions, "minutes": round(minutes, 1), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}
    (out / "words_model.json").write_text(json.dumps(model, separators=(",", ":")), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"done in {minutes:.1f} min, peak RSS {summary['peak_rss_mb']} MB -> {out}")

def confusion_with_na(y: np.ndarray, pred: np.ndarray, K: int) -> np.ndarray:
    """K rows by K + 1 columns, the last column the N/A readings."""
    M = np.zeros((K, K + 1), np.int64)
    np.add.at(M, (y, np.where(pred < 0, K, pred)), 1)
    return M

if __name__ == "__main__":
    main()

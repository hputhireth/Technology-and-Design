#!/usr/bin/env python3
"""linear: the control for the hidden layers. A ridge-penalised multinomial logistic regression on the same 2,048 standardised features, fitted by L-BFGS
on the network's own confirmation split and folds (read from results/<config>/train/), so the comparison is paired row for row.
C is chosen on the first two folds of seed 0 from {0.001, 0.003, 0.01, 0.03, 0.1}, the chosen C runs on every fold x seed, a temperature is fitted on the
out-of-fold logits, the final fit on every development row is scored once on the confirmation rows, and the corrected resampled t-test against the network's
runs is recorded. One linear head per reading.
    python scripts/linear.py --config finance
    python scripts/linear.py --config dialogue --threads 16
Writes $Root/results/<config>/linear/: linear_model.json, summary.json, cv_runs.csv, confirmation_ids.csv, folds.csv, confusion_<reading>.csv
and <set>/predictions.csv with metrics.json for every prediction set.
"""
from __future__ import annotations
import argparse
import json
import os
import resource
import sys
import time
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import head as heads
from common import metrics, paths, sets

GRID = [0.001, 0.003, 0.01, 0.03, 0.1]

def log(*a):
    print("[linear]", *a, flush=True)

def fit_logit(Z: np.ndarray, y: np.ndarray, K: int, C: float, max_iter: int = 1000):
    """Multinomial logit with an L2 penalty by L-BFGS, intercept unpenalised. Returns W [K, p] and b [K]."""
    from sklearn.linear_model import LogisticRegression
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = LogisticRegression(C=C, solver="lbfgs", max_iter=max_iter, tol=1e-5).fit(Z, y)
    W, b = np.zeros((K, Z.shape[1]), np.float64), np.zeros(K, np.float64)
    if len(m.classes_) == 2 and m.coef_.shape[0] == 1:
        W[m.classes_[1]], b[m.classes_[1]] = m.coef_[0], m.intercept_[0]
    else:
        W[m.classes_], b[m.classes_] = m.coef_, m.intercept_
    return W.astype(np.float32), b.astype(np.float32), int(np.max(m.n_iter_))

def logits_of(W, b, Z):
    return Z @ W.T + b

def read_folds(train_dir: Path, ids: np.ndarray) -> tuple[np.ndarray, list[tuple[int, int, np.ndarray, np.ndarray]]]:
    """The confirmation mask and the network's (seed, fold, train rows, validation rows), as row indices of the table."""
    conf_ids = set(pd.read_csv(train_dir / "confirmation_ids.csv", dtype=str)["id"])
    folds = pd.read_csv(train_dir / "folds.csv", dtype={"id": str})
    pos = {i: k for k, i in enumerate(ids)}
    conf = np.array([i in conf_ids for i in ids])
    dev = np.where(~conf)[0]
    out = []
    for (s, f), part in folds.groupby(["seed", "fold"], sort=True):
        va = np.array(sorted(pos[i] for i in part["id"]))
        tr = np.setdiff1d(dev, va)
        out.append((int(s), int(f), tr, va))
    return conf, out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--grid", type=float, nargs="+", default=None)
    ap.add_argument("--max-iter", type=int, default=1000)
    args = ap.parse_args()
    n_threads = args.threads or int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) or os.cpu_count() or 1
    os.environ.setdefault("OMP_NUM_THREADS", str(n_threads))
    t_all = time.time()
    cfg = paths.load_config(args.config)
    readings, P = cfg["readings"], cfg["protocol"]
    names, Ks = [r["name"] for r in readings], [len(r["labels"]) for r in readings]
    grid = args.grid or GRID
    train_dir = paths.results_dir(cfg, "train")
    out = paths.results_dir(cfg, "linear")
    seed = int(P.get("seed", 0))

    df, X, key = sets.load_set(cfg, "train")
    Y = sets.labels(df, readings)
    ids = df["id"].to_numpy()
    conf, folds = read_folds(train_dir, ids)
    dev = np.where(~conf)[0]
    log(f"{cfg['name']}: {len(df)} rows, {X.shape[1]} features; the network's split: {len(dev)} development rows, {int(conf.sum())} confirmation rows, {len(folds)} folds x seeds")
    pd.DataFrame({"id": ids[conf], **{n: df[n].to_numpy()[conf] for n in names}}).to_csv(out / "confirmation_ids.csv", index=False)
    pd.read_csv(train_dir / "folds.csv", dtype=str).to_csv(out / "folds.csv", index=False)
    net_runs = pd.read_csv(train_dir / "cv_runs.csv")

    runs, chosen, temps, W_final, b_final, cv, calibration, paired = [], {}, [], [], [], {}, {}, {}
    mean, sd, (Zd,) = heads.standardise(X[dev])
    for t, n in enumerate(names):
        y, K = Y[t], Ks[t]
        # the penalty on the first two folds of seed 0
        scores = {}
        for C in grid:
            f1s = []
            for s, f, tr, va in [x for x in folds if x[0] == 0][:2]:
                _, _, (Ztr, Zva) = heads.standardise(X[tr], X[va])
                W, b, _ = fit_logit(Ztr, y[tr], K, C, args.max_iter)
                f1s.append(metrics.macro_f1(y[va], logits_of(W, b, Zva).argmax(1), K))
            scores[C] = float(np.mean(f1s))
        C = max(scores, key=scores.get)
        chosen[n] = {"C": C, "macro_f1_on_two_folds": scores}
        log(f"{n}: C {C} chosen on two folds " + ", ".join(f"{c}: {v:.4f}" for c, v in scores.items()))
        # every fold x seed with the chosen C
        oof = np.zeros((len(folds), len(df), K), np.float32)
        oof_mask = np.zeros((len(folds), len(df)), bool)
        for j, (s, f, tr, va) in enumerate(folds):
            t0 = time.time()
            _, _, (Ztr, Zva) = heads.standardise(X[tr], X[va])
            W, b, it = fit_logit(Ztr, y[tr], K, C, args.max_iter)
            l = logits_of(W, b, Zva)
            oof[j, va], oof_mask[j, va] = l, True
            ev = metrics.evaluate(y[va], metrics.softmax(l))
            runs.append({"reading": n, "seed": s, "fold": f, "rows_train": int(len(tr)), "rows_valid": int(len(va)), "C": C, "iterations": it, "seconds": round(time.time() - t0, 1), **ev})
            log(f"  {n} seed {s} fold {f}: macro-F1 {ev['macro_f1']:.4f} acc {ev['accuracy']:.4f}, {it} iterations, {time.time() - t0:.0f} s")
        tab = pd.DataFrame([r for r in runs if r["reading"] == n])
        cv[n] = {"runs": int(len(tab)), "C": C, "mean": {k: float(tab[k].mean()) for k in ("accuracy", "macro_f1", "log_loss", "auc_ovr_macro", "ece_15")},
                 "sd": {k: (float(tab[k].std(ddof=1)) if len(tab) > 1 else 0.0) for k in ("accuracy", "macro_f1", "log_loss", "auc_ovr_macro", "ece_15")}}
        # paired against the network's runs, same seed and fold
        col = f"{n}_macro_f1"
        if col in net_runs.columns:
            m = tab.merge(net_runs[["seed", "fold", col, "rows_train", "rows_valid"]], on=["seed", "fold"], suffixes=("", "_net"))
            test = metrics.corrected_resampled_t(m[col], m["macro_f1"], int(m["rows_train"].mean()), int(m["rows_valid"].mean()))
            paired[n] = {"network_minus_linear": test, "network_cv_macro_f1": float(m[col].mean()), "linear_cv_macro_f1": float(m["macro_f1"].mean())}
            log(f"  {n}: network minus linear {test['mean_diff']:+.4f} [{test['ci_low']:+.4f}, {test['ci_high']:+.4f}], p {test['p']:.2g} over {test['runs']} paired runs")
        # temperature on the out-of-fold logits
        z, yy = oof[oof_mask], np.broadcast_to(y, oof_mask.shape)[oof_mask]
        T = metrics.fit_temperature(z, yy)
        temps.append(T)
        calibration[n] = {"temperature": T, "ece_before": metrics.ece(yy, metrics.softmax(z)), "ece_after": metrics.ece(yy, metrics.softmax(z / T))}
        log(f"  {n}: cross-validation macro-F1 {cv[n]['mean']['macro_f1']:.4f} +/- {cv[n]['sd']['macro_f1']:.4f}; temperature {T:.3f}, ECE {calibration[n]['ece_before']:.4f} -> {calibration[n]['ece_after']:.4f}")
        # the final fit on every development row
        t0 = time.time()
        W, b, it = fit_logit(Zd, y[dev], K, C, args.max_iter)
        W_final.append(W)
        b_final.append(b)
        log(f"  {n}: final fit on {len(dev)} rows, {it} iterations, {time.time() - t0:.0f} s")
    pd.DataFrame(runs).to_csv(out / "cv_runs.csv", index=False, float_format="%.8g")

    model = heads.MultiHead(X.shape[1], [], [], 0.0, Ks, 0.0)
    import torch
    for o, W, b in zip(model.outs, W_final, b_final):
        o.weight.data, o.bias.data = torch.from_numpy(W), torch.from_numpy(b)
    model.eval()

    # the confirmation rows, scored once, with the network's predictions on the same rows for the paired difference
    net = json.loads((train_dir / "nn_model.json").read_text(encoding="utf-8"))
    net_model = heads.from_json(net)
    net_temps = [tk["temperature"] for tk in net["tasks"]]
    Zc = ((X[conf] - mean) / sd).astype(np.float32)
    in_sample = {n: metrics.evaluate(Y[t][dev], Pt) for t, (n, Pt) in enumerate(zip(names, heads.predict_proba(model, Zd, temps)))}
    confirmation = {"rows": int(conf.sum())}
    Pn = heads.predict_proba(net_model, heads.standardise_with(net, X[conf]), net_temps)
    for t, (n, Pt) in enumerate(zip(names, heads.predict_proba(model, Zc, temps))):
        yc = Y[t][conf]
        ev = metrics.evaluate(yc, Pt)
        pred = Pt.argmax(1)
        boot = metrics.bootstrap_macro_f1(yc, pred, Ks[t], seed=seed)
        M = metrics.confusion(yc, pred, Ks[t])
        pd.DataFrame(M, index=[f"true {c}" for c in readings[t]["labels"]], columns=[f"pred {c}" for c in readings[t]["labels"]]).to_csv(out / f"confusion_{n}.csv")
        diff = paired_difference(yc, pred, Pn[t].argmax(1), Ks[t], seed)
        confirmation[n] = {"metrics": ev, "macro_f1_ci": [boot["ci_low"], boot["ci_high"]], "confusion": M.tolist(),
                           "recall": [float(M[k, k] / max(1, M[k].sum())) for k in range(Ks[t])], "linear_minus_network": diff}
        log(f"confirmation {n}: macro-F1 {ev['macro_f1']:.4f} [{boot['ci_low']:.4f}, {boot['ci_high']:.4f}], accuracy {ev['accuracy']:.4f}, ECE {ev['ece_15']:.4f}; "
            f"linear minus network {diff['difference']:+.4f} [{diff['ci_low']:+.4f}, {diff['ci_high']:+.4f}]")

    # every prediction set
    predictions = {}
    for s in sorted(p.stem for p in paths.cache_dir(cfg).glob("*.csv") if p.stem != "train"):
        dfs, Xs, _ = sets.load_set(cfg, s)
        Ys = sets.labels(dfs, readings)
        Ps = heads.predict_proba(model, ((Xs - mean) / sd).astype(np.float32), temps)
        Pns = heads.predict_proba(net_model, heads.standardise_with(net, Xs), net_temps)
        sdir = out / s
        sdir.mkdir(exist_ok=True)
        table = {"id": dfs["id"], "source_row": dfs["source_row"], "text": dfs["text"]}
        report = {"set": s, "rows": int(len(dfs)), "readings": {}}
        for t, (r, Pt) in enumerate(zip(readings, Ps)):
            pred = Pt.argmax(1)
            table[f"{r['name']}_reading"], table[f"{r['name']}_confidence"] = np.array(r["labels"])[pred], Pt.max(1)
            for k, c in enumerate(r["labels"]):
                table[f"p_{r['name']}_{c}"] = Pt[:, k]
            ok = Ys[t] >= 0
            if ok.any():
                ev = metrics.evaluate(Ys[t][ok], Pt[ok])
                M = metrics.confusion(Ys[t][ok], pred[ok], Ks[t])
                report["readings"][r["name"]] = {"labelled_rows": int(ok.sum()), **ev, "recall": [float(M[k, k] / max(1, M[k].sum())) for k in range(Ks[t])],
                                                 "confusion": M.tolist(), "linear_minus_network": paired_difference(Ys[t][ok], pred[ok], Pns[t][ok].argmax(1), Ks[t], seed)}
                log(f"{s} {r['name']}: {int(ok.sum())} labelled rows, accuracy {ev['accuracy']:.4f}, macro-F1 {ev['macro_f1']:.4f}")
        pd.DataFrame(table).to_csv(sdir / "predictions.csv", index=False, float_format="%.5f")
        if report["readings"]:
            (sdir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        predictions[s] = report

    minutes = (time.time() - t_all) / 60
    head_cfg = {"widths": [], "acts": [], "dropout": 0.0, "input_dropout": 0.0, "penalty": "l2", "solver": "lbfgs", "C": {n: chosen[n]["C"] for n in names}, "grid": grid}
    extra = {"set": "train", "rows": int(len(df)), "rows_development": int(len(dev)), "rows_confirmation": int(conf.sum()), "chosen": chosen, "cv": cv,
             "paired_with_network": paired, "calibration": calibration, "in_sample": in_sample, "confirmation": confirmation, "predictions": predictions,
             "feature_key": key, "minutes": round(minutes, 1), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}
    mj = heads.to_json(model, readings, mean, sd, temps, head_cfg, extra)
    (out / "linear_model.json").write_text(json.dumps(mj, separators=(",", ":")), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps({k: v for k, v in mj.items() if k not in ("mean", "sd", "trunk", "tasks")}, indent=2), encoding="utf-8")
    log(f"done in {minutes:.1f} min, peak RSS {extra['peak_rss_mb']} MB -> {out}")

def paired_difference(y, pred_a, pred_b, K: int, seed: int, n_boot: int = 1000) -> dict:
    """Macro-F1 of a minus b on the same rows with a percentile bootstrap interval."""
    rng = np.random.RandomState(seed)
    n = len(y)
    d = [metrics.macro_f1(y[i], pred_a[i], K) - metrics.macro_f1(y[i], pred_b[i], K) for i in (rng.randint(0, n, n) for _ in range(n_boot))]
    return {"difference": metrics.macro_f1(y, pred_a, K) - metrics.macro_f1(y, pred_b, K), "ci_low": float(np.percentile(d, 2.5)), "ci_high": float(np.percentile(d, 97.5))}

if __name__ == "__main__":
    main()

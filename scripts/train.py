#!/usr/bin/env python3
"""train: A confirmation split is held out by group before anything is fitted; the fixed configuration is trained on grouped folds x seeds
to measure the cross-validated scores and to pick the number of epochs; one temperature per reading is fitted on the out-of-fold logits. 
The head is then fitted once on every development row and scored once on the confirmation split, with a bootstrap interval on the macro-F1.
    python scripts/train.py --config finance
    python scripts/train.py --config dialogue --threads 16
Writes to $Root/results/<config>/train/: nn_model.json, summary.json, cv_runs.csv, confirmation_ids.csv, confusion_<reading>.csv.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import head as heads
from common import metrics, paths, sets, text  

METRICS = ["accuracy", "macro_f1", "log_loss", "auc_ovr_macro", "ece_15"]

def log(*a):
    print("[train]", *a, flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--folds", type=int, default=None)
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--max-epochs", type=int, default=None)
    ap.add_argument("--patience", type=int, default=None)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--max-rows", type=int, default=None)
    args = ap.parse_args()

    import torch
    torch.set_num_threads(args.threads or int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) or os.cpu_count() or 1)
    t_all = time.time()
    cfg = paths.load_config(args.config)
    H, P, readings = cfg["head"], cfg["protocol"], cfg["readings"]
    names, Ks = [r["name"] for r in readings], [len(r["labels"]) for r in readings]
    weights = list(H.get("task_weights", [1.0] * len(readings)))
    folds, seeds = args.folds or int(P["folds"]), args.seeds or int(P["seeds"])
    max_epochs, patience, seed = args.max_epochs or int(P["max_epochs"]), args.patience or int(P["patience"]), int(P.get("seed", 0))
    opt_cfg = {k: P[k] for k in ("warmup_epochs", "cosine_floor", "ema") if k in P}
    out = paths.results_dir(cfg, "train")

    df, X, key = sets.load_set(cfg, "train", args.max_rows)
    Y = sets.labels(df, readings)
    groups = df["group"].to_numpy()
    strat = Y[names.index(P["stratify_on"])] if P.get("stratify_on") in names else Y[0]
    dev, conf = text.confirmation_split(strat, groups, float(P["confirmation_fraction"]), seed)
    pd.DataFrame({"id": df["id"].to_numpy()[conf], **{n: df[n].to_numpy()[conf] for n in names}}).to_csv(out / "confirmation_ids.csv", index=False)
    log(f"{cfg['name']}: {len(df)} rows, {X.shape[1]} features, readings {names} with {Ks} classes; torch threads {torch.get_num_threads()}")
    log(f"confirmation split: {len(conf)} rows held out by group ({float(P['confirmation_fraction']):.0%}), {len(dev)} development rows; groups {len(set(groups))}")
    Xd, Yd, sd_, gd = X[dev], [y[dev] for y in Y], strat[dev], groups[dev]

    # grouped folds x seeds on the fixed configuration
    runs, oof = [], [np.zeros((seeds, len(dev), K), np.float32) for K in Ks]
    for s in range(seeds):
        for f, (tr, va) in enumerate(text.grouped_folds(sd_, gd, folds, seed + s)):
            _, _, (Ztr, Zva) = heads.standardise(Xd[tr], Xd[va])
            r = heads.fit(Ztr, [y[tr] for y in Yd], Zva, [y[va] for y in Yd], H, Ks, seed + 1000 * f + 17 * s, max_epochs, patience,
                          opt_cfg=opt_cfg, horizon_epochs=max_epochs, weights=weights)
            row = {"seed": s, "fold": f + 1, "rows_train": int(len(tr)), "rows_valid": int(len(va)), "best_epoch": r["best_epoch"], "seconds": round(r["seconds"], 1)}
            f1s = []
            for t, logits in enumerate(heads.predict_logits(r["model"], Zva)):
                oof[t][s, va] = logits
                ev = metrics.evaluate(Yd[t][va], metrics.softmax(logits))
                row.update({f"{names[t]}_{k}": v for k, v in ev.items()})
                f1s.append(ev["macro_f1"])
            row["score"] = float(np.mean(f1s))
            runs.append(row)
            log(f"  seed {s} fold {f + 1}: " + ", ".join(f"{n} F1 {row[n + '_macro_f1']:.4f} acc {row[n + '_accuracy']:.4f}" for n in names)
                + f", best epoch {r['best_epoch']}, {r['seconds']:.0f} s")
    tab = pd.DataFrame(runs)
    tab.to_csv(out / "cv_runs.csv", index=False, float_format="%.6g")
    epochs = max(3, int(round(float(np.median(tab["best_epoch"])))))
    cv = {"folds": folds, "seeds": seeds, "runs": len(runs), "epochs_median": epochs, "score_mean": float(tab["score"].mean()), "score_sd": float(tab["score"].std(ddof=1)) if len(tab) > 1 else 0.0,
          "seed_means": [float(tab[tab["seed"] == s]["score"].mean()) for s in range(seeds)]}
    for n in names:
        cv[n] = {"mean": {k: float(tab[f"{n}_{k}"].mean()) for k in METRICS}, "sd": {k: (float(tab[f"{n}_{k}"].std(ddof=1)) if len(tab) > 1 else 0.0) for k in METRICS}}
        log(f"cross-validation {n}: macro-F1 {cv[n]['mean']['macro_f1']:.4f} +/- {cv[n]['sd']['macro_f1']:.4f}, accuracy {cv[n]['mean']['accuracy']:.4f}, log-loss {cv[n]['mean']['log_loss']:.4f}")
    log(f"median best epoch {epochs}")

    # one temperature per reading, on the out-of-fold logits
    temps, calibration = [], {}
    for t, n in enumerate(names):
        z, y = oof[t].reshape(-1, Ks[t]), np.tile(Yd[t], seeds)
        T = metrics.fit_temperature(z, y)
        temps.append(T)
        calibration[n] = {"temperature": T, "ece_before": metrics.ece(y, metrics.softmax(z)), "ece_after": metrics.ece(y, metrics.softmax(z / T))}
        log(f"temperature {n} {T:.3f}: ECE {calibration[n]['ece_before']:.4f} -> {calibration[n]['ece_after']:.4f}")

    # the final fit on every development row, then the one-time confirmation score
    mean, sd, (Zd,) = heads.standardise(Xd)
    final = heads.fit(Zd, Yd, None, None, H, Ks, seed, epochs, patience, opt_cfg=opt_cfg, horizon_epochs=max_epochs, weights=weights)
    model = final["model"]
    in_sample = {n: metrics.evaluate(Yd[t], Pt) for t, (n, Pt) in enumerate(zip(names, heads.predict_proba(model, Zd, temps)))}
    log(f"final fit: {epochs} epochs on {len(dev)} rows in {final['seconds']:.0f} s; in-sample " + ", ".join(f"{n} F1 {in_sample[n]['macro_f1']:.4f}" for n in names))
    confirmation = {"rows": int(len(conf))}
    if len(conf):
        Zc = ((X[conf] - mean) / sd).astype(np.float32)
        for t, (n, Pt) in enumerate(zip(names, heads.predict_proba(model, Zc, temps))):
            yc = Y[t][conf]
            ev = metrics.evaluate(yc, Pt)
            boot = metrics.bootstrap_macro_f1(yc, Pt.argmax(1), Ks[t], seed=seed)
            M = metrics.confusion(yc, Pt.argmax(1), Ks[t])
            pd.DataFrame(M, index=[f"true {c}" for c in readings[t]["labels"]], columns=[f"pred {c}" for c in readings[t]["labels"]]).to_csv(out / f"confusion_{n}.csv")
            confirmation[n] = {"metrics": ev, "macro_f1_ci": [boot["ci_low"], boot["ci_high"]], "confusion": M.tolist(),
                               "cv_interval_covers": bool(abs(ev["macro_f1"] - cv[n]["mean"]["macro_f1"]) <= 2 * cv[n]["sd"]["macro_f1"])}
            log(f"confirmation {n}: macro-F1 {ev['macro_f1']:.4f} [{boot['ci_low']:.4f}, {boot['ci_high']:.4f}], accuracy {ev['accuracy']:.4f}, log-loss {ev['log_loss']:.4f}, ECE {ev['ece_15']:.4f}"
                + ("; the cross-validation band covers it" if confirmation[n]["cv_interval_covers"] else "; outside the cross-validation band"))

    minutes = (time.time() - t_all) / 60
    protocol = (f"{len(dev)} development rows and {len(conf)} confirmation rows held out first by group. Grouped {folds}-fold cross-validation with {seeds} seeds "
                f"on the fixed configuration, every fold standardised with its own training rows; AdamW, warm-up {opt_cfg.get('warmup_epochs', 1)} epoch, cosine decay to "
                f"{opt_cfg.get('cosine_floor', 0.1)} of the rate, EMA {opt_cfg.get('ema', 0)}, early stopping on validation cross-entropy (patience {patience}, at most {max_epochs} epochs), "
                f"label smoothing {H.get('smoothing', 0)}. Final fit of {epochs} epochs (the median best epoch) on the development rows. One temperature per reading fitted on the out-of-fold logits.")
    extra = {"set": "train", "rows": int(len(df)), "rows_development": int(len(dev)), "rows_confirmation": int(len(conf)),
             "class_counts": {n: {c: int((Y[t] == k).sum()) for k, c in enumerate(readings[t]["labels"])} for t, n in enumerate(names)},
             "epochs_final": epochs, "cv": cv, "calibration": calibration, "in_sample": in_sample, "confirmation": confirmation,
             "optimiser": dict(opt_cfg, batch=H.get("batch", 256), max_epochs=max_epochs, patience=patience), "protocol": protocol,
             "feature_key": key, "minutes": round(minutes, 1), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}
    mj = heads.to_json(model, readings, mean, sd, temps, H, extra)
    (out / "nn_model.json").write_text(json.dumps(mj, separators=(",", ":")), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps({k: v for k, v in mj.items() if k not in ("mean", "sd", "trunk", "tasks")}, indent=2), encoding="utf-8")
    log(f"done in {minutes:.1f} min, peak RSS {extra['peak_rss_mb']} MB -> {out}")

if __name__ == "__main__":
    main()

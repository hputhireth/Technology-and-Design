#!/usr/bin/env python3
"""predict: a trained head on every prediction set of its config from the cached features. 
Writes one row per text with every reading's label and probabilities, and scores a set wherever it carries labels.
    python scripts/predict.py --config finance
    python scripts/predict.py --config dialogue --sets sentfin --model path/to/nn_model.json
Writes $COS_ROOT/results/<config>/<set>/predictions.csv and, for labelled sets, metrics.json and confusion_<reading>.csv.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import head as heads
from common import metrics, paths, sets

def log(*a):
    print("[predict]", *a, flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--sets", nargs="+", default=None, help="default: every prepared set except train")
    ap.add_argument("--model", default=None, help="default: results/<config>/train/nn_model.json")
    ap.add_argument("--out", default=None, help="results folder name for the predictions (default: the set's name)")
    args = ap.parse_args()
    t_all = time.time()
    cfg = paths.load_config(args.config)
    mpath = Path(args.model) if args.model else paths.results_dir(cfg, "train") / "nn_model.json"
    mj = json.loads(mpath.read_text(encoding="utf-8"))
    model = heads.from_json(mj)
    temps = [t["temperature"] for t in mj["tasks"]]
    readings = [{"name": t["name"], "labels": t["classes"]} for t in mj["tasks"]]
    names = [r["name"] for r in readings]
    names_available = sorted(p.stem for p in paths.cache_dir(cfg).glob("*.csv") if p.stem != "train")
    for s in args.sets or names_available:
        df, X, _ = sets.load_set(cfg, s)
        Z = heads.standardise_with(mj, X)
        Ps = heads.predict_proba(model, Z, temps)
        Y = sets.labels(df, readings)
        out = paths.results_dir(cfg, args.out or s)
        table = {"id": df["id"], "source_row": df["source_row"], "text": df["text"]}
        report = {"set": s, "rows": int(len(df)), "model": str(mpath), "readings": {}}
        for t, (r, P) in enumerate(zip(readings, Ps)):
            pred = P.argmax(1)
            table[f"{r['name']}_reading"] = np.array(r["labels"])[pred]
            table[f"{r['name']}_confidence"] = P.max(1)
            if r["name"] in df.columns:
                table[f"{r['name']}_label"] = df[r["name"]]
            for k, c in enumerate(r["labels"]):
                table[f"p_{r['name']}_{c}"] = P[:, k]
            ok = Y[t] >= 0
            if ok.any():
                ev = metrics.evaluate(Y[t][ok], P[ok])
                M = metrics.confusion(Y[t][ok], pred[ok], len(r["labels"]))
                pd.DataFrame(M, index=[f"true {c}" for c in r["labels"]], columns=[f"pred {c}" for c in r["labels"]]).to_csv(out / f"confusion_{r['name']}.csv")
                report["readings"][r["name"]] = {"labelled_rows": int(ok.sum()), **ev, "macro_f1_ci": [v for k, v in metrics.bootstrap_macro_f1(Y[t][ok], pred[ok], len(r["labels"])).items() if k in ("ci_low", "ci_high")],
                                                 "recall": [float(M[k, k] / max(1, M[k].sum())) for k in range(len(r["labels"]))], "confusion": M.tolist()}
                log(f"{s} {r['name']}: {int(ok.sum())} labelled rows, accuracy {ev['accuracy']:.4f}, macro-F1 {ev['macro_f1']:.4f}, log-loss {ev['log_loss']:.4f}, ECE {ev['ece_15']:.4f}, "
                    f"recall " + " / ".join(f"{v:.2f}" for v in report["readings"][r["name"]]["recall"]))
            else:
                called = sorted(((float((pred == k).mean()), c) for k, c in enumerate(r["labels"])), reverse=True)[:5]
                log(f"{s} {r['name']}: {len(df)} rows predicted, no labels to score; most called " + ", ".join(f"{c} {v:.1%}" for v, c in called))
        pd.DataFrame(table).to_csv(out / "predictions.csv", index=False, float_format="%.5f")
        if report["readings"]:
            (out / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"done in {time.time() - t_all:.1f} s")

if __name__ == "__main__":
    main()

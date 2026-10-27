#!/usr/bin/env python3
"""adapt: move a trained head to a new corpus without losing what it knows. 
The update is the closed form of the leashed objective, maximise reward minus beta x KL(policy || starting head):
on every labelled row of the new corpus the target is the starting head's distribution tilted towards the label, softmax(log pi_ref + onehot(y) / beta), and the head is fitted to it by
cross-entropy. A retention term, the forward KL of every reading on the head's own training rows, holds its old readings.
    python scripts/adapt.py --config finance --adapt-set sentfin
    python scripts/adapt.py --config dialogue --adapt-config finance --adapt-set train --transfer-set sentfin
    python scripts/adapt.py --config dialogue --model results/dialogue/adapt/finance_train/nn_model.json --adapt-config finance --adapt-set sentfin

Half of the new corpus is held out by group (--holdout). 
The head's own confirmation rows (results/<config>/train/confirmation_ids.csv) score retention; its development rows feed the retention term. 
Writes $Root/results/<config>/adapt/<run>/: nn_model.json, summary.json, adapt_log.csv (every epoch), predictions_<set>.csv (every row before and after), weight_changes.csv.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
import resource
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import head as heads
from common import metrics, paths, sets, text

def log(*a):
    print("[adapt]", *a, flush=True)

def kl_rows(logp: torch.Tensor, logq: torch.Tensor) -> torch.Tensor:
    """KL(p || q) per row from log-probabilities, exact over the classes."""
    return (logp.exp() * (logp - logq)).sum(1)

def logits_of(model, z: torch.Tensor, temps: list[float]) -> list[torch.Tensor]:
    return [l / T for l, T in zip(model(z), temps)]

def probs_of(model, Z: np.ndarray, temps: list[float]) -> list[np.ndarray]:
    return heads.predict_proba(model, Z, temps)

def held_mask(cfg_adapt: dict, df: pd.DataFrame, y: np.ndarray, groups: np.ndarray, name: str, fraction: float, seed: int) -> tuple[np.ndarray, str]:
    cid = paths.p("results", cfg_adapt["name"], "train", "confirmation_ids.csv")
    if name == "train" and cid.exists():
        ids = set(pd.read_csv(cid, dtype=str)["id"])
        return df["id"].isin(ids).to_numpy(), f"the {len(ids)} confirmation rows of the {cfg_adapt['name']} head"
    k = max(2, int(round(1.0 / fraction)))
    _, held = text.grouped_folds(y, groups, k, seed)[0]
    m = np.zeros(len(df), bool)
    m[held] = True
    return m, f"a grouped split of {fraction:.0%} ({int(m.sum())} rows), seed {seed}"

def score(P: np.ndarray, Pr: np.ndarray, y: np.ndarray, K: int) -> dict:
    pred = P.argmax(1)
    return {"accuracy": float((pred == y).mean()), "macro_f1": metrics.macro_f1(y, pred, K),
            "recall": [float(((pred == k) & (y == k)).sum() / max(1, (y == k).sum())) for k in range(K)],
            "kl_to_start": float((P * (np.log(np.clip(P, 1e-12, 1)) - np.log(np.clip(Pr, 1e-12, 1)))).sum(1).mean()),
            "entropy": float(-(P * np.log(np.clip(P, 1e-12, 1))).sum(1).mean())}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="the config the head was trained under; its training set is the home corpus")
    ap.add_argument("--model", default=None, help="nn_model.json to start from (default: results/<config>/train/nn_model.json)")
    ap.add_argument("--adapt-config", default=None, help="config whose cache holds the new corpus (default: --config)")
    ap.add_argument("--adapt-set", required=True, help="a prepared set of that config, e.g. sentfin, or train")
    ap.add_argument("--transfer-config", default=None)
    ap.add_argument("--transfer-set", default=None, help="a set scored before and after, never trained on")
    ap.add_argument("--holdout", type=float, default=None)
    ap.add_argument("--beta", type=float, default=None)
    ap.add_argument("--retain", type=float, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--run", default=None, help="output folder name (default: <adapt config>_<adapt set>)")
    args = ap.parse_args()
    torch.set_num_threads(args.threads or int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) or os.cpu_count() or 1)
    t_all = time.time()
    cfg = paths.load_config(args.config)
    A = dict(cfg.get("adapt", {}))
    beta, retain = args.beta or float(A.get("beta", 0.3)), args.retain if args.retain is not None else float(A.get("retain", 1.0))
    epochs, lr, batch = args.epochs or int(A.get("epochs", 20)), args.lr or float(A.get("lr", 3e-4)), args.batch or int(A.get("batch", 256))
    retain_batch, holdout = int(A.get("retain_batch", 256)), args.holdout or float(A.get("holdout", 0.5))
    cfg_adapt = paths.load_config(args.adapt_config) if args.adapt_config else cfg
    mpath = Path(args.model) if args.model else paths.results_dir(cfg, "train") / "nn_model.json"
    mj = json.loads(mpath.read_text(encoding="utf-8"))
    readings = [{"name": t["name"], "labels": t["classes"]} for t in mj["tasks"]]
    names, Ks, temps = [r["name"] for r in readings], [len(r["labels"]) for r in readings], [float(t["temperature"]) for t in mj["tasks"]]
    K = Ks[0]
    run = args.run or f"{cfg_adapt['name']}_{args.adapt_set}"
    out = paths.results_dir(cfg, "adapt", run)
    rng = np.random.RandomState(args.seed)
    torch.manual_seed(args.seed)

    # the new corpus, standardised with the head's own mean and sd
    df, X, _ = sets.load_set(cfg_adapt, args.adapt_set)
    ya = sets.labels(df, readings[:1])[0]
    keep = ya >= 0
    df, Za, ya = df[keep].reset_index(drop=True), heads.standardise_with(mj, X[keep]), ya[keep]
    held, how = held_mask(cfg_adapt, df, ya, df["group"].to_numpy(), args.adapt_set, holdout, args.seed)
    tr = np.where(~held)[0]
    log(f"{cfg_adapt['name']}/{args.adapt_set}: {len(df)} labelled rows; held out = {how}; training on the other {len(tr)}")

    # the home corpus: confirmation rows score retention, development rows feed the retention term
    dfh, Xh, _ = sets.load_set(cfg, "train")
    Yh = sets.labels(dfh, readings)
    Zh = heads.standardise_with(mj, Xh)
    cid = paths.results_dir(cfg, "train") / "confirmation_ids.csv"
    conf = dfh["id"].isin(set(pd.read_csv(cid, dtype=str)["id"])).to_numpy() if cid.exists() else np.zeros(len(dfh), bool)
    dev_rows = np.where(~conf)[0]
    log(f"home corpus {cfg['name']}/train: {int(conf.sum())} confirmation rows for the retention scores, {len(dev_rows)} development rows for the retention term")

    transfer = None
    if args.transfer_set:
        cfg_t = paths.load_config(args.transfer_config) if args.transfer_config else cfg_adapt
        dft, Xt, _ = sets.load_set(cfg_t, args.transfer_set)
        yt = sets.labels(dft, readings[:1])[0]
        ok = yt >= 0
        cidt = paths.p("results", cfg_t["name"], "train", "confirmation_ids.csv")
        if args.transfer_set == "train" and cidt.exists():
            ok &= dft["id"].isin(set(pd.read_csv(cidt, dtype=str)["id"])).to_numpy()
        transfer = {"name": f"{cfg_t['name']}/{args.transfer_set}", "Z": heads.standardise_with(mj, Xt[ok]), "y": yt[ok]}
        log(f"transfer set {transfer['name']}: {int(ok.sum())} labelled rows, scored but never trained on")

    ref = heads.from_json(mj)
    for p_ in ref.parameters():
        p_.requires_grad_(False)
    pol = copy.deepcopy(ref)
    for p_ in pol.parameters():
        p_.requires_grad_(True)
    opt = torch.optim.AdamW(pol.parameters(), lr=lr, weight_decay=0.0)
    Za_t, Zh_t = torch.from_numpy(Za), torch.from_numpy(Zh)
    steps_per_epoch = max(1, int(np.ceil(len(tr) / batch)))
    log(f"exact update: beta {beta}, retention {retain}, {epochs} epochs of {steps_per_epoch} steps, batch {batch}, AdamW {lr}; {pol.n_params():,} weights")

    def evaluate() -> dict:
        res = {}
        P, Pr = probs_of(pol, Za[held], temps)[0], probs_of(ref, Za[held], temps)[0]
        res["held"] = score(P, Pr, ya[held], K)
        if transfer is not None:
            res["transfer"] = score(probs_of(pol, transfer["Z"], temps)[0], probs_of(ref, transfer["Z"], temps)[0], transfer["y"], K)
        if conf.any():
            Ps, Prs = probs_of(pol, Zh[conf], temps), probs_of(ref, Zh[conf], temps)
            home = {}
            for t, n in enumerate(names):
                yk = Yh[t][conf]
                ok = yk >= 0
                home[n] = score(Ps[t][ok], Prs[t][ok], yk[ok], Ks[t])
            res["home"] = home
        return res

    def flat(res: dict) -> dict:
        row = {}
        for part, d in res.items():
            if part == "home":
                for n, dd in d.items():
                    row.update({f"home_{n}_{k}": v for k, v in dd.items() if k != "recall"})
            else:
                row.update({f"{part}_{k}": v for k, v in d.items() if k != "recall"})
                row.update({f"{part}_recall_{i}": v for i, v in enumerate(d["recall"])})
        return row

    def report(step: int, res: dict):
        h = res["held"]
        msg = f"  epoch {step / steps_per_epoch:4.1f}: held-out acc {h['accuracy']:.4f} F1 {h['macro_f1']:.4f} KL {h['kl_to_start']:.4f} entropy {h['entropy']:.3f}"
        if "transfer" in res:
            msg += f" | transfer acc {res['transfer']['accuracy']:.4f}"
        if "home" in res:
            msg += " | home " + ", ".join(f"{n} acc {d['accuracy']:.4f} F1 {d['macro_f1']:.4f}" for n, d in res["home"].items())
        log(msg)

    before = evaluate()
    report(0, before)
    history = [{"step": 0, "epoch": 0.0, **flat(before)}]
    step = 0
    for epoch in range(1, epochs + 1):
        pol.train()
        perm = rng.permutation(tr)
        for i in range(0, len(perm), batch):
            idx = perm[i:i + batch]
            step += 1
            opt.zero_grad()
            ls = logits_of(pol, Za_t[idx], temps)
            logp = torch.log_softmax(ls[0], 1)
            with torch.no_grad():
                logpr = torch.log_softmax(logits_of(ref, Za_t[idx], temps)[0], 1)
            onehot = torch.zeros_like(logpr)
            onehot[torch.arange(len(idx)), torch.from_numpy(ya[idx])] = 1.0
            target = torch.softmax(logpr + onehot / beta, 1)
            loss = -(target * logp).sum(1).mean()
            kl_ret = torch.zeros(())
            if retain > 0 and len(dev_rows):
                ridx = rng.choice(dev_rows, min(retain_batch, len(dev_rows)), replace=False)
                lh = logits_of(pol, Zh_t[ridx], temps)
                with torch.no_grad():
                    lhr = logits_of(ref, Zh_t[ridx], temps)
                kl_ret = sum(kl_rows(torch.log_softmax(r_, 1), torch.log_softmax(p_, 1)).mean() for r_, p_ in zip(lhr, lh))
                loss = loss + retain * kl_ret
            loss.backward()
            torch.nn.utils.clip_grad_norm_(pol.parameters(), 1.0)
            opt.step()
        pol.eval()
        res = evaluate()
        report(step, res)
        history.append({"step": step, "epoch": float(epoch), "loss": float(loss.detach()), "kl_retain": float(kl_ret.detach()), **flat(res)})
    after = res if epochs else before
    minutes = (time.time() - t_all) / 60
    pd.DataFrame(history).to_csv(out / "adapt_log.csv", index=False, float_format="%.6g")

    # new corpus before and after
    Pb, Pa = probs_of(ref, Za, temps), probs_of(pol, Za, temps)
    classes = np.array(readings[0]["labels"])
    pred_b, pred_a = Pb[0].argmax(1), Pa[0].argmax(1)
    table = {"id": df["id"], "held_out": held.astype(int), "text": df["text"], "label": classes[ya],
             "reading_before": classes[pred_b], "confidence_before": Pb[0].max(1), "reading_after": classes[pred_a], "confidence_after": Pa[0].max(1),
             "right_before": (pred_b == ya).astype(int), "right_after": (pred_a == ya).astype(int), "changed": (pred_b != pred_a).astype(int)}
    for t in range(1, len(readings)):
        lab = np.array(readings[t]["labels"])
        table[f"{names[t]}_before"], table[f"{names[t]}_after"] = lab[Pb[t].argmax(1)], lab[Pa[t].argmax(1)]
    pd.DataFrame(table).to_csv(out / f"predictions_{args.adapt_set}.csv", index=False, float_format="%.4f")

    # how much of the head moved
    rows = []
    for (k, b), a in zip(ref.state_dict().items(), pol.state_dict().values()):
        d = (a - b).abs()
        rows.append({"tensor": k, "n": int(d.numel()), "moved_over_1e-4": float((d > 1e-4).float().mean()), "mean_abs_change": float(d.mean()),
                     "max_abs_change": float(d.max()), "relative_change": float(d.norm() / (b.norm() + 1e-12))})
    pd.DataFrame(rows).to_csv(out / "weight_changes.csv", index=False, float_format="%.6g")

    design = {"method": "exact closed form of the leashed objective", "beta": beta, "retain": retain, "epochs": epochs, "steps": step, "lr": lr, "batch": batch,
              "retain_batch": retain_batch, "seed": args.seed, "started_from": str(mpath), "adapt_set": f"{cfg_adapt['name']}/{args.adapt_set}",
              "rows_trained_on": int(len(tr)), "rows_held_out": int(held.sum()), "held_out": how, "transfer_set": transfer["name"] if transfer else None,
              "minutes": round(minutes, 1), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}
    summary = {"adapted": design, "before": before, "after": after, "weights_moved_share": float(np.mean([r["moved_over_1e-4"] for r in rows]))}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    mean, sd = np.array(mj["mean"], np.float32), np.array(mj["sd"], np.float32)
    extra = {k: mj[k] for k in ("set", "rows", "class_counts", "protocol") if k in mj}
    extra.update({"adapted": design, "scores_before": before, "scores_after": after})
    (out / "nn_model.json").write_text(json.dumps(heads.to_json(pol, readings, mean, sd, temps, mj["config"], extra), separators=(",", ":")), encoding="utf-8")
    h0, h1 = before["held"], after["held"]
    log(f"held-out {h0['accuracy']:.4f} -> {h1['accuracy']:.4f} (macro-F1 {h0['macro_f1']:.4f} -> {h1['macro_f1']:.4f}, KL {h1['kl_to_start']:.3f})"
        + (f"; transfer {before['transfer']['accuracy']:.4f} -> {after['transfer']['accuracy']:.4f}" if transfer else "")
        + ("; home " + ", ".join(f"{n} {before['home'][n]['macro_f1']:.4f} -> {after['home'][n]['macro_f1']:.4f}" for n in names) if "home" in before else ""))
    log(f"done in {minutes:.1f} min, peak RSS {design['peak_rss_mb']} MB -> {out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""prepare: read the training file and every prediction file of a config, clean the text, put the labels of every reading on their configured names, 
fold exact duplicates of the training set, give every row a group and write one table per set to $Root/data/cache/<config>/.
    python scripts/prepare.py --config finance
    python scripts/prepare.py --config dialogue
Rows of the training set whose label is unknown are dropped.
"""
from __future__ import annotations
import argparse
import glob
import json
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import paths, text

def log(*a):
    print("[prepare]", *a, flush=True)

def set_name(path: Path) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")
    return s if s and s != "train" else f"set_{s or 'x'}"

def prediction_files(cfg: dict) -> list[Path]:
    train = paths.resolve(cfg["train_file"]).resolve()
    out = []
    for pat in cfg.get("predict_files", []):
        for h in sorted(glob.glob(str(paths.resolve(pat)))):
            if Path(h).resolve() != train and Path(h).suffix.lower() in (".csv", ".tsv", ".txt"):
                out.append(Path(h))
    return out

def groups_for(df: pd.DataFrame, cfg: dict) -> tuple[np.ndarray, str]:
    g = cfg.get("group", {"by": "near_duplicates"})
    if g.get("by") == "column":
        col = g["col"]
        if col in df.columns and (df[col].astype(str).str.len() > 0).all():
            return df[col].astype(str).to_numpy(), f"the {col} column"
        run_of = g.get("fallback_runs_of")
        if run_of and run_of in df.columns and (df[run_of].astype(str).str.len() > 0).any():
            return text.run_keys(df[run_of].to_numpy()), f"runs of consecutive rows with the same {run_of} (no usable {col} column)"
    return text.near_duplicate_keys(df["text"].tolist()), "near-duplicate text"

def prepare(path: Path, cfg: dict, name: str, is_train: bool) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8", sep="\t" if path.suffix.lower() == ".tsv" else ",")
    tcol = cfg.get("text_col", "text") if cfg.get("text_col", "text") in raw.columns else "text"
    if tcol not in raw.columns:
        raise SystemExit(f"{path}: no text column ({cfg.get('text_col', 'text')})")
    df = pd.DataFrame({"source_row": np.arange(len(raw)), "text": raw[tcol].map(text.clean_text)})
    n_moji = int((raw[tcol].map(text.fix_mojibake) != raw[tcol]).sum())
    for r in cfg["readings"]:
        df[r["name"]] = text.normalise_labels(raw[r["col"]], r) if r["col"] in raw.columns else ""
    for col in (c for c in ("conv_id", cfg.get("group", {}).get("col")) if c and c in raw.columns):
        df[col] = raw[col]
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    note = {"file": str(path), "rows_read": int(len(raw)), "mojibake_repairs": n_moji}
    if is_train:
        labelled = np.all([(df[r["name"]] != "").to_numpy() for r in cfg["readings"]], axis=0)
        note["rows_without_a_known_label"] = int((~labelled).sum())
        df = df[labelled].reset_index(drop=True)
        key = df["text"].map(text.norm_key)
        first = cfg["readings"][0]["name"]
        note["duplicate_texts_folded"] = int(key.duplicated().sum())
        note["duplicates_with_conflicting_labels"] = int((df.groupby(key)[first].nunique() > 1).sum())
        df = df.assign(dup_count=key.map(key.value_counts()).astype(int))
        df = df[~key.duplicated(keep="first")].reset_index(drop=True)
    groups, how = groups_for(df, cfg)
    df["group"] = groups
    df.insert(0, "id", [f"{name}_{i:07d}" for i in range(len(df))])
    sizes = pd.Series(groups).value_counts()
    note.update({"rows_kept": int(len(df)), "groups": int(len(sizes)), "largest_group": int(sizes.max()), "grouped_by": how,
                 "label_counts": {r["name"]: {k: int(v) for k, v in df[r["name"]].value_counts().items() if k != ""} for r in cfg["readings"]}})
    return df, note

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    t0 = time.time()
    cfg = paths.load_config(args.config)
    cdir = paths.cache_dir(cfg)
    files = [("train", paths.resolve(cfg["train_file"]), True)] + [(set_name(f), f, False) for f in prediction_files(cfg)]
    notes = {}
    for name, path, is_train in files:
        if not path.exists():
            raise SystemExit(f"{name}: file not found: {path}")
        df, note = prepare(path, cfg, name, is_train)
        df.to_csv(cdir / f"{name}.csv", index=False)
        notes[name] = note
        log(f"{name}: {note['rows_read']} rows read, {note['rows_kept']} kept, {note['mojibake_repairs']} mojibake repairs"
            + (f", {note['duplicate_texts_folded']} duplicates folded ({note['duplicates_with_conflicting_labels']} with conflicting labels, first kept)" if is_train else "")
            + f"; {note['groups']} groups by {how_short(note['grouped_by'])}, largest {note['largest_group']}; labels {note['label_counts']}")
    (cdir / "prepared.json").write_text(json.dumps({"config": cfg["name"], "sets": notes, "seconds": round(time.time() - t0, 1)}, indent=2), encoding="utf-8")
    log(f"written to {cdir} in {time.time() - t0:.1f} s")

def how_short(s: str) -> str:
    return s.split(" (")[0]

if __name__ == "__main__":
    main()

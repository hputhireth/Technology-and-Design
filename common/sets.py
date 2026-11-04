"""Prepared table with respective cached features, rows aligned by id, and labels as class indices."""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import cache, encoder, paths

def feature_key(cfg: dict, texts: list[str], dtype: str) -> str:
    wd, td = encoder.digests(cfg["encoder"])
    return cache.feature_key(wd, td, cache.sha256_column(texts), "cls_mean", cfg["max_len"], dtype, f"chunk{int(cfg.get('chunk_overlap', 32))}")

def load_set(cfg: dict, name: str, max_rows: int | None = None):
    """The table and its features as float32. The features were computed in fp16 on a GPU or in fp32 on a CPU; whichever exists is used, but the GPU one first."""
    df = pd.read_csv(paths.cache_dir(cfg) / f"{name}.csv", dtype=str, keep_default_na=False)
    if max_rows:
        df = df.head(max_rows)
    texts = df["text"].tolist()
    found = None
    for dtype in ("fp16", "fp32"):
        key = feature_key(cfg, texts, dtype)
        found = cache.load_features(key)
        if found is not None:
            break
    if found is None:
        raise SystemExit(f"no cached features for {cfg['name']}/{name}: run scripts/encode.py --config {cfg['name']} --sets {name}")
    X, ids = found
    pos = {i: k for k, i in enumerate(ids)}
    missing = [i for i in df["id"] if i not in pos]
    if missing:
        raise SystemExit(f"features for {name} do not cover the table (e.g. {missing[0]}): rerun encode.py --force")
    return df, X[[pos[i] for i in df["id"]]].astype(np.float32), key

def labels(df: pd.DataFrame, readings: list[dict]) -> list[np.ndarray]:
    """One integer array per reading, -1 where the row carries no known label."""
    out = []
    for r in readings:
        idx = {c: k for k, c in enumerate(r["labels"])}
        col = df[r["name"]] if r["name"] in df.columns else pd.Series([""] * len(df))
        out.append(np.array([idx.get(v, -1) for v in col.astype(str)], dtype=np.int64))
    return out

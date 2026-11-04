#!/usr/bin/env python3
"""encode: frozen encoder run once over every prepared table of a config and writes the pooled output ([CLS] joined with the masked mean, 2,048 numbers per text) to the
feature cache under a content-derived key. A table whose key is already cached is skipped.
    python scripts/encode.py --config finance # GPU fp16
    python scripts/encode.py --config dialogue --sets train --cpu
"""
from __future__ import annotations
import argparse
import json
import resource
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import cache, encoder, paths  # noqa: E402

def log(*a):
    print("[encode]", *a, flush=True)

def feature_key_of(cfg: dict, texts: list[str], dtype: str, wd: str, td: str) -> str:
    return cache.feature_key(wd, td, cache.sha256_column(texts), "cls_mean", cfg["max_len"], dtype, f"chunk{int(cfg.get('chunk_overlap', 32))}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--sets", nargs="+", default=None, help="default: every prepared table of the config")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--force", action="store_true", help="encode again even when the key is cached")
    args = ap.parse_args()
    t_all = time.time()
    cfg = paths.load_config(args.config)
    cdir = paths.cache_dir(cfg)
    sets = args.sets or sorted(p.stem for p in cdir.glob("*.csv"))
    device = "cpu" if args.cpu or not torch.cuda.is_available() else "cuda"
    dtype = "fp16" if device == "cuda" else "fp32"
    wd, td = encoder.digests(cfg["encoder"])
    log(f"encoder {cfg['encoder']} weights {wd[:12]} tokenizer {td[:12]} device {device} {dtype} max_len {cfg['max_len']} overlap {cfg.get('chunk_overlap', 32)}")
    tok = enc = None
    for s in sets:
        df = pd.read_csv(cdir / f"{s}.csv", dtype=str, keep_default_na=False)
        texts = df["text"].tolist()
        key = feature_key_of(cfg, texts, dtype, wd, td)
        if cache.load_features(key) is not None and not args.force:
            log(f"{s}: {len(texts)} texts already cached under {key}")
            continue
        if enc is None:
            tok, enc = encoder.load(cfg["encoder"], device)
        t0 = time.time()
        X, lengths, n_win = encoder.encode(tok, enc, texts, cfg["max_len"], int(cfg.get("chunk_overlap", 32)), int(cfg.get("token_budget", 16384)),
                                           device=device, progress=lambda d, n: log(f"  {s}: {d}/{n} windows"))
        secs = time.time() - t0
        audit = {"n": int(len(texts)), "tokens_p50": int(np.percentile(lengths, 50)), "tokens_p99": int(np.percentile(lengths, 99)),
                 "tokens_max": int(lengths.max()), "texts_over_one_window": int((n_win > 1).sum())}
        cache.save_features(key, X, df["id"].tolist(), {"config": cfg["name"], "set": s, "encoder": cfg["encoder"], "weights_sha256": wd, "tokenizer_sha256": td,
                                                        "pooling": "cls_mean", "max_len": cfg["max_len"], "chunk_overlap": int(cfg.get("chunk_overlap", 32)),
                                                        "dtype": dtype, "device": device, "seconds": round(secs, 1),
                                                        "rows_per_second": round(len(texts) / max(secs, 1e-6), 1), "length_audit": audit})
        log(f"{s}: {len(texts)} texts in {secs / 60:.1f} min ({len(texts) / max(secs, 1e-6):.0f} per second); tokens p50 {audit['tokens_p50']} p99 {audit['tokens_p99']} "
            f"max {audit['tokens_max']}, {audit['texts_over_one_window']} needed more than one window -> features/{key}")
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    gpu = f", GPU peak {torch.cuda.max_memory_allocated() / 2 ** 30:.1f} GB" if device == "cuda" else ""
    log(f"done in {(time.time() - t_all) / 60:.1f} min; peak RSS {peak_mb:.0f} MB{gpu}")

if __name__ == "__main__":
    main()

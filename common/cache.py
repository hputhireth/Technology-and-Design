"""Caching of the encoder output. Feature is keyed by SHA-256 and carries a manifest, so a
table is encoded once and a changed input can never be read as an old one."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
import numpy as np
from . import paths

_MEMO = ".digest_memo.json"

def sha256_file(path: str | Path, chunk: int = 1 << 24) -> str:
    """SHA-256 of a file"""
    path = Path(path)
    st = path.stat()
    memo_file = paths.p("hf_cache", _MEMO)
    memo = {}
    if memo_file.exists():
        try:
            memo = json.loads(memo_file.read_text(encoding="utf-8"))
        except Exception:
            memo = {}
    key = f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    if key in memo:
        return memo[key]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    d = h.hexdigest()
    if st.st_size > 1 << 20:
        memo[key] = d
        try:
            memo_file.parent.mkdir(parents=True, exist_ok=True)
            memo_file.write_text(json.dumps(memo, indent=1), encoding="utf-8")
        except Exception:
            pass
    return d

def sha256_column(values) -> str:
    """Digest of a text column, order-sensitive, one line per row."""
    h = hashlib.sha256()
    for v in values:
        h.update(str(v).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()

def feature_key(*parts) -> str:
    return hashlib.sha256("||".join(str(x) for x in parts).encode("utf-8")).hexdigest()[:16]

def feature_dir(key: str) -> Path:
    return paths.p("features", key)

def manifest(extra: dict) -> dict:
    m = {"command": " ".join(sys.argv), "time": time.strftime("%Y-%m-%d %H:%M:%S"), "hostname": platform.node(), "slurm_job_id": os.environ.get("SLURM_JOB_ID")}
    m.update(extra)
    return m

def save_features(key: str, pooled: np.ndarray, ids, extra: dict) -> Path:
    d = feature_dir(key)
    d.mkdir(parents=True, exist_ok=True)
    np.save(d / "pooled.npy", pooled.astype(np.float16))
    with open(d / "ids.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write("id\n")
        for i in ids:
            f.write(f"{i}\n")
    (d / "manifest.json").write_text(json.dumps(manifest(dict(extra, key=key, rows=int(pooled.shape[0]), dims=int(pooled.shape[1]))), indent=2, default=str), encoding="utf-8")
    return d

def load_features(key: str) -> tuple[np.ndarray, list[str]] | None:
    """The cached matrix and its ids, or None when the key is not cached or its manifest is missing."""
    d = feature_dir(key)
    if not (d / "pooled.npy").exists() or not (d / "manifest.json").exists():
        return None
    X = np.load(d / "pooled.npy")
    ids = [ln.strip() for ln in open(d / "ids.csv", encoding="utf-8")][1:]
    return X, ids

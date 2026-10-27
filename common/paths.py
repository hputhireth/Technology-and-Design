"""Folder layout under root, the project root on the supercomputer.
    hf_cache/ for encoder weights and tokenizer, read offline by the compute nodes
    data/raw/ the training files and data/raw/predict/*.csv
    data/cache/<config>/ the prepared tables written by scripts/prepare.py
    features/<key>/ the encoder output per table, fp16, keyed by content
    results/<config>/ the trained head, its scores, predictions and adaptations
    logs/ scheduler output, one file per job
"""
import json
import os
from pathlib import Path

DEFAULT_ROOT = "[redacted project path]"

def root() -> Path:
    return Path(os.environ.get("COS_ROOT", DEFAULT_ROOT)).expanduser()

def p(*parts) -> Path:
    return root().joinpath(*parts)

def code_root() -> Path:
    return Path(__file__).resolve().parents[1]

def load_config(name: str) -> dict:
    path = Path(name)
    if not path.exists():
        path = code_root() / "configs" / (name if name.endswith(".json") else name + ".json")
    if not path.exists():
        raise FileNotFoundError(f"config not found: {name}")
    return json.loads(path.read_text(encoding="utf-8"))

def resolve(path: str) -> Path:
    q = Path(path)
    return q if q.is_absolute() else root() / q

def cache_dir(cfg: dict) -> Path:
    d = p("data", "cache", cfg["name"])
    d.mkdir(parents=True, exist_ok=True)
    return d

def results_dir(cfg: dict, *parts) -> Path:
    d = p("results", cfg["name"], *parts)
    d.mkdir(parents=True, exist_ok=True)
    return d
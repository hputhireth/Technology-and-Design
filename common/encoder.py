"""The frozen encoder: bge-large forward pass that turns any number of texts of any length into one vector of 2,048 numbers each."""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import torch
from . import cache, paths

# compute nodes (no internet)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
if "HF_HOME" not in os.environ:
    os.environ["HF_HOME"] = str(paths.p("hf_cache"))

def model_dir(name_or_path: str) -> Path:
    """The folder with config.json and the weights: local path/ hub id already in HF_HOME."""
    p = Path(name_or_path)
    if p.exists():
        return p
    if (paths.root() / name_or_path).exists():
        return paths.root() / name_or_path
    from huggingface_hub import snapshot_download
    try:
        return Path(snapshot_download(name_or_path, local_files_only=True, allow_patterns=["*.json", "*.txt", "model.safetensors"]))
    except Exception as e:
        raise FileNotFoundError(f"{name_or_path} is not in the offline cache {os.environ['HF_HOME']}; download it once on a login node") from e

def weights_file(d: Path) -> Path:
    for n in ("model.safetensors", "pytorch_model.bin"):
        if (d / n).exists():
            return d / n
    raise FileNotFoundError(f"no weights file in {d}")

def digests(name_or_path: str) -> tuple[str, str]:
    """SHA-256 of the weights and the tokenizer."""
    d = model_dir(name_or_path)
    tok = next((d / n for n in ("tokenizer.json", "vocab.txt") if (d / n).exists()), None)
    if tok is None:
        raise FileNotFoundError(f"no tokenizer file in {d}")
    return cache.sha256_file(weights_file(d)), cache.sha256_file(tok)

def load(name_or_path: str, device: str):
    """Tokenizer and encoder, the encoder in fp16 on a GPU and fp32 on a CPU, evaluation mode."""
    from transformers import AutoModel, AutoTokenizer
    d = str(model_dir(name_or_path))
    tok = AutoTokenizer.from_pretrained(d)
    enc = AutoModel.from_pretrained(d, add_pooling_layer=False).to(device).eval()
    if device == "cuda":
        enc.half()
    return tok, enc

def pool(hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """[CLS] joined with the mean over the real tokens: [B, T, H] -> [B, 2H]."""
    m = mask.unsqueeze(-1).to(hidden.dtype)
    return torch.cat([hidden[:, 0], (hidden * m).sum(1) / m.sum(1).clamp(min=1.0)], dim=-1)

@torch.no_grad()
def encode(tok, enc, texts: list[str], max_len: int = 512, overlap: int = 32, token_budget: int = 16384,
           max_batch: int = 128, device: str = "cpu", progress=None):
    """Tokenisation without truncation. If text longer than a window, it is cut into
    windows of max_len (with [CLS] and [SEP]) that overlap by `overlap` tokens, each window is
    pooled and the windows are averaged by their token count. Batches are packed longest first
    under a token budget. Returns the pooled matrix [N, 2H] in float32, the token count per text
    and the number of windows per text."""
    body, step = max_len - 2, max_len - 2 - overlap
    windows, lengths, n_win = [], np.zeros(len(texts), np.int64), np.zeros(len(texts), np.int64)
    for i, ids in enumerate(tok(texts, add_special_tokens=False, truncation=False)["input_ids"]):
        lengths[i] = len(ids) + 2
        for start in range(0, max(len(ids) - overlap, 1), step):
            windows.append((i, [tok.cls_token_id] + ids[start:start + body] + [tok.sep_token_id]))
            n_win[i] += 1
    out = np.zeros((len(texts), 2 * enc.config.hidden_size), np.float64)
    weight = np.zeros(len(texts))
    order = sorted(range(len(windows)), key=lambda w: -len(windows[w][1]))
    pos, done = 0, 0
    while pos < len(order):
        L = len(windows[order[pos]][1])
        sel = order[pos:pos + max(1, min(max_batch, token_budget // L))]
        pos += len(sel)
        batch = tok.pad({"input_ids": [windows[w][1] for w in sel]}, return_tensors="pt").to(device)
        hidden = enc(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).last_hidden_state
        pooled = pool(hidden, batch["attention_mask"]).float().cpu().numpy()
        toks = batch["attention_mask"].sum(1).cpu().numpy()
        for r, w in enumerate(sel):
            out[windows[w][0]] += pooled[r] * toks[r]
            weight[windows[w][0]] += toks[r]
        done += len(sel)
        if progress and (done % 2000 < len(sel) or done == len(order)):
            progress(done, len(order))
    return (out / np.maximum(weight, 1.0)[:, None]).astype(np.float32), lengths, n_win

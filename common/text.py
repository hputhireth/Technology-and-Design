"""Text cleaning, label normalisation, duplicate keys, grouping and the grouped splits."""
from __future__ import annotations
import re
import unicodedata
import numpy as np

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")
_MOJI_TAIL = ("\u0080-\u00bf\u20ac\u201a\u0192\u201e\u2026\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\u017d"
              "\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\u017e\u0178")
_MOJIBAKE = re.compile("(?:\u00c2[ " + _MOJI_TAIL + "]|[\u00c3\u00e2][" + _MOJI_TAIL + "])")
_CASHTAG = re.compile(r"\$[a-z]+")
_NONALPHA = re.compile(r"[^a-z ]+")
_SPACES = re.compile(r" +")

def fix_mojibake(s: str) -> str:
    """Repair text that was UTF-8 but got decoded as Windows-1252."""
    if not s or not _MOJIBAKE.search(s):
        return s
    s = s.replace("\u00c2 ", " ")
    if not _MOJIBAKE.search(s):
        return s
    for errors in ("strict", "ignore"):
        try:
            fixed = s.encode("cp1252", errors=errors).decode("utf-8", errors=errors)
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if len(fixed) >= 0.7 * len(s):
            return fixed
    return s

def clean_text(s) -> str:
    """Mojibake repair, unicode NFC, invisible characters out, whitespace collapsed. Punctuation stays: it carries sentiment."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = fix_mojibake(str(s))
    s = unicodedata.normalize("NFC", s).replace("​", "").replace("﻿", "").replace("\xa0", " ")
    s = s.replace("_comma_", ",")
    return _WS.sub(" ", s).strip()


def norm_key(s: str) -> str:
    """Key for exact-duplicate detection: lower case, punctuation and whitespace removed."""
    return _PUNCT.sub("", str(s).lower()).replace(" ", "")

def normalise_labels(values, reading: dict) -> np.ndarray:
    """Labels of one reading as the configured names; anything unknown becomes '' (unlabelled)."""
    aliases = {k.lower(): v for k, v in reading.get("aliases", {}).items()}
    known = set(reading["labels"])
    out = []
    for v in values:
        v = _WS.sub(" ", str(v).strip().lower())
        v = aliases.get(v, v)
        out.append(v if v in known else "")
    return np.array(out, dtype=object)

def near_duplicate_keys(texts) -> np.ndarray:
    """One key per text so that near duplicates never mount a split."""
    keys = []
    for i, t in enumerate(texts):
        k = _SPACES.sub(" ", _NONALPHA.sub(" ", _CASHTAG.sub(" ", str(t).lower()))).strip()
        keys.append(k if k else f"t{i}")
    return np.array(keys)

def run_keys(values) -> np.ndarray:
    """Runs of consecutive rows with the same value, in file order."""
    v = np.asarray(values)
    run = np.cumsum(np.r_[True, v[1:] != v[:-1]])
    return np.array([f"run{r:06d}" for r in run])

def grouped_folds(y: np.ndarray, groups: np.ndarray, folds: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    from sklearn.model_selection import StratifiedGroupKFold
    sgk = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    return [(tr, va) for tr, va in sgk.split(np.zeros(len(y)), y, groups)]

def confirmation_split(y: np.ndarray, groups: np.ndarray, fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Development rows and the confirmation rows held out before anything is fitted by group."""
    if fraction <= 0:
        return np.arange(len(y)), np.zeros(0, int)
    k = max(2, int(round(1.0 / fraction)))
    dev, conf = grouped_folds(y, groups, k, seed)[0]
    return np.sort(dev), np.sort(conf)
